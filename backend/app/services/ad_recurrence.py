from __future__ import annotations

import calendar
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.core import (
    ADAMOCProvision,
    ADComplianceEvent,
    ADComplianceRequirement,
    ADComplianceTrigger,
    ADExtraction,
    ADTargetApplicability,
    AircraftADDueState,
    AircraftTimeState,
    InstalledComponent,
    LogbookEntry,
)


DUE_ALGORITHM_VERSION = "1.2.0"
CALENDAR_DUE_SOON_DAYS = 30
USAGE_DUE_SOON_HOURS = Decimal("10")

_CALENDAR_PATTERN = re.compile(
    r"(?:every|each|at intervals? (?:not )?to exceed)?\s*(\d+(?:\.\d+)?)\s*(calendar\s+)?(months?|years?)",
    re.IGNORECASE,
)
_HOUR_PATTERN = re.compile(
    r"(?:every|each|at intervals? (?:not )?to exceed)?\s*(\d+(?:\.\d+)?)\s*(tach|hobbs|time[- ]in[- ]service|total time|flight)?\s*hours?",
    re.IGNORECASE,
)
_CYCLE_PATTERN = re.compile(
    r"(?:every|each|at intervals? (?:not )?to exceed)?\s*(\d+(?:\.\d+)?)\s*(?:flight\s+)?cycles?",
    re.IGNORECASE,
)


