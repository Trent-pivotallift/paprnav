from __future__ import annotations

from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import (
    ADCostLedgerEntry,
    ADCoverageSet,
    ADCoverageSubscription,
    ADMatchAdjudication,
    ADMatchResult,
    ADSourceSnapshot,
    ADSupersession,
    IngestionJob,
    LogbookEntry,
    LogbookEntryEvidence,
    LogbookSection,
    OCRRun,
)
from app.services.ad_coverage import resolve_aircraft_ad_coverage
from app.services.ad_matching import match_aircraft_ads
from app.services.drs_bulk_import import import_drs_bulk_rows, upsert_snapshot
from app.services.ingestion import process_ingestion_job
from tests.conftest import (
    add_membership,
    create_aircraft,
    create_organization,
    create_user,
    login,
)
from tests.test_ad_matching import create_approved_extraction


NATIVE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "native_text" / "pure_native.pdf"
)


class ProviderMustNotRun:
    provider_name = "aws_textract"
    provider_version = "test"
    configuration_hash = "must-not-run"

    def process_upload(self, **_kwargs):
        raise AssertionError("A reliable native page must not invoke Textract")


def _ingest_and_verify_native_entry(
    client: TestClient,
    db: Session,
    *,
    aircraft_id: str,
) -> tuple[LogbookEntry, OCRRun, str]:
    pdf_bytes = NATIVE_FIXTURE.read_bytes()
    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={
            "file": (
                "controlled-native-entry.pdf",
                BytesIO(pdf_bytes),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 201
    upload_payload = upload_response.json()["upload"]
    job_id = upload_response.json()["ingestionJob"]["id"]
    download = client.get(upload_payload["downloadUrl"])
    assert download.status_code == 200
    assert download.content == pdf_bytes

    job = db.get(IngestionJob, job_id)
    assert job is not None
    process_ingestion_job(db, job, provider=ProviderMustNotRun())
    run = db.scalar(select(OCRRun).where(OCRRun.ingestion_job_id == job_id))
    assert run is not None

    detail = client.get(f"/api/v1/ingestion-jobs/{job_id}").json()
    assert len(detail["pages"]) == 1
    page = detail["pages"][0]
    assert page["extractionPlan"]["selectedProvider"] == "pdf_native_text"
    assert page["imageDownloadUrl"]

    verify_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/page-verification",
        json={
            "pages": [
                {
                    "pageId": page["id"],
                    "currentPageOrder": page["currentPageOrder"],
                }
            ],
            "isOrderConfirmed": True,
            "isComplete": True,
            "missingOrUncertainNotes": None,
        },
    )
    assert verify_response.status_code == 200
    extract_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/extract-logbook-entries"
    )
    assert extract_response.status_code == 200
    entries = extract_response.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["reviewStatus"] == "needs_review"
    db.expire(job)
    assert job.status == "awaiting_entry_review"
    assert job.completed_at is None

    owner_attempt = client.patch(
        f"/api/v1/aircraft/{aircraft_id}/logbook-entries/{entries[0]['id']}",
        json={"reviewStatus": "verified"},
    )
    assert owner_attempt.status_code == 403

    login(client, "shop.test@paprnav.local")
    review_response = client.patch(
        f"/api/v1/aircraft/{aircraft_id}/logbook-entries/{entries[0]['id']}",
        json={"reviewStatus": "verified"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["reviewStatus"] == "verified"
    db.expire(job)
    assert job.status == "complete"
    assert job.completed_at is not None
    entry = db.get(LogbookEntry, entries[0]["id"])
    assert entry is not None
    assert entry.reviewed_by_user_id is not None
    assert entry.reviewed_at is not None
    return entry, run, page["id"]


def _create_verified_entry(
    db: Session,
    *,
    aircraft,
    user,
    section_key: str,
    entry_date: date,
    text: str,
    review_status: str = "verified",
) -> LogbookEntry:
    section = db.scalar(
        select(LogbookSection).where(LogbookSection.key == section_key)
    )
    assert section is not None
    entry = LogbookEntry(
        aircraft_id=aircraft.id,
        logbook_section_id=section.id,
        entry_date=entry_date,
        description=text,
        performer_name="Fixture Mechanic",
        performer_credential="A&P IA",
        source_type="ocr_ingestion",
        created_by_user_id=user.id,
        raw_text=text,
        review_status=review_status,
    )
    db.add(entry)
    db.flush()
    return entry


def _approved_ad(
    db: Session,
    *,
    ad_number: str,
    product: str,
    action: str,
    intervals: list[dict] | None = None,
):
    return create_approved_extraction(
        db,
        title=f"Airworthiness Directives; {product}",
        document_number=f"fixture-{ad_number}",
        ad_number=ad_number,
        affected_products=[product],
        compliance_actions=[action],
        compliance_intervals=intervals or [],
    )


def _import_drs_row(
    db: Session,
    *,
    ad_number: str,
    product_type: str,
    make: str,
    model: str,
    status: str = "Current",
) -> None:
    import_drs_bulk_rows(
        db,
        [
            {
                "adNumber": ad_number,
                "Subject": f"Airworthiness Directives; {make} {model}",
                "ProductType": product_type,
                "Make": make,
                "Model": model,
                "Status": status,
                "Identifier": f"DRS-{ad_number}",
            }
        ],
        filename=f"controlled-{ad_number}.accdb",
        content_hash=ad_number.replace("-", "").ljust(64, "0"),
    )


def test_scenario_01_retained_native_pdf_requires_human_review_and_keeps_evidence(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    login(client, "owner.test@paprnav.local")
    entry, run, page_id = _ingest_and_verify_native_entry(
        client,
        db_session,
        aircraft_id=demo_data["aircraft"].id,
    )

    assert run.billable_page_count == 0
    assert run.cost_allocation_tags["native_bypass_page_count"] == 1
    assert run.cost_allocation_tags["textract_page_count"] == 0
    assert entry.review_status == "verified"
    assert "AD 2020-01-02" in entry.description
    evidence = db_session.scalars(
        select(LogbookEntryEvidence).where(
            LogbookEntryEvidence.logbook_entry_id == entry.id
        )
    ).all()
    assert evidence
    assert any(item.ingestion_page_id == page_id for item in evidence)
    review_outcome = next(
        item for item in evidence if item.field_name == "review_outcome"
    )
    assert review_outcome.review_metadata["actorUserId"] == entry.reviewed_by_user_id
    assert review_outcome.review_metadata["reviewElapsedSeconds"] is None


def test_scenario_02_airframe_ad_uses_verified_page_evidence(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    login(client, "owner.test@paprnav.local")
    entry, _, page_id = _ingest_and_verify_native_entry(
        client,
        db_session,
        aircraft_id=aircraft.id,
    )
    _approved_ad(
        db_session,
        ad_number="2020-01-02",
        product="Cessna 172R Airplanes",
        action="Inspect the affected airframe.",
    )
    _import_drs_row(
        db_session,
        ad_number="2020-01-02",
        product_type="Aircraft",
        make="Cessna",
        model="172R",
    )
    db_session.commit()

    stats = match_aircraft_ads(db_session, aircraft.id)
    assert stats["matched"] == 1
    result = db_session.scalar(
        select(ADMatchResult).where(ADMatchResult.status == "candidate_satisfied")
    )
    assert result is not None
    assert result.installed_component.role == "airframe"
    assert result.evidence_links[0].logbook_entry_id == entry.id
    assert any(
        item.ingestion_page_id == page_id for item in entry.evidence_links
    )


def test_scenario_03_engine_applicability_remains_component_specific(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    _create_verified_entry(
        db_session,
        aircraft=aircraft,
        user=demo_data["owner_user"],
        section_key="engine",
        entry_date=date(2026, 1, 3),
        text="Complied with AD 2026-03-01 by inspecting the Lycoming engine.",
    )
    _approved_ad(
        db_session,
        ad_number="2026-03-01",
        product="Lycoming IO-360-L2A Engines",
        action="Inspect the engine.",
    )
    _import_drs_row(
        db_session,
        ad_number="2026-03-01",
        product_type="Engine",
        make="Lycoming",
        model="IO-360-L2A",
    )
    db_session.commit()

    match_aircraft_ads(db_session, aircraft.id)
    result = db_session.scalar(
        select(ADMatchResult).where(ADMatchResult.status == "candidate_satisfied")
    )
    assert result is not None
    assert result.installed_component.role == "engine"
    assert result.target_applicability.target.product_type == "Engine"


def test_scenario_04_propeller_applicability_remains_component_specific(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    _create_verified_entry(
        db_session,
        aircraft=aircraft,
        user=demo_data["owner_user"],
        section_key="propeller",
        entry_date=date(2026, 1, 4),
        text="Complied with AD 2026-04-01 by inspecting the McCauley propeller.",
    )
    _approved_ad(
        db_session,
        ad_number="2026-04-01",
        product="McCauley 1A170 Propellers",
        action="Inspect the propeller.",
    )
    _import_drs_row(
        db_session,
        ad_number="2026-04-01",
        product_type="Propeller",
        make="McCauley",
        model="1A170",
    )
    db_session.commit()

    match_aircraft_ads(db_session, aircraft.id)
    result = db_session.scalar(
        select(ADMatchResult).where(ADMatchResult.status == "candidate_satisfied")
    )
    assert result is not None
    assert result.installed_component.role == "propeller"
    assert result.target_applicability.target.product_type == "Propeller"


def test_scenario_05_recurring_ad_requires_adjudication(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    _create_verified_entry(
        db_session,
        aircraft=aircraft,
        user=demo_data["owner_user"],
        section_key="airframe",
        entry_date=date(2026, 1, 5),
        text="Complied with recurring AD 2026-05-01 by inspecting the seat rails.",
    )
    _approved_ad(
        db_session,
        ad_number="2026-05-01",
        product="Cessna 172R Airplanes",
        action="Inspect seat rails every 100 tach hours.",
        intervals=[{"type": "tach_hours", "intervalHours": 100}],
    )
    db_session.commit()

    match_aircraft_ads(db_session, aircraft.id)
    result = db_session.scalar(select(ADMatchResult))
    assert result is not None
    assert result.status == "needs_adjudication"
    assert "recurring_due_status_unknown" in result.unresolved_reasons
    assert result.adjudication.status == "pending"


def test_scenario_06_superseded_ad_cannot_be_cleanly_satisfied(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    _create_verified_entry(
        db_session,
        aircraft=aircraft,
        user=demo_data["owner_user"],
        section_key="airframe",
        entry_date=date(2026, 1, 6),
        text="Complied with AD 2026-06-01 by inspection.",
    )
    old = _approved_ad(
        db_session,
        ad_number="2026-06-01",
        product="Cessna 172R Airplanes",
        action="Inspect the elevator.",
    )
    new = _approved_ad(
        db_session,
        ad_number="2026-06-02",
        product="Cessna 172R Airplanes",
        action="Inspect and replace the elevator fitting.",
    )
    db_session.add(
        ADSupersession(
            superseding_ad_id=new.directive_id,
            superseded_ad_id=old.directive_id,
            relationship_type="supersedes",
            evidence_text="AD 2026-06-02 supersedes AD 2026-06-01.",
            confidence=0.99,
        )
    )
    db_session.commit()

    match_aircraft_ads(db_session, aircraft.id)
    old_result = db_session.scalar(
        select(ADMatchResult).where(ADMatchResult.directive_id == old.directive_id)
    )
    assert old_result is not None
    assert old_result.status == "needs_adjudication"
    assert "directive_superseded" in old_result.unresolved_reasons
    assert old_result.evidence_links


def test_scenario_07_missing_evidence_creates_pending_review(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    extraction = _approved_ad(
        db_session,
        ad_number="2026-07-01",
        product="Cessna 172R Airplanes",
        action="Inspect the rudder.",
    )
    db_session.commit()

    match_aircraft_ads(db_session, aircraft.id)
    result = db_session.scalar(
        select(ADMatchResult).where(
            ADMatchResult.directive_id == extraction.directive_id
        )
    )
    assert result is not None
    assert result.status == "needs_adjudication"
    assert result.evidence_links == []
    assert db_session.scalar(
        select(ADMatchAdjudication).where(
            ADMatchAdjudication.match_result_id == result.id,
            ADMatchAdjudication.status == "pending",
        )
    ) is not None


def test_scenario_08_unverified_claim_is_excluded_from_matching(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    _create_verified_entry(
        db_session,
        aircraft=aircraft,
        user=demo_data["owner_user"],
        section_key="airframe",
        entry_date=date(2026, 1, 8),
        text="Complied with AD 2026-08-01 by inspection.",
        review_status="needs_review",
    )
    extraction = _approved_ad(
        db_session,
        ad_number="2026-08-01",
        product="Cessna 172R Airplanes",
        action="Inspect the airframe.",
    )
    db_session.commit()

    match_aircraft_ads(db_session, aircraft.id)
    result = db_session.scalar(
        select(ADMatchResult).where(
            ADMatchResult.directive_id == extraction.directive_id
        )
    )
    assert result is not None
    assert result.status == "needs_adjudication"
    assert result.evidence_links == []


def test_scenario_09_degraded_drs_source_is_exposed_at_worklist_boundary(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    _approved_ad(
        db_session,
        ad_number="2026-09-01",
        product="Cessna 172R Airplanes",
        action="Inspect the airframe.",
    )
    upsert_snapshot(
        db_session,
        source_type="bulk_access",
        source_url="https://drs.faa.gov/controlled",
        filename="controlled-partial.accdb",
        content_hash="9" * 64,
        captured_at=datetime.now(timezone.utc),
        row_count=1,
        table_inventory={"rows": 1},
        metadata={"fixture": True, "reason": "controlled_partial"},
        status="partial",
        storage_bytes=100,
    )
    db_session.commit()
    match_aircraft_ads(db_session, aircraft.id)

    login(client, "owner.test@paprnav.local")
    response = client.get(f"/api/v1/ads/aircraft/{aircraft.id}/matches")
    assert response.status_code == 200
    payload = response.json()
    assert payload["matcherStatus"] == "current"
    assert payload["coverageStatus"] == "degraded"
    assert payload["coverageWarnings"]
    assert any(
        "may be incomplete" in warning or "unverified" in warning
        for warning in payload["coverageWarnings"]
    )
    assert any(
        target["status"] == "degraded_source"
        for target in payload["coverageTargets"]
    )


def test_scenario_10_second_client_reuses_coverage_and_cost_scopes(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    first_aircraft = demo_data["aircraft"]
    rows = [
        {
            "adNumber": "2026-10-01",
            "Subject": "Airworthiness Directives; Cessna 172R Airplanes",
            "ProductType": "Aircraft",
            "Make": "Cessna",
            "Model": "172R",
            "Status": "Current",
            "Identifier": "DRS-2026-10-01",
        },
        {
            "adNumber": "2026-10-02",
            "Subject": "Airworthiness Directives; Lycoming IO-360-L2A Engines",
            "ProductType": "Engine",
            "Make": "Lycoming",
            "Model": "IO-360-L2A",
            "Status": "Current",
            "Identifier": "DRS-2026-10-02",
        },
        {
            "adNumber": "2026-10-03",
            "Subject": "Airworthiness Directives; McCauley 1A170 Propellers",
            "ProductType": "Propeller",
            "Make": "McCauley",
            "Model": "1A170",
            "Status": "Current",
            "Identifier": "DRS-2026-10-03",
        },
    ]
    import_drs_bulk_rows(
        db_session,
        rows,
        filename="controlled-reuse.accdb",
        content_hash="a" * 64,
    )
    first_stats = resolve_aircraft_ad_coverage(db_session, first_aircraft.id)

    second_user = create_user(
        db_session,
        "readiness.second@paprnav.local",
        "Second Readiness Owner",
    )
    second_org = create_organization(
        db_session,
        "Second Readiness Hangar",
        "owner",
    )
    add_membership(db_session, second_org, second_user, "owner_admin")
    second_aircraft = create_aircraft(
        db_session,
        second_org,
        second_user,
        n_number="N210RD",
    )
    second_stats = resolve_aircraft_ad_coverage(db_session, second_aircraft.id)
    match_aircraft_ads(db_session, first_aircraft.id)
    match_aircraft_ads(db_session, second_aircraft.id)
    db_session.commit()

    assert first_stats["coverage_sets_created"] == 3
    assert second_stats["coverage_sets_created"] == 0
    assert second_stats["coverage_sets_reused"] == 3
    assert db_session.scalar(select(func.count()).select_from(ADSourceSnapshot)) == 1
    assert db_session.scalar(select(func.count()).select_from(ADCoverageSet)) == 3
    subscriptions = db_session.scalars(select(ADCoverageSubscription)).all()
    assert len(subscriptions) == 6
    assert sum(item.triggered_creation for item in subscriptions) == 3

    ledger = db_session.scalars(select(ADCostLedgerEntry)).all()
    assert {"shared_source", "coverage_set", "aircraft"}.issubset(
        {entry.scope_type for entry in ledger}
    )
    assert all(entry.allocated_cost_usd == 0 for entry in ledger)
    assert all(
        entry.attribution_status
        in {"platform_shared_unallocated", "informational_unallocated"}
        for entry in ledger
    )
    assert all(
        entry.metadata_json is None
        or entry.metadata_json.get("billingActive") is False
        for entry in ledger
    )
