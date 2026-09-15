from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
from typing import Any, Iterable

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADV4CandidateAppProjection,
    ADV4CandidateAppProjectionEvent,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateCorrection,
    ADV4CandidateCorrectionRef,
    ADV4CandidateCorrectionSemanticBinding,
    ADV4CandidateEvidenceBinding,
    ADV4CandidateSubmissionRelationship,
    ADV4CandidateObligationAction,
    ADV4CandidateObligationActionDocumentRef,
    ADV4CandidateObligationActionStep,
    ADV4CandidateObligationAmocProvision,
    ADV4CandidateObligationBranch,
    ADV4CandidateObligationDatum,
    ADV4CandidateObligationDocument,
    ADV4CandidateObligationEvidenceLink,
    ADV4CandidateObligationExpression,
    ADV4CandidateObligationExpressionEdge,
    ADV4CandidateObligationMaterializationRequest,
    ADV4CandidateObligationProjection,
    ADV4CandidateObligationProjectionEvent,
    ADV4CandidateObligationRecurrence,
    ADV4CandidateObligationRecurrenceGroup,
    ADV4CandidateObligationRecurrenceGroupMember,
    ADV4CandidateObligationRequirement,
    ADV4CandidateObligationRequirementDependency,
    ADV4CandidateObligationSemanticNode,
    ADV4CandidateObligationTerminatingEffect,
    ADV4CandidateObligationTerminationEdge,
    ADV4CandidateObligationTimingGroup,
    ADV4CandidateObligationTimingTerm,
    ADV4CandidateObligationValueAssertion,
    ADV4CandidateProposal,
    ADV4CandidateSubmission,
    OrganizationMembership,
    User,
)
from app.services.ad_v4_applicability import (
    _node_value,
    _repair_stale_projection_on_materialization,
    _verify_live_evidence,
    projection_state,
    reconstruct_applicability,
)
from app.services.ad_v4_candidates import (
    ADV4Error,
    CANONICALIZATION_VERSION_V2,
    VALIDATOR_VERSION_V2,
    _advisory_lock,
    _authorization,
    canonical_bytes,
    require_v4_database_gate,
    verified_candidate,
    verified_submission,
)
from app.services.ad_evidence import (
    ADEvidenceError,
    verified_evidence_lifecycle_events,
)
from app.services.ad_v4_obligations import (
    APP_MATERIALIZER_VERSION,
    DOMAINS,
    MATERIALIZER_VERSION,
    ObligationApplicabilityTarget,
    ObligationCorrectionReference,
    ObligationIntegrityError,
    ObligationProjectionGraph,
    _row_id,
    build_correction_reference_snapshot,
    materialize_obligation_projection_graph,
    obligation_record_bytes,
)


POLICY_NAME = "paprnav-platform-admin-v4-obligation-materialize"
POLICY_VERSION = "1"
ENDPOINT_ACTION = "materialize_ad_v4_obligations"


@dataclass(frozen=True)
class PersistedObligationMaterialization:
    projection: ADV4CandidateObligationProjection
    request: ADV4CandidateObligationMaterializationRequest
    event: ADV4CandidateObligationProjectionEvent


@dataclass(frozen=True)
class MaterializedObligations:
    projection: ADV4CandidateObligationProjection
    request: ADV4CandidateObligationMaterializationRequest
    created: bool
    idempotent_retry: bool


_COUNT_COLUMNS = {
    "semanticNodeCount": "semantic_node_count",
    "datumCount": "datum_count",
    "evidenceLinkCount": "evidence_link_count",
    "documentCount": "document_count",
    "valueAssertionCount": "value_assertion_count",
    "requirementCount": "requirement_count",
    "actionCount": "action_count",
    "actionStepCount": "action_step_count",
    "actionDocumentRefCount": "action_document_ref_count",
    "branchCount": "branch_count",
    "expressionCount": "expression_count",
    "expressionEdgeCount": "expression_edge_count",
    "requirementDependencyCount": "requirement_dependency_count",
    "timingGroupCount": "timing_group_count",
    "timingTermCount": "timing_term_count",
    "recurrenceCount": "recurrence_count",
    "terminatingEffectCount": "terminating_effect_count",
    "terminationEdgeCount": "termination_edge_count",
    "recurrenceGroupCount": "recurrence_group_count",
    "recurrenceGroupMemberCount": "recurrence_group_member_count",
    "amocProvisionCount": "amoc_provision_count",
    "correctionBindingCount": "correction_binding_count",
}


