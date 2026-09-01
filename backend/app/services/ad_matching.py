from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.core import (
    ADExtraction,
    ADMatchAdjudication,
    ADMatchDueStateLink,
    ADMatchEvidence,
    ADMatchResult,
    ADTargetApplicability,
    Aircraft,
    AirworthinessDirective,
    InstalledComponent,
    LogbookEntry,
    ProductEvent,
)
from app.services.ad_applicability import infer_component_role
from app.services.ad_costs import record_ad_cost_entry
from app.services.ad_coverage import resolve_aircraft_ad_coverage
from app.services.ad_identity import normalize_ad_number
from app.services.ad_recurrence import (
    compute_due_state,
    evidence_supports_terminating_action,
    requirements_for_applicability,
    sync_verified_time_states,
    upsert_verified_compliance_event,
)
from app.services.ad_release import released_signed_extractions
from app.services.maintenance_extraction import extract_structured_maintenance_data
from app.services.observability import record_product_event, record_workflow_status

ALGORITHM_NAME = "deterministic_ad_logbook_matcher"
ALGORITHM_VERSION = "0.7.0"
ACTION_WORDS = {"comply", "complied", "compliance", "inspect", "inspection", "replace", "replaced", "modify", "modified"}


@dataclass(frozen=True)
class CandidateEvidence:
    entry: LogbookEntry
    confidence: float
    rationale: str
    matched_text: str
    explicit_ad_reference: bool
    disposition_candidate: str | None


def match_aircraft_ads(db: Session, aircraft_id: str) -> dict[str, int]:
    aircraft = db.scalar(select(Aircraft).where(Aircraft.id == aircraft_id).options(selectinload(Aircraft.installed_components)))
    if not aircraft:
        raise ValueError("Aircraft not found")

    db.execute(
        update(ADMatchResult)
        .where(
            ADMatchResult.aircraft_id == aircraft_id,
            ADMatchResult.algorithm_name == ALGORITHM_NAME,
            ADMatchResult.is_current.is_(True),
        )
        .values(is_current=False)
    )
    coverage_stats = resolve_aircraft_ad_coverage(db, aircraft_id)
    entries = db.scalars(
        select(LogbookEntry)
        .where(
            LogbookEntry.aircraft_id == aircraft_id,
            LogbookEntry.entry_date.is_not(None),
            LogbookEntry.review_status == "verified",
        )
        .options(selectinload(LogbookEntry.logbook_section))
        .order_by(LogbookEntry.entry_date.desc(), LogbookEntry.created_at.desc())
    ).all()
    extractions = approved_current_extractions(db)
    structured_entries = {
        entry.id: extract_entry_structure(entry)
        for entry in entries
    }
    sync_verified_time_states(db, aircraft_id=aircraft.id, entries=entries)
    stats = {"directives_seen": 0, "matched": 0, "unresolved": 0, "review_tasks": 0, "skipped_not_applicable": 0}
    for extraction in extractions:
        stats["directives_seen"] += 1
        output = extraction.output
        applicability_contexts = select_applicable_components(aircraft, extraction)
        uncertain_contexts = select_uncertain_components(aircraft, extraction)
        has_structured_applicability = any(
            item.status == "current" and item.source_extraction_id == extraction.id
            for item in extraction.directive.target_applicabilities
        )
        if has_structured_applicability and not applicability_contexts:
            if not uncertain_contexts:
                stats["skipped_not_applicable"] += 1
                continue
        if not has_structured_applicability and not is_potentially_applicable(aircraft, output):
            stats["skipped_not_applicable"] += 1
            continue
        contexts: list[
            tuple[InstalledComponent | None, ADTargetApplicability | None, bool]
        ] = [
            (component, target, True)
            for component, target in applicability_contexts
        ] + [
            (component, target, False)
            for component, target in uncertain_contexts
        ]
        if not contexts:
            contexts = [(None, None, True)]
        for installed_component, target_applicability, applicability_confirmed in contexts:
            result = upsert_match_result(
                db,
                aircraft,
                entries,
                extraction,
                installed_component=installed_component,
                target_applicability=target_applicability,
                structured_entries=structured_entries,
                applicability_confirmed=applicability_confirmed,
                forced_unresolved_reasons=(
                    ["component_applicability_uncertain"]
                    if not applicability_confirmed
                    else None
                ),
            )
            if result.status == "candidate_satisfied":
                stats["matched"] += 1
            else:
                stats["unresolved"] += 1
                if result.adjudication and result.adjudication.status == "pending":
                    stats["review_tasks"] += 1
    record_product_event(
        db,
        event_type="ad_matching_completed",
        subject_type="aircraft",
        subject_id=aircraft.id,
        aircraft_id=aircraft.id,
        event_source="worker",
        properties={
            **stats,
            "algorithm_name": ALGORITHM_NAME,
            "algorithm_version": ALGORITHM_VERSION,
        },
    )
    record_workflow_status(
        db,
        workflow_type="ad_matching",
        workflow_id=aircraft.id,
        new_status="complete",
        reason=f"matched={stats['matched']} unresolved={stats['unresolved']}",
        actor_type="worker",
    )
    record_ad_cost_entry(
        db,
        idempotency_key=None,
        scope_type="aircraft",
        cost_category="ad_logbook_comparison",
        usage_quantity=stats["directives_seen"],
        usage_unit="directive_comparison",
        aircraft_id=aircraft.id,
        organization_id=aircraft.owner_organization_id,
        actual_cost_usd=0,
        allocated_cost_usd=0,
        attribution_status="informational_unallocated",
        metadata={
            "algorithmName": ALGORITHM_NAME,
            "algorithmVersion": ALGORITHM_VERSION,
            "verifiedEntryCount": len(entries),
            "coverageSetsCreated": coverage_stats["coverage_sets_created"],
            "coverageSetsReused": coverage_stats["coverage_sets_reused"],
            "billingActive": False,
        },
    )
    db.commit()
    return stats


