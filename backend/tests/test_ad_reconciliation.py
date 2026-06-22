from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    ADExtraction,
    ADPublication,
    ADReconciliationIssue,
    ADSourceSnapshot,
    ADTargetApplicability,
    AirworthinessDirective,
    ApplicabilityTarget,
    ProductEvent,
    WorkflowStatusEvent,
)
from app.services.ad_reconciliation import run_ad_reconciliation


def test_ad_reconciliation_worker_is_idempotent_and_resolves_repaired_issues(db_session: Session) -> None:
    snapshot = ADSourceSnapshot(
        source_system="drs",
        source_type="bulk_rows",
        content_hash="c" * 64,
        filename="ADFinalRulesEmergencyADs_fixture.accdb",
        status="failed",
        parser_name="fixture",
        parser_version="0.1.0",
        row_count=0,
        table_inventory={},
        metadata_json={"error": "fixture failure"},
    )
    directive = AirworthinessDirective(
        discovery_record_id=None,
        ad_number="1993-01-01",
        title="Historical sample",
        status="current",
        source_content_hash="c" * 64,
        extraction_status="not_started",
        review_status="not_started",
    )
    db_session.add_all([snapshot, directive])
    db_session.commit()

    first_stats = run_ad_reconciliation(db_session)
    assert first_stats["issues_opened"] == 4
    assert first_stats["issues_resolved"] == 0

    second_stats = run_ad_reconciliation(db_session)
    assert second_stats["issues_opened"] == 0
    assert second_stats["issues_unchanged"] == 4

    issues = db_session.scalars(select(ADReconciliationIssue).where(ADReconciliationIssue.status == "open")).all()
    assert {issue.issue_type for issue in issues} == {
        "ad_extraction_missing",
        "applicability_missing",
        "drs_source_degraded",
        "missing_federal_register_match",
    }
    assert all("raw_text" not in str(issue.payload).lower() for issue in issues)

    snapshot.status = "complete"
    fr_publication = ADPublication(
        directive_id=directive.id,
        source_system="federal_register",
        source_type="rule",
        source_identifier="1993-00001",
        status="current",
        metadata_json={"document_number": "1993-00001"},
    )
    target = ApplicabilityTarget(
        product_type="Aircraft",
        product_subtype=None,
        make="Cessna",
        model="172R",
        normalized_key="aircraft||cessna|172r",
    )
    db_session.add_all([fr_publication, target])
    db_session.flush()
    db_session.add(
        ADTargetApplicability(
            directive_id=directive.id,
            target_id=target.id,
            source_publication_id=fr_publication.id,
            applicability_basis="fixture",
            compliance_actions=[],
            compliance_intervals=[],
            conditions=[],
            citations=[],
            confidence=0.9,
            status="current",
        )
    )
    db_session.add(
        ADExtraction(
            directive_id=directive.id,
            provider_name="fixture",
            provider_version="0.1.0",
            schema_version="ad_extraction_v1",
            input_content_hash="c" * 64,
            status="approved",
            confidence=0.9,
            output={"adNumber": "1993-01-01", "affectedProducts": ["Cessna 172R"]},
            citations=[],
            raw_response={},
        )
    )
    db_session.commit()

    repaired_stats = run_ad_reconciliation(db_session)
    assert repaired_stats["issues_opened"] == 0
    assert repaired_stats["issues_resolved"] == 4
    assert db_session.scalar(select(ADReconciliationIssue).where(ADReconciliationIssue.status == "open")) is None
    assert len(db_session.scalars(select(ADReconciliationIssue).where(ADReconciliationIssue.status == "resolved")).all()) == 4

    event = db_session.scalar(select(ProductEvent).where(ProductEvent.event_type == "ad_reconciliation_completed").order_by(ProductEvent.created_at.desc()))
    assert event is not None
    assert "raw_text" not in str(event.properties_json).lower()
    workflow_event = db_session.scalar(select(WorkflowStatusEvent).where(WorkflowStatusEvent.workflow_type == "ad_reconciliation"))
    assert workflow_event is not None


def test_ad_reconciliation_worker_flags_incomplete_targets_and_publication_conflicts(db_session: Session) -> None:
    directive = AirworthinessDirective(
        discovery_record_id=None,
        ad_number="2026-99-01",
        title="Correction sample",
        status="current",
        source_content_hash="d" * 64,
        extraction_status="complete",
        review_status="approved",
    )
    db_session.add(directive)
    db_session.flush()
    publication = ADPublication(
        directive_id=directive.id,
        source_system="federal_register",
        source_type="rule",
        source_identifier="2026-99001",
        title="Correction; Airworthiness Directives",
        status="current",
        metadata_json={"action": "Correction"},
    )
    target = ApplicabilityTarget(
        product_type="Engine",
        product_subtype=None,
        make="Lycoming",
        model=None,
        normalized_key="engine||lycoming|",
    )
    db_session.add_all([publication, target])
    db_session.flush()
    db_session.add(
        ADTargetApplicability(
            directive_id=directive.id,
            target_id=target.id,
            source_publication_id=publication.id,
            applicability_basis="fixture",
            compliance_actions=[],
            compliance_intervals=[],
            conditions=[],
            citations=[],
            confidence=0.8,
            status="stale",
        )
    )
    db_session.add(
        ADExtraction(
            directive_id=directive.id,
            provider_name="fixture",
            provider_version="0.1.0",
            schema_version="ad_extraction_v1",
            input_content_hash="d" * 64,
            status="approved",
            confidence=0.9,
            output={"adNumber": "2026-99-01", "affectedProducts": ["Lycoming"]},
            citations=[],
            raw_response={},
        )
    )
    db_session.commit()

    stats = run_ad_reconciliation(db_session)

    assert stats["issues_opened"] == 3
    issue_types = {
        issue.issue_type
        for issue in db_session.scalars(select(ADReconciliationIssue).where(ADReconciliationIssue.status == "open")).all()
    }
    assert issue_types == {
        "applicability_target_incomplete",
        "supersession_correction_conflict",
        "target_applicability_stale",
    }

