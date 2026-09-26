from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADMatchResult,
    AirworthinessDirective,
    IngestionJob,
    IngestionPage,
    LogbookEntry,
    OCRRun,
    OCRTextSpan,
    ProductEvent,
    Upload,
)
from app.services.ingestion import extract_entries_from_job
from app.services.invitations import create_invitation
from app.services.pilot_achievements import (
    ACHIEVEMENT_SPECS,
    PILOT_ACHIEVEMENT_TAXONOMY,
    project_pilot_achievements,
    record_pilot_achievement,
)
from tests.conftest import (
    TEST_PASSWORD,
    add_membership,
    create_aircraft,
    create_organization,
    create_user,
    login,
)


INVITE_SECRET = "package-d-invitation-secret-at-least-32-bytes"
def _event_count(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(ProductEvent).where(
            ProductEvent.event_source == PILOT_ACHIEVEMENT_TAXONOMY
        )
    ) or 0


def _achievement_events(db: Session, event_type: str) -> list[ProductEvent]:
    return list(
        db.scalars(
            select(ProductEvent).where(
                ProductEvent.event_source == PILOT_ACHIEVEMENT_TAXONOMY,
                ProductEvent.event_type == event_type,
            )
        ).all()
    )


def _add_verified_extraction_job(
    db: Session,
    *,
    aircraft,
    user,
    suffix: str,
) -> IngestionJob:
    upload = Upload(
        aircraft_id=aircraft.id,
        uploaded_by_user_id=user.id,
        original_filename=f"{suffix}.pdf",
        content_type="application/pdf",
        file_size_bytes=100,
        storage_backend="local",
        storage_key=f"fixtures/{suffix}.pdf",
        sha256=suffix.rjust(64, "0"),
        status="processed",
        pilot_consent_accepted=True,
    )
    db.add(upload)
    db.flush()
    job = IngestionJob(
        upload_id=upload.id,
        aircraft_id=aircraft.id,
        created_by_user_id=user.id,
        status="ready_for_entry_extraction",
        page_extraction_status="complete",
        ocr_status="complete",
        verification_status="verified",
        entry_extraction_status="ready",
        logbook_section_key="airframe",
    )
    db.add(job)
    db.flush()
    page = IngestionPage(
        ingestion_job_id=job.id,
        upload_id=upload.id,
        source_page_number=1,
        current_page_order=1,
        page_label="Page 1",
    )
    db.add(page)
    db.flush()
    run = OCRRun(
        ingestion_job_id=job.id,
        provider_name="package_d_test",
        provider_version="1",
        configuration_hash=suffix,
        status="complete",
        billing_status="not_billable",
    )
    db.add(run)
    db.flush()
    db.add(
        OCRTextSpan(
            ocr_run_id=run.id,
            ingestion_page_id=page.id,
            provider_block_id=f"{suffix}-line",
            span_type="LINE",
            text="2026-09-01 Annual inspection completed.",
            confidence=95,
            bbox_left=0.1,
            bbox_top=0.1,
            bbox_width=0.8,
            bbox_height=0.1,
            bbox_units="ratio",
            reading_order=1,
        )
    )
    db.commit()
    return job