def approved_current_extractions(db: Session) -> list[ADExtraction]:
    return released_signed_extractions(db)


def upsert_match_result(
    db: Session,
    aircraft: Aircraft,
    entries: list[LogbookEntry],
    extraction: ADExtraction,
    installed_component: InstalledComponent | None = None,
    target_applicability: ADTargetApplicability | None = None,
    structured_entries: Mapping[str, dict[str, Any]] | None = None,
    applicability_confirmed: bool = True,
    forced_unresolved_reasons: list[str] | None = None,
) -> ADMatchResult:
    output = extraction.output
    evidence = rank_candidate_entries(
        entries,
        output,
        structured_entries=structured_entries,
    )
    requirements = (
        requirements_for_applicability(
            db,
            extraction=extraction,
            applicability=target_applicability,
        )
        if target_applicability is not None and applicability_confirmed
        else []
    )
    match_type, unresolved_reasons = classify_requirement_set(output, requirements)
    unresolved_reasons.extend(forced_unresolved_reasons or [])
    if extraction.directive.superseded_by_edges:
        unresolved_reasons.append("directive_superseded")
    confidence = evidence[0].confidence if evidence else 0.42
    if evidence:
        strongest_evidence = evidence[0]
        if not strongest_evidence.explicit_ad_reference:
            unresolved_reasons.append("explicit_ad_reference_missing")
        if strongest_evidence.disposition_candidate not in {
            "complied",
            "inspected",
        }:
            unresolved_reasons.append("explicit_compliance_claim_missing")
        unresolved_reasons = sorted(set(unresolved_reasons))
    due_states = []
    if requirements:
        strongest_evidence = evidence[0] if evidence else None
        context_binding_required = (
            len(output.get("applicabilityGroups") or []) > 1
            or len(output.get("requirements") or []) > 1
        )
        if len(requirements) > 1 and strongest_evidence:
            unresolved_reasons.append("multiple_requirement_evidence_requires_adjudication")
        for requirement in requirements:
            if (
                len(requirements) == 1
                and strongest_evidence
                and strongest_evidence.explicit_ad_reference
                and strongest_evidence.disposition_candidate in {"complied", "inspected"}
                and (
                    not context_binding_required
                    or evidence_supports_requirement_context(
                        strongest_evidence,
                        requirement,
                        installed_component,
                    )
                )
            ):
                upsert_verified_compliance_event(
                    db,
                    requirement=requirement,
                    aircraft_id=aircraft.id,
                    component=installed_component,
                    entry=strongest_evidence.entry,
                    action_text=strongest_evidence.matched_text,
                    is_terminating_action=evidence_supports_terminating_action(
                        requirement,
                        strongest_evidence.matched_text,
                    ),
                )
            elif (
                len(requirements) == 1
                and strongest_evidence
                and context_binding_required
            ):
                unresolved_reasons.append("component_requirement_evidence_unbound")
            due_state = compute_due_state(
                db,
                aircraft_id=aircraft.id,
                requirement=requirement,
                component=installed_component,
            )
            due_states.append(due_state)
            if due_state.status == "unknown":
                unresolved_reasons.extend(
                    [
                        f"requirement_{requirement.id}_due_status_unknown",
                        *(due_state.unresolved_reasons or []),
                    ]
                )
            elif due_state.status == "due_soon":
                unresolved_reasons.append(f"requirement_{requirement.id}_due_soon")
            elif due_state.status == "overdue":
                unresolved_reasons.append(f"requirement_{requirement.id}_overdue")
        unresolved_reasons = sorted(set(unresolved_reasons))
    elif target_applicability is not None and applicability_confirmed:
        unresolved_reasons.append("compliance_requirement_missing")
    if unresolved_reasons:
        confidence = min(confidence, 0.68)
    applicability_snapshot = build_applicability_snapshot(installed_component, target_applicability)
    if (
        target_applicability
        and installed_component
        and not installed_component.serial_number
    ):
        unresolved_reasons = sorted(set(unresolved_reasons + ["component_serial_unknown"]))
        confidence = min(confidence, 0.72)
    status = "candidate_satisfied" if evidence and not unresolved_reasons else "needs_adjudication"
    rationale = build_rationale(output, evidence, unresolved_reasons)
    input_hash = build_input_hash(
        aircraft,
        entries,
        extraction,
        installed_component,
        target_applicability,
        due_state_input_hashes=[state.input_hash for state in due_states],
    )

    existing = db.scalar(
        select(ADMatchResult).where(
            ADMatchResult.aircraft_id == aircraft.id,
            ADMatchResult.directive_id == extraction.directive_id,
            ADMatchResult.algorithm_name == ALGORITHM_NAME,
            ADMatchResult.algorithm_version == ALGORITHM_VERSION,
            ADMatchResult.input_hash == input_hash,
        )
    )
    if existing:
        result = existing
        result.extraction_id = extraction.id
        result.installed_component_id = installed_component.id if installed_component else None
        result.target_applicability_id = target_applicability.id if target_applicability else None
        result.due_state_id = due_states[0].id if len(due_states) == 1 else None
        result.status = status
        result.match_type = match_type
        result.confidence = confidence
        result.rationale = rationale
        result.unresolved_reasons = unresolved_reasons
        result.applicability_snapshot = applicability_snapshot
        result.is_current = True
        result.computed_at = datetime.now(timezone.utc)
        db.execute(delete(ADMatchEvidence).where(ADMatchEvidence.match_result_id == result.id))
        db.execute(delete(ADMatchDueStateLink).where(ADMatchDueStateLink.match_result_id == result.id))
    else:
        result = ADMatchResult(
            aircraft_id=aircraft.id,
            directive_id=extraction.directive_id,
            extraction_id=extraction.id,
            installed_component_id=installed_component.id if installed_component else None,
            target_applicability_id=target_applicability.id if target_applicability else None,
            due_state_id=due_states[0].id if len(due_states) == 1 else None,
            status=status,
            match_type=match_type,
            confidence=confidence,
            rationale=rationale,
            unresolved_reasons=unresolved_reasons,
            applicability_snapshot=applicability_snapshot,
            algorithm_name=ALGORITHM_NAME,
            algorithm_version=ALGORITHM_VERSION,
            input_hash=input_hash,
            is_current=True,
        )
        db.add(result)
        db.flush()

    for due_state in due_states:
        db.add(
            ADMatchDueStateLink(
                match_result_id=result.id,
                due_state_id=due_state.id,
            )
        )

    for item in evidence[:5]:
        db.add(
            ADMatchEvidence(
                match_result_id=result.id,
                logbook_entry_id=item.entry.id,
                evidence_type="candidate_logbook_entry",
                field_name="description",
                matched_text=item.matched_text,
                confidence=item.confidence,
                rationale=item.rationale,
            )
        )

    ensure_adjudication(db, result, status)
    db.flush()
    return result


