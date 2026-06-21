from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    ADExtraction,
    ADPublication,
    ADReconciliationIssue,
    ADTargetApplicability,
    AirworthinessDirective,
    ApplicabilityTarget,
)
from app.services.installed_components import (
    ROLE_AIRFRAME,
    ROLE_APPLIANCE,
    ROLE_DRIVETRAIN_TRANSMISSION,
    ROLE_ENGINE,
    ROLE_PROPELLER,
    ROLE_ROTORCRAFT_AIRFRAME,
    ROLE_ROTOR_SYSTEM,
    ROLE_UNKNOWN,
)


def normalize_key(*values: str | None) -> str:
    parts = []
    for value in values:
        cleaned = " ".join(str(value or "").strip().lower().split())
        parts.append(cleaned)
    return "|".join(parts)


def get_or_create_target(
    db: Session,
    *,
    product_type: str | None,
    product_subtype: str | None,
    make: str | None,
    model: str | None,
) -> ApplicabilityTarget:
    product_type = clean(product_type) or "unknown"
    product_subtype = clean(product_subtype)
    make = clean(make)
    model = clean(model)
    key = normalize_key(product_type, product_subtype, make, model)
    target = db.scalar(select(ApplicabilityTarget).where(ApplicabilityTarget.normalized_key == key))
    if target is None:
        target = ApplicabilityTarget(
            product_type=product_type,
            product_subtype=product_subtype,
            make=make,
            model=model,
            normalized_key=key,
        )
        db.add(target)
        db.flush()
    return target


def upsert_target_applicability(
    db: Session,
    *,
    directive: AirworthinessDirective,
    target: ApplicabilityTarget,
    source_publication: ADPublication | None,
    basis: str,
    compliance_actions: list | None = None,
    compliance_intervals: list | None = None,
    conditions: list | None = None,
    citations: list | None = None,
    confidence: float = 0.8,
    status: str = "current",
) -> ADTargetApplicability:
    applicability = db.scalar(
        select(ADTargetApplicability).where(
            ADTargetApplicability.directive_id == directive.id,
            ADTargetApplicability.target_id == target.id,
            ADTargetApplicability.source_publication_id == (source_publication.id if source_publication else None),
            ADTargetApplicability.applicability_basis == basis,
        )
    )
    if applicability is None:
        applicability = ADTargetApplicability(
            directive_id=directive.id,
            target_id=target.id,
            source_publication_id=source_publication.id if source_publication else None,
            applicability_basis=basis,
        )
        db.add(applicability)
    applicability.compliance_actions = compliance_actions or []
    applicability.compliance_intervals = compliance_intervals or []
    applicability.conditions = conditions or []
    applicability.citations = citations or []
    applicability.confidence = confidence
    applicability.status = status
    db.flush()
    return applicability


def populate_applicability_from_extraction(db: Session, extraction: ADExtraction) -> int:
    output = extraction.output or {}
    products = [str(item) for item in output.get("affectedProducts") or [] if item]
    if not products:
        ensure_issue(
            db,
            directive=extraction.directive,
            issue_type="missing_extracted_applicability",
            severity="medium",
            payload={"extractionId": extraction.id},
        )
        return 0

    count = 0
    for product in products:
        parsed = parse_product_text(product)
        target = get_or_create_target(db, **parsed)
        upsert_target_applicability(
            db,
            directive=extraction.directive,
            target=target,
            source_publication=None,
            basis="extraction",
            compliance_actions=output.get("complianceActions") or [],
            compliance_intervals=output.get("complianceIntervals") or [],
            citations=extraction.citations or [],
            confidence=min(0.86, max(0.55, extraction.confidence)),
            status="current",
        )
        count += 1
    return count


def infer_component_role(product_type: str | None, product_subtype: str | None = None) -> str:
    text = f"{product_type or ''} {product_subtype or ''}".lower()
    if "rotor" in text and "drive" in text:
        return ROLE_DRIVETRAIN_TRANSMISSION
    if "rotor" in text and ("system" in text or "blade" in text or "hub" in text):
        return ROLE_ROTOR_SYSTEM
    if "rotorcraft" in text or "helicopter" in text:
        return ROLE_ROTORCRAFT_AIRFRAME
    if "engine" in text:
        return ROLE_ENGINE
    if "propeller" in text:
        return ROLE_PROPELLER
    if "appliance" in text or "equipment" in text:
        return ROLE_APPLIANCE
    if "aircraft" in text or "airplane" in text:
        return ROLE_AIRFRAME
    return ROLE_UNKNOWN


def parse_product_text(product: str) -> dict[str, str | None]:
    text = product.strip()
    lower = text.lower()
    product_type = "Aircraft"
    if "engine" in lower:
        product_type = "Engine"
    elif "propeller" in lower:
        product_type = "Propeller"
    elif "rotorcraft" in lower or "helicopter" in lower:
        product_type = "Rotorcraft"

    cleaned = re.sub(r"\b(airplanes?|aircraft|engines?|propellers?|rotorcraft|helicopters?)\b", "", text, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.replace(";", " ").split())
    words = cleaned.split()
    make = words[0] if words else None
    model = " ".join(words[1:]) if len(words) > 1 else None
    return {"product_type": product_type, "product_subtype": None, "make": make, "model": model}


def ensure_issue(
    db: Session,
    *,
    directive: AirworthinessDirective | None,
    issue_type: str,
    severity: str,
    payload: dict[str, Any],
) -> ADReconciliationIssue:
    issue = db.scalar(
        select(ADReconciliationIssue).where(
            ADReconciliationIssue.directive_id == (directive.id if directive else None),
            ADReconciliationIssue.issue_type == issue_type,
            ADReconciliationIssue.status == "open",
        )
    )
    if issue is None:
        issue = ADReconciliationIssue(
            directive_id=directive.id if directive else None,
            issue_type=issue_type,
            severity=severity,
            payload=payload,
        )
        db.add(issue)
    else:
        issue.payload = payload
        issue.severity = severity
    db.flush()
    return issue


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = " ".join(str(value).strip().split())
    return stripped or None