def _materialization_request_values(
    projection: ADV4CandidateObligationProjection,
    *,
    actor_user_id: str,
    authorizing_membership_id: str,
    organization_id: str,
    actor_role: str,
    actor_status: str,
    idempotency_key: str,
) -> dict[str, Any]:
    request_value = {
        "action": ENDPOINT_ACTION,
        "directiveId": projection.directive_id,
        "proposalId": projection.proposal_id,
        "appProjectionId": projection.app_projection_id,
        "validatorVersion": projection.validator_version,
        "canonicalizationVersion": projection.canonicalization_version,
        "appMaterializerVersion": projection.app_materializer_version,
        "materializerVersion": projection.materializer_version,
        "mappingVersion": projection.mapping_version,
        "mappingDigest": projection.mapping_digest,
    }
    request_bytes = obligation_record_bytes(request_value)
    claims = {
        "actorUserId": actor_user_id,
        "authorizingMembershipId": authorizing_membership_id,
        "organizationId": organization_id,
        "role": actor_role,
        "status": actor_status,
        "endpointAction": ENDPOINT_ACTION,
        "authPolicyVersion": POLICY_VERSION,
    }
    request_identity = {
        "actorUserId": actor_user_id,
        "authorizingMembershipId": authorizing_membership_id,
        "endpointAction": ENDPOINT_ACTION,
        "authPolicyVersion": POLICY_VERSION,
        "idempotencyKey": idempotency_key,
    }
    request_id, identity_hash = _row_id(
        "aoq", "materialization-request", request_identity,
    )
    return {
        "id": request_id,
        "identity_hash": identity_hash,
        "projection_id": projection.id,
        "proposal_id": projection.proposal_id,
        "directive_id": projection.directive_id,
        "app_projection_id": projection.app_projection_id,
        "actor_user_id": actor_user_id,
        "authorizing_membership_id": authorizing_membership_id,
        "organization_id": organization_id,
        "actor_role": actor_role,
        "actor_status": actor_status,
        "auth_policy_name": POLICY_NAME,
        "auth_policy_version": POLICY_VERSION,
        "auth_claims_hash": hashlib.sha256(
            DOMAINS["authClaims"] + obligation_record_bytes(claims)
        ).hexdigest(),
        "endpoint_action": ENDPOINT_ACTION,
        "idempotency_key": idempotency_key,
        "request_canonical_bytes": request_bytes,
        "request_hash": hashlib.sha256(
            DOMAINS["request"] + request_bytes
        ).hexdigest(),
    }


def _projection_event_values(
    projection: ADV4CandidateObligationProjection,
    *,
    correction_binding_set_hash: str,
    causing_request_id: str,
    event_type: str,
    sequence_number: int,
    predecessor_event_hash: str | None,
    cause_kind: str | None,
    cause_id: str | None,
    cause_hash: str | None,
) -> dict[str, Any]:
    event_value = {
        "eventType": event_type,
        "projectionId": projection.id,
        "proposalId": projection.proposal_id,
        "appProjectionId": projection.app_projection_id,
        "sequenceNumber": sequence_number,
        "predecessorEventHash": predecessor_event_hash,
        "proposalCanonicalHash": projection.proposal_canonical_hash,
        "evidenceBindingHash": projection.evidence_binding_hash,
        "appProjectionHash": projection.app_projection_hash,
        "obligationSubtreeHash": projection.obligation_subtree_hash,
        "projectionHash": projection.projection_hash,
        "correctionBindingSetHash": correction_binding_set_hash,
        "causingRequestId": causing_request_id,
        "cause": (
            None if cause_kind is None
            else {"kind": cause_kind, "id": cause_id, "hash": cause_hash}
        ),
    }
    event_bytes = obligation_record_bytes(event_value)
    event_hash = hashlib.sha256(DOMAINS["event"] + event_bytes).hexdigest()
    event_id, identity_hash = _row_id(
        "aov", "projection-event", {
            "projectionId": projection.id,
            "sequenceNumber": sequence_number,
            "eventHash": event_hash,
        },
    )
    return {
        "id": event_id,
        "identity_hash": identity_hash,
        "projection_id": projection.id,
        "proposal_id": projection.proposal_id,
        "app_projection_id": projection.app_projection_id,
        "sequence_number": sequence_number,
        "event_type": event_type,
        "predecessor_event_hash": predecessor_event_hash,
        "proposal_canonical_hash": projection.proposal_canonical_hash,
        "evidence_binding_hash": projection.evidence_binding_hash,
        "app_projection_hash": projection.app_projection_hash,
        "obligation_subtree_hash": projection.obligation_subtree_hash,
        "projection_hash": projection.projection_hash,
        "correction_binding_set_hash": correction_binding_set_hash,
        "causing_request_id": causing_request_id,
        "cause_kind": cause_kind,
        "cause_id": cause_id,
        "cause_hash": cause_hash,
        "canonical_bytes": event_bytes,
        "event_hash": event_hash,
    }


def _root_event_values(
    projection: ADV4CandidateObligationProjection,
    *, correction_binding_set_hash: str, causing_request_id: str,
) -> dict[str, Any]:
    return _projection_event_values(
        projection,
        correction_binding_set_hash=correction_binding_set_hash,
        causing_request_id=causing_request_id,
        event_type="materialized",
        sequence_number=0,
        predecessor_event_hash=None,
        cause_kind=None,
        cause_id=None,
        cause_hash=None,
    )


def _models(model: type[Any], rows: Iterable[Any]) -> list[Any]:
    return [model(**{field.name: getattr(row, field.name) for field in fields(row)}) for row in rows]