def invalidate_aircraft_match_results(
    db: Session,
    *,
    aircraft_id: str,
    actor=None,
) -> int:
    invalidated = db.execute(
        update(ADMatchResult)
        .where(
            ADMatchResult.aircraft_id == aircraft_id,
            ADMatchResult.algorithm_name == ALGORITHM_NAME,
            ADMatchResult.is_current.is_(True),
        )
        .values(is_current=False)
    ).rowcount or 0
    prior_completion = db.scalar(
        select(ProductEvent.id)
        .where(
            ProductEvent.aircraft_id == aircraft_id,
            ProductEvent.event_type == "ad_matching_completed",
        )
        .limit(1)
    )
    if invalidated or prior_completion is not None:
        event = record_product_event(
            db,
            event_type="ad_matching_invalidated",
            subject_type="aircraft",
            subject_id=aircraft_id,
            actor=actor,
            aircraft_id=aircraft_id,
            properties={
                "algorithm_name": ALGORITHM_NAME,
                "algorithm_version": ALGORITHM_VERSION,
                "invalidated_result_count": invalidated,
            },
        )
        event.event_time = datetime.now(timezone.utc)
    return invalidated


def ensure_adjudication(db: Session, result: ADMatchResult, status: str) -> None:
    existing = db.scalar(select(ADMatchAdjudication).where(ADMatchAdjudication.match_result_id == result.id))
    if status == "needs_adjudication":
        if not existing:
            db.add(ADMatchAdjudication(match_result_id=result.id, status="pending"))
        elif existing.status != "pending":
            existing.status = "pending"
            existing.decision = None
            existing.reviewer_user_id = None
            existing.notes = None
            existing.reviewed_at = None
        return
    if existing and existing.status == "pending":
        existing.status = "not_required"