def materialize_requirements_from_extraction(
    db: Session,
    extraction: ADExtraction,
) -> list[ADComplianceRequirement]:
    """Create replayable normalized requirements for every current applicability row.

    Extraction output remains retained as source evidence. A requirement is approved
    only when every recurrence interval can be normalized and no unsupported
    condition is silently discarded.
    """

    output = extraction.output or {}
    applicability_rows = db.scalars(
        select(ADTargetApplicability)
        .where(
            ADTargetApplicability.directive_id == extraction.directive_id,
            ADTargetApplicability.status == "current",
            ADTargetApplicability.source_extraction_id == extraction.id,
        )
        .options(selectinload(ADTargetApplicability.target))
    ).all()
    effective_date = parse_date(output.get("effectiveDate"))
    specs = output.get("requirements") or [legacy_requirement_spec(output)]
    if extraction.schema_version == "ad_extraction_v3" and not output.get("requirements"):
        raise ValueError("AD extraction v3 cannot materialize without requirements")
    if extraction.schema_version == "ad_extraction_v3":
        available_group_keys = {
            normalize_group_key(row.applicability_group_key)
            for row in applicability_rows
            if normalize_group_key(row.applicability_group_key)
        }
        for spec in specs:
            required_group_keys = {
                normalize_group_key(key)
                for key in spec.get("applicabilityGroupKeys") or []
                if normalize_group_key(key)
            }
            if not required_group_keys or not required_group_keys.intersection(available_group_keys):
                raise ValueError(
                    f"AD requirement {spec.get('requirementKey') or 'unknown'} has no materialized applicability group"
                )
    materialized: list[ADComplianceRequirement] = []
    active_hashes: set[str] = set()

    for spec in specs:
        applicability_group_keys = {
            normalize_group_key(key)
            for key in spec.get("applicabilityGroupKeys") or []
            if normalize_group_key(key)
        }
        scoped_applicability_rows = applicability_rows
        if extraction.schema_version == "ad_extraction_v3" or applicability_group_keys:
            scoped_applicability_rows = [
                row
                for row in applicability_rows
                if normalize_group_key(row.applicability_group_key) in applicability_group_keys
            ]
        if extraction.schema_version == "ad_extraction_v3" and not scoped_applicability_rows:
            raise ValueError(
                f"AD requirement {spec.get('requirementKey') or 'unknown'} has no materialized applicability group"
            )
        initial_intervals = spec.get("initialThresholds") or []
        intervals = spec.get("recurringTriggers") or []
        initial_triggers, initial_reasons, _initial_logic = normalize_intervals(initial_intervals)
        recurring_triggers, recurring_reasons, parsed_logic = normalize_intervals(intervals)
        triggers = [
            {**trigger, "triggerKind": "initial"} for trigger in initial_triggers
        ] + [
            {**trigger, "triggerKind": "recurring"} for trigger in recurring_triggers
        ]
        parse_reasons = initial_reasons + recurring_reasons
        combination_logic = normalize_logic(parsed_logic if spec.get("legacy") else spec.get("combinationLogic") or parsed_logic)
        if combination_logic == "alternative":
            parse_reasons.append("alternative_trigger_logic_requires_adjudication")
        conditions = spec.get("conditions") or []
        if conditions:
            parse_reasons.append("conditions_require_adjudication")
        parse_reasons.extend(spec.get("uncertaintyReasons") or [])
        requirement_type = spec.get("requirementType") or ("recurring" if intervals else "one_time")
        extracted_action_text = str(spec.get("actionText") or "").strip()
        if not extracted_action_text:
            parse_reasons.append("compliance_action_missing")
        action_text = extracted_action_text or "Compliance action requires adjudication."
        terminating_action = first_text(spec.get("terminatingAction"))
        review_status = (
            "approved"
            if extraction.status == "approved"
            and not parse_reasons
            and extracted_action_text
            and (
                extraction.schema_version not in {"ad_extraction_v2", "ad_extraction_v3"}
                or spec.get("citations")
            )
            else "needs_adjudication"
        )
        source_payload = {
            "requirementKey": spec.get("requirementKey"),
            "applicabilityGroupKeys": sorted(applicability_group_keys),
            "initialThresholds": spec.get("initialThresholds") or [],
            "recurringTriggers": intervals,
            "conditions": conditions,
            "parseReasons": sorted(set(parse_reasons)),
            "combinationLogic": combination_logic,
        }
        for applicability in scoped_applicability_rows:
            requirement_hash = stable_hash(
            {
                "directiveId": extraction.directive_id,
                "targetApplicabilityId": applicability.id,
                "sourceExtractionId": extraction.id,
                "sourceContentHash": extraction.input_content_hash,
                "requirementType": requirement_type,
                "actionText": action_text,
                "terminatingActionText": terminating_action,
                "effectiveDate": effective_date,
                "triggers": triggers,
                "sourcePayload": source_payload,
            })
            active_hashes.add(requirement_hash)
            requirement = db.scalar(
                select(ADComplianceRequirement).where(
                    ADComplianceRequirement.requirement_hash == requirement_hash
                )
            )
            if requirement is None:
                requirement = ADComplianceRequirement(
                directive_id=extraction.directive_id,
                target_applicability_id=applicability.id,
                source_extraction_id=extraction.id,
                requirement_hash=requirement_hash,
                requirement_type=requirement_type,
                combination_logic=combination_logic,
                action_text=action_text,
                terminating_action_text=terminating_action,
                effective_date=effective_date,
                review_status=review_status,
                confidence=extraction.confidence,
                citations=spec.get("citations") or extraction.citations or [],
                source_payload=source_payload,
                status="current",
                )
                db.add(requirement)
                db.flush()
            requirement.directive_id = extraction.directive_id
            requirement.target_applicability_id = applicability.id
            requirement.source_extraction_id = extraction.id
            requirement.requirement_type = requirement_type
            requirement.combination_logic = combination_logic
            requirement.action_text = action_text
            requirement.terminating_action_text = terminating_action
            requirement.effective_date = effective_date
            requirement.review_status = review_status
            requirement.confidence = extraction.confidence
            requirement.citations = spec.get("citations") or extraction.citations or []
            requirement.source_payload = source_payload
            requirement.status = "current"
            db.execute(
                delete(ADComplianceTrigger).where(
                    ADComplianceTrigger.requirement_id == requirement.id
                )
            )
            for sequence, trigger in enumerate(triggers):
                db.add(ADComplianceTrigger(
                    requirement_id=requirement.id,
                    sequence=sequence,
                    trigger_kind=trigger["triggerKind"],
                    metric=trigger["metric"],
                    interval_value=Decimal(trigger["intervalValue"]),
                    interval_unit=trigger["intervalUnit"],
                    anchor_kind=trigger.get("anchorKind", "last_compliance"),
                    source_text=trigger.get("sourceText"),
                ))
            materialized.append(requirement)

    if applicability_rows:
        stale = db.scalars(
            select(ADComplianceRequirement).where(
                ADComplianceRequirement.directive_id == extraction.directive_id,
                ADComplianceRequirement.status == "current",
                ADComplianceRequirement.requirement_hash.not_in(active_hashes),
            )
        ).all()
        for requirement in stale:
            requirement.status = "superseded"
    materialize_amoc_provisions(db, extraction)
    db.flush()
    return materialized


