from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import (
    ADComplianceEvent,
    ADComplianceRequirement,
    ADComplianceTrigger,
    AircraftADDueState,
    AircraftTimeState,
    InstalledComponent,
    LogbookEntry,
    LogbookSection,
)
from app.services.ad_recurrence import (
    compute_due_state,
    materialize_requirements_from_extraction,
    sync_verified_time_states,
    upsert_verified_compliance_event,
)
from tests.test_ad_matching import create_approved_extraction


def test_calendar_recurring_requirement_calculates_current_due_soon_and_overdue(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    requirement, component = setup_requirement(
        db_session,
        intervals=["Every 6 calendar months"],
    )
    event_entry = verified_entry(
        db_session,
        demo_data,
        entry_date=date(2026, 1, 15),
        text="Complied with AD 2026-88-01 by inspection.",
    )
    upsert_verified_compliance_event(
        db_session,
        requirement=requirement,
        aircraft_id=demo_data["aircraft"].id,
        component=component,
        entry=event_entry,
        action_text=event_entry.description,
    )

    current = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2026, 5, 1),
    )
    assert current.status == "current"
    assert current.due_date == date(2026, 7, 15)

    due_soon = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2026, 7, 1),
    )
    assert due_soon.status == "due_soon"

    overdue = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2026, 7, 16),
    )
    assert overdue.status == "overdue"


def test_usage_recurring_requirement_uses_verified_current_time(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    requirement, component = setup_requirement(
        db_session,
        intervals=[{"type": "tach_hours", "intervalHours": 100}],
    )
    event_entry = verified_entry(
        db_session,
        demo_data,
        entry_date=date(2026, 1, 1),
        text="Complied with AD 2026-88-01 by inspection.",
        tach=1000,
    )
    current_entry = verified_entry(
        db_session,
        demo_data,
        entry_date=date(2026, 2, 1),
        text="Routine inspection.",
        tach=1080,
    )
    sync_verified_time_states(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        entries=[event_entry, current_entry],
    )
    upsert_verified_compliance_event(
        db_session,
        requirement=requirement,
        aircraft_id=demo_data["aircraft"].id,
        component=component,
        entry=event_entry,
        action_text=event_entry.description,
    )

    state = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2026, 2, 1),
    )
    assert state.status == "current"
    assert state.due_metric == "tach_hours"
    assert state.due_value == 1100


def test_whichever_first_combination_uses_first_overdue_trigger(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    requirement, component = setup_requirement(
        db_session,
        intervals=[
            {
                "logic": "whichever_first",
                "triggers": [
                    {"type": "calendar_months", "intervalMonths": 12},
                    {"type": "tach_hours", "intervalHours": 100},
                ],
            }
        ],
    )
    event_entry = verified_entry(
        db_session,
        demo_data,
        entry_date=date(2026, 1, 1),
        text="Complied with AD 2026-88-01 by inspection.",
        tach=1000,
    )
    current_entry = verified_entry(
        db_session,
        demo_data,
        entry_date=date(2026, 4, 1),
        text="Routine inspection.",
        tach=1101,
    )
    sync_verified_time_states(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        entries=[event_entry, current_entry],
    )
    upsert_verified_compliance_event(
        db_session,
        requirement=requirement,
        aircraft_id=demo_data["aircraft"].id,
        component=component,
        entry=event_entry,
        action_text=event_entry.description,
    )

    state = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2026, 4, 1),
    )
    assert requirement.combination_logic == "whichever_first"
    assert state.status == "overdue"
    assert {item["metric"] for item in state.trigger_states} == {
        "calendar",
        "tach_hours",
    }


def test_terminating_action_closes_recurrence(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    requirement, component = setup_requirement(
        db_session,
        intervals=["Every 6 months"],
    )
    entry = verified_entry(
        db_session,
        demo_data,
        entry_date=date(2026, 3, 1),
        text="Terminating modification completed for AD 2026-88-01.",
    )
    upsert_verified_compliance_event(
        db_session,
        requirement=requirement,
        aircraft_id=demo_data["aircraft"].id,
        component=component,
        entry=entry,
        action_text=entry.description,
        is_terminating_action=True,
    )

    state = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2030, 1, 1),
    )
    assert state.status == "terminated"