def persist_obligation_projection_graph(
    db: Session, graph: ObligationProjectionGraph,
) -> ADV4CandidateObligationProjection:
    """Write one already-verified graph; the database remains the final arbiter."""
    if type(graph) is not ObligationProjectionGraph:
        raise ObligationIntegrityError("obligation projection graph type differs")
    projection_values = {
        field.name: getattr(graph.projection, field.name)
        for field in fields(graph.projection)
    }
    counts = projection_values.pop("counts")
    if set(counts) != set(_COUNT_COLUMNS):
        raise ObligationIntegrityError("obligation projection count columns differ")
    projection_values.update({
        column: counts[name] for name, column in _COUNT_COLUMNS.items()
    })
    projection = ADV4CandidateObligationProjection(**projection_values)
    db.add(projection)
    db.flush()

    db.add_all(_models(ADV4CandidateObligationSemanticNode, graph.semantic_nodes))
    db.flush()
    db.add_all(_models(ADV4CandidateObligationDatum, graph.datums))
    db.add_all(_models(ADV4CandidateObligationEvidenceLink, graph.evidence_links))

    documents = graph.document_family
    requirements = graph.requirement_family
    expressions = graph.expression_family
    timing = graph.timing_recurrence_family
    relationships = graph.requirement_relationship_family
    groups = graph.recurrence_group_family
    authority = graph.authority_family
    db.add_all(_models(ADV4CandidateObligationDocument, documents.documents))
    db.add_all(_models(
        ADV4CandidateObligationValueAssertion,
        (*documents.value_assertions, *authority.value_assertions),
    ))
    db.add_all(_models(ADV4CandidateObligationRequirement, requirements.requirements))
    db.add_all(_models(ADV4CandidateObligationAction, requirements.actions))
    db.add_all(_models(ADV4CandidateObligationActionStep, requirements.action_steps))
    db.add_all(_models(
        ADV4CandidateObligationActionDocumentRef,
        requirements.action_document_refs,
    ))
    db.add_all(_models(ADV4CandidateObligationBranch, requirements.branches))
    db.add_all(_models(ADV4CandidateObligationExpression, expressions.expressions))
    db.add_all(_models(ADV4CandidateObligationExpressionEdge, expressions.edges))
    db.add_all(_models(
        ADV4CandidateObligationTimingGroup,
        (*timing.timing_groups, *groups.timing_groups),
    ))
    db.add_all(_models(
        ADV4CandidateObligationTimingTerm,
        (*timing.timing_terms, *groups.timing_terms),
    ))
    db.add_all(_models(ADV4CandidateObligationRecurrence, timing.recurrences))
    db.add_all(_models(
        ADV4CandidateObligationTerminatingEffect,
        relationships.terminating_effects,
    ))
    db.add_all(_models(
        ADV4CandidateObligationTerminationEdge,
        relationships.termination_edges,
    ))
    db.add_all(_models(
        ADV4CandidateObligationRequirementDependency,
        relationships.requirement_dependencies,
    ))
    db.add_all(_models(
        ADV4CandidateObligationRecurrenceGroup, groups.recurrence_groups,
    ))
    db.add_all(_models(
        ADV4CandidateObligationRecurrenceGroupMember, groups.members,
    ))
    db.add_all(_models(
        ADV4CandidateObligationAmocProvision, authority.amoc_provisions,
    ))
    db.add_all(_models(
        ADV4CandidateCorrectionSemanticBinding,
        graph.correction_binding_family.bindings,
    ))
    db.flush()
    return projection


def persist_obligation_materialization(
    db: Session,
    graph: ObligationProjectionGraph,
    *,
    actor_user_id: str,
    authorizing_membership_id: str,
    organization_id: str,
    actor_role: str,
    actor_status: str,
    idempotency_key: str,
) -> PersistedObligationMaterialization:
    """Persist a complete graph together with its authorization and root event."""
    if (
        actor_role != "platform_admin"
        or actor_status != "active"
        or any(type(value) is not str or not value for value in (
            actor_user_id, authorizing_membership_id, organization_id,
            idempotency_key,
        ))
    ):
        raise ObligationIntegrityError("obligation materialization authority differs")
    projection = persist_obligation_projection_graph(db, graph)
    request = ADV4CandidateObligationMaterializationRequest(
        **_materialization_request_values(
            projection,
            actor_user_id=actor_user_id,
            authorizing_membership_id=authorizing_membership_id,
            organization_id=organization_id,
            actor_role=actor_role,
            actor_status=actor_status,
            idempotency_key=idempotency_key,
        ),
    )
    db.add(request)
    db.flush()

    event = ADV4CandidateObligationProjectionEvent(
        **_root_event_values(
            projection,
            correction_binding_set_hash=(
                graph.correction_binding_family.binding_set_hash
            ),
            causing_request_id=request.id,
        ),
    )
    db.add(event)
    db.flush()
    return PersistedObligationMaterialization(projection, request, event)


def _require_obligation_application_gate(*, materialize: bool) -> None:
    settings = get_settings()
    if not settings.ad_v4_slice3b_routes_enabled:
        raise ADV4Error(
            "capability_disabled", "",
            "Slice-3B application capability is disabled", http_status=404,
        )
    if materialize and not settings.ad_v4_validator2_writes_enabled:
        raise ADV4Error(
            "validator2_write_gate_disabled", "",
            "Validator-2 application capability is disabled", http_status=409,
        )


def authorize_obligation_audit(
    db: Session, actor: User, membership_id: str,
) -> OrganizationMembership:
    """Recheck read authority and gates without taking locks or writing."""
    _require_obligation_application_gate(materialize=False)
    actor_row = db.get(User, actor.id)
    membership = db.get(OrganizationMembership, membership_id)
    if (
        actor_row is None
        or actor_row.status != "active"
        or membership is None
        or membership.user_id != actor.id
        or membership.status != "active"
        or membership.role != "platform_admin"
    ):
        raise ADV4Error(
            "forbidden", "", "Active platform administrator membership required",
            http_status=403,
        )
    require_v4_database_gate(db, "materializer3a_enabled")
    require_v4_database_gate(db, "materializer3b_enabled")
    return membership


def _new_materialization_request(
    db: Session,
    projection: ADV4CandidateObligationProjection,
    *,
    membership: OrganizationMembership,
    actor: User,
    idempotency_key: str,
) -> ADV4CandidateObligationMaterializationRequest:
    request = ADV4CandidateObligationMaterializationRequest(
        **_materialization_request_values(
            projection,
            actor_user_id=actor.id,
            authorizing_membership_id=membership.id,
            organization_id=membership.organization_id,
            actor_role=membership.role,
            actor_status=membership.status,
            idempotency_key=idempotency_key,
        ),
    )
    db.add(request)
    db.flush([request])
    return request


