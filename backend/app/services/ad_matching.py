from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.core import (
    ADExtraction,
    ADMatchAdjudication,
    ADMatchEvidence,
    ADMatchResult,
    ADTargetApplicability,
    Aircraft,
    AirworthinessDirective,
    InstalledComponent,
    LogbookEntry,
)
from app.services.ad_applicability import infer_component_role
from app.services.observability import record_product_event, record_workflow_status

ALGORITHM_NAME = "deterministic_ad_logbook_matcher"
ALGORITHM_VERSION = "0.1.0"
ACTION_WORDS = {"comply", "complied", "compliance", "inspect", "inspection", "replace", "replaced", "modify", "modified"}


@dataclass(frozen=True)
class CandidateEvidence:
    entry: LogbookEntry
    confidence: float
    rationale: str
    matched_text: str


def match_aircraft_ads(db: Session, aircraft_id: str) -> dict[str, int]:
    aircraft = db.scalar(select(Aircraft).where(Aircraft.id == aircraft_id).options(selectinload(Aircraft.installed_components)))
    if not aircraft:
        raise ValueError("Aircraft not found")

    entries = db.scalars(
        select(LogbookEntry)
        .where(LogbookEntry.aircraft_id == aircraft_id)
        .options(selectinload(LogbookEntry.logbook_section))
        .order_by(LogbookEntry.entry_date.desc(), LogbookEntry.created_at.desc())
    ).all()
    extractions = approved_current_extractions(db)
    stats = {"directives_seen": 0, "matched": 0, "unresolved": 0, "review_tasks": 0, "skipped_not_applicable": 0}
    for extraction in extractions:
        stats["directives_seen"] += 1
        output = extraction.output
        applicability = select_applicable_component(aircraft, extraction)
        has_structured_applicability = bool(extraction.directive.target_applicabilities)
        if has_structured_applicability and applicability is None:
            stats["skipped_not_applicable"] += 1
            continue
        if not has_structured_applicability and not is_potentially_applicable(aircraft, output):
            stats["skipped_not_applicable"] += 1
            continue
        result = upsert_match_result(
            db,
            aircraft,
            entries,
            extraction,
            installed_component=applicability[0] if applicability else None,
            target_applicability=applicability[1] if applicability else None,
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
        properties=stats,
    )
    record_workflow_status(
        db,
        workflow_type="ad_matching",
        workflow_id=aircraft.id,
        new_status="complete",
        reason=f"matched={stats['matched']} unresolved={stats['unresolved']}",
        actor_type="worker",
    )
    db.commit()
    return stats


def approved_current_extractions(db: Session) -> list[ADExtraction]:
    return db.scalars(
        select(ADExtraction)
        .where(ADExtraction.status == "approved")
        .options(
            selectinload(ADExtraction.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.target_applicabilities)
            .selectinload(ADTargetApplicability.target),
            selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.target_applicabilities)
            .selectinload(ADTargetApplicability.source_publication),
            selectinload(ADExtraction.directive).selectinload(AirworthinessDirective.superseded_by_edges),
        )
        .order_by(ADExtraction.created_at.desc())
    ).all()


