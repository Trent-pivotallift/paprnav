from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.core import IngestionJob, OCRRun, UserFeedback, WorkflowStatusEvent
from app.services.pilot_achievements import (
    PILOT_ACHIEVEMENT_TAXONOMY,
    project_pilot_achievements,
)


ZERO = Decimal("0")
_FAILURE_STATUSES = {"failed", "error"}
_FEEDBACK_TYPES = {"bug", "demo_note", "feature_request", "support", "usability"}
_FEEDBACK_SEVERITIES = {"low", "medium", "high", "critical"}
_FEEDBACK_STATUSES = {"open", "triaged", "closed"}
_BILLING_STATUSES = {"chargeable", "not_billable", "credited", "disputed"}


def summarize_pilot(
    db: Session,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    actor_user_id: str | None = None,
    recent_limit: int = 25,
) -> dict[str, Any]:
    counts, recent = project_pilot_achievements(
        db,
        date_from=date_from,
        date_to=date_to,
        actor_user_id=actor_user_id,
        recent_limit=recent_limit,
    )
    return {
        "generatedAt": datetime.now(timezone.utc),
        "dateFrom": date_from,
        "dateTo": date_to,
        "actorUserId": actor_user_id,
        "achievements": {
            "taxonomyVersion": PILOT_ACHIEVEMENT_TAXONOMY,
            "identityCount": sum(counts.values()),
            "counts": counts,
            "recent": [
                {
                    "id": row.id,
                    "eventType": row.event_type,
                    "subjectType": row.subject_type,
                    "subjectId": row.subject_id,
                    "actorUserId": row.actor_user_id,
                    "organizationId": row.organization_id,
                    "aircraftId": row.aircraft_id,
                    "eventTime": row.event_time,
                }
                for row in recent
            ],
        },
        "failures": _summarize_failures(
            db,
            date_from=date_from,
            date_to=date_to,
            actor_user_id=actor_user_id,
            recent_limit=recent_limit,
        ),
        "feedback": _summarize_feedback(
            db,
            date_from=date_from,
            date_to=date_to,
            actor_user_id=actor_user_id,
            recent_limit=recent_limit,
        ),
        "ocr": _summarize_recorded_ocr_runs(
            db,
            date_from=date_from,
            date_to=date_to,
            actor_user_id=actor_user_id,
        ),
    }


def _summarize_failures(
    db: Session,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    actor_user_id: str | None,
    recent_limit: int,
) -> dict[str, Any]:
    statement = select(WorkflowStatusEvent).order_by(
        WorkflowStatusEvent.created_at.desc(),
        WorkflowStatusEvent.id.desc(),
    )
    if date_from is not None:
        statement = statement.where(WorkflowStatusEvent.created_at >= date_from)
    if date_to is not None:
        statement = statement.where(WorkflowStatusEvent.created_at < date_to)
    if actor_user_id is not None:
        statement = statement.where(WorkflowStatusEvent.actor_user_id == actor_user_id)
    workflow_records = [
        {
            "id": row.id,
            "workflowType": _bounded_category(row.workflow_type),
            "workflowId": row.workflow_id,
            "category": f"workflow_{_failure_category(row.new_status)}",
            "createdAt": row.created_at,
        }
        for row in db.scalars(statement).all()
        if _failure_category(row.new_status) is not None
    ]
    job_statement = select(IngestionJob).where(IngestionJob.status == "failed")
    if date_from is not None:
        job_statement = job_statement.where(IngestionJob.created_at >= date_from)
    if date_to is not None:
        job_statement = job_statement.where(IngestionJob.created_at < date_to)
    if actor_user_id is not None:
        job_statement = job_statement.where(IngestionJob.created_by_user_id == actor_user_id)
    job_records = [
        {
            "id": row.id,
            "workflowType": "upload_ingestion",
            "workflowId": row.id,
            "category": _ingestion_failure_category(row.error_code),
            "createdAt": row.created_at,
        }
        for row in db.scalars(job_statement).all()
    ]
    records = sorted(
        workflow_records + job_records,
        key=lambda item: (item["createdAt"], item["id"]),
        reverse=True,
    )
    categories = Counter(record["category"] for record in records)
    return {
        "count": len(records),
        "counts": dict(sorted(categories.items())),
        "recent": records[:recent_limit],
    }


def _summarize_feedback(
    db: Session,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    actor_user_id: str | None,
    recent_limit: int,
) -> dict[str, Any]:
    statement = select(UserFeedback).order_by(
        UserFeedback.created_at.desc(),
        UserFeedback.id.desc(),
    )
    if date_from is not None:
        statement = statement.where(UserFeedback.created_at >= date_from)
    if date_to is not None:
        statement = statement.where(UserFeedback.created_at < date_to)
    if actor_user_id is not None:
        statement = statement.where(UserFeedback.submitted_by_user_id == actor_user_id)
    rows = list(db.scalars(statement).all())
    type_counts = Counter(_known_category(row.feedback_type, _FEEDBACK_TYPES) for row in rows)
    severity_counts = Counter(_known_category(row.severity, _FEEDBACK_SEVERITIES) for row in rows)
    status_counts = Counter(_known_category(row.status, _FEEDBACK_STATUSES) for row in rows)
    return {
        "count": len(rows),
        "typeCounts": dict(sorted(type_counts.items())),
        "severityCounts": dict(sorted(severity_counts.items())),
        "statusCounts": dict(sorted(status_counts.items())),
        "recent": [
            {
                "id": row.id,
                "feedbackType": _known_category(row.feedback_type, _FEEDBACK_TYPES),
                "severity": _known_category(row.severity, _FEEDBACK_SEVERITIES),
                "status": _known_category(row.status, _FEEDBACK_STATUSES),
                "organizationId": row.organization_id,
                "aircraftId": row.aircraft_id,
                "createdAt": row.created_at,
            }
            for row in rows[:recent_limit]
        ],
    }


