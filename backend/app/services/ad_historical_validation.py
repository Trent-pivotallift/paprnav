from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ADReconciliationIssue, AirworthinessDirective
from app.services.ad_identity import normalize_ad_number

VALIDATION_VERSION = "pre1994_historical_validation_v1"
ISSUE_BY_STATUS = {
    "missing": "pre1994_validation_missing",
    "ambiguous": "pre1994_validation_ambiguous",
    "snapshot_unparseable": "pre1994_validation_snapshot_unparseable",
    "historical_source_unavailable": "pre1994_validation_historical_source_unavailable",
}


def record_pre1994_validation_issues(db: Session, report: dict[str, Any]) -> dict[str, int]:
    if report.get("validationVersion") != VALIDATION_VERSION:
        raise ValueError(f"Unsupported pre-1994 validation report version: {report.get('validationVersion')}")

    stats = {"samples_seen": 0, "issues_opened": 0, "matched": 0}
    for sample in report.get("samples") or []:
        stats["samples_seen"] += 1
        status = str(sample.get("status") or "ambiguous")
        if status == "matched":
            stats["matched"] += 1
            continue

        issue_type = ISSUE_BY_STATUS.get(status, "pre1994_validation_ambiguous")
        ad_number = normalize_ad_number(sample.get("adNumber"))
        directive = db.scalar(select(AirworthinessDirective).where(AirworthinessDirective.ad_number == ad_number)) if ad_number else None
        issue = db.scalar(
            select(ADReconciliationIssue).where(
                ADReconciliationIssue.issue_type == issue_type,
                ADReconciliationIssue.directive_id == (directive.id if directive else None),
                ADReconciliationIssue.status == "open",
            )
        )
        payload = {
            "validationVersion": VALIDATION_VERSION,
            "adNumber": ad_number,
            "sampleId": sample.get("sampleId"),
            "status": status,
            "targetQuery": sample.get("targetQuery"),
            "drsWebUiSnapshot": sample.get("drsWebUiSnapshot"),
            "historicalSources": sample.get("historicalSources") or [],
            "notes": sample.get("notes"),
        }
        if issue is None:
            issue = ADReconciliationIssue(
                issue_type=issue_type,
                severity=severity_for_status(status),
                directive_id=directive.id if directive else None,
                payload=payload,
            )
            db.add(issue)
            stats["issues_opened"] += 1
        else:
            issue.payload = payload
            issue.severity = severity_for_status(status)
    db.flush()
    return stats


def severity_for_status(status: str) -> str:
    if status == "missing":
        return "high"
    if status in {"snapshot_unparseable", "historical_source_unavailable"}:
        return "medium"
    return "low"

