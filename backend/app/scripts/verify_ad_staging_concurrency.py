from __future__ import annotations

import threading

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    AirworthinessDirective,
    Organization,
    OrganizationMembership,
    User,
)
from app.scripts import stage_ad_review_proposal as staging


REVIEW_ID = "arv_t081_stage_concurrency"
EXTRACTION_ID = "adx_t081_stage_concurrency"
DIRECTIVE_ID = "ad_t081_stage_concurrency"
ADMIN_ID = "usr_t081_stage_admin"
APPROVER_ID = "usr_t081_stage_approver"
SOURCE_TEXT = (
    "14 CFR Part 39 [Docket No. FAA-2099-1; Amendment 39-1; AD 2099-00-82] "
    "Airworthiness Directives; Example Aircraft Model E-1, all serial numbers. "
    "Inspect the aircraft."
)
SOURCE_PAGES = [{
    "sourceDocumentId": "asd_t081_stage",
    "pageNumber": 1,
    "text": SOURCE_TEXT,
}]


def proposal(title: str) -> dict:
    citation = {
        "sourceDocumentId": "asd_t081_stage",
        "pageNumber": 1,
        "text": "Example Aircraft Model E-1, all serial numbers",
    }
    return {
        "adNumber": "2099-00-82",
        "title": title,
        "effectiveDate": None,
        "publicationDate": None,
        "applicabilityGroups": [{
            "groupKey": "example-e1",
            "productType": "aircraft",
            "productSubtype": "airplane",
            "manufacturer": {"sourceName": "Example Aircraft", "normalizedName": None},
            "modelApplicability": {
                "kind": "listed",
                "models": [{
                    "sourceDesignation": "E-1",
                    "normalizedDesignation": None,
                    "aliases": [],
                }],
                "sourceText": "Example Aircraft Model E-1",
            },
            "serialNumberApplicability": {
                "kind": "all",
                "values": [],
                "ranges": [],
                "excludedValues": [],
                "sourceText": "all serial numbers",
            },
            "equipmentCombinationLogic": "all",
            "equipmentConditions": [],
            "conditions": [],
            "citations": [citation],
            "confidence": 1.0,
            "uncertaintyReasons": [],
        }],
        "affectedProducts": [],
        "complianceActions": ["Inspect the aircraft."],
        "complianceIntervals": [],
        "supersedesAdNumbers": [],
        "sourceUrls": {"html": None, "pdf": None, "publicInspectionPdf": None},
        "confidence": 1.0,
        "citations": [],
        "uncertaintyReasons": [],
        "requirements": [{
            "requirementKey": "inspect",
            "applicabilityGroupKeys": ["example-e1"],
            "requirementType": "one_time",
            "actionText": "Inspect the aircraft.",
            "initialThresholds": [],
            "recurringTriggers": [],
            "combinationLogic": "all",
            "conditions": [],
            "terminatingAction": None,
            "citations": [{
                "sourceDocumentId": "asd_t081_stage",
                "pageNumber": 1,
                "text": "Inspect the aircraft.",
            }],
            "confidence": 1.0,
            "uncertaintyReasons": [],
        }],
        "amocProvisions": [],
    }


