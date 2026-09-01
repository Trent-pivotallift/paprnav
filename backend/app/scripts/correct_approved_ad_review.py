from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    ADAMOCProvision,
    ADComplianceRequirement,
    ADTargetApplicability,
    ADCoverageSet,
    AircraftADDueState,
    ADMatchResult,
    ADPublication,
    AirworthinessDirective,
    User,
)
from app.services.ad_extraction import (
    bounded_source_document_pages,
    derive_compliance_action_summaries,
    ensure_persisted_source_pages,
    extraction_approval_blockers,
)
from app.services.ad_matching import invalidate_aircraft_match_results
from app.services.observability import record_product_event, record_workflow_status


def load_patch(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {"requirements": payload}
    if isinstance(payload, dict):
        return payload
    raise SystemExit("Correction input must be a JSON object or a top-level requirements array")


def stable_output_hash(output: dict) -> str:
    serialized = json.dumps(output, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def supersede_amoc_provisions_statement(extraction_id: str):
    """Build the PostgreSQL-safe AMOC revocation used by correction staging."""

    return (
        update(ADAMOCProvision)
        .where(
            ADAMOCProvision.source_extraction_id == extraction_id,
            ADAMOCProvision.status == "current",
        )
        .values(status="superseded")
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage a correction to an approved AD review and require a new human decision"
    )
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--actor-user-id", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    correction_patch = load_patch(args.input)
    corrected_at = datetime.now(timezone.utc)
    with SessionLocal() as db:
        actor = db.scalar(
            select(User)
            .where(User.id == args.actor_user_id)
            .options(selectinload(User.memberships))
        )
        if actor is None or actor.status != "active" or not any(
            membership.status == "active" and membership.role == "platform_admin"
            for membership in actor.memberships
        ):
            raise SystemExit("An active Paprnav platform administrator actor is required")
        review = db.scalar(
            select(ADExtractionReview)
            .where(ADExtractionReview.id == args.review_id)
            .options(
                selectinload(ADExtractionReview.extraction)
                .selectinload(ADExtraction.directive)
                .selectinload(AirworthinessDirective.discovery_record),
                selectinload(ADExtractionReview.extraction)
                .selectinload(ADExtraction.directive)
                .selectinload(AirworthinessDirective.publications)
                .selectinload(ADPublication.source_document),
            )
        )
        if review is None:
            raise SystemExit(f"AD extraction review {args.review_id} was not found")
        if review.status not in {"approved", "edited"} or review.extraction.status != "approved":
            raise SystemExit("Only an approved extraction review can use the correction workflow")

        prior_output = review.decision_output or review.proposed_output
        corrected_output = derive_compliance_action_summaries(
            {**prior_output, **correction_patch}
        )
        source_pages = bounded_source_document_pages(
            ensure_persisted_source_pages(
                review.extraction.directive,
                review.extraction,
            ),
            ad_number=review.extraction.directive.ad_number,
            title=review.extraction.directive.title,
        )
        blockers = extraction_approval_blockers(
            review.extraction,
            corrected_output,
            source_pages,
        )
        if blockers:
            raise SystemExit(" ".join(blockers))
        if corrected_output == prior_output:
            raise SystemExit("Correction does not change the approved output")

        prior_reviewer_user_id = review.reviewer_user_id
        prior_reviewed_at = review.reviewed_at
        db.add(
            ADExtractionReviewDecision(
                review_id=review.id,
                extraction_id=review.extraction_id,
                decision=review.decision or review.status,
                output_hash=stable_output_hash(prior_output),
                decision_output=prior_output,
                actor_user_id=prior_reviewer_user_id,
                decided_at=prior_reviewed_at or corrected_at,
                notes=review.notes,
                event_type="approved_correction_snapshot",
                metadata_json={
                    "correctionReason": args.reason,
                    "correctionStagedByUserId": actor.id,
                    "correctedAt": corrected_at.isoformat(),
                },
            )
        )
        affected_aircraft_ids = set(
            db.scalars(
                select(ADMatchResult.aircraft_id)
                .where(
                    ADMatchResult.directive_id == review.extraction.directive_id,
                    ADMatchResult.is_current.is_(True),
                )
                .distinct()
            ).all()
        )

        history = list((review.extraction.raw_response or {}).get("approvedCorrectionHistory") or [])
        history.append({
            "correctedAt": corrected_at.isoformat(),
            "reason": args.reason,
            "priorDecisionOutputHash": stable_output_hash(prior_output),
            "priorDecisionOutput": prior_output,
            "priorReviewerUserId": prior_reviewer_user_id,
            "priorReviewedAt": prior_reviewed_at.isoformat() if prior_reviewed_at else None,
            "correctionStagedByUserId": actor.id,
        })
        review.extraction.raw_response = {
            **(review.extraction.raw_response or {}),
            "approvedCorrectionHistory": history,
            "lastApprovedCorrectionAt": corrected_at.isoformat(),
        }
        review.proposed_output = corrected_output
        review.decision_output = None
        review.decision = None
        review.status = "pending"
        review.reviewer_user_id = None
        review.reviewed_at = None
        review.notes = args.reason
        review.extraction.output = corrected_output
        review.extraction.status = "needs_review"
        review.extraction.directive.extraction_status = "needs_review"
        review.extraction.directive.review_status = "pending"
        review.extraction.directive.approved_at = None
        target_ids = set(
            db.scalars(
                select(ADTargetApplicability.target_id).where(
                    ADTargetApplicability.source_extraction_id == review.extraction_id,
                    ADTargetApplicability.status == "current",
                )
            ).all()
        )
        requirement_ids = set(
            db.scalars(
                select(ADComplianceRequirement.id).where(
                    ADComplianceRequirement.source_extraction_id == review.extraction_id,
                    ADComplianceRequirement.status == "current",
                )
            ).all()
        )
        db.execute(
            update(ADTargetApplicability)
            .where(
                ADTargetApplicability.source_extraction_id == review.extraction_id,
                ADTargetApplicability.status == "current",
            )
            .values(status="superseded")
        )
        db.execute(
            update(ADComplianceRequirement)
            .where(
                ADComplianceRequirement.source_extraction_id == review.extraction_id,
                ADComplianceRequirement.status == "current",
            )
            .values(status="superseded", review_status="needs_adjudication")
        )
        db.execute(supersede_amoc_provisions_statement(review.extraction_id))
        if requirement_ids:
            db.execute(
                update(AircraftADDueState)
                .where(
                    AircraftADDueState.requirement_id.in_(requirement_ids),
                    AircraftADDueState.is_current.is_(True),
                )
                .values(is_current=False)
            )
        if target_ids:
            db.execute(
                update(ADCoverageSet)
                .where(ADCoverageSet.target_id.in_(target_ids))
                .values(
                    status="pending_recalculation",
                    metadata_json={
                        "reason": "approved_ad_correction_staged",
                        "extractionId": review.extraction_id,
                    },
                )
            )
        for aircraft_id in affected_aircraft_ids:
            invalidate_aircraft_match_results(
                db,
                aircraft_id=aircraft_id,
                actor=actor,
            )

        record_product_event(
            db,
            event_type="ad_extraction_approved_correction_staged",
            subject_type="ad_review",
            subject_id=review.id,
            actor=actor,
            properties={
                "directiveId": review.extraction.directive_id,
                "adNumber": review.extraction.directive.ad_number,
                "reason": args.reason,
                "priorOutputHash": stable_output_hash(prior_output),
                "correctedOutputHash": stable_output_hash(corrected_output),
                "requirementCount": len(corrected_output["requirements"]),
            },
        )
        record_workflow_status(
            db,
            workflow_type="ad_extraction",
            workflow_id=review.extraction_id,
            previous_status="approved",
            new_status="needs_review",
            reason="approved_output_correction_requires_new_review",
            actor_type="reviewer",
            actor=actor,
        )

        checks = [
            ("review_reopened", review.status == "pending"),
            ("prior_reviewer_attribution_cleared", review.reviewer_user_id is None),
            ("prior_review_timestamp_cleared", review.reviewed_at is None),
            ("source_wording_validated", not blockers),
            ("correction_history_appended", len(history) > 0),
            ("publication_revoked_until_reapproval", review.extraction.status == "needs_review"),
            ("derived_applicability_revoked", all(
                item.status != "current"
                for item in review.extraction.target_applicabilities
            )),
        ]
        if args.commit:
            db.commit()
        else:
            db.rollback()

    passed = sum(value for _, value in checks)
    print(json.dumps({
        "reviewId": args.review_id,
        "checks": dict(checks),
        "committed": args.commit,
    }, sort_keys=True))
    print(f"{passed} passed out of {len(checks)}")
    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