def materialize_amoc_provisions(
    db: Session,
    extraction: ADExtraction,
) -> list[ADAMOCProvision]:
    if "amocProvisions" not in (extraction.output or {}):
        # Legacy schemas have no AMOC envelope. Re-materializing them must not
        # supersede source-reviewed AMOC rows from a later v3 extraction.
        return []
    materialized: list[ADAMOCProvision] = []
    active_hashes: set[str] = set()
    for provision in (extraction.output or {}).get("amocProvisions") or []:
        provision_hash = stable_hash({
            "directiveId": extraction.directive_id,
            "sourceExtractionId": extraction.id,
            "sourceContentHash": extraction.input_content_hash,
            "provision": provision,
        })
        active_hashes.add(provision_hash)
        row = db.scalar(
            select(ADAMOCProvision).where(
                ADAMOCProvision.provision_hash == provision_hash
            )
        )
        if row is None:
            row = ADAMOCProvision(
                directive_id=extraction.directive_id,
                source_extraction_id=extraction.id,
                provision_hash=provision_hash,
                provision_key=normalize_group_key(provision.get("provisionKey")),
                authority_text=str(provision.get("authorityText") or "").strip(),
                approving_authority=first_text(provision.get("approvingAuthority")),
                submission_instructions=first_text(provision.get("submissionInstructions")),
                conditions=provision.get("conditions") or [],
                citations=provision.get("citations") or [],
                confidence=float(provision.get("confidence") or extraction.confidence),
                source_payload=provision,
                status="current",
            )
            db.add(row)
        else:
            row.status = "current"
        row.directive_id = extraction.directive_id
        row.source_extraction_id = extraction.id
        row.provision_key = normalize_group_key(provision.get("provisionKey"))
        row.authority_text = str(provision.get("authorityText") or "").strip()
        row.approving_authority = first_text(provision.get("approvingAuthority"))
        row.submission_instructions = first_text(provision.get("submissionInstructions"))
        row.conditions = provision.get("conditions") or []
        row.source_payload = provision
        row.citations = provision.get("citations") or []
        row.confidence = float(provision.get("confidence") or extraction.confidence)
        row.status = "current"
        materialized.append(row)
    stale_statement = select(ADAMOCProvision).where(
        ADAMOCProvision.directive_id == extraction.directive_id,
        ADAMOCProvision.status == "current",
    )
    if active_hashes:
        stale_statement = stale_statement.where(
            ADAMOCProvision.provision_hash.not_in(active_hashes)
        )
    for row in db.scalars(stale_statement).all():
        row.status = "superseded"
    return materialized


def legacy_requirement_spec(output: dict[str, Any]) -> dict[str, Any]:
    actions = [str(item).strip() for item in output.get("complianceActions") or [] if str(item).strip()]
    intervals = output.get("complianceIntervals") or []
    return {
        "requirementKey": "legacy-primary",
        "requirementType": "recurring" if intervals else "one_time",
        "actionText": "\n".join(actions),
        "initialThresholds": [],
        "recurringTriggers": intervals,
        "combinationLogic": "all",
        "conditions": output.get("conditions") or [],
        "terminatingAction": output.get("terminatingActions") or output.get("terminatingAction"),
        "citations": output.get("citations") or [],
        "uncertaintyReasons": [],
        "legacy": True,
    }


def normalize_intervals(intervals: Iterable[Any]) -> tuple[list[dict[str, str]], list[str], str]:
    triggers: list[dict[str, str]] = []
    reasons: list[str] = []
    combination_logic = "all"
    for interval in intervals:
        if isinstance(interval, dict) and interval.get("triggers"):
            logic = str(interval.get("logic") or interval.get("combinationLogic") or "whichever_first")
            combination_logic = normalize_logic(logic)
            nested, nested_reasons, _ = normalize_intervals(interval["triggers"])
            triggers.extend(nested)
            reasons.extend(
                reason
                for reason in nested_reasons
                if reason != "multiple_interval_logic_unknown"
            )
            continue
        if isinstance(interval, str) and not recurrence_language_is_explicit(interval):
            reasons.append("recurrence_semantics_uncertain")
        trigger = normalize_interval(interval)
        if trigger is None:
            reasons.append(f"unparsed_interval:{str(interval)[:160]}")
            continue
        triggers.append(trigger)
        source_text = trigger.get("sourceText", "").lower()
        if "whichever" in source_text and "first" in source_text:
            combination_logic = "whichever_first"
    if len(triggers) > 1 and combination_logic == "all":
        combined_text = " ".join(trigger.get("sourceText", "") for trigger in triggers).lower()
        if "whichever" in combined_text and "first" in combined_text:
            combination_logic = "whichever_first"
        else:
            reasons.append("multiple_interval_logic_unknown")
    return triggers, reasons, combination_logic


