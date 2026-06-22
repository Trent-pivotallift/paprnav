from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.core import (
    ADExtraction,
    ADPublication,
    ADReconciliationIssue,
    ADSourceSnapshot,
    ADTargetApplicability,
    AirworthinessDirective,
)
from app.services.observability import record_product_event, record_workflow_status

MANAGED_ISSUE_TYPES = {
    "drs_source_degraded",
    "missing_federal_register_match",
    "ad_extraction_missing",
    "ad_extraction_incomplete",
    "applicability_missing",
    "applicability_target_incomplete",
    "target_applicability_stale",
    "supersession_correction_conflict",
}
DEGRADED_SOURCE_STATUSES = {"failed", "stale", "unavailable"}
DEGRADED_APPLICABILITY_STATUSES = {"failed", "stale", "unavailable"}


@dataclass(frozen=True)
class IssueSpec:
    issue_type: str
    severity: str
    payload: dict[str, Any]
    directive_id: str | None = None
    publication_id: str | None = None
    target_id: str | None = None
    aircraft_id: str | None = None
    source_snapshot_id: str | None = None

    def signature(self) -> tuple[str, str | None, str | None, str | None, str | None, str | None]:
        return (
            self.issue_type,
            self.directive_id,
            self.publication_id,
            self.target_id,
            self.aircraft_id,
            self.source_snapshot_id,
        )


def run_ad_reconciliation(db: Session) -> dict[str, int]:
    specs = collect_issue_specs(db)
    stats = {
        "issues_seen": len(specs),
        "issues_opened": 0,
        "issues_updated": 0,
        "issues_unchanged": 0,
        "issues_resolved": 0,
    }
    active_signatures: set[tuple[str, str | None, str | None, str | None, str | None, str | None]] = set()
    for spec in specs:
        active_signatures.add(spec.signature())
        outcome = upsert_issue(db, spec)
        stats[f"issues_{outcome}"] += 1

    stats["issues_resolved"] = resolve_inactive_issues(db, active_signatures)
    record_product_event(
        db,
        event_type="ad_reconciliation_completed",
        subject_type="ad_reconciliation",
        subject_id="batch",
        event_source="worker",
        properties=stats,
    )
    record_workflow_status(
        db,
        workflow_type="ad_reconciliation",
        workflow_id="batch",
        new_status="complete",
        reason=f"open={stats['issues_opened']} updated={stats['issues_updated']} resolved={stats['issues_resolved']}",
        actor_type="worker",
    )
    db.commit()
    return stats


def collect_issue_specs(db: Session) -> list[IssueSpec]:
    specs: list[IssueSpec] = []
    specs.extend(source_snapshot_specs(db))
    directives = db.scalars(
        select(AirworthinessDirective).options(
            selectinload(AirworthinessDirective.publications),
            selectinload(AirworthinessDirective.extractions),
            selectinload(AirworthinessDirective.target_applicabilities).selectinload(ADTargetApplicability.target),
            selectinload(AirworthinessDirective.target_applicabilities).selectinload(ADTargetApplicability.source_publication),
            selectinload(AirworthinessDirective.superseded_by_edges),
            selectinload(AirworthinessDirective.supersedes_edges),
        )
    ).all()
    for directive in directives:
        specs.extend(directive_specs(directive))
    return specs


def source_snapshot_specs(db: Session) -> list[IssueSpec]:
    snapshots = db.scalars(select(ADSourceSnapshot).where(ADSourceSnapshot.status.in_(DEGRADED_SOURCE_STATUSES))).all()
    specs: list[IssueSpec] = []
    for snapshot in snapshots:
        specs.append(
            IssueSpec(
                issue_type="drs_source_degraded",
                severity="high" if snapshot.status in {"failed", "unavailable"} else "medium",
                source_snapshot_id=snapshot.id,
                payload={
                    "sourceSystem": snapshot.source_system,
                    "sourceType": snapshot.source_type,
                    "status": snapshot.status,
                    "filename": snapshot.filename,
                    "contentHash": snapshot.content_hash,
                    "parserName": snapshot.parser_name,
                    "parserVersion": snapshot.parser_version,
                },
            )
        )
    return specs


