from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import IngestionJob, OCRRun, Upload
from app.services.ingestion import create_ingestion_job, process_ingestion_job
from tests.conftest import (
    add_membership,
    create_aircraft,
    create_organization,
    create_user,
    login,
)

NATIVE_FIXTURE = Path(__file__).parent / "fixtures" / "native_text" / "pure_native.pdf"


class ProviderMustNotRun:
    provider_name = "aws_textract"
    provider_version = "test"
    configuration_hash = "must-not-run"

    def process_upload(self, **_kwargs):
        raise AssertionError("A reliable native page must not invoke Textract")


def _add_ocr_run(
    db: Session,
    *,
    aircraft,
    user,
    account_tag: str,
    aircraft_tag: str,
    billing_status: str,
    pages: int,
    rate: Decimal,
    created_at: datetime,
    provider_mode: str = "analysis_async",
    upload_suffix: str,
) -> OCRRun:
    upload = Upload(
        aircraft_id=aircraft.id,
        uploaded_by_user_id=user.id,
        original_filename=f"{upload_suffix}.pdf",
        content_type="application/pdf",
        file_size_bytes=100,
        storage_backend="local",
        storage_key=f"fixtures/{upload_suffix}.pdf",
        sha256=upload_suffix.rjust(64, "0"),
        status="processed",
        pilot_consent_accepted=billing_status == "chargeable",
        initial_ocr_billable_to_tag=account_tag,
        cost_allocation_tags={
            "BillableAccount": account_tag,
            "Aircraft": aircraft_tag,
        },
    )
    db.add(upload)
    db.flush()
    job = IngestionJob(
        upload_id=upload.id,
        aircraft_id=aircraft.id,
        created_by_user_id=user.id,
        status="awaiting_page_review",
        page_extraction_status="complete",
        ocr_status="complete",
        verification_status="awaiting_review",
        entry_extraction_status="not_started",
    )
    db.add(job)
    db.flush()
    run = OCRRun(
        ingestion_job_id=job.id,
        provider_name="selective_pdf_text_router",
        provider_version="1.0",
        configuration_hash=upload_suffix,
        status="complete",
        billing_status=billing_status,
        billable_account_tag=account_tag,
        billable_aircraft_tag=aircraft_tag,
        billable_page_count=pages,
        pricing_unit="page",
        pricing_rate_usd=rate,
        estimated_cost_usd=None,
        cost_allocation_tags={
            "provider_channel": "aws",
            "provider_mode": provider_mode,
        },
        created_at=created_at,
    )
    db.add(run)
    db.flush()
    return run


def _add_platform_admin(db: Session) -> None:
    admin_user = create_user(db, "billing.admin@paprnav.local", "Billing Admin")
    admin_org = create_organization(db, "Paprnav Operations", "platform")
    add_membership(db, admin_org, admin_user, "platform_admin")