def _current_obligation_stale_causes(
    db: Session,
    *,
    proposal: ADV4CandidateProposal,
    app_projection: ADV4CandidateAppProjection,
) -> tuple[tuple[str, str, str, str], ...]:
    """Return verified current stale causes sorted by their closed identity."""

    causes: list[tuple[str, str, str, str]] = []
    bindings = db.scalars(
        select(ADV4CandidateEvidenceBinding)
        .where(ADV4CandidateEvidenceBinding.proposal_id == proposal.id)
        .order_by(ADV4CandidateEvidenceBinding.fragment_id)
    ).all()
    for binding in bindings:
        fragment = db.get(ADEvidenceFragment, binding.fragment_id)
        if fragment is None:
            raise ObligationIntegrityError("obligation evidence fragment differs")
        try:
            lifecycle = verified_evidence_lifecycle_events(db, fragment=fragment)
        except ADEvidenceError as exc:
            raise ObligationIntegrityError("obligation evidence lifecycle differs") from exc
        for event in lifecycle[1:]:
            causes.append((
                "evidence_lifecycle_event", event.id, event.event_hash,
                "evidence_invalidated",
            ))

    app_events = db.scalars(
        select(ADV4CandidateAppProjectionEvent)
        .where(
            ADV4CandidateAppProjectionEvent.projection_id == app_projection.id,
            ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
        )
        .order_by(ADV4CandidateAppProjectionEvent.id)
    ).all()
    causes.extend((
        "app_projection_event", event.id, event.event_hash,
        "parent_app_stale",
    ) for event in app_events)

    relationships = db.scalars(
        select(ADV4CandidateSubmissionRelationship)
        .where(
            ADV4CandidateSubmissionRelationship.predecessor_proposal_id
            == proposal.id,
        )
        .order_by(ADV4CandidateSubmissionRelationship.id)
    ).all()
    verified_relationship_ids: set[str] = set()
    for submission_id in sorted({row.submission_id for row in relationships}):
        submission = db.get(ADV4CandidateSubmission, submission_id)
        if submission is None:
            raise ObligationIntegrityError("candidate relationship differs")
        try:
            verified_relationship_ids.update(
                row.id for row in verified_submission(db, submission)
            )
        except ADV4Error as exc:
            raise ObligationIntegrityError("candidate relationship differs") from exc
    for relationship in relationships:
        if relationship.id not in verified_relationship_ids:
            raise ObligationIntegrityError("candidate relationship differs")
        causes.append((
            "candidate_relationship",
            relationship.id,
            relationship.relationship_hash,
            (
                "candidate_corrected"
                if relationship.relation_type == "corrects_candidate"
                else "candidate_replaced"
            ),
        ))
    return tuple(sorted(causes, key=lambda row: (row[0], row[1])))


def _append_obligation_stale_events(
    db: Session,
    *,
    projection: ADV4CandidateObligationProjection,
    request: ADV4CandidateObligationMaterializationRequest,
    causes: Iterable[tuple[str, str, str, str]],
) -> None:
    events = db.scalars(
        select(ADV4CandidateObligationProjectionEvent)
        .where(ADV4CandidateObligationProjectionEvent.projection_id == projection.id)
        .order_by(ADV4CandidateObligationProjectionEvent.sequence_number)
        .with_for_update()
    ).all()
    if not events:
        raise ObligationIntegrityError("projection event root is missing")
    existing_causes = {
        (event.cause_kind, event.cause_id)
        for event in events if event.cause_id is not None
    }
    correction_binding_set_hash = events[0].correction_binding_set_hash
    predecessor_hash = events[-1].event_hash
    sequence_number = events[-1].sequence_number + 1
    new_events: list[ADV4CandidateObligationProjectionEvent] = []
    for cause_kind, cause_id, cause_hash, event_type in causes:
        if (cause_kind, cause_id) in existing_causes:
            continue
        values = _projection_event_values(
            projection,
            correction_binding_set_hash=correction_binding_set_hash,
            causing_request_id=request.id,
            event_type=event_type,
            sequence_number=sequence_number,
            predecessor_event_hash=predecessor_hash,
            cause_kind=cause_kind,
            cause_id=cause_id,
            cause_hash=cause_hash,
        )
        event = ADV4CandidateObligationProjectionEvent(**values)
        db.add(event)
        new_events.append(event)
        existing_causes.add((cause_kind, cause_id))
        predecessor_hash = event.event_hash
        sequence_number += 1
    if new_events:
        db.flush(new_events)