def is_potentially_applicable(aircraft: Aircraft, output: dict[str, Any]) -> bool:
    products = [str(item).lower() for item in output.get("affectedProducts") or [] if item]
    if not products:
        return True
    aircraft_terms = {
        value.lower()
        for value in [
            aircraft.make,
            aircraft.model,
            aircraft.engine_make,
            aircraft.engine_model,
            aircraft.propeller_make,
            aircraft.propeller_model,
        ]
        if value
    }
    joined_aircraft = " ".join(sorted(aircraft_terms))
    return any(product in joined_aircraft or any(term in product for term in aircraft_terms) for product in products)


def select_applicable_components(
    aircraft: Aircraft,
    extraction: ADExtraction,
) -> list[tuple[InstalledComponent, ADTargetApplicability]]:
    """Return every signed component/group context that is positively applicable."""

    active_components = [component for component in aircraft.installed_components if component.removed_at is None]
    matches: list[tuple[InstalledComponent, ADTargetApplicability, float]] = []
    for applicability in extraction.directive.target_applicabilities:
        target = applicability.target
        if (
            applicability.status != "current"
            or applicability.source_extraction_id != extraction.id
        ):
            continue
        target_role = infer_component_role(target.product_type, target.product_subtype)
        for component in active_components:
            if evaluate_component_applicability(component, applicability, target_role) != "applicable":
                continue
            score = component_target_score(component, applicability, target_role)
            if score <= 0:
                continue
            matches.append((component, applicability, score))
    matches.sort(key=lambda item: (-item[2], item[1].id, item[0].id))
    return [(component, applicability) for component, applicability, _score in matches]


