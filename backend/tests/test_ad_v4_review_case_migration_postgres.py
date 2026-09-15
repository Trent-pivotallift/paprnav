"""Independent SQL-boundary probes for the rejection-only review foundation."""
from __future__ import annotations

import hashlib
import json
import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.models.core import (
    ADV4CandidateProposal, ADV4CandidateAppProjection, ADV4CandidateAppProjectionEvent,
    ADV4CandidateSubmission, ADV4CandidateAppMaterializationRequest,
    ADV4CandidateObligationProjection, ADV4CandidateObligationProjectionEvent,
    ADV4ReviewCase, ADV4ReviewCaseEvent,
    ADV4ReviewDraftRevision, ADV4ReviewRequest, ADV4ReviewRejection,
    ADV4SignoffEvent, OrganizationMembership, User,
)
from app.services.ad_v4_candidates import VALIDATOR_VERSION_V2
from test_ad_v4_applicability_postgres import _enable, _store

URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PAPRNAV_TEST_POSTGRES_URL required")
VERSION = "paprnav-ad-v4-candidate-review-1"
MODELS = (ADV4ReviewCase, ADV4ReviewDraftRevision, ADV4ReviewRequest, ADV4ReviewRejection, ADV4SignoffEvent, ADV4ReviewCaseEvent)


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _hash(domain, payload):
    return hashlib.sha256(domain.encode() + b"\0" + payload).hexdigest()


