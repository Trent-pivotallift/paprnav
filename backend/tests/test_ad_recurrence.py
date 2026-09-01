from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.core import (
    ADAMOCProvision,
    ADComplianceEvent,
    ADComplianceRequirement,
    ADComplianceTrigger,
    ADExtractionReview,
    ADMatchDueStateLink,
    ADMatchResult,
    ADTargetApplicability,
    AircraftADDueState,
    AircraftTimeState,
    InstalledComponent,
    LogbookEntry,
    LogbookSection,
)
from app.services.ad_recurrence import (
    combine_trigger_statuses,
    compute_due_state,
    materialize_amoc_provisions,
    materialize_requirements_from_extraction,
    latest_time_state,
    normalize_logic,
    sync_verified_time_states,
    upsert_verified_compliance_event,
)
from app.services.ad_applicability import populate_applicability_from_extraction, upsert_target_applicability
from app.services.ad_extraction import ensure_review_for_extraction
from app.services import ad_matching
from app.services.ad_matching import match_aircraft_ads, upsert_match_result
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


def test_v2_page_cited_requirements_materialize_separately(db_session: Session) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="fixture-v2-2026-88-01",
        ad_number="2026-88-01",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect and replace as required."],
        compliance_intervals=[],
    )
    extraction.schema_version = "ad_extraction_v2"
    extraction.output["requirements"] = [
        {
            "requirementKey": "inspection",
            "requirementType": "recurring",
            "actionText": "Inspect the affected part.",
            "initialThresholds": [],
            "recurringTriggers": [{"metric": "tach_hours", "value": 100, "unit": "hours", "anchorKind": "last_compliance", "sourceText": "every 100 hours"}],
            "combinationLogic": "all",
            "conditions": [],
            "terminatingAction": None,
            "citations": [{"sourceDocumentId": "asd_fixture", "pageNumber": 4, "text": "Thereafter at intervals not to exceed 100 hours."}],
            "confidence": 0.94,
            "uncertaintyReasons": [],
        },
        {
            "requirementKey": "replacement",
            "requirementType": "one_time",
            "actionText": "Replace any cracked part.",
            "initialThresholds": [],
            "recurringTriggers": [],
            "combinationLogic": "all",
            "conditions": [],
            "terminatingAction": "Install the improved part.",
            "citations": [{"sourceDocumentId": "asd_fixture", "pageNumber": 5, "text": "Before further flight, replace the cracked part."}],
            "confidence": 0.96,
            "uncertaintyReasons": [],
        },
    ]

    requirements = materialize_requirements_from_extraction(db_session, extraction)

    assert len(requirements) == 2
    assert {item.source_payload["requirementKey"] for item in requirements} == {"inspection", "replacement"}
    assert all(item.review_status == "approved" for item in requirements)
    assert sum(len(item.triggers) for item in requirements) == 1


def test_v3_requirements_materialize_only_for_declared_applicability_groups(db_session: Session) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna Airplanes",
        document_number="fixture-v3-2026-88-02",
        ad_number="2026-88-02",
        affected_products=["Cessna 172R"],
        compliance_actions=[],
        compliance_intervals=[],
    )
    extraction.schema_version = "ad_extraction_v3"
    extraction.output["applicabilityGroups"] = [
        v3_group("cessna-172r", "Cessna", "172R"),
        v3_group("piper-pa-28", "Piper", "PA-28-140"),
    ]
    extraction.output["requirements"] = [
        v3_requirement("cessna-inspection", "cessna-172r"),
        v3_requirement("piper-inspection", "piper-pa-28"),
    ]
    extraction.output["requirements"][0]["actionText"] = "Inspect the Cessna seat rail."
    extraction.output["requirements"][1]["actionText"] = "Inspect the Piper seat rail."

    populate_applicability_from_extraction(db_session, extraction)
    requirements = materialize_requirements_from_extraction(db_session, extraction)

    assert len(requirements) == 2
    assert {
        (item.source_payload["requirementKey"], item.target_applicability.applicability_group_key)
        for item in requirements
    } == {
        ("cessna-inspection", "cessna-172r"),
        ("piper-inspection", "piper-pa-28"),
    }
    current_rows = db_session.scalars(
        select(ADTargetApplicability).where(ADTargetApplicability.status == "current")
    ).all()
    assert {row.applicability_group_key for row in current_rows} == {
        "cessna-172r",
        "piper-pa-28",
    }
    cessa_row = next(row for row in current_rows if row.applicability_group_key == "cessna-172r")
    assert cessa_row.source_identity["manufacturer"]["sourceName"] == "Cessna"
    assert cessa_row.source_identity["model"]["sourceDesignation"] == "172R"
    assert cessa_row.compliance_actions == ["Inspect the Cessna seat rail."]
    piper_row = next(row for row in current_rows if row.applicability_group_key == "piper-pa-28")
    assert piper_row.compliance_actions == ["Inspect the Piper seat rail."]


