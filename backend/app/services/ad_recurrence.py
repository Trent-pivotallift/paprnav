from __future__ import annotations

import calendar
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models.core import (
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


DUE_ALGORITHM_VERSION = "1.0.0"
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
            ADTargetApplicability.status.in_({"current", "active", "unknown"}),
        )
        .options(selectinload(ADTargetApplicability.target))
    ).all()
    actions = [str(item).strip() for item in output.get("complianceActions") or [] if str(item).strip()]
    intervals = output.get("complianceIntervals") or []
    action_text = "\n".join(actions) or "Compliance action requires adjudication."
    effective_date = parse_date(output.get("effectiveDate"))
    terminating_action = first_text(output.get("terminatingActions") or output.get("terminatingAction"))
    triggers, parse_reasons, combination_logic = normalize_intervals(intervals)
    conditions = output.get("conditions") or []
    if conditions:
        parse_reasons.append("conditions_require_adjudication")
    requirement_type = "recurring" if intervals else "one_time"
    if intervals and not triggers:
        parse_reasons.append("recurring_interval_unstructured")
    review_status = (
        "approved"
        if extraction.status == "approved" and not parse_reasons and actions
        else "needs_adjudication"
    )
    source_payload = {
        "actions": actions,
        "intervals": intervals,
        "conditions": conditions,
        "parseReasons": sorted(set(parse_reasons)),
        "combinationLogic": combination_logic,
    }
    materialized: list[ADComplianceRequirement] = []
    active_hashes: set[str] = set()

    for applicability in applicability_rows:
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
            }
        )
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
                citations=extraction.citations or [],
                source_payload=source_payload,
                status="current",
            )
            db.add(requirement)
            db.flush()
            for sequence, trigger in enumerate(triggers):
                db.add(
                    ADComplianceTrigger(
                        requirement_id=requirement.id,
                        sequence=sequence,
                        metric=trigger["metric"],
                        interval_value=Decimal(trigger["intervalValue"]),
                        interval_unit=trigger["intervalUnit"],
                        anchor_kind=trigger.get("anchorKind", "last_compliance"),
                        source_text=trigger.get("sourceText"),
                    )
                )
        else:
            requirement.status = "current"
            requirement.review_status = review_status
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
    db.flush()
    return materialized


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
        mapping = {
            "calendar_months": ("calendar", interval.get("intervalMonths"), "months"),
            "months": ("calendar", interval.get("value") or interval.get("intervalMonths"), "months"),
            "calendar_years": ("calendar", interval.get("intervalYears"), "years"),
            "tach_hours": ("tach_hours", interval.get("intervalHours"), "hours"),
            "hobbs_hours": ("hobbs_hours", interval.get("intervalHours"), "hours"),
            "total_time_hours": ("total_time_hours", interval.get("intervalHours"), "hours"),
            "time_in_service_hours": ("total_time_hours", interval.get("intervalHours"), "hours"),
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
            return trigger_payload(metric, decimal_value, unit, source_text)
        value = positive_decimal(interval.get("value"))
        unit = str(interval.get("unit") or "").lower()
        if value is not None and unit:
            if unit.startswith("month"):
                return trigger_payload("calendar", value, "months", source_text)
            if unit.startswith("year"):
                return trigger_payload("calendar", value * 12, "months", source_text)
            if unit.startswith("hour"):
                return trigger_payload("total_time_hours", value, "hours", source_text)
            if unit.startswith("cycle"):
                return trigger_payload("cycles", value, "cycles", source_text)
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
    states: list[AircraftTimeState] = []
    for entry in entries:
        if entry.review_status != "verified" or entry.entry_date is None:
            continue
        if entry.tach_time is None and entry.hobbs_time is None and entry.total_time is None:
            continue
        payload = {
            "aircraftId": aircraft_id,
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
    elif requirement.requirement_type == "one_time":
        status = "current" if last_event else "unknown"
        if not last_event:
            reasons.append("compliance_event_missing")
    elif not last_event:
        reasons.append("compliance_event_missing")
    elif not triggers:
        reasons.append("recurring_interval_unstructured")
    else:
        for trigger in triggers:
            trigger_state = evaluate_trigger(
                trigger,
                last_event=last_event,
                current_state=current_state,
                as_of_date=as_of_date,
            )
            trigger_states.append(trigger_state)
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
    primary = earliest_due_trigger(trigger_states)
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
    last_event: ADComplianceEvent,
    current_state: AircraftTimeState | None,
    as_of_date: date,
) -> dict[str, Any]:
    if trigger.metric == "calendar":
        months = int(trigger.interval_value)
        if Decimal(months) != trigger.interval_value:
            return unknown_trigger(trigger, "fractional_calendar_interval_unsupported")
        due_date = add_months(last_event.occurred_on, months)
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
    if state is None and component is not None:
        state = db.scalar(
            select(AircraftTimeState)
            .where(
                AircraftTimeState.aircraft_id == aircraft_id,
                AircraftTimeState.installed_component_id.is_(None),
                AircraftTimeState.verification_status == "verified_logbook",
            )
            .order_by(AircraftTimeState.observed_on.desc(), AircraftTimeState.created_at.desc())
            .limit(1)
        )
    return state


def combine_trigger_statuses(statuses: list[str], logic: str) -> str:
    if not statuses:
        return "unknown"
    if logic == "whichever_first":
        for status in ["overdue", "due_soon"]:
            if status in statuses:
                return status
        return "unknown" if "unknown" in statuses else "current"
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
    requirements = materialize_requirements_from_extraction(db, extraction)
    if applicability:
        exact = next(
            (item for item in requirements if item.target_applicability_id == applicability.id),
            None,
        )
        if exact:
            return exact
        target_id = applicability.target_id
        return next(
            (
                item
                for item in requirements
                if item.target_applicability.target_id == target_id
            ),
            None,
        )
    return requirements[0] if len(requirements) == 1 else None


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
    return "whichever_first" if normalized in {"any", "or", "whichever_first", "earliest"} else "all"


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


def trigger_payload(metric: str, value: Decimal, unit: str, source_text: str) -> dict[str, str]:
    return {
        "metric": metric,
        "intervalValue": decimal_text(value),
        "intervalUnit": unit,
        "anchorKind": "last_compliance",
        "sourceText": source_text,
    }


def unknown_trigger(trigger: ADComplianceTrigger, reason: str) -> dict[str, Any]:
    return {
        "metric": trigger.metric,
        "status": "unknown",
        "sourceText": trigger.source_text,
        "unresolvedReasons": [reason],
    }


def earliest_due_trigger(states: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not states:
        return None
    dated = [item for item in states if item.get("dueDate")]
    if dated:
        return min(dated, key=lambda item: item["dueDate"])
    valued = [item for item in states if item.get("dueValue") is not None]
    return valued[0] if valued else None


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