def test_ocr_billing_summary_groups_filters_and_separates_statuses(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    first_aircraft = demo_data["aircraft"]
    first_owner = demo_data["owner_user"]
    second_owner = create_user(db_session, "billing.owner@paprnav.local", "Billing Owner")
    second_org = create_organization(db_session, "Billing Owner Hangar", "owner")
    add_membership(db_session, second_org, second_owner, "owner_admin")
    second_aircraft = create_aircraft(db_session, second_org, second_owner, n_number="N222BB")
    _add_platform_admin(db_session)

    now = datetime.now(timezone.utc)
    _add_ocr_run(
        db_session,
        aircraft=first_aircraft,
        user=first_owner,
        account_tag="acct-first",
        aircraft_tag="aircraft-first",
        billing_status="chargeable",
        pages=4,
        rate=Decimal("0.015"),
        created_at=now - timedelta(days=2),
        upload_suffix="one",
    )
    second_first_run = _add_ocr_run(
        db_session,
        aircraft=first_aircraft,
        user=first_owner,
        account_tag="acct-first",
        aircraft_tag="aircraft-first",
        billing_status="not_billable",
        pages=2,
        rate=Decimal("0.015"),
        created_at=now - timedelta(days=1),
        upload_suffix="two",
    )
    second_first_run.estimated_cost_usd = Decimal("0.04000000")
    _add_ocr_run(
        db_session,
        aircraft=second_aircraft,
        user=second_owner,
        account_tag="acct-second",
        aircraft_tag="aircraft-second",
        billing_status="chargeable",
        pages=3,
        rate=Decimal("0.020"),
        created_at=now,
        provider_mode="sync",
        upload_suffix="three",
    )
    db_session.commit()

    login(client, "owner.test@paprnav.local")
    assert client.get("/api/v1/admin/ocr-billing").status_code == 403
    client.post("/api/v1/auth/logout")
    login(client, "billing.admin@paprnav.local")

    response = client.get("/api/v1/admin/ocr-billing")
    assert response.status_code == 200
    payload = response.json()
    assert payload["totals"]["groupCount"] == 2
    assert payload["totals"]["uploadCount"] == 3
    assert payload["totals"]["ocrRunCount"] == 3
    assert payload["totals"]["excludedRunCount"] == 0
    assert payload["totals"]["unattributedRunCount"] == 0
    assert payload["totals"]["unpricedRunCount"] == 0
    assert payload["totals"]["chargeableUnpricedRunCount"] == 0
    assert payload["totals"]["notBillableUnpricedRunCount"] == 0
    assert payload["totals"]["otherBillingStatusUnpricedRunCount"] == 0
    assert payload["totals"]["nonPagePricedRunCount"] == 0
    assert payload["totals"]["chargeablePageCount"] == 7
    assert payload["totals"]["notBillablePageCount"] == 2
    assert payload["totals"]["otherBillingStatusPageCount"] == 0
    assert payload["totals"]["nativeBypassPageCount"] == 0
    assert payload["totals"]["textractPageCount"] == 9
    assert Decimal(payload["totals"]["totalEstimatedCostUsd"]) == Decimal("0.16000000")
    assert Decimal(payload["totals"]["chargeableEstimatedCostUsd"]) == Decimal("0.12000000")
    assert Decimal(payload["totals"]["notBillableEstimatedCostUsd"]) == Decimal("0.04000000")
    assert Decimal(payload["totals"]["otherBillingStatusEstimatedCostUsd"]) == Decimal("0")

    first_group = next(group for group in payload["groups"] if group["accountTag"] == "acct-first")
    assert first_group["aircraftTag"] == "aircraft-first"
    assert first_group["uploadCount"] == 2
    assert first_group["providers"][0]["providerChannel"] == "aws"
    assert first_group["providers"][0]["providerMode"] == "analysis_async"
    assert first_group["providers"][0]["routingMode"] is None

    filtered = client.get(
        "/api/v1/admin/ocr-billing",
        params={
            "accountTag": "acct-first",
            "billingStatus": "chargeable",
            "dateFrom": (now - timedelta(days=3)).isoformat(),
            "dateTo": (now - timedelta(days=1, hours=12)).isoformat(),
        },
    )
    assert filtered.status_code == 200
    filtered_payload = filtered.json()
    assert filtered_payload["totals"]["groupCount"] == 1
    assert filtered_payload["totals"]["ocrRunCount"] == 1
    assert filtered_payload["totals"]["chargeablePageCount"] == 4
    assert filtered_payload["totals"]["notBillablePageCount"] == 0


def test_ocr_billing_summary_empty_result_and_invalid_dates(
    client: TestClient,
    db_session: Session,
) -> None:
    _add_platform_admin(db_session)
    db_session.commit()
    login(client, "billing.admin@paprnav.local")

    response = client.get(
        "/api/v1/admin/ocr-billing",
        params={"accountTag": "missing"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["groups"] == []
    assert payload["totals"] == {
        "uploadCount": 0,
        "ocrRunCount": 0,
        "unattributedRunCount": 0,
        "unpricedRunCount": 0,
        "chargeableUnpricedRunCount": 0,
        "notBillableUnpricedRunCount": 0,
        "otherBillingStatusUnpricedRunCount": 0,
        "nonPagePricedRunCount": 0,
        "chargeablePageCount": 0,
        "notBillablePageCount": 0,
        "otherBillingStatusPageCount": 0,
        "nativeBypassPageCount": 0,
        "textractPageCount": 0,
        "totalEstimatedCostUsd": "0",
        "chargeableEstimatedCostUsd": "0",
        "notBillableEstimatedCostUsd": "0",
        "otherBillingStatusEstimatedCostUsd": "0",
        "groupCount": 0,
        "excludedRunCount": 0,
    }

    invalid = client.get(
        "/api/v1/admin/ocr-billing",
        params={
            "dateFrom": "2026-07-28T00:00:00Z",
            "dateTo": "2026-07-27T00:00:00Z",
        },
    )
    assert invalid.status_code == 422
    invalid_status = client.get(
        "/api/v1/admin/ocr-billing",
        params={"billingStatus": "chargable"},
    )
    assert invalid_status.status_code == 422


def test_ocr_billing_summary_marks_unknown_cost_instead_of_assuming_page_pricing(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    _add_platform_admin(db_session)
    run = _add_ocr_run(
        db_session,
        aircraft=demo_data["aircraft"],
        user=demo_data["owner_user"],
        account_tag="acct-unpriced",
        aircraft_tag="aircraft-unpriced",
        billing_status="chargeable",
        pages=2,
        rate=Decimal("0.50"),
        created_at=datetime.now(timezone.utc),
        upload_suffix="unpriced",
    )
    run.pricing_unit = "processing_second"
    db_session.commit()
    login(client, "billing.admin@paprnav.local")

    response = client.get(
        "/api/v1/admin/ocr-billing",
        params={
            "accountTag": "acct-unpriced",
            "dateFrom": "2026-01-01T00:00:00",
        },
    )
    assert response.status_code == 200
    totals = response.json()["totals"]
    assert totals["ocrRunCount"] == 1
    assert totals["unpricedRunCount"] == 1
    assert totals["chargeableUnpricedRunCount"] == 1
    assert totals["nonPagePricedRunCount"] == 1
    assert totals["chargeablePageCount"] == 0
    assert Decimal(totals["totalEstimatedCostUsd"]) == Decimal("0")


def test_ocr_billing_excludes_failed_runs_and_separates_other_billing_status(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    _add_platform_admin(db_session)
    failed = _add_ocr_run(
        db_session,
        aircraft=demo_data["aircraft"],
        user=demo_data["owner_user"],
        account_tag="acct-status",
        aircraft_tag="aircraft-status",
        billing_status="chargeable",
        pages=5,
        rate=Decimal("0.10"),
        created_at=datetime.now(timezone.utc),
        upload_suffix="failed",
    )
    failed.status = "failed"
    credited = _add_ocr_run(
        db_session,
        aircraft=demo_data["aircraft"],
        user=demo_data["owner_user"],
        account_tag="acct-status",
        aircraft_tag="aircraft-status",
        billing_status="credited",
        pages=2,
        rate=Decimal("0.10"),
        created_at=datetime.now(timezone.utc),
        upload_suffix="credited",
    )
    credited.cost_allocation_tags = {
        **credited.cost_allocation_tags,
        "routing_mode": "selective_native_text",
        "native_bypass_page_count": 1,
        "textract_page_count": 1,
    }
    db_session.commit()
    login(client, "billing.admin@paprnav.local")

    response = client.get(
        "/api/v1/admin/ocr-billing",
        params={"accountTag": "acct-status"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["totals"]["ocrRunCount"] == 1
    assert payload["totals"]["excludedRunCount"] == 1
    assert payload["totals"]["chargeablePageCount"] == 0
    assert payload["totals"]["notBillablePageCount"] == 0
    assert payload["totals"]["otherBillingStatusPageCount"] == 2
    assert payload["totals"]["nativeBypassPageCount"] == 1
    assert payload["totals"]["textractPageCount"] == 1
    assert Decimal(payload["totals"]["otherBillingStatusEstimatedCostUsd"]) == Decimal("0.20")
    assert payload["groups"][0]["providers"][0]["routingMode"] == "selective_native_text"


def test_native_only_ingestion_persists_and_reports_zero_billable_pages(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    pdf_bytes = NATIVE_FIXTURE.read_bytes()
    storage_key = "fixtures/native-only-billing.pdf"
    stored_path = Path(get_settings().local_storage_path) / storage_key
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(pdf_bytes)
    upload = Upload(
        aircraft_id=demo_data["aircraft"].id,
        uploaded_by_user_id=demo_data["owner_user"].id,
        original_filename="native-only-billing.pdf",
        content_type="application/pdf",
        file_size_bytes=len(pdf_bytes),
        storage_backend="local",
        storage_key=storage_key,
        sha256=sha256(pdf_bytes).hexdigest(),
        status="received",
        pilot_consent_accepted=True,
        initial_ocr_billable_to_tag="acct-native",
        cost_allocation_tags={
            "BillableAccount": "acct-native",
            "Aircraft": "aircraft-native",
        },
    )
    db_session.add(upload)
    db_session.flush()
    job = create_ingestion_job(
        db_session,
        upload,
        demo_data["owner_user"].id,
        "airframe",
    )
    db_session.commit()

    process_ingestion_job(db_session, job, provider=ProviderMustNotRun())
    run = db_session.scalar(select(OCRRun).where(OCRRun.ingestion_job_id == job.id))
    assert run is not None
    assert run.status == "complete"
    assert run.billable_page_count == 0
    assert run.pricing_unit == "page"
    assert run.pricing_rate_usd == 0
    assert run.estimated_cost_usd == 0

    _add_platform_admin(db_session)
    db_session.commit()
    login(client, "billing.admin@paprnav.local")
    response = client.get(
        "/api/v1/admin/ocr-billing",
        params={"accountTag": "acct-native"},
    )
    assert response.status_code == 200
    totals = response.json()["totals"]
    assert totals["ocrRunCount"] == 1
    assert totals["unpricedRunCount"] == 0
    assert totals["chargeablePageCount"] == 0
    assert totals["nativeBypassPageCount"] == 1
    assert totals["textractPageCount"] == 0
    assert Decimal(totals["totalEstimatedCostUsd"]) == Decimal("0")