def _time(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _auth(db, user, member, action, now):
    a = db.get(User, user)
    m = db.get(OrganizationMembership, member)
    stable = dict(version="paprnav-ad-v4-review-authorization-1", policyName=VERSION,
        policyVersion="1", action=action, actorUserId=user, authorizingMembershipId=member,
        organizationId=m.organization_id, userStatus="active", membershipStatus="active",
        role="platform_admin", validityRule="status_only_v1", validFrom=None, validUntil=None,
        userUpdatedAt=_time(a.updated_at), membershipUpdatedAt=_time(m.updated_at), serverAuthorized=True)
    result = dict(stable, decisionTime=_time(now),
        authorizationObservationHash=_hash("paprnav-ad-v4-review-auth-observation-1", _bytes(stable)),
        claimsHash=_hash("paprnav-ad-v4-review-claims-1", _bytes(stable)))
    return result


def _seal(model, values):
    row = {column.name: values.get(column.name) for column in model.__table__.c}
    scalar = {key: _time(value) if isinstance(value, datetime) else value
        for key, value in row.items() if not key.endswith("_bytes")
        and key not in {"row_hash", "event_hash", "signature_hash"}}
    row["canonical_bytes"] = _bytes(dict(version=VERSION, table=model.__tablename__, record=scalar))
    row["event_hash" if model is ADV4ReviewCaseEvent else "row_hash"] = _hash("paprnav-ad-v4-review-row-1", row["canonical_bytes"])
    if model is ADV4SignoffEvent:
        row["signature_hash"] = _hash("paprnav-ad-v4-review-signature-1", row["canonical_bytes"])
    return row


def _scope(common):
    return {key: common[key] for key in ("auth_policy_version", "endpoint_action", "idempotency_key", "request_canonical_bytes", "request_hash")}


def _assert_authoritative_byte_total(db, case_id):
    # Independent metadata-driven accounting detects an omitted byte column
    # in the migration's deliberately explicit, non-JSON SQL helper.
    total = 0
    for model in MODELS:
        columns = [column for column in model.__table__.c if column.name.endswith("_bytes")]
        owner = model.id if model is ADV4ReviewCase else model.case_id
        for row in db.execute(select(*columns).where(owner == case_id)):
            total += sum(len(value) if value is not None else 0 for value in row)
    assert db.scalar(text("SELECT paprnav_v4_review_case_authoritative_bytes(:c)"), dict(c=case_id)) == total
    return total


class Records:
    def __init__(self, db, *, validator_version=VALIDATOR_VERSION_V2):
        self.db = db
        _enable(db)
        for gate in ("reviewer4_draft_enabled", "reviewer4_decision_enabled"):
            db.execute(text("SELECT paprnav_set_v4_feature_gate(:g,true,'review-test')"), dict(g=gate))
        db.commit()
        self.user, self.member, self.directive, self.proposal = _store(db,
            validator_version=validator_version, suffix=uuid.uuid4().hex)
        self.case = "arc_" + uuid.uuid4().hex
        self.head = None
        self.sequence = 0

    def common(self, action, now):
        auth = _auth(self.db, self.user, self.member, action, now)
        auth_bytes = _bytes(auth)
        return dict(id="arr_" + uuid.uuid4().hex, proposal_id=self.proposal,
            directive_id=self.directive, actor_user_id=self.user,
            authorizing_membership_id=self.member, organization_id=auth["organizationId"],
            auth_snapshot_bytes=auth_bytes, auth_snapshot_hash=_hash("paprnav-ad-v4-review-authorization-1", auth_bytes),
            contract_version=VERSION, auth_policy_version="1", endpoint_action=action, idempotency_key=uuid.uuid4().hex)

    def observation(self, now):
        p = self.db.get(ADV4CandidateProposal, self.proposal)
        heads = self.db.scalar(text("SELECT paprnav_v4_review_cutoff(:p)->'fragmentHeads'"), dict(p=self.proposal))
        identity = dict(version="paprnav-ad-v4-review-input-identity-1", directiveId=self.directive,
            proposal=dict(state="verified", id=self.proposal, storedCanonicalHash=p.canonical_hash, verifiedCanonicalHash=p.canonical_hash),
            evidence=dict(state="verified", storedBindingHash=p.evidence_binding_hash, verifiedBindingHash=p.evidence_binding_hash, headSetHash=_hash("paprnav-ad-v4-review-evidence-heads-1", _bytes(heads))),
            applicabilityProjection=dict(state="missing", errorCode="projection_missing"),
            obligationProjection=dict(state="missing", errorCode="projection_missing"))
        if getattr(self, "mutate_identity", None):
            self.mutate_identity(identity)
        identity_bytes = _bytes(identity)
        identity_hash = _hash("paprnav-ad-v4-review-input-identity-1", identity_bytes)
        observation = _bytes(dict(version="paprnav-ad-v4-review-observation-1", inputIdentityHash=identity_hash, observedAt=_time(now)))
        return dict(input_identity_bytes=identity_bytes, input_identity_hash=identity_hash,
            observation_bytes=observation, observation_hash=_hash("paprnav-ad-v4-review-observation-1", observation), observed_at=now)

    def event(self, common, kind, state, now, **objects):
        body = {} if kind == "case_created" else dict(expectedPredecessorEventHash=self.head)
        body.update(expectedAuthorizationObservationHash=json.loads(common["auth_snapshot_bytes"])["authorizationObservationHash"], expectedInputIdentityHash=self.observation(now)["input_identity_hash"])
        if kind == "review_requested":
            body["draftRevisionId"] = None
        if kind == "review_rejected":
            body["expectedRequestId"] = objects["review_request_id"]
            body["reasonCodes"] = ["projection_integrity"]
            body["explanation"] = "Both projections are missing."
        payload = _bytes(dict(version=VERSION, action=json.loads(common["auth_snapshot_bytes"])["action"], directiveId=self.directive, proposalId=self.proposal, caseId=None if kind == "case_created" else self.case, body=body))
        common.update(request_canonical_bytes=payload, request_hash=_hash("paprnav-ad-v4-review-request-1", payload))
        result = _seal(ADV4ReviewCaseEvent, dict(common, id="are_" + uuid.uuid4().hex,
            case_id=self.case, sequence_number=self.sequence, predecessor_event_hash=self.head,
            event_type=kind, resulting_state=state, auth_policy_version="1",
            endpoint_action=json.loads(common["auth_snapshot_bytes"])["action"], idempotency_key=common["idempotency_key"],
            request_canonical_bytes=payload, request_hash=_hash("paprnav-ad-v4-review-request-1", payload), occurred_at=now, **objects))
        self.head = result["event_hash"]
        self.sequence += 1
        return result

    def create(self, mutate_body=None):
        now = datetime.now(timezone.utc)
        common = self.common("create_ad_v4_review_case", now)
        event = self.event(common, "case_created", "draft", now)
        if mutate_body:
            request = json.loads(event["request_canonical_bytes"])
            mutate_body(request["body"])
            event["request_canonical_bytes"] = _bytes(request)
            event["request_hash"] = _hash("paprnav-ad-v4-review-request-1", event["request_canonical_bytes"])
            event = _seal(ADV4ReviewCaseEvent, event)
            common.update(_scope(event))
        case = _seal(ADV4ReviewCase, dict(common, **self.observation(now), id=self.case,
            proposal_canonical_hash=self.db.get(ADV4CandidateProposal, self.proposal).canonical_hash,
            case_sequence=0, predecessor_case_id=None, created_at=now))
        self.db.execute(ADV4ReviewCase.__table__.insert(), case)
        self.db.execute(ADV4ReviewCaseEvent.__table__.insert(), event)
        self.db.commit()
        return case


def test_review_migration_metadata_matches_six_table_contract():
    engine = create_engine(URL)
    with engine.connect() as connection:
        catalog = inspect(connection)
        for model in MODELS:
            actual = {column["name"] for column in catalog.get_columns(model.__tablename__)}
            assert actual == set(model.__table__.c.keys())
            assert len(catalog.get_check_constraints(model.__tablename__)) == len([c for c in model.__table__.constraints if c.__class__.__name__ == "CheckConstraint"])
        assert connection.scalar(text("SELECT count(*) FROM pg_trigger WHERE tgname LIKE 'trg_ar4_%' AND NOT tgisinternal")) == 18
        for function, mode in (("paprnav_v4_validate_submission", "UPDATE"), ("paprnav_v4_validate_app_request", "SHARE")):
            definition = connection.scalar(text(f"SELECT pg_get_functiondef('{function}()'::regprocedure)"))
            user_lock = f"SELECT * INTO u FROM users WHERE id=NEW.actor_user_id FOR {mode};"
            member_lock = f"SELECT * INTO m FROM organization_memberships WHERE id=NEW.authorizing_membership_id FOR {mode};"
            assert definition.index(user_lock) < definition.index(member_lock)
    engine.dispose()


def test_direct_review_creation_and_graph_free_rejection_commit():
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        now = datetime.now(timezone.utc)
        common = records.common("request_ad_v4_review", now)
        cutoff = db.scalar(text("SELECT paprnav_v4_review_cutoff(:p)"), dict(p=records.proposal))
        authors = db.scalar(text("SELECT paprnav_v4_review_authors(:p)"), dict(p=records.proposal))
        request = _seal(ADV4ReviewRequest, dict(common, **records.observation(now), case_id=records.case,
            draft_revision_id=None, expected_predecessor_event_hash=records.head,
            cutoff_bytes=_bytes(cutoff), cutoff_hash=_hash("paprnav-ad-v4-review-cutoff-1", _bytes(cutoff)),
            authorship_set_bytes=_bytes(authors), authorship_set_hash=_hash("paprnav-ad-v4-review-authorship-1", _bytes(authors)),
            authorship_source_count=len(authors["bindings"]), requested_at=now))
        event = records.event(common, "review_requested", "pending_review", now, review_request_id=request["id"])
        request = _seal(ADV4ReviewRequest, dict(request, **_scope(common)))
        db.execute(ADV4ReviewRequest.__table__.insert(), request)
        db.execute(ADV4ReviewCaseEvent.__table__.insert(), event)
        db.commit()
        now = datetime.now(timezone.utc)
        common = records.common("reject_ad_v4_review", now)
        observation = records.observation(now)
        reason_bytes = _bytes(dict(version="paprnav-ad-v4-review-reasons-1", codes=["projection_integrity"], explanation="Both projections are missing."))
        rejection = _seal(ADV4ReviewRejection, dict(common, case_id=records.case, request_id=request["id"],
            proposal_canonical_hash=case["proposal_canonical_hash"], requested_input_identity_hash=request["input_identity_hash"],
            requested_observation_hash=request["observation_hash"], **{"decision_"+key:value for key,value in observation.items()},
            reasons_bytes=reason_bytes, reasons_hash=_hash("paprnav-ad-v4-review-reasons-1", reason_bytes), expected_predecessor_event_hash=records.head, rejected_at=now))
        signoff = _seal(ADV4SignoffEvent, dict(common, id="ars_"+uuid.uuid4().hex, case_id=records.case,
            request_id=request["id"], rejection_id=rejection["id"], action="reject", rejection_hash=rejection["row_hash"],
            requested_input_identity_hash=request["input_identity_hash"], requested_observation_hash=request["observation_hash"],
            decision_input_identity_hash=observation["input_identity_hash"], decision_observation_hash=observation["observation_hash"],
            authorization_observation_hash=json.loads(common["auth_snapshot_bytes"])["authorizationObservationHash"], signed_at=now))
        event = records.event(common, "review_rejected", "rejected", now, review_request_id=request["id"], rejection_id=rejection["id"], signoff_id=signoff["id"])
        rejection = _seal(ADV4ReviewRejection, dict(rejection, **_scope(common)))
        signoff = _seal(ADV4SignoffEvent, dict(signoff, **_scope(common), rejection_hash=rejection["row_hash"]))
        db.execute(ADV4ReviewRejection.__table__.insert(), rejection)
        db.execute(ADV4SignoffEvent.__table__.insert(), signoff)
        db.execute(ADV4ReviewCaseEvent.__table__.insert(), event)
        db.commit()
        assert db.scalar(select(ADV4ReviewCaseEvent.resulting_state).where(ADV4ReviewCaseEvent.id==event["id"])) == "rejected"
        assert 0 < _assert_authoritative_byte_total(db, records.case) < 16 * 1024 * 1024
        db.execute(text("UPDATE users SET status='inactive' WHERE id=:u"), dict(u=records.user))
        db.commit()
        db.execute(text("SELECT paprnav_v4_review_require_complete(:c)"), dict(c=records.case))
        db.rollback()
    engine.dispose()


def test_orphan_case_and_immutable_update_fail_closed():
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        with pytest.raises(DBAPIError):
            db.execute(text("UPDATE ad_v4_review_cases SET case_sequence=1 WHERE id=:c"), dict(c=records.case))
        db.rollback()
        duplicate = dict(case, id="arc_"+uuid.uuid4().hex, case_sequence=1, predecessor_case_id=case["id"])
        duplicate = _seal(ADV4ReviewCase, duplicate)
        with pytest.raises(DBAPIError):
            db.execute(ADV4ReviewCase.__table__.insert(), duplicate)
            db.commit()
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("attack,expected", [
    ("auth_claim", "authorization snapshot differs"),
    ("false_proposal_hash", "observed proposal differs"),
    ("observation_time", "observation identity differs"),
    ("missing_projection_with_id", "required or forbidden keys differ"),
    ("writer_disabled", "feature gate disabled"),
])
def test_direct_sql_cannot_forge_review_observation_or_authorization(attack, expected):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        forged = dict(case, id="arc_"+uuid.uuid4().hex, case_sequence=1, predecessor_case_id=case["id"])
        if attack == "auth_claim":
            value = json.loads(forged["auth_snapshot_bytes"])
            value["validityRule"] = "invented_expiry_rule"
            forged["auth_snapshot_bytes"] = _bytes(value)
            forged["auth_snapshot_hash"] = _hash("paprnav-ad-v4-review-authorization-1", forged["auth_snapshot_bytes"])
        elif attack == "observation_time":
            value = json.loads(forged["observation_bytes"])
            value["observedAt"] = "2000-01-01T00:00:00.000000Z"
            forged["observation_bytes"] = _bytes(value)
            forged["observation_hash"] = _hash("paprnav-ad-v4-review-observation-1", forged["observation_bytes"])
        elif attack == "writer_disabled":
            db.execute(text("SELECT paprnav_set_v4_feature_gate('reviewer4_draft_enabled',false,'review-test')"))
            db.commit()
        else:
            value = json.loads(forged["input_identity_bytes"])
            if attack == "false_proposal_hash":
                value["proposal"]["storedCanonicalHash"] = "a"*64
            else:
                value["applicabilityProjection"]["id"] = "avp_forged"
            forged["input_identity_bytes"] = _bytes(value)
            forged["input_identity_hash"] = _hash("paprnav-ad-v4-review-input-identity-1", forged["input_identity_bytes"])
            observation = json.loads(forged["observation_bytes"])
            observation["inputIdentityHash"] = forged["input_identity_hash"]
            forged["observation_bytes"] = _bytes(observation)
            forged["observation_hash"] = _hash("paprnav-ad-v4-review-observation-1", forged["observation_bytes"])
        forged = _seal(ADV4ReviewCase, forged)
        with pytest.raises(DBAPIError, match=expected):
            db.execute(ADV4ReviewCase.__table__.insert(), forged)
            db.commit()
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("attack,expected", [
    ("missing_field", "request body shape differs"),
    ("extra_field", "request body shape differs"),
    ("input_cas", "request compare-and-swap differs"),
    ("auth_cas", "request compare-and-swap differs"),
])
def test_self_consistently_restamped_request_must_bind_exact_case(attack, expected):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        def mutate(body):
            if attack == "missing_field":
                body.pop("expectedInputIdentityHash")
            elif attack == "extra_field":
                body["publish"] = True
            elif attack == "input_cas":
                body["expectedInputIdentityHash"] = "a"*64
            else:
                body["expectedAuthorizationObservationHash"] = "b"*64
        with pytest.raises(DBAPIError, match=expected):
            records.create(mutate_body=mutate)
        db.rollback()
        assert db.get(ADV4ReviewCase, records.case) is None
    engine.dispose()


@pytest.mark.parametrize("family,state,changes,removed,expected", [
    ("evidence", "missing", {"headSetHash": "not-a-hash"}, ["verifiedBindingHash"], "nested identity encoding"),
    ("evidence", "integrity_error", {"headSetHash": "not-a-hash"}, ["verifiedBindingHash"], "nested identity encoding"),
    ("evidence", "integrity_error", {"headSetHash": "a"*64}, ["verifiedBindingHash"], "evidence head set differs"),
    ("evidence", "missing", {}, ["verifiedBindingHash", "headSetHash"], "falsely missing evidence"),
    ("evidence", "stale", {}, ["verifiedBindingHash", "headSetHash"], "required or forbidden keys"),
    ("evidence", "integrity_error", {"headSetHash": None}, ["verifiedBindingHash"], "observation branch differs"),
    ("proposal", "integrity_error", {}, [], "required or forbidden keys"),
    ("proposal", "stale", {"storedCanonicalHash": "bad"}, ["verifiedCanonicalHash"], "nested identity encoding"),
    ("proposal", "missing", {}, ["verifiedCanonicalHash"], "observed proposal differs"),
    ("applicabilityProjection", "integrity_error", {}, [], "required or forbidden keys"),
    ("applicabilityProjection", "integrity_error", {"id": "avp_absent", "storedHash": "a"*64}, [], "projection binding differs"),
    ("obligationProjection", "missing", {"eventHeadHash": "not-a-hash"}, [], "nested identity encoding"),
    ("obligationProjection", "unsupported_version", {"id": 12, "storedHash": "a"*64}, [], "observation branch differs"),
])
def test_fully_resealed_observation_union_negatives(family, state, changes, removed, expected):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        def mutate(identity):
            component = identity[family]
            component["state"] = state
            component["errorCode"] = "missing_evidence" if state == "missing" and family == "evidence" else "projection_integrity" if "Projection" in family else "candidate_integrity"
            component.update(changes)
            for key in removed:
                component.pop(key, None)
        records.mutate_identity = mutate
        with pytest.raises(DBAPIError, match=expected):
            records.create()
        db.rollback()
        assert db.get(ADV4ReviewCase, records.case) is None
    engine.dispose()


def _materialize_review_fixture(records):
    from app.core.config import get_settings
    from app.services.ad_v4_applicability import materialize_applicability
    from app.services.ad_v4_obligation_persistence import materialize_obligations
    os.environ["PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED"] = "true"
    get_settings.cache_clear()
    db = records.db
    db.execute(text("SELECT paprnav_set_v4_feature_gate('materializer3b_enabled',true,'review-test')"))
    app = materialize_applicability(db, directive_id=records.directive, proposal_id=records.proposal,
        actor=db.get(User, records.user), membership_id=records.member, idempotency_key=uuid.uuid4().hex)
    db.commit()
    obligation = materialize_obligations(db, directive_id=records.directive, proposal_id=records.proposal,
        app_projection_id=app.projection.id, actor=db.get(User, records.user), membership_id=records.member,
        idempotency_key=uuid.uuid4().hex)
    db.commit()
    result = {}
    for name, projection, event_model in (
        ("applicabilityProjection", app.projection, ADV4CandidateAppProjectionEvent),
        ("obligationProjection", obligation.projection, ADV4CandidateObligationProjectionEvent),
    ):
        event = db.scalar(select(event_model).where(event_model.projection_id==projection.id).order_by(event_model.sequence_number.desc()))
        result[name] = dict(state="verified", id=projection.id, storedHash=projection.projection_hash, eventHeadHash=event.event_hash)
    return result


@pytest.mark.parametrize("family,state,with_head", [
    ("proposal", "verified", False), ("proposal", "integrity_error", False),
    ("proposal", "stale", False), ("proposal", "unsupported_version", False),
    ("evidence", "verified", True), ("evidence", "missing", False),
    ("evidence", "stale", True), ("evidence", "integrity_error", False),
    ("evidence", "integrity_error", True), ("evidence", "unsupported_version", False),
    ("evidence", "unsupported_version", True),
    ("applicabilityProjection", "verified", True), ("applicabilityProjection", "missing", False),
    ("applicabilityProjection", "stale", True), ("applicabilityProjection", "integrity_error", True),
    ("applicabilityProjection", "unsupported_version", True), ("applicabilityProjection", "integrity_error", False),
    ("applicabilityProjection", "unsupported_version", False),
    ("obligationProjection", "verified", True), ("obligationProjection", "missing", False),
    ("obligationProjection", "stale", True), ("obligationProjection", "integrity_error", True),
    ("obligationProjection", "unsupported_version", True), ("obligationProjection", "integrity_error", False),
    ("obligationProjection", "unsupported_version", False),
])
def test_observation_branch_shapes_commit_and_match_python(family, state, with_head):
    from app.services.ad_v4_reviews import _verify_observation, _verify_observation_sources
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        projections = _materialize_review_fixture(records) if "Projection" in family and state != "missing" else None
        if projections and not with_head:
            event_table = "ad_v4_candidate_app_projection_events" if family == "applicabilityProjection" else "ad_v4_candidate_obligation_projection_events"
            db.execute(text(f"ALTER TABLE {event_table} DISABLE TRIGGER USER"))
            db.execute(text(f"DELETE FROM {event_table} WHERE projection_id=:p"), dict(p=projections[family]["id"]))
            db.execute(text(f"ALTER TABLE {event_table} ENABLE TRIGGER USER"))
            projections[family].pop("eventHeadHash")
            if family == "applicabilityProjection":
                projections["obligationProjection"].update(state="integrity_error", errorCode="projection_integrity")
        if family == "evidence" and state == "missing":
            # Model pre-existing source corruption. Restore guards before any
            # review insertion; the review must accurately retain absence.
            db.execute(text("ALTER TABLE ad_v4_candidate_evidence_bindings DISABLE TRIGGER USER"))
            db.execute(text("DELETE FROM ad_v4_candidate_evidence_bindings WHERE proposal_id=:p"), dict(p=records.proposal))
            db.execute(text("ALTER TABLE ad_v4_candidate_evidence_bindings ENABLE TRIGGER USER"))
        def mutate(identity):
            if projections:
                identity.update({key:dict(value) for key,value in projections.items()})
            component = identity[family]
            component["state"] = state
            if state != "verified":
                component.pop("verifiedCanonicalHash", None)
                component.pop("verifiedBindingHash", None)
                component["errorCode"] = "missing_evidence" if family == "evidence" and state == "missing" else "unsupported_version" if state == "unsupported_version" else "candidate_integrity" if family == "proposal" else "evidence_not_current" if family == "evidence" and state == "stale" else "evidence_integrity" if family == "evidence" else "projection_missing" if state == "missing" else "projection_integrity"
            if family == "evidence" and not with_head:
                component.pop("headSetHash", None)
        records.mutate_identity = mutate
        records.create()
        row = db.get(ADV4ReviewCase, records.case)
        _verify_observation(row)
        _verify_observation_sources(db, row)
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("family", ["applicabilityProjection", "obligationProjection"])
@pytest.mark.parametrize("attack", ["false_missing", "wrong_head", "omitted_head", "wrong_stored_hash"])
def test_resealed_projection_observations_bind_actual_rows_and_heads(family, attack):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        projections = _materialize_review_fixture(records)
        def mutate(identity):
            identity.update({key:dict(value) for key,value in projections.items()})
            component = identity[family]
            component.update(state="integrity_error", errorCode="projection_integrity")
            if attack == "false_missing":
                identity[family] = dict(state="missing", errorCode="projection_missing")
            elif attack == "wrong_head":
                component["eventHeadHash"] = "a"*64
            elif attack == "omitted_head":
                component.pop("eventHeadHash")
            else:
                component["storedHash"] = "b"*64
        records.mutate_identity = mutate
        with pytest.raises(DBAPIError, match="projection binding differs"):
            records.create()
        db.rollback()
        assert db.get(ADV4ReviewCase, records.case) is None
    engine.dispose()


@pytest.mark.parametrize("family", ["applicabilityProjection", "obligationProjection"])
def test_resealed_nonverified_projection_rejects_cross_directive_source(family):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        other = Records(db)
        projections = _materialize_review_fixture(records)
        table = "ad_v4_candidate_app_projections" if family == "applicabilityProjection" else "ad_v4_candidate_obligation_projections"
        db.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
        db.execute(text(f"UPDATE {table} SET directive_id=:d WHERE id=:p"), dict(d=other.directive, p=projections[family]["id"]))
        db.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))
        def mutate(identity):
            identity.update({key:dict(value, state="integrity_error", errorCode="projection_integrity") for key,value in projections.items()})
        records.mutate_identity = mutate
        with pytest.raises(DBAPIError, match="projection binding differs"):
            records.create()
        db.rollback()
        assert db.get(ADV4ReviewCase, records.case) is None
    engine.dispose()