def normalize_interval(interval: Any) -> dict[str, str] | None:
    if isinstance(interval, dict):
        interval_type = str(interval.get("type") or interval.get("metric") or "").lower()
        source_text = str(interval.get("sourceText") or interval)
        anchor_kind = normalize_anchor_kind(interval.get("anchorKind"))
        mapping = {
            "calendar": ("calendar", interval.get("value"), interval.get("unit") or "months"),
            "calendar_months": ("calendar", interval.get("intervalMonths") or interval.get("value"), "months"),
            "months": ("calendar", interval.get("value") or interval.get("intervalMonths"), "months"),
            "calendar_years": ("calendar", interval.get("intervalYears"), "years"),
            "tach_hours": ("tach_hours", interval.get("intervalHours") or interval.get("value"), "hours"),
            "hobbs_hours": ("hobbs_hours", interval.get("intervalHours") or interval.get("value"), "hours"),
            "total_time_hours": ("total_time_hours", interval.get("intervalHours") or interval.get("value"), "hours"),
            "time_in_service_hours": ("total_time_hours", interval.get("intervalHours") or interval.get("value"), "hours"),
            "cycles": ("cycles", interval.get("intervalCycles") or interval.get("value"), "cycles"),
        }
        if interval_type in mapping:
            metric, value, unit = mapping[interval_type]
            decimal_value = positive_decimal(value)
            if decimal_value is None:
                return None
            if unit == "years":
                decimal_value *= 12
                unit = "months"
            return trigger_payload(metric, decimal_value, unit, source_text, anchor_kind)
        value = positive_decimal(interval.get("value"))
        unit = str(interval.get("unit") or "").lower()
        if value is not None and unit:
            if unit.startswith("month"):
                return trigger_payload("calendar", value, "months", source_text, anchor_kind)
            if unit.startswith("year"):
                return trigger_payload("calendar", value * 12, "months", source_text, anchor_kind)
            if unit.startswith("hour"):
                return trigger_payload("total_time_hours", value, "hours", source_text, anchor_kind)
            if unit.startswith("cycle"):
                return trigger_payload("cycles", value, "cycles", source_text, anchor_kind)
        return normalize_interval(source_text)

    text = str(interval).strip()
    if not text:
        return None
    calendar_match = _CALENDAR_PATTERN.search(text)
    if calendar_match:
        value = Decimal(calendar_match.group(1))
        unit = calendar_match.group(3).lower()
        if unit.startswith("year"):
            value *= 12
        return trigger_payload("calendar", value, "months", text)
    hour_match = _HOUR_PATTERN.search(text)
    if hour_match:
        qualifier = (hour_match.group(2) or "").lower()
        metric = "total_time_hours"
        if "tach" in qualifier:
            metric = "tach_hours"
        elif "hobbs" in qualifier:
            metric = "hobbs_hours"
        return trigger_payload(metric, Decimal(hour_match.group(1)), "hours", text)
    cycle_match = _CYCLE_PATTERN.search(text)
    if cycle_match:
        return trigger_payload("cycles", Decimal(cycle_match.group(1)), "cycles", text)
    return None