def select_uncertain_components(
    aircraft: Aircraft,
    extraction: ADExtraction,
) -> list[tuple[InstalledComponent, ADTargetApplicability]]:
    """Retain every plausible context whose signed predicates cannot be decided."""

    active_components = [
        component
        for component in aircraft.installed_components
        if component.removed_at is None
    ]
    matches: list[tuple[InstalledComponent, ADTargetApplicability, float]] = []
    for applicability in extraction.directive.target_applicabilities:
        if (
            applicability.status != "current"
            or applicability.source_extraction_id != extraction.id
        ):
            continue
        target_role = infer_component_role(
            applicability.target.product_type,
            applicability.target.product_subtype,
        )
        for component in active_components:
            if evaluate_component_applicability(component, applicability, target_role) != "uncertain":
                continue
            score = max(
                component_target_score(component, applicability, target_role),
                component_target_role_score(component, target_role),
            )
            if score > 0:
                matches.append((component, applicability, score))
    matches.sort(key=lambda item: (-item[2], item[1].id, item[0].id))
    return [(component, applicability) for component, applicability, _score in matches]


def select_applicable_component(aircraft: Aircraft, extraction: ADExtraction) -> tuple[InstalledComponent, ADTargetApplicability] | None:
    """Compatibility helper for callers that only display one context."""

    contexts = select_applicable_components(aircraft, extraction)
    return contexts[0] if contexts else None


def structured_applicability_is_uncertain(
    aircraft: Aircraft,
    extraction: ADExtraction,
) -> bool:
    return bool(select_uncertain_components(aircraft, extraction))


def evaluate_component_applicability(
    component: InstalledComponent,
    applicability: ADTargetApplicability,
    target_role: str,
) -> str:
    """Evaluate the full signed applicability row without guessing."""

    target = applicability.target
    if component_target_role_score(component, target_role) <= 0:
        return "not_applicable"
    for component_value, target_value in (
        (component.make, target.make),
        (component.model, target.model),
    ):
        if not target_value:
            continue
        if not component_value:
            return "uncertain"
        if not text_matches(component_value, target_value):
            return "not_applicable"

    source_identity = applicability.source_identity or {}
    model_scope = source_identity.get("modelApplicability") or {}
    if model_scope.get("kind") in {"expression", "unknown"}:
        return "uncertain"

    serial_status = evaluate_serial_scope(
        component.serial_number,
        applicability.serial_range or {},
    )
    if serial_status != "applicable":
        return serial_status
    if applicability.equipment_conditions or applicability.conditions:
        return "uncertain"
    source_payload = applicability.source_payload or {}
    if source_payload.get("uncertaintyReasons"):
        return "uncertain"
    return "applicable"


def evaluate_serial_scope(serial_number: str | None, scope: dict[str, Any]) -> str:
    kind = scope.get("kind") or "unknown"
    excluded = {
        normalize_serial(value)
        for value in scope.get("excludedValues") or []
        if normalize_serial(value)
    }
    serial = normalize_serial(serial_number)
    if serial and serial in excluded:
        return "not_applicable"
    if kind == "all":
        return "applicable"
    if kind in {"expression", "unknown"}:
        return "uncertain"
    if not serial:
        return "uncertain"
    if kind == "values":
        allowed = {
            normalize_serial(value)
            for value in scope.get("values") or []
            if normalize_serial(value)
        }
        return "applicable" if serial in allowed else "not_applicable"
    if kind == "ranges":
        comparisons = [
            serial_in_range(serial, item)
            for item in scope.get("ranges") or []
            if isinstance(item, dict)
        ]
        if any(result is True for result in comparisons):
            return "applicable"
        if comparisons and all(result is False for result in comparisons):
            return "not_applicable"
        return "uncertain"
    return "uncertain"