def test_match_replays_every_requirement_for_selected_applicability(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna Airplanes",
        document_number="fixture-v3-multi-obligation",
        ad_number="2026-88-22",
        affected_products=["Cessna 172R"],
        compliance_actions=[],
        compliance_intervals=[],
    )
    extraction.schema_version = "ad_extraction_v3"
    extraction.output["applicabilityGroups"] = [
        v3_group("cessna-172r", "Cessna", "172R")
    ]
    extraction.output["requirements"] = [
        v3_requirement("inspect-left-rail", "cessna-172r"),
        v3_requirement("inspect-right-rail", "cessna-172r"),
    ]
    extraction.output["requirements"][0]["actionText"] = "Inspect the left seat rail."
    extraction.output["requirements"][1]["actionText"] = "Inspect the right seat rail."
    populate_applicability_from_extraction(db_session, extraction)
    applicability = db_session.scalar(
        select(ADTargetApplicability).where(
            ADTargetApplicability.source_extraction_id == extraction.id,
            ADTargetApplicability.status == "current",
        )
    )
    component = db_session.scalar(
        select(InstalledComponent).where(InstalledComponent.role == "airframe")
    )
    assert applicability is not None
    assert component is not None

    result = upsert_match_result(
        db_session,
        demo_data["aircraft"],
        [],
        extraction,
        installed_component=component,
        target_applicability=applicability,
        structured_entries={},
    )

    links = db_session.scalars(
        select(ADMatchDueStateLink).where(
            ADMatchDueStateLink.match_result_id == result.id
        )
    ).all()
    assert result.match_type == "multi_obligation"
    assert result.due_state_id is None
    assert len(links) == 2
    assert {link.due_state.requirement.source_payload["requirementKey"] for link in links} == {
        "inspect-left-rail",
        "inspect-right-rail",
    }