def sync_verified_time_states(
    db: Session,
    *,
    aircraft_id: str,
    entries: Iterable[LogbookEntry],
) -> list[AircraftTimeState]:
    active_components = db.scalars(
        select(InstalledComponent).where(
            InstalledComponent.aircraft_id == aircraft_id,
            InstalledComponent.removed_at.is_(None),
        )
    ).all()
    components_by_section = {
        "airframe": next((item for item in active_components if item.role == "airframe"), None),
        "engine": next((item for item in active_components if item.role == "engine"), None),
        "propeller": next((item for item in active_components if item.role == "propeller"), None),
    }
    states: list[AircraftTimeState] = []
    for entry in entries:
        if entry.review_status != "verified" or entry.entry_date is None:
            continue
        if entry.tach_time is None and entry.hobbs_time is None and entry.total_time is None:
            continue
        section_key = entry.logbook_section.key if entry.logbook_section else None
        component = components_by_section.get(section_key)
        payload = {
            "aircraftId": aircraft_id,
            "componentId": component.id if component else None,
            "entryId": entry.id,
            "observedOn": entry.entry_date,
            "tachHours": entry.tach_time,
            "hobbsHours": entry.hobbs_time,
            "totalTimeHours": entry.total_time,
        }
        state_hash = stable_hash(payload)
        state = db.scalar(select(AircraftTimeState).where(AircraftTimeState.state_hash == state_hash))
        if state is None:
            state = AircraftTimeState(
                state_hash=state_hash,
                aircraft_id=aircraft_id,
                installed_component_id=component.id if component else None,
                source_logbook_entry_id=entry.id,
                observed_on=entry.entry_date,
                tach_hours=decimal_or_none(entry.tach_time),
                hobbs_hours=decimal_or_none(entry.hobbs_time),
                total_time_hours=decimal_or_none(entry.total_time),
                verification_status="verified_logbook",
            )
            db.add(state)
        states.append(state)
    db.flush()
    return states


def upsert_verified_compliance_event(
    db: Session,
    *,
    requirement: ADComplianceRequirement,
    aircraft_id: str,
    component: InstalledComponent | None,
    entry: LogbookEntry,
    action_text: str,
    is_terminating_action: bool = False,
) -> ADComplianceEvent:
    if entry.review_status != "verified" or entry.entry_date is None:
        raise ValueError("AD compliance events require a dated, verified logbook entry")
    evidence_key = stable_hash(
        {
            "requirementId": requirement.id,
            "aircraftId": aircraft_id,
            "componentId": component.id if component else None,
            "logbookEntryId": entry.id,
            "actionText": action_text,
            "terminating": is_terminating_action,
        }
    )
    event = db.scalar(select(ADComplianceEvent).where(ADComplianceEvent.evidence_key == evidence_key))
    if event is None:
        event = ADComplianceEvent(
            evidence_key=evidence_key,
            requirement_id=requirement.id,
            aircraft_id=aircraft_id,
            installed_component_id=component.id if component else None,
            logbook_entry_id=entry.id,
            occurred_on=entry.entry_date,
            action_text=action_text,
            tach_hours=decimal_or_none(entry.tach_time),
            hobbs_hours=decimal_or_none(entry.hobbs_time),
            total_time_hours=decimal_or_none(entry.total_time),
            is_terminating_action=is_terminating_action,
            verification_status="verified_logbook",
        )
        db.add(event)
        db.flush()
    return event


def evidence_supports_terminating_action(
    requirement: ADComplianceRequirement,
    evidence_text: str,
) -> bool:
    """Require both an extracted terminating action and explicit logbook wording."""

    if not requirement.terminating_action_text:
        return False
    evidence = evidence_text.lower()
    source = requirement.terminating_action_text.lower()
    terminating_terms = {"terminating", "terminates", "terminated"}
    return any(term in evidence for term in terminating_terms) and any(
        term in source for term in terminating_terms
    )