def normalize_serial(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())


def serial_in_range(serial: str, serial_range: dict[str, Any]) -> bool | None:
    serial_key = comparable_serial_key(serial)
    start = normalize_serial(serial_range.get("start"))
    end = normalize_serial(serial_range.get("end"))
    start_key = comparable_serial_key(start) if start else None
    end_key = comparable_serial_key(end) if end else None
    if serial_key is None or (start and start_key is None) or (end and end_key is None):
        return None
    bounds = [key for key in (start_key, end_key) if key is not None]
    if any(serial_key[0] != key[0] for key in bounds):
        return None
    values = serial_key[1]
    if start_key is not None and values < start_key[1]:
        return False
    if end_key is not None and values > end_key[1]:
        return False
    return True


def comparable_serial_key(value: str) -> tuple[tuple[str, ...], tuple[Any, ...]] | None:
    if not value:
        return None
    raw_parts = re.findall(r"[A-Z]+|\d+", value)
    if not raw_parts or "".join(raw_parts) != value:
        return None
    signature = tuple("n" if part.isdigit() else "s" for part in raw_parts)
    normalized = tuple(int(part) if part.isdigit() else part for part in raw_parts)
    return signature, normalized


def component_target_role_score(
    component: InstalledComponent,
    target_role: str,
) -> float:
    compatible_roles = {
        "airframe": {"airframe", "rotorcraft_airframe"},
        "rotorcraft_airframe": {"airframe", "rotorcraft_airframe"},
        "engine": {"engine"},
        "propeller": {"propeller", "rotor_system"},
        "rotor_system": {"rotor_system", "propeller"},
        "drivetrain_transmission": {"drivetrain_transmission"},
        "appliance": {"appliance", "other", "unknown"},
        "unknown": {
            "airframe",
            "engine",
            "propeller",
            "rotorcraft_airframe",
            "rotor_system",
            "drivetrain_transmission",
            "appliance",
            "other",
            "unknown",
        },
    }
    return 0.25 if component.role in compatible_roles.get(
        target_role, {target_role}
    ) else 0.0


def component_target_score(component: InstalledComponent, applicability: ADTargetApplicability, target_role: str) -> float:
    target = applicability.target
    score = component_target_role_score(component, target_role)
    if score <= 0:
        return 0.0
    if text_matches(component.make, target.make):
        score += 0.35
    elif target.make:
        return 0.0
    if text_matches(component.model, target.model):
        score += 0.35
    elif target.model:
        return 0.0
    return score


def text_matches(component_value: str | None, target_value: str | None) -> bool:
    if not target_value:
        return True
    if not component_value:
        return False
    component_text = normalize_match_text(component_value)
    target_text = normalize_match_text(target_value)
    return component_text == target_text


def identity_is_close(
    component_value: str | None,
    target_value: str | None,
) -> bool:
    if not component_value or not target_value:
        return False
    component_text = normalize_match_text(component_value)
    target_text = normalize_match_text(target_value)
    if component_text == target_text:
        return False
    return (
        min(len(component_text), len(target_text)) >= 4
        and (
            component_text.startswith(target_text)
            or target_text.startswith(component_text)
        )
    )