def _capacity_record(records, model, ordinal, case):
    if model is ADV4ReviewCase:
        return _seal(model, dict(case, id="arc_"+uuid.uuid4().hex,
            case_sequence=ordinal, predecessor_case_id=case["id"]))
    now = datetime.now(timezone.utc)
    action = "save_ad_v4_review_draft" if model is ADV4ReviewDraftRevision else "reject_ad_v4_review"
    common = records.common(action, now)
    observation = records.observation(now)
    body = dict(expectedAuthorizationObservationHash=json.loads(common["auth_snapshot_bytes"])["authorizationObservationHash"],
        expectedInputIdentityHash=observation["input_identity_hash"], expectedPredecessorEventHash=records.head)
    if model is ADV4ReviewDraftRevision:
        body.update(annotations=[], intendedAction="undecided")
    else:
        body.update(expectedRequestId="arq_"+"1"*32, reasonCodes=["projection_integrity"], explanation="Missing projections.")
    payload = _bytes(dict(version=VERSION, action=action, directiveId=records.directive, proposalId=records.proposal, caseId=records.case, body=body))
    common.update(request_canonical_bytes=payload, request_hash=_hash("paprnav-ad-v4-review-request-1", payload))
    if model is ADV4ReviewDraftRevision:
        annotations = _bytes(dict(version="paprnav-ad-v4-review-annotation-1", annotations=[]))
        return _seal(model, dict(common, **observation, case_id=records.case, revision_number=ordinal,
            predecessor_draft_id="ard_"+"1"*32 if ordinal else None, expected_predecessor_event_hash=records.head,
            annotation_bytes=annotations, annotation_hash=_hash("paprnav-ad-v4-review-annotation-1", annotations),
            intended_action="undecided", created_at=now))
    return _seal(model, dict(common, case_id=records.case, sequence_number=ordinal,
        predecessor_event_hash=records.head, event_type="review_rejected", resulting_state="rejected",
        draft_revision_id=None, review_request_id="arq_"+"1"*32, rejection_id="arr_"+"1"*32,
        signoff_id="ars_"+"1"*32, occurred_at=now))


