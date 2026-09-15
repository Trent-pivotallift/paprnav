from __future__ import annotations

import json
import os
import uuid

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateAppMaterializationRequest, ADV4CandidateAppProjection,
    ADV4CandidateObligationMaterializationRequest,
    ADV4CandidateObligationProjection, User,
)
from app.services import ad_v4_reviews as review_module
from app.services.ad_v4_candidates import ADV4Error, VALIDATOR_VERSION_V2
from app.services.ad_v4_reviews import (
    create_review_case,
    reject_review_case,
    request_review,
    review_proposal_observation,
    save_review_draft,
    verified_review_case,
)
from test_ad_v4_applicability_postgres import _enable, _store
from test_ad_v4_review_case_migration_postgres import Records, _materialize_review_fixture


URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


def test_service_rejection_lifecycle_commits_under_deferred_sql_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_READS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", "true")
    get_settings.cache_clear()
    engine = create_engine(URL)
    with Session(engine) as db:
        _enable(db)
        for gate in ("materializer3b_enabled", "reviewer4_draft_enabled", "reviewer4_decision_enabled"):
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,true,'review-service-test')"
            ), {"gate": gate})
        db.commit()
        user_id, membership_id, directive_id, proposal_id = _store(
            db,
            validator_version=VALIDATOR_VERSION_V2,
            suffix=f"review-service-{uuid.uuid4().hex}",
        )
        actor = db.get(User, user_id)
        assert actor is not None

        observed = review_proposal_observation(
            db,
            directive_id=directive_id,
            proposal_id=proposal_id,
            actor=actor,
            membership_id=membership_id,
        )
        case = create_review_case(
            db,
            directive_id=directive_id,
            proposal_id=proposal_id,
            actor=actor,
            membership_id=membership_id,
            idempotency_key=f"case-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=observed[
                "authorizationObservationHashes"
            ]["create_ad_v4_review_case"],
            expected_input_identity_hash=observed["inputIdentityHash"],
        )
        draft = save_review_draft(
            db,
            case_id=case["caseId"],
            actor=actor,
            membership_id=membership_id,
            idempotency_key=f"draft-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=case[
                "authorizationObservationHashes"
            ]["save_ad_v4_review_draft"],
            expected_input_identity_hash=case["inputIdentityHash"],
            expected_predecessor_event_hash=case["latestEventHash"],
            annotations=[{"pointer": "/requirements", "text": "Remediate"}],
            intended_action="reject",
        )
        requested = request_review(
            db,
            case_id=case["caseId"],
            actor=actor,
            membership_id=membership_id,
            idempotency_key=f"request-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=draft[
                "authorizationObservationHashes"
            ]["request_ad_v4_review"],
            expected_input_identity_hash=draft["inputIdentityHash"],
            expected_predecessor_event_hash=draft["latestEventHash"],
            draft_revision_id=draft["draftRevisionId"],
        )
        rejected = reject_review_case(
            db,
            case_id=case["caseId"],
            actor=actor,
            membership_id=membership_id,
            idempotency_key=f"reject-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=requested[
                "authorizationObservationHashes"
            ]["reject_ad_v4_review"],
            expected_input_identity_hash=requested["inputIdentityHash"],
            expected_predecessor_event_hash=requested["latestEventHash"],
            expected_request_id=requested["reviewRequestId"],
            reason_codes=["remediation_requested"],
            explanation="Candidate requires remediation.",
        )
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.commit()

        verified = verified_review_case(
            db,
            case_id=case["caseId"],
            actor=actor,
            membership_id=membership_id,
            event_limit=2,
            event_offset=1,
        )
        assert rejected["state"] == verified["state"] == "rejected"
        assert verified["eventTotal"] == 4
        assert [event["sequenceNumber"] for event in verified["events"]] == [1, 2]
        assert verified["signoff"]["action"] == "reject"
    engine.dispose()