def normalize_match_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def build_applicability_snapshot(
    component: InstalledComponent | None,
    applicability: ADTargetApplicability | None,
) -> dict[str, Any] | None:
    if component is None and applicability is None:
        return None
    target = applicability.target if applicability else None
    publication = applicability.source_publication if applicability else None
    return {
        "component": {
            "id": component.id,
            "role": component.role,
            "make": component.make,
            "model": component.model,
            "serialNumber": component.serial_number,
        }
        if component
        else None,
        "target": {
            "id": target.id,
            "productType": target.product_type,
            "productSubtype": target.product_subtype,
            "make": target.make,
            "model": target.model,
        }
        if target
        else None,
        "basis": applicability.applicability_basis if applicability else None,
        "sourceSystem": publication.source_system if publication else None,
        "sourceStatus": publication.status if publication else None,
        "serialStatus": "known" if component and component.serial_number else "unknown",
    }


def rank_candidate_entries(
    entries: list[LogbookEntry],
    output: dict[str, Any],
    *,
    structured_entries: Mapping[str, dict[str, Any]] | None = None,
) -> list[CandidateEvidence]:
    ranked: list[CandidateEvidence] = []
    ad_number = normalize_ad_number(str(output.get("adNumber") or ""))
    product_terms = keywords(" ".join(str(item) for item in output.get("affectedProducts") or []))
    action_terms = keywords(" ".join(str(item) for item in output.get("complianceActions") or [])) | ACTION_WORDS
    title_terms = keywords(str(output.get("title") or ""))

    for entry in entries:
        text = " ".join(filter(None, [entry.description, entry.raw_text])).lower()
        structured = (
            structured_entries.get(entry.id)
            if structured_entries is not None
            else None
        )
        if structured is None:
            structured = extract_entry_structure(entry)
        matching_references = [
            reference
            for reference in structured["adReferences"]
            if reference["adNumber"] == ad_number
        ]
        strongest_reference = matching_references[0] if matching_references else None
        score = 0.0
        reasons: list[str] = []
        if strongest_reference:
            disposition = strongest_reference["dispositionCandidate"]
            score += 0.82 if disposition in {"complied", "inspected"} else 0.45
            reasons.append(
                "logbook text explicitly cites the normalized AD number "
                f"with disposition candidate '{disposition}'"
            )
        elif ad_number and ad_number.lower() in text:
            score += 0.45
            reasons.append("logbook text cites the AD number without a parsed compliance claim")
        product_overlap = product_terms.intersection(keywords(text))
        if product_overlap:
            score += min(0.16, 0.04 * len(product_overlap))
            reasons.append(f"product terms overlap: {', '.join(sorted(product_overlap)[:4])}")
        action_overlap = action_terms.intersection(keywords(text))
        if action_overlap:
            score += min(0.18, 0.04 * len(action_overlap))
            reasons.append(f"maintenance action terms overlap: {', '.join(sorted(action_overlap)[:4])}")
        title_overlap = title_terms.intersection(keywords(text))
        if title_overlap:
            score += min(0.1, 0.025 * len(title_overlap))
            reasons.append(f"title terms overlap: {', '.join(sorted(title_overlap)[:4])}")
        if score >= 0.2:
            ranked.append(
                CandidateEvidence(
                    entry=entry,
                    confidence=min(0.95, score),
                    rationale="; ".join(reasons),
                    matched_text=entry.raw_text or entry.description,
                    explicit_ad_reference=strongest_reference is not None,
                    disposition_candidate=(
                        strongest_reference["dispositionCandidate"]
                        if strongest_reference
                        else None
                    ),
                )
            )

    return sorted(ranked, key=lambda item: item.confidence, reverse=True)


def evidence_supports_requirement_context(
    evidence: CandidateEvidence,
    requirement: Any,
    component: InstalledComponent | None,
) -> bool:
    """Require multi-obligation log evidence to identify its exact context."""

    if component is None:
        return False
    section_key = (
        evidence.entry.logbook_section.key
        if evidence.entry.logbook_section is not None
        else None
    )
    compatible_sections = {
        "airframe": {"airframe"},
        "rotorcraft_airframe": {"airframe"},
        "engine": {"engine"},
        "propeller": {"propeller"},
        "rotor_system": {"propeller"},
    }
    if section_key in compatible_sections.get(component.role, {component.role}):
        return True

    text = normalize_match_text(evidence.matched_text)
    for identity in (component.role, component.make, component.model):
        normalized = normalize_match_text(str(identity or ""))
        if len(normalized) >= 4 and normalized in text:
            return True

    generic = ACTION_WORDS | {
        "affected", "part", "parts", "required", "action", "actions",
        "component", "components", "within", "after", "before",
    }
    requirement_terms = keywords(str(requirement.action_text or "")) - generic
    return bool(requirement_terms.intersection(keywords(evidence.matched_text)))