@pytest.mark.parametrize("model,maximum,check", [
    (ADV4ReviewCase, 99, "ck_ar4_case_capacity"),
    (ADV4ReviewDraftRevision, 999, "ck_ar4_draft_capacity"),
    (ADV4ReviewCaseEvent, 1002, "ck_ar4_event_capacity"),
])
def test_direct_sql_capacity_ordinals_accept_boundary_reject_overflow(model, maximum, check):
    # Test the immediate ordinal boundary separately from the deferred full
    # history requirement. These deliberately incomplete probes never commit.
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        probe = _capacity_record(records, model, maximum, case)
        nested = db.begin_nested()
        db.execute(model.__table__.insert(), probe)
        nested.rollback()
        db.rollback()
        probe = _capacity_record(records, model, maximum+1, case)
        with pytest.raises(DBAPIError, match=check):
            db.execute(model.__table__.insert(), probe)
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("model,check,extra", [
    (ADV4ReviewCase, "ck_ar4_case_capacity", 100),
    (ADV4ReviewDraftRevision, "ck_ar4_draft_capacity", 1001),
    (ADV4ReviewCaseEvent, "ck_ar4_event_capacity", 1003),
])
def test_commit_validator_bounds_corrupted_overcapacity_history(model, check, extra):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        probe = _capacity_record(records, model, 1 if model is ADV4ReviewCaseEvent else 0, case)
        table = model.__tablename__
        # Corruption fixture: bypass immediate defenses transactionally so the
        # independent bounded recount is exercised before any history walk.
        db.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
        db.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT {check}"))
        template = {key: "\\x"+value.hex() if isinstance(value, bytes) else _time(value) if isinstance(value, datetime) else value for key,value in probe.items()}
        if model is ADV4ReviewCase:
            overrides = "jsonb_build_object('id','cap_'||lpad(g::text,32,'0'),'case_sequence',g,'predecessor_case_id',CASE WHEN g=1 THEN CAST(:case_id AS text) ELSE 'cap_'||lpad((g-1)::text,32,'0') END)"
        elif model is ADV4ReviewDraftRevision:
            overrides = "jsonb_build_object('id','cap_'||lpad(g::text,32,'0'),'revision_number',g-1,'predecessor_draft_id',CASE WHEN g=1 THEN NULL ELSE 'cap_'||lpad((g-1)::text,32,'0') END)"
        else:
            overrides = "jsonb_build_object('id','cap_'||lpad(g::text,32,'0'),'sequence_number',g,'event_type','draft_saved','resulting_state','draft','draft_revision_id','cap_'||lpad(g::text,32,'0'),'review_request_id',NULL,'rejection_id',NULL,'signoff_id',NULL,'idempotency_key','capacity-'||g,'event_hash',md5('event'||g)||md5('event2'||g),'predecessor_event_hash',md5('prior'||g)||md5('prior2'||g))"
        db.execute(text(f"INSERT INTO {table} SELECT (jsonb_populate_record(NULL::{table},CAST(:template AS jsonb)||{overrides})).* FROM generate_series(1,:extra) g"), dict(template=json.dumps(template), extra=extra, case_id=case["id"]))
        with pytest.raises(DBAPIError, match="history capacity exceeded"):
            db.execute(text("SELECT paprnav_v4_review_require_complete(:case_id)"), dict(case_id=case["id"]))
        db.rollback()  # Restores every dropped check/disabled trigger and row.
    engine.dispose()