def upsert_match_result(
    db: Session,
    aircraft: Aircraft,
    entries: list[LogbookEntry],
    extraction: ADExtraction,
    installed_component: InstalledComponent | None = None,
    target_applicability: ADTargetApplicability | None = None,
) -> ADMatchResult:
    output = extraction.output
    evidence = rank_candidate_entries(entries, output)
    match_type, unresolved_reasons = classify_match_type(output)
    confidence = evidence[0].confidence if evidence else 0.42
    if unresolved_reasons:
        confidence = min(confidence, 0.68)
    applicability_snapshot = build_applicability_snapshot(installed_component, target_applicability)
    if target_applicability and not installed_component.serial_number:
        unresolved_reasons = sorted(set(unresolved_reasons + ["component_serial_unknown"]))
        confidence = min(confidence, 0.72)
    status = "candidate_satisfied" if evidence and not unresolved_reasons else "needs_adjudication"
    rationale = build_rationale(output, evidence, unresolved_reasons)
    input_hash = build_input_hash(aircraft, entries, extraction, installed_component, target_applicability)

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
        result.status = status
        result.match_type = match_type
        result.confidence = confidence
        result.rationale = rationale
        result.unresolved_reasons = unresolved_reasons
        result.applicability_snapshot = applicability_snapshot
        result.computed_at = datetime.now(timezone.utc)
        db.execute(delete(ADMatchEvidence).where(ADMatchEvidence.match_result_id == result.id))
    else:
        result = ADMatchResult(
            aircraft_id=aircraft.id,
            directive_id=extraction.directive_id,
            extraction_id=extraction.id,
            installed_component_id=installed_component.id if installed_component else None,
            target_applicability_id=target_applicability.id if target_applicability else None,
            status=status,
            match_type=match_type,
            confidence=confidence,
            rationale=rationale,
            unresolved_reasons=unresolved_reasons,
            applicability_snapshot=applicability_snapshot,
            algorithm_name=ALGORITHM_NAME,
            algorithm_version=ALGORITHM_VERSION,
            input_hash=input_hash,
        )
        db.add(result)
        db.flush()

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


def select_applicable_component(aircraft: Aircraft, extraction: ADExtraction) -> tuple[InstalledComponent, ADTargetApplicability] | None:
    active_components = [component for component in aircraft.installed_components if component.removed_at is None]
    best: tuple[InstalledComponent, ADTargetApplicability, float] | None = None
    for applicability in extraction.directive.target_applicabilities:
        target = applicability.target
        if applicability.status not in {"current", "active", "unknown"}:
            continue
        target_role = infer_component_role(target.product_type, target.product_subtype)
        for component in active_components:
            score = component_target_score(component, applicability, target_role)
            if score <= 0:
                continue
            if best is None or score > best[2]:
                best = (component, applicability, score)
    if best is None:
        return None
    return best[0], best[1]


def component_target_score(component: InstalledComponent, applicability: ADTargetApplicability, target_role: str) -> float:
    target = applicability.target
    score = 0.0
    compatible_roles = {
        "airframe": {"airframe", "rotorcraft_airframe"},
        "rotorcraft_airframe": {"airframe", "rotorcraft_airframe"},
        "engine": {"engine"},
        "propeller": {"propeller", "rotor_system"},
        "rotor_system": {"rotor_system", "propeller"},
        "drivetrain_transmission": {"drivetrain_transmission"},
        "appliance": {"appliance", "other", "unknown"},
        "unknown": {"airframe", "engine", "propeller", "rotorcraft_airframe", "rotor_system", "drivetrain_transmission", "appliance", "other", "unknown"},
    }
    if component.role not in compatible_roles.get(target_role, {target_role}):
        return 0.0
    score += 0.25
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
    return component_text in target_text or target_text in component_text


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


def rank_candidate_entries(entries: list[LogbookEntry], output: dict[str, Any]) -> list[CandidateEvidence]:
    ranked: list[CandidateEvidence] = []
    ad_number = str(output.get("adNumber") or "").lower()
    product_terms = keywords(" ".join(str(item) for item in output.get("affectedProducts") or []))
    action_terms = keywords(" ".join(str(item) for item in output.get("complianceActions") or [])) | ACTION_WORDS
    title_terms = keywords(str(output.get("title") or ""))

    for entry in entries:
        text = " ".join(filter(None, [entry.description, entry.raw_text])).lower()
        score = 0.0
        reasons: list[str] = []
        if ad_number and ad_number in text:
            score += 0.7
            reasons.append("logbook text cites the AD number")
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
                )
            )

    return sorted(ranked, key=lambda item: item.confidence, reverse=True)


def classify_match_type(output: dict[str, Any]) -> tuple[str, list[str]]:
    intervals = output.get("complianceIntervals") or []
    products = output.get("affectedProducts") or []
    reasons: list[str] = []
    if not products:
        reasons.append("applicability_unknown")
    if intervals:
        match_type = "simple_recurring"
        normalized_intervals = [item for item in intervals if isinstance(item, dict)]
        if not normalized_intervals:
            reasons.append("recurring_interval_unstructured")
    else:
        match_type = "one_time"
    if not output.get("complianceActions"):
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