def test_maximal_admitted_drafts_preserve_request_rejection_and_successor_liveness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The draft-phase ceiling must reserve every remaining immutable row."""
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_READS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", "true")
    get_settings.cache_clear()
    engine = create_engine(URL)
    with Session(engine) as db:
        _enable(db)
        for gate in ("materializer3b_enabled", "reviewer4_draft_enabled", "reviewer4_decision_enabled"):
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,true,'review-liveness-test')"
            ), {"gate": gate})
        db.commit()
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix=f"review-liveness-{uuid.uuid4().hex}")
        actor = db.get(User, user_id)
        observed = review_proposal_observation(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=actor, membership_id=membership_id)
        current = create_review_case(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=actor, membership_id=membership_id,
            idempotency_key=f"case-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=observed[
                "authorizationObservationHashes"]["create_ad_v4_review_case"],
            expected_input_identity_hash=observed["inputIdentityHash"])
        db.commit()

        annotations = [
            {"pointer": f"/requirements/{index}", "text": "x" * 4096}
            for index in range(128)
        ]
        accepted = 0
        for attempt in range(30):
            try:
                current = save_review_draft(
                    db, case_id=current["caseId"], actor=actor,
                    membership_id=membership_id,
                    idempotency_key=f"draft-{attempt}-{uuid.uuid4().hex}",
                    expected_authorization_observation_hash=current[
                        "authorizationObservationHashes"]["save_ad_v4_review_draft"],
                    expected_input_identity_hash=current["inputIdentityHash"],
                    expected_predecessor_event_hash=current["latestEventHash"],
                    annotations=annotations, intended_action="reject")
                db.commit()
                accepted += 1
            except ADV4Error as exc:
                assert exc.code == "review_history_limit"
                db.rollback()
                break
        else:
            pytest.fail("Draft-phase byte ceiling was not reached")
        assert accepted > 0
        stored = db.scalar(text(
            "SELECT paprnav_v4_review_case_authoritative_bytes(:case_id)"
        ), {"case_id": current["caseId"]})

        # Fill the remaining draft phase to within one small append quantum.
        # Measuring pending rows does not flush or bypass any persisted guard;
        # the selected payload is then written through the ordinary service.
        class PendingBytes(Exception):
            def __init__(self, size: int):
                self.size = size

        def measure(text_size: int) -> int:
            annotations = [
                {"pointer": f"/requirements/{index}", "text": "y" * text_size}
                for index in range(128)
            ]
            def capture_pending(session, case_id, objects=None):
                from app.services import ad_v4_reviews as review_module
                raise PendingBytes(review_module._pending_case_history_bytes(session, case_id))
            with monkeypatch.context() as scoped:
                scoped.setattr("app.services.ad_v4_reviews._flush_review_history", capture_pending)
                with pytest.raises(PendingBytes) as captured:
                    save_review_draft(
                        db, case_id=current["caseId"], actor=actor,
                        membership_id=membership_id,
                        idempotency_key=f"measure-{text_size}-{uuid.uuid4().hex}",
                        expected_authorization_observation_hash=current[
                            "authorizationObservationHashes"]["save_ad_v4_review_draft"],
                        expected_input_identity_hash=current["inputIdentityHash"],
                        expected_predecessor_event_hash=current["latestEventHash"],
                        annotations=annotations, intended_action="reject")
            db.rollback()
            return captured.value.size

        low, high = 1, 4096
        while low < high:
            middle = (low + high + 1) // 2
            if stored + measure(middle) <= 16 * 1024 * 1024:
                low = middle
            else:
                high = middle - 1
        final_annotations = [
            {"pointer": f"/requirements/{index}", "text": "y" * low}
            for index in range(128)
        ]
        current = save_review_draft(
            db, case_id=current["caseId"], actor=actor,
            membership_id=membership_id,
            idempotency_key=f"draft-final-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=current[
                "authorizationObservationHashes"]["save_ad_v4_review_draft"],
            expected_input_identity_hash=current["inputIdentityHash"],
            expected_predecessor_event_hash=current["latestEventHash"],
            annotations=final_annotations, intended_action="reject")
        db.commit()
        stored = db.scalar(text(
            "SELECT paprnav_v4_review_case_authoritative_bytes(:case_id)"
        ), {"case_id": current["caseId"]})
        assert 0 <= 16 * 1024 * 1024 - stored < 1024

        requested = request_review(
            db, case_id=current["caseId"], actor=actor,
            membership_id=membership_id,
            idempotency_key=f"request-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=current[
                "authorizationObservationHashes"]["request_ad_v4_review"],
            expected_input_identity_hash=current["inputIdentityHash"],
            expected_predecessor_event_hash=current["latestEventHash"],
            draft_revision_id=current["draftRevisionId"])
        db.commit()
        rejected = reject_review_case(
            db, case_id=current["caseId"], actor=actor,
            membership_id=membership_id,
            idempotency_key=f"reject-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=requested[
                "authorizationObservationHashes"]["reject_ad_v4_review"],
            expected_input_identity_hash=requested["inputIdentityHash"],
            expected_predecessor_event_hash=requested["latestEventHash"],
            expected_request_id=requested["reviewRequestId"],
            reason_codes=["remediation_requested"],
            explanation="Bounded remediation is required.")
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.commit()

        successor = create_review_case(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=actor, membership_id=membership_id,
            idempotency_key=f"successor-{uuid.uuid4().hex}",
            expected_authorization_observation_hash=rejected[
                "authorizationObservationHashes"]["create_ad_v4_review_case"],
            expected_input_identity_hash=rejected["inputIdentityHash"])
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.commit()
        assert successor["caseId"] != current["caseId"]
        assert successor["state"] == "draft"
    engine.dispose()


@pytest.mark.parametrize("overflow", ["obligation_count", "parent_count", "parent_bytes"])
def test_repeated_projection_requests_are_preflighted_before_payload_loading(
    monkeypatch: pytest.MonkeyPatch, overflow: str,
) -> None:
    from app.services.ad_v4_applicability import materialize_applicability
    from app.services.ad_v4_obligation_persistence import materialize_obligations

    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        projections = _materialize_review_fixture(records)
        projection = db.get(
            ADV4CandidateObligationProjection,
            projections["obligationProjection"]["id"],
        )
        app_projection = db.get(ADV4CandidateAppProjection, projection.app_projection_id)
        repeats = 7 if overflow == "parent_bytes" else 2
        for _ in range(repeats):
            if overflow == "obligation_count":
                materialize_obligations(
                    db, directive_id=records.directive, proposal_id=records.proposal,
                    app_projection_id=projection.app_projection_id,
                    actor=db.get(User, records.user), membership_id=records.member,
                    idempotency_key=uuid.uuid4().hex)
            else:
                materialize_applicability(
                    db, directive_id=records.directive, proposal_id=records.proposal,
                    actor=db.get(User, records.user), membership_id=records.member,
                    idempotency_key=uuid.uuid4().hex)
            db.commit()
        request_model = (ADV4CandidateObligationMaterializationRequest
                         if overflow == "obligation_count"
                         else ADV4CandidateAppMaterializationRequest)
        request_projection_id = projection.id if overflow == "obligation_count" else app_projection.id
        assert db.scalar(select(text("count(*)")).select_from(
            request_model).where(request_model.projection_id == request_projection_id)) == repeats + 1

        statements = []
        def capture(execute_state):
            statements.append(execute_state.statement)
        if overflow.endswith("count"):
            monkeypatch.setattr(review_module, "MAX_ARRAY_ITEMS", 2)
        else:
            parent_work = review_module._prepare_projection_observation(
                db, records.proposal, obligation=False)[1]
            child_work = review_module._prepare_projection_observation(
                db, records.proposal, obligation=True)[1]
            evidence_work = review_module._evidence_work_metadata(db, records.proposal)
            evidence_bytes = (evidence_work.text_bytes + evidence_work.lifecycle_reason_bytes
                              + sum(key[2] for key in evidence_work.document_keys))
            limit = max(child_work.payload_bytes, evidence_bytes) + 1
            assert parent_work.payload_bytes > limit
            monkeypatch.setattr(review_module, "MAX_RETAINED_SOURCE_BYTES", limit)
        event.listen(db, "do_orm_execute", capture)
        try:
            observation = review_module.observe_review_inputs(db, records.proposal)
        finally:
            event.remove(db, "do_orm_execute", capture)
        identity = json.loads(observation["input_identity_bytes"])
        assert identity["obligationProjection"]["state"] == "integrity_error"
        assert identity["obligationProjection"]["errorCode"] == "projection_integrity"
        assert identity["applicabilityProjection"]["state"] == (
            "verified" if overflow == "obligation_count" else "integrity_error")
        request_statements = [statement for statement in statements
                              if request_model.__tablename__ in str(statement)]
        assert request_statements
        assert any("count(" in str(statement).lower() for statement in request_statements)
        assert not any(
            getattr(column, "name", "") == "request_canonical_bytes"
            for statement in request_statements for column in statement.selected_columns
        )
    engine.dispose()