def _seed_cutoff_sources(records, family, first, last):
    """Synthetic retained-source cardinality only; all changes are rolled back.

    Old source guards are bypassed for fixture setup, never review guards.
    This tests bounded review work, not candidate-submission validation.
    """
    db = records.db
    submission = db.scalar(text("SELECT to_jsonb(s) FROM ad_v4_candidate_submissions s WHERE proposal_id=:p LIMIT 1"), dict(p=records.proposal))
    if family == "submissions":
        table = "ad_v4_candidate_submissions"
        template = submission
        overrides = "jsonb_build_object('id','cut_'||lpad(g::text,32,'0'),'idempotency_key','cutoff-'||g)"
    else:
        table = "ad_v4_candidate_submission_relationships"
        template = dict(id="", submission_id=submission["id"], relationship_key="",
            relation_type="corrects_candidate", predecessor_proposal_id=records.proposal,
            reason="Synthetic capacity fixture", evidence_keys=[], canonical_bytes="\\x7b7d",
            relationship_hash="", validator_version=submission["validator_version"],
            canonicalization_version=submission["canonicalization_version"], created_at=submission["created_at"])
        overrides = "jsonb_build_object('id','cur_'||lpad(g::text,32,'0'),'relationship_key','cutoff-'||g,'relationship_hash',md5('cutoff'||g)||md5('cutoff2'||g))"
    db.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
    db.execute(text(f"INSERT INTO {table} SELECT (jsonb_populate_record(NULL::{table},CAST(:template AS jsonb)||{overrides})).* FROM generate_series(CAST(:first AS integer),CAST(:last AS integer)) g"), dict(template=json.dumps(template), first=first, last=last))
    db.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))


