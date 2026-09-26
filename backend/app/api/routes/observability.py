from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.admin import ensure_platform_admin
from app.api.routes.aircraft import get_visible_aircraft_or_404, visible_aircraft_statement
from app.db.session import get_db
from app.models.core import (
    ADMatchAdjudication,
    ADMatchResult,
    Aircraft,
    AircraftAssignment,
    IngestionJob,
    ProductEvent,
    User,
    UserFeedback,
    WorkflowStatusEvent,
)
from app.schemas.observability import (
    ObservabilityListResponse,
    ProductEventResponse,
    UserFeedbackCreateRequest,
    UserFeedbackCreateResponse,
    UserFeedbackResponse,
    UserFeedbackUpdateRequest,
    WorkflowStatusEventResponse,
)
from app.services.observability import record_product_event, sanitize_value

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


@router.get("", response_model=ObservabilityListResponse)
def list_observability(
    aircraft_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    subject_type: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    workflow_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ObservabilityListResponse:
    if aircraft_id:
        get_visible_aircraft_or_404(db, current_user, aircraft_id)
    if user_id and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot widen observability scope",
        )
    return _list_observability(
        db,
        current_user=current_user,
        admin_scope=False,
        aircraft_id=aircraft_id,
        user_id=user_id,
        event_type=event_type,
        subject_type=subject_type,
        status_filter=status_filter,
        workflow_id=workflow_id,
    )