def extract_entry_structure(entry: LogbookEntry) -> dict[str, Any]:
    return extract_structured_maintenance_data(
        "\n".join(
            filter(
                None,
                [entry.raw_text, entry.description],
            )
        ).splitlines()
    )


def classify_requirement_set(
    output: dict[str, Any],
    requirements: list[Any],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not output.get("applicabilityGroups") and not output.get("affectedProducts"):
        reasons.append("applicability_unknown")
    if len(requirements) > 1:
        match_type = "multi_obligation"
    elif requirements and requirements[0].requirement_type == "recurring":
        match_type = "simple_recurring"
    else:
        match_type = "one_time"
    if not requirements:
        reasons.append("compliance_requirement_missing")
    if not output.get("requirements") and not output.get("complianceActions"):
        reasons.append("compliance_action_unknown")
    return match_type, reasons


def build_rationale(output: dict[str, Any], evidence: list[CandidateEvidence], unresolved_reasons: list[str]) -> str:
    ad_number = output.get("adNumber") or "unknown AD"
    if evidence and not unresolved_reasons:
        return f"Candidate satisfied: found logbook evidence for {ad_number} with {evidence[0].rationale}."
    if evidence:
        return f"Needs adjudication: found possible evidence for {ad_number}, but unresolved reasons remain: {', '.join(unresolved_reasons)}."
    return f"Needs adjudication: no logbook entry cites or strongly matches {ad_number}."


def build_input_hash(
    aircraft: Aircraft,
    entries: list[LogbookEntry],
    extraction: ADExtraction,
    installed_component: InstalledComponent | None = None,
    target_applicability: ADTargetApplicability | None = None,
    due_state_input_hashes: list[str] | None = None,
) -> str:
    payload = {
        "aircraft": {
            "id": aircraft.id,
            "make": aircraft.make,
            "model": aircraft.model,
            "serial": aircraft.serial_number,
            "engineMake": aircraft.engine_make,
            "engineModel": aircraft.engine_model,
            "propellerMake": aircraft.propeller_make,
            "propellerModel": aircraft.propeller_model,
            "components": [
                {
                    "id": component.id,
                    "role": component.role,
                    "type": component.component_type,
                    "make": component.make,
                    "model": component.model,
                    "serial": component.serial_number,
                }
                for component in sorted(aircraft.installed_components, key=lambda item: item.id)
                if component.removed_at is None
            ],
        },
        "selectedApplicability": {
            "componentId": installed_component.id if installed_component else None,
            "targetApplicabilityId": target_applicability.id if target_applicability else None,
        },
        "dueStateInputHashes": sorted(due_state_input_hashes or []),
        "extraction": {
            "id": extraction.id,
            "inputContentHash": extraction.input_content_hash,
            "output": extraction.output,
        },
        "entries": [
            {
                "id": entry.id,
                "date": entry.entry_date.isoformat(),
                "description": entry.description,
                "rawText": entry.raw_text,
                "reviewStatus": entry.review_status,
                "tachTime": entry.tach_time,
                "hobbsTime": entry.hobbs_time,
                "totalTime": entry.total_time,
            }
            for entry in entries
        ],
    }
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def keywords(text: str) -> set[str]:
    return {
        value
        for value in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9-]{2,}", text.lower())
        if value not in {"the", "and", "for", "with", "this", "that", "from", "all", "model"}
    }