def materialize_obligations(
    db: Session,
    *,
    directive_id: str,
    proposal_id: str,
    app_projection_id: str,
    actor: User,
    membership_id: str,
    idempotency_key: str,
) -> MaterializedObligations:
    """Authorized, gate-checked, idempotent Slice-3B materialization."""
    _require_obligation_application_gate(materialize=True)
    if type(idempotency_key) is not str or not idempotency_key:
        raise ADV4Error(
            "invalid_request", "", "Idempotency key is required", http_status=422,
        )
    membership = _authorization(db, actor, membership_id)
    scope = (
        f"{actor.id}:{membership.id}:{ENDPOINT_ACTION}:"
        f"{POLICY_VERSION}:{idempotency_key}"
    )
    _advisory_lock(db, f"idem:{scope}")
    _advisory_lock(db, f"candidate-relationship-graph:{directive_id}")
    # Lock the immutable candidate before any database gate row. An existing
    # obligation projection is looked up only after the parent locks below.
    proposal = db.scalar(select(ADV4CandidateProposal).where(
        ADV4CandidateProposal.id == proposal_id,
    ).with_for_update())
    if proposal is None or proposal.directive_id != directive_id:
        raise ADV4Error(
            "not_found", "", "Candidate proposal not found", http_status=404,
        )
    require_v4_database_gate(db, "validator2_write_enabled", lock=True)
    require_v4_database_gate(db, "materializer3a_enabled", lock=True)
    require_v4_database_gate(db, "materializer3b_enabled", lock=True)
    proposal = verified_candidate(db, proposal.id)
    if (
        proposal.gate != "candidate_only"
        or proposal.validator_version != VALIDATOR_VERSION_V2
        or proposal.canonicalization_version != CANONICALIZATION_VERSION_V2
    ):
        raise ADV4Error(
            "predecessor_semantic_defect", "",
            "Candidate is not eligible for Slice-3B materialization",
            http_status=422,
        )
    evidence_bindings = db.scalars(
        select(ADV4CandidateEvidenceBinding)
        .where(ADV4CandidateEvidenceBinding.proposal_id == proposal.id)
        .order_by(ADV4CandidateEvidenceBinding.id)
        .with_for_update()
    ).all()
    fragment_ids = sorted({row.fragment_id for row in evidence_bindings})
    if fragment_ids:
        db.scalars(
            select(ADEvidenceFragment)
            .where(ADEvidenceFragment.id.in_(fragment_ids))
            .order_by(ADEvidenceFragment.id)
            .with_for_update()
        ).all()
    _advisory_lock(
        db, f"projection:{proposal_id}:{APP_MATERIALIZER_VERSION}",
    )
    app_projection = db.scalar(select(ADV4CandidateAppProjection).where(
        ADV4CandidateAppProjection.id == app_projection_id,
        ADV4CandidateAppProjection.proposal_id == proposal.id,
        ADV4CandidateAppProjection.directive_id == directive_id,
        ADV4CandidateAppProjection.materializer_version
        == APP_MATERIALIZER_VERSION,
    ).with_for_update())
    if app_projection is None:
        raise ADV4Error(
            "predecessor_semantic_defect", "",
            "Verified Slice-3A projection is required", http_status=422,
        )
    reconstruct_applicability(db, app_projection)
    _repair_stale_projection_on_materialization(db, app_projection)
    db.scalars(select(ADV4CandidateCorrection).where(
        ADV4CandidateCorrection.proposal_id == proposal.id,
    ).order_by(ADV4CandidateCorrection.id).with_for_update()).all()
    db.scalars(select(ADV4CandidateCorrectionRef).where(
        ADV4CandidateCorrectionRef.proposal_id == proposal.id,
    ).order_by(ADV4CandidateCorrectionRef.id).with_for_update()).all()
    _advisory_lock(db, f"projection:{proposal_id}:{MATERIALIZER_VERSION}")

    prior = db.scalar(select(
        ADV4CandidateObligationMaterializationRequest,
    ).where(
        ADV4CandidateObligationMaterializationRequest.actor_user_id == actor.id,
        ADV4CandidateObligationMaterializationRequest.authorizing_membership_id
        == membership.id,
        ADV4CandidateObligationMaterializationRequest.endpoint_action
        == ENDPOINT_ACTION,
        ADV4CandidateObligationMaterializationRequest.auth_policy_version
        == POLICY_VERSION,
        ADV4CandidateObligationMaterializationRequest.idempotency_key
        == idempotency_key,
    ))
    if prior is not None:
        if (
            prior.proposal_id != proposal.id
            or prior.directive_id != directive_id
            or prior.app_projection_id != app_projection.id
        ):
            raise ADV4Error(
                "idempotency_conflict", "",
                "Idempotency key was used for another projection",
                http_status=409,
            )
        existing = db.scalar(select(ADV4CandidateObligationProjection).where(
            ADV4CandidateObligationProjection.id == prior.projection_id,
        ).with_for_update())
        if existing is None:
            raise ADV4Error(
                "projection_integrity", "",
                "Idempotent request lost its projection", http_status=409,
            )
        try:
            reconstruct_obligation_projection(db, existing, require_fresh=False)
        except ObligationIntegrityError as exc:
            raise ADV4Error(
                "projection_integrity", "", str(exc), http_status=409,
            ) from exc
        _append_obligation_stale_events(
            db,
            projection=existing,
            request=prior,
            causes=_current_obligation_stale_causes(
                db, proposal=proposal, app_projection=app_projection,
            ),
        )
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        return MaterializedObligations(existing, prior, False, True)

    existing = db.scalar(select(ADV4CandidateObligationProjection).where(
        ADV4CandidateObligationProjection.proposal_id == proposal.id,
        ADV4CandidateObligationProjection.materializer_version
        == MATERIALIZER_VERSION,
    ).with_for_update())
    if existing is not None:
        try:
            reconstruct_obligation_projection(db, existing, require_fresh=False)
        except ObligationIntegrityError as exc:
            raise ADV4Error(
                "projection_integrity", "", str(exc), http_status=409,
            ) from exc
        request = _new_materialization_request(
            db, existing, membership=membership, actor=actor,
            idempotency_key=idempotency_key,
        )
        _append_obligation_stale_events(
            db,
            projection=existing,
            request=request,
            causes=_current_obligation_stale_causes(
                db, proposal=proposal, app_projection=app_projection,
            ),
        )
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        return MaterializedObligations(existing, request, False, False)

    try:
        _verify_live_evidence(db, proposal)
        state, reasons = projection_state(db, app_projection)
    except ADV4Error as exc:
        raise ADV4Error(
            "predecessor_semantic_defect", "",
            "A fresh verified Slice-3A parent is required",
            http_status=422,
        ) from exc
    if state != "candidate_verified":
        raise ADV4Error(
            "predecessor_semantic_defect", "",
            f"Slice-3A projection is stale: {','.join(reasons)}",
            http_status=422,
        )
    graph = _build_obligation_graph_from_verified_parents(
        db, proposal=proposal, app_projection=app_projection,
    )
    persisted = persist_obligation_materialization(
        db, graph,
        actor_user_id=actor.id,
        authorizing_membership_id=membership.id,
        organization_id=membership.organization_id,
        actor_role=membership.role,
        actor_status=membership.status,
        idempotency_key=idempotency_key,
    )
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    return MaterializedObligations(
        persisted.projection, persisted.request, True, False,
    )