def _add_ocr_run(
    db: Session,
    *,
    aircraft,
    user,
    suffix: str,
    status: str,
    billing_status: str,
    account_tag: str | None,
    aircraft_tag: str | None,
    pages: int | None,
    rate: Decimal | None,
) -> OCRRun:
    upload = Upload(
        aircraft_id=aircraft.id,
        uploaded_by_user_id=user.id,
        original_filename=f"{suffix}.pdf",
        content_type="application/pdf",
        file_size_bytes=100,
        storage_backend="local",
        storage_key=f"fixtures/{suffix}.pdf",
        sha256=suffix.rjust(64, "0"),
        status="processed",
        pilot_consent_accepted=True,
    )
    db.add(upload)
    db.flush()
    job = IngestionJob(
        upload_id=upload.id,
        aircraft_id=aircraft.id,
        created_by_user_id=user.id,
        status="processing",
        page_extraction_status="complete",
        ocr_status=status,
        verification_status="not_started",
        entry_extraction_status="not_started",
    )
    db.add(job)
    db.flush()
    run = OCRRun(
        ingestion_job_id=job.id,
        provider_name="test_provider",
        provider_version="1",
        configuration_hash=suffix,
        status=status,
        billing_status=billing_status,
        billable_account_tag=account_tag,
        billable_aircraft_tag=aircraft_tag,
        billable_page_count=pages,
        pricing_unit="page" if pages is not None else None,
        pricing_rate_usd=rate,
    )
    db.add(run)
    db.flush()
    return run