def test_match_replays_obligations_for_every_applicable_component_group(
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch,
) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Engine and Propeller Assemblies",
        document_number="fixture-v3-multi-component",
        ad_number="2026-88-23",
        affected_products=["Lycoming IO-360-L2A", "McCauley 1A170"],
        compliance_actions=[],
        compliance_intervals=[],
    )
    extraction.schema_version = "ad_extraction_v3"
    engine_group = v3_group("lycoming-engine", "Lycoming", "IO-360-L2A")
    engine_group["productType"] = "engine"
    propeller_group = v3_group("mccauley-propeller", "McCauley", "1A170")
    propeller_group["productType"] = "propeller"
    extraction.output = {
        **extraction.output,
        "applicabilityGroups": [engine_group, propeller_group],
        "requirements": [
            v3_requirement("inspect-engine", "lycoming-engine"),
            v3_requirement("inspect-propeller", "mccauley-propeller"),
        ],
    }
    engine_section = db_session.scalar(
        select(LogbookSection).where(LogbookSection.key == "engine")
    )
    db_session.add(LogbookEntry(
        aircraft_id=demo_data["aircraft"].id,
        logbook_section_id=engine_section.id,
        entry_date=date(2026, 8, 1),
        description="Complied with AD 2026-88-23 by inspecting the engine.",
        raw_text="Complied with AD 2026-88-23 by inspecting the engine.",
        source_type="manual",
        review_status="verified",
        created_by_user_id=demo_data["owner_user"].id,
        reviewed_by_user_id=demo_data["shop_user"].id,
    ))
    populate_applicability_from_extraction(db_session, extraction)
    materialized = materialize_requirements_from_extraction(db_session, extraction)
    db_session.flush()
    engine_requirement = next(
        item for item in materialized
        if item.source_payload["requirementKey"] == "inspect-engine"
    )
    engine_requirement.action_text = "Tampered out-of-band action"
    engine_requirement.combination_logic = "whichever_later"
    materialize_requirements_from_extraction(db_session, extraction)
    db_session.flush()
    assert engine_requirement.action_text == "Inspect the affected part."
    assert engine_requirement.combination_logic == "all"
    db_session.expire(extraction.directive, ["target_applicabilities"])
    monkeypatch.setattr(
        ad_matching,
        "approved_current_extractions",
        lambda _db: [extraction],
    )
    contexts = ad_matching.select_applicable_components(
        demo_data["aircraft"],
        extraction,
    )
    assert {component.role for component, _applicability in contexts} == {
        "engine",
        "propeller",
    }

    first_stats = match_aircraft_ads(db_session, demo_data["aircraft"].id)
    first_results = db_session.scalars(
        select(ADMatchResult).where(
            ADMatchResult.directive_id == extraction.directive_id,
            ADMatchResult.is_current.is_(True),
        )
    ).all()
    assert first_stats["matched"] == 1
    assert first_stats["unresolved"] == 1
    assert len(first_results) == 2
    assert {result.installed_component.role for result in first_results} == {
        "engine",
        "propeller",
    }
    assert {
        link.due_state.requirement.source_payload["requirementKey"]
        for result in first_results
        for link in result.due_state_links
    } == {"inspect-engine", "inspect-propeller"}
    events = db_session.scalars(
        select(ADComplianceEvent).where(
            ADComplianceEvent.requirement_id.in_([
                link.due_state.requirement_id
                for result in first_results
                for link in result.due_state_links
            ])
        )
    ).all()
    assert {event.installed_component.role for event in events} == {"engine"}
    propeller_result = next(
        result for result in first_results
        if result.installed_component.role == "propeller"
    )
    assert "component_requirement_evidence_unbound" in propeller_result.unresolved_reasons

    second_stats = match_aircraft_ads(db_session, demo_data["aircraft"].id)
    second_results = db_session.scalars(
        select(ADMatchResult).where(
            ADMatchResult.directive_id == extraction.directive_id,
            ADMatchResult.is_current.is_(True),
        )
    ).all()
    assert second_stats["matched"] == 1
    assert second_stats["unresolved"] == 1
    assert {result.id for result in second_results} == {
        result.id for result in first_results
    }

    propeller_applicability = next(
        result.target_applicability
        for result in second_results
        if result.installed_component.role == "propeller"
    )
    propeller_applicability.equipment_conditions = [{
        "conditionText": "Only when the unresolved optional governor is installed."
    }]
    db_session.commit()
    uncertain_stats = match_aircraft_ads(db_session, demo_data["aircraft"].id)
    uncertain_results = db_session.scalars(
        select(ADMatchResult).where(
            ADMatchResult.directive_id == extraction.directive_id,
            ADMatchResult.is_current.is_(True),
        )
    ).all()
    uncertain_propeller = next(
        result
        for result in uncertain_results
        if result.installed_component.role == "propeller"
    )
    uncertain_propeller_links = db_session.scalars(
        select(ADMatchDueStateLink).where(
            ADMatchDueStateLink.match_result_id == uncertain_propeller.id
        )
    ).all()
    assert uncertain_stats["matched"] == 1
    assert uncertain_stats["unresolved"] == 1
    assert "component_applicability_uncertain" in uncertain_propeller.unresolved_reasons
    assert uncertain_propeller_links == []