def _require_exact_values(
    actual: Any, expected: Any, names: Iterable[str], *, label: str,
) -> None:
    for name in names:
        actual_value = getattr(actual, name)
        expected_value = getattr(expected, name)
        if (
            type(actual_value) is not type(expected_value)
            or actual_value != expected_value
        ):
            raise ObligationIntegrityError(f"{label} differs")


def _require_exact_rows(
    db: Session,
    *,
    projection_id: str,
    model: type[Any],
    expected_rows: Iterable[Any],
    label: str,
    projection_column: str = "projection_id",
) -> None:
    expected = tuple(expected_rows)
    actual = tuple(db.scalars(select(model).where(
        getattr(model, projection_column) == projection_id,
    )).all())
    if len(actual) != len(expected):
        raise ObligationIntegrityError(f"{label} count differs")
    if not expected:
        return
    names = tuple(field.name for field in fields(expected[0]))
    key_name = "id" if "id" in names else "semantic_node_id"
    expected_by_key = {getattr(row, key_name): row for row in expected}
    actual_by_key = {getattr(row, key_name): row for row in actual}
    if (
        len(expected_by_key) != len(expected)
        or len(actual_by_key) != len(actual)
        or set(actual_by_key) != set(expected_by_key)
    ):
        raise ObligationIntegrityError(f"{label} identity set differs")
    for key, expected_row in expected_by_key.items():
        _require_exact_values(
            actual_by_key[key], expected_row, names, label=label,
        )


def _build_obligation_graph_from_verified_parents(
    db: Session, *, proposal: Any, app_projection: ADV4CandidateAppProjection,
) -> ObligationProjectionGraph:
    app_nodes = db.scalars(select(ADV4CandidateAppSemanticNode).where(
        ADV4CandidateAppSemanticNode.projection_id == app_projection.id,
        ADV4CandidateAppSemanticNode.node_type.in_((
            "product_scope", "condition", "applicability_rule",
        )),
    )).all()
    app_targets = tuple(ObligationApplicabilityTarget(
        id=node.id,
        identity_hash=node.identity_hash,
        proposal_id=node.proposal_id,
        projection_id=node.projection_id,
        node_type=node.node_type,
        node_key=node.node_key,
        source_pointer=node.source_pointer,
        canonical_node_bytes=canonical_bytes(
            _node_value(proposal.parsed_json, node.source_pointer),
            CANONICALIZATION_VERSION_V2,
        ),
        canonical_node_hash=node.canonical_node_hash,
    ) for node in app_nodes)
    evidence_bindings = {
        row.evidence_key: row.id
        for row in db.scalars(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == proposal.id,
        )).all()
    }
    expected_refs = build_correction_reference_snapshot(
        proposal_id=proposal.id,
        canonical_corrections=proposal.parsed_json["authoritativeCorrections"],
    )
    refs_by_id = {
        row.id: row
        for row in db.scalars(select(ADV4CandidateCorrectionRef).where(
            ADV4CandidateCorrectionRef.proposal_id == proposal.id,
        )).all()
    }
    ordered_ref_ids = [row.id for row in expected_refs]
    if set(refs_by_id) != set(ordered_ref_ids):
        raise ObligationIntegrityError("correction reference identity set differs")
    foundation_refs = tuple(ObligationCorrectionReference(
        id=refs_by_id[row_id].id,
        correction_id=refs_by_id[row_id].correction_id,
        proposal_id=refs_by_id[row_id].proposal_id,
        canonical_ordinal=refs_by_id[row_id].canonical_ordinal,
        namespace=refs_by_id[row_id].namespace,
        semantic_key=refs_by_id[row_id].semantic_key,
        owner_slice=refs_by_id[row_id].owner_slice,
        reference_hash=refs_by_id[row_id].reference_hash,
    ) for row_id in ordered_ref_ids)
    return materialize_obligation_projection_graph(
        proposal_id=proposal.id,
        directive_id=proposal.directive_id,
        proposal_canonical_hash=proposal.canonical_hash,
        evidence_binding_hash=proposal.evidence_binding_hash,
        app_projection_id=app_projection.id,
        app_projection_hash=app_projection.projection_hash,
        canonical_proposal=proposal.parsed_json,
        evidence_bindings=evidence_bindings,
        app_targets=app_targets,
        foundation_refs=foundation_refs,
    )


def _expected_obligation_graph(
    db: Session, projection: ADV4CandidateObligationProjection,
) -> ObligationProjectionGraph:
    proposal = verified_candidate(db, projection.proposal_id)
    app_projection = db.get(ADV4CandidateAppProjection, projection.app_projection_id)
    if (
        app_projection is None
        or app_projection.proposal_id != proposal.id
        or app_projection.directive_id != proposal.directive_id
    ):
        raise ObligationIntegrityError("obligation parent applicability differs")
    reconstruct_applicability(db, app_projection)
    return _build_obligation_graph_from_verified_parents(
        db, proposal=proposal, app_projection=app_projection,
    )