def compute_due_state(
    db: Session,
    *,
    aircraft_id: str,
    requirement: ADComplianceRequirement,
    component: InstalledComponent | None,
    as_of_date: date | None = None,
) -> AircraftADDueState:
    as_of_date = as_of_date or date.today()
    events = db.scalars(
        select(ADComplianceEvent)
        .where(
            ADComplianceEvent.aircraft_id == aircraft_id,
            ADComplianceEvent.requirement_id == requirement.id,
            ADComplianceEvent.verification_status == "verified_logbook",
            ADComplianceEvent.installed_component_id == (component.id if component else None),
        )
        .order_by(ADComplianceEvent.occurred_on.desc(), ADComplianceEvent.created_at.desc())
    ).all()
    last_event = events[0] if events else None
    triggers = db.scalars(
        select(ADComplianceTrigger)
        .where(ADComplianceTrigger.requirement_id == requirement.id)
        .order_by(ADComplianceTrigger.sequence)
    ).all()
    current_state = latest_time_state(db, aircraft_id=aircraft_id, component=component)
    trigger_states: list[dict[str, Any]] = []
    reasons: list[str] = []
    status = "unknown"

    if requirement.review_status != "approved":
        reasons.append("recurrence_requirement_needs_adjudication")
    elif last_event and last_event.is_terminating_action:
        status = "terminated"
    elif requirement.requirement_type == "one_time" and last_event:
        status = "current"
    elif not triggers:
        reasons.append("compliance_threshold_unstructured")
    else:
        active_triggers = [
            trigger for trigger in triggers
            if trigger.trigger_kind == ("recurring" if last_event else "initial")
        ]
        if not active_triggers:
            reasons.append(
                "recurring_interval_unstructured" if last_event else "initial_compliance_threshold_missing"
            )
        for trigger in active_triggers:
            trigger_state = evaluate_trigger(
                trigger,
                last_event=last_event,
                current_state=current_state,
                requirement=requirement,
                component=component,
                as_of_date=as_of_date,
            )
            trigger_states.append(trigger_state)
        if trigger_states:
            status = combine_trigger_statuses(
                [item["status"] for item in trigger_states],
                requirement.combination_logic,
            )
        for item in trigger_states:
            reasons.extend(item.get("unresolvedReasons") or [])

    input_hash = stable_hash(
        {
            "aircraftId": aircraft_id,
            "componentId": component.id if component else None,
            "requirementHash": requirement.requirement_hash,
            "asOfDate": as_of_date,
            "lastEvent": event_payload(last_event),
            "currentState": time_state_payload(current_state),
            "triggerStates": trigger_states,
            "status": status,
            "reasons": sorted(set(reasons)),
        }
    )
    db.execute(
        update(AircraftADDueState)
        .where(
            AircraftADDueState.aircraft_id == aircraft_id,
            AircraftADDueState.requirement_id == requirement.id,
            AircraftADDueState.installed_component_id == (component.id if component else None),
            AircraftADDueState.is_current.is_(True),
        )
        .values(is_current=False)
    )
    due_state = db.scalar(
        select(AircraftADDueState).where(
            AircraftADDueState.aircraft_id == aircraft_id,
            AircraftADDueState.requirement_id == requirement.id,
            AircraftADDueState.installed_component_id == (component.id if component else None),
            AircraftADDueState.algorithm_version == DUE_ALGORITHM_VERSION,
            AircraftADDueState.input_hash == input_hash,
        )
    )
    primary = primary_due_trigger(trigger_states, requirement.combination_logic)
    if due_state is None:
        due_state = AircraftADDueState(
            aircraft_id=aircraft_id,
            requirement_id=requirement.id,
            installed_component_id=component.id if component else None,
            last_compliance_event_id=last_event.id if last_event else None,
            status=status,
            due_date=parse_date(primary.get("dueDate")) if primary else None,
            due_metric=primary.get("metric") if primary else None,
            due_value=decimal_or_none(primary.get("dueValue")) if primary else None,
            trigger_states=trigger_states,
            unresolved_reasons=sorted(set(reasons)),
            algorithm_version=DUE_ALGORITHM_VERSION,
            input_hash=input_hash,
            is_current=True,
        )
        db.add(due_state)
    else:
        due_state.is_current = True
        due_state.computed_at = datetime.now(timezone.utc)
    db.flush()
    return due_state


def evaluate_trigger(
    trigger: ADComplianceTrigger,
    *,
    last_event: ADComplianceEvent | None,
    current_state: AircraftTimeState | None,
    requirement: ADComplianceRequirement,
    component: InstalledComponent | None,
    as_of_date: date,
) -> dict[str, Any]:
    if trigger.metric == "calendar":
        interval = int(trigger.interval_value)
        if Decimal(interval) != trigger.interval_value:
            return unknown_trigger(trigger, "fractional_calendar_interval_unsupported")
        anchor_date, anchor_reason = calendar_anchor_date(
            trigger,
            last_event=last_event,
            requirement=requirement,
            component=component,
        )
        if anchor_date is None:
            return unknown_trigger(trigger, anchor_reason or "calendar_anchor_missing")
        if trigger.interval_unit == "days":
            due_date = anchor_date + timedelta(days=interval)
        elif trigger.interval_unit == "months":
            due_date = add_months(anchor_date, interval)
        else:
            return unknown_trigger(trigger, "calendar_interval_unit_unsupported")
        remaining_days = (due_date - as_of_date).days
        status = "overdue" if remaining_days < 0 else "due_soon" if remaining_days <= CALENDAR_DUE_SOON_DAYS else "current"
        return {
            "metric": trigger.metric,
            "status": status,
            "dueDate": due_date.isoformat(),
            "remainingDays": remaining_days,
            "sourceText": trigger.source_text,
            "unresolvedReasons": [],
        }

    if trigger.anchor_kind != "last_compliance":
        return unknown_trigger(trigger, f"{trigger.anchor_kind}_{trigger.metric}_baseline_missing")
    if last_event is None:
        return unknown_trigger(trigger, "compliance_event_missing")
    event_value = metric_value(last_event, trigger.metric)
    current_value = metric_value(current_state, trigger.metric)
    if event_value is None:
        return unknown_trigger(trigger, f"last_compliance_{trigger.metric}_missing")
    if current_value is None:
        return unknown_trigger(trigger, f"current_{trigger.metric}_missing")
    due_value = event_value + trigger.interval_value
    remaining = due_value - current_value
    status = "overdue" if remaining < 0 else "due_soon" if remaining <= USAGE_DUE_SOON_HOURS else "current"
    return {
        "metric": trigger.metric,
        "status": status,
        "dueValue": decimal_text(due_value),
        "currentValue": decimal_text(current_value),
        "remainingValue": decimal_text(remaining),
        "unit": trigger.interval_unit,
        "sourceText": trigger.source_text,
        "unresolvedReasons": [],
    }


