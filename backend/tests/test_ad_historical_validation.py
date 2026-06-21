import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ADReconciliationIssue, AirworthinessDirective
from app.services.ad_historical_validation import record_pre1994_validation_issues


def test_pre1994_validation_report_opens_issues_for_ambiguous_samples(db_session: Session) -> None:
    directive = AirworthinessDirective(
        discovery_record_id=None,
        ad_number="1992-26-01",
        title="Historical PA-28 sample",
        status="current",
        source_content_hash="b" * 64,
        extraction_status="not_started",
        review_status="not_started",
    )
    db_session.add(directive)
    db_session.flush()

    fixture_path = Path(__file__).parent / "fixtures" / "drs" / "pre1994_historical_validation.sample.json"
    report = json.loads(fixture_path.read_text())
    stats = record_pre1994_validation_issues(db_session, report)
    db_session.commit()

    assert stats == {"samples_seen": 3, "issues_opened": 2, "matched": 1}
    issues = db_session.scalars(select(ADReconciliationIssue).order_by(ADReconciliationIssue.issue_type)).all()
    assert [issue.issue_type for issue in issues] == [
        "pre1994_validation_historical_source_unavailable",
        "pre1994_validation_snapshot_unparseable",
    ]
    linked_issue = next(issue for issue in issues if issue.issue_type == "pre1994_validation_snapshot_unparseable")
    assert linked_issue.directive_id == directive.id
    assert linked_issue.payload["targetQuery"]["model"] == "PA-28-180"