def test_v3_initial_and_recurring_anchors_are_preserved_and_replayed(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna Airplanes",
        document_number="fixture-v3-2026-88-03",
        ad_number="2026-88-03",
        affected_products=["Cessna 172R"],
        compliance_actions=[],
        compliance_intervals=[],
    )
    extraction.schema_version = "ad_extraction_v3"
    extraction.output["effectiveDate"] = "2026-01-01"
    extraction.output["applicabilityGroups"] = [v3_group("cessna  172r", "Cessna", "172R")]
    requirement = v3_requirement("seat-rail", "cessna 172r")
    requirement["requirementType"] = "recurring"
    requirement["initialThresholds"] = [{
        "metric": "calendar",
        "value": 12,
        "unit": "months",
        "anchorKind": "effective_date",
        "sourceText": "within 12 months after the effective date",
    }]
    requirement["recurringTriggers"] = [{
        "metric": "calendar",
        "value": 6,
        "unit": "months",
        "anchorKind": "last_compliance",
        "sourceText": "thereafter at intervals not to exceed 6 months",
    }]
    extraction.output["requirements"] = [requirement]
    extraction.output = {**extraction.output, "amocProvisions": [{
        "provisionKey": "paragraph-i",
        "authorityText": "The Manager has the authority to approve AMOCs for this AD.",
        "approvingAuthority": "Manager",
        "submissionInstructions": None,
        "conditions": [],
        "citations": [{"sourceDocumentId": "asd_fixture", "pageNumber": 9, "text": "The Manager has the authority to approve AMOCs for this AD."}],
        "confidence": 0.95,
        "uncertaintyReasons": [],
    }]}

    populate_applicability_from_extraction(db_session, extraction)
    materialized = materialize_requirements_from_extraction(db_session, extraction)

    assert len(materialized) == 1
    assert [(item.trigger_kind, item.anchor_kind) for item in materialized[0].triggers] == [
        ("initial", "effective_date"),
        ("recurring", "last_compliance"),
    ]
    state = compute_due_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        requirement=materialized[0],
        component=None,
        as_of_date=date(2026, 6, 1),
    )
    assert state.status == "current"
    assert state.due_date == date(2027, 1, 1)
    amoc = db_session.scalar(select(ADAMOCProvision))
    assert amoc is not None
    assert amoc.approving_authority == "Manager"


def test_legacy_upsert_preserves_existing_serial_scope(db_session: Session) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="fixture-v2-serial-preservation",
        ad_number="2026-88-04",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect the affected part."],
        compliance_intervals=[],
    )
    populate_applicability_from_extraction(db_session, extraction)
    row = db_session.scalar(
        select(ADTargetApplicability).where(
            ADTargetApplicability.directive_id == extraction.directive_id,
            ADTargetApplicability.status == "current",
        )
    )
    assert row is not None
    row.serial_range = {"kind": "values", "values": ["17280001"]}
    db_session.flush()

    upsert_target_applicability(
        db_session,
        directive=extraction.directive,
        target=row.target,
        source_publication=None,
        basis="extraction",
        compliance_actions=["Inspect the affected part."],
    )

    assert row.serial_range == {"kind": "values", "values": ["17280001"]}


def test_null_safe_applicability_identity_is_database_enforced(db_session: Session) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="fixture-v2-null-safe-identity",
        ad_number="2026-88-05",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect the affected part."],
        compliance_intervals=[],
    )
    populate_applicability_from_extraction(db_session, extraction)
    existing = db_session.scalar(
        select(ADTargetApplicability).where(
            ADTargetApplicability.directive_id == extraction.directive_id,
            ADTargetApplicability.status == "current",
        )
    )
    assert existing is not None

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(ADTargetApplicability(
                directive_id=existing.directive_id,
                target_id=existing.target_id,
                source_publication_id=None,
                applicability_basis=existing.applicability_basis,
                applicability_group_key=None,
                source_extraction_id=existing.source_extraction_id,
                confidence=0.8,
                status="current",
            ))
            db_session.flush()