@router.get("/admin", response_model=ObservabilityListResponse)
def list_observability_admin(
    aircraft_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    subject_type: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    workflow_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ObservabilityListResponse:
    ensure_platform_admin(current_user)
    return _list_observability(
        db,
        current_user=current_user,
        admin_scope=True,
        aircraft_id=aircraft_id,
        user_id=user_id,
        event_type=event_type,
        subject_type=subject_type,
        status_filter=status_filter,
        workflow_id=workflow_id,
    )


def _list_observability(
    db: Session,
    *,
    current_user: User,
    admin_scope: bool,
    aircraft_id: Optional[str],
    user_id: Optional[str],
    event_type: Optional[str],
    subject_type: Optional[str],
    status_filter: Optional[str],
    workflow_id: Optional[str],
) -> ObservabilityListResponse:
    visible_aircraft_ids = (
        visible_aircraft_statement(current_user)
        .with_only_columns(Aircraft.id)
        .order_by(None)
    )

    event_statement = select(ProductEvent).order_by(ProductEvent.event_time.desc()).limit(100)
    if not admin_scope:
        event_statement = event_statement.where(
            or_(
                ProductEvent.aircraft_id.in_(visible_aircraft_ids),
                and_(
                    ProductEvent.aircraft_id.is_(None),
                    ProductEvent.organization_id.is_(None),
                    ProductEvent.actor_user_id == current_user.id,
                ),
            )
        )
    if aircraft_id:
        event_statement = event_statement.where(ProductEvent.aircraft_id == aircraft_id)
    if user_id:
        event_statement = event_statement.where(ProductEvent.actor_user_id == user_id)
    if event_type:
        event_statement = event_statement.where(ProductEvent.event_type == event_type)
    if subject_type:
        event_statement = event_statement.where(ProductEvent.subject_type == subject_type)

    workflow_statement = select(WorkflowStatusEvent).order_by(WorkflowStatusEvent.created_at.desc()).limit(100)
    if not admin_scope:
        visible_job_ids = select(IngestionJob.id).where(
            IngestionJob.aircraft_id.in_(visible_aircraft_ids)
        )
        visible_adjudication_ids = (
            select(ADMatchAdjudication.id)
            .join(ADMatchResult, ADMatchAdjudication.match_result_id == ADMatchResult.id)
            .where(ADMatchResult.aircraft_id.in_(visible_aircraft_ids))
        )
        workflow_statement = workflow_statement.where(
            or_(
                and_(
                    WorkflowStatusEvent.workflow_type.in_(
                        {"upload_ingestion", "page_verification", "ocr_correction"}
                    ),
                    WorkflowStatusEvent.workflow_id.in_(visible_job_ids),
                ),
                and_(
                    WorkflowStatusEvent.workflow_type == "ad_matching",
                    WorkflowStatusEvent.workflow_id.in_(visible_aircraft_ids),
                ),
                and_(
                    WorkflowStatusEvent.workflow_type == "hitl_adjudication",
                    WorkflowStatusEvent.workflow_id.in_(visible_adjudication_ids),
                ),
            )
        )
    if workflow_id:
        workflow_statement = workflow_statement.where(WorkflowStatusEvent.workflow_id == workflow_id)
    if status_filter:
        workflow_statement = workflow_statement.where(WorkflowStatusEvent.new_status == status_filter)
    if user_id:
        workflow_statement = workflow_statement.where(WorkflowStatusEvent.actor_user_id == user_id)

    feedback_statement = select(UserFeedback).order_by(UserFeedback.created_at.desc()).limit(50)
    if not admin_scope:
        feedback_statement = feedback_statement.where(
            or_(
                UserFeedback.aircraft_id.in_(visible_aircraft_ids),
                and_(
                    UserFeedback.aircraft_id.is_(None),
                    UserFeedback.organization_id.is_(None),
                    UserFeedback.submitted_by_user_id == current_user.id,
                ),
            )
        )
    if aircraft_id:
        feedback_statement = feedback_statement.where(UserFeedback.aircraft_id == aircraft_id)
    if status_filter:
        feedback_statement = feedback_statement.where(UserFeedback.status == status_filter)
    if subject_type:
        feedback_statement = feedback_statement.where(UserFeedback.subject_type == subject_type)

    return ObservabilityListResponse(
        events=[serialize_product_event(event) for event in db.scalars(event_statement).all()],
        workflowEvents=[serialize_workflow_status(event) for event in db.scalars(workflow_statement).all()],
        feedback=[serialize_feedback(item) for item in db.scalars(feedback_statement).all()],
    )


@router.post("/feedback", response_model=UserFeedbackCreateResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: UserFeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserFeedbackCreateResponse:
    organization_id = None
    if payload.aircraftId:
        aircraft = get_visible_aircraft_or_404(db, current_user, payload.aircraftId)
        active_organization_ids = {
            membership.organization_id
            for membership in current_user.memberships
            if membership.status == "active"
        }
        if aircraft.owner_organization_id in active_organization_ids:
            organization_id = aircraft.owner_organization_id
        else:
            organization_id = db.scalar(
                select(AircraftAssignment.organization_id).where(
                    AircraftAssignment.aircraft_id == aircraft.id,
                    AircraftAssignment.organization_id.in_(active_organization_ids),
                    AircraftAssignment.status == "active",
                )
            )
    feedback = UserFeedback(
        submitted_by_user_id=current_user.id,
        organization_id=organization_id,
        aircraft_id=payload.aircraftId,
        subject_type=payload.subjectType,
        subject_id=payload.subjectId,
        feedback_type=payload.feedbackType,
        message=sanitize_value(payload.message),
        severity=payload.severity,
        status="open",
    )
    db.add(feedback)
    db.flush()
    record_product_event(
        db,
        event_type="feedback_created",
        subject_type=payload.subjectType,
        subject_id=payload.subjectId,
        actor=current_user,
        aircraft_id=payload.aircraftId,
        organization_id=organization_id,
        properties={"feedbackType": payload.feedbackType, "severity": payload.severity},
    )
    db.commit()
    db.refresh(feedback)
    return UserFeedbackCreateResponse(feedback=serialize_feedback(feedback))


@router.patch("/feedback/{feedback_id}", response_model=UserFeedbackCreateResponse)
def update_feedback(
    feedback_id: str,
    payload: UserFeedbackUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserFeedbackCreateResponse:
    ensure_platform_admin(current_user)
    feedback = db.get(UserFeedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    feedback.status = payload.status
    record_product_event(
        db,
        event_type="feedback_status_updated",
        subject_type="feedback",
        subject_id=feedback.id,
        actor=current_user,
        aircraft_id=feedback.aircraft_id,
        organization_id=feedback.organization_id,
        properties={"status": payload.status},
    )
    db.commit()
    db.refresh(feedback)
    return UserFeedbackCreateResponse(feedback=serialize_feedback(feedback))


def serialize_product_event(event: ProductEvent) -> ProductEventResponse:
    return ProductEventResponse(
        id=event.id,
        actorUserId=event.actor_user_id,
        organizationId=event.organization_id,
        aircraftId=event.aircraft_id,
        eventType=event.event_type,
        eventSource=event.event_source,
        subjectType=event.subject_type,
        subjectId=event.subject_id,
        eventTime=event.event_time,
        properties=event.properties_json or {},
    )


def serialize_workflow_status(event: WorkflowStatusEvent) -> WorkflowStatusEventResponse:
    return WorkflowStatusEventResponse(
        id=event.id,
        workflowType=event.workflow_type,
        workflowId=event.workflow_id,
        previousStatus=event.previous_status,
        newStatus=event.new_status,
        reason=event.reason,
        actorType=event.actor_type,
        actorUserId=event.actor_user_id,
        createdAt=event.created_at,
    )


def serialize_feedback(feedback: UserFeedback) -> UserFeedbackResponse:
    return UserFeedbackResponse(
        id=feedback.id,
        submittedByUserId=feedback.submitted_by_user_id,
        organizationId=feedback.organization_id,
        aircraftId=feedback.aircraft_id,
        subjectType=feedback.subject_type,
        subjectId=feedback.subject_id,
        feedbackType=feedback.feedback_type,
        message=feedback.message,
        severity=feedback.severity,
        status=feedback.status,
    )
