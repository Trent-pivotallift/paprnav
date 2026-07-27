from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ADCostLedgerEntry


def record_ad_cost_entry(
    db: Session,
    *,
    idempotency_key: str | None,
    scope_type: str,
    cost_category: str,
    usage_quantity: Decimal | int | float | str,
    usage_unit: str,
    actual_cost_usd: Decimal | int | float | str = Decimal("0"),
    allocated_cost_usd: Decimal | int | float | str = Decimal("0"),
    attribution_status: str = "informational_unallocated",
    source_snapshot_id: str | None = None,
    coverage_set_id: str | None = None,
    aircraft_id: str | None = None,
    organization_id: str | None = None,
    allocation_policy_version: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ADCostLedgerEntry:
    entry = None
    if idempotency_key:
        entry = db.scalar(
            select(ADCostLedgerEntry).where(ADCostLedgerEntry.idempotency_key == idempotency_key)
        )
    if entry is None:
        entry = ADCostLedgerEntry(idempotency_key=idempotency_key)
        db.add(entry)

    entry.scope_type = scope_type
    entry.cost_category = cost_category
    entry.source_snapshot_id = source_snapshot_id
    entry.coverage_set_id = coverage_set_id
    entry.aircraft_id = aircraft_id
    entry.organization_id = organization_id
    entry.usage_quantity = Decimal(str(usage_quantity))
    entry.usage_unit = usage_unit
    entry.actual_cost_usd = Decimal(str(actual_cost_usd))
    entry.allocated_cost_usd = Decimal(str(allocated_cost_usd))
    entry.attribution_status = attribution_status
    entry.allocation_policy_version = allocation_policy_version
    entry.metadata_json = metadata or {}
    db.flush()
    return entry
