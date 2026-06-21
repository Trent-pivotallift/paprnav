from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Aircraft, InstalledComponent

ROLE_AIRFRAME = "airframe"
ROLE_ENGINE = "engine"
ROLE_PROPELLER = "propeller"
ROLE_ROTORCRAFT_AIRFRAME = "rotorcraft_airframe"
ROLE_ROTOR_SYSTEM = "rotor_system"
ROLE_DRIVETRAIN_TRANSMISSION = "drivetrain_transmission"
ROLE_APPLIANCE = "appliance"
ROLE_UNKNOWN = "unknown"
ROLE_OTHER = "other"


@dataclass(frozen=True)
class ComponentFact:
    role: str
    component_type: str
    make: str | None
    model: str | None
    serial_number: str | None


def sync_installed_components_from_aircraft(db: Session, aircraft: Aircraft) -> list[InstalledComponent]:
    components = [
        ComponentFact(
            role=ROLE_AIRFRAME,
            component_type="aircraft",
            make=aircraft.make,
            model=aircraft.model,
            serial_number=aircraft.airframe_serial_number or aircraft.serial_number,
        )
    ]
    if aircraft.engine_make or aircraft.engine_model or aircraft.engine_serial_number:
        components.append(
            ComponentFact(
                role=ROLE_ENGINE,
                component_type="engine",
                make=aircraft.engine_make,
                model=aircraft.engine_model,
                serial_number=aircraft.engine_serial_number,
            )
        )
    if aircraft.propeller_make or aircraft.propeller_model or aircraft.propeller_serial_number:
        components.append(
            ComponentFact(
                role=ROLE_PROPELLER,
                component_type="propeller",
                make=aircraft.propeller_make,
                model=aircraft.propeller_model,
                serial_number=aircraft.propeller_serial_number,
            )
        )

    synced: list[InstalledComponent] = []
    for fact in components:
        component = db.scalar(
            select(InstalledComponent).where(
                InstalledComponent.aircraft_id == aircraft.id,
                InstalledComponent.role == fact.role,
                InstalledComponent.source == "aircraft_facts",
            )
        )
        if component is None:
            component = InstalledComponent(
                aircraft_id=aircraft.id,
                role=fact.role,
                component_type=fact.component_type,
                source="aircraft_facts",
                confidence=0.86,
            )
            db.add(component)
        component.component_type = fact.component_type
        component.make = fact.make
        component.model = fact.model
        component.serial_number = fact.serial_number
        component.removed_at = None
        synced.append(component)
    db.flush()
    return synced


def component_display_name(component: InstalledComponent | None) -> str | None:
    if component is None:
        return None
    parts = [component.make, component.model]
    name = " ".join(part for part in parts if part)
    return name or component.component_type or component.role
