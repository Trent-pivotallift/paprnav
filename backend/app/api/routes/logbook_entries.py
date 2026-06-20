from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.aircraft import get_visible_aircraft_or_404
from app.db.session import get_db
from app.models.core import LogbookEntry, LogbookSection, User
from app.schemas.logbook_entries import (
    LogbookEntryCreateRequest,
    LogbookEntryListResponse,
    LogbookEntryResponse,
    LogbookEntryUpdateRequest,
    LogbookSectionKey,
)
from app.services.observability import record_product_event

router = APIRouter(prefix="/api/v1/aircraft/{aircraft_id}/logbook-entries", tags=["logbook-entries"])


def optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def response_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(value, 2)


def get_section_by_key(db: Session, section_key: str) -> LogbookSection:
    section = db.scalar(select(LogbookSection).where(LogbookSection.key == section_key))
    if not section:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown logbook section")
    return section


def get_entry_or_404(db: Session, aircraft_id: str, entry_id: str) -> LogbookEntry:
    entry = db.scalar(
        select(LogbookEntry).where(
            LogbookEntry.aircraft_id == aircraft_id,
            LogbookEntry.id == entry_id,
        )
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logbook entry not found")
    return entry


def serialize_entry(entry: LogbookEntry) -> LogbookEntryResponse:
    return LogbookEntryResponse(
        id=entry.id,
        aircraftId=entry.aircraft_id,
        section=entry.logbook_section.key,
        entryDate=entry.entry_date,
        description=entry.description,
        performerName=entry.performer_name,
        performerCredential=entry.performer_credential,
        sourceType=entry.source_type,
        reviewStatus=entry.review_status,
        tachTime=response_float(entry.tach_time),
        hobbsTime=response_float(entry.hobbs_time),
        totalTime=response_float(entry.total_time),
    )


@router.get("", response_model=LogbookEntryListResponse)
def list_logbook_entries(
    aircraft_id: str,
    section: Optional[LogbookSectionKey] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogbookEntryListResponse:
    get_visible_aircraft_or_404(db, current_user, aircraft_id)

    statement = select(LogbookEntry).where(LogbookEntry.aircraft_id == aircraft_id).join(LogbookEntry.logbook_section)
    if section is not None:
        statement = statement.where(LogbookSection.key == section)
    statement = statement.order_by(LogbookEntry.entry_date.desc(), LogbookEntry.created_at.desc())

    entries = db.scalars(statement).all()
    return LogbookEntryListResponse(entries=[serialize_entry(entry) for entry in entries])


@router.post("", response_model=LogbookEntryResponse, status_code=status.HTTP_201_CREATED)
def create_logbook_entry(
    aircraft_id: str,
    payload: LogbookEntryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogbookEntryResponse:
    get_visible_aircraft_or_404(db, current_user, aircraft_id)
    section = get_section_by_key(db, payload.section)

    entry = LogbookEntry(
        aircraft_id=aircraft_id,
        logbook_section_id=section.id,
        entry_date=payload.entryDate,
        description=payload.description.strip(),
        performer_name=optional_str(payload.performerName),
        performer_credential=optional_str(payload.performerCredential),
        source_type="manual",
        created_by_user_id=current_user.id,
        tach_time=payload.tachTime,
        hobbs_time=payload.hobbsTime,
        total_time=payload.totalTime,
        raw_text=None,
        review_status="verified",
    )
    db.add(entry)
    db.flush()
    record_product_event(
        db,
        event_type="logbook_entry_created",
        subject_type="logbook_entry",
        subject_id=entry.id,
        actor=current_user,
        aircraft_id=aircraft_id,
        properties={
            "section": section.key,
            "entryDate": entry.entry_date.isoformat(),
            "sourceType": entry.source_type,
            "reviewStatus": entry.review_status,
        },
    )
    db.commit()
    db.refresh(entry)
    return serialize_entry(entry)


@router.get("/{entry_id}", response_model=LogbookEntryResponse)
def get_logbook_entry(
    aircraft_id: str,
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogbookEntryResponse:
    get_visible_aircraft_or_404(db, current_user, aircraft_id)
    return serialize_entry(get_entry_or_404(db, aircraft_id, entry_id))


@router.patch("/{entry_id}", response_model=LogbookEntryResponse)
def update_logbook_entry(
    aircraft_id: str,
    entry_id: str,
    payload: LogbookEntryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogbookEntryResponse:
    get_visible_aircraft_or_404(db, current_user, aircraft_id)
    entry = get_entry_or_404(db, aircraft_id, entry_id)
    fields = payload.model_dump(exclude_unset=True)

    if "section" in fields and fields["section"] is not None:
        entry.logbook_section_id = get_section_by_key(db, fields["section"]).id
    if "entryDate" in fields and fields["entryDate"] is not None:
        entry.entry_date = fields["entryDate"]
    if "description" in fields and fields["description"] is not None:
        entry.description = fields["description"].strip()
    if "performerName" in fields:
        entry.performer_name = optional_str(fields["performerName"])
    if "performerCredential" in fields:
        entry.performer_credential = optional_str(fields["performerCredential"])
    if "tachTime" in fields:
        entry.tach_time = fields["tachTime"]
    if "hobbsTime" in fields:
        entry.hobbs_time = fields["hobbsTime"]
    if "totalTime" in fields:
        entry.total_time = fields["totalTime"]
    if "reviewStatus" in fields and fields["reviewStatus"] is not None:
        entry.review_status = fields["reviewStatus"]

    db.commit()
    db.refresh(entry)
    return serialize_entry(entry)