def latest_time_state(
    db: Session,
    *,
    aircraft_id: str,
    component: InstalledComponent | None,
) -> AircraftTimeState | None:
    component_id = component.id if component else None
    state = db.scalar(
        select(AircraftTimeState)
        .where(
            AircraftTimeState.aircraft_id == aircraft_id,
            AircraftTimeState.installed_component_id == component_id,
            AircraftTimeState.verification_status == "verified_logbook",
        )
        .order_by(AircraftTimeState.observed_on.desc(), AircraftTimeState.created_at.desc())
        .limit(1)
    )
    return state


def combine_trigger_statuses(statuses: list[str], logic: str) -> str:
    if not statuses:
        return "unknown"
    if logic == "alternative":
        return "unknown"
    if logic == "whichever_first":
        for status in ["overdue", "due_soon"]:
            if status in statuses:
                return status
        return "unknown" if "unknown" in statuses else "current"
    if logic == "whichever_later":
        if "unknown" in statuses:
            return "unknown"
        if "current" in statuses:
            return "current"
        if "due_soon" in statuses:
            return "due_soon"
        return "overdue"
    if "unknown" in statuses:
        return "unknown"
    if "overdue" in statuses:
        return "overdue"
    if "due_soon" in statuses:
        return "due_soon"
    return "current"


def requirement_for_applicability(
    db: Session,
    *,
    extraction: ADExtraction,
    applicability: ADTargetApplicability | None,
) -> ADComplianceRequirement | None:
    requirements = requirements_for_applicability(
        db,
        extraction=extraction,
        applicability=applicability,
    )
    return requirements[0] if len(requirements) == 1 else None


def requirements_for_applicability(
    db: Session,
    *,
    extraction: ADExtraction,
    applicability: ADTargetApplicability | None,
) -> list[ADComplianceRequirement]:
    requirements = materialize_requirements_from_extraction(db, extraction)
    if applicability:
        exact = [
            item for item in requirements
            if item.target_applicability_id == applicability.id
            and item.source_extraction_id == extraction.id
        ]
        if exact or extraction.schema_version == "ad_extraction_v3":
            return exact
        # Older extraction schemas did not preserve an exact applicability-group
        # identity. Keep their target-level compatibility fallback isolated here;
        # signed v3 requirements must never cross group boundaries.
        target_id = applicability.target_id
        return [
            item
            for item in requirements
            if item.source_extraction_id == extraction.id
            and item.target_applicability.target_id == target_id
        ]
    return [
        item for item in requirements
        if item.source_extraction_id == extraction.id
    ]


def due_state_payload(state: AircraftADDueState | None) -> dict[str, Any] | None:
    if state is None:
        return None
    return {
        "id": state.id,
        "requirementId": state.requirement_id,
        "status": state.status,
        "dueDate": state.due_date.isoformat() if state.due_date else None,
        "dueMetric": state.due_metric,
        "dueValue": decimal_text(state.due_value) if state.due_value is not None else None,
        "triggerStates": state.trigger_states or [],
        "unresolvedReasons": state.unresolved_reasons or [],
        "algorithmVersion": state.algorithm_version,
        "inputHash": state.input_hash,
    }


def normalize_logic(value: str) -> str:
    normalized = value.lower().replace("-", "_").replace(" ", "_")
    if normalized in {"any", "or", "whichever_first", "earliest"}:
        return "whichever_first"
    if normalized in {"whichever_later", "latest"}:
        return "whichever_later"
    if normalized in {"alternative", "either"}:
        return "alternative"
    return "all"