def _insert_cutoff_request(records, cutoff):
    db = records.db
    now = datetime.now(timezone.utc)
    common = records.common("request_ad_v4_review", now)
    authors = db.scalar(text("SELECT paprnav_v4_review_authors(:p)"), dict(p=records.proposal))
    request = dict(common, **records.observation(now), case_id=records.case,
        draft_revision_id=None, expected_predecessor_event_hash=records.head,
        cutoff_bytes=_bytes(cutoff), cutoff_hash=_hash("paprnav-ad-v4-review-cutoff-1", _bytes(cutoff)),
        authorship_set_bytes=_bytes(authors), authorship_set_hash=_hash("paprnav-ad-v4-review-authorship-1", _bytes(authors)),
        authorship_source_count=len(authors["bindings"]), requested_at=now)
    event = records.event(common, "review_requested", "pending_review", now, review_request_id=request["id"])
    request = _seal(ADV4ReviewRequest, dict(request, **_scope(common)))
    db.execute(ADV4ReviewRequest.__table__.insert(), request)
    db.execute(ADV4ReviewCaseEvent.__table__.insert(), event)


@pytest.mark.parametrize("family", ["submissions", "relationships"])
@pytest.mark.parametrize("overflow_source", ["live", "provided"])
def test_direct_sql_cutoff_2000_boundary_and_2001_overflow(family, overflow_source):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        records.create()
        original_head, original_sequence = records.head, records.sequence
        _seed_cutoff_sources(records, family, 2 if family == "submissions" else 1, 2000)
        cutoff = db.scalar(text("SELECT paprnav_v4_review_cutoff(:p)"), dict(p=records.proposal))
        assert len(cutoff[family]) == 2000
        boundary = db.begin_nested()
        _insert_cutoff_request(records, cutoff)
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        boundary.rollback()  # Keep synthetic source history isolated and recover draft state.
        records.head, records.sequence = original_head, original_sequence
        if overflow_source == "live":
            _seed_cutoff_sources(records, family, 2001, 2002)
            live = db.scalar(text("SELECT paprnav_v4_review_cutoff(:p)"), dict(p=records.proposal))
            assert len(live[family]) == 2001  # limit+1 sentinel even with 2002 rows
            # Still submit the previously valid 2000-item cutoff: the live
            # bound must fail before exact-cutoff comparison or authorship walk.
        else:
            cutoff[family].append(dict(cutoff[family][-1]))
            assert len(cutoff[family]) == 2001
        with pytest.raises(DBAPIError, match="cutoff capacity exceeded"):
            _insert_cutoff_request(records, cutoff)
        db.rollback()
    engine.dispose()