def _summarize_recorded_ocr_runs(
    db: Session,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    actor_user_id: str | None,
) -> dict[str, Any]:
    statement = (
        select(OCRRun)
        .options(
            selectinload(OCRRun.ingestion_job).selectinload(IngestionJob.aircraft),
        )
        .order_by(OCRRun.created_at.asc(), OCRRun.id.asc())
    )
    if date_from is not None:
        statement = statement.where(OCRRun.created_at >= date_from)
    if date_to is not None:
        statement = statement.where(OCRRun.created_at < date_to)
    if actor_user_id is not None:
        statement = statement.join(OCRRun.ingestion_job).where(
            IngestionJob.created_by_user_id == actor_user_id
        )
    runs = list(db.scalars(statement).all())

    lifecycle = Counter(_lifecycle(run.status) for run in runs)
    pricing = Counter("priced" if _estimate(run) is not None else "unpriced" for run in runs)
    attribution = Counter(
        "attributed"
        if run.billable_account_tag and run.billable_aircraft_tag
        else "unattributed"
        for run in runs
    )
    billing = Counter(_known_category(run.billing_status, _BILLING_STATUSES) for run in runs)
    known_estimates = [_estimate(run) for run in runs if _estimate(run) is not None]
    completed_estimates = [
        _estimate(run)
        for run in runs
        if _lifecycle(run.status) == "completed" and _estimate(run) is not None
    ]
    reconciliation_required = sum(
        _requires_reconciliation(run)
        for run in runs
    )
    return {
        "recordedRunsOnly": True,
        "paidAttemptCoverageComplete": False,
        "reconciliationCompletenessAvailable": False,
        "missingRowVisibilityAvailable": False,
        "attributionBasis": "recorded_billing_tags",
        "historicalTagsReattributed": False,
        "recordedRunCount": len(runs),
        "lifecycleCounts": {
            "completed": lifecycle["completed"],
            "failed": lifecycle["failed"],
            "pending": lifecycle["pending"],
        },
        "pricingCounts": {
            "priced": pricing["priced"],
            "unpriced": pricing["unpriced"],
        },
        "attributionCounts": {
            "attributed": attribution["attributed"],
            "unattributed": attribution["unattributed"],
        },
        "billingCounts": {
            "chargeable": billing["chargeable"],
            "not_billable": billing["not_billable"],
            "credited": billing["credited"],
            "disputed": billing["disputed"],
            "other": billing["other"],
        },
        "reconciliationRequiredRunCount": reconciliation_required,
        "knownEstimateRunCount": len(known_estimates),
        "unknownAmountRunCount": len(runs) - len(known_estimates),
        "knownPartialEstimateUsd": sum(known_estimates, ZERO) if known_estimates else None,
        "completedPricedEstimateUsd": (
            sum(completed_estimates, ZERO) if completed_estimates else None
        ),
        # Even when every recorded row is priced, the pre-call crash window
        # means this can only be described as a partial recorded-run estimate.
        "estimateIsPartial": True,
    }


def _estimate(run: OCRRun) -> Decimal | None:
    if run.estimated_cost_usd is not None:
        return Decimal(str(run.estimated_cost_usd))
    if (
        run.pricing_unit == "page"
        and run.pricing_rate_usd is not None
        and run.billable_page_count is not None
    ):
        return Decimal(str(run.pricing_rate_usd)) * max(run.billable_page_count, 0)
    return None


def _lifecycle(status: str | None) -> str:
    normalized = (status or "").strip().lower()
    if normalized in {"complete", "completed", "succeeded", "success"}:
        return "completed"
    if normalized in _FAILURE_STATUSES or "fail" in normalized or "error" in normalized:
        return "failed"
    return "pending"


def _requires_reconciliation(run: OCRRun) -> bool:
    return (
        _lifecycle(run.status) != "completed"
        or _estimate(run) is None
        or not run.billable_account_tag
        or not run.billable_aircraft_tag
        or run.billing_status not in _BILLING_STATUSES
        or run.billing_status == "disputed"
    )


def _failure_category(status: str | None) -> str | None:
    normalized = (status or "").strip().lower()
    if "fail" in normalized:
        return "failed"
    if "error" in normalized:
        return "error"
    return None


def _ingestion_failure_category(error_code: str | None) -> str:
    normalized = (error_code or "").strip().lower()
    if normalized in {"ocr_provider_failed", "upload_missing"}:
        return normalized
    return "ingestion_failed"


def _known_category(value: str | None, allowed: set[str]) -> str:
    normalized = (value or "").strip().lower()
    return normalized if normalized in allowed else "other"


def _bounded_category(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    allowed = {
        "ad_extraction",
        "ad_matching",
        "hitl_adjudication",
        "ocr_correction",
        "page_verification",
        "upload_ingestion",
    }
    return normalized if normalized in allowed else "other"