def recurrence_language_is_explicit(value: str) -> bool:
    normalized = value.lower()
    return any(
        phrase in normalized
        for phrase in (
            "every ",
            "each ",
            "at intervals",
            "repeat ",
            "repetitive",
            "recurring",
        )
    )


def trigger_payload(
    metric: str,
    value: Decimal,
    unit: str,
    source_text: str,
    anchor_kind: str = "last_compliance",
) -> dict[str, str]:
    return {
        "metric": metric,
        "intervalValue": decimal_text(value),
        "intervalUnit": unit,
        "anchorKind": normalize_anchor_kind(anchor_kind),
        "sourceText": source_text,
    }


def normalize_group_key(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_anchor_kind(value: Any) -> str:
    anchor = str(value or "last_compliance").strip().lower()
    if anchor not in {"effective_date", "last_compliance", "installation", "manufacture", "unknown"}:
        return "unknown"
    return anchor


def calendar_anchor_date(
    trigger: ADComplianceTrigger,
    *,
    last_event: ADComplianceEvent | None,
    requirement: ADComplianceRequirement,
    component: InstalledComponent | None,
) -> tuple[date | None, str | None]:
    if trigger.anchor_kind == "last_compliance":
        return (
            (last_event.occurred_on, None)
            if last_event is not None
            else (None, "compliance_event_missing")
        )
    if trigger.anchor_kind == "effective_date":
        return (
            (requirement.effective_date, None)
            if requirement.effective_date is not None
            else (None, "effective_date_missing")
        )
    if trigger.anchor_kind == "installation":
        return (
            (component.installed_at, None)
            if component is not None and component.installed_at is not None
            else (None, "installation_date_missing")
        )
    if trigger.anchor_kind == "manufacture":
        return None, "manufacture_date_unsupported"
    return None, "trigger_anchor_unknown"


def unknown_trigger(trigger: ADComplianceTrigger, reason: str) -> dict[str, Any]:
    return {
        "metric": trigger.metric,
        "status": "unknown",
        "sourceText": trigger.source_text,
        "unresolvedReasons": [reason],
    }


def primary_due_trigger(
    states: list[dict[str, Any]],
    logic: str,
) -> dict[str, Any] | None:
    if not states:
        return None
    dated = [item for item in states if item.get("dueDate")]
    if dated:
        selector = max if logic == "whichever_later" else min
        return selector(dated, key=lambda item: item["dueDate"])
    valued = [item for item in states if item.get("dueValue") is not None]
    if not valued:
        return None
    if logic == "whichever_later" and len({item.get("metric") for item in valued}) == 1:
        return max(valued, key=lambda item: Decimal(str(item["dueValue"])))
    return valued[0]


def metric_value(source: Any, metric: str) -> Decimal | None:
    if source is None:
        return None
    field = {
        "tach_hours": "tach_hours",
        "hobbs_hours": "hobbs_hours",
        "total_time_hours": "total_time_hours",
        "cycles": "cycle_count",
    }.get(metric)
    return decimal_or_none(getattr(source, field, None)) if field else None


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def first_text(value: Any) -> str | None:
    if isinstance(value, list):
        return next((str(item).strip() for item in value if str(item).strip()), None)
    text = str(value).strip() if value else ""
    return text or None


def positive_decimal(value: Any) -> Decimal | None:
    result = decimal_or_none(value)
    return result if result is not None and result > 0 else None


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def stable_hash(payload: Any) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def event_payload(event: ADComplianceEvent | None) -> dict[str, Any] | None:
    if event is None:
        return None
    return {
        "id": event.id,
        "occurredOn": event.occurred_on,
        "tachHours": event.tach_hours,
        "hobbsHours": event.hobbs_hours,
        "totalTimeHours": event.total_time_hours,
        "cycleCount": event.cycle_count,
        "terminating": event.is_terminating_action,
    }


def time_state_payload(state: AircraftTimeState | None) -> dict[str, Any] | None:
    if state is None:
        return None
    return {
        "id": state.id,
        "observedOn": state.observed_on,
        "tachHours": state.tach_hours,
        "hobbsHours": state.hobbs_hours,
        "totalTimeHours": state.total_time_hours,
        "cycleCount": state.cycle_count,
    }
