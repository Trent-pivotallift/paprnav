"""Storage-failure remediation and bounded review-history service regressions."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from botocore.exceptions import (
    ClientError, ConnectionClosedError, ConnectTimeoutError, CredentialRetrievalError,
    EndpointConnectionError, IncompleteReadError, NoCredentialsError,
    PartialCredentialsError, ReadTimeoutError, ResponseStreamingError, SSLError,
)
from sqlalchemy import LargeBinary, event, func, insert, select, update
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragment, ADEvidenceFragmentLifecycleEvent, ADPublication,
    ADSourceDocument, ADSourcePageTextVersion, ADV4CandidateEvidenceBinding,
    ADV4CandidateProposal, ADV4CandidateSubmission, ADV4CandidateSubmissionRelationship,
    ADV4ReviewCase, ADV4ReviewCaseEvent, ADV4ReviewDraftRevision,
    ADV4ReviewRejection, ADV4ReviewRequest, ADV4SignoffEvent,
)
from app.services import ad_v4_reviews as review, storage
from app.services.ad_evidence import _hash_parts
from app.services.ad_v4_candidates import DOMAINS_V2, canonical_bytes, CANONICALIZATION_VERSION_V2
from test_ad_v4_reviews import _enable_app, _seed_review_source


def _source(db, *, backend="s3", source=None):
    actor, member, directive, proposal = source if source is not None else _seed_review_source(db)
    identifier = f"review-storage-{proposal.id}"
    document = ADSourceDocument(source_system="test", source_type="ad_rule", source_identifier=identifier,
        storage_backend=backend, storage_key="unavailable-source.pdf", content_hash=hashlib.sha256(b"source").hexdigest(),
        storage_bytes=6, captured_at=datetime.now(timezone.utc))
    db.add(document)
    db.flush()
    db.add(ADPublication(directive_id=directive.id, source_document_id=document.id,
                        source_system="test", source_type="ad_rule", source_identifier=identifier))
    page = ADSourcePageTextVersion(rendition_id=f"rendition-{document.id}"[:36], source_document_id=document.id,
        source_content_hash=document.content_hash, page_number=1, extractor_name="test", extractor_version="1",
        extractor_configuration_hash="a" * 64, page_text="source", text_hash=hashlib.sha256(b"source").hexdigest())
    db.add(page)
    db.flush()
    fragment = ADEvidenceFragment(directive_id=directive.id, source_document_id=document.id,
        source_content_hash=document.content_hash, rendition_id=page.rendition_id, page_text_version_id=page.id,
        page_start=1, page_end=1, character_start=0, character_end=6, exact_text="source",
        parser_name="test", parser_version="1", created_by_user_id=actor.id,
        fragment_hash=_hash_parts(directive.id, document.id, document.content_hash, page.rendition_id,
                                 page.id, 1, 1, 0, 6, None, None, None, None, None, "source", "test", "1"))
    db.add(fragment)
    db.flush()
    admitted = ADEvidenceFragmentLifecycleEvent(fragment_id=fragment.id, event_type="admitted",
        actor_user_id=actor.id, reason="test admission", sequence_number=0,
        event_hash=_hash_parts(fragment.id, fragment.fragment_hash, "admitted", actor.id, "test admission", 0, None))
    db.add(admitted)
    db.flush()
    binding = ADV4CandidateEvidenceBinding(proposal_id=proposal.id, directive_id=directive.id,
        evidence_key="ev-source", fragment_id=fragment.id, fragment_hash=fragment.fragment_hash,
        admitted_event_id=admitted.id, admitted_event_hash=admitted.event_hash,
        validator_version=proposal.validator_version, canonicalization_version=proposal.canonicalization_version)
    db.add(binding)
    proposal.parsed_json = {"evidenceBindings": {"ev-source": {"fragmentId": fragment.id, "fragmentHash": fragment.fragment_hash}}}
    envelope = {"version": "ad-v4-evidence-bindings-v2", "validatorVersion": proposal.validator_version,
        "canonicalizationVersion": proposal.canonicalization_version, "bindings": [{"evidenceKey": "ev-source",
        "fragmentId": fragment.id, "fragmentHash": fragment.fragment_hash, "admittedEventId": admitted.id,
        "admittedEventHash": admitted.event_hash}]}
    proposal.evidence_binding_bytes = canonical_bytes(envelope, CANONICALIZATION_VERSION_V2)
    proposal.evidence_binding_hash = hashlib.sha256(DOMAINS_V2["bindings"] + proposal.evidence_binding_bytes).hexdigest()
    proposal.binding_count = 1
    db.commit()
    return actor, member, directive, proposal


def _workflow(db, actor, member, directive, proposal, *, idempotency_key="create"):
    authority = dict(actor=actor, membership_id=member.id)
    observation = review.review_proposal_observation(db, directive_id=directive.id, proposal_id=proposal.id, **authority)
    case = review.create_review_case(db, directive_id=directive.id, proposal_id=proposal.id,
        idempotency_key=idempotency_key, expected_input_identity_hash=observation["inputIdentityHash"],
        expected_authorization_observation_hash=observation["authorizationObservationHashes"][review.ACTIONS["case_created"]],
        **authority)
    db.commit()
    return authority, case


def _args(db, authority, case, action):
    current = review.verified_review_case(db, case_id=case["caseId"], **authority)
    return dict(case_id=case["caseId"], expected_predecessor_event_hash=current["latestEventHash"],
        expected_input_identity_hash=current["inputIdentityHash"],
        expected_authorization_observation_hash=current["authorizationObservationHashes"][review.ACTIONS[action]], **authority)


@pytest.mark.parametrize("failure", ["NoSuchKey", "AccessDenied", "transport", "local_missing"])
def test_expected_storage_failure_keeps_observation_and_rejection_available(db_session, monkeypatch, tmp_path, failure):
    _enable_app(monkeypatch)
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "review-test")
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(tmp_path))
    get_settings.cache_clear()
    actor, member, directive, proposal = _source(db_session, backend="local" if failure == "local_missing" else "s3")
    calls = []
    if failure != "local_missing":
        def fail(**kwargs):
            calls.append(kwargs)
            if failure == "transport":
                raise EndpointConnectionError(endpoint_url="https://storage.test")
            raise ClientError({"Error": {"Code": failure}, "ResponseMetadata": {"HTTPStatusCode": 404 if failure == "NoSuchKey" else 403}}, "GetObject")
        monkeypatch.setattr(storage, "get_s3_client", lambda region: SimpleNamespace(get_object=fail))
    observation = review.observe_review_inputs(db_session, proposal.id)
    evidence = review._read_blob(observation["input_identity_bytes"])["evidence"]
    assert evidence["state"] == "integrity_error"
    assert evidence["errorCode"] == "source_identity_or_evidence_missing"
    assert "verifiedBindingHash" not in evidence
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    request = review.request_review(db_session, idempotency_key="request", **_args(db_session, authority, case, "review_requested"))
    db_session.commit()
    rejected = review.reject_review_case(db_session, idempotency_key="reject",
        expected_request_id=request["reviewRequestId"], reason_codes=["source_identity_or_evidence_missing"],
        explanation="Retained source is unavailable", **_args(db_session, authority, case, "review_rejected"))
    db_session.commit()
    assert rejected["state"] == "rejected"
    assert review.verified_review_case(db_session, case_id=case["caseId"], **authority)["signoff"]["action"] == "reject"
    if failure != "local_missing":
        assert calls


@pytest.mark.parametrize("code", sorted(review._STORAGE_UNAVAILABLE_CODES))
def test_expected_provider_error_codes_are_explicitly_classified(monkeypatch, code):
    error = ClientError({"Error": {"Code": code}}, "GetObject")
    def fail(document, **kwargs):
        raise error
    monkeypatch.setattr(review, "verified_retained_document_bytes", fail)
    assert review._retained_source_available(SimpleNamespace(storage_bytes=1)) is False


@pytest.mark.parametrize("error", [
    FileNotFoundError("missing"), PermissionError("denied"),
    EndpointConnectionError(endpoint_url="https://storage.test"),
    ConnectTimeoutError(endpoint_url="https://storage.test"),
    ReadTimeoutError(endpoint_url="https://storage.test"),
    ConnectionClosedError(endpoint_url="https://storage.test"),
    IncompleteReadError(actual_bytes=1, expected_bytes=2),
    ResponseStreamingError(error="stream unavailable"),
    SSLError(endpoint_url="https://storage.test", error="transport failed"),
    CredentialRetrievalError(provider="test", error_msg="unavailable"),
    NoCredentialsError(), PartialCredentialsError(provider="test", cred_var="secret_key"),
])
def test_expected_transport_and_unavailability_exceptions_are_classified(monkeypatch, error):
    def fail(document, **kwargs):
        raise error
    monkeypatch.setattr(review, "verified_retained_document_bytes", fail)
    assert review._retained_source_available(SimpleNamespace(storage_bytes=1)) is False


@pytest.mark.parametrize("error", [
    TypeError("programmer error"), KeyError("malformed SDK response"), RuntimeError("programmer error"),
    ValueError("SDK argument validation"), OperationalError("SELECT broken", {}, RuntimeError("database failed")),
    ClientError({"Error": {"Code": "InvalidRequest"}, "ResponseMetadata": {"HTTPStatusCode": 400}}, "GetObject"),
])
def test_unexpected_storage_or_database_exceptions_are_not_reclassified(db_session, monkeypatch, error):
    _, _, _, proposal = _source(db_session)
    def fail(document, **kwargs):
        raise error
    monkeypatch.setattr(review, "verified_retained_document_bytes", fail)
    with pytest.raises(type(error)) as captured:
        review._evidence_observation(db_session, proposal)
    assert captured.value is error


def test_history_capacity_leaves_request_and_rejection_slots(db_session, monkeypatch):
    _enable_app(monkeypatch)
    assert (review.MAX_CASES_PER_PROPOSAL, review.MAX_DRAFT_REVISIONS_PER_CASE, review.MAX_EVENTS_PER_CASE) == (100, 1000, 1003)
    monkeypatch.setattr(review, "MAX_CASES_PER_PROPOSAL", 1)
    monkeypatch.setattr(review, "MAX_DRAFT_REVISIONS_PER_CASE", 2)
    monkeypatch.setattr(review, "MAX_EVENTS_PER_CASE", 5)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    draft = None
    for index in range(2):
        draft = review.save_review_draft(db_session, idempotency_key=f"draft-{index}", annotations=[],
            **_args(db_session, authority, case, "draft_saved"))
        db_session.commit()
    with pytest.raises(review.ADV4Error) as exceeded:
        review.save_review_draft(db_session, idempotency_key="draft-overflow", annotations=[],
            **_args(db_session, authority, case, "draft_saved"))
    assert exceeded.value.code == "review_history_limit"
    db_session.rollback()
    request = review.request_review(db_session, idempotency_key="request", draft_revision_id=draft["draftRevisionId"],
        **_args(db_session, authority, case, "review_requested"))
    db_session.commit()
    review.reject_review_case(db_session, idempotency_key="reject", expected_request_id=request["reviewRequestId"],
        reason_codes=["remediation_requested"], explanation="Repair needed",
        **_args(db_session, authority, case, "review_rejected"))
    db_session.commit()
    current = review.verified_review_case(db_session, case_id=case["caseId"], **authority)
    assert current["eventTotal"] == 5
    with pytest.raises(review.ADV4Error) as exceeded_cases:
        review.create_review_case(db_session, directive_id=directive.id, proposal_id=proposal.id,
            idempotency_key="successor-overflow", expected_input_identity_hash=current["inputIdentityHash"],
            expected_authorization_observation_hash=current["authorizationObservationHashes"][review.ACTIONS["case_created"]], **authority)
    assert exceeded_cases.value.code == "review_history_limit"


@pytest.mark.parametrize("capacity", ["MAX_EVENTS_PER_CASE", "MAX_DRAFT_REVISIONS_PER_CASE"])
def test_history_queries_limit_plus_one_and_fail_closed_on_overflow(db_session, monkeypatch, capacity):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    review.save_review_draft(db_session, idempotency_key="draft", annotations=[],
        **_args(db_session, authority, case, "draft_saved"))
    db_session.commit()
    monkeypatch.setattr(review, capacity, 1 if capacity == "MAX_EVENTS_PER_CASE" else 0)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        with pytest.raises(review.ADV4Error) as captured:
            review.verified_review_case(db_session, case_id=case["caseId"], **authority)
        assert captured.value.code == "review_integrity"
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    model = ADV4ReviewCaseEvent if capacity == "MAX_EVENTS_PER_CASE" else ADV4ReviewDraftRevision
    reads = [stmt for stmt in statements if model.__table__ in stmt.get_final_froms() and stmt._limit_clause is not None]
    assert len(reads) == 1
    assert reads[0]._limit_clause.value == getattr(review, capacity) + 1
    assert len(statements) <= 6


def test_case_overflow_query_and_predecessor_queries_are_bounded(db_session, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        review.verified_review_case(db_session, case_id=case["caseId"], **authority)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    limited = [stmt._limit_clause.value for stmt in statements
               if ADV4ReviewCase.__table__ in stmt.get_final_froms() and stmt._limit_clause is not None]
    assert review.MAX_CASES_PER_PROPOSAL + 1 in limited
    assert 2 in limited
    # A bounded query detects excess rows before materializing their full graph.
    with pytest.raises(review.ADV4Error) as captured:
        review._bounded_rows(db_session, select(ADV4ReviewCase).where(ADV4ReviewCase.proposal_id == proposal.id),
                             limit=0, label="test overflow")
    assert captured.value.code == "review_integrity"


def _submission(actor, member, directive, proposal, number):
    return ADV4CandidateSubmission(proposal_id=proposal.id, directive_id=directive.id,
        actor_kind="platform_admin", actor_user_id=actor.id, authorizing_membership_id=member.id,
        organization_id=member.organization_id, actor_role="platform_admin", actor_status="active",
        auth_policy_name="test", auth_policy_version="1", auth_claims_hash="a" * 64,
        endpoint_action="test", idempotency_key=f"submission-{number}", request_hash="b" * 64,
        request_canonical_bytes=b"{}", raw_transport_hash="c" * 64,
        validator_version=proposal.validator_version, canonicalization_version=proposal.canonicalization_version)


@pytest.mark.parametrize("inventory", ["submissions", "relationships"])
def test_source_cutoff_real_2000_boundary_and_overflow(db_session, inventory):
    actor, member, directive, proposal = _seed_review_source(db_session)
    assert review.MAX_ARRAY_ITEMS == 2000
    if inventory == "submissions":
        def source(number):
            return _submission(actor, member, directive, proposal, number)
        model = ADV4CandidateSubmission
    else:
        submission = _submission(actor, member, directive, proposal, 0)
        db_session.add(submission)
        db_session.flush()
        def source(number):
            return ADV4CandidateSubmissionRelationship(submission_id=submission.id,
                relationship_key=f"relationship-{number}", relation_type="corrects_candidate",
                predecessor_proposal_id=proposal.id, reason="test bounded lookup", evidence_keys=[],
                canonical_bytes=b"{}", relationship_hash=f"{number + 1:064x}")
        model = ADV4CandidateSubmissionRelationship
    db_session.add_all([source(number) for number in range(2000)])
    db_session.flush()
    cutoff = review._cutoff(db_session, proposal.id)
    assert len(cutoff[inventory]) == 2000
    db_session.add(source(2000))
    db_session.flush()
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        with pytest.raises(review.ADV4Error) as captured:
            review._cutoff(db_session, proposal.id)
        assert captured.value.code == "review_history_limit"
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    relevant = [stmt for stmt in statements if model.__tablename__ in str(stmt)]
    assert relevant[-1]._limit_clause.value == 2001
    assert len(statements) <= 2
    # Historical validation also refuses oversized arrays before querying IDs.
    cutoff[inventory].append(cutoff[inventory][-1])
    request = SimpleNamespace(proposal_id=proposal.id)
    with pytest.raises(review.ADV4Error) as stored:
        review._verify_frozen_sources(db_session, request, {"cutoff": cutoff})
    assert stored.value.code == "review_integrity"


def test_repeated_history_identity_uses_constant_source_verification_queries(db_session, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    for number in range(10):
        review.save_review_draft(db_session, idempotency_key=f"draft-{number}", annotations=[],
            **_args(db_session, authority, case, "draft_saved"))
        db_session.commit()
    original = review._verify_observation_sources
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(review, "_verify_observation_sources", counted)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        result = review.verified_review_case(db_session, case_id=case["caseId"], **authority)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert result["draftTotal"] == 10 and result["eventTotal"] == 11
    assert len(calls) == 1
    assert len(statements) <= 20


def test_unavailable_retained_source_result_is_cached_only_within_one_read(db_session, monkeypatch):
    _, _, _, proposal = _source(db_session)
    calls = []
    def unavailable(document, **kwargs):
        calls.append(document.id)
        raise FileNotFoundError("expected missing retained source")
    monkeypatch.setattr(review, "verified_retained_document_bytes", unavailable)
    cache = {}
    for _ in range(3):
        observed = review._evidence_observation(db_session, proposal, document_cache=cache)
        assert observed["errorCode"] == "source_identity_or_evidence_missing"
    assert len(calls) == 1
    review._evidence_observation(db_session, proposal, document_cache={})
    assert len(calls) == 2


def _complete_history(db, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db)
    authority, case = _workflow(db, actor, member, directive, proposal)
    draft = review.save_review_draft(db, idempotency_key="draft", annotations=[
        {"pointer": "/metadata", "text": "Keep the original extraction intact"}],
        **_args(db, authority, case, "draft_saved"))
    db.commit()
    request = review.request_review(db, idempotency_key="request", draft_revision_id=draft["draftRevisionId"],
        **_args(db, authority, case, "review_requested"))
    db.commit()
    review.reject_review_case(db, idempotency_key="reject", expected_request_id=request["reviewRequestId"],
        reason_codes=["remediation_requested"], explanation="Repair is required",
        **_args(db, authority, case, "review_rejected"))
    db.commit()
    return authority, case


def test_authoritative_byte_aggregate_is_single_portable_query_and_counts_every_blob(db_session, monkeypatch):
    _, case = _complete_history(db_session, monkeypatch)
    case_id = case["caseId"]
    models = (ADV4ReviewCase, ADV4ReviewDraftRevision, ADV4ReviewRequest,
              ADV4ReviewRejection, ADV4SignoffEvent, ADV4ReviewCaseEvent)
    expected = 0
    blobs = []
    for model in models:
        blob_columns = [column for column in model.__table__.columns if isinstance(column.type, LargeBinary)]
        assert {column.name for column in blob_columns} == {
            column.name for column in review._history_byte_columns(model)}
        identity = model.id if model is ADV4ReviewCase else model.case_id
        rows = list(db_session.scalars(select(model).where(identity == case_id)))
        assert rows
        for row in rows:
            for column in blob_columns:
                value = getattr(row, column.name)
                expected += len(value or b"")
                blobs.append((model, row.id, column.name, value))
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        assert review._stored_case_history_bytes(db_session, case_id) == expected
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert len(statements) == 1
    for dialect in (postgresql.dialect(), sqlite.dialect()):
        sql = str(statements[0].compile(dialect=dialect))
        assert sql.count("length(") == sum(len(review._history_byte_columns(model)) for model in models)
        assert "coalesce(length(" in sql
    # Independently perturb every stored byte field, including each event blob:
    # no field can be skipped or counted twice by the aggregate.
    for model, row_id, field, payload in blobs:
        db_session.execute(update(model).where(model.id == row_id).values({field: payload + b" "}))
        assert review._stored_case_history_bytes(db_session, case_id) == expected + 1
        db_session.execute(update(model).where(model.id == row_id).values({field: payload}))
    assert review._stored_case_history_bytes(db_session, "absent-review-case") == 0


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_stored_and_pending_history_bytes_under_exact_and_over_boundary(db_session, monkeypatch, delta):
    assert review.MAX_DRAFT_PHASE_BYTES == 16 * 1024 * 1024
    assert review.MAX_REQUESTED_PHASE_BYTES == 28 * 1024 * 1024
    assert review.MAX_CASE_HISTORY_BYTES == 40 * 1024 * 1024
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    _, case = _workflow(db_session, actor, member, directive, proposal)
    stored = review._stored_case_history_bytes(db_session, case["caseId"])
    monkeypatch.setattr(review, "MAX_CASE_HISTORY_BYTES", stored - delta)
    if delta > 0:
        with pytest.raises(review.ADV4Error) as overflow:
            review._check_case_history_bytes(db_session, case["caseId"])
        assert overflow.value.code == "review_integrity"
    else:
        assert review._check_case_history_bytes(db_session, case["caseId"]) == stored
    # Null pending blobs count zero, with canonical_bytes counted exactly once.
    pending = ADV4ReviewDraftRevision(id="pending-byte-test", case_id=case["caseId"],
        annotation_bytes=b"abc", canonical_bytes=b"12345")
    unrelated = ADV4ReviewDraftRevision(id="other-byte-test", case_id="other-case", annotation_bytes=b"unrelated")
    db_session.add_all([pending, unrelated])
    assert review._pending_case_history_bytes(db_session, case["caseId"]) == 8
    monkeypatch.setattr(review, "MAX_CASE_HISTORY_BYTES", stored + 8 - delta)
    if delta > 0:
        with pytest.raises(review.ADV4Error) as overflow:
            review._check_case_history_bytes(db_session, case["caseId"], include_pending=True)
        assert overflow.value.code == "review_history_limit"
    else:
        assert review._check_case_history_bytes(db_session, case["caseId"], include_pending=True) == stored
    # The aggregate must never autoflush these deliberately incomplete objects.
    assert pending in db_session.new and unrelated in db_session.new
    db_session.rollback()


@pytest.mark.parametrize("action,owner_models", [
    ("case_created", {ADV4ReviewCase, ADV4ReviewCaseEvent}),
    ("draft_saved", {ADV4ReviewDraftRevision, ADV4ReviewCaseEvent}),
    ("review_requested", {ADV4ReviewRequest, ADV4ReviewCaseEvent}),
    ("review_rejected", {ADV4ReviewRejection, ADV4SignoffEvent, ADV4ReviewCaseEvent}),
])
def test_projected_operation_refused_before_any_owner_flush(db_session, monkeypatch, action, owner_models):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority = dict(actor=actor, membership_id=member.id)
    if action == "case_created":
        snapshot = review.review_proposal_observation(db_session, directive_id=directive.id, proposal_id=proposal.id, **authority)
        mutate = review.create_review_case
        args = dict(directive_id=directive.id, proposal_id=proposal.id, **authority,
            expected_input_identity_hash=snapshot["inputIdentityHash"],
            expected_authorization_observation_hash=snapshot["authorizationObservationHashes"][review.ACTIONS[action]])
    else:
        authority, case = _workflow(db_session, actor, member, directive, proposal)
        if action == "review_rejected":
            request = review.request_review(db_session, idempotency_key="request", **_args(db_session, authority, case, "review_requested"))
            db_session.commit()
        args = _args(db_session, authority, case, action)
        mutate = {"draft_saved": review.save_review_draft, "review_requested": review.request_review,
                  "review_rejected": review.reject_review_case}[action]
        if action == "draft_saved":
            args["annotations"] = []
        elif action == "review_rejected":
            args.update(expected_request_id=request["reviewRequestId"], reason_codes=["remediation_requested"],
                        explanation="Needs correction")
    original_flush = review._flush_review_history
    observed = []
    flushed = []
    def before_flush(*args):
        flushed.append(True)
    def constrained_flush(db, case_id, objects=None):
        rows = [row for row in db.new if type(row) in owner_models]
        assert {type(row) for row in rows} == owner_models
        assert len(rows) == len(owner_models)
        pending = sum(len(getattr(row, column.name) or b"") for row in rows
                      for column in row.__table__.columns if isinstance(column.type, LargeBinary))
        assert review._pending_case_history_bytes(db, case_id) == pending
        stored = review._stored_case_history_bytes(db, case_id)
        observed.append((stored, pending))
        monkeypatch.setattr(review, "MAX_CASE_HISTORY_BYTES", stored + pending - 1)
        return original_flush(db, case_id, objects)
    monkeypatch.setattr(review, "_flush_review_history", constrained_flush)
    event.listen(db_session, "before_flush", before_flush)
    try:
        with pytest.raises(review.ADV4Error) as captured:
            mutate(db_session, idempotency_key="over-byte-budget", **args)
        assert captured.value.code == "review_history_limit"
    finally:
        event.remove(db_session, "before_flush", before_flush)
    assert len(observed) == 1 and not flushed
    db_session.rollback()


@pytest.mark.parametrize("reader", ["detail", "queue"])
def test_corrupted_history_byte_preflight_precedes_blob_materialization(db_session, monkeypatch, reader):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _seed_review_source(db_session)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    # The altered canonical blob is corrupt but still fits its per-column bound.
    db_session.execute(update(ADV4ReviewCase).where(ADV4ReviewCase.id == case["caseId"]).values(canonical_bytes=b"corrupt-case"))
    db_session.commit()
    stored = review._stored_case_history_bytes(db_session, case["caseId"])
    monkeypatch.setattr(review, "MAX_CASE_HISTORY_BYTES", stored - 1)
    statements, loaded = [], []
    def capture(execute_state):
        statements.append(execute_state.statement)
    def row_loaded(*args):
        loaded.append(True)
    event.listen(db_session, "do_orm_execute", capture)
    event.listen(db_session, "loaded_as_persistent", row_loaded)
    try:
        with pytest.raises(review.ADV4Error) as captured:
            if reader == "detail":
                review.verified_review_case(db_session, case_id=case["caseId"], **authority)
            else:
                review.list_review_cases(db_session, **authority)
        assert captured.value.code == "review_integrity"
    finally:
        event.remove(db_session, "do_orm_execute", capture)
        event.remove(db_session, "loaded_as_persistent", row_loaded)
    # Only scalar byte lengths, never authoritative review blobs, may be selected.
    model_tables = {model.__table__ for model in review._HISTORY_MODELS}
    for statement in statements:
        assert not any(getattr(column, "name", "").endswith("_bytes") and column.table in model_tables
                       for column in statement.selected_columns)
    if reader == "detail":
        assert not loaded
        assert len(statements) <= 3  # Fresh user/membership scalars + one byte aggregate.


def _clone_proposal(db, proposal, *, copy_bindings):
    values = {column.name: getattr(proposal, column.name) for column in proposal.__table__.columns
              if column.name not in {"id", "created_at"}}
    values["canonical_bytes"] = b'{"second":true}'
    values["canonical_hash"] = hashlib.sha256(DOMAINS_V2["proposal"] + values["canonical_bytes"]).hexdigest()
    clone = ADV4CandidateProposal(**values)
    db.add(clone)
    db.flush()
    if copy_bindings:
        for binding in db.scalars(select(ADV4CandidateEvidenceBinding).where(ADV4CandidateEvidenceBinding.proposal_id == proposal.id)):
            fields = {column.name: getattr(binding, column.name) for column in binding.__table__.columns
                      if column.name not in {"id", "created_at", "proposal_id"}}
            db.add(ADV4CandidateEvidenceBinding(proposal_id=clone.id, **fields))
    db.commit()
    return clone


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_retained_source_declared_exact_budget_and_overflow_before_io(db_session, monkeypatch, delta):
    assert review.MAX_RETAINED_SOURCE_BYTES == 64 * 1024 * 1024
    _, _, _, proposal = _source(db_session)
    document = db_session.scalar(select(ADSourceDocument))
    work = review._evidence_work_metadata(db_session, proposal.id)
    database_text_bytes = work.text_bytes + work.lifecycle_reason_bytes
    document.storage_bytes = review.MAX_RETAINED_SOURCE_BYTES - database_text_bytes + delta
    db_session.commit()
    calls = []
    def retained(document, *, max_size_bytes):
        calls.append(max_size_bytes)
        return b"stubbed-bounded-read"
    monkeypatch.setattr(review, "verified_retained_document_bytes", retained)
    observation = review._evidence_observation(db_session, proposal)
    if delta > 0:
        assert observation["state"] == "integrity_error"
        assert observation["errorCode"] == "source_identity_or_evidence_missing"
        assert not calls
    else:
        assert observation["state"] == "verified"
        assert calls == [document.storage_bytes]


def test_oversized_proposal_is_stably_nonverified_and_rejectable(db_session, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, proposal = _source(db_session)
    document = db_session.scalar(select(ADSourceDocument))
    document.storage_bytes = review.MAX_RETAINED_SOURCE_BYTES + 1
    db_session.commit()
    def forbidden_io(*args, **kwargs):
        pytest.fail("Over-budget proposals must never open a retained source")
    monkeypatch.setattr(review, "verified_retained_document_bytes", forbidden_io)
    authority, case = _workflow(db_session, actor, member, directive, proposal)
    request = review.request_review(db_session, idempotency_key="request", **_args(db_session, authority, case, "review_requested"))
    db_session.commit()
    rejected = review.reject_review_case(db_session, idempotency_key="reject", expected_request_id=request["reviewRequestId"],
        reason_codes=["source_identity_or_evidence_missing"], explanation="Source exceeds the review work budget",
        **_args(db_session, authority, case, "review_rejected"))
    db_session.commit()
    assert rejected["state"] == "rejected"
    queue = review.list_review_cases(db_session, **authority)
    detail = review.verified_review_case(db_session, case_id=case["caseId"], **authority)
    assert queue["cases"][0]["inputIdentityHash"] == detail["inputIdentityHash"] == case["inputIdentityHash"]


@pytest.mark.parametrize("shared_source,delta", [(False, -1), (False, 0), (False, 1), (True, 0)])
def test_queue_retained_source_budget_is_distinct_cumulative_and_preflighted(db_session, monkeypatch, shared_source, delta):
    _enable_app(monkeypatch)
    actor, member, directive, first = _source(db_session)
    second = _clone_proposal(db_session, first, copy_bindings=shared_source)
    if not shared_source:
        _source(db_session, source=(actor, member, directive, second))
    documents = list(db_session.scalars(select(ADSourceDocument).order_by(ADSourceDocument.id)))
    text_bytes = sum(
        work.text_bytes + work.lifecycle_reason_bytes
        for proposal in (first, second)
        for work in (review._evidence_work_metadata(db_session, proposal.id),)
    )
    remaining = review.MAX_RETAINED_SOURCE_BYTES - text_bytes
    per_document, remainder = divmod(remaining, len(documents))
    for index, document in enumerate(documents):
        document.storage_bytes = (remaining if shared_source else
            per_document + (remainder if index == 0 else 0) + (delta if index == len(documents) - 1 else 0))
    db_session.commit()
    calls = []
    def retained(document, *, max_size_bytes):
        calls.append((document.id, max_size_bytes))
        return b"stubbed-bounded-read"
    monkeypatch.setattr(review, "verified_retained_document_bytes", retained)
    authority, first_case = _workflow(db_session, actor, member, directive, first)
    _, second_case = _workflow(db_session, actor, member, directive, second, idempotency_key="create-second")
    calls.clear()
    if delta > 0:
        with pytest.raises(review.ADV4Error) as captured:
            review.list_review_cases(db_session, **authority)
        assert captured.value.code == "review_work_limit"
        assert not calls  # Full page union checked before even the first read.
        # Neither proposal's individual identity is weakened by queue overflow.
        for case in (first_case, second_case):
            detail = review.verified_review_case(db_session, case_id=case["caseId"], **authority)
            assert detail["inputIdentityHash"] == case["inputIdentityHash"]
            assert detail["inputIdentity"]["evidence"]["state"] == "verified"
    else:
        queue = review.list_review_cases(db_session, **authority)
        assert queue["count"] == 2
        assert len(calls) == (1 if shared_source else 2)
        assert sum(size for _, size in calls) <= review.MAX_RETAINED_SOURCE_BYTES
        assert {item["inputIdentityHash"] for item in queue["cases"]} == {
            first_case["inputIdentityHash"], second_case["inputIdentityHash"]}


def test_actual_retained_read_limit_failure_is_exactly_classified(monkeypatch):
    def too_large(document, *, max_size_bytes):
        assert max_size_bytes == 7
        raise ValueError("Stored file exceeds read byte limit")
    monkeypatch.setattr(review, "verified_retained_document_bytes", too_large)
    assert review._retained_source_available(SimpleNamespace(storage_bytes=7)) is False


def test_evidence_metadata_counts_utf8_text_repeated_per_binding_not_per_document(db_session):
    _, _, _, proposal = _source(db_session)
    binding = db_session.scalar(select(ADV4CandidateEvidenceBinding))
    fields = {column.name: getattr(binding, column.name) for column in binding.__table__.columns
              if column.name not in {"id", "created_at", "evidence_key"}}
    db_session.add(ADV4CandidateEvidenceBinding(evidence_key="second-binding", **fields))
    db_session.execute(update(ADEvidenceFragment).values(exact_text="é😀"))
    db_session.execute(update(ADSourcePageTextVersion).values(page_text="é😀"))
    db_session.commit()
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    proposal_id = proposal.id
    statements.clear()
    try:
        work = review._evidence_work_metadata(db_session, proposal_id)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert work.binding_count == 2
    assert work.text_bytes == 24  # (6 UTF-8 fragment bytes + 6 page bytes) x 2 bindings.
    assert work.lifecycle_count == 1
    assert work.lifecycle_reason_bytes == len("test admission".encode())
    assert len(work.document_keys) == 1
    assert len(statements) == 2  # One combined count/SUM plus bounded scalar document metadata.
    assert "sum(" in str(statements[0]) and "count(" in str(statements[0])


def test_authorship_cutoff_and_frozen_verification_never_select_payload_columns(db_session, monkeypatch):
    authority, case = _complete_history(db_session, monkeypatch)
    request = db_session.scalar(select(ADV4ReviewRequest).where(
        ADV4ReviewRequest.case_id == case["caseId"]))
    blobs = {
        "cutoff": review._read_blob(request.cutoff_bytes),
        "authorship_set": review._read_blob(request.authorship_set_bytes),
    }
    operations = (
        lambda: review._authorship(db_session, request.proposal_id),
        lambda: review._cutoff(db_session, request.proposal_id),
        lambda: review._verify_frozen_sources(db_session, request, blobs),
    )
    forbidden = {
        "request_canonical_bytes", "canonical_bytes", "raw_transport_bytes",
        "evidence_binding_bytes", "parsed_json", "exact_text", "page_text",
    }
    for operation in operations:
        statements = []
        def capture(execute_state):
            statements.append(execute_state.statement)
        event.listen(db_session, "do_orm_execute", capture)
        try:
            operation()
        finally:
            event.remove(db_session, "do_orm_execute", capture)
        assert statements
        selected = {getattr(column, "name", "")
                    for statement in statements for column in statement.selected_columns}
        assert not forbidden & selected
        sql = "\n".join(str(statement) for statement in statements)
        assert not any(name in sql for name in forbidden)


def test_lifecycle_count_overflow_fails_before_fragment_or_reason_materialization(db_session, monkeypatch):
    actor, _, _, proposal = _source(db_session)
    fragment = db_session.scalar(select(ADEvidenceFragment))
    admission = db_session.scalar(select(ADEvidenceFragmentLifecycleEvent).where(
        ADEvidenceFragmentLifecycleEvent.fragment_id == fragment.id))
    reason = "bounded quarantine"
    db_session.add(ADEvidenceFragmentLifecycleEvent(
        fragment_id=fragment.id, event_type="quarantined", actor_user_id=actor.id,
        reason=reason, sequence_number=1, predecessor_event_hash=admission.event_hash,
        event_hash=_hash_parts(fragment.id, fragment.fragment_hash, "quarantined",
                               actor.id, reason, 1, admission.event_hash)))
    db_session.commit()
    proposal = review._proposal(db_session, proposal.id)
    monkeypatch.setattr(review, "MAX_ARRAY_ITEMS", 1)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        observed = review._evidence_observation(db_session, proposal)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert observed == {
        "storedBindingHash": proposal.evidence_binding_hash,
        "state": "integrity_error",
        "errorCode": "source_identity_or_evidence_missing",
    }
    assert len(statements) == 1
    assert not any(getattr(column, "name", "") in {"reason", "exact_text", "page_text"}
                   for column in statements[0].selected_columns)


@pytest.mark.parametrize("delta", [0, 1])
def test_direct_sql_text_size_is_preflighted_before_text_materialization(db_session, monkeypatch, delta):
    _, _, _, proposal = _source(db_session)
    # Generate the large page in SQLite, not as a Python/ORM text value. The
    # fixture bound is small; the same aggregate is used for the 64 MiB constant.
    monkeypatch.setattr(review, "MAX_RETAINED_SOURCE_BYTES", 1024)
    lifecycle_bytes = review._evidence_work_metadata(db_session, proposal.id).lifecycle_reason_bytes
    page_size = 1024 - 6 - 6 - lifecycle_bytes + delta  # exact text + retained file + lifecycle reason.
    db_session.execute(update(ADSourcePageTextVersion).values(
        page_text=func.substr(func.hex(func.zeroblob(page_size)), 1, page_size)))
    db_session.commit()
    proposal_id = proposal.id
    proposal = review._proposal(db_session, proposal_id)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    def forbidden_io(*args, **kwargs):
        pytest.fail("Invalid/over-budget database text must not reach external I/O")
    monkeypatch.setattr(review, "verified_retained_document_bytes", forbidden_io)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        observed = review._evidence_observation(db_session, proposal)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    text_selected = any(getattr(column, "name", "") in {"exact_text", "page_text"}
                        for statement in statements for column in statement.selected_columns)
    assert observed["state"] == "integrity_error"
    if delta:
        assert observed["errorCode"] == "source_identity_or_evidence_missing"
        assert not text_selected
        assert len(statements) <= 2
    else:
        assert observed["errorCode"] == "evidence_integrity"  # Byte budget passed; altered page hash fails.
        assert text_selected


@pytest.mark.parametrize("delta", [0, 1])
def test_queue_text_and_binding_preflight_happens_before_any_preparation(db_session, monkeypatch, delta):
    _enable_app(monkeypatch)
    actor, member, directive, first = _source(db_session)
    second = _clone_proposal(db_session, first, copy_bindings=True)
    monkeypatch.setattr(review, "verified_retained_document_bytes", lambda *args, **kwargs: b"source")
    authority, _ = _workflow(db_session, actor, member, directive, first)
    _workflow(db_session, actor, member, directive, second, idempotency_key="second-create")
    # Distinct proposals each repeat the same tiny source 1,000 times. Only a
    # count budget, not a distinct retained-file byte budget, detects +1 here.
    for number, proposal in enumerate((first, second)):
        binding = db_session.scalar(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == proposal.id))
        fields = {column.name: getattr(binding, column.name) for column in binding.__table__.columns
                  if column.name not in {"id", "created_at", "evidence_key"}}
        db_session.execute(insert(ADV4CandidateEvidenceBinding), [
            {**fields, "evidence_key": f"repeat-{index}"} for index in range(999 + (delta if number else 0))])
    db_session.commit()
    prepared = []
    class PreparationReached(Exception):
        pass
    def prepare(*args, **kwargs):
        prepared.append(True)
        raise PreparationReached()
    monkeypatch.setattr(review, "_prepare_evidence_observation", prepare)
    if delta:
        with pytest.raises(review.ADV4Error) as captured:
            review.list_review_cases(db_session, **authority)
        assert captured.value.code == "review_work_limit"
        assert not prepared
    else:
        with pytest.raises(PreparationReached):
            review.list_review_cases(db_session, **authority)
        assert prepared


def test_queue_cumulative_database_text_is_preflighted_before_materialization(db_session, monkeypatch):
    _enable_app(monkeypatch)
    actor, member, directive, first = _source(db_session)
    second = _clone_proposal(db_session, first, copy_bindings=True)
    monkeypatch.setattr(review, "verified_retained_document_bytes", lambda *args, **kwargs: b"source")
    authority, _ = _workflow(db_session, actor, member, directive, first)
    _workflow(db_session, actor, member, directive, second, idempotency_key="second-create")
    # Each proposal: 6 fragment + 12 page + 6 retained = 24 bytes. The request:
    # two distinct proposal text workloads (36) + one shared retained source (6).
    db_session.execute(update(ADSourcePageTextVersion).values(page_text="longer text!"))
    db_session.commit()
    monkeypatch.setattr(review, "MAX_RETAINED_SOURCE_BYTES", 41)
    def forbidden_prepare(*args, **kwargs):
        pytest.fail("Queue byte budget must run before text preparation")
    monkeypatch.setattr(review, "_prepare_evidence_observation", forbidden_prepare)
    with pytest.raises(review.ADV4Error) as captured:
        review.list_review_cases(db_session, **authority)
    assert captured.value.code == "review_work_limit"


def test_single_proposal_binding_overflow_is_nonverified_without_binding_or_text_loads(db_session):
    _, _, _, proposal = _source(db_session)
    binding = db_session.scalar(select(ADV4CandidateEvidenceBinding))
    fields = {column.name: getattr(binding, column.name) for column in binding.__table__.columns
              if column.name not in {"id", "created_at", "evidence_key"}}
    db_session.execute(insert(ADV4CandidateEvidenceBinding), [
        {**fields, "evidence_key": f"repeat-{index}"} for index in range(review.MAX_ARRAY_ITEMS)])
    db_session.commit()
    proposal = review._proposal(db_session, proposal.id)
    statements = []
    def capture(execute_state):
        statements.append(execute_state.statement)
    event.listen(db_session, "do_orm_execute", capture)
    try:
        observed = review._evidence_observation(db_session, proposal)
    finally:
        event.remove(db_session, "do_orm_execute", capture)
    assert observed["state"] == "integrity_error"
    assert observed["errorCode"] == "source_identity_or_evidence_missing"
    assert len(statements) == 1  # Scalar count/text aggregate only, no owner rows.
    assert not any(getattr(column, "name", "") in {"exact_text", "page_text", "evidence_key"}
                   for column in statements[0].selected_columns)


@pytest.mark.parametrize("obligation", [False, True])
def test_source_work_overflow_does_not_reenter_fragment_loading_via_projection(monkeypatch, obligation):
    projection = SimpleNamespace(id="projection", projection_hash="a" * 64,
        directive_id="directive",
        materializer_version=review.OBLIGATION_VERSION if obligation else review.APP_VERSION)
    head = SimpleNamespace(event_hash="b" * 64)
    db = SimpleNamespace(execute=lambda query: SimpleNamespace(one_or_none=lambda: head))
    def forbidden(*args, **kwargs):
        pytest.fail("An over-budget source cannot enter projection reconstruction")
    monkeypatch.setattr(review, "reconstruct_applicability", forbidden)
    monkeypatch.setattr(review, "reconstruct_obligation_projection", forbidden)
    result = review._projection_observation(
        db, SimpleNamespace(id="proposal"), obligation=obligation,
        source_work_exceeded=True,
        prepared=([projection], review._ProjectionAuditWork(1)))
    assert result == {"id": "projection", "storedHash": "a" * 64, "eventHeadHash": "b" * 64,
                      "state": "integrity_error", "errorCode": "projection_integrity"}
