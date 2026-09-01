from __future__ import annotations

import threading
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    AirworthinessDirective,
    User,
)


REVIEW_ID = "arv_t081_concurrency"
EXTRACTION_ID = "adx_t081_concurrency"
DIRECTIVE_ID = "ad_t081_concurrency"
WINNER_ID = "usr_t081_winner"
LOSER_ID = "usr_t081_loser"


def seed() -> None:
    with SessionLocal() as db:
        db.add_all([
            User(
                id=WINNER_ID,
                email="t081-winner@example.invalid",
                name="T081 Winner",
                password_hash="not-a-login-credential",
                status="active",
            ),
            User(
                id=LOSER_ID,
                email="t081-loser@example.invalid",
                name="T081 Loser",
                password_hash="not-a-login-credential",
                status="active",
            ),
        ])
        directive = AirworthinessDirective(
            id=DIRECTIVE_ID,
            ad_number="2099-00-81",
            title="T081 concurrency verification",
            status="candidate",
            source_content_hash="1" * 64,
            extraction_status="needs_review",
            review_status="pending",
        )
        extraction = ADExtraction(
            id=EXTRACTION_ID,
            directive=directive,
            provider_name="t081-verifier",
            provider_version="1",
            schema_version="ad_extraction_v3",
            input_content_hash="2" * 64,
            status="needs_review",
            confidence=1.0,
            output={"adNumber": "2099-00-81"},
            citations=[],
            raw_response={"verification": True},
        )
        db.add(ADExtractionReview(
            id=REVIEW_ID,
            extraction=extraction,
            status="pending",
            proposed_output=extraction.output,
        ))
        db.commit()


def main() -> None:
    seed()
    winner_locked = threading.Event()
    loser_attempting = threading.Event()
    release_winner = threading.Event()
    loser_completed = threading.Event()
    outcomes: list[str] = []

    def decide(actor_id: str, *, winner: bool) -> None:
        with SessionLocal() as db:
            if not winner:
                loser_attempting.set()
            review = db.scalar(
                select(ADExtractionReview)
                .where(ADExtractionReview.id == REVIEW_ID)
                .with_for_update()
            )
            if review is None:
                outcomes.append("missing")
                return
            if review.status != "pending":
                db.add(ADExtractionReviewDecision(
                    review_id=review.id,
                    extraction_id=review.extraction_id,
                    decision="rejected",
                    output_hash="3" * 64,
                    decision_output=review.proposed_output,
                    actor_user_id=actor_id,
                    decided_at=datetime.now(timezone.utc),
                    event_type="decision_conflict",
                    metadata_json={
                        "terminalStatusObserved": review.status,
                        "terminalReviewerUserId": review.reviewer_user_id,
                    },
                ))
                db.commit()
                outcomes.append("conflict")
                loser_completed.set()
                return
            if winner:
                winner_locked.set()
                if not release_winner.wait(timeout=5):
                    outcomes.append("winner_timeout")
                    return
            decision_time = datetime.now(timezone.utc)
            review.status = "approved"
            review.decision = "approved"
            review.decision_output = review.proposed_output
            review.reviewer_user_id = actor_id
            review.reviewed_at = decision_time
            db.add(ADExtractionReviewDecision(
                review_id=review.id,
                extraction_id=review.extraction_id,
                decision="approved",
                output_hash="4" * 64,
                decision_output=review.proposed_output,
                actor_user_id=actor_id,
                decided_at=decision_time,
                event_type="review_decision",
                metadata_json={"verification": True},
            ))
            db.commit()
            outcomes.append("approved")

    winner_thread = threading.Thread(
        target=decide,
        kwargs={"actor_id": WINNER_ID, "winner": True},
    )
    loser_thread = threading.Thread(
        target=decide,
        kwargs={"actor_id": LOSER_ID, "winner": False},
    )
    winner_thread.start()
    if not winner_locked.wait(timeout=5):
        raise SystemExit("Winner did not acquire the review row lock")
    loser_thread.start()
    if not loser_attempting.wait(timeout=5):
        raise SystemExit("Losing reviewer did not attempt the row lock")
    serialized = not loser_completed.wait(timeout=0.25)
    release_winner.set()
    winner_thread.join(timeout=5)
    loser_thread.join(timeout=5)

    with SessionLocal() as db:
        review = db.get(ADExtractionReview, REVIEW_ID)
        decisions = db.scalars(
            select(ADExtractionReviewDecision).where(
                ADExtractionReviewDecision.review_id == REVIEW_ID
            )
        ).all()
    checks = {
        "second_session_blocked_on_row_lock": serialized,
        "exactly_one_terminal_transition": outcomes.count("approved") == 1,
        "second_actor_received_conflict": outcomes.count("conflict") == 1,
        "review_terminal_status_preserved": review is not None and review.status == "approved",
        "winner_attribution_preserved": review is not None and review.reviewer_user_id == WINNER_ID,
        "winner_decision_is_immutable_history": sum(item.event_type == "review_decision" for item in decisions) == 1,
        "loser_attempt_is_auditable": any(
            item.event_type == "decision_conflict" and item.actor_user_id == LOSER_ID
            for item in decisions
        ),
    }
    passed = sum(checks.values())
    print(f"{passed} passed out of {len(checks)}")
    if passed != len(checks):
        raise SystemExit(str(checks))


if __name__ == "__main__":
    main()
