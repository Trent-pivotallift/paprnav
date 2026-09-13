from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.routes.admin import ensure_platform_admin
from app.api.routes.aircraft import (
    ensure_maintenance_review_access,
    get_visible_aircraft_or_404,
)
from app.core.config import get_settings
from app.db.session import get_db, repeatable_read_only_session
from app.models.core import (
    ADDiscoveryRecord,
    ADCoverageSet,
    ADCoverageSubscription,
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    ADPublication,
    ADSourceDocument,
    ADMatchAdjudication,
    ADMatchDueStateLink,
    ADMatchEvidence,
    ADMatchResult,
    ADTargetApplicability,
    ADV4CandidateProposal,
    ADV4CandidateAppMaterializationRequest,
    ADV4CandidateAppProjection,
    ADV4CandidateObligationMaterializationRequest,
    ADV4CandidateObligationProjection,
    ADV4CandidateSubmission,
    AircraftADDueState,
    AirworthinessDirective,
    ApplicabilityTarget,
    LogbookEntry,
    ProductEvent,
    User,
)
from app.schemas.ads import (
    ADDiscoveryRecordResponse,
    ADExtractionResponse,
    ADExtractionReviewListResponse,
    ADExtractionReviewResponse,
    ADEvidenceFragmentCreateRequest,
    ADEvidenceFragmentResponse,
    ADV4CandidateListResponse,
    ADV4CandidateResponse,
    ADV4ApplicabilityProjectionListResponse,
    ADV4ApplicabilityProjectionResponse,
    ADV4ApplicabilityReconstructionResponse,
    ADV4ObligationMaterializationRequest,
    ADV4ObligationProjectionListResponse,
    ADV4ObligationProjectionResponse,
    ADV4ObligationReconstructionResponse,
    ADV4SubmissionAuditResponse,
    ADV4SubmissionRelationshipAuditResponse,
    ADProposalProvenanceResponse,
    ADSourcePageEvidenceResponse,
    ADSourcePageMaterializeRequest,
    ADSourceDocumentResponse,
    ADMatchAdjudicationResponse,
    ADMatchAdjudicationDecisionRequest,
    ADMatchAdjudicationDecisionResponse,
    ADMatchApplicabilityResponse,
    ADMatchComponentResponse,
    ADMatchEvidenceResponse,
    ADMatchResultListResponse,
    ADMatchResultResponse,
    ADMatchPublicationResponse,
    ADMatchTargetResponse,
    ADDueStateResponse,
    ADReviewDecisionRequest,
    ADReviewDecisionResponse,
    ADDirectiveApplicabilityTargetResponse,
    AirworthinessDirectiveResponse,
)
from app.services.ad_extraction import (
    bounded_source_document_pages,
    derive_compliance_action_summaries,
    ensure_persisted_source_pages,
    extraction_approval_blockers,
    extraction_input_hash,
    official_ad_number,
    persisted_source_pages,
    source_evidence_status,
    structured_output_hash,
    retained_document_bytes_match,
    verified_retained_document_bytes,
)
from app.services.ad_applicability import populate_applicability_from_extraction
from app.services.ad_coverage import summarize_aircraft_coverage_status
from app.services.ad_coverage import resolve_aircraft_ad_coverage
from app.services.ad_matching import (
    ALGORITHM_NAME,
    ALGORITHM_VERSION,
    invalidate_aircraft_match_results,
)
from app.services.ad_recurrence import materialize_requirements_from_extraction
from app.services.ad_release import (
    extraction_has_signed_release,
    released_extraction_for_directive,
    released_signed_extractions,
)
from app.services.ad_extraction import full_text_pages_for_extraction
from app.services.ad_evidence import (
    ADEvidenceError,
    admit_evidence_fragment,
    get_materialized_source_page,
    materialize_source_page,
)
from app.services.ad_v4_candidates import (
    ADV4Error,
    MAX_REQUEST_BYTES,
    parse_v4_request_bytes,
    store_v4_candidate,
    verified_candidate,
    verified_submission,
)
from app.services.ad_v4_applicability import (
    POLICY_VERSION as APP_PROJECTION_POLICY_VERSION,
    authorize_projection_audit,
    materialize_applicability,
    projection_state,
    reconstruct_applicability,
    verified_app_projection,
)
from app.services.ad_v4_obligation_persistence import (
    POLICY_VERSION as OBLIGATION_PROJECTION_POLICY_VERSION,
    authorize_obligation_audit,
    materialize_obligations,
    obligation_projection_counts,
    reconstruct_obligation_projection,
    verified_obligation_projection,
)
from app.services.ad_v4_obligations import ObligationIntegrityError
from app.services.ad_recurrence import due_state_payload
from app.services.installed_components import component_display_name
from app.services.observability import record_product_event, record_workflow_status
from app.services.storage import safe_filename

router = APIRouter(prefix="/api/v1/ads", tags=["airworthiness-directives"])


def ensure_ad_extraction_reviewer(user: User) -> None:
    ensure_platform_admin(user)


def is_platform_admin(user: User) -> bool:
    return any(
        membership.status == "active" and membership.role == "platform_admin"
        for membership in user.memberships
    )


@router.get("/source-documents/{source_document_id}/content")
def open_retained_source_document(
    source_document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_ad_extraction_reviewer(current_user)
    document = db.scalar(
        select(ADSourceDocument).where(ADSourceDocument.id == source_document_id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retained AD source document not found")
    filename = safe_filename(Path(document.storage_key).name or f"{document.id}.pdf")
    headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"}
    settings = get_settings()
    try:
        payload = verified_retained_document_bytes(document, settings=settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Retained AD source document hash mismatch",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retained AD source document not found") from exc
    return Response(
        content=payload,
        media_type=document.media_type or "application/octet-stream",
        headers=headers,
    )


def evidence_http_error(exc: ADEvidenceError) -> HTTPException:
    if exc.code in {"not_found", "page_not_materialized"}:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if exc.code == "source_unavailable":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if exc.code in {
        "source_hash_mismatch", "rendition_hash_mismatch", "page_text_hash_mismatch",
        "fragment_not_admitted",
    }:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))


def v4_http_error(exc: ADV4Error) -> HTTPException:
    return HTTPException(
        status_code=exc.http_status,
        detail={"code": exc.code, "jsonPointer": exc.pointer, "message": str(exc)},
    )


def _obligation_database_error(exc: DBAPIError) -> ADV4Error | None:
    sqlstate = getattr(exc.orig, "sqlstate", None)
    if sqlstate == "P0001" or (
        isinstance(sqlstate, str) and sqlstate.startswith("23")
    ):
        return ADV4Error(
            "projection_integrity", "",
            "PostgreSQL rejected the obligation projection transaction",
            http_status=409,
        )
    if sqlstate in {"40P01", "40001", "57014", "55P03"}:
        return ADV4Error(
            "transaction_conflict", "",
            "Obligation projection transaction must be retried",
            http_status=409,
        )
    return None


def serialize_v4_candidate(
    proposal: ADV4CandidateProposal,
    submission: ADV4CandidateSubmission,
    *,
    db: Session | None = None,
    content_reused: bool = False,
    idempotent_retry: bool = False,
    submission_limit: int = 25,
    submission_offset: int = 0,
) -> ADV4CandidateResponse:
    submission_rows = [submission]
    submission_count = 1
    if db is not None:
        submission_count = db.scalar(
            select(func.count()).select_from(ADV4CandidateSubmission)
            .where(ADV4CandidateSubmission.proposal_id == proposal.id)
        ) or 0
        submission_rows = db.scalars(
            select(ADV4CandidateSubmission)
            .where(ADV4CandidateSubmission.proposal_id == proposal.id)
            .order_by(ADV4CandidateSubmission.created_at, ADV4CandidateSubmission.id)
            .offset(submission_offset)
            .limit(submission_limit)
        ).all()
    audits = []
    for row in submission_rows:
        relationships = verified_submission(db, row) if db is not None else []
        audits.append(ADV4SubmissionAuditResponse(
            submissionId=row.id,
            actorUserId=row.actor_user_id,
            authorizingMembershipId=row.authorizing_membership_id,
            organizationId=row.organization_id,
            actorRole=row.actor_role,
            actorStatus=row.actor_status,
            authPolicyName=row.auth_policy_name,
            authPolicyVersion=row.auth_policy_version,
            authClaimsHash=row.auth_claims_hash,
            endpointAction=row.endpoint_action,
            idempotencyKey=row.idempotency_key,
            requestHash=row.request_hash,
            rawTransportHash=row.raw_transport_hash,
            relationships=[ADV4SubmissionRelationshipAuditResponse(
                relationshipKey=relationship.relationship_key,
                relationType=relationship.relation_type,
                predecessorProposalId=relationship.predecessor_proposal_id,
                reason=relationship.reason,
                evidenceKeys=relationship.evidence_keys,
                relationshipHash=relationship.relationship_hash,
                createdAt=relationship.created_at,
            ) for relationship in relationships],
            createdAt=row.created_at,
        ))
    return ADV4CandidateResponse(
        proposalId=proposal.id,
        submissionId=submission.id,
        directiveId=proposal.directive_id,
        schemaVersion=proposal.schema_version,
        canonicalizationVersion=proposal.canonicalization_version,
        validatorVersion=proposal.validator_version,
        canonicalHash=proposal.canonical_hash,
        evidenceBindingHash=proposal.evidence_binding_hash,
        bindingCount=proposal.binding_count,
        gate=proposal.gate,
        contentReused=content_reused,
        idempotentRetry=idempotent_retry,
        canonicalProposal=proposal.parsed_json,
        submissions=audits,
        submissionCount=submission_count,
        submissionLimit=submission_limit,
        submissionOffset=submission_offset,
        createdAt=proposal.created_at,
    )


async def bounded_v4_request_bytes(request: Request) -> bytes:
    payload = bytearray()
    async for chunk in request.stream():
        payload.extend(chunk)
        if len(payload) > MAX_REQUEST_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="V4 request body exceeds the byte limit",
            )
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="V4 request body is empty",
        )
    return bytes(payload)