def test_v3_approved_provider_row_without_human_decision_is_reopened(
    db_session: Session,
) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="fixture-v3-human-gate",
        ad_number="2026-88-06",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect the affected part."],
        compliance_intervals=[],
    )
    extraction.schema_version = "ad_extraction_v3"

    ensure_review_for_extraction(db_session, extraction.directive, extraction)

    assert extraction.status == "needs_review"
    assert extraction.directive.review_status == "pending"
    review = db_session.scalar(
        select(ADExtractionReview).where(
            ADExtractionReview.extraction_id == extraction.id
        )
    )
    assert review is not None
    assert review.status == "pending"


def test_v3_review_signature_mismatch_is_reopened_before_materialization(
    db_session: Session,
) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna 172R Airplanes",
        document_number="fixture-v3-review-integrity",
        ad_number="2026-88-08",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect the affected part."],
        compliance_intervals=[],
    )
    extraction.schema_version = "ad_extraction_v3"
    extraction.output = {
        **extraction.output,
        "applicabilityGroups": [v3_group("cessna-172r", "Cessna", "172R")],
        "requirements": [v3_requirement("inspection", "cessna-172r")],
        "amocProvisions": [],
    }
    reviewed_output = dict(extraction.output)
    review = ADExtractionReview(
        extraction_id=extraction.id,
        status="approved",
        decision="approved",
        proposed_output=reviewed_output,
        decision_output=reviewed_output,
    )
    db_session.add(review)
    db_session.flush()
    extraction.output = {**extraction.output, "title": "Out-of-band mutation"}

    ensure_review_for_extraction(db_session, extraction.directive, extraction)

    assert extraction.status == "needs_review"
    assert extraction.directive.review_status == "pending"
    assert review.status == "pending"
    assert review.decision_output is None
    assert review.reviewer_user_id is None
    assert len(extraction.raw_response["reviewIntegrityMismatches"]) == 1


def v3_group(group_key: str, manufacturer: str, model: str) -> dict:
    citation = {"sourceDocumentId": "asd_fixture", "pageNumber": 1, "text": f"{manufacturer} {model}"}
    return {
        "groupKey": group_key,
        "productType": "aircraft",
        "productSubtype": None,
        "manufacturer": {"sourceName": manufacturer, "normalizedName": None},
        "modelApplicability": {
            "kind": "listed",
            "models": [{"sourceDesignation": model, "normalizedDesignation": None, "aliases": []}],
            "sourceText": f"{manufacturer} {model}",
        },
        "serialNumberApplicability": {
            "kind": "all", "values": [], "ranges": [], "excludedValues": [], "sourceText": "all",
        },
        "equipmentCombinationLogic": "all",
        "equipmentConditions": [],
        "conditions": [],
        "citations": [citation],
        "confidence": 0.95,
        "uncertaintyReasons": [],
    }


def v3_requirement(requirement_key: str, group_key: str) -> dict:
    return {
        "requirementKey": requirement_key,
        "applicabilityGroupKeys": [group_key],
        "requirementType": "one_time",
        "actionText": "Inspect the affected part.",
        "initialThresholds": [],
        "recurringTriggers": [],
        "combinationLogic": "all",
        "conditions": [],
        "terminatingAction": None,
        "citations": [{"sourceDocumentId": "asd_fixture", "pageNumber": 2, "text": "Inspect the affected part."}],
        "confidence": 0.95,
        "uncertaintyReasons": [],
    }


def test_trigger_combination_logic_preserves_later_and_fails_closed_for_alternatives() -> None:
    assert normalize_logic("whichever_later") == "whichever_later"
    assert combine_trigger_statuses(["overdue", "current"], "whichever_later") == "current"
    assert combine_trigger_statuses(["overdue", "due_soon"], "whichever_later") == "due_soon"
    assert normalize_logic("alternative") == "alternative"
    assert combine_trigger_statuses(["overdue", "current"], "alternative") == "unknown"


