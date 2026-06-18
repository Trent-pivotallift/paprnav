from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.core import (
    Aircraft,
    AircraftAssignment,
    LogbookEntry,
    LogbookSection,
    Organization,
    OrganizationMembership,
    User,
)

DEV_PASSWORD = "demo-password"


def get_or_create_user(db: Session, email: str, name: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.name = name
        user.status = "active"
        if not user.password_hash.startswith("pbkdf2_sha256$"):
            user.password_hash = hash_password(DEV_PASSWORD)
        return user

    user = User(
        email=email,
        name=name,
        password_hash=hash_password(DEV_PASSWORD),
        status="active",
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_organization(db: Session, name: str, org_type: str) -> Organization:
    organization = db.scalar(select(Organization).where(Organization.name == name))
    if organization:
        organization.type = org_type
        return organization

    organization = Organization(name=name, type=org_type)
    db.add(organization)
    db.flush()
    return organization


def get_or_create_membership(db: Session, organization: Organization, user: User, role: str) -> OrganizationMembership:
    membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization.id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if membership:
        membership.role = role
        membership.status = "active"
        return membership

    membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=user.id,
        role=role,
        status="active",
    )
    db.add(membership)
    db.flush()
    return membership


def get_or_create_section(db: Session, key: str, name: str, sort_order: int) -> LogbookSection:
    section = db.scalar(select(LogbookSection).where(LogbookSection.key == key))
    if section:
        section.name = name
        section.sort_order = sort_order
        return section

    section = LogbookSection(key=key, name=name, sort_order=sort_order)
    db.add(section)
    db.flush()
    return section


def get_or_create_aircraft(
    db: Session,
    owner: Organization,
    created_by: User,
    n_number: str,
    make: str,
    model: str,
    serial_number: str,
) -> Aircraft:
    normalized = n_number.upper().replace("-", "").replace(" ", "")
    aircraft = db.scalar(select(Aircraft).where(Aircraft.n_number_normalized == normalized))
    if aircraft:
        aircraft.owner_organization_id = owner.id
        aircraft.make = make
        aircraft.model = model
        aircraft.serial_number = serial_number
        aircraft.status = "active"
        return aircraft

    aircraft = Aircraft(
        owner_organization_id=owner.id,
        n_number_raw=n_number,
        n_number_normalized=normalized,
        make=make,
        model=model,
        serial_number=serial_number,
        year=2003,
        status="active",
        created_by_user_id=created_by.id,
        airframe_serial_number=serial_number,
        engine_make="Lycoming",
        engine_model="IO-360-L2A",
        engine_serial_number="L-12345-51A",
        propeller_make="McCauley",
        propeller_model="1A170",
        propeller_serial_number="P-54321",
    )
    db.add(aircraft)
    db.flush()
    return aircraft


def get_or_create_assignment(
    db: Session,
    aircraft: Aircraft,
    organization: Organization,
    assigned_by: User,
    role: str,
) -> AircraftAssignment:
    assignment = db.scalar(
        select(AircraftAssignment).where(
            AircraftAssignment.aircraft_id == aircraft.id,
            AircraftAssignment.organization_id == organization.id,
        )
    )
    if assignment:
        assignment.assigned_by_user_id = assigned_by.id
        assignment.role = role
        assignment.status = "active"
        return assignment

    assignment = AircraftAssignment(
        aircraft_id=aircraft.id,
        organization_id=organization.id,
        assigned_by_user_id=assigned_by.id,
        role=role,
        status="active",
    )
    db.add(assignment)
    db.flush()
    return assignment


def get_or_create_entry(
    db: Session,
    aircraft: Aircraft,
    section: LogbookSection,
    created_by: User,
    entry_date: date,
    description: str,
    performer_name: str,
    performer_credential: str,
    tach_time: float,
) -> LogbookEntry:
    entry = db.scalar(
        select(LogbookEntry).where(
            LogbookEntry.aircraft_id == aircraft.id,
            LogbookEntry.logbook_section_id == section.id,
            LogbookEntry.entry_date == entry_date,
            LogbookEntry.description == description,
        )
    )
    if entry:
        entry.performer_name = performer_name
        entry.performer_credential = performer_credential
        entry.tach_time = tach_time
        entry.review_status = "verified"
        return entry

    entry = LogbookEntry(
        aircraft_id=aircraft.id,
        logbook_section_id=section.id,
        entry_date=entry_date,
        description=description,
        performer_name=performer_name,
        performer_credential=performer_credential,
        source_type="manual",
        created_by_user_id=created_by.id,
        tach_time=tach_time,
        hobbs_time=tach_time + 12.4,
        total_time=3200.0 + tach_time,
        raw_text=None,
        review_status="verified",
    )
    db.add(entry)
    db.flush()
    return entry


def seed(db: Session) -> None:
    owner_user = get_or_create_user(db, "owner.demo@paprnav.local", "Olivia Owner")
    maintenance_user = get_or_create_user(db, "shop.demo@paprnav.local", "Miles Mechanic")

    owner_org = get_or_create_organization(db, "Demo Owner Hangar", "owner")
    shop_org = get_or_create_organization(db, "Demo Maintenance Shop", "maintenance_shop")

    get_or_create_membership(db, owner_org, owner_user, "owner_admin")
    get_or_create_membership(db, shop_org, maintenance_user, "maintenance_admin")

    airframe = get_or_create_section(db, "airframe", "Airframe", 1)
    engine = get_or_create_section(db, "engine", "Engine", 2)
    propeller = get_or_create_section(db, "propeller", "Propeller", 3)

    aircraft = get_or_create_aircraft(
        db=db,
        owner=owner_org,
        created_by=owner_user,
        n_number="N123AB",
        make="Cessna",
        model="172R",
        serial_number="17280001",
    )
    get_or_create_assignment(db, aircraft, shop_org, owner_user, "maintainer")

    get_or_create_entry(
        db,
        aircraft,
        airframe,
        owner_user,
        date(2026, 1, 15),
        "Annual inspection completed in accordance with 14 CFR Part 43 Appendix D.",
        "A. Mechanic",
        "A&P IA",
        1022.4,
    )
    get_or_create_entry(
        db,
        aircraft,
        engine,
        owner_user,
        date(2026, 2, 12),
        "Changed engine oil and filter; inspected screen with no defects noted.",
        "M. Mechanic",
        "A&P",
        1035.8,
    )
    get_or_create_entry(
        db,
        aircraft,
        propeller,
        maintenance_user,
        date(2026, 3, 4),
        "Propeller visual inspection completed; no nicks, cracks, or corrosion found.",
        "M. Mechanic",
        "A&P",
        1041.2,
    )


def main() -> None:
    with SessionLocal() as db:
        seed(db)
        db.commit()

        counts = {
            "users": db.scalar(select(func.count()).select_from(User)),
            "organizations": db.scalar(select(func.count()).select_from(Organization)),
            "aircraft": db.scalar(select(func.count()).select_from(Aircraft)),
            "logbook_sections": db.scalar(select(func.count()).select_from(LogbookSection)),
            "logbook_entries": db.scalar(select(func.count()).select_from(LogbookEntry)),
        }

    print("Seeded demo users, organizations, aircraft, sections, assignment, and logbook entries.")
    print(counts)


if __name__ == "__main__":
    main()