@pytest.mark.parametrize("excess,validation", [(0, "read"), (1, "read"), (1, "commit")])
def test_authoritative_byte_budget_exact_boundary_and_overflow(excess, validation):
    engine = create_engine(URL)
    with Session(engine) as db:
        records = Records(db)
        case = records.create()
        baseline = _assert_authoritative_byte_total(db, records.case)
        assert baseline > 0
        target = 16 * 1024 * 1024 + excess
        byte_columns = [c.name for c in ADV4ReviewDraftRevision.__table__.c if c.name.endswith("_bytes")]
        per_column, remainder = divmod(target - baseline, 3 * len(byte_columns))
        assert 2 <= per_column < 1024 * 1024
        # Corruption fixture bypasses only the insert guard. The normal
        # deferred commit trigger stays enabled, as do every CHECK and FK.
        # Invalid padded JSON ensures the budget precedes deep verification.
        db.execute(text("ALTER TABLE ad_v4_review_draft_revisions DISABLE TRIGGER trg_ar4_1_guard"))
        previous = None
        for ordinal in range(3):
            draft = _capacity_record(records, ADV4ReviewDraftRevision, ordinal, case)
            draft["predecessor_draft_id"] = previous
            previous = draft["id"]
            for column in byte_columns:
                draft[column] = b"x" * per_column
            if ordinal == 0:
                draft[byte_columns[0]] += b"x" * remainder
            db.execute(ADV4ReviewDraftRevision.__table__.insert(), draft)
        assert _assert_authoritative_byte_total(db, records.case) == target
        expected = "authoritative byte capacity exceeded" if excess else "object-event completeness differs"
        with pytest.raises(DBAPIError, match=expected):
            if validation == "commit":
                db.commit()
            else:
                db.execute(text("SELECT paprnav_v4_review_require_complete(:c)"), dict(c=records.case))
        db.rollback()  # Restores the insert guard and removes padded records.
    engine.dispose()


