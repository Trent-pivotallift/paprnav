from __future__ import annotations

import json
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateProposal,
    ADV4CandidateSubmission,
    OrganizationMembership,
    User,
)
from app.services import ad_v4_candidates as candidates
from app.services import ad_v4_reviews as reviews
from test_ad_v4_applicability_postgres import _enable, _store


URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


@pytest.mark.parametrize("transition", ["case", "request", "rejection"])
@pytest.mark.parametrize("reuse_content", [False, True], ids=["new-content", "resubmission"])
def test_candidate_submission_and_review_share_relationship_before_fragment_lock_order(
    monkeypatch: pytest.MonkeyPatch, transition: str, reuse_content: bool,
) -> None:
    """Force the previous two-admin deadlock, including content deduplication.

    The review writer owns the relationship lock before the candidate writer
    requests it. Previously the candidate already owned the fragment then,
    so allowing review to continue closed a relationship/fragment lock cycle.
    Both real transactions must now commit, with no synthetic lock bypass.
    """
    for flag in ("READS", "DRAFTS", "DECISIONS"):
        monkeypatch.setenv(f"PAPRNAV_AD_V4_SLICE4_{flag}_ENABLED", "true")
    get_settings.cache_clear()
    engine = create_engine(URL, connect_args={
        "connect_timeout": 5,
        "options": "-c statement_timeout=12000 -c lock_timeout=10000",
    })
    token = uuid.uuid4().hex
    try:
        with Session(engine) as db:
            _enable(db)
            for gate in ("materializer3b_enabled", "reviewer4_draft_enabled", "reviewer4_decision_enabled"):
                db.execute(text("SELECT paprnav_set_v4_feature_gate(:gate,true,'lock-order-test')"), {"gate": gate})
            db.commit()
            author_id, author_membership_id, directive_id, proposal_id = _store(
                db, validator_version=candidates.VALIDATOR_VERSION_V2, suffix=f"lock-order-{token}",
            )
            author_membership = db.get(OrganizationMembership, author_membership_id)
            reviewer = User(email=f"review-lock-{token}@example.test", name="Second administrator",
                            password_hash="x", status="active")
            db.add(reviewer)
            db.flush()
            membership = OrganizationMembership(
                organization_id=author_membership.organization_id, user_id=reviewer.id,
                role="platform_admin", status="active",
            )
            db.add(membership)
            db.commit()
            reviewer_id, reviewer_membership_id = reviewer.id, membership.id
            proposal = db.get(ADV4CandidateProposal, proposal_id)
            payload = json.loads(proposal.canonical_bytes)
            if not reuse_content:
                payload["decisionKey"] = f"concurrent-{token}"
            parsed = candidates.parse_v4_request_bytes(json.dumps({
                "proposal": payload, "submissionContext": {"relationships": []},
            }).encode())
            observed = reviews.review_proposal_observation(
                db, directive_id=directive_id, proposal_id=proposal_id,
                actor=reviewer, membership_id=reviewer_membership_id,
            )
            state = observed
            if transition != "case":
                state = reviews.create_review_case(
                    db, directive_id=directive_id, proposal_id=proposal_id,
                    actor=reviewer, membership_id=reviewer_membership_id,
                    idempotency_key=f"case-{token}",
                    expected_authorization_observation_hash=state["authorizationObservationHashes"]["create_ad_v4_review_case"],
                    expected_input_identity_hash=state["inputIdentityHash"],
                )
                state = reviews.save_review_draft(
                    db, case_id=state["caseId"], actor=reviewer, membership_id=reviewer_membership_id,
                    idempotency_key=f"draft-{token}",
                    expected_authorization_observation_hash=state["authorizationObservationHashes"]["save_ad_v4_review_draft"],
                    expected_input_identity_hash=state["inputIdentityHash"],
                    expected_predecessor_event_hash=state["latestEventHash"],
                    annotations=[{"pointer": "/requirements", "text": "Remediation required"}],
                    intended_action="reject",
                )
            if transition == "rejection":
                state = reviews.request_review(
                    db, case_id=state["caseId"], actor=reviewer, membership_id=reviewer_membership_id,
                    idempotency_key=f"request-{token}",
                    expected_authorization_observation_hash=state["authorizationObservationHashes"]["request_ad_v4_review"],
                    expected_input_identity_hash=state["inputIdentityHash"],
                    expected_predecessor_event_hash=state["latestEventHash"],
                    draft_revision_id=state["draftRevisionId"],
                )
            db.commit()

        review_has_relationship = threading.Event()
        candidate_requests_relationship = threading.Event()
        original_lock = candidates._advisory_lock
        original_bindings = candidates._binding_snapshot
        candidate_order: list[str] = []

        def coordinated_lock(db: Session, value: str) -> None:
            role = db.info["lock_order_test_role"]
            relationship = value == f"candidate-relationship-graph:{directive_id}"
            if role == "candidate" and relationship:
                candidate_requests_relationship.set()
            original_lock(db, value)
            if role == "candidate":
                candidate_order.append("relationship" if relationship else value.split(":", 1)[0])
            elif relationship and not review_has_relationship.is_set():
                review_has_relationship.set()
                assert candidate_requests_relationship.wait(8), "Candidate never requested relationship lock"

        def traced_bindings(db: Session, *args, **kwargs):
            candidate_order.append("bindings")
            return original_bindings(db, *args, **kwargs)

        monkeypatch.setattr(candidates, "_advisory_lock", coordinated_lock)
        monkeypatch.setattr(reviews, "_advisory_lock", coordinated_lock)
        monkeypatch.setattr(candidates, "_binding_snapshot", traced_bindings)

        def mutate_review():
            with Session(engine) as db:
                db.info["lock_order_test_role"] = "review"
                reviewer = db.get(User, reviewer_id)
                common = dict(actor=reviewer, membership_id=reviewer_membership_id,
                              idempotency_key=f"concurrent-review-{token}",
                              expected_input_identity_hash=state["inputIdentityHash"])
                if transition == "case":
                    result = reviews.create_review_case(
                        db, **common, directive_id=directive_id, proposal_id=proposal_id,
                        expected_authorization_observation_hash=state["authorizationObservationHashes"]["create_ad_v4_review_case"],
                    )
                elif transition == "request":
                    result = reviews.request_review(
                        db, **common, case_id=state["caseId"], draft_revision_id=state["draftRevisionId"],
                        expected_predecessor_event_hash=state["latestEventHash"],
                        expected_authorization_observation_hash=state["authorizationObservationHashes"]["request_ad_v4_review"],
                    )
                else:
                    result = reviews.reject_review_case(
                        db, **common, case_id=state["caseId"], expected_request_id=state["reviewRequestId"],
                        expected_predecessor_event_hash=state["latestEventHash"],
                        expected_authorization_observation_hash=state["authorizationObservationHashes"]["reject_ad_v4_review"],
                        reason_codes=["remediation_requested"], explanation="Remediation required.",
                    )
                db.commit()
                return result

        def submit_candidate():
            assert review_has_relationship.wait(8), "Review never obtained relationship lock"
            with Session(engine) as db:
                db.info["lock_order_test_role"] = "candidate"
                result = candidates.store_v4_candidate(
                    db, directive_id=directive_id, parsed=parsed, actor=db.get(User, author_id),
                    membership_id=author_membership_id, idempotency_key=f"concurrent-candidate-{token}",
                    validator_version=candidates.VALIDATOR_VERSION_V2,
                )
                db.commit()
                return result.proposal.id, result.submission.id, result.content_reused

        with ThreadPoolExecutor(max_workers=2) as pool:
            review_future = pool.submit(mutate_review)
            candidate_future = pool.submit(submit_candidate)
            review_result = review_future.result(timeout=20)
            candidate_id, submission_id, reused = candidate_future.result(timeout=20)
        assert review_result["state"] == {"case": "draft", "request": "pending_review", "rejection": "rejected"}[transition]
        assert reused is reuse_content
        assert (candidate_id == proposal_id) is reuse_content
        assert candidate_order.index("content") < candidate_order.index("relationship") < candidate_order.index("bindings")
        with Session(engine) as db:
            assert db.scalar(select(ADV4CandidateSubmission.id).where(
                ADV4CandidateSubmission.id == submission_id,
            )) == submission_id
    finally:
        engine.dispose()