def test_missing_current_measurement_remains_unknown(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    requirement, component = setup_requirement(
        db_session,
        intervals=[{"type": "tach_hours", "intervalHours": 100}],
    )
    event_entry = verified_entry(
        db_session,
        demo_data,
        entry_date=date(2026, 1, 1),
        text="Complied with AD 2026-88-01 by inspection.",
        tach=1000,
    )
    upsert_verified_compliance_event(
        db_session,
        requirement=requirement,
        aircraft_id=demo_data["aircraft"].id,
        component=component,
        entry=event_entry,
        action_text=event_entry.description,
    )

    state = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2026, 2, 1),
    )
    assert state.status == "unknown"
    assert "current_tach_hours_missing" in state.unresolved_reasons


def test_interval_without_explicit_recurrence_language_requires_adjudication(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    requirement, _ = setup_requirement(
        db_session,
        intervals=["Within 100 flight hours after the effective date"],
    )

    assert requirement.review_status == "needs_adjudication"
    assert "recurrence_semantics_uncertain" in requirement.source_payload["parseReasons"]


def test_requirement_event_time_and_due_replays_are_idempotent_and_related(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="fixture-2026-88-02",
        ad_number="2026-88-02",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect every 50 tach hours."],
        compliance_intervals=[{"type": "tach_hours", "intervalHours": 50}],
    )
    first = materialize_requirements_from_extraction(db_session, extraction)
    second = materialize_requirements_from_extraction(db_session, extraction)
    assert [item.id for item in first] == [item.id for item in second]
    requirement = first[0]
    component = db_session.scalar(
        select(InstalledComponent).where(
            InstalledComponent.aircraft_id == demo_data["aircraft"].id,
            InstalledComponent.role == "airframe",
        )
    )
    entry = verified_entry(
        db_session,
        demo_data,
        entry_date=date(2026, 1, 1),
        text="Complied with AD 2026-88-02 by inspection.",
        tach=500,
    )
    sync_verified_time_states(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        entries=[entry],
    )
    first_event = upsert_verified_compliance_event(
        db_session,
        requirement=requirement,
        aircraft_id=demo_data["aircraft"].id,
        component=component,
        entry=entry,
        action_text=entry.description,
    )
    second_event = upsert_verified_compliance_event(
        db_session,
        requirement=requirement,
        aircraft_id=demo_data["aircraft"].id,
        component=component,
        entry=entry,
        action_text=entry.description,
    )
    first_due = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2026, 1, 1),
    )
    second_due = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=requirement,
        component=component,
        as_of_date=date(2026, 1, 1),
    )

    assert first_event.id == second_event.id
    assert first_due.id == second_due.id
    assert first_due.aircraft_id == demo_data["aircraft"].id
    assert first_due.requirement.directive_id == extraction.directive_id
    assert first_due.installed_component_id == component.id
    assert db_session.scalar(select(func.count(ADComplianceRequirement.id))) == 1
    assert db_session.scalar(select(func.count(ADComplianceTrigger.id))) == 1
    assert db_session.scalar(select(func.count(ADComplianceEvent.id))) == 1
    assert db_session.scalar(select(func.count(AircraftTimeState.id))) == 1
    assert db_session.scalar(select(func.count(AircraftADDueState.id))) == 1


def setup_requirement(
    db: Session,
    *,
    intervals: list,
) -> tuple[ADComplianceRequirement, InstalledComponent]:
    extraction = create_approved_extraction(
        db,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="fixture-2026-88-01",
        ad_number="2026-88-01",
        affected_products=["Cessna 172R"],
        compliance_actions=["Perform the required inspection."],
        compliance_intervals=intervals,
    )
    requirement = materialize_requirements_from_extraction(db, extraction)[0]
    component = db.scalar(
        select(InstalledComponent).where(InstalledComponent.role == "airframe")
    )
    assert component is not None
    return requirement, component


def verified_entry(
    db: Session,
    demo_data: dict[str, object],
    *,
    entry_date: date,
    text: str,
    tach: float | None = None,
) -> LogbookEntry:
    section = db.scalar(select(LogbookSection).where(LogbookSection.key == "airframe"))
    entry = LogbookEntry(
        aircraft_id=demo_data["aircraft"].id,
        logbook_section_id=section.id,
        entry_date=entry_date,
        description=text,
        raw_text=text,
        source_type="ocr_ingestion",
        created_by_user_id=demo_data["owner_user"].id,
        review_status="verified",
        tach_time=tach,
    )
    db.add(entry)
    db.flush()
    return entry