@pytest.mark.parametrize("source_model", [ADV4CandidateSubmission, ADV4CandidateAppMaterializationRequest])
def test_direct_sql_candidate_audit_and_review_share_actor_membership_order(source_model):
    """Hold U in review, force old writer to wait on U, then acquire M.

    The pre-0029 writer already owns M while waiting, so the actual review
    insertion closes U→M→U. The final writer waits on U without owning M.
    No audit trigger is bypassed and both real transactions must commit.
    """
    engine = create_engine(URL, connect_args={"options": "-c statement_timeout=10000 -c lock_timeout=8000"})
    try:
        with Session(engine) as db:
            records = Records(db)
            if source_model is ADV4CandidateAppMaterializationRequest:
                projections = _materialize_review_fixture(records)
                records.mutate_identity = lambda identity: identity.update({key:dict(value) for key,value in projections.items()})
            source = dict(db.execute(select(source_model.__table__).where(source_model.proposal_id == records.proposal).limit(1)).mappings().one())
            source.update(id="con_"+uuid.uuid4().hex, idempotency_key=uuid.uuid4().hex)
            db.commit()
            review_pid = db.scalar(text("SELECT pg_backend_pid()"))
            db.execute(text("SELECT id FROM users WHERE id=:u FOR UPDATE"), dict(u=records.user))
            candidate_pid = Queue()
            def insert_candidate_audit():
                with Session(engine) as writer:
                    candidate_pid.put(writer.scalar(text("SELECT pg_backend_pid()")))
                    writer.execute(source_model.__table__.insert(), source)
                    writer.commit()
                    return source["id"]
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(insert_candidate_audit)
                pid = candidate_pid.get(timeout=5)
                deadline = time.monotonic()+5
                with engine.connect() as observer:
                    while time.monotonic() < deadline:
                        blocked = observer.scalar(text("SELECT :review=ANY(pg_blocking_pids(:candidate))"), dict(review=review_pid, candidate=pid))
                        if blocked:
                            break
                        time.sleep(0.01)
                    assert blocked, "Candidate audit never blocked on the review actor lock"
                records.create()  # Must acquire M and commit, not deadlock.
                assert pending.result(timeout=10) == source["id"]
            assert db.scalar(select(source_model.id).where(source_model.id == source["id"])) == source["id"]
            db.execute(text("SELECT paprnav_v4_review_require_complete(:c)"), dict(c=records.case))
            db.rollback()
    finally:
        engine.dispose()