def test_alternative_trigger_logic_requires_adjudication(db_session: Session) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna Airplanes",
        document_number="fixture-v3-alternative-trigger",
        ad_number="2026-88-05",
        affected_products=["Cessna 172R"],
        compliance_actions=[],
        compliance_intervals=[],
    )
    extraction.schema_version = "ad_extraction_v3"
    extraction.output["applicabilityGroups"] = [v3_group("cessna-172r", "Cessna", "172R")]
    requirement = v3_requirement("alternative-inspection", "cessna-172r")
    requirement["requirementType"] = "recurring"
    requirement["recurringTriggers"] = [{
        "metric": "calendar",
        "value": 12,
        "unit": "months",
        "anchorKind": "last_compliance",
        "sourceText": "at 12 months or by an approved alternative inspection",
    }]
    requirement["combinationLogic"] = "alternative"
    extraction.output["requirements"] = [requirement]

    populate_applicability_from_extraction(db_session, extraction)
    materialized = materialize_requirements_from_extraction(db_session, extraction)

    assert materialized[0].combination_logic == "alternative"
    assert materialized[0].review_status == "needs_adjudication"
    assert "alternative_trigger_logic_requires_adjudication" in materialized[0].source_payload["parseReasons"]


def test_missing_compliance_action_cannot_materialize_as_approved(db_session: Session) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna Airplanes",
        document_number="fixture-empty-compliance-action",
        ad_number="2026-88-06",
        affected_products=["Cessna 172R"],
        compliance_actions=[],
        compliance_intervals=[],
    )

    materialized = materialize_requirements_from_extraction(db_session, extraction)

    assert materialized[0].review_status == "needs_adjudication"
    assert "compliance_action_missing" in materialized[0].source_payload["parseReasons"]


def test_legacy_amoc_envelope_absence_does_not_supersede_reviewed_rows(db_session: Session) -> None:
    extraction = create_approved_extraction(
        db_session,
        title="Airworthiness Directives; Cessna Airplanes",
        document_number="fixture-amoc-preservation",
        ad_number="2026-88-07",
        affected_products=["Cessna 172R"],
        compliance_actions=["Inspect the affected part."],
        compliance_intervals=[],
    )
    extraction.output = {**extraction.output, "amocProvisions": [{
        "provisionKey": "paragraph-i",
        "authorityText": "The Manager has the authority to approve AMOCs for this AD.",
        "approvingAuthority": "Manager",
        "submissionInstructions": None,
        "conditions": [],
        "citations": [{"sourceDocumentId": "asd_fixture", "pageNumber": 9, "text": "The Manager has the authority to approve AMOCs for this AD."}],
        "confidence": 0.95,
        "uncertaintyReasons": [],
    }]}
    materialize_amoc_provisions(db_session, extraction)
    db_session.flush()
    provision = db_session.scalar(select(ADAMOCProvision))
    assert provision is not None
    assert provision.status == "current"

    extraction.output = {
        key: value for key, value in extraction.output.items() if key != "amocProvisions"
    }
    assert materialize_amoc_provisions(db_session, extraction) == []

    assert provision.status == "current"


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


def test_component_time_never_falls_back_to_aircraft_time(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    component = db_session.scalar(
        select(InstalledComponent).where(InstalledComponent.role == "engine")
    )
    assert component is not None
    db_session.add(
        AircraftTimeState(
            aircraft_id=demo_data["aircraft"].id,
            installed_component_id=None,
            observed_on=date(2026, 2, 1),
            tach_hours=1080,
            verification_status="verified_logbook",
            source_logbook_entry_id=None,
            state_hash="aircraft-only-time",
        )
    )
    db_session.flush()

    assert latest_time_state(
        db_session,
        aircraft_id=demo_data["aircraft"].id,
        component=component,
    ) is None


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
