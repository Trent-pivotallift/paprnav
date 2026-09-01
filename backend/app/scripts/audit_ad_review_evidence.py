from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADPublication,
    AirworthinessDirective,
)
from app.services.ad_extraction import (
    bounded_source_document_pages,
    extraction_approval_blockers,
    full_text_pages_for_extraction,
    official_ad_number,
    source_evidence_status,
)


def audit_ad_review_evidence() -> dict[str, Any]:
    """Read every extraction review and classify its retained source identity."""
    with SessionLocal() as db:
        reviews = db.scalars(
            select(ADExtractionReview)
            .options(
                selectinload(ADExtractionReview.extraction)
                .selectinload(ADExtraction.directive)
                .selectinload(AirworthinessDirective.discovery_record),
                selectinload(ADExtractionReview.extraction)
                .selectinload(ADExtraction.directive)
                .selectinload(AirworthinessDirective.publications)
                .selectinload(ADPublication.source_document),
            )
            .order_by(ADExtractionReview.created_at.desc(), ADExtractionReview.id)
        ).all()

        rows: list[dict[str, Any]] = []
        for review in reviews:
            directive = review.extraction.directive
            pages = bounded_source_document_pages(
                full_text_pages_for_extraction(review.extraction),
                ad_number=directive.ad_number,
                title=directive.title,
            )
            evidence_status, evidence_message = source_evidence_status(
                directive.ad_number,
                pages,
            )
            output = review.decision_output or review.proposed_output or {}
            proposed_number = output.get("adNumber")
            normalized_number_matches = (
                not proposed_number
                or str(proposed_number).upper().removeprefix("AD ").strip()
                == (directive.ad_number or "").upper().removeprefix("AD ").strip()
            )
            approval_blockers = extraction_approval_blockers(
                review.extraction,
                output,
                pages,
            )
            rows.append({
                "reviewId": review.id,
                "reviewStatus": review.status,
                "normalizedAdNumber": directive.ad_number,
                "officialAdNumber": official_ad_number(directive.ad_number),
                "title": directive.title,
                "sourceDocumentIds": sorted({
                    str(page["sourceDocumentId"])
                    for page in pages
                    if page.get("sourceDocumentId")
                }),
                "sourcePageNumbers": [page["pageNumber"] for page in pages],
                "evidenceStatus": evidence_status,
                "evidenceMessage": evidence_message,
                "proposedNumberMatches": normalized_number_matches,
                "approvalBlockers": approval_blockers,
                "approvalGatePassed": not approval_blockers,
                "passed": evidence_status == "verified" and normalized_number_matches,
            })

    evidence_counts = Counter(row["evidenceStatus"] for row in rows)
    passed = sum(bool(row["passed"]) for row in rows)
    approval_ready = sum(bool(row["approvalGatePassed"]) for row in rows)
    decided_but_failed = [
        row for row in rows
        if row["reviewStatus"] != "pending" and not row["passed"]
    ]
    return {
        "verification": {
            "passed": passed,
            "total": len(rows),
        },
        "approvalVerification": {
            "passed": approval_ready,
            "total": len(rows),
        },
        "evidenceStatusCounts": dict(sorted(evidence_counts.items())),
        "decidedButFailedCount": len(decided_but_failed),
        "decidedButFailedReviewIds": [row["reviewId"] for row in decided_but_failed],
        "reviews": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit every queued AD extraction review against its formal Part 39 source identity"
    )
    parser.add_argument("--json", action="store_true", help="Print the complete JSON report")
    args = parser.parse_args()

    report = audit_ad_review_evidence()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for row in report["reviews"]:
            pages = ",".join(str(page) for page in row["sourcePageNumbers"]) or "none"
            print(
                f"{row['evidenceStatus']:20} AD {row['officialAdNumber'] or 'unnumbered':12} "
                f"pages={pages:12} {row['title']}"
            )
        print(json.dumps(report["evidenceStatusCounts"], sort_keys=True))
    verification = report["verification"]
    print(f"{verification['passed']} passed out of {verification['total']}")
    approval_verification = report["approvalVerification"]
    print(
        f"{approval_verification['passed']} approval-ready out of "
        f"{approval_verification['total']}"
    )


if __name__ == "__main__":
    main()