@router.post(
    "/directives/{directive_id}/v4/candidate-proposals",
    response_model=ADV4CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_v4_candidate_proposal(
    directive_id: str,
    request: Request,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=255),
    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4CandidateResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json" or request.headers.get("content-encoding", "identity") not in {"", "identity"}:
        raise HTTPException(status_code=415, detail="Strict application/json without content encoding is required")
    length = request.headers.get("content-length")
    if length is not None:
        try:
            if int(length) < 1 or int(length) > MAX_REQUEST_BYTES:
                raise ValueError
        except ValueError as exc:
            raise HTTPException(status_code=413, detail="V4 request body exceeds the byte limit") from exc
    raw = await bounded_v4_request_bytes(request)
    try:
        parsed = parse_v4_request_bytes(raw)
        stored = store_v4_candidate(
            db,
            directive_id=directive_id,
            parsed=parsed,
            actor=current_user,
            membership_id=acting_membership_id,
            idempotency_key=idempotency_key,
        )
        db.commit()
        db.refresh(stored.proposal)
        db.refresh(stored.submission)
    except ADV4Error as exc:
        db.rollback()
        raise v4_http_error(exc) from exc
    if stored.idempotent_retry or stored.content_reused:
        response.status_code = status.HTTP_200_OK
    return serialize_v4_candidate(
        stored.proposal,
        stored.submission,
        db=db,
        content_reused=stored.content_reused,
        idempotent_retry=stored.idempotent_retry,
    )


@router.get(
    "/directives/{directive_id}/v4/candidate-proposals",
    response_model=ADV4CandidateListResponse,
)
def list_v4_candidate_proposals(
    directive_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    submission_limit: int = Query(default=25, ge=1, le=100, alias="submissionLimit"),
    submission_offset: int = Query(default=0, ge=0, alias="submissionOffset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4CandidateListResponse:
    ensure_platform_admin(current_user)
    total = db.scalar(
        select(func.count()).select_from(ADV4CandidateProposal)
        .where(ADV4CandidateProposal.directive_id == directive_id)
    ) or 0
    proposals = db.scalars(
        select(ADV4CandidateProposal)
        .where(ADV4CandidateProposal.directive_id == directive_id)
        .order_by(ADV4CandidateProposal.created_at.desc(), ADV4CandidateProposal.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    responses = []
    for proposal in proposals:
        proposal = verified_candidate(db, proposal.id)
        submission = db.scalar(
            select(ADV4CandidateSubmission)
            .where(ADV4CandidateSubmission.proposal_id == proposal.id)
            .order_by(ADV4CandidateSubmission.created_at.desc())
        )
        if submission is None:
            raise v4_http_error(ADV4Error("candidate_integrity", "", "Candidate has no submission", http_status=409))
        try:
            responses.append(serialize_v4_candidate(
                proposal, submission, db=db,
                submission_limit=submission_limit, submission_offset=submission_offset,
            ))
        except ADV4Error as exc:
            raise v4_http_error(exc) from exc
    return ADV4CandidateListResponse(
        candidates=responses, count=len(responses), total=total, limit=limit, offset=offset,
    )


@router.get(
    "/v4/candidate-proposals/{proposal_id}",
    response_model=ADV4CandidateResponse,
)
def get_v4_candidate_proposal(
    proposal_id: str,
    submission_limit: int = Query(default=25, ge=1, le=100, alias="submissionLimit"),
    submission_offset: int = Query(default=0, ge=0, alias="submissionOffset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4CandidateResponse:
    ensure_platform_admin(current_user)
    try:
        proposal = verified_candidate(db, proposal_id)
    except ADV4Error as exc:
        raise v4_http_error(exc) from exc
    submission = db.scalar(
        select(ADV4CandidateSubmission)
        .where(ADV4CandidateSubmission.proposal_id == proposal.id)
        .order_by(ADV4CandidateSubmission.created_at.desc())
    )
    if submission is None:
        raise v4_http_error(ADV4Error("candidate_integrity", "", "Candidate has no submission", http_status=409))
    try:
        return serialize_v4_candidate(
            proposal, submission, db=db,
            submission_limit=submission_limit, submission_offset=submission_offset,
        )
    except ADV4Error as exc:
        raise v4_http_error(exc) from exc


def serialize_v4_app_projection(
    db: Session,
    projection: ADV4CandidateAppProjection,
    *,
    acting_membership_id: str,
    request_row: ADV4CandidateAppMaterializationRequest | None = None,
    created: bool = False,
    idempotent_retry: bool = False,
) -> ADV4ApplicabilityProjectionResponse:
    # Every audit representation is verified against the complete typed graph;
    # list responses must not be a weaker integrity path than detail/readback.
    reconstruct_applicability(db, projection)
    state_value, reasons = projection_state(db, projection)
    return ADV4ApplicabilityProjectionResponse(
        projectionId=projection.id,
        proposalId=projection.proposal_id,
        directiveId=projection.directive_id,
        validatorVersion=projection.validator_version,
        canonicalizationVersion=projection.canonicalization_version,
        materializerVersion=projection.materializer_version,
        proposalCanonicalHash=projection.proposal_canonical_hash,
        evidenceBindingHash=projection.evidence_binding_hash,
        applicabilitySubtreeHash=projection.applicability_subtree_hash,
        projectionHash=projection.projection_hash,
        gate=projection.gate,
        projectionState=state_value,
        stateReasons=reasons,
        semanticNodeCount=projection.semantic_node_count,
        datumCount=projection.datum_count,
        evidenceLinkCount=projection.evidence_link_count,
        identityMappingCount=projection.identity_mapping_count,
        requestId=request_row.id if request_row else None,
        created=created,
        idempotentRetry=idempotent_retry,
        actingMembershipId=acting_membership_id,
        authPolicyVersion=APP_PROJECTION_POLICY_VERSION,
        createdAt=projection.created_at,
    )


@router.post(
    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection",
    response_model=ADV4ApplicabilityProjectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_v4_applicability_projection(
    directive_id: str,
    proposal_id: str,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=255),
    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4ApplicabilityProjectionResponse:
    try:
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=current_user, membership_id=acting_membership_id,
            idempotency_key=idempotency_key,
        )
        db.commit()
        db.refresh(result.projection)
        db.refresh(result.request)
        if not result.created:
            response.status_code = status.HTTP_200_OK
        return serialize_v4_app_projection(
            db, result.projection, acting_membership_id=acting_membership_id,
            request_row=result.request, created=result.created,
            idempotent_retry=result.idempotent_retry,
        )
    except ADV4Error as exc:
        db.rollback()
        raise v4_http_error(exc) from exc


@router.get(
    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection",
    response_model=ADV4ApplicabilityProjectionResponse,
)
def get_v4_applicability_projection(
    directive_id: str,
    proposal_id: str,
    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4ApplicabilityProjectionResponse:
    try:
        authorize_projection_audit(db, current_user, acting_membership_id)
        projection = verified_app_projection(db, directive_id=directive_id, proposal_id=proposal_id)
        return serialize_v4_app_projection(db, projection, acting_membership_id=acting_membership_id)
    except ADV4Error as exc:
        db.rollback()
        raise v4_http_error(exc) from exc


@router.get(
    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection/reconstruction",
    response_model=ADV4ApplicabilityReconstructionResponse,
)
def get_v4_applicability_reconstruction(
    directive_id: str,
    proposal_id: str,
    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4ApplicabilityReconstructionResponse:
    try:
        authorize_projection_audit(db, current_user, acting_membership_id)
        projection = verified_app_projection(db, directive_id=directive_id, proposal_id=proposal_id)
        subtree = reconstruct_applicability(db, projection)
        return ADV4ApplicabilityReconstructionResponse(
            projectionId=projection.id, proposalId=projection.proposal_id,
            directiveId=projection.directive_id, gate=projection.gate,
            applicabilitySubtreeHash=projection.applicability_subtree_hash,
            projectionHash=projection.projection_hash,
            canonicalApplicability=subtree,
            actingMembershipId=acting_membership_id,
            authPolicyVersion=APP_PROJECTION_POLICY_VERSION,
        )
    except ADV4Error as exc:
        db.rollback()
        raise v4_http_error(exc) from exc


@router.get(
    "/directives/{directive_id}/v4/applicability-projections",
    response_model=ADV4ApplicabilityProjectionListResponse,
)
def list_v4_applicability_projections(
    directive_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    acting_membership_id: str = Header(alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4ApplicabilityProjectionListResponse:
    try:
        authorize_projection_audit(db, current_user, acting_membership_id)
        total = db.scalar(select(func.count()).select_from(ADV4CandidateAppProjection).where(ADV4CandidateAppProjection.directive_id == directive_id)) or 0
        rows = db.scalars(select(ADV4CandidateAppProjection).where(ADV4CandidateAppProjection.directive_id == directive_id).order_by(ADV4CandidateAppProjection.created_at.desc(), ADV4CandidateAppProjection.id.desc()).offset(offset).limit(limit)).all()
        responses = [serialize_v4_app_projection(db, row, acting_membership_id=acting_membership_id) for row in rows]
        return ADV4ApplicabilityProjectionListResponse(projections=responses, count=len(responses), total=total, limit=limit, offset=offset)
    except ADV4Error as exc:
        db.rollback()
        raise v4_http_error(exc) from exc


def serialize_v4_obligation_projection(
    db: Session,
    projection: ADV4CandidateObligationProjection,
    *,
    acting_membership_id: str,
    request_row: ADV4CandidateObligationMaterializationRequest | None = None,
    created: bool = False,
    idempotent_retry: bool = False,
    require_fresh: bool = True,
) -> ADV4ObligationProjectionResponse:
    reconstruct_obligation_projection(
        db, projection, require_fresh=require_fresh,
    )
    return ADV4ObligationProjectionResponse(
        projectionId=projection.id,
        proposalId=projection.proposal_id,
        directiveId=projection.directive_id,
        appProjectionId=projection.app_projection_id,
        validatorVersion=projection.validator_version,
        canonicalizationVersion=projection.canonicalization_version,
        appMaterializerVersion=projection.app_materializer_version,
        materializerVersion=projection.materializer_version,
        mappingVersion=projection.mapping_version,
        mappingDigest=projection.mapping_digest,
        proposalCanonicalHash=projection.proposal_canonical_hash,
        evidenceBindingHash=projection.evidence_binding_hash,
        appProjectionHash=projection.app_projection_hash,
        obligationSubtreeHash=projection.obligation_subtree_hash,
        projectionHash=projection.projection_hash,
        gate=projection.gate,
        counts=obligation_projection_counts(projection),
        requestId=request_row.id if request_row else None,
        created=created,
        idempotentRetry=idempotent_retry,
        actingMembershipId=acting_membership_id,
        authPolicyVersion=OBLIGATION_PROJECTION_POLICY_VERSION,
        createdAt=projection.created_at,
    )


@router.post(
    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection",
    response_model=ADV4ObligationProjectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_v4_obligation_projection(
    directive_id: str,
    proposal_id: str,
    request: ADV4ObligationMaterializationRequest,
    response: Response,
    idempotency_key: str = Header(
        alias="Idempotency-Key", min_length=1, max_length=255,
    ),
    acting_membership_id: str = Header(
        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4ObligationProjectionResponse:
    try:
        result = materialize_obligations(
            db,
            directive_id=directive_id,
            proposal_id=proposal_id,
            app_projection_id=request.appProjectionId,
            actor=current_user,
            membership_id=acting_membership_id,
            idempotency_key=idempotency_key,
        )
        db.commit()
        db.refresh(result.projection)
        db.refresh(result.request)
        if not result.created:
            response.status_code = status.HTTP_200_OK
        return serialize_v4_obligation_projection(
            db, result.projection,
            acting_membership_id=acting_membership_id,
            request_row=result.request,
            created=result.created,
            idempotent_retry=result.idempotent_retry,
            require_fresh=False,
        )
    except ObligationIntegrityError as exc:
        db.rollback()
        raise v4_http_error(ADV4Error(
            "projection_integrity", "", str(exc), http_status=409,
        )) from exc
    except ADV4Error as exc:
        db.rollback()
        raise v4_http_error(exc) from exc
    except DBAPIError as exc:
        db.rollback()
        translated = _obligation_database_error(exc)
        if translated is None:
            raise
        raise v4_http_error(translated) from exc


@router.get(
    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection",
    response_model=ADV4ObligationProjectionResponse,
)
def get_v4_obligation_projection(
    directive_id: str,
    proposal_id: str,
    acting_membership_id: str = Header(
        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4ObligationProjectionResponse:
    try:
        with repeatable_read_only_session(db.get_bind()) as read_db:
            authorize_obligation_audit(
                read_db, current_user, acting_membership_id,
            )
            projection = verified_obligation_projection(
                read_db, directive_id=directive_id, proposal_id=proposal_id,
            )
            return serialize_v4_obligation_projection(
                read_db, projection,
                acting_membership_id=acting_membership_id,
            )
    except ObligationIntegrityError as exc:
        raise v4_http_error(ADV4Error(
            "projection_integrity", "", str(exc), http_status=409,
        )) from exc
    except ADV4Error as exc:
        raise v4_http_error(exc) from exc
    except DBAPIError as exc:
        translated = _obligation_database_error(exc)
        if translated is None:
            raise
        raise v4_http_error(translated) from exc


@router.get(
    "/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection/reconstruction",
    response_model=ADV4ObligationReconstructionResponse,
)
def get_v4_obligation_reconstruction(
    directive_id: str,
    proposal_id: str,
    acting_membership_id: str = Header(
        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4ObligationReconstructionResponse:
    try:
        with repeatable_read_only_session(db.get_bind()) as read_db:
            authorize_obligation_audit(
                read_db, current_user, acting_membership_id,
            )
            projection = verified_obligation_projection(
                read_db, directive_id=directive_id, proposal_id=proposal_id,
            )
            subtree = reconstruct_obligation_projection(read_db, projection)
            return ADV4ObligationReconstructionResponse(
                projectionId=projection.id,
                proposalId=projection.proposal_id,
                directiveId=projection.directive_id,
                appProjectionId=projection.app_projection_id,
                gate=projection.gate,
                obligationSubtreeHash=projection.obligation_subtree_hash,
                projectionHash=projection.projection_hash,
                canonicalObligations=subtree,
                actingMembershipId=acting_membership_id,
                authPolicyVersion=OBLIGATION_PROJECTION_POLICY_VERSION,
            )
    except ObligationIntegrityError as exc:
        raise v4_http_error(ADV4Error(
            "projection_integrity", "", str(exc), http_status=409,
        )) from exc
    except ADV4Error as exc:
        raise v4_http_error(exc) from exc
    except DBAPIError as exc:
        translated = _obligation_database_error(exc)
        if translated is None:
            raise
        raise v4_http_error(translated) from exc


@router.get(
    "/directives/{directive_id}/v4/obligation-projections",
    response_model=ADV4ObligationProjectionListResponse,
)
def list_v4_obligation_projections(
    directive_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    acting_membership_id: str = Header(
        alias="Paprnav-Acting-Membership-Id", min_length=1, max_length=36,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADV4ObligationProjectionListResponse:
    try:
        with repeatable_read_only_session(db.get_bind()) as read_db:
            authorize_obligation_audit(
                read_db, current_user, acting_membership_id,
            )
            total = read_db.scalar(select(func.count()).select_from(
                ADV4CandidateObligationProjection,
            ).where(
                ADV4CandidateObligationProjection.directive_id == directive_id,
            )) or 0
            rows = read_db.scalars(select(
                ADV4CandidateObligationProjection,
            ).where(
                ADV4CandidateObligationProjection.directive_id == directive_id,
            ).order_by(
                ADV4CandidateObligationProjection.created_at.desc(),
                ADV4CandidateObligationProjection.id.desc(),
            ).offset(offset).limit(limit)).all()
            responses = [serialize_v4_obligation_projection(
                read_db, row, acting_membership_id=acting_membership_id,
            ) for row in rows]
            return ADV4ObligationProjectionListResponse(
                projections=responses, count=len(responses), total=total,
                limit=limit, offset=offset,
            )
    except ObligationIntegrityError as exc:
        raise v4_http_error(ADV4Error(
            "projection_integrity", "", str(exc), http_status=409,
        )) from exc
    except ADV4Error as exc:
        raise v4_http_error(exc) from exc
    except DBAPIError as exc:
        translated = _obligation_database_error(exc)
        if translated is None:
            raise
        raise v4_http_error(translated) from exc


@router.get(
    "/source-documents/{source_document_id}/pages/{page_number}",
    response_model=ADSourcePageEvidenceResponse,
)
def get_retained_source_page_evidence(
    source_document_id: str,
    page_number: int,
    directive_id: str = Query(alias="directiveId"),
    expected_source_content_hash: str = Query(
        alias="expectedSourceContentHash", min_length=64, max_length=64
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADSourcePageEvidenceResponse:
    ensure_ad_extraction_reviewer(current_user)
    try:
        rendition, text_version = get_materialized_source_page(
            db,
            directive_id=directive_id,
            source_document_id=source_document_id,
            page_number=page_number,
            expected_source_content_hash=expected_source_content_hash,
        )
    except ADEvidenceError as exc:
        raise evidence_http_error(exc) from exc
    return ADSourcePageEvidenceResponse(
        sourceDocumentId=source_document_id,
        directiveId=directive_id,
        sourceContentHash=rendition.source_content_hash,
        pageNumber=rendition.page_number,
        pageTextVersionId=text_version.id,
        pageTextHash=text_version.text_hash,
        pageText=text_version.page_text,
        renditionId=rendition.id,
        renditionHash=rendition.rendition_hash,
        renditionMediaType=rendition.media_type,
        renditionWidthPx=rendition.width_px,
        renditionHeightPx=rendition.height_px,
    )


@router.post(
    "/source-documents/{source_document_id}/pages/{page_number}/materialization",
    response_model=ADSourcePageEvidenceResponse,
)
def materialize_retained_source_page_evidence(
    source_document_id: str,
    page_number: int,
    request: ADSourcePageMaterializeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADSourcePageEvidenceResponse:
    ensure_ad_extraction_reviewer(current_user)
    try:
        rendition, text_version = materialize_source_page(
            db,
            directive_id=request.directiveId,
            source_document_id=source_document_id,
            page_number=page_number,
            expected_source_content_hash=request.expectedSourceContentHash,
        )
    except ADEvidenceError as exc:
        raise evidence_http_error(exc) from exc
    db.commit()
    return ADSourcePageEvidenceResponse(
        sourceDocumentId=source_document_id,
        directiveId=request.directiveId,
        sourceContentHash=rendition.source_content_hash,
        pageNumber=rendition.page_number,
        pageTextVersionId=text_version.id,
        pageTextHash=text_version.text_hash,
        pageText=text_version.page_text,
        renditionId=rendition.id,
        renditionHash=rendition.rendition_hash,
        renditionMediaType=rendition.media_type,
        renditionWidthPx=rendition.width_px,
        renditionHeightPx=rendition.height_px,
    )


@router.post(
    "/source-documents/{source_document_id}/fragments",
    response_model=ADEvidenceFragmentResponse,
)
def create_retained_source_evidence_fragment(
    source_document_id: str,
    request: ADEvidenceFragmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADEvidenceFragmentResponse:
    ensure_ad_extraction_reviewer(current_user)
    try:
        fragment, created = admit_evidence_fragment(
            db,
            directive_id=request.directiveId,
            source_document_id=source_document_id,
            page_number=request.pageNumber,
            expected_source_content_hash=request.expectedSourceContentHash,
            expected_page_text_hash=request.expectedPageTextHash,
            character_start=request.characterStart,
            character_end=request.characterEnd,
            actor=current_user,
            reason=request.reason,
            paragraph_locator=request.paragraphLocator,
            table_locator=request.tableLocator,
            row_locator=request.rowLocator,
            note_locator=request.noteLocator,
        )
    except ADEvidenceError as exc:
        raise evidence_http_error(exc) from exc
    db.commit()
    db.refresh(fragment)
    return ADEvidenceFragmentResponse(
        id=fragment.id,
        directiveId=fragment.directive_id,
        sourceDocumentId=fragment.source_document_id,
        sourceContentHash=fragment.source_content_hash,
        pageTextVersionId=fragment.page_text_version_id,
        pageStart=fragment.page_start,
        pageEnd=fragment.page_end,
        characterStart=fragment.character_start,
        characterEnd=fragment.character_end,
        paragraphLocator=fragment.paragraph_locator,
        tableLocator=fragment.table_locator,
        rowLocator=fragment.row_locator,
        noteLocator=fragment.note_locator,
        exactText=fragment.exact_text,
        fragmentHash=fragment.fragment_hash,
        createdByUserId=fragment.created_by_user_id,
        createdAt=fragment.created_at,
        created=created,
    )


@router.get("/discovery-records", response_model=list[ADDiscoveryRecordResponse])
def list_discovery_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ADDiscoveryRecordResponse]:
    _ = current_user
    records = db.scalars(select(ADDiscoveryRecord).order_by(ADDiscoveryRecord.publication_date.desc())).all()
    return [serialize_discovery_record(record) for record in records]


@router.get("/directives", response_model=list[AirworthinessDirectiveResponse])
def list_directives(
    q: str | None = Query(default=None, max_length=200),
    ad_number: str | None = Query(default=None, max_length=64),
    directive_status: str | None = Query(default=None, alias="status", max_length=64),
    product_type: str | None = Query(default=None, alias="productType", max_length=64),
    manufacturer: str | None = Query(default=None, max_length=255),
    model: str | None = Query(default=None, max_length=255),
    include_unreviewed: bool = Query(default=False, alias="includeUnreviewed"),
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AirworthinessDirectiveResponse]:
    if include_unreviewed and not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paprnav administrator access required for unreleased directives",
        )
    statement = select(AirworthinessDirective).options(
        selectinload(AirworthinessDirective.discovery_record),
        selectinload(AirworthinessDirective.extractions)
        .selectinload(ADExtraction.reviews)
        .selectinload(ADExtractionReview.reviewer)
        .selectinload(User.memberships),
        selectinload(AirworthinessDirective.publications).selectinload(
            ADPublication.source_document
        ),
        selectinload(AirworthinessDirective.target_applicabilities).selectinload(
            ADTargetApplicability.target
        ),
    )
    if not include_unreviewed:
        statement = statement.where(AirworthinessDirective.review_status == "approved")
    if q and include_unreviewed:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                AirworthinessDirective.title.ilike(term),
                AirworthinessDirective.ad_number.ilike(term),
                current_target_exists(search_term=term),
            )
        )
    if ad_number:
        normalized_number = ad_number.upper().removeprefix("AD ").strip()
        statement = statement.where(AirworthinessDirective.ad_number.ilike(f"%{normalized_number}%"))
    if directive_status:
        statement = statement.where(AirworthinessDirective.status == directive_status)
    if (product_type or manufacturer or model) and include_unreviewed:
        statement = statement.where(current_target_exists(
            product_type=product_type,
            manufacturer=manufacturer,
            model=model,
        ))
    ordered = statement.order_by(
        AirworthinessDirective.ad_number.desc(),
        AirworthinessDirective.created_at.desc(),
    )
    if include_unreviewed:
        ordered = ordered.limit(limit)
    directives = db.scalars(ordered).all()
    if not include_unreviewed:
        released_by_directive = {
            extraction.directive_id: extraction
            for extraction in released_signed_extractions(db)
        }
        directives = [
            directive for directive in directives
            if directive.id in released_by_directive
        ]
        directives = [
            directive
            for directive in directives
            if directive_has_verified_release_evidence(directive)
            and released_directive_matches_query(
                directive,
                q=q,
                product_type=product_type,
                manufacturer=manufacturer,
                model=model,
            )
        ][:limit]
    return [serialize_directive(directive) for directive in directives]


def current_target_exists(
    *,
    search_term: str | None = None,
    product_type: str | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
):
    target_query = (
        select(ADTargetApplicability.id)
        .join(
            ApplicabilityTarget,
            ApplicabilityTarget.id == ADTargetApplicability.target_id,
        )
        .where(
            ADTargetApplicability.directive_id == AirworthinessDirective.id,
            ADTargetApplicability.status == "current",
        )
    )
    if search_term:
        target_query = target_query.where(or_(
            ApplicabilityTarget.make.ilike(search_term),
            ApplicabilityTarget.model.ilike(search_term),
            ApplicabilityTarget.product_type.ilike(search_term),
            ApplicabilityTarget.product_subtype.ilike(search_term),
        ))
    if product_type:
        target_query = target_query.where(ApplicabilityTarget.product_type.ilike(product_type.strip()))
    if manufacturer:
        target_query = target_query.where(ApplicabilityTarget.make.ilike(f"%{manufacturer.strip()}%"))
    if model:
        target_query = target_query.where(ApplicabilityTarget.model.ilike(f"%{model.strip()}%"))
    return target_query.exists()


def directive_has_verified_release_evidence(directive: AirworthinessDirective) -> bool:
    return released_extraction_for_directive(directive) is not None


def released_directive_matches_query(
    directive: AirworthinessDirective,
    *,
    q: str | None,
    product_type: str | None,
    manufacturer: str | None,
    model: str | None,
) -> bool:
    extraction = released_extraction_for_directive(directive)
    if extraction is None:
        return False
    targets = [
        item.target
        for item in directive.target_applicabilities
        if item.status == "current"
        and item.source_extraction_id == extraction.id
        and item.target is not None
    ]
    if q:
        needle = q.strip().lower()
        searchable = [directive.title, directive.ad_number]
        searchable.extend(
            value
            for target in targets
            for value in (
                target.make,
                target.model,
                target.product_type,
                target.product_subtype,
            )
        )
        if not any(needle in str(value or "").lower() for value in searchable):
            return False
    if product_type and not any(
        target.product_type.lower() == product_type.strip().lower()
        for target in targets
    ):
        return False
    if manufacturer and not any(
        manufacturer.strip().lower() in str(target.make or "").lower()
        for target in targets
    ):
        return False
    if model and not any(
        model.strip().lower() in str(target.model or "").lower()
        for target in targets
    ):
        return False
    return True


@router.get("/extraction-reviews", response_model=ADExtractionReviewListResponse)
def list_extraction_reviews(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=1, ge=1, le=20),
    review_id: str | None = Query(default=None, alias="reviewId", max_length=64),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADExtractionReviewListResponse:
    ensure_ad_extraction_reviewer(current_user)
    all_reviews = db.scalars(
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
    review_statuses = [review.status for review in all_reviews]
    current_offset = offset
    if review_id:
        matching_index = next(
            (index for index, review in enumerate(all_reviews) if review.id == review_id),
            None,
        )
        selected_models = (
            [all_reviews[matching_index]]
            if matching_index is not None
            else []
        )
        current_offset = matching_index or 0
    else:
        selected_models = all_reviews[offset:offset + limit]
    # Exact retained-byte/text verification is intentionally limited to the
    # selected page. Re-parsing every retained Federal Register PDF just to
    # render queue counters made the reviewer UI unavailable. Aggregate counts
    # are triage hints derived from the persisted source cache; the selected
    # review, approval action, and release gate all re-derive exact source text.
    selected_reviews = [serialize_review(review) for review in selected_models]
    aggregate_states = [review_queue_candidate_state(review) for review in all_reviews]
    verified_count = sum(state[0] for state in aggregate_states)
    return ADExtractionReviewListResponse(
        reviews=selected_reviews,
        currentOffset=current_offset,
        totalCount=len(review_statuses),
        pendingCount=sum(review_status == "pending" for review_status in review_statuses),
        reviewedCount=sum(review_status != "pending" for review_status in review_statuses),
        verifiedCount=verified_count,
        quarantinedCount=len(all_reviews) - verified_count,
        approvalReadyCount=sum(state[1] for state in aggregate_states),
    )


@router.get("/aircraft/{aircraft_id}/matches", response_model=ADMatchResultListResponse)
def list_aircraft_matches(
    aircraft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADMatchResultListResponse:
    get_visible_aircraft_or_404(db, current_user, aircraft_id)
    matches = db.scalars(
        select(ADMatchResult)
        .where(
            ADMatchResult.aircraft_id == aircraft_id,
            ADMatchResult.algorithm_name == ALGORITHM_NAME,
            ADMatchResult.algorithm_version == ALGORITHM_VERSION,
            ADMatchResult.is_current.is_(True),
        )
        .options(
            selectinload(ADMatchResult.aircraft),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.publications),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.extractions),
            selectinload(ADMatchResult.extraction)
            .selectinload(ADExtraction.reviews)
            .selectinload(ADExtractionReview.reviewer)
            .selectinload(User.memberships),
            selectinload(ADMatchResult.directive)
            .selectinload(AirworthinessDirective.publications)
            .selectinload(ADPublication.source_document),
            selectinload(ADMatchResult.installed_component),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.target),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.source_publication),
            selectinload(ADMatchResult.due_state).selectinload(AircraftADDueState.requirement),
            selectinload(ADMatchResult.due_state_links)
            .selectinload(ADMatchDueStateLink.due_state)
            .selectinload(AircraftADDueState.requirement),
            selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
            selectinload(ADMatchResult.adjudication),
        )
        .order_by(ADMatchResult.status.desc(), ADMatchResult.confidence.desc(), ADMatchResult.created_at.desc())
    ).all()
    matches = [
        match for match in matches
        if extraction_has_signed_release(match.extraction)
        and match_has_signed_materialization_chain(match)
    ]
    latest_matching_event = db.scalar(
        select(ProductEvent)
        .where(
            ProductEvent.aircraft_id == aircraft_id,
            ProductEvent.event_type.in_(
                {"ad_matching_completed", "ad_matching_invalidated"}
            ),
        )
        .order_by(ProductEvent.event_time.desc(), ProductEvent.created_at.desc())
        .limit(1)
    )
    completion_properties = (
        latest_matching_event.properties_json
        if latest_matching_event and latest_matching_event.properties_json
        else {}
    )
    completed_with_current_version = (
        latest_matching_event is not None
        and latest_matching_event.event_type == "ad_matching_completed"
        and completion_properties.get("algorithm_name") == ALGORITHM_NAME
        and completion_properties.get("algorithm_version") == ALGORITHM_VERSION
    )
    matching_was_invalidated = (
        latest_matching_event is not None
        and latest_matching_event.event_type == "ad_matching_invalidated"
    )
    has_stale_results = db.scalar(
        select(ADMatchResult.id)
        .where(
            ADMatchResult.aircraft_id == aircraft_id,
            ADMatchResult.algorithm_name == ALGORITHM_NAME,
            (
                (ADMatchResult.algorithm_version != ALGORITHM_VERSION)
                | ADMatchResult.is_current.is_(False)
            ),
        )
        .limit(1)
    ) is not None
    if matches or completed_with_current_version:
        matcher_status = "current"
    elif matching_was_invalidated or has_stale_results:
        matcher_status = "pending_recomputation"
    else:
        matcher_status = "not_run"
    coverage = summarize_aircraft_coverage_status(db, aircraft_id)
    return ADMatchResultListResponse(
        matches=[serialize_match_result(match) for match in matches],
        matcherStatus=matcher_status,
        algorithmName=ALGORITHM_NAME,
        algorithmVersion=ALGORITHM_VERSION,
        reprocessingRequired=matcher_status == "pending_recomputation",
        **coverage,
    )


def match_has_signed_materialization_chain(match: ADMatchResult) -> bool:
    applicability = match.target_applicability
    if (
        applicability is None
        or applicability.status != "current"
        or applicability.source_extraction_id != match.extraction_id
    ):
        return False
    due_states = [
        link.due_state for link in match.due_state_links
        if link.due_state is not None
    ]
    if match.due_state is not None and all(
        state.id != match.due_state.id for state in due_states
    ):
        due_states.append(match.due_state)
    for state in due_states:
        requirement = state.requirement
        if (
            not state.is_current
            or state.aircraft_id != match.aircraft_id
            or state.installed_component_id != match.installed_component_id
            or requirement is None
            or requirement.status != "current"
            or requirement.source_extraction_id != match.extraction_id
            or requirement.target_applicability_id != applicability.id
        ):
            return False
    return True


@router.post("/matches/{match_id}/adjudication", response_model=ADMatchAdjudicationDecisionResponse)
def decide_match_adjudication(
    match_id: str,
    payload: ADMatchAdjudicationDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADMatchAdjudicationDecisionResponse:
    allowed = {"satisfied", "not_satisfied", "not_applicable", "needs_more_info", "deferred"}
    if payload.decision not in allowed:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported adjudication decision")
    match = db.scalar(
        select(ADMatchResult)
        .where(ADMatchResult.id == match_id)
        .options(
            selectinload(ADMatchResult.aircraft),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.publications),
            selectinload(ADMatchResult.installed_component),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.target),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.source_publication),
            selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
            selectinload(ADMatchResult.adjudication),
        )
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AD match not found")
    aircraft = get_visible_aircraft_or_404(db, current_user, match.aircraft_id)
    ensure_maintenance_review_access(db, aircraft, current_user)
    if not match.is_current:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="AD match is stale and must be recomputed before adjudication",
        )
    adjudication = match.adjudication
    if adjudication is None:
        adjudication = ADMatchAdjudication(match_result_id=match.id)
        db.add(adjudication)
        db.flush()
        match.adjudication = adjudication
    adjudication.status = "reviewed"
    adjudication.decision = payload.decision
    adjudication.reviewer_user_id = current_user.id
    adjudication.notes = payload.notes
    adjudication.future_improvement_tags = payload.futureImprovementTags
    adjudication.reviewed_at = datetime.now(timezone.utc)
    match.status = f"adjudicated_{payload.decision}"
    record_product_event(
        db,
        event_type="ad_match_adjudicated",
        subject_type="ad_match",
        subject_id=match.id,
        actor=current_user,
        aircraft_id=match.aircraft_id,
        properties={
            "decision": payload.decision,
            "tags": payload.futureImprovementTags,
            "matchStatus": match.status,
        },
    )
    record_workflow_status(
        db,
        workflow_type="hitl_adjudication",
        workflow_id=adjudication.id,
        previous_status="pending",
        new_status="reviewed",
        reason=payload.decision,
        actor_type="reviewer",
        actor=current_user,
    )
    db.commit()
    match = db.scalar(
        select(ADMatchResult)
        .where(ADMatchResult.id == match_id)
        .options(
            selectinload(ADMatchResult.aircraft),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.publications),
            selectinload(ADMatchResult.installed_component),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.target),
            selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.source_publication),
            selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
            selectinload(ADMatchResult.adjudication),
        )
    )
    return ADMatchAdjudicationDecisionResponse(match=serialize_match_result(match))


@router.post("/extraction-reviews/{review_id}/decision", response_model=ADReviewDecisionResponse)
def decide_extraction_review(
    review_id: str,
    payload: ADReviewDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADReviewDecisionResponse:
    ensure_ad_extraction_reviewer(current_user)
    review = db.scalar(
        select(ADExtractionReview)
        .where(ADExtractionReview.id == review_id)
        .with_for_update()
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AD extraction review not found")
    if review.status != "pending":
        attempted_output = derive_compliance_action_summaries(
            payload.output if payload.output is not None else review.proposed_output
        )
        db.add(ADExtractionReviewDecision(
            review_id=review.id,
            extraction_id=review.extraction_id,
            decision=payload.decision,
            output_hash=structured_output_hash(attempted_output),
            decision_output=attempted_output,
            actor_user_id=current_user.id,
            decided_at=datetime.now(timezone.utc),
            notes=payload.notes,
            event_type="decision_conflict",
            metadata_json={
                "directiveId": review.extraction.directive_id,
                "terminalStatusObserved": review.status,
                "terminalReviewerUserId": review.reviewer_user_id,
            },
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review has already been decided; the conflicting attempt was recorded",
        )
    if payload.decision not in {"approved", "edited", "rejected"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported review decision")

    decision_output = derive_compliance_action_summaries(
        payload.output if payload.output is not None else review.proposed_output
    )
    affected_aircraft_ids = set(
        db.scalars(
            select(ADMatchResult.aircraft_id)
            .where(
                ADMatchResult.directive_id == review.extraction.directive_id,
                ADMatchResult.is_current.is_(True),
            )
            .distinct()
        )
        .all()
    )
    if payload.decision in {"approved", "edited"}:
        source_pages = bounded_source_document_pages(
            ensure_persisted_source_pages(
                review.extraction.directive,
                review.extraction,
            ),
            ad_number=review.extraction.directive.ad_number,
            title=review.extraction.directive.title,
        )
        evidence_status, evidence_message = source_evidence_status(
            review.extraction.directive.ad_number,
            source_pages,
        )
        if evidence_status != "verified":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=evidence_message,
            )
        approval_blockers = extraction_approval_blockers(
            review.extraction,
            decision_output,
            source_pages,
        )
        if approval_blockers:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=" ".join(approval_blockers),
            )
        review.extraction.output = decision_output
        db.execute(
            update(ADExtraction)
            .where(
                ADExtraction.directive_id == review.extraction.directive_id,
                ADExtraction.id != review.extraction.id,
                ADExtraction.status == "approved",
            )
            .values(status="superseded")
        )
        review.extraction.status = "approved"
        review.extraction.directive.extraction_status = "complete"
        review.extraction.directive.review_status = "approved"
        review.extraction.directive.approved_at = datetime.now(timezone.utc)
        populate_applicability_from_extraction(db, review.extraction)
        materialize_requirements_from_extraction(db, review.extraction)
        db.flush()
        target_ids = db.scalars(
            select(ADTargetApplicability.target_id)
            .where(
                ADTargetApplicability.directive_id
                == review.extraction.directive_id,
                ADTargetApplicability.status == "current",
                ADTargetApplicability.source_extraction_id == review.extraction.id,
            )
            .distinct()
        ).all()
        if target_ids:
            affected_aircraft_ids.update(
                db.scalars(
                    select(ADCoverageSubscription.aircraft_id)
                    .join(
                        ADCoverageSet,
                        ADCoverageSet.id
                        == ADCoverageSubscription.coverage_set_id,
                    )
                    .where(
                        ADCoverageSet.target_id.in_(target_ids),
                        ADCoverageSubscription.status == "active",
                    )
                    .distinct()
                ).all()
            )
    else:
        review.extraction.status = "rejected"
        review.extraction.directive.review_status = "rejected"

    decision_time = datetime.now(timezone.utc)
    db.add(ADExtractionReviewDecision(
        review_id=review.id,
        extraction_id=review.extraction_id,
        decision=payload.decision,
        output_hash=structured_output_hash(decision_output),
        decision_output=decision_output,
        actor_user_id=current_user.id,
        decided_at=decision_time,
        notes=payload.notes,
        event_type="review_decision",
        metadata_json={"directiveId": review.extraction.directive_id},
    ))
    review.status = payload.decision
    review.decision = payload.decision
    review.decision_output = decision_output
    review.reviewer_user_id = current_user.id
    review.notes = payload.notes
    review.reviewed_at = decision_time
    for aircraft_id in affected_aircraft_ids:
        resolve_aircraft_ad_coverage(db, aircraft_id)
        invalidate_aircraft_match_results(
            db,
            aircraft_id=aircraft_id,
            actor=current_user,
        )
    record_product_event(
        db,
        event_type="ad_extraction_review_decided",
        subject_type="ad_review",
        subject_id=review.id,
        actor=current_user,
        properties={
            "decision": payload.decision,
            "directiveId": review.extraction.directive_id,
            "extractionStatus": review.extraction.status,
        },
    )
    record_workflow_status(
        db,
        workflow_type="ad_extraction",
        workflow_id=review.extraction_id,
        previous_status="needs_review",
        new_status=review.extraction.status,
        reason=payload.decision,
        actor_type="reviewer",
        actor=current_user,
    )
    db.commit()
    db.refresh(review)
    return ADReviewDecisionResponse(review=serialize_review(review))


def serialize_discovery_record(record: ADDiscoveryRecord) -> ADDiscoveryRecordResponse:
    return ADDiscoveryRecordResponse(
        id=record.id,
        federalRegisterDocumentNumber=record.federal_register_document_number,
        title=record.title,
        documentType=record.document_type,
        publicationDate=record.publication_date,
        htmlUrl=record.html_url,
        pdfUrl=record.pdf_url,
        classification=record.classification,
        classificationConfidence=record.classification_confidence,
        classificationReason=record.classification_reason,
        contentHash=record.content_hash,
    )


def serialize_directive(directive: AirworthinessDirective) -> AirworthinessDirectiveResponse:
    record = directive.discovery_record
    return AirworthinessDirectiveResponse(
        id=directive.id,
        discoveryRecordId=directive.discovery_record_id,
        adNumber=directive.ad_number,
        officialAdNumber=official_ad_number(directive.ad_number),
        title=directive.title,
        status=directive.status,
        extractionStatus=directive.extraction_status,
        reviewStatus=directive.review_status,
        federalRegisterDocumentNumber=record.federal_register_document_number if record else None,
        publicationDate=record.publication_date if record else first_publication_date(directive),
        htmlUrl=record.html_url if record else first_publication_url(directive, "html_url"),
        pdfUrl=record.pdf_url if record else first_publication_url(directive, "pdf_url"),
        applicabilityTargets=serialize_directive_applicability_targets(directive),
    )


def serialize_directive_applicability_targets(
    directive: AirworthinessDirective,
) -> list[ADDirectiveApplicabilityTargetResponse]:
    released_extraction = released_extraction_for_directive(directive)
    released_extraction_id = released_extraction.id if released_extraction else None
    rows: list[ADDirectiveApplicabilityTargetResponse] = []
    seen: set[tuple[str | None, str, str | None, str | None]] = set()
    for applicability in directive.target_applicabilities:
        if (
            applicability.status != "current"
            or applicability.target is None
            or applicability.source_extraction_id != released_extraction_id
        ):
            continue
        target = applicability.target
        identity = applicability.source_identity or {}
        source_manufacturer = identity.get("manufacturer") or {}
        source_model = identity.get("model") or {}
        key = (
            applicability.applicability_group_key,
            target.product_type,
            target.make,
            target.model,
        )
        if key in seen:
            continue
        seen.add(key)
        rows.append(ADDirectiveApplicabilityTargetResponse(
            groupKey=applicability.applicability_group_key,
            productType=target.product_type,
            productSubtype=target.product_subtype,
            manufacturer=target.make,
            model=target.model,
            sourceManufacturer=source_manufacturer.get("sourceName"),
            sourceModel=source_model.get("sourceDesignation"),
        ))
    return rows


def serialize_extraction(extraction: ADExtraction) -> ADExtractionResponse:
    return ADExtractionResponse(
        id=extraction.id,
        directiveId=extraction.directive_id,
        providerName=extraction.provider_name,
        providerVersion=extraction.provider_version,
        schemaVersion=extraction.schema_version,
        inputContentHash=extraction.input_content_hash,
        status=extraction.status,
        confidence=extraction.confidence,
        output=extraction.output,
        citations=extraction.citations or [],
    )


def review_queue_candidate_state(
    review: ADExtractionReview,
) -> tuple[bool, bool]:
    """Return cheap triage counts without asserting a release decision.

    The selected review is always serialized through ``persisted_source_pages``
    and therefore re-derived from verified bytes. These aggregate values only
    keep the queue responsive; they never authorize approval or publication.
    """

    raw_response = review.extraction.raw_response or {}
    cached_pages = raw_response.get("retainedSourcePages")
    if (
        not raw_response.get("retainedSourcePagesCached")
        or not isinstance(cached_pages, list)
        or review.extraction.input_content_hash
        != extraction_input_hash(review.extraction.directive)
    ):
        return False, False
    source_pages = bounded_source_document_pages(
        cached_pages,
        ad_number=review.extraction.directive.ad_number,
        title=review.extraction.directive.title,
    )
    evidence_status, _ = source_evidence_status(
        review.extraction.directive.ad_number,
        source_pages,
    )
    source_candidate = evidence_status == "verified"
    if not source_candidate:
        return False, False
    proposed_output = derive_compliance_action_summaries(
        review.decision_output
        if review.decision_output is not None
        else review.proposed_output
    )
    blockers = extraction_approval_blockers(
        review.extraction,
        proposed_output,
        source_pages,
    )
    return True, review.status == "pending" and not blockers


def serialize_review(review: ADExtractionReview) -> ADExtractionReviewResponse:
    source_pages = bounded_source_document_pages(
        full_text_pages_for_extraction(review.extraction),
        ad_number=review.extraction.directive.ad_number,
        title=review.extraction.directive.title,
    )
    evidence_status, evidence_message = source_evidence_status(
        review.extraction.directive.ad_number,
        source_pages,
    )
    proposed_output = derive_compliance_action_summaries(review.proposed_output)
    decision_output = (
        derive_compliance_action_summaries(review.decision_output)
        if review.decision_output is not None
        else None
    )
    output = decision_output or proposed_output
    requirements = output.get("requirements") or []
    approval_blockers = extraction_approval_blockers(
        review.extraction,
        output,
        source_pages,
    )
    source_document_ids = {
        str(page.get("sourceDocumentId"))
        for page in source_pages
        if page.get("sourceDocumentId")
    }
    source_documents: list[ADSourceDocumentResponse] = []
    relevant_pages_by_document: dict[str, list[int]] = {}
    for page in source_pages:
        document_id = page.get("sourceDocumentId")
        page_number = page.get("pageNumber")
        if document_id and isinstance(page_number, int):
            relevant_pages_by_document.setdefault(str(document_id), []).append(page_number)
    seen_document_ids: set[str] = set()
    for publication in review.extraction.directive.publications:
        document = publication.source_document
        if (
            document is None
            or document.id not in source_document_ids
            or document.id in seen_document_ids
        ):
            continue
        seen_document_ids.add(document.id)
        source_documents.append(serialize_source_document(
            document,
            relevant_page_numbers=relevant_pages_by_document.get(document.id, []),
        ))
    provenance = None
    staging_decision_id = (review.extraction.raw_response or {}).get(
        "latestProposalStagingDecisionId"
    )
    if staging_decision_id:
        staging_decision = next(
            (
                decision
                for decision in review.decision_history
                if decision.id == staging_decision_id
                and decision.event_type == "proposal_staged"
                and decision.decision == "proposal_staged"
            ),
            None,
        )
        if staging_decision is not None:
            metadata = staging_decision.metadata_json or {}
            provenance = ADProposalProvenanceResponse(
                stagingDecisionId=staging_decision.id,
                actorUserId=staging_decision.actor_user_id,
                stagedAt=staging_decision.decided_at,
                stagingMode=(
                    "allow_incomplete"
                    if metadata.get("allowIncomplete")
                    else "strict"
                ),
            )
    return ADExtractionReviewResponse(
        id=review.id,
        status=review.status,
        proposedOutput=proposed_output,
        decisionOutput=decision_output,
        decision=review.decision,
        notes=review.notes,
        extraction=serialize_extraction(review.extraction),
        directive=serialize_directive(review.extraction.directive),
        sourceText="\n\n".join(page["text"] for page in source_pages),
        sourcePages=source_pages,
        sourceDocuments=source_documents,
        requirementCount=len(requirements),
        unresolvedRequirementCount=(
            sum(bool(item.get("uncertaintyReasons")) for item in requirements)
            + sum(
                bool(item.get("uncertaintyReasons"))
                for item in output.get("applicabilityGroups") or []
            )
        ),
        evidenceStatus=evidence_status,
        evidenceMessage=evidence_message,
        canApprove=review.status == "pending" and not approval_blockers,
        approvalBlockers=approval_blockers,
        proposalProvenance=provenance,
    )


def serialize_source_document(
    document: ADSourceDocument,
    *,
    relevant_page_numbers: list[int] | None = None,
) -> ADSourceDocumentResponse:
    page_numbers = sorted(set(relevant_page_numbers or []))
    content_url = f"/api/v1/ads/source-documents/{document.id}/content"
    navigation_url = (
        f"{content_url}#page={page_numbers[0]}" if page_numbers else content_url
    )
    pages_contiguous = bool(page_numbers) and page_numbers == list(
        range(page_numbers[0], page_numbers[-1] + 1)
    )
    return ADSourceDocumentResponse(
        id=document.id,
        sourceSystem=document.source_system,
        sourceType=document.source_type,
        sourceIdentifier=document.source_identifier,
        parentSourceIdentifier=document.parent_source_identifier,
        sourceUrl=document.source_url,
        contentUrl=content_url,
        mediaType=document.media_type,
        contentHash=document.content_hash,
        storageBytes=document.storage_bytes,
        capturedAt=document.captured_at,
        publicationDate=document.publication_date,
        parserName=document.parser_name,
        parserVersion=document.parser_version,
        relevantPageStart=page_numbers[0] if page_numbers else None,
        relevantPageEnd=page_numbers[-1] if page_numbers else None,
        relevantPageNumbers=page_numbers,
        relevantPagesContiguous=pages_contiguous,
        navigationUrl=navigation_url,
    )


def serialize_match_result(match: ADMatchResult) -> ADMatchResultResponse:
    due_states = [
        link.due_state
        for link in match.due_state_links
        if link.due_state is not None
    ]
    if not due_states and match.due_state is not None:
        due_states = [match.due_state]
    return ADMatchResultResponse(
        id=match.id,
        aircraftId=match.aircraft_id,
        aircraftFacts={
            "nNumber": match.aircraft.n_number_normalized if match.aircraft else None,
            "make": match.aircraft.make if match.aircraft else None,
            "model": match.aircraft.model if match.aircraft else None,
            "serialNumber": match.aircraft.serial_number if match.aircraft else None,
            "engineMake": match.aircraft.engine_make if match.aircraft else None,
            "engineModel": match.aircraft.engine_model if match.aircraft else None,
            "propellerMake": match.aircraft.propeller_make if match.aircraft else None,
            "propellerModel": match.aircraft.propeller_model if match.aircraft else None,
        },
        directive=serialize_directive(match.directive),
        status=match.status,
        matchType=match.match_type,
        confidence=match.confidence,
        rationale=match.rationale,
        unresolvedReasons=match.unresolved_reasons or [],
        applicability=serialize_match_applicability(match),
        dueState=(
            ADDueStateResponse(**due_state_payload(due_states[0]))
            if len(due_states) == 1
            else None
        ),
        dueStates=[
            ADDueStateResponse(**due_state_payload(state))
            for state in due_states
        ],
        algorithmName=match.algorithm_name,
        algorithmVersion=match.algorithm_version,
        inputHash=match.input_hash,
        evidence=[serialize_match_evidence(evidence) for evidence in match.evidence_links],
        adjudication=serialize_match_adjudication(match.adjudication) if match.adjudication else None,
    )


def serialize_match_applicability(match: ADMatchResult) -> ADMatchApplicabilityResponse | None:
    applicability = match.target_applicability
    component = match.installed_component
    publications = []
    if applicability and applicability.source_publication:
        publications.append(applicability.source_publication)
    publications.extend([publication for publication in match.directive.publications if publication not in publications])
    if not applicability and not component and not publications and not match.applicability_snapshot:
        return None
    target = applicability.target if applicability else None
    return ADMatchApplicabilityResponse(
        component=ADMatchComponentResponse(
            id=component.id if component else None,
            role=component.role if component else None,
            componentType=component.component_type if component else None,
            displayName=component_display_name(component),
            make=component.make if component else None,
            model=component.model if component else None,
            serialNumber=component.serial_number if component else None,
            source=component.source if component else None,
        )
        if component
        else None,
        target=ADMatchTargetResponse(
            id=target.id,
            productType=target.product_type,
            productSubtype=target.product_subtype,
            make=target.make,
            model=target.model,
        )
        if target
        else None,
        basis=applicability.applicability_basis if applicability else None,
        confidence=applicability.confidence if applicability else None,
        status=applicability.status if applicability else None,
        sourceStatus=(publications[0].status if publications else None),
        serialStatus=(match.applicability_snapshot or {}).get("serialStatus"),
        publications=[
            ADMatchPublicationResponse(
                sourceSystem=publication.source_system,
                sourceType=publication.source_type,
                sourceIdentifier=publication.source_identifier,
                status=publication.status,
                htmlUrl=publication.html_url,
                pdfUrl=publication.pdf_url,
            )
            for publication in publications
        ],
        snapshot=match.applicability_snapshot,
    )


def first_publication_date(directive: AirworthinessDirective):
    publication = next(iter(directive.publications), None)
    return publication.publication_date if publication else None


def first_publication_url(directive: AirworthinessDirective, field_name: str) -> str | None:
    for publication in directive.publications:
        value = getattr(publication, field_name)
        if value:
            return value
    return None


def serialize_match_evidence(evidence: ADMatchEvidence) -> ADMatchEvidenceResponse:
    entry = evidence.logbook_entry
    return ADMatchEvidenceResponse(
        id=evidence.id,
        logbookEntryId=evidence.logbook_entry_id,
        entryDate=entry.entry_date,
        section=entry.logbook_section.key,
        evidenceType=evidence.evidence_type,
        fieldName=evidence.field_name,
        matchedText=evidence.matched_text,
        confidence=evidence.confidence,
        rationale=evidence.rationale,
    )


def serialize_match_adjudication(adjudication: ADMatchAdjudication) -> ADMatchAdjudicationResponse:
    return ADMatchAdjudicationResponse(
        id=adjudication.id,
        status=adjudication.status,
        decision=adjudication.decision,
        notes=adjudication.notes,
        futureImprovementTags=adjudication.future_improvement_tags or [],
    )
