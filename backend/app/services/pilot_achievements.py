from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.request_context import get_correlation_id
from app.models.core import ProductEvent, User
from app.services.observability import record_product_event


PILOT_ACHIEVEMENT_TAXONOMY = "pilot-achievement-v1"


@dataclass(frozen=True)
class AchievementSpec:
    subject_types: frozenset[str]
    property_keys: frozenset[str]


ACHIEVEMENT_SPECS: dict[str, AchievementSpec] = {
    "invite_accepted": AchievementSpec(
        frozenset({"user"}),
        frozenset(),
    ),
    "aircraft_created": AchievementSpec(
        frozenset({"aircraft"}),
        frozenset({"hasAccountTag", "hasAircraftTag"}),
    ),
    "upload_received": AchievementSpec(
        frozenset({"upload"}),
        frozenset({"contentType", "logbookSection", "storageBackend"}),
    ),
    "page_review_completed": AchievementSpec(
        frozenset({"ingestion_job"}),
        frozenset({"pageCount"}),
    ),
    "logbook_entry_created": AchievementSpec(
        frozenset({"logbook_entry"}),
        frozenset({"logbookSection", "sourceType"}),
    ),
    "ad_review_completed": AchievementSpec(
        frozenset({"ad_extraction_review", "ad_match_adjudication"}),
        frozenset({"decision", "decisionKind"}),
    ),
}


def record_pilot_achievement(
    db: Session,
    *,
    event_type: str,
    subject_type: str,
    subject_id: str,
    actor: User,
    organization_id: str | None = None,
    aircraft_id: str | None = None,
    properties: dict[str, Any] | None = None,
) -> ProductEvent:
    """Record only a declared, server-owned pilot achievement.

    Callers own the surrounding transaction. Unknown properties are discarded,
    so request metadata and free-form content cannot expand the event contract.
    """

    spec = ACHIEVEMENT_SPECS.get(event_type)
    if spec is None:
        raise ValueError("Unknown pilot achievement")
    if subject_type not in spec.subject_types:
        raise ValueError("Invalid pilot achievement subject type")
    if not subject_id or actor is None or not actor.id:
        raise ValueError("Pilot achievements require a subject and actor")

    supplied = properties or {}
    fixed_properties = {
        key: _safe_fixed_value(supplied[key])
        for key in spec.property_keys
        if key in supplied
    }
    fixed_properties["taxonomyVersion"] = PILOT_ACHIEVEMENT_TAXONOMY
    return record_product_event(
        db,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        actor=actor,
        aircraft_id=aircraft_id,
        organization_id=organization_id,
        event_source=PILOT_ACHIEVEMENT_TAXONOMY,
        properties=fixed_properties,
        request_id=get_correlation_id(),
    )


def achievement_already_recorded(
    db: Session,
    *,
    event_type: str,
    subject_type: str,
    subject_id: str,
) -> bool:
    return db.scalar(
        select(ProductEvent.id)
        .where(
            ProductEvent.event_source == PILOT_ACHIEVEMENT_TAXONOMY,
            ProductEvent.event_type == event_type,
            ProductEvent.subject_type == subject_type,
            ProductEvent.subject_id == subject_id,
        )
        .limit(1)
    ) is not None


def project_pilot_achievements(
    db: Session,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    actor_user_id: str | None = None,
    recent_limit: int = 25,
) -> tuple[dict[str, int], list[ProductEvent]]:
    """Return first-success representatives, filtering only after deduplication."""

    rows = db.scalars(
        select(ProductEvent)
        .where(
            ProductEvent.event_source == PILOT_ACHIEVEMENT_TAXONOMY,
            ProductEvent.event_type.in_(tuple(ACHIEVEMENT_SPECS)),
        )
        .order_by(ProductEvent.event_time.asc(), ProductEvent.id.asc())
    ).all()
    representatives: dict[tuple[str, str, str, str], ProductEvent] = {}
    for row in rows:
        if row.subject_id is None:
            continue
        key = (
            PILOT_ACHIEVEMENT_TAXONOMY,
            row.event_type,
            row.subject_type,
            row.subject_id,
        )
        representatives.setdefault(key, row)

    filtered = [
        row
        for row in representatives.values()
        if (date_from is None or _utc(row.event_time) >= _utc(date_from))
        and (date_to is None or _utc(row.event_time) < _utc(date_to))
        and (actor_user_id is None or row.actor_user_id == actor_user_id)
    ]
    counts = {event_type: 0 for event_type in ACHIEVEMENT_SPECS}
    for row in filtered:
        counts[row.event_type] += 1
    recent = sorted(
        filtered,
        key=lambda row: (row.event_time, row.id),
        reverse=True,
    )[:recent_limit]
    return counts, recent


def _safe_fixed_value(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:64]
    return None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
