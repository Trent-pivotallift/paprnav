from typing import Any

from sqlalchemy.orm import Session

from app.models.core import ProductEvent, User, WorkflowStatusEvent

BLOCKED_PROPERTY_NAMES = {
    "password",
    "token",
    "secret",
    "raw_text",
    "ocr_text",
    "file_content",
    "file_bytes",
    "corrected_text",
    "original_text",
    "message_body",
}


def record_product_event(
    db: Session,
    event_type: str,
    subject_type: str,
    subject_id: str | None = None,
    actor: User | None = None,
    aircraft_id: str | None = None,
    organization_id: str | None = None,
    event_source: str = "backend",
    properties: dict[str, Any] | None = None,
    request_id: str | None = None,
    session_id: str | None = None,
) -> ProductEvent:
    safe_properties = sanitize_properties(properties or {})
    event = ProductEvent(
        actor_user_id=actor.id if actor else None,
        organization_id=organization_id,
        aircraft_id=aircraft_id,
        event_type=event_type,
        event_source=event_source,
        subject_type=subject_type,
        subject_id=subject_id,
        properties_json=safe_properties,
        request_id=request_id,
        session_id=session_id,
    )
    db.add(event)
    db.flush()
    return event


def record_workflow_status(
    db: Session,
    workflow_type: str,
    workflow_id: str,
    new_status: str,
    previous_status: str | None = None,
    reason: str | None = None,
    actor_type: str = "system",
    actor: User | None = None,
) -> WorkflowStatusEvent:
    event = WorkflowStatusEvent(
        workflow_type=workflow_type,
        workflow_id=workflow_id,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        actor_type=actor_type,
        actor_user_id=actor.id if actor else None,
    )
    db.add(event)
    db.flush()
    return event


def sanitize_properties(properties: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in properties.items():
        normalized_key = key.lower()
        if normalized_key in BLOCKED_PROPERTY_NAMES or any(part in normalized_key for part in ["password", "secret", "token"]):
            continue
        safe[key] = sanitize_value(value)
    return safe


def sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize_properties(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value[:20]]
    if isinstance(value, str):
        return value[:256]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:256]
