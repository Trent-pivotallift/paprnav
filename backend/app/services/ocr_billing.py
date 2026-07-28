from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.core import OCRRun


ZERO = Decimal("0")


def summarize_ocr_billing(
    db: Session,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    account_tag: str | None = None,
    aircraft_tag: str | None = None,
    billing_status: str | None = None,
) -> dict[str, Any]:
    statement = (
        select(OCRRun)
        .options(selectinload(OCRRun.ingestion_job))
        .order_by(OCRRun.created_at, OCRRun.id)
    )
    if date_from is not None:
        statement = statement.where(OCRRun.created_at >= date_from)
    if date_to is not None:
        statement = statement.where(OCRRun.created_at < date_to)
    if account_tag is not None:
        statement = statement.where(OCRRun.billable_account_tag == account_tag)
    if aircraft_tag is not None:
        statement = statement.where(OCRRun.billable_aircraft_tag == aircraft_tag)
    if billing_status is not None:
        statement = statement.where(OCRRun.billing_status == billing_status)

    selected_runs = list(db.scalars(statement).all())
    runs = [run for run in selected_runs if run.status == "complete"]
    excluded_run_count = len(selected_runs) - len(runs)
    groups: dict[tuple[str | None, str | None], list[OCRRun]] = defaultdict(list)
    for run in runs:
        groups[(run.billable_account_tag, run.billable_aircraft_tag)].append(run)

    group_summaries = [
        _summarize_group(group_runs, account_tag=key[0], aircraft_tag=key[1])
        for key, group_runs in sorted(
            groups.items(),
            key=lambda item: (item[0][0] or "", item[0][1] or ""),
        )
    ]
    totals = _usage_totals(runs)
    totals["groupCount"] = len(group_summaries)
    totals["excludedRunCount"] = excluded_run_count

    return {
        "generatedAt": datetime.now(timezone.utc),
        "dateFrom": date_from,
        "dateTo": date_to,
        "accountTag": account_tag,
        "aircraftTag": aircraft_tag,
        "billingStatus": billing_status,
        "totals": totals,
        "groups": group_summaries,
    }


def _summarize_group(
    runs: list[OCRRun],
    *,
    account_tag: str | None,
    aircraft_tag: str | None,
) -> dict[str, Any]:
    provider_groups: dict[
        tuple[str, str, str | None, str | None, str | None],
        list[OCRRun],
    ] = defaultdict(list)
    for run in runs:
        metadata = run.cost_allocation_tags or {}
        key = (
            run.provider_name,
            run.provider_version,
            _optional_string(metadata.get("provider_channel")),
            _optional_string(metadata.get("provider_mode")),
            _optional_string(metadata.get("routing_mode")),
        )
        provider_groups[key].append(run)

    provider_summaries = []
    for key, provider_runs in sorted(
        provider_groups.items(),
        key=lambda item: tuple(value or "" for value in item[0]),
    ):
        provider_summary = {
            "providerName": key[0],
            "providerVersion": key[1],
            "providerChannel": key[2],
            "providerMode": key[3],
            "routingMode": key[4],
            **_usage_totals(provider_runs),
        }
        provider_summaries.append(provider_summary)

    return {
        "accountTag": account_tag,
        "aircraftTag": aircraft_tag,
        **_usage_totals(runs),
        "providers": provider_summaries,
    }


def _usage_totals(runs: list[OCRRun]) -> dict[str, Any]:
    upload_ids = {
        run.ingestion_job.upload_id
        for run in runs
        if run.ingestion_job is not None
    }
    chargeable_pages = sum(
        _page_priced_quantity(run)
        for run in runs
        if run.billing_status == "chargeable"
    )
    not_billable_pages = sum(
        _page_priced_quantity(run)
        for run in runs
        if run.billing_status == "not_billable"
    )
    other_status_pages = sum(
        _page_priced_quantity(run)
        for run in runs
        if run.billing_status not in {"chargeable", "not_billable"}
    )
    chargeable_cost = sum(
        (_estimated_cost(run) for run in runs if run.billing_status == "chargeable"),
        start=ZERO,
    )
    not_billable_cost = sum(
        (_estimated_cost(run) for run in runs if run.billing_status == "not_billable"),
        start=ZERO,
    )
    other_status_cost = sum(
        (
            _estimated_cost(run)
            for run in runs
            if run.billing_status not in {"chargeable", "not_billable"}
        ),
        start=ZERO,
    )
    return {
        "uploadCount": len(upload_ids),
        "ocrRunCount": len(runs),
        "unattributedRunCount": sum(
            run.billable_account_tag is None or run.billable_aircraft_tag is None
            for run in runs
        ),
        "unpricedRunCount": sum(not _has_cost_estimate(run) for run in runs),
        "chargeableUnpricedRunCount": sum(
            run.billing_status == "chargeable" and not _has_cost_estimate(run)
            for run in runs
        ),
        "notBillableUnpricedRunCount": sum(
            run.billing_status == "not_billable" and not _has_cost_estimate(run)
            for run in runs
        ),
        "otherBillingStatusUnpricedRunCount": sum(
            run.billing_status not in {"chargeable", "not_billable"}
            and not _has_cost_estimate(run)
            for run in runs
        ),
        "nonPagePricedRunCount": sum(
            run.pricing_unit != "page" for run in runs
        ),
        "chargeablePageCount": chargeable_pages,
        "notBillablePageCount": not_billable_pages,
        "otherBillingStatusPageCount": other_status_pages,
        "nativeBypassPageCount": sum(_metadata_count(run, "native_bypass_page_count") for run in runs),
        "textractPageCount": sum(_textract_page_count(run) for run in runs),
        "totalEstimatedCostUsd": chargeable_cost + not_billable_cost + other_status_cost,
        "chargeableEstimatedCostUsd": chargeable_cost,
        "notBillableEstimatedCostUsd": not_billable_cost,
        "otherBillingStatusEstimatedCostUsd": other_status_cost,
    }


def _estimated_cost(run: OCRRun) -> Decimal:
    if run.estimated_cost_usd is not None:
        return Decimal(str(run.estimated_cost_usd))
    if (
        run.pricing_unit == "page"
        and run.pricing_rate_usd is not None
        and run.billable_page_count is not None
    ):
        return Decimal(str(run.pricing_rate_usd)) * max(run.billable_page_count, 0)
    return ZERO


def _has_cost_estimate(run: OCRRun) -> bool:
    return run.estimated_cost_usd is not None or (
        run.pricing_unit == "page"
        and run.pricing_rate_usd is not None
        and run.billable_page_count is not None
    )


def _page_priced_quantity(run: OCRRun) -> int:
    if run.pricing_unit != "page":
        return 0
    return max(run.billable_page_count or 0, 0)


def _textract_page_count(run: OCRRun) -> int:
    metadata_count = _metadata_count(run, "textract_page_count")
    if "textract_page_count" in (run.cost_allocation_tags or {}):
        return metadata_count
    metadata = run.cost_allocation_tags or {}
    if metadata.get("provider_channel") == "aws" and run.pricing_unit == "page":
        return _page_priced_quantity(run)
    return 0


def _metadata_count(run: OCRRun, key: str) -> int:
    value = (run.cost_allocation_tags or {}).get(key)
    if isinstance(value, bool):
        return 0
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