def seed() -> None:
    initial = proposal("Initial proposal")
    with SessionLocal() as db:
        db.execute(delete(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == REVIEW_ID
        ))
        review = db.get(ADExtractionReview, REVIEW_ID)
        if review is None:
            admin = User(
                id=ADMIN_ID,
                email="t081-stage-admin@example.invalid",
                name="T081 Stage Admin",
                password_hash="not-a-login-credential",
                status="active",
            )
            approver = User(
                id=APPROVER_ID,
                email="t081-stage-approver@example.invalid",
                name="T081 Stage Approver",
                password_hash="not-a-login-credential",
                status="active",
            )
            organization = Organization(
                id="org_t081_stage_concurrency",
                name="T081 Stage Verification",
                type="platform",
            )
            db.add_all([admin, approver, organization])
            db.flush()
            db.add_all([
                OrganizationMembership(
                    organization_id=organization.id,
                    user_id=ADMIN_ID,
                    role="platform_admin",
                    status="active",
                ),
                OrganizationMembership(
                    organization_id=organization.id,
                    user_id=APPROVER_ID,
                    role="platform_admin",
                    status="active",
                ),
            ])
            directive = AirworthinessDirective(
                id=DIRECTIVE_ID,
                ad_number="2099-00-82",
                title="T081 staging concurrency verification",
                status="candidate",
                source_content_hash="8" * 64,
                extraction_status="needs_review",
                review_status="pending",
            )
            extraction = ADExtraction(
                id=EXTRACTION_ID,
                directive=directive,
                provider_name="t081-verifier",
                provider_version="1",
                schema_version="ad_extraction_v3",
                input_content_hash="8" * 64,
                status="needs_review",
                confidence=1.0,
                output=initial,
                citations=[],
                raw_response={"verification": True},
            )
            review = ADExtractionReview(
                id=REVIEW_ID,
                extraction=extraction,
                status="pending",
                proposed_output=initial,
            )
            db.add(review)
        else:
            review.status = "pending"
            review.decision = None
            review.decision_output = None
            review.reviewer_user_id = None
            review.reviewed_at = None
            review.proposed_output = initial
            review.extraction.status = "needs_review"
            review.extraction.output = initial
            review.extraction.raw_response = {"verification": True}
            review.extraction.directive.review_status = "pending"
            review.extraction.directive.extraction_status = "needs_review"
        db.commit()


def main() -> None:
    seed()
    staging.ensure_persisted_source_pages = lambda *_: SOURCE_PAGES
    staging.bounded_source_document_pages = lambda pages, **_: pages

    approval_locked = threading.Event()
    stage_attempting = threading.Event()
    release_approval = threading.Event()
    stage_finished = threading.Event()
    outcomes: list[str] = []

    def approval_wins() -> None:
        with SessionLocal() as db:
            review = db.scalar(select(ADExtractionReview).where(
                ADExtractionReview.id == REVIEW_ID
            ).with_for_update())
            approval_locked.set()
            if not release_approval.wait(timeout=5):
                outcomes.append("approval_timeout")
                return
            review.status = "approved"
            review.decision = "approved"
            review.extraction.status = "approved"
            review.reviewer_user_id = APPROVER_ID
            db.commit()
            outcomes.append("approved")

    def stage_loses() -> None:
        with SessionLocal() as db:
            stage_attempting.set()
            try:
                staging.stage_review_proposal(
                    db,
                    ad_number="2099-00-82",
                    review_id=REVIEW_ID,
                    actor_user_id=ADMIN_ID,
                    loaded_proposal=proposal("Concurrent staged proposal"),
                    allow_incomplete=False,
                )
            except ValueError as exc:
                outcomes.append("stage_terminal" if "terminal" in str(exc) else str(exc))
            else:
                outcomes.append("stage_unexpected")
            finally:
                stage_finished.set()

    approval_thread = threading.Thread(target=approval_wins)
    stage_thread = threading.Thread(target=stage_loses)
    approval_thread.start()
    if not approval_locked.wait(timeout=5):
        raise SystemExit("Approval verifier did not lock the review row")
    stage_thread.start()
    if not stage_attempting.wait(timeout=5):
        raise SystemExit("Staging verifier did not attempt the row lock")
    stage_blocked = not stage_finished.wait(timeout=0.25)
    release_approval.set()
    approval_thread.join(timeout=5)
    stage_thread.join(timeout=5)

    with SessionLocal() as db:
        review = db.get(ADExtractionReview, REVIEW_ID)
        stage_decisions = db.scalars(select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == REVIEW_ID,
            ADExtractionReviewDecision.event_type == "proposal_staged",
        )).all()
    checks = {
        "staging_blocked_on_approval_row_lock": stage_blocked,
        "approval_terminal_transition_committed": outcomes.count("approved") == 1,
        "staging_rechecked_terminal_state": outcomes.count("stage_terminal") == 1,
        "no_losing_staging_history_survived": not stage_decisions,
        "terminal_review_preserved": review is not None and review.status == "approved",
        "original_proposal_preserved": review is not None and review.proposed_output["title"] == "Initial proposal",
    }
    passed = sum(checks.values())
    print(f"{passed} passed out of {len(checks)}")
    if passed != len(checks):
        raise SystemExit(str(checks))


if __name__ == "__main__":
    main()
