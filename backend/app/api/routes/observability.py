from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.aircraft import get_visible_aircraft_or_404
from app.db.session import get_db
from app.models.core import ProductEvent, User, UserFeedback, WorkflowStatusEvent
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

    event_statement = select(ProductEvent).order_by(ProductEvent.event_time.desc()).limit(100)
    if aircraft_id:
        event_statement = event_statement.where(ProductEvent.aircraft_id == aircraft_id)
    if user_id:
        event_statement = event_statement.where(ProductEvent.actor_user_id == user_id)
    if event_type:
        event_statement = event_statement.where(ProductEvent.event_type == event_type)
    if subject_type:
        event_statement = event_statement.where(ProductEvent.subject_type == subject_type)

    workflow_statement = select(WorkflowStatusEvent).order_by(WorkflowStatusEvent.created_at.desc()).limit(100)
    if workflow_id:
        workflow_statement = workflow_statement.where(WorkflowStatusEvent.workflow_id == workflow_id)
    if status_filter:
        workflow_statement = workflow_statement.where(WorkflowStatusEvent.new_status == status_filter)
    if user_id:
        workflow_statement = workflow_statement.where(WorkflowStatusEvent.actor_user_id == user_id)

    feedback_statement = select(UserFeedback).order_by(UserFeedback.created_at.desc()).limit(50)
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
    if payload.aircraftId:
        get_visible_aircraft_or_404(db, current_user, payload.aircraftId)
    organization_id = current_user.memberships[0].organization_id if current_user.memberships else None
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
    feedback = db.get(UserFeedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    if feedback.aircraft_id:
        get_visible_aircraft_or_404(db, current_user, feedback.aircraft_id)
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
