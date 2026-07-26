from __future__ import annotations

from statistics import mean, median
from typing import Any

from app.models.core import IngestionJob


REVIEW_METRICS_PROFILE = "evidence-review-metrics-v1"


def calculate_ingestion_review_metrics(job: IngestionJob) -> dict[str, Any]:
    entries = {
        evidence.logbook_entry_id: evidence.logbook_entry
        for evidence in job.evidence_links
        if evidence.logbook_entry is not None
    }
    outcomes = [
        evidence.review_metadata or {}
        for evidence in job.evidence_links
        if evidence.field_name == "review_outcome"
        and evidence.review_metadata is not None
    ]
    durations = [
        float(outcome["reviewElapsedSeconds"])
        for outcome in outcomes
        if isinstance(outcome.get("reviewElapsedSeconds"), (int, float))
    ]
    edit_counts = [
        int(outcome["editedFieldCount"])
        for outcome in outcomes
        if isinstance(outcome.get("editedFieldCount"), (int, float))
    ]
    decisions = [
        decision
        for outcome in outcomes
        for decision in (outcome.get("fieldDecisions") or {}).values()
    ]
    accepted = decisions.count("accepted")
    corrected = decisions.count("corrected")
    null_count = decisions.count("null")
    unresolved = decisions.count("unresolved")
    decided_for_accuracy = accepted + corrected
    verified = sum(entry.review_status == "verified" for entry in entries.values())
    extracted_count = len(entries)
    return {
        "profile": REVIEW_METRICS_PROFILE,
        "ingestionJobId": job.id,
        "extractedEntryCount": extracted_count,
        "reviewedEntryCount": len(outcomes),
        "verifiedEntryCount": verified,
        "verificationRate": round(verified / extracted_count, 6) if extracted_count else 0.0,
        "medianReviewSeconds": round(median(durations), 3) if durations else None,
        "meanEditedFieldCount": round(mean(edit_counts), 3) if edit_counts else None,
        "acceptedFieldAccuracy": (
            round(accepted / decided_for_accuracy, 6)
            if decided_for_accuracy
            else None
        ),
        "acceptedFieldCount": accepted,
        "decidedFieldCount": len(decisions),
        "unresolvedFieldCount": unresolved,
        "nullFieldCount": null_count,
    }
