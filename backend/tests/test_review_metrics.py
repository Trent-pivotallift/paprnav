from types import SimpleNamespace

from app.services.review_metrics import calculate_ingestion_review_metrics


def test_review_metrics_are_derived_from_evidence_outcomes() -> None:
    first = SimpleNamespace(id="entry_1", review_status="verified")
    second = SimpleNamespace(id="entry_2", review_status="needs_review")
    job = SimpleNamespace(
        id="job_metrics",
        evidence_links=[
            SimpleNamespace(
                logbook_entry_id="entry_1",
                logbook_entry=first,
                field_name="entry_date",
                review_metadata=None,
            ),
            SimpleNamespace(
                logbook_entry_id="entry_2",
                logbook_entry=second,
                field_name="description",
                review_metadata=None,
            ),
            SimpleNamespace(
                logbook_entry_id="entry_1",
                logbook_entry=first,
                field_name="review_outcome",
                review_metadata={
                    "reviewElapsedSeconds": 20.0,
                    "editedFieldCount": 1,
                    "fieldDecisions": {
                        "entry_date": "accepted",
                        "description": "corrected",
                        "total_time": "null",
                    },
                },
            ),
        ],
    )

    metrics = calculate_ingestion_review_metrics(job)

    assert metrics["extractedEntryCount"] == 2
    assert metrics["reviewedEntryCount"] == 1
    assert metrics["verifiedEntryCount"] == 1
    assert metrics["verificationRate"] == 0.5
    assert metrics["medianReviewSeconds"] == 20.0
    assert metrics["meanEditedFieldCount"] == 1
    assert metrics["acceptedFieldAccuracy"] == 0.5
    assert metrics["nullFieldCount"] == 1
