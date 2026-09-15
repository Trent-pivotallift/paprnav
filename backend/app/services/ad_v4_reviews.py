"""Append-only V4 review cases through graph-free remediation rejection.

This module owns no release, selection, materialization, or semantic mutation.
Callers commit writes and supply a repeatable-read, read-only session to GETs.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from botocore.exceptions import (
    ClientError, ConnectionClosedError, ConnectTimeoutError, CredentialRetrievalError,
    EndpointConnectionError, IncompleteReadError, NoCredentialsError,
    PartialCredentialsError, ReadTimeoutError, ResponseStreamingError, SSLError,
)
from sqlalchemy import LargeBinary, case as sql_case, cast, func, inspect, select
from sqlalchemy.orm import Session, load_only

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragment, ADEvidenceFragmentLifecycleEvent, ADPublication,
    ADSourceDocument, ADSourcePageTextVersion, ADV4CandidateAppProjection,
    ADV4CandidateAppProjectionEvent, ADV4CandidateAppMaterializationRequest,
    ADV4CandidateEvidenceBinding, ADV4CandidateObligationMaterializationRequest,
    ADV4CandidateObligationProjection, ADV4CandidateObligationProjectionEvent,
    ADV4CandidateProposal, ADV4CandidateSubmission,
    ADV4CandidateSubmissionRelationship, ADV4FeatureGate, ADV4ReviewCase,
    ADV4ReviewCaseEvent, ADV4ReviewDraftRevision, ADV4ReviewRejection,
    ADV4ReviewRequest, ADV4SignoffEvent, OrganizationMembership, User,
)
from app.services.ad_evidence import ADEvidenceError, _hash_parts
from app.services.ad_extraction import verified_retained_document_bytes
from app.services.ad_v4_candidates import (
    ADV4Error, CANONICALIZATION_VERSION_V2, DOMAINS, DOMAINS_V2,
    MAX_ARRAY_ITEMS, MAX_EVIDENCE_BINDINGS, PROFILE_ENVELOPES, VALIDATOR_VERSION_V2,
    _advisory_lock, canonical_bytes, verified_candidate,
)
from app.services.ad_v4_applicability import (
    MATERIALIZER_VERSION as APP_VERSION, projection_state,
    reconstruct_applicability,
)
from app.services.ad_v4_obligation_persistence import (
    MATERIALIZER_VERSION as OBLIGATION_VERSION, reconstruct_obligation_projection,
)
from app.services.ad_v4_obligations import ObligationIntegrityError


CONTRACT_VERSION = "paprnav-ad-v4-candidate-review-1"
INPUT_VERSION = "paprnav-ad-v4-review-input-identity-1"
OBSERVATION_VERSION = "paprnav-ad-v4-review-observation-1"
ACTIONS = {
    "case_created": "create_ad_v4_review_case",
    "draft_saved": "save_ad_v4_review_draft",
    "review_requested": "request_ad_v4_review",
    "review_rejected": "reject_ad_v4_review",
}
REASON_CODES = frozenset({
    "candidate_integrity", "source_identity_or_evidence_missing",
    "evidence_not_current", "projection_integrity", "unsupported_version",
    "input_changed", "remediation_requested",
})
MAX_BYTES = 1048576
MAX_CASES_PER_PROPOSAL = 100
MAX_DRAFT_REVISIONS_PER_CASE = 1000
MAX_EVENTS_PER_CASE = 1003
MAX_DRAFT_PHASE_BYTES = 16 * 1024 * 1024
MAX_REQUESTED_PHASE_BYTES = 28 * 1024 * 1024
MAX_CASE_HISTORY_BYTES = 40 * 1024 * 1024
MAX_RETAINED_SOURCE_BYTES = 64 * 1024 * 1024
_HISTORY_MODELS = (ADV4ReviewCase, ADV4ReviewDraftRevision, ADV4ReviewRequest,
                   ADV4ReviewRejection, ADV4SignoffEvent, ADV4ReviewCaseEvent)
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_STORAGE_UNAVAILABLE_CODES = frozenset({
    "NoSuchKey", "NoSuchBucket", "AccessDenied", "InvalidAccessKeyId",
    "SignatureDoesNotMatch", "ExpiredToken", "InvalidToken", "RequestExpired",
    "RequestTimeTooSkewed", "SlowDown", "Throttling", "ThrottlingException",
    "RequestTimeout", "RequestTimeoutException", "InternalError", "ServiceUnavailable",
    "403", "404", "408", "429", "500", "502", "503", "504",
})
_STORAGE_UNAVAILABLE_EXCEPTIONS = (
    OSError, ConnectionClosedError, ConnectTimeoutError, EndpointConnectionError,
    IncompleteReadError, ReadTimeoutError, ResponseStreamingError, SSLError,
    CredentialRetrievalError, NoCredentialsError, PartialCredentialsError,
)


def _error(code: str, message: str, status: int = 409) -> ADV4Error:
    return ADV4Error(code, "", message, http_status=status)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def review_canonical_bytes(value: Any) -> bytes:
    """Fixed-key audit JSON, distinct from the numeric/null-free AD profile."""
    try:
        payload = json.dumps(value, sort_keys=True, ensure_ascii=False,
                             allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, UnicodeError) as exc:
        raise _error("review_payload_invalid", "Review payload is not valid JSON", 422) from exc
    if b"\\u0000" in payload or len(payload) > MAX_BYTES:
        raise _error("review_payload_invalid", "Review payload exceeds the audit contract", 422)
    return payload


def review_hash(domain: str, payload: bytes) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + payload).hexdigest()


def _fresh(db: Session, model: Any, **where: Any) -> Any:
    query = select(model).filter_by(**where).execution_options(populate_existing=True)
    return db.scalar(query)


def _require_application_gate(*, write: bool = False, terminal: bool = False) -> None:
    settings = get_settings()
    if not settings.ad_v4_slice4_reads_enabled:
        raise _error("capability_disabled", "V4 review read capability is disabled", 404)
    if write and not settings.ad_v4_slice4_drafts_enabled:
        raise _error("review_draft_gate_disabled", "V4 review draft capability is disabled")
    if terminal and not settings.ad_v4_slice4_decisions_enabled:
        raise _error("review_decision_gate_disabled", "V4 review decision capability is disabled")


def _database_gates(db: Session, *, terminal: bool = False) -> None:
    # Lock the common prefix even where an older capability need not be enabled.
    keys = ("validator2_write_enabled", "materializer3a_enabled", "materializer3b_enabled",
            "reviewer4_draft_enabled", "reviewer4_decision_enabled")
    for key in keys[:5 if terminal else 4]:
        enabled = db.scalar(select(ADV4FeatureGate.enabled).where(
            ADV4FeatureGate.gate_key == key).with_for_update(read=True))
        if enabled is None:
            raise _error("schema_capability_mismatch", "V4 review database capability is unavailable")
        if key.startswith("reviewer4_") and not enabled:
            raise _error("review_gate_disabled", "V4 review database write gate is disabled")


def _authorize(db: Session, actor: User, membership_id: str, *, lock: bool) -> dict[str, Any]:
    # Only the immutable locator comes from the identity map. Authorization still
    # uses fresh scalar rows; expired User attributes must not trigger a full load.
    actor_identity = inspect(actor).identity
    actor_id = actor_identity[0] if actor_identity else actor.id
    actor_query = select(User.id, User.status, User.updated_at).where(User.id == actor_id)
    member_query = select(OrganizationMembership.id, OrganizationMembership.user_id,
                          OrganizationMembership.organization_id, OrganizationMembership.role,
                          OrganizationMembership.status, OrganizationMembership.updated_at).where(
                              OrganizationMembership.id == membership_id)
    if lock:
        actor_query = actor_query.with_for_update()
        member_query = member_query.with_for_update()
    user = db.execute(actor_query).mappings().one_or_none()
    member = db.execute(member_query).mappings().one_or_none()
    if (user is None or user["status"] != "active" or member is None
        or member["user_id"] != actor_id or member["status"] != "active"
        or member["role"] != "platform_admin"):
        raise _error("forbidden", "Active platform administrator membership required", 403)
    return {
        "actorUserId": user["id"], "userStatus": user["status"],
        "userUpdatedAt": _time(user["updated_at"]),
        "authorizingMembershipId": member["id"], "organizationId": member["organization_id"],
        "membershipStatus": member["status"],
        "role": member["role"], "membershipUpdatedAt": _time(member["updated_at"]),
        "validityRule": "status_only_v1", "validFrom": None, "validUntil": None,
    }


def authorize_review_audit(db: Session, actor: User, membership_id: str) -> dict[str, Any]:
    _require_application_gate()
    with db.no_autoflush:
        return _authorize(db, actor, membership_id, lock=False)


def _proposal(db: Session, proposal_id: str) -> ADV4CandidateProposal:
    row = _fresh(db, ADV4CandidateProposal, id=proposal_id)
    if row is None:
        raise _error("not_found", "V4 candidate proposal not found", 404)
    return row


def _retained_source_available(document: ADSourceDocument) -> bool:
    """Only expected storage failures become remediation observations.

    Keep this boundary outside structural row-validation exception handling:
    database failures, malformed SDK responses, and programmer errors propagate.
    """
    try:
        verified_retained_document_bytes(document, max_size_bytes=min(document.storage_bytes, MAX_RETAINED_SOURCE_BYTES))
        return True
    except _STORAGE_UNAVAILABLE_EXCEPTIONS:
        return False
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code in _STORAGE_UNAVAILABLE_CODES or status in {403, 404, 408, 429, 500, 502, 503, 504}:
            return False
        raise
    except ValueError as exc:
        # This exact integrity exception belongs to the retained-byte verifier;
        # other ValueErrors (SDK validation/configuration/programmer errors) do not.
        if str(exc) in {"Retained AD source document hash or size mismatch", "Stored file exceeds read byte limit"}:
            return False
        raise


@dataclass(frozen=True)
class _EvidenceWork:
    binding_count: int
    text_bytes: int
    lifecycle_count: int = 0
    lifecycle_reason_bytes: int = 0
    document_keys: frozenset[tuple[str, str, int]] = frozenset()
    invalid_source_size: bool = False

    @property
    def over_budget(self) -> bool:
        return (self.invalid_source_size or self.binding_count > MAX_ARRAY_ITEMS
                or self.lifecycle_count > MAX_ARRAY_ITEMS
                or self.text_bytes + self.lifecycle_reason_bytes
                + sum(key[2] for key in self.document_keys) > MAX_RETAINED_SOURCE_BYTES)


def _evidence_work_metadata(db: Session, proposal_id: str) -> _EvidenceWork:
    # SQLite length(TEXT) counts characters; BLOB length counts UTF-8 bytes.
    # PostgreSQL octet_length(TEXT) provides the same byte measurement.
    def text_length(column: Any) -> Any:
        size = (func.length(cast(column, LargeBinary)) if db.get_bind().dialect.name == "sqlite"
                else func.octet_length(column))
        return func.coalesce(size, 0)
    binding, fragment, page, document, lifecycle = (
        ADV4CandidateEvidenceBinding, ADEvidenceFragment,
        ADSourcePageTextVersion, ADSourceDocument, ADEvidenceFragmentLifecycleEvent)
    fragment_ids = select(binding.fragment_id).where(
        binding.proposal_id == proposal_id).distinct().subquery()
    lifecycle_count = select(func.count(lifecycle.id)).select_from(lifecycle).join(
        fragment_ids, fragment_ids.c.fragment_id == lifecycle.fragment_id).scalar_subquery()
    lifecycle_reason_bytes = select(func.coalesce(func.sum(text_length(lifecycle.reason)), 0)).select_from(
        lifecycle).join(fragment_ids, fragment_ids.c.fragment_id == lifecycle.fragment_id).scalar_subquery()
    count, text_bytes, event_count, event_reason_bytes = db.execute(select(
        func.count(binding.id), func.coalesce(func.sum(
        text_length(fragment.exact_text) + text_length(page.page_text)), 0),
        lifecycle_count, lifecycle_reason_bytes).select_from(binding).outerjoin(
            fragment, fragment.id == binding.fragment_id).outerjoin(page, page.id == fragment.page_text_version_id).where(
                binding.proposal_id == proposal_id)).one()
    work = _EvidenceWork(binding_count=count, text_bytes=text_bytes,
                         lifecycle_count=event_count, lifecycle_reason_bytes=event_reason_bytes)
    if not count or work.over_budget:
        return work
    documents = db.execute(select(document.id, document.content_hash, document.storage_bytes).select_from(
        binding).join(fragment, fragment.id == binding.fragment_id).join(
            document, document.id == fragment.source_document_id).where(
                binding.proposal_id == proposal_id).distinct().limit(MAX_ARRAY_ITEMS + 1)).all()
    if any(type(row.storage_bytes) is not int or row.storage_bytes < 0 for row in documents):
        return _EvidenceWork(binding_count=count, text_bytes=text_bytes,
                             lifecycle_count=event_count, lifecycle_reason_bytes=event_reason_bytes,
                             invalid_source_size=True)
    return _EvidenceWork(binding_count=count, text_bytes=text_bytes,
                         lifecycle_count=event_count, lifecycle_reason_bytes=event_reason_bytes,
                         document_keys=frozenset(tuple(row) for row in documents))


def _verified_evidence_lifecycle_events_bounded(db: Session, fragment: ADEvidenceFragment) -> list[Any]:
    """Verify one lifecycle through a scalar, limit-plus-one projection."""
    event = ADEvidenceFragmentLifecycleEvent
    rows = db.execute(select(
        event.id, event.fragment_id, event.event_type, event.actor_user_id,
        event.reason, event.sequence_number, event.predecessor_event_hash,
        event.event_hash,
    ).where(event.fragment_id == fragment.id).order_by(event.sequence_number).limit(
        MAX_ARRAY_ITEMS + 1)).all()
    if len(rows) > MAX_ARRAY_ITEMS:
        raise ADEvidenceError("evidence_lifecycle_integrity", "Evidence lifecycle exceeds review work bound")
    if not rows or [row.sequence_number for row in rows] != list(range(len(rows))):
        raise ADEvidenceError("evidence_lifecycle_integrity", "Evidence lifecycle sequence is incomplete")
    for index, row in enumerate(rows):
        predecessor_hash = None if index == 0 else rows[index - 1].event_hash
        if (row.predecessor_event_hash != predecessor_hash
            or (index == 0 and row.event_type != "admitted")
            or (index > 0 and row.event_type not in {"superseded", "quarantined"})
            or row.event_hash != _hash_parts(
                fragment.id, fragment.fragment_hash, row.event_type,
                row.actor_user_id, row.reason, row.sequence_number,
                row.predecessor_event_hash)):
            raise ADEvidenceError("evidence_lifecycle_integrity", "Evidence lifecycle chain or hash differs")
    return rows


def _prepare_evidence_observation(db: Session, proposal: ADV4CandidateProposal, *,
                                  work: _EvidenceWork | None = None) -> tuple[
        dict[str, Any], dict[tuple[str, str, int], ADSourceDocument], bool, _EvidenceWork]:
    """Validate source metadata without loading any retained document bytes."""
    result: dict[str, Any] = {"storedBindingHash": proposal.evidence_binding_hash}
    work = work if work is not None else _evidence_work_metadata(db, proposal.id)
    if work.over_budget:
        return {**result, "state": "integrity_error", "errorCode": "source_identity_or_evidence_missing"}, {}, False, work
    bindings = _bounded_rows(db, select(ADV4CandidateEvidenceBinding).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal.id).order_by(
            ADV4CandidateEvidenceBinding.evidence_key), limit=MAX_ARRAY_ITEMS, label="review observation evidence bindings")
    if not bindings:
        return {**result, "state": "missing", "errorCode": "missing_evidence"}, {}, False, work
    try:
        if (len(bindings) != proposal.binding_count
            or set(proposal.parsed_json["evidenceBindings"]) != {b.evidence_key for b in bindings}):
            raise ValueError("binding set differs")
        snapshots, heads = [], {}
        verified_documents: set[str] = set()
        documents_to_verify: dict[tuple[str, str, int], ADSourceDocument] = {}
        stale = False
        lifecycle_cache: dict[str, list[Any]] = {}
        for binding in bindings:
            fragment = _fresh(db, ADEvidenceFragment, id=binding.fragment_id)
            if fragment is None or fragment.directive_id != proposal.directive_id:
                raise ValueError("fragment identity differs")
            events = lifecycle_cache.get(fragment.id)
            if events is None:
                events = _verified_evidence_lifecycle_events_bounded(db, fragment)
                lifecycle_cache[fragment.id] = events
            admission = events[0]
            if (binding.directive_id != proposal.directive_id
                or binding.validator_version != proposal.validator_version
                or binding.canonicalization_version != proposal.canonicalization_version
                or binding.fragment_hash != fragment.fragment_hash
                or admission.id != binding.admitted_event_id
                or admission.event_hash != binding.admitted_event_hash
                or proposal.parsed_json["evidenceBindings"][binding.evidence_key]
                != {"fragmentId": fragment.id, "fragmentHash": fragment.fragment_hash}):
                raise ValueError("binding identity differs")
            expected_fragment_hash = _hash_parts(
                fragment.directive_id, fragment.source_document_id, fragment.source_content_hash,
                fragment.rendition_id, fragment.page_text_version_id, fragment.page_start,
                fragment.page_end, fragment.character_start, fragment.character_end,
                fragment.paragraph_locator, fragment.table_locator, fragment.row_locator,
                fragment.note_locator, fragment.region_map_hash, fragment.exact_text,
                fragment.parser_name, fragment.parser_version)
            page = _fresh(db, ADSourcePageTextVersion, id=fragment.page_text_version_id)
            if (expected_fragment_hash != fragment.fragment_hash or page is None
                or page.source_document_id != fragment.source_document_id
                or page.source_content_hash != fragment.source_content_hash
                or page.rendition_id != fragment.rendition_id
                or page.page_number != fragment.page_start or fragment.page_end != fragment.page_start
                or hashlib.sha256(page.page_text.encode()).hexdigest() != page.text_hash
                or fragment.character_start < 0 or fragment.character_end > len(page.page_text)
                or fragment.character_end <= fragment.character_start
                or page.page_text[fragment.character_start:fragment.character_end] != fragment.exact_text):
                raise ValueError("fragment source differs")
            if fragment.source_document_id not in verified_documents:
                document = db.scalar(select(ADSourceDocument).options(load_only(
                    ADSourceDocument.id, ADSourceDocument.content_hash, ADSourceDocument.storage_bytes,
                    ADSourceDocument.storage_backend, ADSourceDocument.storage_key)).where(
                        ADSourceDocument.id == fragment.source_document_id).execution_options(populate_existing=True))
                publication = db.scalar(select(ADPublication.id).where(
                    ADPublication.directive_id == proposal.directive_id,
                    ADPublication.source_document_id == fragment.source_document_id))
                if (document is None or publication is None or document.content_hash != fragment.source_content_hash
                    or type(document.storage_bytes) is not int or document.storage_bytes < 0):
                    raise ValueError("retained source identity differs")
                document_key = (document.id, document.content_hash, document.storage_bytes)
                documents_to_verify[document_key] = document
                verified_documents.add(document.id)
            snapshots.append({"evidenceKey": binding.evidence_key, "fragmentId": fragment.id,
                              "fragmentHash": fragment.fragment_hash, "admittedEventId": admission.id,
                              "admittedEventHash": admission.event_hash})
            heads[fragment.id] = {"fragmentId": fragment.id, "eventId": events[-1].id,
                                  "eventHash": events[-1].event_hash, "sequenceNumber": events[-1].sequence_number}
            stale = stale or len(events) != 1
        envelope = {"version": PROFILE_ENVELOPES[proposal.validator_version]["binding"],
                    "bindings": snapshots}
        if proposal.validator_version == VALIDATOR_VERSION_V2:
            envelope.update(validatorVersion=proposal.validator_version,
                            canonicalizationVersion=proposal.canonicalization_version)
        payload = canonical_bytes(envelope, proposal.canonicalization_version)
        domain = DOMAINS_V2 if proposal.validator_version == VALIDATOR_VERSION_V2 else DOMAINS
        if (payload != proposal.evidence_binding_bytes
            or hashlib.sha256(domain["bindings"] + payload).hexdigest() != proposal.evidence_binding_hash):
            raise ValueError("binding envelope differs")
        result["headSetHash"] = review_hash("paprnav-ad-v4-review-evidence-heads-1",
            review_canonical_bytes([heads[key] for key in sorted(heads)]))
    except (ADV4Error, ADEvidenceError, ValueError, KeyError, TypeError):
        return {**result, "state": "integrity_error", "errorCode": "evidence_integrity"}, {}, False, work
    return result, documents_to_verify, stale, work


def _check_source_work_budget(document_keys: Any, *, text_bytes: int = 0,
                              binding_count: int = 0, lifecycle_count: int = 0) -> None:
    if (text_bytes + sum(key[2] for key in set(document_keys)) > MAX_RETAINED_SOURCE_BYTES
        or binding_count > MAX_ARRAY_ITEMS or lifecycle_count > MAX_ARRAY_ITEMS):
        raise _error("review_work_limit", "Evidence sources exceed the review request work budget")


def _evidence_observation(db: Session, proposal: ADV4CandidateProposal, *,
                          document_cache: dict[tuple[str, str, int], bool] | None = None,
                          prepared: Any = None,
                          ) -> dict[str, Any]:
    result, documents, stale, work = prepared if prepared is not None else _prepare_evidence_observation(db, proposal)
    if "state" in result:
        return result
    cache = document_cache if document_cache is not None else {}
    _check_source_work_budget(
        set(cache) | set(documents),
        text_bytes=work.text_bytes + work.lifecycle_reason_bytes,
        binding_count=work.binding_count, lifecycle_count=work.lifecycle_count)
    for document_key, document in documents.items():
        if document_key not in cache:
            cache[document_key] = _retained_source_available(document)
        available = cache[document_key]
        if not available:
            return {**result, "state": "integrity_error", "errorCode": "source_identity_or_evidence_missing"}
    if stale:
        return {**result, "state": "stale", "errorCode": "evidence_not_current"}
    return {**result, "state": "verified", "verifiedBindingHash": proposal.evidence_binding_hash}


@dataclass(frozen=True)
class _ProjectionAuditWork:
    projection_count: int
    request_count: int = 0
    event_count: int = 0
    payload_bytes: int = 0

    @property
    def row_count(self) -> int:
        return self.request_count + self.event_count

    @property
    def over_budget(self) -> bool:
        return (self.projection_count > MAX_ARRAY_ITEMS
                or self.row_count > MAX_ARRAY_ITEMS
                or self.payload_bytes > MAX_RETAINED_SOURCE_BYTES)


def _prepare_projection_observation(db: Session, proposal_id: str, *, obligation: bool) -> tuple[list[Any], _ProjectionAuditWork]:
    model = ADV4CandidateObligationProjection if obligation else ADV4CandidateAppProjection
    request_model = (ADV4CandidateObligationMaterializationRequest if obligation
                     else ADV4CandidateAppMaterializationRequest)
    event_model = ADV4CandidateObligationProjectionEvent if obligation else ADV4CandidateAppProjectionEvent
    columns = [model.id, model.materializer_version, model.projection_hash, model.directive_id]
    if obligation:
        columns.append(ADV4CandidateObligationProjection.app_projection_id)
    projections = list(db.execute(select(*columns).where(
        model.proposal_id == proposal_id).order_by(model.id).limit(MAX_ARRAY_ITEMS + 1)))
    if not projections:
        return [], _ProjectionAuditWork(0)
    version = OBLIGATION_VERSION if obligation else APP_VERSION
    projection = next((row for row in projections if row.materializer_version == version), projections[0])
    if len(projections) > MAX_ARRAY_ITEMS:
        return projections, _ProjectionAuditWork(len(projections))
    request_count = select(func.count(request_model.id)).where(
        request_model.projection_id == projection.id).scalar_subquery()
    request_bytes = select(func.coalesce(func.sum(func.length(
        request_model.request_canonical_bytes)), 0)).where(
            request_model.projection_id == projection.id).scalar_subquery()
    event_count = select(func.count(event_model.id)).where(
        event_model.projection_id == projection.id).scalar_subquery()
    event_bytes = select(func.coalesce(func.sum(func.length(event_model.canonical_bytes)), 0)).where(
        event_model.projection_id == projection.id).scalar_subquery()
    counts = db.execute(select(request_count, event_count, request_bytes + event_bytes)).one()
    return projections, _ProjectionAuditWork(
        projection_count=len(projections), request_count=int(counts[0] or 0),
        event_count=int(counts[1] or 0), payload_bytes=int(counts[2] or 0))


def _projection_work_exceeded(works: Any) -> bool:
    eligible = [work for work in works if not work.over_budget]
    return (sum(work.row_count for work in eligible) > MAX_ARRAY_ITEMS
            or sum(work.payload_bytes for work in eligible) > MAX_RETAINED_SOURCE_BYTES)


def _projection_observation(db: Session, proposal: ADV4CandidateProposal, *, obligation: bool,
                            source_work_exceeded: bool = False, prepared: Any = None) -> dict[str, Any]:
    model = ADV4CandidateObligationProjection if obligation else ADV4CandidateAppProjection
    event_model = ADV4CandidateObligationProjectionEvent if obligation else ADV4CandidateAppProjectionEvent
    version = OBLIGATION_VERSION if obligation else APP_VERSION
    projections, audit_work = (prepared if prepared is not None
                               else _prepare_projection_observation(db, proposal.id, obligation=obligation))
    if not projections:
        return {"state": "missing", "errorCode": "projection_missing"}
    row = next((p for p in projections if p.materializer_version == version), projections[0])
    result = {"id": row.id, "storedHash": row.projection_hash}
    head = db.execute(select(
        event_model.id, event_model.event_hash, event_model.event_type,
        event_model.sequence_number,
    ).where(event_model.projection_id == row.id).order_by(
        event_model.sequence_number.desc()).limit(1)).one_or_none()
    if head is not None:
        result["eventHeadHash"] = head.event_hash
    if row.materializer_version != version:
        return {**result, "state": "unsupported_version", "errorCode": "unsupported_version"}
    if source_work_exceeded or audit_work.over_budget:
        return {**result, "state": "integrity_error", "errorCode": "projection_integrity"}
    try:
        if row.directive_id != proposal.directive_id or head is None:
            raise ValueError("projection identity differs")
        row = _fresh(db, model, id=row.id)
        if row is None:
            raise ValueError("projection identity differs")
        if obligation:
            reconstruct_obligation_projection(db, row, require_fresh=False)
            app = _fresh(db, ADV4CandidateAppProjection, id=row.app_projection_id)
            state, _ = projection_state(db, app) if app else ("candidate_stale", [])
        else:
            reconstruct_applicability(db, row)
            state, _ = projection_state(db, row)
        if state != "candidate_verified" or (head.event_type != "materialized" if obligation else head.event_type == "stale_marked"):
            return {**result, "state": "stale", "errorCode": "projection_stale"}
        return {**result, "state": "verified"}
    except (ADV4Error, ObligationIntegrityError, ValueError, KeyError, TypeError):
        return {**result, "state": "integrity_error", "errorCode": "projection_integrity"}


def observe_review_inputs(db: Session, proposal_id: str, *, observed_at: datetime | None = None,
                           _document_cache: dict[tuple[str, str, int], bool] | None = None,
                           _prepared_evidence: Any = None,
                           _prepared_projections: Any = None) -> dict[str, Any]:
    """Describe invalid inputs honestly; observation never repairs or materializes."""
    with db.no_autoflush:
        proposal = _proposal(db, proposal_id)
        prepared = _prepared_evidence if _prepared_evidence is not None else _prepare_evidence_observation(db, proposal)
        projections = (_prepared_projections if _prepared_projections is not None else {
            obligation: _prepare_projection_observation(db, proposal.id, obligation=obligation)
            for obligation in (False, True)
        })
        projection_page_exceeded = _projection_work_exceeded(
            prepared_projection[1] for prepared_projection in projections.values())
        parent_projection_exceeded = projections[False][1].over_budget
        proposal_value = {"id": proposal.id, "storedCanonicalHash": proposal.canonical_hash}
        if (proposal.validator_version, proposal.canonicalization_version) != (VALIDATOR_VERSION_V2, CANONICALIZATION_VERSION_V2):
            proposal_value.update(state="unsupported_version", errorCode="unsupported_validator")
        else:
            try:
                verified_candidate(db, proposal.id)
                proposal_value.update(state="verified", verifiedCanonicalHash=proposal.canonical_hash)
            except (ADV4Error, ValueError, TypeError, KeyError):
                proposal_value.update(state="integrity_error", errorCode="candidate_integrity")
        identity = {"version": INPUT_VERSION, "directiveId": proposal.directive_id,
                    "proposal": proposal_value, "evidence": _evidence_observation(
                        db, proposal, document_cache=_document_cache, prepared=prepared),
                    "applicabilityProjection": _projection_observation(
                        db, proposal, obligation=False,
                        source_work_exceeded=prepared[3].over_budget or projection_page_exceeded,
                        prepared=projections[False]),
                    "obligationProjection": _projection_observation(
                        db, proposal, obligation=True,
                        source_work_exceeded=(prepared[3].over_budget or projection_page_exceeded
                                              or parent_projection_exceeded),
                        prepared=projections[True])}
        identity_bytes = review_canonical_bytes(identity)
        identity_hash = review_hash(INPUT_VERSION, identity_bytes)
        instant = observed_at or _now()
        audit = {"version": OBSERVATION_VERSION, "inputIdentityHash": identity_hash,
                 "observedAt": _time(instant)}
        audit_bytes = review_canonical_bytes(audit)
        return {"input_identity_bytes": identity_bytes, "input_identity_hash": identity_hash,
                "observation_bytes": audit_bytes, "observation_hash": review_hash(OBSERVATION_VERSION, audit_bytes),
                "observed_at": instant}


def _auth_snapshot(auth: dict[str, Any], action: str, instant: datetime) -> dict[str, Any]:
    stable = {"version": "paprnav-ad-v4-review-authorization-1", "policyName": CONTRACT_VERSION,
              "policyVersion": "1", "serverAuthorized": True, "action": action, **auth}
    payload = review_canonical_bytes(stable)
    return {**stable, "decisionTime": _time(instant),
            "authorizationObservationHash": review_hash("paprnav-ad-v4-review-auth-observation-1", payload),
            "claimsHash": review_hash("paprnav-ad-v4-review-claims-1", payload)}


def _auth_hashes(auth: dict[str, Any]) -> dict[str, str]:
    return {action: _auth_snapshot(auth, action, _now())["authorizationObservationHash"]
            for action in ACTIONS.values()}


def _blob(values: dict[str, Any], name: str, domain: str, payload: Any) -> None:
    encoded = review_canonical_bytes(payload)
    values[name + "_bytes"] = encoded
    values[name + "_hash"] = review_hash(domain, encoded)


def _common(proposal: ADV4CandidateProposal, auth: dict[str, Any], *, idempotency_key: str,
            request_bytes: bytes, request_hash: str) -> dict[str, Any]:
    values = {"id": str(uuid.uuid4()), "proposal_id": proposal.id, "directive_id": proposal.directive_id,
              "actor_user_id": auth["actorUserId"], "authorizing_membership_id": auth["authorizingMembershipId"],
              "organization_id": auth["organizationId"], "contract_version": CONTRACT_VERSION,
              "auth_policy_version": "1", "endpoint_action": auth["action"],
              "idempotency_key": idempotency_key, "request_canonical_bytes": request_bytes,
              "request_hash": request_hash}
    _blob(values, "auth_snapshot", "paprnav-ad-v4-review-authorization-1", auth)
    return values


def _record_envelope(model: Any, values: dict[str, Any]) -> dict[str, Any]:
    record = {}
    for column in model.__table__.columns:
        name = column.name
        if name.endswith("_bytes") or name in {"row_hash", "event_hash", "signature_hash"}:
            continue
        value = values.get(name)
        record[name] = _time(value) if isinstance(value, datetime) else value
    return {"version": CONTRACT_VERSION, "table": model.__tablename__, "record": record}


def _new_record(db: Session, model: Any, values: dict[str, Any]) -> Any:
    encoded = review_canonical_bytes(_record_envelope(model, values))
    values = {**values, "canonical_bytes": encoded,
              "event_hash" if model is ADV4ReviewCaseEvent else "row_hash":
                  review_hash("paprnav-ad-v4-review-row-1", encoded)}
    if model is ADV4SignoffEvent:
        values["signature_hash"] = review_hash("paprnav-ad-v4-review-signature-1", encoded)
    row = model(**values)
    db.add(row)
    return row


def _authorship(db: Session, proposal_id: str, *, submission_ids: set[str] | None = None) -> dict[str, Any]:
    sources: set[tuple[str, str, str, str, str]] = set()
    submissions = select(
        ADV4CandidateSubmission.id, ADV4CandidateSubmission.actor_user_id,
        ADV4CandidateSubmission.request_hash,
    ).where(ADV4CandidateSubmission.proposal_id == proposal_id)
    if submission_ids is not None:
        submissions = submissions.where(ADV4CandidateSubmission.id.in_(submission_ids))
    for submission in _bounded_result_rows(
            db, submissions.order_by(ADV4CandidateSubmission.id), limit=MAX_ARRAY_ITEMS,
            label="review authorship submissions", overflow_code="review_history_limit"):
        sources.add(("ad_v4_candidate_submissions", submission.id, submission.actor_user_id,
                     "candidate_submitter", submission.request_hash))
    bindings = _bounded_result_rows(db, select(
        ADV4CandidateEvidenceBinding.fragment_id,
        ADV4CandidateEvidenceBinding.admitted_event_id,
    ).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal_id).order_by(ADV4CandidateEvidenceBinding.id),
        limit=MAX_EVIDENCE_BINDINGS, label="review evidence bindings")
    fragments = {row.id: row for row in db.execute(select(
        ADEvidenceFragment.id, ADEvidenceFragment.created_by_user_id,
        ADEvidenceFragment.fragment_hash,
    ).where(ADEvidenceFragment.id.in_({binding.fragment_id for binding in bindings})))}
    admissions = {row.id: row for row in db.execute(select(
        ADEvidenceFragmentLifecycleEvent.id,
        ADEvidenceFragmentLifecycleEvent.actor_user_id,
        ADEvidenceFragmentLifecycleEvent.event_hash,
    ).where(ADEvidenceFragmentLifecycleEvent.id.in_(
        {binding.admitted_event_id for binding in bindings})))}
    for binding in bindings:
        fragment = fragments.get(binding.fragment_id)
        admission = admissions.get(binding.admitted_event_id)
        if fragment is not None:
            sources.add(("ad_evidence_fragments", fragment.id, fragment.created_by_user_id,
                         "fragment_creator", fragment.fragment_hash))
        if admission is not None:
            sources.add(("ad_evidence_fragment_lifecycle_events", admission.id, admission.actor_user_id,
                         "fragment_admitter", admission.event_hash))
    return {"version": "paprnav-ad-v4-review-authorship-1", "bindings": [
        dict(zip(("sourceTable", "sourceId", "userId", "authorshipRole", "boundHash"), source))
        for source in sorted(sources)]}


def _cutoff(db: Session, proposal_id: str) -> dict[str, Any]:
    submissions = _bounded_result_rows(db, select(
        ADV4CandidateSubmission.id, ADV4CandidateSubmission.request_hash,
    ).where(
        ADV4CandidateSubmission.proposal_id == proposal_id).order_by(ADV4CandidateSubmission.id),
        limit=MAX_ARRAY_ITEMS, label="review cutoff submissions", overflow_code="review_history_limit")
    relationships = _bounded_result_rows(db, select(
        ADV4CandidateSubmissionRelationship.id,
        ADV4CandidateSubmissionRelationship.relationship_hash,
    ).join(
        ADV4CandidateSubmission, ADV4CandidateSubmission.id == ADV4CandidateSubmissionRelationship.submission_id
    ).where((ADV4CandidateSubmission.proposal_id == proposal_id)
            | (ADV4CandidateSubmissionRelationship.predecessor_proposal_id == proposal_id)).order_by(
                ADV4CandidateSubmissionRelationship.id), limit=MAX_ARRAY_ITEMS,
        label="review cutoff relationships", overflow_code="review_history_limit")
    fragment_ids = set(db.scalars(select(ADV4CandidateEvidenceBinding.fragment_id).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal_id)))
    result = {"version": "paprnav-ad-v4-review-cutoff-1", "proposalId": proposal_id,
              "submissions": [{"id": row.id, "hash": row.request_hash} for row in submissions],
              "relationships": [{"id": row.id, "hash": row.relationship_hash} for row in relationships]}
    for key, owner_ids, event_model, owner_column, owner_name in (
        ("fragmentHeads", fragment_ids, ADEvidenceFragmentLifecycleEvent,
         ADEvidenceFragmentLifecycleEvent.fragment_id, "fragmentId"),
        ("applicabilityHeads", set(db.scalars(select(ADV4CandidateAppProjection.id).where(
            ADV4CandidateAppProjection.proposal_id == proposal_id))), ADV4CandidateAppProjectionEvent,
         ADV4CandidateAppProjectionEvent.projection_id, "projectionId"),
        ("obligationHeads", set(db.scalars(select(ADV4CandidateObligationProjection.id).where(
            ADV4CandidateObligationProjection.proposal_id == proposal_id))), ADV4CandidateObligationProjectionEvent,
         ADV4CandidateObligationProjectionEvent.projection_id, "projectionId"),
    ):
        if not owner_ids:
            result[key] = []
            continue
        ranked = select(
            owner_column.label("owner_id"), event_model.id.label("event_id"),
            event_model.event_hash.label("event_hash"),
            event_model.sequence_number.label("sequence_number"),
            func.row_number().over(partition_by=owner_column,
                                   order_by=event_model.sequence_number.desc()).label("head_rank"),
        ).where(owner_column.in_(owner_ids)).subquery()
        heads = db.execute(select(
            ranked.c.owner_id, ranked.c.event_id, ranked.c.event_hash,
            ranked.c.sequence_number,
        ).where(ranked.c.head_rank == 1).order_by(ranked.c.owner_id).limit(
            len(owner_ids) + 1)).all()
        if len(heads) > len(owner_ids):
            raise _error("review_integrity", "Review cutoff event heads exceed owner cardinality")
        result[key] = [{owner_name: row.owner_id, "eventId": row.event_id,
                        "eventHash": row.event_hash, "sequenceNumber": row.sequence_number}
                       for row in heads]
    return result


def _lock_inputs(db: Session, proposal: ADV4CandidateProposal, *, terminal: bool) -> None:
    _advisory_lock(db, f"candidate-relationship-graph:{proposal.directive_id}")
    db.execute(select(ADV4CandidateProposal.id).where(ADV4CandidateProposal.id == proposal.id).with_for_update())
    _database_gates(db, terminal=terminal)
    db.execute(select(ADV4CandidateEvidenceBinding.id).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal.id).order_by(
            ADV4CandidateEvidenceBinding.id).with_for_update(read=True)).all()
    fragment_ids = select(ADV4CandidateEvidenceBinding.fragment_id).where(
        ADV4CandidateEvidenceBinding.proposal_id == proposal.id)
    db.execute(select(ADEvidenceFragment.id).where(ADEvidenceFragment.id.in_(fragment_ids)).order_by(
        ADEvidenceFragment.id).with_for_update(read=True)).all()
    for model, version in ((ADV4CandidateAppProjection, APP_VERSION),
                           (ADV4CandidateObligationProjection, OBLIGATION_VERSION)):
        _advisory_lock(db, f"projection:{proposal.id}:{version}")
        db.execute(select(model.id).where(model.proposal_id == proposal.id).order_by(
            model.id).with_for_update(read=True)).all()
    _advisory_lock(db, f"review-case:{proposal.id}")


def _mutation_start(db: Session, *, actor: User, membership_id: str, proposal_id: str,
                    directive_id: str, case_id: str | None, event_type: str,
                    idempotency_key: str, body: dict[str, Any]) -> tuple[Any, ...]:
    terminal = event_type == "review_rejected"
    _require_application_gate(write=True, terminal=terminal)
    if not isinstance(idempotency_key, str) or not idempotency_key.strip() or len(idempotency_key) > 255:
        raise _error("invalid_idempotency_key", "A bounded idempotency key is required", 422)
    current_auth = _authorize(db, actor, membership_id, lock=True)
    action = ACTIONS[event_type]
    scope = f"{actor.id}:{membership_id}:{action}:1:{idempotency_key}"
    _advisory_lock(db, f"idem:{scope}")
    _advisory_lock(db, f"candidate-relationship-graph:{directive_id}")
    proposal = _proposal(db, proposal_id)
    if proposal.directive_id != directive_id:
        raise _error("not_found", "V4 proposal does not belong to the requested directive", 404)
    _lock_inputs(db, proposal, terminal=terminal)
    request_value = {"version": CONTRACT_VERSION, "action": action, "directiveId": directive_id,
                     "proposalId": proposal_id, "caseId": case_id, "body": body}
    request_bytes = review_canonical_bytes(request_value)
    request_hash = review_hash("paprnav-ad-v4-review-request-1", request_bytes)
    prior = db.scalar(select(ADV4ReviewCaseEvent).where(
        ADV4ReviewCaseEvent.actor_user_id == actor.id,
        ADV4ReviewCaseEvent.authorizing_membership_id == membership_id,
        ADV4ReviewCaseEvent.endpoint_action == action,
        ADV4ReviewCaseEvent.auth_policy_version == "1",
        ADV4ReviewCaseEvent.idempotency_key == idempotency_key).execution_options(populate_existing=True))
    if prior is not None:
        if prior.request_hash != request_hash or prior.request_canonical_bytes != request_bytes:
            raise _error("idempotency_conflict", "Idempotency key was used for different review content")
        return proposal, current_auth, None, prior, request_bytes, request_hash
    instant = _now()
    auth = _auth_snapshot(current_auth, action, instant)
    if body["expectedAuthorizationObservationHash"] != auth["authorizationObservationHash"]:
        raise _error("stale_authorization", "Authorization facts changed since this review page was read")
    observation = observe_review_inputs(db, proposal_id, observed_at=instant)
    expected_identity = body.get("expectedInputIdentityHash")
    if expected_identity is not None and expected_identity != observation["input_identity_hash"]:
        raise _error("stale_review_inputs", "Review input identity changed")
    return proposal, auth, observation, None, request_bytes, request_hash


def _case(db: Session, case_id: str, *, lock: bool = False) -> ADV4ReviewCase:
    _check_case_history_bytes(db, case_id)
    query = select(ADV4ReviewCase).where(ADV4ReviewCase.id == case_id).execution_options(populate_existing=True)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise _error("not_found", "V4 review case not found", 404)
    return row


def _history_byte_columns(model: Any) -> tuple[Any, ...]:
    # canonical_bytes is included by the suffix exactly once, like every other
    # authoritative blob. Use the mapped schema so new blobs cannot be omitted.
    return tuple(column for column in model.__table__.columns if column.name.endswith("_bytes"))


def _stored_case_history_usage(db: Session, case_id: str) -> tuple[int, int]:
    """One portable scalar query; no case or child blobs cross the DB boundary."""
    totals = []
    for model in _HISTORY_MODELS:
        row_bytes = sum(func.coalesce(func.length(column), 0) for column in _history_byte_columns(model))
        identity = model.id if model is ADV4ReviewCase else model.case_id
        totals.append(select(func.coalesce(func.sum(row_bytes), 0)).where(identity == case_id).scalar_subquery())
    phase = select(func.coalesce(func.max(sql_case(
        (ADV4ReviewCaseEvent.event_type == "review_rejected", 2),
        (ADV4ReviewCaseEvent.event_type == "review_requested", 1),
        else_=0,
    )), 0)).where(ADV4ReviewCaseEvent.case_id == case_id).scalar_subquery()
    with db.no_autoflush:
        row = db.execute(select(sum(totals), phase)).one()
    return int(row[0] or 0), int(row[1] or 0)


def _stored_case_history_bytes(db: Session, case_id: str) -> int:
    return _stored_case_history_usage(db, case_id)[0]


def _pending_case_history_bytes(db: Session, case_id: str) -> int:
    return sum(len(getattr(row, column.name) or b"")
        for row in db.new if isinstance(row, _HISTORY_MODELS)
        and (row.id if isinstance(row, ADV4ReviewCase) else row.case_id) == case_id
        for column in _history_byte_columns(type(row)))


def _pending_case_history_phase(db: Session, case_id: str, stored_phase: int) -> int:
    phase = stored_phase
    for row in db.new:
        if isinstance(row, ADV4ReviewCaseEvent) and row.case_id == case_id:
            phase = max(phase, {"review_requested": 1, "review_rejected": 2}.get(row.event_type, 0))
    return phase


def _case_history_limit(phase: int) -> int:
    return min(MAX_CASE_HISTORY_BYTES, (
        MAX_DRAFT_PHASE_BYTES, MAX_REQUESTED_PHASE_BYTES, MAX_CASE_HISTORY_BYTES)[phase])


def _check_case_history_bytes(db: Session, case_id: str, *, include_pending: bool = False) -> int:
    stored, stored_phase = _stored_case_history_usage(db, case_id)
    pending_phase = _pending_case_history_phase(db, case_id, stored_phase)
    effective_phase = pending_phase if include_pending else stored_phase
    if stored > _case_history_limit(effective_phase):
        raise _error("review_integrity", "Stored review history exceeds the authoritative byte bound")
    if include_pending and stored + _pending_case_history_bytes(db, case_id) > _case_history_limit(pending_phase):
        raise _error("review_history_limit", "Review append exceeds the authoritative history byte bound")
    return stored


def _flush_review_history(db: Session, case_id: str, objects: list[Any] | None = None) -> None:
    # The whole operation (including its event/signoff) is pending before the
    # first flush. Subsequent checks count flushed rows in SQL, pending rows once.
    _check_case_history_bytes(db, case_id, include_pending=True)
    db.flush(objects)


def _bounded_rows(db: Session, query: Any, *, limit: int, label: str,
                  overflow_code: str = "review_integrity") -> list[Any]:
    rows = list(db.scalars(query.limit(limit + 1).execution_options(populate_existing=True)))
    if len(rows) > limit:
        raise _error(overflow_code, f"Stored {label} exceeds the review history bound")
    return rows


def _bounded_result_rows(db: Session, query: Any, *, limit: int, label: str,
                         overflow_code: str = "review_integrity") -> list[Any]:
    rows = list(db.execute(query.limit(limit + 1)))
    if len(rows) > limit:
        raise _error(overflow_code, f"Stored {label} exceeds the review history bound")
    return rows


def _append_event(db: Session, *, case: ADV4ReviewCase, proposal: ADV4CandidateProposal,
                  auth: dict[str, Any], event_type: str, instant: datetime,
                  predecessor: ADV4ReviewCaseEvent | None, idempotency_key: str,
                  request_bytes: bytes, request_hash: str, draft: Any = None,
                  request: Any = None, rejection: Any = None, signoff: Any = None) -> ADV4ReviewCaseEvent:
    next_sequence = predecessor.sequence_number + 1 if predecessor else 0
    if next_sequence >= MAX_EVENTS_PER_CASE:
        raise _error("review_history_limit", "Review case event capacity is exhausted")
    return _new_record(db, ADV4ReviewCaseEvent, {
        **_common(proposal, auth, idempotency_key=idempotency_key,
                  request_bytes=request_bytes, request_hash=request_hash), "case_id": case.id,
        "sequence_number": next_sequence,
        "predecessor_event_hash": predecessor.event_hash if predecessor else None,
        "event_type": event_type,
        "resulting_state": {"case_created": "draft", "draft_saved": "draft",
                            "review_requested": "pending_review", "review_rejected": "rejected"}[event_type],
        "draft_revision_id": draft.id if draft else None,
        "review_request_id": request.id if request else None,
        "rejection_id": rejection.id if rejection else None, "signoff_id": signoff.id if signoff else None,
        "auth_policy_version": "1", "endpoint_action": ACTIONS[event_type],
        "idempotency_key": idempotency_key, "request_canonical_bytes": request_bytes,
        "request_hash": request_hash, "occurred_at": instant,
    })


def _finish(db: Session, *, actor: User, membership_id: str, event: ADV4ReviewCaseEvent,
            idempotent: bool = False) -> dict[str, Any]:
    with db.no_autoflush:
        current_auth = _authorize(db, actor, membership_id, lock=True)
    _flush_review_history(db, event.case_id)
    history = _verify_case_history(db, event.case_id)
    result = _serialize_case(history, through_event_id=event.id, auth=current_auth)
    result["idempotentRetry"] = idempotent
    return result


def create_review_case(db: Session, *, actor: User, membership_id: str, directive_id: str,
                       proposal_id: str, idempotency_key: str,
                       expected_authorization_observation_hash: str,
                       expected_input_identity_hash: str | None = None) -> dict[str, Any]:
    body = {"expectedInputIdentityHash": expected_input_identity_hash,
            "expectedAuthorizationObservationHash": expected_authorization_observation_hash}
    proposal, auth, observation, prior, request_bytes, request_hash = _mutation_start(
        db, actor=actor, membership_id=membership_id, proposal_id=proposal_id,
        directive_id=directive_id, case_id=None, event_type="case_created",
        idempotency_key=idempotency_key, body=body)
    if prior is not None:
        return _finish(db, actor=actor, membership_id=membership_id, event=prior, idempotent=True)
    cases = _bounded_rows(db, select(ADV4ReviewCase).options(load_only(
        ADV4ReviewCase.id, ADV4ReviewCase.case_sequence)).where(ADV4ReviewCase.proposal_id == proposal.id).order_by(
        ADV4ReviewCase.case_sequence), limit=MAX_CASES_PER_PROPOSAL, label="proposal case history")
    if [case.case_sequence for case in cases] != list(range(len(cases))):
        raise _error("review_integrity", "Review case sequence differs")
    if len(cases) >= MAX_CASES_PER_PROPOSAL:
        raise _error("review_history_limit", "Candidate review-case capacity is exhausted")
    if cases:
        if _verify_case_history(db, cases[-1].id)["events"][-1].resulting_state != "rejected":
            raise _error("review_case_open", "This candidate already has an open review case")
    instant = observation["observed_at"]
    case = _new_record(db, ADV4ReviewCase, {
        **_common(proposal, auth, idempotency_key=idempotency_key,
                  request_bytes=request_bytes, request_hash=request_hash),
        **observation, "proposal_canonical_hash": proposal.canonical_hash,
        "case_sequence": len(cases), "predecessor_case_id": cases[-1].id if cases else None,
        "created_at": instant,
    })
    event = _append_event(db, case=case, proposal=proposal, auth=auth, event_type="case_created",
        instant=instant, predecessor=None, idempotency_key=idempotency_key,
        request_bytes=request_bytes, request_hash=request_hash)
    _flush_review_history(db, case.id, [case])
    return _finish(db, actor=actor, membership_id=membership_id, event=event)


def _existing_mutation(db: Session, *, actor: User, membership_id: str, case_id: str,
                       event_type: str, idempotency_key: str, body: dict[str, Any]) -> tuple[Any, ...]:
    # Authorization precedes aggregate lookup, including direct service callers.
    _require_application_gate(write=True, terminal=event_type == "review_rejected")
    _authorize(db, actor, membership_id, lock=True)
    case = _case(db, case_id)
    result = _mutation_start(db, actor=actor, membership_id=membership_id,
        proposal_id=case.proposal_id, directive_id=case.directive_id, case_id=case.id,
        event_type=event_type, idempotency_key=idempotency_key, body=body)
    case = _case(db, case_id, lock=True)
    if result[3] is not None:
        return case, None, *result
    history = _verify_case_history(db, case.id)
    if len(history["events"]) >= MAX_EVENTS_PER_CASE:
        raise _error("review_history_limit", "Review case event capacity is exhausted")
    head = history["events"][-1]
    if head.event_hash != body["expectedPredecessorEventHash"]:
        raise _error("stale_review_predecessor", "Review event head changed")
    expected_state = "pending_review" if event_type == "review_rejected" else "draft"
    if head.resulting_state != expected_state:
        raise _error("review_lifecycle_conflict", "Review case does not permit this transition")
    return case, history, *result


def save_review_draft(db: Session, *, actor: User, membership_id: str, case_id: str,
                      idempotency_key: str, expected_predecessor_event_hash: str,
                      expected_input_identity_hash: str, expected_authorization_observation_hash: str,
                      annotations: list[dict[str, str]], intended_action: str = "undecided") -> dict[str, Any]:
    _validate_annotations(annotations)
    if intended_action not in {"undecided", "reject"}:
        raise _error("review_payload_invalid", "Draft intent must be undecided or reject", 422)
    body = {"expectedPredecessorEventHash": expected_predecessor_event_hash,
            "expectedInputIdentityHash": expected_input_identity_hash,
            "expectedAuthorizationObservationHash": expected_authorization_observation_hash,
            "annotations": annotations, "intendedAction": intended_action}
    case, history, proposal, auth, observation, prior, request_bytes, request_hash = _existing_mutation(
        db, actor=actor, membership_id=membership_id, case_id=case_id,
        event_type="draft_saved", idempotency_key=idempotency_key, body=body)
    if prior is not None:
        return _finish(db, actor=actor, membership_id=membership_id, event=prior, idempotent=True)
    drafts = history["drafts"]
    if len(drafts) >= MAX_DRAFT_REVISIONS_PER_CASE:
        raise _error("review_history_limit", "Review case draft capacity is exhausted")
    values = {**_common(proposal, auth, idempotency_key=idempotency_key,
                       request_bytes=request_bytes, request_hash=request_hash), **observation, "case_id": case.id,
              "revision_number": len(drafts), "predecessor_draft_id": drafts[-1].id if drafts else None,
              "expected_predecessor_event_hash": expected_predecessor_event_hash,
              "intended_action": intended_action, "created_at": observation["observed_at"]}
    _blob(values, "annotation", "paprnav-ad-v4-review-annotation-1",
          {"version": "paprnav-ad-v4-review-annotation-1", "annotations": annotations})
    draft = _new_record(db, ADV4ReviewDraftRevision, values)
    event = _append_event(db, case=case, proposal=proposal, auth=auth, event_type="draft_saved",
        instant=observation["observed_at"], predecessor=history["events"][-1],
        idempotency_key=idempotency_key, request_bytes=request_bytes, request_hash=request_hash, draft=draft)
    _flush_review_history(db, case.id, [draft])
    return _finish(db, actor=actor, membership_id=membership_id, event=event)


def request_review(db: Session, *, actor: User, membership_id: str, case_id: str,
                   idempotency_key: str, expected_predecessor_event_hash: str,
                   expected_input_identity_hash: str, expected_authorization_observation_hash: str,
                   draft_revision_id: str | None = None) -> dict[str, Any]:
    body = {"expectedPredecessorEventHash": expected_predecessor_event_hash,
            "expectedInputIdentityHash": expected_input_identity_hash,
            "expectedAuthorizationObservationHash": expected_authorization_observation_hash,
            "draftRevisionId": draft_revision_id}
    case, history, proposal, auth, observation, prior, request_bytes, request_hash = _existing_mutation(
        db, actor=actor, membership_id=membership_id, case_id=case_id,
        event_type="review_requested", idempotency_key=idempotency_key, body=body)
    if prior is not None:
        return _finish(db, actor=actor, membership_id=membership_id, event=prior, idempotent=True)
    drafts = history["drafts"]
    if draft_revision_id != (drafts[-1].id if drafts else None):
        raise _error("stale_review_draft", "Review request must freeze the latest draft")
    authorship = _authorship(db, proposal.id)
    values = {**_common(proposal, auth, idempotency_key=idempotency_key,
                       request_bytes=request_bytes, request_hash=request_hash), **observation, "case_id": case.id,
              "draft_revision_id": draft_revision_id,
              "expected_predecessor_event_hash": expected_predecessor_event_hash,
              "authorship_source_count": len(authorship["bindings"]), "requested_at": observation["observed_at"]}
    _blob(values, "cutoff", "paprnav-ad-v4-review-cutoff-1", _cutoff(db, proposal.id))
    _blob(values, "authorship_set", "paprnav-ad-v4-review-authorship-1", authorship)
    request = _new_record(db, ADV4ReviewRequest, values)
    event = _append_event(db, case=case, proposal=proposal, auth=auth, event_type="review_requested",
        instant=observation["observed_at"], predecessor=history["events"][-1],
        idempotency_key=idempotency_key, request_bytes=request_bytes, request_hash=request_hash, request=request)
    _flush_review_history(db, case.id, [request])
    return _finish(db, actor=actor, membership_id=membership_id, event=event)


def reject_review_case(db: Session, *, actor: User, membership_id: str, case_id: str,
                       idempotency_key: str, expected_predecessor_event_hash: str,
                       expected_request_id: str, expected_input_identity_hash: str,
                       expected_authorization_observation_hash: str, reason_codes: list[str],
                       explanation: str) -> dict[str, Any]:
    _validate_reasons(reason_codes, explanation)
    body = {"expectedPredecessorEventHash": expected_predecessor_event_hash,
            "expectedRequestId": expected_request_id, "expectedInputIdentityHash": expected_input_identity_hash,
            "expectedAuthorizationObservationHash": expected_authorization_observation_hash,
            "reasonCodes": sorted(reason_codes), "explanation": explanation}
    case, history, proposal, auth, observation, prior, request_bytes, request_hash = _existing_mutation(
        db, actor=actor, membership_id=membership_id, case_id=case_id,
        event_type="review_rejected", idempotency_key=idempotency_key, body=body)
    if prior is not None:
        return _finish(db, actor=actor, membership_id=membership_id, event=prior, idempotent=True)
    request = history["requests"][0]
    if expected_request_id != request.id:
        raise _error("stale_review_request", "Review rejection must bind the frozen request")
    codes = set(reason_codes)
    if request.input_identity_hash != observation["input_identity_hash"]:
        codes.add("input_changed")
    instant = observation["observed_at"]
    values = {**_common(proposal, auth, idempotency_key=idempotency_key,
                       request_bytes=request_bytes, request_hash=request_hash), "case_id": case.id, "request_id": request.id,
              "proposal_canonical_hash": case.proposal_canonical_hash,
              "requested_input_identity_hash": request.input_identity_hash,
              "requested_observation_hash": request.observation_hash,
              "decision_input_identity_bytes": observation["input_identity_bytes"],
              "decision_input_identity_hash": observation["input_identity_hash"],
              "decision_observation_bytes": observation["observation_bytes"],
              "decision_observation_hash": observation["observation_hash"],
              "decision_observed_at": instant, "expected_predecessor_event_hash": expected_predecessor_event_hash,
              "rejected_at": instant}
    _blob(values, "reasons", "paprnav-ad-v4-review-reasons-1",
          {"version": "paprnav-ad-v4-review-reasons-1", "codes": sorted(codes), "explanation": explanation})
    rejection = _new_record(db, ADV4ReviewRejection, values)
    signoff = _new_record(db, ADV4SignoffEvent, {
        **_common(proposal, auth, idempotency_key=idempotency_key,
                  request_bytes=request_bytes, request_hash=request_hash), "case_id": case.id, "request_id": request.id,
        "rejection_id": rejection.id, "action": "reject", "rejection_hash": rejection.row_hash,
        "requested_input_identity_hash": request.input_identity_hash,
        "requested_observation_hash": request.observation_hash,
        "decision_input_identity_hash": rejection.decision_input_identity_hash,
        "decision_observation_hash": rejection.decision_observation_hash,
        "authorization_observation_hash": auth["authorizationObservationHash"], "signed_at": instant,
    })
    event = _append_event(db, case=case, proposal=proposal, auth=auth, event_type="review_rejected",
        instant=instant, predecessor=history["events"][-1], idempotency_key=idempotency_key,
        request_bytes=request_bytes, request_hash=request_hash, request=request, rejection=rejection, signoff=signoff)
    _flush_review_history(db, case.id, [rejection])
    _flush_review_history(db, case.id, [signoff])
    return _finish(db, actor=actor, membership_id=membership_id, event=event)


_BLOB_DOMAINS = {
    "auth_snapshot": "paprnav-ad-v4-review-authorization-1",
    "input_identity": INPUT_VERSION, "decision_input_identity": INPUT_VERSION,
    "observation": OBSERVATION_VERSION, "decision_observation": OBSERVATION_VERSION,
    "annotation": "paprnav-ad-v4-review-annotation-1",
    "cutoff": "paprnav-ad-v4-review-cutoff-1",
    "authorship_set": "paprnav-ad-v4-review-authorship-1",
    "reasons": "paprnav-ad-v4-review-reasons-1",
    "request_canonical": "paprnav-ad-v4-review-request-1",
}
_REQUEST_BODY_KEYS = {
    "case_created": {"expectedAuthorizationObservationHash", "expectedInputIdentityHash"},
    "draft_saved": {"expectedAuthorizationObservationHash", "expectedInputIdentityHash",
                    "expectedPredecessorEventHash", "annotations", "intendedAction"},
    "review_requested": {"expectedAuthorizationObservationHash", "expectedInputIdentityHash",
                         "expectedPredecessorEventHash", "draftRevisionId"},
    "review_rejected": {"expectedAuthorizationObservationHash", "expectedInputIdentityHash",
                        "expectedPredecessorEventHash", "expectedRequestId", "reasonCodes", "explanation"},
}


def _validate_annotations(annotations: Any) -> None:
    if not isinstance(annotations, list) or len(annotations) > 128:
        raise _error("review_payload_invalid", "At most 128 review annotations are allowed", 422)
    for annotation in annotations:
        if (not isinstance(annotation, dict) or set(annotation) != {"pointer", "text"}
            or not isinstance(annotation["pointer"], str) or not 1 <= len(annotation["pointer"]) <= 1024
            or not annotation["pointer"].startswith("/") or re.search(r"~(?![01])", annotation["pointer"])
            or not isinstance(annotation["text"], str) or not annotation["text"].strip()
            or len(annotation["text"]) > 4096):
            raise _error("review_payload_invalid", "Review annotations require a JSON pointer and bounded text", 422)
    review_canonical_bytes(annotations)


def _validate_reasons(codes: Any, explanation: Any) -> None:
    if (not isinstance(codes, list) or not 1 <= len(codes) <= 7
        or any(not isinstance(code, str) or code not in REASON_CODES for code in codes)
        or len(set(codes)) != len(codes) or not isinstance(explanation, str)
        or not explanation.strip() or len(explanation) > 4096):
        raise _error("review_payload_invalid", "Rejection requires distinct controlled reasons and bounded explanation", 422)
    review_canonical_bytes({"codes": codes, "explanation": explanation})


def _read_blob(encoded: bytes) -> Any:
    try:
        if not isinstance(encoded, bytes) or not 2 <= len(encoded) <= MAX_BYTES:
            raise ValueError("blob size differs")
        value = json.loads(encoded.decode("utf-8"))
        if review_canonical_bytes(value) != encoded:
            raise ValueError("blob is not canonical")
        return value
    except (ValueError, TypeError, UnicodeError) as exc:
        raise _error("review_integrity", "Review canonical blob differs") from exc


def _verify_observation(row: Any, *, decision: bool = False) -> None:
    prefix = "decision_" if decision else ""
    identity = _read_blob(getattr(row, prefix + "input_identity_bytes"))
    audit = _read_blob(getattr(row, prefix + "observation_bytes"))
    if (not isinstance(identity, dict) or set(identity) != {
        "version", "directiveId", "proposal", "evidence", "applicabilityProjection", "obligationProjection"}
        or identity["version"] != INPUT_VERSION or identity["directiveId"] != row.directive_id
        or audit != {"version": OBSERVATION_VERSION,
                     "inputIdentityHash": getattr(row, prefix + "input_identity_hash"),
                     "observedAt": _time(getattr(row, prefix + "observed_at"))}):
        raise _error("review_integrity", "Review observation envelope differs")
    for family in ("proposal", "evidence", "applicabilityProjection", "obligationProjection"):
        component = identity[family]
        if not isinstance(component, dict):
            raise _error("review_integrity", "Review observation component differs")
        state = component.get("state")
        if state not in {"verified", "missing", "stale", "integrity_error", "unsupported_version"}:
            raise _error("review_integrity", "Review observation state differs")
        if any(value is None for value in component.values()):
            raise _error("review_integrity", "Review observation must preserve field absence")
        if state == "verified":
            if "errorCode" in component:
                raise _error("review_integrity", "Verified review observation has an error")
        elif (component.get("errorCode") not in {
            "candidate_integrity", "evidence_integrity", "evidence_not_current", "projection_integrity",
            "projection_missing", "projection_stale", "unsupported_version", "unsupported_validator",
            "missing_evidence", "source_identity_or_evidence_missing"}
            or {"verifiedCanonicalHash", "verifiedBindingHash"} & set(component)):
            raise _error("review_integrity", "Nonverified review observation differs")
        if family == "proposal":
            expected = {"state", "id", "storedCanonicalHash",
                        "verifiedCanonicalHash" if state == "verified" else "errorCode"}
            if (set(component) != expected or state == "missing" or component["id"] != row.proposal_id
                or (state == "verified" and component["verifiedCanonicalHash"] != component["storedCanonicalHash"])):
                raise _error("review_integrity", "Observed proposal identity differs")
        elif family == "evidence":
            allowed = {"state", "storedBindingHash", "verifiedBindingHash", "headSetHash", "errorCode"}
            if (not set(component) <= allowed or "storedBindingHash" not in component
                or (state == "verified" and (not {"verifiedBindingHash", "headSetHash"} <= set(component)
                    or component["verifiedBindingHash"] != component["storedBindingHash"]))):
                raise _error("review_integrity", "Observed evidence identity differs")
        elif (not set(component) <= {"state", "id", "storedHash", "eventHeadHash", "errorCode"}
              or (state == "missing" and set(component) != {"state", "errorCode"})
              or (state == "verified" and set(component) != {"state", "id", "storedHash", "eventHeadHash"})):
            raise _error("review_integrity", "Observed projection identity differs")
        for key, value in component.items():
            if key.endswith("Hash") and (not isinstance(value, str) or not _HASH.fullmatch(value)):
                raise _error("review_integrity", "Observed digest encoding differs")


def _verify_observation_sources(db: Session, row: Any, *, decision: bool = False) -> None:
    prefix = "decision_" if decision else ""
    identity = _read_blob(getattr(row, prefix + "input_identity_bytes"))
    proposal = _proposal(db, row.proposal_id)
    if (identity["proposal"]["storedCanonicalHash"] != proposal.canonical_hash
        or identity["evidence"]["storedBindingHash"] != proposal.evidence_binding_hash):
        raise _error("review_integrity", "Frozen observation differs from immutable candidate identity")
    if identity["evidence"]["state"] == "verified":
        heads = {}
        for binding in db.scalars(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == proposal.id)):
            admission = _fresh(db, ADEvidenceFragmentLifecycleEvent, id=binding.admitted_event_id)
            if (admission is None or admission.fragment_id != binding.fragment_id
                or admission.event_hash != binding.admitted_event_hash):
                raise _error("review_integrity", "Frozen evidence admission differs")
            heads[binding.fragment_id] = {"fragmentId": binding.fragment_id, "eventId": admission.id,
                                          "eventHash": admission.event_hash, "sequenceNumber": admission.sequence_number}
        expected = review_hash("paprnav-ad-v4-review-evidence-heads-1",
                               review_canonical_bytes([heads[key] for key in sorted(heads)]))
        if not heads or identity["evidence"]["headSetHash"] != expected:
            raise _error("review_integrity", "Frozen evidence head identity differs")
    for name, model, event_model in (
        ("applicabilityProjection", ADV4CandidateAppProjection, ADV4CandidateAppProjectionEvent),
        ("obligationProjection", ADV4CandidateObligationProjection, ADV4CandidateObligationProjectionEvent),
    ):
        component = identity[name]
        if "id" not in component:
            continue
        projection = _fresh(db, model, id=component["id"])
        if (projection is None or projection.proposal_id != proposal.id
            or projection.directive_id != row.directive_id
            or component.get("storedHash", projection.projection_hash) != projection.projection_hash):
            raise _error("review_integrity", "Frozen projection identity differs")
        if "eventHeadHash" in component:
            event = db.scalar(select(event_model.id).where(event_model.projection_id == projection.id,
                event_model.event_hash == component["eventHeadHash"]))
            if event is None:
                raise _error("review_integrity", "Frozen projection event head differs")


def _verify_record(row: Any, *, action: str, instant: datetime, case: ADV4ReviewCase) -> dict[str, Any]:
    if row.contract_version != CONTRACT_VERSION:
        raise _error("historical_verifier_unavailable", "Historical V4 review verifier is unavailable")
    values = {column.name: getattr(row, column.name) for column in row.__table__.columns}
    if (row.proposal_id != case.proposal_id or row.directive_id != case.directive_id
        or (hasattr(row, "case_id") and row.case_id != case.id)
        or row.endpoint_action != action or row.auth_policy_version != "1"
        or not row.idempotency_key.strip() or len(row.idempotency_key) > 255
        or row.canonical_bytes != review_canonical_bytes(_record_envelope(type(row), values))):
        raise _error("review_integrity", "Review row identity or canonical envelope differs")
    digest = row.event_hash if isinstance(row, ADV4ReviewCaseEvent) else row.row_hash
    if digest != review_hash("paprnav-ad-v4-review-row-1", row.canonical_bytes):
        raise _error("review_integrity", "Review row digest differs")
    blobs = {}
    for key, value in values.items():
        if key.endswith("_hash") and value is not None and (not isinstance(value, str) or not _HASH.fullmatch(value)):
            raise _error("review_integrity", "Review digest encoding differs")
        if key.endswith("_bytes") and key != "canonical_bytes":
            name = key[:-6]
            payload = _read_blob(value)
            hash_name = "request_hash" if name == "request_canonical" else name + "_hash"
            if name not in _BLOB_DOMAINS or values[hash_name] != review_hash(_BLOB_DOMAINS[name], value):
                raise _error("review_integrity", "Review nested blob digest differs")
            blobs[name] = payload
    auth = blobs["auth_snapshot"]
    auth_keys = {"version", "policyName", "policyVersion", "actorUserId", "authorizingMembershipId",
                 "organizationId", "userStatus", "membershipStatus", "role", "validityRule",
                 "validFrom", "validUntil", "serverAuthorized", "userUpdatedAt", "membershipUpdatedAt",
                 "action", "decisionTime", "authorizationObservationHash", "claimsHash"}
    if (not isinstance(auth, dict) or set(auth) != auth_keys
        or auth["version"] != "paprnav-ad-v4-review-authorization-1"
        or auth["policyName"] != CONTRACT_VERSION or auth["policyVersion"] != "1"
        or auth["actorUserId"] != row.actor_user_id or auth["authorizingMembershipId"] != row.authorizing_membership_id
        or auth["organizationId"] != row.organization_id or auth["userStatus"] != "active"
        or auth["membershipStatus"] != "active" or auth["role"] != "platform_admin"
        or auth["validityRule"] != "status_only_v1" or auth["validFrom"] is not None
        or auth["validUntil"] is not None or auth["serverAuthorized"] is not True
        or auth["action"] != action or auth["decisionTime"] != _time(instant)):
        raise _error("review_integrity", "Historical authorization snapshot differs")
    for name in ("userUpdatedAt", "membershipUpdatedAt", "decisionTime"):
        if not isinstance(auth[name], str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", auth[name]):
            raise _error("review_integrity", "Historical authorization timestamp differs")
    stable = {key: value for key, value in auth.items()
              if key not in {"authorizationObservationHash", "claimsHash", "decisionTime"}}
    if (auth["authorizationObservationHash"] != review_hash(
        "paprnav-ad-v4-review-auth-observation-1", review_canonical_bytes(stable))
        or auth["claimsHash"] != review_hash("paprnav-ad-v4-review-claims-1", review_canonical_bytes(stable))):
        raise _error("review_integrity", "Historical authorization digest differs")
    if isinstance(row, (ADV4ReviewCase, ADV4ReviewDraftRevision, ADV4ReviewRequest)):
        _verify_observation(row)
    if isinstance(row, ADV4ReviewRejection):
        _verify_observation(row, decision=True)
    if isinstance(row, ADV4SignoffEvent):
        if (row.action != "reject" or row.authorization_observation_hash != auth["authorizationObservationHash"]
            or row.signature_hash != review_hash("paprnav-ad-v4-review-signature-1", row.canonical_bytes)):
            raise _error("review_integrity", "Historical rejecting signature differs")
    return blobs


def _verify_frozen_sources(db: Session, request: ADV4ReviewRequest, blobs: dict[str, Any]) -> None:
    cutoff = blobs["cutoff"]
    if (not isinstance(cutoff, dict) or set(cutoff) != {"version", "proposalId", "submissions", "relationships",
        "fragmentHeads", "applicabilityHeads", "obligationHeads"}
        or cutoff["version"] != "paprnav-ad-v4-review-cutoff-1" or cutoff["proposalId"] != request.proposal_id):
        raise _error("review_integrity", "Frozen review cutoff differs")
    for name, model, digest_name in (("submissions", ADV4CandidateSubmission, "request_hash"),
                                     ("relationships", ADV4CandidateSubmissionRelationship, "relationship_hash")):
        items = cutoff[name]
        if not isinstance(items, list) or len(items) > MAX_ARRAY_ITEMS or items != sorted(items, key=lambda row: row["id"]):
            raise _error("review_integrity", "Frozen source order differs")
        if len({item["id"] for item in items}) != len(items):
            raise _error("review_integrity", "Frozen source identity is duplicated")
        columns = [model.id, getattr(model, digest_name)]
        if name == "submissions":
            columns.append(ADV4CandidateSubmission.proposal_id)
        else:
            columns.extend((ADV4CandidateSubmissionRelationship.submission_id,
                            ADV4CandidateSubmissionRelationship.predecessor_proposal_id))
        sources = {row.id: row for row in db.execute(select(*columns).where(
            model.id.in_({item["id"] for item in items})))}
        relationship_submissions = {}
        if name == "relationships":
            relationship_submissions = {row.id: row for row in db.execute(select(
                ADV4CandidateSubmission.id, ADV4CandidateSubmission.proposal_id,
            ).where(ADV4CandidateSubmission.id.in_(
                {row.submission_id for row in sources.values()})))}
        for item in items:
            source = sources.get(item["id"])
            if set(item) != {"id", "hash"} or source is None or getattr(source, digest_name) != item["hash"]:
                raise _error("review_integrity", "Frozen review source hash differs")
            if name == "submissions" and source.proposal_id != request.proposal_id:
                raise _error("review_integrity", "Frozen submission belongs to another proposal")
            if name == "relationships":
                submission = relationship_submissions.get(source.submission_id)
                if submission is None or (submission.proposal_id != request.proposal_id
                                          and source.predecessor_proposal_id != request.proposal_id):
                    raise _error("review_integrity", "Frozen relationship belongs to another proposal")
    for name, model, owner_column, owner_key in (
        ("fragmentHeads", ADEvidenceFragmentLifecycleEvent, "fragment_id", "fragmentId"),
        ("applicabilityHeads", ADV4CandidateAppProjectionEvent, "projection_id", "projectionId"),
        ("obligationHeads", ADV4CandidateObligationProjectionEvent, "projection_id", "projectionId"),
    ):
        items = cutoff[name]
        if not isinstance(items, list) or items != sorted(items, key=lambda item: item[owner_key]):
            raise _error("review_integrity", "Frozen event order differs")
        if len({item[owner_key] for item in items}) != len(items):
            raise _error("review_integrity", "Frozen event owner is duplicated")
        owner_attribute = getattr(model, owner_column)
        sources = {row.id: row for row in db.execute(select(
            model.id, owner_attribute, model.event_hash, model.sequence_number,
        ).where(model.id.in_({item["eventId"] for item in items})))}
        for item in items:
            source = sources.get(item["eventId"])
            if (set(item) != {owner_key, "eventId", "eventHash", "sequenceNumber"}
                or source is None or getattr(source, owner_column) != item[owner_key]
                or source.event_hash != item["eventHash"] or source.sequence_number != item["sequenceNumber"]):
                raise _error("review_integrity", "Frozen event source differs")
    authors = _authorship(db, request.proposal_id, submission_ids={item["id"] for item in cutoff["submissions"]})
    if blobs["authorship_set"] != authors or request.authorship_source_count != len(authors["bindings"]):
        raise _error("review_integrity", "Frozen authorship differs from its source set")


def _verify_case_history_unchecked(db: Session, case_id: str, *,
                                    source_cache: set[str] | None = None) -> dict[str, Any]:
    if source_cache is None:
        source_cache = set()
    case = _case(db, case_id)
    if not 0 <= case.case_sequence < MAX_CASES_PER_PROPOSAL:
        raise _error("review_integrity", "Review case sequence exceeds the proposal bound")
    history: dict[str, Any] = {"case": case}
    for name, model, order, bound in (
        ("events", ADV4ReviewCaseEvent, ADV4ReviewCaseEvent.sequence_number, MAX_EVENTS_PER_CASE),
        ("drafts", ADV4ReviewDraftRevision, ADV4ReviewDraftRevision.revision_number, MAX_DRAFT_REVISIONS_PER_CASE),
        ("requests", ADV4ReviewRequest, ADV4ReviewRequest.id, 1),
        ("rejections", ADV4ReviewRejection, ADV4ReviewRejection.id, 1),
        ("signoffs", ADV4SignoffEvent, ADV4SignoffEvent.id, 1),
    ):
        history[name] = _bounded_rows(db, select(model).where(model.case_id == case.id).order_by(
            order), limit=bound, label=name)
    events, drafts, requests, rejections, signoffs = (history[name] for name in (
        "events", "drafts", "requests", "rejections", "signoffs"))
    if (not events or [event.sequence_number for event in events] != list(range(len(events)))
        or [draft.revision_number for draft in drafts] != list(range(len(drafts)))
        or any(len(history[name]) > 1 for name in ("requests", "rejections", "signoffs"))):
        raise _error("review_integrity", "Review history cardinality differs")
    proposal = _proposal(db, case.proposal_id)
    if case.proposal_canonical_hash != proposal.canonical_hash or case.directive_id != proposal.directive_id:
        raise _error("review_integrity", "Review case proposal identity differs")
    terminated = select(ADV4ReviewCaseEvent.case_id).where(ADV4ReviewCaseEvent.event_type == "review_rejected")
    open_cases = list(db.scalars(select(ADV4ReviewCase.id).where(
        ADV4ReviewCase.proposal_id == case.proposal_id, ADV4ReviewCase.id.not_in(terminated)).limit(2)))
    if len(open_cases) > 1:
        raise _error("review_integrity", "Candidate has multiple open review cases")
    proposal_cases = _bounded_rows(db, select(ADV4ReviewCase).options(load_only(
        ADV4ReviewCase.id, ADV4ReviewCase.case_sequence)).where(
        ADV4ReviewCase.proposal_id == case.proposal_id).order_by(ADV4ReviewCase.case_sequence),
        limit=MAX_CASES_PER_PROPOSAL, label="proposal cases and predecessors")
    if [row.case_sequence for row in proposal_cases] != list(range(len(proposal_cases))):
        raise _error("review_integrity", "Proposal case sequence differs")
    predecessor_cases = [row for row in proposal_cases if row.case_sequence < case.case_sequence]
    if ([row.case_sequence for row in predecessor_cases] != list(range(case.case_sequence))
        or case.predecessor_case_id != (predecessor_cases[-1].id if predecessor_cases else None)):
        raise _error("review_integrity", "Review case predecessor sequence differs")
    if predecessor_cases:
        predecessor_ids = {row.id for row in predecessor_cases}
        terminal_ids = _bounded_rows(db, select(ADV4ReviewCaseEvent.case_id).where(
            ADV4ReviewCaseEvent.case_id.in_(predecessor_ids),
            ADV4ReviewCaseEvent.event_type == "review_rejected"),
            limit=MAX_CASES_PER_PROPOSAL, label="predecessor terminal events")
        if len(terminal_ids) != len(predecessor_ids) or set(terminal_ids) != predecessor_ids:
            raise _error("review_integrity", "Review successor follows an open case")
    draft_by_id = {row.id: row for row in drafts}
    request = requests[0] if requests else None
    rejection = rejections[0] if rejections else None
    signoff = signoffs[0] if signoffs else None
    seen_drafts: list[str] = []
    seen_request = seen_rejection = False
    previous = None
    for event in events:
        action = ACTIONS.get(event.event_type)
        if (action is None or event.predecessor_event_hash != (previous.event_hash if previous else None)
            or event.endpoint_action != action or event.auth_policy_version != "1"
            or not event.idempotency_key.strip() or len(event.idempotency_key) > 255):
            raise _error("review_integrity", "Review lifecycle identity differs")
        event_blobs = _verify_record(event, action=action, instant=event.occurred_at, case=case)
        envelope = event_blobs["request_canonical"]
        if (not isinstance(envelope, dict) or set(envelope) != {"version", "action", "directiveId", "proposalId", "caseId", "body"}
            or envelope["version"] != CONTRACT_VERSION or envelope["action"] != action
            or envelope["directiveId"] != case.directive_id or envelope["proposalId"] != case.proposal_id
            or envelope["caseId"] != (None if event.event_type == "case_created" else case.id)
            or not isinstance(envelope["body"], dict)):
            raise _error("review_integrity", "Review canonical request differs")
        body = envelope["body"]
        if set(body) != _REQUEST_BODY_KEYS[event.event_type]:
            raise _error("review_integrity", "Review request body is outside its closed branch")
        if body.get("expectedAuthorizationObservationHash") != event_blobs["auth_snapshot"]["authorizationObservationHash"]:
            raise _error("review_integrity", "Review authorization CAS differs")
        if previous is not None and body.get("expectedPredecessorEventHash") != previous.event_hash:
            raise _error("review_integrity", "Review predecessor CAS differs")
        if event.event_type == "case_created":
            if previous is not None or event.resulting_state != "draft" or any(
                (event.draft_revision_id, event.review_request_id, event.rejection_id, event.signoff_id)):
                raise _error("review_integrity", "Review creation event differs")
            owner, stamp = case, case.created_at
            if body.get("expectedInputIdentityHash") not in {None, case.input_identity_hash}:
                raise _error("review_integrity", "Review creation input CAS differs")
        elif event.event_type == "draft_saved":
            owner = draft_by_id.get(event.draft_revision_id)
            if (previous is None or previous.resulting_state != "draft" or event.resulting_state != "draft"
                or owner is None or event.review_request_id or event.rejection_id or event.signoff_id
                or owner.predecessor_draft_id != (seen_drafts[-1] if seen_drafts else None)
                or owner.revision_number != len(seen_drafts)
                or owner.expected_predecessor_event_hash != event.predecessor_event_hash):
                raise _error("review_integrity", "Review draft transition differs")
            stamp = owner.created_at
            seen_drafts.append(owner.id)
        elif event.event_type == "review_requested":
            owner = request
            if (previous is None or previous.resulting_state != "draft" or event.resulting_state != "pending_review"
                or owner is None or event.review_request_id != owner.id or seen_request
                or event.draft_revision_id or event.rejection_id or event.signoff_id
                or owner.draft_revision_id != (seen_drafts[-1] if seen_drafts else None)
                or owner.expected_predecessor_event_hash != event.predecessor_event_hash):
                raise _error("review_integrity", "Review request transition differs")
            stamp = owner.requested_at
            seen_request = True
        else:
            owner = rejection
            if (previous is None or previous.resulting_state != "pending_review" or event.resulting_state != "rejected"
                or not seen_request or seen_rejection or owner is None or signoff is None or request is None
                or event.rejection_id != owner.id or event.signoff_id != signoff.id
                or event.review_request_id != request.id or event.draft_revision_id
                or owner.request_id != request.id or signoff.request_id != request.id or signoff.rejection_id != owner.id
                or owner.expected_predecessor_event_hash != event.predecessor_event_hash
                or owner.proposal_canonical_hash != case.proposal_canonical_hash
                or owner.requested_input_identity_hash != request.input_identity_hash
                or owner.requested_observation_hash != request.observation_hash
                or signoff.requested_input_identity_hash != request.input_identity_hash
                or signoff.requested_observation_hash != request.observation_hash
                or signoff.decision_input_identity_hash != owner.decision_input_identity_hash
                or signoff.decision_observation_hash != owner.decision_observation_hash
                or signoff.rejection_hash != owner.row_hash
                or signoff.request_hash != owner.request_hash
                or signoff.request_canonical_bytes != owner.request_canonical_bytes
                or signoff.idempotency_key != owner.idempotency_key
                or signoff.auth_snapshot_bytes != owner.auth_snapshot_bytes
                or _time(signoff.signed_at) != _time(owner.rejected_at)):
                raise _error("review_integrity", "Review rejection signoff transition differs")
            _verify_record(signoff, action=action, instant=signoff.signed_at, case=case)
            stamp = owner.rejected_at
            seen_rejection = True
        owner_blobs = _verify_record(owner, action=action, instant=stamp, case=case)
        is_rejection = isinstance(owner, ADV4ReviewRejection)
        source_hash = owner.decision_input_identity_hash if is_rejection else owner.input_identity_hash
        if source_hash not in source_cache:
            _verify_observation_sources(db, owner, decision=is_rejection)
            source_cache.add(source_hash)
        if (owner.auth_snapshot_bytes != event.auth_snapshot_bytes or _time(stamp) != _time(event.occurred_at)
            or owner.idempotency_key != event.idempotency_key or owner.request_hash != event.request_hash
            or owner.request_canonical_bytes != event.request_canonical_bytes):
            raise _error("review_integrity", "Review event authorization differs from its object")
        if event.event_type != "case_created":
            actual_input = owner.decision_input_identity_hash if event.event_type == "review_rejected" else owner.input_identity_hash
            if body.get("expectedInputIdentityHash") != actual_input:
                raise _error("review_integrity", "Review input CAS differs")
        if event.event_type == "draft_saved":
            annotation = owner_blobs["annotation"]
            if annotation != {"version": "paprnav-ad-v4-review-annotation-1", "annotations": body.get("annotations")}:
                raise _error("review_integrity", "Draft annotations differ from submitted request")
            _validate_annotations(annotation["annotations"])
            if owner.intended_action != body.get("intendedAction") or owner.intended_action not in {"undecided", "reject"}:
                raise _error("review_integrity", "Draft intent differs")
        elif event.event_type == "review_requested":
            if body.get("draftRevisionId") != owner.draft_revision_id:
                raise _error("review_integrity", "Frozen draft differs from submitted request")
            _verify_frozen_sources(db, owner, owner_blobs)
        elif event.event_type == "review_rejected":
            reasons = owner_blobs["reasons"]
            _validate_reasons(body.get("reasonCodes"), body.get("explanation"))
            codes = set(body["reasonCodes"])
            if owner.decision_input_identity_hash != request.input_identity_hash:
                codes.add("input_changed")
            if (body.get("expectedRequestId") != request.id or reasons != {
                "version": "paprnav-ad-v4-review-reasons-1", "codes": sorted(codes), "explanation": body["explanation"]}):
                raise _error("review_integrity", "Rejection reasons differ from submitted request")
        previous = event
    if (len(seen_drafts) != len(drafts) or bool(requests) != seen_request
        or bool(rejections) != seen_rejection or bool(signoffs) != seen_rejection):
        raise _error("review_integrity", "Review object-event completeness differs")
    return history


def _verify_case_history(db: Session, case_id: str, *, source_cache: set[str] | None = None) -> dict[str, Any]:
    try:
        return _verify_case_history_unchecked(db, case_id, source_cache=source_cache)
    except ADV4Error as exc:
        if exc.http_status == 422:
            raise _error("review_integrity", "Stored review payload fails its historical contract") from exc
        raise
    except (KeyError, TypeError, AttributeError, ValueError, StopIteration) as exc:
        raise _error("review_integrity", "Stored review history is malformed") from exc


def _history_payload(row: Any) -> dict[str, Any]:
    common = {"rowHash": row.row_hash, "actorUserId": row.actor_user_id,
              "authorizingMembershipId": row.authorizing_membership_id}
    if isinstance(row, ADV4ReviewDraftRevision):
        return {**common, "draftRevisionId": row.id, "revisionNumber": row.revision_number,
                "inputIdentityHash": row.input_identity_hash, "observationHash": row.observation_hash,
                "annotations": _read_blob(row.annotation_bytes)["annotations"],
                "intendedAction": row.intended_action, "createdAt": row.created_at}
    if isinstance(row, ADV4ReviewRequest):
        return {**common, "reviewRequestId": row.id, "draftRevisionId": row.draft_revision_id,
                "inputIdentityHash": row.input_identity_hash, "observationHash": row.observation_hash,
                "cutoffHash": row.cutoff_hash, "authorshipSetHash": row.authorship_set_hash,
                "authorshipSourceCount": row.authorship_source_count, "requestedAt": row.requested_at}
    common.update(reviewRequestId=row.request_id,
                  requestedInputIdentityHash=row.requested_input_identity_hash,
                  requestedObservationHash=row.requested_observation_hash,
                  decisionInputIdentityHash=row.decision_input_identity_hash,
                  decisionObservationHash=row.decision_observation_hash)
    if isinstance(row, ADV4ReviewRejection):
        reasons = _read_blob(row.reasons_bytes)
        return {**common, "rejectionId": row.id, "reasonCodes": reasons["codes"],
                "explanation": reasons["explanation"], "rejectedAt": row.rejected_at}
    return {**common, "signoffId": row.id, "rejectionId": row.rejection_id, "action": row.action,
            "authorizationObservationHash": row.authorization_observation_hash,
            "signatureHash": row.signature_hash, "signedAt": row.signed_at}


def _serialize_case(history: dict[str, Any], *, through_event_id: str | None = None,
                    observation: dict[str, Any] | None = None,
                    auth: dict[str, Any] | None = None, draft_limit: int = 100,
                    draft_offset: int = 0, event_limit: int = 100,
                    event_offset: int = 0, summary_only: bool = False) -> dict[str, Any]:
    case = history["case"]
    events = history["events"]
    if through_event_id is not None:
        index = next(index for index, event in enumerate(events) if event.id == through_event_id)
        events = events[:index + 1]
    last = events[-1]
    drafts = [row for row in history["drafts"] if row.id in {event.draft_revision_id for event in events}]
    request = next((row for row in history["requests"] if row.id in {event.review_request_id for event in events}), None)
    rejection = next((row for row in history["rejections"] if row.id == last.rejection_id), None)
    signoff = next((row for row in history["signoffs"] if row.id == last.signoff_id), None)
    bound = rejection or request or (drafts[-1] if drafts else case)
    if observation is None:
        prefix = "decision_" if rejection else ""
        observation = {name: getattr(bound, prefix + name) for name in (
            "input_identity_bytes", "input_identity_hash", "observation_bytes", "observation_hash", "observed_at")}
    return {
        "caseId": case.id, "proposalId": case.proposal_id, "directiveId": case.directive_id,
        "caseSequence": case.case_sequence, "state": last.resulting_state,
        "proposalCanonicalHash": case.proposal_canonical_hash,
        "inputIdentityHash": observation["input_identity_hash"], "observationHash": observation["observation_hash"],
        "inputIdentity": _read_blob(observation["input_identity_bytes"]),
        "observation": _read_blob(observation["observation_bytes"]),
        "authorizationObservationHashes": _auth_hashes(auth) if auth is not None else {},
        "latestEventHash": last.event_hash, "draftRevisionId": drafts[-1].id if drafts else None,
        "reviewRequestId": request.id if request else None, "rejectionId": rejection.id if rejection else None,
        "signoffId": signoff.id if signoff else None,
        "drafts": [] if summary_only else [_history_payload(row) for row in drafts[draft_offset:draft_offset + draft_limit]],
        "draftTotal": len(drafts), "draftLimit": draft_limit, "draftOffset": draft_offset,
        "eventTotal": len(events), "eventLimit": event_limit, "eventOffset": event_offset,
        "reviewRequest": _history_payload(request) if request else None,
        "rejection": _history_payload(rejection) if rejection else None,
        "signoff": _history_payload(signoff) if signoff else None,
        "events": [] if summary_only else [{"eventId": event.id, "sequenceNumber": event.sequence_number,
                    "predecessorEventHash": event.predecessor_event_hash,
                    "eventType": event.event_type, "resultingState": event.resulting_state,
                    "eventHash": event.event_hash, "actorUserId": event.actor_user_id,
                    "authorizingMembershipId": event.authorizing_membership_id,
                    "occurredAt": event.occurred_at} for event in events[event_offset:event_offset + event_limit]],
        "createdAt": case.created_at,
    }


def verified_review_case(db: Session, *, case_id: str, actor: User, membership_id: str,
                         draft_limit: int = 100, draft_offset: int = 0,
                         event_limit: int = 100, event_offset: int = 0) -> dict[str, Any]:
    auth = authorize_review_audit(db, actor, membership_id)
    for limit, offset in ((draft_limit, draft_offset), (event_limit, event_offset)):
        if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or not 0 <= offset <= 10000:
            raise _error("review_page_invalid", "Review history pagination is outside the supported bounds", 422)
    with db.no_autoflush:
        try:
            history = _verify_case_history(db, case_id)
            observation = observe_review_inputs(db, history["case"].proposal_id)
            return _serialize_case(history, observation=observation, auth=auth,
                draft_limit=draft_limit, draft_offset=draft_offset,
                event_limit=event_limit, event_offset=event_offset)
        except ADV4Error as exc:
            if exc.http_status == 422:
                raise _error("review_integrity", "Stored review payload fails its historical contract") from exc
            raise
        except (KeyError, TypeError, AttributeError, ValueError, StopIteration) as exc:
            raise _error("review_integrity", "Stored review history is malformed") from exc


def review_proposal_observation(db: Session, *, directive_id: str, proposal_id: str,
                                actor: User, membership_id: str) -> dict[str, Any]:
    auth = authorize_review_audit(db, actor, membership_id)
    with db.no_autoflush:
        proposal = _proposal(db, proposal_id)
        if proposal.directive_id != directive_id:
            raise _error("not_found", "V4 candidate does not belong to the requested directive", 404)
        observation = observe_review_inputs(db, proposal.id)
        return {"proposalId": proposal.id, "directiveId": directive_id,
                "inputIdentityHash": observation["input_identity_hash"],
                "observationHash": observation["observation_hash"],
                "inputIdentity": _read_blob(observation["input_identity_bytes"]),
                "observation": _read_blob(observation["observation_bytes"]),
                "authorizationObservationHashes": _auth_hashes(auth)}


def list_review_cases(db: Session, *, actor: User, membership_id: str, limit: int = 25,
                      offset: int = 0, directive_id: str | None = None,
                      proposal_id: str | None = None) -> dict[str, Any]:
    auth = authorize_review_audit(db, actor, membership_id)
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or not 0 <= offset <= 10000:
        raise _error("review_page_invalid", "Review pagination is outside the supported bounds", 422)
    with db.no_autoflush:
        query = select(ADV4ReviewCase.id, ADV4ReviewCase.proposal_id)
        if directive_id is not None:
            query = query.where(ADV4ReviewCase.directive_id == directive_id)
        if proposal_id is not None:
            query = query.where(ADV4ReviewCase.proposal_id == proposal_id)
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        cases = list(db.execute(query.order_by(ADV4ReviewCase.created_at.desc(), ADV4ReviewCase.id).limit(limit).offset(offset)))
        results = []
        document_cache: dict[tuple[str, str, int], bool] = {}
        source_cache: set[str] = set()
        proposal_observations: dict[str, dict[str, Any]] = {}
        proposal_ids = sorted({case.proposal_id for case in cases})
        work_metadata = {proposal_id: _evidence_work_metadata(db, proposal_id) for proposal_id in proposal_ids}
        projection_metadata = {
            proposal_id: {
                obligation: _prepare_projection_observation(db, proposal_id, obligation=obligation)
                for obligation in (False, True)
            }
            for proposal_id in proposal_ids
        }
        # Preflight the full page before its first external read. A queue-wide
        # budget failure must not turn a proposal's stable identity nonverified.
        within_budget = [work for work in work_metadata.values() if not work.over_budget]
        _check_source_work_budget((key for work in within_budget for key in work.document_keys),
            text_bytes=sum(work.text_bytes + work.lifecycle_reason_bytes for work in within_budget),
            binding_count=sum(work.binding_count for work in within_budget),
            lifecycle_count=sum(work.lifecycle_count for work in within_budget))
        if _projection_work_exceeded(
                prepared[1] for by_kind in projection_metadata.values()
                for prepared in by_kind.values()):
            raise _error("review_work_limit", "Projection histories exceed the review request work budget")
        prepared_evidence = {proposal_id: _prepare_evidence_observation(
            db, _proposal(db, proposal_id), work=work_metadata[proposal_id]) for proposal_id in proposal_ids}
        for case in cases:
            history = _verify_case_history(db, case.id, source_cache=source_cache)
            if case.proposal_id not in proposal_observations:
                proposal_observations[case.proposal_id] = observe_review_inputs(
                    db, case.proposal_id, _document_cache=document_cache,
                    _prepared_evidence=prepared_evidence[case.proposal_id],
                    _prepared_projections=projection_metadata[case.proposal_id])
            results.append(_serialize_case(history, auth=auth, summary_only=True,
                observation=proposal_observations[case.proposal_id]))
        return {"cases": results, "count": len(results), "total": total, "limit": limit, "offset": offset,
                "authorizationObservationHashes": _auth_hashes(auth)}
