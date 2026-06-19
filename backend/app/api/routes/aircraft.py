from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.core import Aircraft, AircraftAssignment, LogbookEntry, OrganizationMembership, User
from app.schemas.aircraft import (
    AircraftAssignmentCreateRequest,
    AircraftAssignmentListResponse,
    AircraftAssignmentResponse,
    AircraftCreateRequest,
    AircraftListResponse,
    AircraftResponse,
    AircraftUpdateRequest,
)

router = APIRouter(prefix="/api/v1/aircraft", tags=["aircraft"])


def normalize_n_number(n_number: str) -> str:
    return n_number.strip().upper().replace("-", "").replace(" ", "")


def active_memberships(user: User) -> list[OrganizationMembership]:
    return [membership for membership in user.memberships if membership.status == "active"]


def active_organization_ids(user: User) -> list[str]:
    return [membership.organization_id for membership in active_memberships(user)]


def owner_memberships(user: User) -> list[OrganizationMembership]:
    return [
        membership
        for membership in active_memberships(user)
        if membership.organization.type == "owner" or membership.role.startswith("owner_")
    ]


def visible_aircraft_statement(user: User):
    organization_ids = active_organization_ids(user)
    if not organization_ids:
        return select(Aircraft).where(False)

    assigned_aircraft = select(AircraftAssignment.aircraft_id).where(
        AircraftAssignment.organization_id.in_(organization_ids),
        AircraftAssignment.status == "active",
    )
    return (
        select(Aircraft)
        .where(
            Aircraft.status == "active",
            or_(
                Aircraft.owner_organization_id.in_(organization_ids),
                Aircraft.id.in_(assigned_aircraft),
            ),
        )
        .order_by(Aircraft.n_number_normalized)
    )


def get_visible_aircraft_or_404(db: Session, user: User, aircraft_id: str) -> Aircraft:
    aircraft = db.scalar(visible_aircraft_statement(user).where(Aircraft.id == aircraft_id))
    if not aircraft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aircraft not found")
    return aircraft


def ensure_owner_access(aircraft: Aircraft, user: User) -> None:
    owner_org_ids = {membership.organization_id for membership in owner_memberships(user)}
    if aircraft.owner_organization_id not in owner_org_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")


def serialize_aircraft(db: Session, aircraft: Aircraft) -> AircraftResponse:
    last_log_entry_date = db.scalar(
        select(func.max(LogbookEntry.entry_date)).where(LogbookEntry.aircraft_id == aircraft.id)
    )
    return AircraftResponse(
        id=aircraft.id,
        nNumber=aircraft.n_number_raw,
        nNumberNormalized=aircraft.n_number_normalized,
        make=aircraft.make,
        model=aircraft.model,
        serialNumber=aircraft.serial_number,
        year=aircraft.year,
        airframeSerialNumber=aircraft.airframe_serial_number,
        engineMake=aircraft.engine_make,
        engineModel=aircraft.engine_model,
        engineSerialNumber=aircraft.engine_serial_number,
        propellerMake=aircraft.propeller_make,
        propellerModel=aircraft.propeller_model,
        propellerSerialNumber=aircraft.propeller_serial_number,
        lastLogEntryDate=last_log_entry_date,
        complianceStatus="needs_review",
    )


def serialize_assignment(assignment: AircraftAssignment) -> AircraftAssignmentResponse:
    return AircraftAssignmentResponse(
        id=assignment.id,
        aircraftId=assignment.aircraft_id,
        organizationId=assignment.organization_id,
        organizationName=assignment.organization.name,
        organizationType=assignment.organization.type,
        role=assignment.role,
        status=assignment.status,
    )


def maintenance_memberships_for_user(user: User) -> list[OrganizationMembership]:
    return [
        membership
        for membership in active_memberships(user)
        if membership.organization.type == "maintenance_shop" or membership.role.startswith("maintenance_")
    ]


def apply_aircraft_fields(aircraft: Aircraft, payload: AircraftCreateRequest | AircraftUpdateRequest) -> None:
    fields = payload.model_dump(exclude_unset=True)
    if "nNumber" in fields:
        aircraft.n_number_raw = fields["nNumber"].strip().upper()
        aircraft.n_number_normalized = normalize_n_number(fields["nNumber"])
    if "make" in fields:
        aircraft.make = fields["make"].strip()
    if "model" in fields:
        aircraft.model = fields["model"].strip()
    if "serialNumber" in fields:
        aircraft.serial_number = optional_str(fields["serialNumber"])
    if "year" in fields:
        aircraft.year = fields["year"]
    if "airframeSerialNumber" in fields:
        aircraft.airframe_serial_number = optional_str(fields["airframeSerialNumber"])
    if "engineMake" in fields:
        aircraft.engine_make = optional_str(fields["engineMake"])
    if "engineModel" in fields:
        aircraft.engine_model = optional_str(fields["engineModel"])
    if "engineSerialNumber" in fields:
        aircraft.engine_serial_number = optional_str(fields["engineSerialNumber"])
    if "propellerMake" in fields:
        aircraft.propeller_make = optional_str(fields["propellerMake"])
    if "propellerModel" in fields:
        aircraft.propeller_model = optional_str(fields["propellerModel"])
    if "propellerSerialNumber" in fields:
        aircraft.propeller_serial_number = optional_str(fields["propellerSerialNumber"])


def optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@router.get("", response_model=AircraftListResponse)
def list_aircraft(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AircraftListResponse:
    aircraft = db.scalars(visible_aircraft_statement(current_user)).all()
    return AircraftListResponse(aircraft=[serialize_aircraft(db, item) for item in aircraft])


@router.post("", response_model=AircraftResponse, status_code=status.HTTP_201_CREATED)
def create_aircraft(
    payload: AircraftCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AircraftResponse:
    owner_membership = next(iter(owner_memberships(current_user)), None)
    if owner_membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")

    normalized_n_number = normalize_n_number(payload.nNumber)
    existing_aircraft = db.scalar(select(Aircraft).where(Aircraft.n_number_normalized == normalized_n_number))
    if existing_aircraft:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Aircraft N-number already exists")

    aircraft = Aircraft(
        owner_organization_id=owner_membership.organization_id,
        n_number_raw=payload.nNumber.strip().upper(),
        n_number_normalized=normalized_n_number,
        make=payload.make.strip(),
        model=payload.model.strip(),
        serial_number=optional_str(payload.serialNumber),
        year=payload.year,
        status="active",
        created_by_user_id=current_user.id,
        airframe_serial_number=optional_str(payload.airframeSerialNumber or payload.serialNumber),
        engine_make=optional_str(payload.engineMake),
        engine_model=optional_str(payload.engineModel),
        engine_serial_number=optional_str(payload.engineSerialNumber),
        propeller_make=optional_str(payload.propellerMake),
        propeller_model=optional_str(payload.propellerModel),
        propeller_serial_number=optional_str(payload.propellerSerialNumber),
    )
    db.add(aircraft)
    db.commit()
    db.refresh(aircraft)
    return serialize_aircraft(db, aircraft)


@router.get("/{aircraft_id}", response_model=AircraftResponse)
def get_aircraft(
    aircraft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AircraftResponse:
    aircraft = get_visible_aircraft_or_404(db, current_user, aircraft_id)
    return serialize_aircraft(db, aircraft)


@router.patch("/{aircraft_id}", response_model=AircraftResponse)
def update_aircraft(
    aircraft_id: str,
    payload: AircraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AircraftResponse:
    aircraft = get_visible_aircraft_or_404(db, current_user, aircraft_id)
    ensure_owner_access(aircraft, current_user)

    if payload.nNumber is not None:
        normalized_n_number = normalize_n_number(payload.nNumber)
        existing_aircraft = db.scalar(select(Aircraft).where(Aircraft.n_number_normalized == normalized_n_number))
        if existing_aircraft and existing_aircraft.id != aircraft.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Aircraft N-number already exists")

    apply_aircraft_fields(aircraft, payload)
    db.commit()
    db.refresh(aircraft)
    return serialize_aircraft(db, aircraft)


@router.get("/{aircraft_id}/assignments", response_model=AircraftAssignmentListResponse)
def list_aircraft_assignments(
    aircraft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AircraftAssignmentListResponse:
    aircraft = get_visible_aircraft_or_404(db, current_user, aircraft_id)
    ensure_owner_access(aircraft, current_user)

    assignments = db.scalars(
        select(AircraftAssignment)
        .where(AircraftAssignment.aircraft_id == aircraft_id, AircraftAssignment.status == "active")
        .order_by(AircraftAssignment.created_at)
    ).all()
    return AircraftAssignmentListResponse(assignments=[serialize_assignment(assignment) for assignment in assignments])


@router.post("/{aircraft_id}/assignments", response_model=AircraftAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_aircraft_assignment(
    aircraft_id: str,
    payload: AircraftAssignmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AircraftAssignmentResponse:
    aircraft = get_visible_aircraft_or_404(db, current_user, aircraft_id)
    ensure_owner_access(aircraft, current_user)

    maintenance_user = db.scalar(select(User).where(User.email == payload.maintenanceUserEmail.strip().lower()))
    if not maintenance_user or maintenance_user.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance user not found")

    maintenance_membership = next(iter(maintenance_memberships_for_user(maintenance_user)), None)
    if maintenance_membership is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not in a maintenance organization")

    assignment = db.scalar(
        select(AircraftAssignment).where(
            AircraftAssignment.aircraft_id == aircraft_id,
            AircraftAssignment.organization_id == maintenance_membership.organization_id,
        )
    )
    if assignment:
        assignment.assigned_by_user_id = current_user.id
        assignment.role = payload.role.strip()
        assignment.status = "active"
    else:
        assignment = AircraftAssignment(
            aircraft_id=aircraft_id,
            organization_id=maintenance_membership.organization_id,
            assigned_by_user_id=current_user.id,
            role=payload.role.strip(),
            status="active",
        )
        db.add(assignment)

    db.commit()
    db.refresh(assignment)
    return serialize_assignment(assignment)