def test_achievement_transaction_projection_and_fixed_properties(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    actor = demo_data["owner_user"]
    aircraft = demo_data["aircraft"]
    assert set(ACHIEVEMENT_SPECS) == {
        "invite_accepted",
        "aircraft_created",
        "upload_received",
        "page_review_completed",
        "logbook_entry_created",
        "ad_review_completed",
    }

    first = record_pilot_achievement(
        db_session,
        event_type="upload_received",
        subject_type="upload",
        subject_id="upl_first",
        actor=actor,
        organization_id=aircraft.owner_organization_id,
        aircraft_id=aircraft.id,
        properties={
            "contentType": "application/pdf",
            "storageBackend": "local",
            "filename": "secret-logbook.pdf",
            "token": "secret",
            "nested": {"raw_text": "maintenance content"},
        },
    )
    db_session.commit()
    assert first.properties_json == {
        "contentType": "application/pdf",
        "storageBackend": "local",
        "taxonomyVersion": PILOT_ACHIEVEMENT_TAXONOMY,
    }
    committed_count = _event_count(db_session)

    record_pilot_achievement(
        db_session,
        event_type="upload_received",
        subject_type="upload",
        subject_id="upl_rolled_back",
        actor=actor,
    )
    db_session.rollback()
    assert _event_count(db_session) == committed_count

    other_actor = create_user(db_session, "achievement.other@paprnav.local", "Other Actor")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    first.event_time = now - timedelta(minutes=3)
    duplicate = record_pilot_achievement(
        db_session,
        event_type="upload_received",
        subject_type="upload",
        subject_id="upl_first",
        actor=other_actor,
    )
    duplicate.event_time = now - timedelta(minutes=2)
    second = record_pilot_achievement(
        db_session,
        event_type="upload_received",
        subject_type="upload",
        subject_id="upl_second",
        actor=other_actor,
    )
    second.event_time = now - timedelta(minutes=1)
    db_session.commit()

    counts, recent = project_pilot_achievements(db_session, recent_limit=1)
    assert counts["upload_received"] == 2
    assert [row.subject_id for row in recent] == ["upl_second"]
    actor_counts, actor_recent = project_pilot_achievements(
        db_session,
        actor_user_id=other_actor.id,
        recent_limit=10,
    )
    assert actor_counts["upload_received"] == 1
    assert [row.subject_id for row in actor_recent] == ["upl_second"]


def test_success_conflict_admin_boundary_and_recorded_cost_categories(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    owner = demo_data["owner_user"]
    aircraft = demo_data["aircraft"]
    second_owner = create_user(db_session, "pilot.second@paprnav.local", "Second Pilot")
    second_org = create_organization(db_session, "Second Pilot Org", "owner")
    add_membership(db_session, second_org, second_owner, "owner_admin")
    second_aircraft = create_aircraft(db_session, second_org, second_owner, n_number="N822PD")
    admin = create_user(db_session, "pilot.admin@paprnav.local", "Pilot Admin")
    admin_org = create_organization(db_session, "Pilot Operations", "platform")
    admin_membership = add_membership(db_session, admin_org, admin, "platform_admin")

    record_pilot_achievement(
        db_session,
        event_type="aircraft_created",
        subject_type="aircraft",
        subject_id=aircraft.id,
        actor=owner,
        organization_id=aircraft.owner_organization_id,
        aircraft_id=aircraft.id,
    )
    record_pilot_achievement(
        db_session,
        event_type="aircraft_created",
        subject_type="aircraft",
        subject_id=second_aircraft.id,
        actor=second_owner,
        organization_id=second_org.id,
        aircraft_id=second_aircraft.id,
    )
    _add_ocr_run(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="priced",
        status="complete",
        billing_status="chargeable",
        account_tag="historical-account",
        aircraft_tag="historical-aircraft",
        pages=2,
        rate=Decimal("0.020"),
    )
    _add_ocr_run(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="failed",
        status="failed",
        billing_status="disputed",
        account_tag=None,
        aircraft_tag=None,
        pages=None,
        rate=None,
    )
    _add_ocr_run(
        db_session,
        aircraft=second_aircraft,
        user=second_owner,
        suffix="pending",
        status="running",
        billing_status="not_billable",
        account_tag="second-account",
        aircraft_tag="second-aircraft",
        pages=1,
        rate=Decimal("0.010"),
    )
    db_session.commit()

    login(client, "owner.test@paprnav.local")
    assert client.get("/api/v1/admin/pilot-summary").status_code == 403
    client.post("/api/v1/auth/logout")
    login(client, "pilot.admin@paprnav.local")
    response = client.get("/api/v1/admin/pilot-summary", params={"recentLimit": 1})
    assert response.status_code == 200
    payload = response.json()
    assert payload["achievements"]["counts"]["aircraft_created"] == 2
    assert len(payload["achievements"]["recent"]) == 1
    assert payload["ocr"] == {
        "recordedRunsOnly": True,
        "paidAttemptCoverageComplete": False,
        "reconciliationCompletenessAvailable": False,
        "missingRowVisibilityAvailable": False,
        "attributionBasis": "recorded_billing_tags",
        "historicalTagsReattributed": False,
        "recordedRunCount": 3,
        "lifecycleCounts": {"completed": 1, "failed": 1, "pending": 1},
        "pricingCounts": {"priced": 2, "unpriced": 1},
        "attributionCounts": {"attributed": 2, "unattributed": 1},
        "billingCounts": {
            "chargeable": 1,
            "not_billable": 1,
            "credited": 0,
            "disputed": 1,
            "other": 0,
        },
        "reconciliationRequiredRunCount": 2,
        "knownEstimateRunCount": 2,
        "unknownAmountRunCount": 1,
        "knownPartialEstimateUsd": 0.05,
        "completedPricedEstimateUsd": 0.04,
        "estimateIsPartial": True,
    }

    admin_membership.status = "revoked"
    db_session.commit()
    assert client.get("/api/v1/admin/pilot-summary").status_code == 403


def test_route_success_points_emit_only_after_canonical_success(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PAPRNAV_INVITE_SIGNING_SECRET", INVITE_SECRET)
    get_settings.cache_clear()
    invitation_code, _ = create_invitation(
        secret=INVITE_SECRET,
        email="package.d.invitee@example.test",
        name="Package D Invitee",
        organization_name="Package D Hangar",
        organization_type="owner",
        role="owner_admin",
    )
    accepted = client.post(
        "/api/v1/auth/invitations/accept",
        json={"invitationCode": invitation_code, "password": TEST_PASSWORD},
    )
    assert accepted.status_code == 201
    invite_events = _achievement_events(db_session, "invite_accepted")
    assert len(invite_events) == 1
    assert invite_events[0].actor_user_id == accepted.json()["user"]["id"]
    assert invite_events[0].subject_id == accepted.json()["user"]["id"]
    replay = client.post(
        "/api/v1/auth/invitations/accept",
        json={"invitationCode": invitation_code, "password": TEST_PASSWORD},
    )
    assert replay.status_code == 404
    assert len(_achievement_events(db_session, "invite_accepted")) == 1

    owner = demo_data["owner_user"]
    aircraft = demo_data["aircraft"]
    login(client, "owner.test@paprnav.local")
    aircraft_payload = {
        "nNumber": "N82PD",
        "make": "Cessna",
        "model": "172R",
        "serialNumber": "D-82",
    }
    created_aircraft = client.post("/api/v1/aircraft", json=aircraft_payload)
    assert created_aircraft.status_code == 201
    aircraft_events = _achievement_events(db_session, "aircraft_created")
    assert len(aircraft_events) == 1
    assert aircraft_events[0].actor_user_id == owner.id
    assert aircraft_events[0].subject_id == created_aircraft.json()["id"]
    assert aircraft_events[0].properties_json == {
        "hasAccountTag": True,
        "hasAircraftTag": True,
        "taxonomyVersion": PILOT_ACHIEVEMENT_TAXONOMY,
    }
    conflict = client.post("/api/v1/aircraft", json=aircraft_payload)
    assert conflict.status_code == 409
    assert len(_achievement_events(db_session, "aircraft_created")) == 1

    rejected_upload = client.post(
        f"/api/v1/aircraft/{aircraft.id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "false"},
        files={"file": ("rejected.pdf", BytesIO(b"rejected"), "application/pdf")},
    )
    assert rejected_upload.status_code == 400
    assert _achievement_events(db_session, "upload_received") == []
    accepted_upload = client.post(
        f"/api/v1/aircraft/{aircraft.id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("accepted.pdf", BytesIO(b"accepted"), "application/pdf")},
    )
    assert accepted_upload.status_code == 201
    upload_events = _achievement_events(db_session, "upload_received")
    assert len(upload_events) == 1
    assert upload_events[0].actor_user_id == owner.id
    assert upload_events[0].subject_id == accepted_upload.json()["upload"]["id"]

    manual_entry = client.post(
        f"/api/v1/aircraft/{aircraft.id}/logbook-entries",
        json={
            "section": "airframe",
            "entryDate": "2026-09-01",
            "description": "Annual inspection completed.",
        },
    )
    assert manual_entry.status_code == 201
    manual_event = _achievement_events(db_session, "logbook_entry_created")[-1]
    assert manual_event.subject_id == manual_entry.json()["id"]
    assert manual_event.actor_user_id == owner.id
    assert manual_event.properties_json["sourceType"] == "manual"

    job_id = accepted_upload.json()["ingestionJob"]["id"]
    job = db_session.get(IngestionJob, job_id)
    job.status = "awaiting_page_review"
    job.page_extraction_status = "complete"
    job.ocr_status = "complete"
    page = IngestionPage(
        ingestion_job_id=job.id,
        upload_id=job.upload_id,
        source_page_number=1,
        current_page_order=1,
        page_label="Page 1",
    )
    db_session.add(page)
    db_session.commit()
    verification_payload = {
        "pages": [{"pageId": page.id, "currentPageOrder": 1}],
        "isOrderConfirmed": True,
        "isComplete": False,
    }
    incomplete = client.post(
        f"/api/v1/ingestion-jobs/{job.id}/page-verification",
        json=verification_payload,
    )
    assert incomplete.status_code == 200
    assert _achievement_events(db_session, "page_review_completed") == []
    verification_payload["isComplete"] = True
    assert client.post(
        f"/api/v1/ingestion-jobs/{job.id}/page-verification",
        json=verification_payload,
    ).status_code == 200
    assert client.post(
        f"/api/v1/ingestion-jobs/{job.id}/page-verification",
        json=verification_payload,
    ).status_code == 200
    page_events = _achievement_events(db_session, "page_review_completed")
    assert len(page_events) == 1
    assert page_events[0].actor_user_id == owner.id
    assert page_events[0].subject_id == job.id


def test_extracted_entry_actor_retry_actorless_and_rollback(
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = demo_data["owner_user"]
    aircraft = demo_data["aircraft"]
    job = _add_verified_extraction_job(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="actor",
    )
    entries = extract_entries_from_job(db_session, job, pilot_actor=owner)
    assert len(entries) == 1
    events = _achievement_events(db_session, "logbook_entry_created")
    assert len(events) == 1
    assert events[0].subject_id == entries[0].id
    assert events[0].actor_user_id == owner.id
    assert events[0].organization_id == aircraft.owner_organization_id
    assert events[0].aircraft_id == aircraft.id

    retried = extract_entries_from_job(
        db_session,
        job,
        pilot_actor=demo_data["shop_user"],
    )
    assert [entry.id for entry in retried] == [entries[0].id]
    events = _achievement_events(db_session, "logbook_entry_created")
    assert len(events) == 1
    assert events[0].actor_user_id == owner.id

    actorless_job = _add_verified_extraction_job(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="actorless",
    )
    actorless_entries = extract_entries_from_job(
        db_session,
        actorless_job,
        pilot_actor=None,
    )
    assert len(actorless_entries) == 1
    assert len(_achievement_events(db_session, "logbook_entry_created")) == 1

    rollback_job = _add_verified_extraction_job(
        db_session,
        aircraft=aircraft,
        user=owner,
        suffix="rollback",
    )
    entry_count_before = db_session.scalar(
        select(func.count()).select_from(LogbookEntry)
    )

    def fail_after_achievement(*args, **kwargs):
        record_pilot_achievement(*args, **kwargs)
        raise RuntimeError("force transaction rollback")

    monkeypatch.setattr(
        "app.services.ingestion.record_pilot_achievement",
        fail_after_achievement,
    )
    with pytest.raises(RuntimeError, match="force transaction rollback"):
        extract_entries_from_job(db_session, rollback_job, pilot_actor=owner)
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(LogbookEntry)) == entry_count_before
    assert len(_achievement_events(db_session, "logbook_entry_created")) == 1


def test_ad_decision_success_rejections_and_conflict_are_transactional(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    match_directive = AirworthinessDirective(
        ad_number="2026-82-00",
        title="Package D match fixture",
        status="accepted",
        source_content_hash="c" * 64,
        extraction_status="complete",
        review_status="approved",
    )
    db_session.add(match_directive)
    db_session.flush()
    match_extraction = ADExtraction(
        directive_id=match_directive.id,
        provider_name="package_d_test",
        provider_version="1",
        schema_version="ad_extraction_v3",
        input_content_hash="b" * 64,
        status="approved",
        confidence=0.9,
        output={"requirements": [], "applicabilityGroups": []},
        raw_response={
            "retainedSourcePagesCached": True,
            "retainedSourcePages": [],
        },
    )
    db_session.add(match_extraction)
    db_session.flush()
    match = ADMatchResult(
        aircraft_id=demo_data["aircraft"].id,
        directive_id=match_directive.id,
        extraction_id=match_extraction.id,
        status="needs_adjudication",
        match_type="unresolved",
        confidence=0.5,
        rationale="Bounded Package D match fixture.",
        unresolved_reasons=["human_review_required"],
        algorithm_name="package_d_test",
        algorithm_version="1",
        input_hash="a" * 64,
        is_current=True,
    )
    db_session.add(match)

    directive = AirworthinessDirective(
        ad_number="2026-82-01",
        title="Package D review fixture",
        status="candidate",
        source_content_hash="d" * 64,
        extraction_status="needs_review",
        review_status="pending",
    )
    db_session.add(directive)
    db_session.flush()
    extraction = ADExtraction(
        directive_id=directive.id,
        provider_name="package_d_test",
        provider_version="1",
        schema_version="ad_extraction_v3",
        input_content_hash="e" * 64,
        status="needs_review",
        confidence=0.5,
        output={"requirements": [], "applicabilityGroups": []},
        raw_response={
            "retainedSourcePagesCached": True,
            "retainedSourcePages": [],
        },
    )
    db_session.add(extraction)
    db_session.flush()
    review = ADExtractionReview(
        extraction_id=extraction.id,
        status="pending",
        proposed_output=extraction.output,
    )
    db_session.add(review)
    admin = create_user(db_session, "package.d.admin@example.test", "Package D Admin")
    admin_org = create_organization(db_session, "Package D Operations", "platform")
    add_membership(db_session, admin_org, admin, "platform_admin")
    db_session.commit()

    login(client, "owner.test@paprnav.local")
    owner_match_decision = client.post(
        f"/api/v1/ads/matches/{match.id}/adjudication",
        json={
            "decision": "needs_more_info",
            "notes": "Owner must not adjudicate.",
            "futureImprovementTags": [],
        },
    )
    assert owner_match_decision.status_code == 403
    assert _achievement_events(db_session, "ad_review_completed") == []

    login(client, "shop.test@paprnav.local")
    match_decision = client.post(
        f"/api/v1/ads/matches/{match.id}/adjudication",
        json={
            "decision": "needs_more_info",
            "notes": "Need additional evidence.",
            "futureImprovementTags": ["evidence_gap"],
        },
    )
    assert match_decision.status_code == 200
    match_events = _achievement_events(db_session, "ad_review_completed")
    assert len(match_events) == 1
    assert match_events[0].actor_user_id == demo_data["shop_user"].id
    assert match_events[0].subject_type == "ad_match_adjudication"
    assert match_events[0].properties_json["decisionKind"] == "aircraft_match"

    login(client, "owner.test@paprnav.local")
    unauthorized = client.post(
        f"/api/v1/ads/extraction-reviews/{review.id}/decision",
        json={"decision": "rejected"},
    )
    assert unauthorized.status_code == 403
    assert len(_achievement_events(db_session, "ad_review_completed")) == 1

    login(client, admin.email)
    invalid = client.post(
        f"/api/v1/ads/extraction-reviews/{review.id}/decision",
        json={"decision": "unsupported"},
    )
    assert invalid.status_code == 422
    assert len(_achievement_events(db_session, "ad_review_completed")) == 1

    rejected = client.post(
        f"/api/v1/ads/extraction-reviews/{review.id}/decision",
        json={"decision": "rejected", "notes": "Human review completed."},
    )
    assert rejected.status_code == 200
    ad_events = _achievement_events(db_session, "ad_review_completed")
    assert len(ad_events) == 2
    extraction_event = next(
        event for event in ad_events if event.subject_type == "ad_extraction_review"
    )
    assert extraction_event.actor_user_id == admin.id
    assert extraction_event.subject_id == review.id
    assert extraction_event.properties_json["decision"] == "rejected"

    conflict = client.post(
        f"/api/v1/ads/extraction-reviews/{review.id}/decision",
        json={"decision": "approved"},
    )
    assert conflict.status_code == 409
    assert len(_achievement_events(db_session, "ad_review_completed")) == 2


def test_static_budget_and_worker_gates():
    root = Path(__file__).resolve().parents[2]
    terraform_main = (root / "infra/terraform/main.tf").read_text(encoding="utf-8")
    terraform_vars = (root / "infra/terraform/variables.tf").read_text(encoding="utf-8")
    terraform_ecs = (root / "infra/terraform/ecs_runtime.tf").read_text(encoding="utf-8")
    assert 'variable "budget_notification_email"' in terraform_vars
    assert "no repository default" in terraform_vars
    assert "!endswith(var.budget_notification_email, \".invalid\")" in terraform_main
    assert "subscriber_email_addresses = [var.budget_notification_email]" in terraform_main
    assert 'resource "aws_scheduler_schedule" "worker"' in terraform_ecs
    assert 'state               = "DISABLED"' in terraform_ecs