def reconstruct_obligation_projection(
    db: Session,
    projection: ADV4CandidateObligationProjection,
    *,
    require_fresh: bool = True,
) -> dict[str, Any]:
    """Rebuild and verify the complete Slice-3B graph without mutating state."""
    expected = _expected_obligation_graph(db, projection)
    projection_names = tuple(
        field.name for field in fields(expected.projection)
        if field.name != "counts"
    )
    _require_exact_values(
        projection, expected.projection, projection_names,
        label="obligation projection",
    )
    actual_counts = {
        name: getattr(projection, column)
        for name, column in _COUNT_COLUMNS.items()
    }
    if (
        any(type(value) is not int for value in actual_counts.values())
        or actual_counts != dict(expected.projection.counts)
    ):
        raise ObligationIntegrityError("obligation projection counts differ")

    documents = expected.document_family
    requirements = expected.requirement_family
    expressions = expected.expression_family
    timing = expected.timing_recurrence_family
    relationships = expected.requirement_relationship_family
    groups = expected.recurrence_group_family
    authority = expected.authority_family
    row_sets = (
        (ADV4CandidateObligationSemanticNode, expected.semantic_nodes, "semantic nodes"),
        (ADV4CandidateObligationDatum, expected.datums, "generic data"),
        (ADV4CandidateObligationEvidenceLink, expected.evidence_links, "evidence links"),
        (ADV4CandidateObligationDocument, documents.documents, "document owners"),
        (
            ADV4CandidateObligationValueAssertion,
            (*documents.value_assertions, *authority.value_assertions),
            "value-assertion owners",
        ),
        (ADV4CandidateObligationRequirement, requirements.requirements, "requirement owners"),
        (ADV4CandidateObligationAction, requirements.actions, "action owners"),
        (ADV4CandidateObligationActionStep, requirements.action_steps, "action-step owners"),
        (
            ADV4CandidateObligationActionDocumentRef,
            requirements.action_document_refs,
            "action-document references",
        ),
        (ADV4CandidateObligationBranch, requirements.branches, "branch owners"),
        (ADV4CandidateObligationExpression, expressions.expressions, "expression owners"),
        (ADV4CandidateObligationExpressionEdge, expressions.edges, "expression edges"),
        (
            ADV4CandidateObligationTimingGroup,
            (*timing.timing_groups, *groups.timing_groups),
            "timing-group owners",
        ),
        (
            ADV4CandidateObligationTimingTerm,
            (*timing.timing_terms, *groups.timing_terms),
            "timing-term owners",
        ),
        (ADV4CandidateObligationRecurrence, timing.recurrences, "recurrence owners"),
        (
            ADV4CandidateObligationTerminatingEffect,
            relationships.terminating_effects,
            "terminating-effect owners",
        ),
        (
            ADV4CandidateObligationTerminationEdge,
            relationships.termination_edges,
            "termination edges",
        ),
        (
            ADV4CandidateObligationRequirementDependency,
            relationships.requirement_dependencies,
            "requirement dependencies",
        ),
        (
            ADV4CandidateObligationRecurrenceGroup,
            groups.recurrence_groups,
            "recurrence-group owners",
        ),
        (
            ADV4CandidateObligationRecurrenceGroupMember,
            groups.members,
            "recurrence-group members",
        ),
        (
            ADV4CandidateObligationAmocProvision,
            authority.amoc_provisions,
            "AMOC-provision owners",
        ),
    )
    for model, expected_rows, label in row_sets:
        _require_exact_rows(
            db, projection_id=projection.id, model=model,
            expected_rows=expected_rows, label=label,
        )
    _require_exact_rows(
        db,
        projection_id=projection.id,
        model=ADV4CandidateCorrectionSemanticBinding,
        expected_rows=expected.correction_binding_family.bindings,
        label="correction bindings",
        projection_column="obligation_projection_id",
    )

    requests = db.scalars(select(
        ADV4CandidateObligationMaterializationRequest,
    ).where(
        ADV4CandidateObligationMaterializationRequest.projection_id
        == projection.id,
    )).all()
    if not requests:
        raise ObligationIntegrityError("materialization request is missing")
    requests_by_id = {request.id: request for request in requests}
    if len(requests_by_id) != len(requests):
        raise ObligationIntegrityError("materialization request identity differs")
    for request in requests:
        actor = db.get(User, request.actor_user_id)
        membership = db.get(
            OrganizationMembership, request.authorizing_membership_id,
        )
        if (
            actor is None
            or actor.status != "active"
            or membership is None
            or membership.user_id != request.actor_user_id
            or membership.organization_id != request.organization_id
            or membership.role != request.actor_role
            or membership.status != request.actor_status
        ):
            raise ObligationIntegrityError("materialization authority differs")
        expected_request = _materialization_request_values(
            projection,
            actor_user_id=request.actor_user_id,
            authorizing_membership_id=request.authorizing_membership_id,
            organization_id=request.organization_id,
            actor_role=request.actor_role,
            actor_status=request.actor_status,
            idempotency_key=request.idempotency_key,
        )
        for name, value in expected_request.items():
            actual_value = getattr(request, name)
            if type(actual_value) is not type(value) or actual_value != value:
                raise ObligationIntegrityError("materialization request differs")

    events = db.scalars(select(
        ADV4CandidateObligationProjectionEvent,
    ).where(
        ADV4CandidateObligationProjectionEvent.projection_id == projection.id,
    ).order_by(
        ADV4CandidateObligationProjectionEvent.sequence_number,
    )).all()
    if not events or [row.sequence_number for row in events] != list(
        range(len(events))
    ):
        raise ObligationIntegrityError("projection event sequence differs")
    for index, event in enumerate(events):
        predecessor = None if index == 0 else events[index - 1].event_hash
        if event.predecessor_event_hash != predecessor:
            raise ObligationIntegrityError("projection event predecessor differs")
        if event.causing_request_id not in requests_by_id:
            raise ObligationIntegrityError("projection event request differs")
        if index == 0:
            if (
                event.event_type != "materialized"
                or event.cause_kind is not None
                or event.cause_id is not None
                or event.cause_hash is not None
            ):
                raise ObligationIntegrityError("projection root event differs")
        else:
            expected_cause_kind = {
                "evidence_invalidated": "evidence_lifecycle_event",
                "parent_app_stale": "app_projection_event",
                "candidate_corrected": "candidate_relationship",
                "candidate_replaced": "candidate_relationship",
            }.get(event.event_type)
            if (
                expected_cause_kind is None
                or event.cause_kind != expected_cause_kind
                or event.cause_id is None
                or event.cause_hash is None
            ):
                raise ObligationIntegrityError("projection event cause differs")
            if event.cause_kind == "evidence_lifecycle_event":
                cause = db.get(ADEvidenceFragmentLifecycleEvent, event.cause_id)
                bound_fragment_ids = db.scalars(select(
                    ADV4CandidateEvidenceBinding.fragment_id,
                ).where(
                    ADV4CandidateEvidenceBinding.proposal_id
                    == projection.proposal_id,
                )).all()
                fragment = (
                    None if cause is None
                    else db.get(ADEvidenceFragment, cause.fragment_id)
                )
                try:
                    lifecycle = (
                        [] if fragment is None
                        else verified_evidence_lifecycle_events(
                            db, fragment=fragment,
                        )
                    )
                except ADEvidenceError:
                    lifecycle = []
                valid_cause = (
                    cause is not None
                    and cause in lifecycle
                    and cause.event_type in {"superseded", "quarantined"}
                    and cause.fragment_id in set(bound_fragment_ids)
                    and cause.event_hash == event.cause_hash
                )
            elif event.cause_kind == "app_projection_event":
                cause = db.get(ADV4CandidateAppProjectionEvent, event.cause_id)
                valid_cause = (
                    cause is not None
                    and cause.projection_id == projection.app_projection_id
                    and cause.event_type == "stale_marked"
                    and cause.event_hash == event.cause_hash
                )
            else:
                cause = db.get(ADV4CandidateSubmissionRelationship, event.cause_id)
                expected_relation = (
                    "corrects_candidate"
                    if event.event_type == "candidate_corrected"
                    else "replaces_candidate"
                )
                submission = (
                    None if cause is None
                    else db.get(ADV4CandidateSubmission, cause.submission_id)
                )
                try:
                    relationships = (
                        [] if submission is None
                        else verified_submission(db, submission)
                    )
                except ADV4Error:
                    relationships = []
                valid_cause = (
                    cause is not None
                    and cause in relationships
                    and cause.predecessor_proposal_id == projection.proposal_id
                    and cause.relation_type == expected_relation
                    and cause.relationship_hash == event.cause_hash
                )
            if not valid_cause:
                raise ObligationIntegrityError("projection event cause differs")
        expected_event = _projection_event_values(
            projection,
            correction_binding_set_hash=(
                expected.correction_binding_family.binding_set_hash
            ),
            causing_request_id=event.causing_request_id,
            event_type=event.event_type,
            sequence_number=event.sequence_number,
            predecessor_event_hash=event.predecessor_event_hash,
            cause_kind=event.cause_kind,
            cause_id=event.cause_id,
            cause_hash=event.cause_hash,
        )
        for name, value in expected_event.items():
            actual_value = getattr(event, name)
            if type(actual_value) is not type(value) or actual_value != value:
                raise ObligationIntegrityError("projection event differs")

    try:
        subtree = json.loads(
            expected.projection.obligation_subtree_bytes.decode("utf-8"),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ObligationIntegrityError(
            "obligation subtree bytes are invalid",
        ) from exc
    if not isinstance(subtree, dict):
        raise ObligationIntegrityError("obligation subtree root differs")
    if require_fresh:
        proposal = db.get(ADV4CandidateProposal, projection.proposal_id)
        app_projection = db.get(
            ADV4CandidateAppProjection, projection.app_projection_id,
        )
        if proposal is None or app_projection is None:
            raise ObligationIntegrityError(
                "obligation parent applicability differs",
            )
        try:
            _verify_live_evidence(db, proposal, lock=False)
            state, reasons = projection_state(db, app_projection)
        except ADV4Error as exc:
            raise ObligationIntegrityError("obligation evidence differs") from exc
        if state != "candidate_verified":
            raise ObligationIntegrityError(
                f"obligation parent applicability is stale: {','.join(reasons)}"
            )
    return subtree


def obligation_projection_counts(
    projection: ADV4CandidateObligationProjection,
) -> dict[str, int]:
    counts = {
        name: getattr(projection, column)
        for name, column in _COUNT_COLUMNS.items()
    }
    if any(type(value) is not int for value in counts.values()):
        raise ObligationIntegrityError("obligation projection counts differ")
    return counts


def verified_obligation_projection(
    db: Session, *, directive_id: str, proposal_id: str,
) -> ADV4CandidateObligationProjection:
    projection = db.scalar(select(ADV4CandidateObligationProjection).where(
        ADV4CandidateObligationProjection.directive_id == directive_id,
        ADV4CandidateObligationProjection.proposal_id == proposal_id,
        ADV4CandidateObligationProjection.materializer_version
        == MATERIALIZER_VERSION,
    ))
    if projection is None:
        raise ADV4Error(
            "not_found", "", "Obligation projection not found", http_status=404,
        )
    try:
        reconstruct_obligation_projection(db, projection)
    except ObligationIntegrityError as exc:
        raise ADV4Error(
            "projection_integrity", "", str(exc), http_status=409,
        ) from exc
    return projection