def directive_specs(directive: AirworthinessDirective) -> list[IssueSpec]:
    specs: list[IssueSpec] = []
    if not has_publication(directive, "federal_register"):
        specs.append(
            IssueSpec(
                issue_type="missing_federal_register_match",
                severity="medium",
                directive_id=directive.id,
                payload={
                    "adNumber": directive.ad_number,
                    "directiveStatus": directive.status,
                    "knownSourceSystems": sorted({publication.source_system for publication in directive.publications}),
                },
            )
        )

    approved_extractions = [extraction for extraction in directive.extractions if extraction.status == "approved"]
    if not directive.extractions:
        specs.append(
            IssueSpec(
                issue_type="ad_extraction_missing",
                severity="medium",
                directive_id=directive.id,
                payload={
                    "adNumber": directive.ad_number,
                    "extractionStatus": directive.extraction_status,
                    "reviewStatus": directive.review_status,
                },
            )
        )
    elif not approved_extractions:
        specs.append(
            IssueSpec(
                issue_type="ad_extraction_incomplete",
                severity="medium",
                directive_id=directive.id,
                payload={
                    "adNumber": directive.ad_number,
                    "extractionStatuses": sorted({extraction.status for extraction in directive.extractions}),
                    "reviewStatus": directive.review_status,
                },
            )
        )

    if not directive.target_applicabilities:
        specs.append(
            IssueSpec(
                issue_type="applicability_missing",
                severity="high",
                directive_id=directive.id,
                payload={"adNumber": directive.ad_number, "sourceSystems": sorted({publication.source_system for publication in directive.publications})},
            )
        )
    for applicability in directive.target_applicabilities:
        target = applicability.target
        if applicability.status in DEGRADED_APPLICABILITY_STATUSES:
            specs.append(
                IssueSpec(
                    issue_type="target_applicability_stale",
                    severity="medium",
                    directive_id=directive.id,
                    publication_id=applicability.source_publication_id,
                    target_id=applicability.target_id,
                    payload={
                        "adNumber": directive.ad_number,
                        "applicabilityStatus": applicability.status,
                        "basis": applicability.applicability_basis,
                    },
                )
            )
        if target and (not target.make or not target.model):
            specs.append(
                IssueSpec(
                    issue_type="applicability_target_incomplete",
                    severity="medium",
                    directive_id=directive.id,
                    publication_id=applicability.source_publication_id,
                    target_id=target.id,
                    payload={
                        "adNumber": directive.ad_number,
                        "productType": target.product_type,
                        "productSubtype": target.product_subtype,
                        "missing": [field for field, value in {"make": target.make, "model": target.model}.items() if not value],
                    },
                )
            )

    specs.extend(publication_conflict_specs(directive))
    return specs


def publication_conflict_specs(directive: AirworthinessDirective) -> list[IssueSpec]:
    has_supersession_edge = bool(directive.superseded_by_edges or directive.supersedes_edges)
    specs: list[IssueSpec] = []
    for publication in directive.publications:
        signals = publication_signals(publication)
        if not signals:
            continue
        if has_supersession_edge and "supersession" in signals:
            continue
        specs.append(
            IssueSpec(
                issue_type="supersession_correction_conflict",
                severity="low",
                directive_id=directive.id,
                publication_id=publication.id,
                payload={
                    "adNumber": directive.ad_number,
                    "sourceSystem": publication.source_system,
                    "sourceType": publication.source_type,
                    "sourceIdentifier": publication.source_identifier,
                    "signals": sorted(signals),
                },
            )
        )
    return specs


def publication_signals(publication: ADPublication) -> set[str]:
    values = [publication.status or "", publication.title or ""]
    metadata = publication.metadata_json or {}
    for key in ["action", "correction", "document_type", "type"]:
        if key in metadata:
            values.append(str(metadata[key]))
    text = " ".join(values).lower()
    signals: set[str] = set()
    if "supersed" in text:
        signals.add("supersession")
    if "correction" in text or "correcting" in text:
        signals.add("correction")
    if "withdraw" in text or "rescinded" in text:
        signals.add("withdrawal")
    return signals


def has_publication(directive: AirworthinessDirective, source_system: str) -> bool:
    return any(publication.source_system == source_system for publication in directive.publications)


def upsert_issue(db: Session, spec: IssueSpec) -> str:
    issue = find_open_issue(db, spec)
    if issue is None:
        issue = ADReconciliationIssue(
            issue_type=spec.issue_type,
            severity=spec.severity,
            status="open",
            directive_id=spec.directive_id,
            publication_id=spec.publication_id,
            target_id=spec.target_id,
            aircraft_id=spec.aircraft_id,
            source_snapshot_id=spec.source_snapshot_id,
            payload=spec.payload,
        )
        db.add(issue)
        db.flush()
        return "opened"

    if issue.severity != spec.severity or issue.payload != spec.payload:
        issue.severity = spec.severity
        issue.payload = spec.payload
        db.flush()
        return "updated"
    return "unchanged"


def find_open_issue(db: Session, spec: IssueSpec) -> ADReconciliationIssue | None:
    return db.scalar(
        select(ADReconciliationIssue).where(
            ADReconciliationIssue.issue_type == spec.issue_type,
            ADReconciliationIssue.status == "open",
            ADReconciliationIssue.directive_id == spec.directive_id,
            ADReconciliationIssue.publication_id == spec.publication_id,
            ADReconciliationIssue.target_id == spec.target_id,
            ADReconciliationIssue.aircraft_id == spec.aircraft_id,
            ADReconciliationIssue.source_snapshot_id == spec.source_snapshot_id,
        )
    )


def resolve_inactive_issues(
    db: Session,
    active_signatures: set[tuple[str, str | None, str | None, str | None, str | None, str | None]],
) -> int:
    resolved = 0
    issues = db.scalars(
        select(ADReconciliationIssue).where(
            ADReconciliationIssue.issue_type.in_(MANAGED_ISSUE_TYPES),
            ADReconciliationIssue.status == "open",
        )
    ).all()
    now = datetime.now(timezone.utc)
    for issue in issues:
        signature = (
            issue.issue_type,
            issue.directive_id,
            issue.publication_id,
            issue.target_id,
            issue.aircraft_id,
            issue.source_snapshot_id,
        )
        if signature in active_signatures:
            continue
        issue.status = "resolved"
        issue.resolved_at = now
        resolved += 1
    db.flush()
    return resolved

