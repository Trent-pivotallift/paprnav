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
    Aircraft,
    AirworthinessDirective,
    LogbookEntry,
)

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
    aircraft = db.scalar(select(Aircraft).where(Aircraft.id == aircraft_id))
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
        if not is_potentially_applicable(aircraft, output):
            stats["skipped_not_applicable"] += 1
            continue
        result = upsert_match_result(db, aircraft, entries, extraction)
        if result.status == "candidate_satisfied":
            stats["matched"] += 1
        else:
            stats["unresolved"] += 1
            if result.adjudication and result.adjudication.status == "pending":
                stats["review_tasks"] += 1
    db.commit()
    return stats


def approved_current_extractions(db: Session) -> list[ADExtraction]:
    return db.scalars(
        select(ADExtraction)
        .where(ADExtraction.status == "approved")
        .options(
            selectinload(ADExtraction.directive).selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADExtraction.directive).selectinload(AirworthinessDirective.superseded_by_edges),
        )
        .order_by(ADExtraction.created_at.desc())
    ).all()


def upsert_match_result(
    db: Session,
    aircraft: Aircraft,
    entries: list[LogbookEntry],
    extraction: ADExtraction,
) -> ADMatchResult:
    output = extraction.output
    evidence = rank_candidate_entries(entries, output)
    match_type, unresolved_reasons = classify_match_type(output)
    status = "candidate_satisfied" if evidence and not unresolved_reasons else "needs_adjudication"
    confidence = evidence[0].confidence if evidence else 0.42
    if unresolved_reasons:
        confidence = min(confidence, 0.68)
    rationale = build_rationale(output, evidence, unresolved_reasons)
    input_hash = build_input_hash(aircraft, entries, extraction)

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
        result.status = status
        result.match_type = match_type
        result.confidence = confidence
        result.rationale = rationale
        result.unresolved_reasons = unresolved_reasons
        result.computed_at = datetime.now(timezone.utc)
        db.execute(delete(ADMatchEvidence).where(ADMatchEvidence.match_result_id == result.id))
    else:
        result = ADMatchResult(
            aircraft_id=aircraft.id,
            directive_id=extraction.directive_id,
            extraction_id=extraction.id,
            status=status,
            match_type=match_type,
            confidence=confidence,
            rationale=rationale,
            unresolved_reasons=unresolved_reasons,
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


def build_input_hash(aircraft: Aircraft, entries: list[LogbookEntry], extraction: ADExtraction) -> str:
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
