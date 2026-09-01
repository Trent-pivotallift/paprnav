from __future__ import annotations

import hashlib
import io
import json
import math
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from pypdf import PdfReader

from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADPublication,
    ADTargetApplicability,
    AirworthinessDirective,
    ApplicabilityTarget,
)
from app.services.storage import read_stored_file_bytes
from app.services.ad_applicability import populate_applicability_from_extraction
from app.services.ad_discovery import extract_ad_number
from app.services.observability import record_product_event, record_workflow_status

PROVIDER_NAME = "deterministic_ad_extractor"
PROVIDER_VERSION = "0.1.0"
OPENAI_PROVIDER_NAME = "openai_responses_ad_extractor"
OPENAI_PROMPT_VERSION = "ad_full_text_compliance_prompt_v3"
SCHEMA_VERSION = "ad_extraction_v3"
REVIEW_THRESHOLD = 0.86
LLM_REVIEW_THRESHOLD = 0.80
AD_NUMBER_PATTERN = re.compile(r"\b(?:AD\s*)?(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE)
AD_EXTRACTION_SYSTEM_PROMPT = """Extract structured FAA Airworthiness Directive data for paprnav.
Return only facts supported by the supplied source text. Use null or empty lists when the source does not support a field.
Confidence is your 0.0-1.0 estimate that the extracted fields are complete and source-supported.
Create source-faithful applicabilityGroups. Keep manufacturer sourceName separate from every model sourceDesignation.
Do not concatenate manufacturer and model, and do not emit manufacturer and model as unrelated sibling values.
Use normalizedName/normalizedDesignation only when a conservative canonical identity is supported; otherwise use null.
Preserve serial scope, installed-equipment conditions, applicability conditions, and page citations in each group.
Create a separate requirement for each compliance action or alternative. Keep initial thresholds separate from recurring triggers.
Every requirement must list the applicabilityGroupKeys it governs.
Set complianceActions to the ordered actionText values from requirements; requirements are the authoritative compliance structure.
Capture the AD's alternative-method-of-compliance paragraph in amocProvisions. Do not treat an AMOC provision as an in-rule alternative requirement.
Every requirement citation must use the source-document ID and page number printed in the supplied source text.
Set uncertaintyReasons when applicability, compliance, dates, trigger logic, conditions, or supersession data are missing or ambiguous."""
AD_THRESHOLD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["metric", "value", "unit", "anchorKind", "sourceText"],
    "properties": {
        "metric": {"type": "string", "enum": ["calendar", "tach_hours", "hobbs_hours", "total_time_hours", "cycles"]},
        "value": {"type": "number", "exclusiveMinimum": 0},
        "unit": {"type": "string", "enum": ["days", "months", "hours", "cycles"]},
        "anchorKind": {"type": "string", "enum": ["effective_date", "last_compliance", "installation", "manufacture", "unknown"]},
        "sourceText": {"type": "string"},
    },
}
AD_PAGE_CITATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["sourceDocumentId", "pageNumber", "text"],
    "properties": {
        "sourceDocumentId": {"type": "string"},
        "pageNumber": {"type": "integer", "minimum": 1},
        "text": {"type": "string"},
    },
}
AD_MANUFACTURER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["sourceName", "normalizedName"],
    "properties": {
        "sourceName": {"type": "string"},
        "normalizedName": {"type": ["string", "null"]},
    },
}
AD_MODEL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["sourceDesignation", "normalizedDesignation", "aliases"],
    "properties": {
        "sourceDesignation": {"type": "string"},
        "normalizedDesignation": {"type": ["string", "null"]},
        "aliases": {"type": "array", "items": {"type": "string"}},
    },
}
AD_SERIAL_APPLICABILITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "values", "ranges", "excludedValues", "sourceText"],
    "properties": {
        "kind": {"type": "string", "enum": ["all", "values", "ranges", "expression", "unknown"]},
        "values": {"type": "array", "items": {"type": "string"}},
        "ranges": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["start", "end"],
                "properties": {
                    "start": {"type": ["string", "null"]},
                    "end": {"type": ["string", "null"]},
                },
            },
        },
        "excludedValues": {"type": "array", "items": {"type": "string"}},
        "sourceText": {"type": ["string", "null"]},
    },
}
AD_EQUIPMENT_CONDITION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "conditionKey", "productType", "manufacturer", "model", "softwareVersions",
        "conditionText", "citations",
    ],
    "properties": {
        "conditionKey": {"type": "string"},
        "productType": {"type": "string"},
        "manufacturer": AD_MANUFACTURER_SCHEMA,
        "model": {"anyOf": [AD_MODEL_SCHEMA, {"type": "null"}]},
        "softwareVersions": {"type": "array", "items": {"type": "string"}},
        "conditionText": {"type": "string"},
        "citations": {"type": "array", "items": AD_PAGE_CITATION_SCHEMA},
    },
}
AD_APPLICABILITY_GROUP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "groupKey", "productType", "productSubtype", "manufacturer", "modelApplicability",
        "serialNumberApplicability", "equipmentCombinationLogic", "equipmentConditions", "conditions",
        "citations", "confidence", "uncertaintyReasons",
    ],
    "properties": {
        "groupKey": {"type": "string"},
        "productType": {
            "type": "string",
            "enum": ["aircraft", "rotorcraft", "engine", "propeller", "appliance", "equipment", "other"],
        },
        "productSubtype": {"type": ["string", "null"]},
        "manufacturer": AD_MANUFACTURER_SCHEMA,
        "modelApplicability": {
            "type": "object",
            "additionalProperties": False,
            "required": ["kind", "models", "sourceText"],
            "properties": {
                "kind": {"type": "string", "enum": ["listed", "all", "expression", "unknown"]},
                "models": {"type": "array", "items": AD_MODEL_SCHEMA},
                "sourceText": {"type": ["string", "null"]},
            },
        },
        "serialNumberApplicability": AD_SERIAL_APPLICABILITY_SCHEMA,
        "equipmentCombinationLogic": {"type": "string", "enum": ["all", "any"]},
        "equipmentConditions": {"type": "array", "items": AD_EQUIPMENT_CONDITION_SCHEMA},
        "conditions": {"type": "array", "items": {"type": "string"}},
        "citations": {"type": "array", "items": AD_PAGE_CITATION_SCHEMA},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "uncertaintyReasons": {"type": "array", "items": {"type": "string"}},
    },
}
AD_AMOC_PROVISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "provisionKey", "authorityText", "approvingAuthority", "submissionInstructions",
        "conditions", "citations", "confidence", "uncertaintyReasons",
    ],
    "properties": {
        "provisionKey": {"type": "string"},
        "authorityText": {"type": "string"},
        "approvingAuthority": {"type": ["string", "null"]},
        "submissionInstructions": {"type": ["string", "null"]},
        "conditions": {"type": "array", "items": {"type": "string"}},
        "citations": {"type": "array", "items": AD_PAGE_CITATION_SCHEMA},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "uncertaintyReasons": {"type": "array", "items": {"type": "string"}},
    },
}
AD_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "adNumber",
        "title",
        "effectiveDate",
        "publicationDate",
        "applicabilityGroups",
        "affectedProducts",
        "complianceActions",
        "complianceIntervals",
        "supersedesAdNumbers",
        "sourceUrls",
        "confidence",
        "citations",
        "uncertaintyReasons",
        "requirements",
        "amocProvisions",
    ],
    "properties": {
        "adNumber": {"type": ["string", "null"]},
        "title": {"type": ["string", "null"]},
        "effectiveDate": {"type": ["string", "null"]},
        "publicationDate": {"type": ["string", "null"]},
        "applicabilityGroups": {"type": "array", "items": AD_APPLICABILITY_GROUP_SCHEMA},
        # Legacy compatibility summary. Applicability groups remain authoritative.
        "affectedProducts": {"type": "array", "items": {"type": "string"}},
        "complianceActions": {"type": "array", "items": {"type": "string"}},
        "complianceIntervals": {"type": "array", "items": {"type": "string"}},
        "supersedesAdNumbers": {"type": "array", "items": {"type": "string"}},
        "sourceUrls": {
            "type": "object",
            "additionalProperties": False,
            "required": ["html", "pdf", "publicInspectionPdf"],
            "properties": {
                "html": {"type": ["string", "null"]},
                "pdf": {"type": ["string", "null"]},
                "publicInspectionPdf": {"type": ["string", "null"]},
            },
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field", "source", "text"],
                "properties": {
                    "field": {"type": "string"},
                    "source": {"type": "string"},
                    "text": {"type": "string"},
                },
            },
        },
        "uncertaintyReasons": {"type": "array", "items": {"type": "string"}},
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "requirementKey", "applicabilityGroupKeys", "requirementType", "actionText", "initialThresholds",
                    "recurringTriggers", "combinationLogic", "conditions", "terminatingAction",
                    "citations", "confidence", "uncertaintyReasons"
                ],
                "properties": {
                    "requirementKey": {"type": "string"},
                    "applicabilityGroupKeys": {"type": "array", "items": {"type": "string"}},
                    "requirementType": {"type": "string", "enum": ["one_time", "recurring", "alternative", "conditional", "installation_prohibition"]},
                    "actionText": {"type": "string"},
                    "initialThresholds": {"type": "array", "items": AD_THRESHOLD_SCHEMA},
                    "recurringTriggers": {"type": "array", "items": AD_THRESHOLD_SCHEMA},
                    "combinationLogic": {"type": "string", "enum": ["all", "whichever_first", "whichever_later", "alternative"]},
                    "conditions": {"type": "array", "items": {"type": "string"}},
                    "terminatingAction": {"type": ["string", "null"]},
                    "citations": {
                        "type": "array",
                        "items": {
                            **AD_PAGE_CITATION_SCHEMA,
                        }
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "uncertaintyReasons": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "amocProvisions": {"type": "array", "items": AD_AMOC_PROVISION_SCHEMA},
    },
}


def validate_extraction_json_schema(output: Any) -> None:
    """Validate an extraction against the exact provider/reviewer v3 contract.

    This intentionally implements the small JSON-Schema subset used by
    ``AD_EXTRACTION_JSON_SCHEMA`` so approval does not depend on an optional
    runtime package. It rejects unknown properties and non-finite JSON numbers.
    """

    def fail(path: str, message: str) -> None:
        raise ValueError(f"AD extraction schema error at {path}: {message}")

    def matches_type(value: Any, expected: str) -> bool:
        if expected == "null":
            return value is None
        if expected == "object":
            return isinstance(value, dict)
        if expected == "array":
            return isinstance(value, list)
        if expected == "string":
            return isinstance(value, str)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(float(value))
            )
        return False

    def validate(value: Any, schema: dict[str, Any], path: str) -> None:
        alternatives = schema.get("anyOf")
        if alternatives:
            for alternative in alternatives:
                try:
                    validate(value, alternative, path)
                except ValueError:
                    continue
                return
            fail(path, "does not match any permitted shape")

        expected = schema.get("type")
        expected_types = expected if isinstance(expected, list) else [expected]
        if expected and not any(matches_type(value, item) for item in expected_types):
            fail(path, f"must be {' or '.join(expected_types)}")
        if value is None:
            return
        if "enum" in schema and value not in schema["enum"]:
            fail(path, f"must be one of {schema['enum']}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                fail(path, f"must be at least {schema['minimum']}")
            if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
                fail(path, f"must be greater than {schema['exclusiveMinimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                fail(path, f"must be at most {schema['maximum']}")
        if isinstance(value, dict):
            required = set(schema.get("required") or [])
            missing = required.difference(value)
            if missing:
                fail(path, f"is missing required properties: {', '.join(sorted(missing))}")
            properties = schema.get("properties") or {}
            if schema.get("additionalProperties") is False:
                extras = set(value).difference(properties)
                if extras:
                    fail(path, f"contains unsupported properties: {', '.join(sorted(extras))}")
            for key, child in value.items():
                if key in properties:
                    validate(child, properties[key], f"{path}.{key}")
        if isinstance(value, list) and "items" in schema:
            for index, child in enumerate(value):
                validate(child, schema["items"], f"{path}[{index}]")

    validate(output, AD_EXTRACTION_JSON_SCHEMA, "$")


class ADExtractionProvider(Protocol):
    provider_name: str
    provider_version: str

    def extract(self, directive: AirworthinessDirective) -> dict[str, Any]:
        ...


def process_pending_ad_extractions(
    db: Session,
    limit: int = 20,
    llm_provider: ADExtractionProvider | None = None,
) -> dict[str, int]:
    directives = db.scalars(
        select(AirworthinessDirective)
        .where(AirworthinessDirective.extraction_status.in_(["not_started", "needs_review"]))
        .options(
            selectinload(AirworthinessDirective.discovery_record),
            selectinload(AirworthinessDirective.extractions),
            selectinload(AirworthinessDirective.publications).selectinload(ADPublication.source_document),
        )
        .limit(limit)
    ).all()
    stats = {"seen": 0, "extracted": 0, "review_queued": 0, "approved": 0}
    for directive in directives:
        stats["seen"] += 1
        extraction = extract_directive(db, directive, llm_provider=llm_provider)
        stats["extracted"] += 1
        if extraction.status == "needs_review":
            stats["review_queued"] += 1
        if extraction.status == "approved":
            stats["approved"] += 1
    record_product_event(
        db,
        event_type="ad_extraction_worker_completed",
        subject_type="ad_extraction",
        subject_id="batch",
        event_source="worker",
        properties=stats,
    )
    record_workflow_status(
        db,
        workflow_type="ad_extraction",
        workflow_id="batch",
        new_status="complete",
        reason=f"extracted={stats['extracted']} review_queued={stats['review_queued']}",
        actor_type="worker",
    )
    db.commit()
    return stats


def extract_directive(
    db: Session,
    directive: AirworthinessDirective,
    llm_provider: ADExtractionProvider | None = None,
) -> ADExtraction:
    if llm_provider is None:
        llm_provider = configured_llm_provider()
    if llm_provider is not None:
        provider_extraction = extract_with_llm_provider(db, directive, llm_provider)
        if provider_extraction is not None:
            return provider_extraction

    return extract_with_deterministic_provider(db, directive, fallback_reason=None)


def extract_with_deterministic_provider(
    db: Session,
    directive: AirworthinessDirective,
    fallback_reason: str | None,
) -> ADExtraction:
    existing = db.scalar(
        select(ADExtraction).where(
            ADExtraction.directive_id == directive.id,
            ADExtraction.input_content_hash == extraction_input_hash(directive),
            ADExtraction.provider_name == PROVIDER_NAME,
            ADExtraction.provider_version == PROVIDER_VERSION,
            ADExtraction.schema_version == SCHEMA_VERSION,
        )
    )
    if existing:
        ensure_persisted_source_pages(directive, existing)
        if fallback_reason and existing.raw_response:
            existing.raw_response = {**existing.raw_response, "latestFallbackReason": fallback_reason}
        ensure_review_for_extraction(db, directive, existing)
        return existing

    output, confidence, citations = build_extraction_output(directive)
    if not output.get("affectedProducts"):
        output["affectedProducts"] = affected_products_from_applicability(
            db,
            directive.id,
        )
    validate_extraction_output(output)
    # The deterministic provider can classify metadata, but it cannot approve
    # regulatory meaning from a retained full-text publication.
    status = (
        "approved"
        if confidence >= REVIEW_THRESHOLD and not retained_pdf_documents(directive)
        else "needs_review"
    )
    source_pages = full_text_pages_for_directive(directive)
    extraction = ADExtraction(
        directive_id=directive.id,
        provider_name=PROVIDER_NAME,
        provider_version=PROVIDER_VERSION,
        schema_version=SCHEMA_VERSION,
        input_content_hash=extraction_input_hash(directive),
        status=status,
        confidence=confidence,
        output=output,
        citations=citations,
        raw_response={
            "mode": "deterministic",
            "amocEnvelopeOrigin": "deterministic_provider",
            "schemaVersion": SCHEMA_VERSION,
            "fallbackReason": fallback_reason,
            "retainedSourcePagesCached": True,
            "retainedSourcePages": source_pages,
            "sourcePageParser": "pypdf-native-text-v1",
        },
    )
    db.add(extraction)
    db.flush()
    ensure_review_for_extraction(db, directive, extraction)
    return extraction


def extract_with_llm_provider(
    db: Session,
    directive: AirworthinessDirective,
    provider: ADExtractionProvider,
) -> ADExtraction | None:
    existing = db.scalar(
        select(ADExtraction).where(
            ADExtraction.directive_id == directive.id,
            ADExtraction.input_content_hash == extraction_input_hash(directive),
            ADExtraction.provider_name == provider.provider_name,
            ADExtraction.provider_version == provider.provider_version,
            ADExtraction.schema_version == SCHEMA_VERSION,
        )
    )
    if existing:
        ensure_persisted_source_pages(directive, existing)
        ensure_review_for_extraction(db, directive, existing)
        return existing

    deterministic_output, _, _ = build_extraction_output(directive)
    try:
        provider_payload = provider.extract(directive)
        output, confidence, citations, raw_provider = normalize_provider_payload(provider_payload)
        validate_extraction_output(output)
    except Exception as exc:
        return extract_with_deterministic_provider(db, directive, fallback_reason=f"{type(exc).__name__}: {exc}")

    review_reasons = review_reasons_for_provider_output(output, confidence, raw_provider, deterministic_output)
    source_pages = full_text_pages_for_directive(directive)
    if retained_pdf_documents(directive) and not source_pages:
        review_reasons.append("retained_pdf_text_unavailable")
    if source_pages and not output.get("requirements"):
        review_reasons.append("missing_full_text_requirements")
    try:
        validate_requirement_evidence(output, source_pages)
    except ValueError:
        review_reasons.append("invalid_requirement_evidence")
    # Full-text regulatory meaning is never machine-published. Even a complete,
    # high-confidence provider result must pass the authenticated admin review.
    review_reasons.append("human_full_text_review_required")
    review_reasons = sorted(set(review_reasons))
    status = "needs_review"
    extraction = ADExtraction(
        directive_id=directive.id,
        provider_name=provider.provider_name,
        provider_version=provider.provider_version,
        schema_version=SCHEMA_VERSION,
        input_content_hash=extraction_input_hash(directive),
        status=status,
        confidence=confidence,
        output=output,
        citations=citations,
        raw_response={
            **raw_provider,
            "mode": "llm",
            "amocEnvelopeOrigin": "llm_provider",
            "schemaVersion": SCHEMA_VERSION,
            "reviewReasons": review_reasons,
            "retainedSourcePagesCached": True,
            "retainedSourcePages": source_pages,
            "sourcePageParser": "pypdf-native-text-v1",
        },
    )
    db.add(extraction)
    db.flush()
    ensure_review_for_extraction(db, directive, extraction)
    return extraction


class OpenAIResponsesADExtractionProvider:
    provider_name = OPENAI_PROVIDER_NAME

    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.prompt_hash = prompt_hash()
        self.provider_version = f"{model}:{OPENAI_PROMPT_VERSION}:{self.prompt_hash}"

    def extract(self, directive: AirworthinessDirective) -> dict[str, Any]:
        request_body = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": AD_EXTRACTION_SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": source_text_for_directive(directive)}],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "paprnav_ad_extraction",
                    "schema": AD_EXTRACTION_JSON_SCHEMA,
                    "strict": True,
                }
            },
        }
        response = httpx.post(
            f"{self.base_url}/responses",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=request_body,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        response_payload = response.json()
        parsed_text = response_payload.get("output_text") or response_output_text(response_payload)
        provider_output = json.loads(parsed_text)
        return {
            "output": provider_output,
            "raw_response": {
                "providerResponseId": response_payload.get("id"),
                "providerModel": response_payload.get("model"),
                "usage": response_payload.get("usage"),
                "promptHash": self.prompt_hash,
                "promptVersion": OPENAI_PROMPT_VERSION,
                "request": {
                    "model": self.model,
                    "textFormat": "json_schema",
                    "strict": True,
                },
            },
        }


def configured_llm_provider() -> ADExtractionProvider | None:
    settings = get_settings()
    if settings.ad_extraction_provider != "openai" or not settings.openai_api_key:
        return None
    return OpenAIResponsesADExtractionProvider(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_ad_extraction_model,
        timeout_seconds=settings.ad_extraction_timeout_seconds,
    )


def normalize_provider_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], float, list[dict[str, str]], dict[str, Any]]:
    raw_provider = dict(payload.get("raw_response") or {})
    provider_output = dict(payload.get("output") or payload)
    confidence = provider_output.pop("confidence", None)
    if not isinstance(confidence, (int, float)):
        raise ValueError("AD provider output confidence must be numeric")
    citations = provider_output.pop("citations", [])
    if not isinstance(citations, list):
        raise ValueError("AD provider output citations must be a list")
    uncertainty_reasons = provider_output.pop("uncertaintyReasons", [])
    if not isinstance(uncertainty_reasons, list):
        raise ValueError("AD provider output uncertaintyReasons must be a list")
    raw_provider["uncertaintyReasons"] = uncertainty_reasons
    return derive_compliance_action_summaries(provider_output), float(confidence), citations, raw_provider


def derive_compliance_action_summaries(output: dict[str, Any]) -> dict[str, Any]:
    """Synchronize compatibility summaries with authoritative v3 structures."""
    normalized = dict(output)
    requirements = normalized.get("requirements")
    if isinstance(requirements, list):
        actions: list[str] = []
        for requirement in requirements:
            if not isinstance(requirement, dict):
                continue
            action = str(requirement.get("actionText") or "").strip()
            if action and action not in actions:
                actions.append(action)
        if actions:
            normalized["complianceActions"] = actions
    groups = normalized.get("applicabilityGroups")
    if isinstance(groups, list):
        normalized["affectedProducts"] = affected_product_labels(groups)
    return normalized


def affected_product_labels(groups: list[Any]) -> list[str]:
    """Derive human-readable legacy labels without parsing them back into data."""
    labels: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        manufacturer = group.get("manufacturer") or {}
        make = clean_schema_text(
            manufacturer.get("normalizedName") or manufacturer.get("sourceName")
        ) if isinstance(manufacturer, dict) else None
        model_scope = group.get("modelApplicability") or {}
        models = model_scope.get("models") or [] if isinstance(model_scope, dict) else []
        if models:
            for model in models:
                if not isinstance(model, dict):
                    continue
                designation = clean_schema_text(
                    model.get("normalizedDesignation") or model.get("sourceDesignation")
                )
                label = " ".join(value for value in (make, designation) if value)
                if label and label not in labels:
                    labels.append(label)
        elif make and make not in labels:
            labels.append(make)
    return labels


def review_reasons_for_provider_output(
    output: dict[str, Any],
    confidence: float,
    raw_provider: dict[str, Any],
    deterministic_output: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if confidence < LLM_REVIEW_THRESHOLD:
        reasons.append("low_confidence")
    if not output.get("applicabilityGroups"):
        reasons.append("missing_applicability_groups")
    if not output.get("complianceActions"):
        reasons.append("missing_compliance_actions")
    if raw_provider.get("uncertaintyReasons"):
        reasons.append("provider_uncertainty")
    if normalize_scalar(output.get("adNumber")) != normalize_scalar(deterministic_output.get("adNumber")):
        reasons.append("ad_number_disagreement")
    if normalize_list(output.get("supersedesAdNumbers")) != normalize_list(deterministic_output.get("supersedesAdNumbers")):
        reasons.append("supersession_disagreement")
    return sorted(set(reasons))


def ensure_review_for_extraction(db: Session, directive: AirworthinessDirective, extraction: ADExtraction) -> None:
    if extraction.status == "approved":
        decided_review = db.scalar(
            select(ADExtractionReview).where(
                ADExtractionReview.extraction_id == extraction.id,
                ADExtractionReview.status.in_({"approved", "edited"}),
            )
        )
        if extraction.schema_version == SCHEMA_VERSION and decided_review is None:
            # Existing/provider-created v3 rows are not allowed to materialize
            # without an authenticated human decision.
            extraction.status = "needs_review"
        elif (
            extraction.schema_version == SCHEMA_VERSION
            and decided_review is not None
            and structured_output_hash(extraction.output)
            != structured_output_hash(decided_review.decision_output)
        ):
            raw_response = dict(extraction.raw_response or {})
            mismatch_history = list(raw_response.get("reviewIntegrityMismatches") or [])
            mismatch_history.append({
                "detectedAt": datetime.now(timezone.utc).isoformat(),
                "reviewId": decided_review.id,
                "reviewedOutputHash": structured_output_hash(decided_review.decision_output),
                "extractionOutputHash": structured_output_hash(extraction.output),
            })
            raw_response["reviewIntegrityMismatches"] = mismatch_history
            extraction.raw_response = raw_response
            extraction.status = "needs_review"
            decided_review.status = "pending"
            decided_review.proposed_output = extraction.output
            decided_review.decision = None
            decided_review.decision_output = None
            decided_review.reviewer_user_id = None
            decided_review.reviewed_at = None
        else:
            directive.extraction_status = "complete"
            directive.review_status = "approved"
            directive.approved_at = directive.approved_at or datetime.now(timezone.utc)
            populate_applicability_from_extraction(db, extraction)
            from app.services.ad_recurrence import materialize_requirements_from_extraction

            materialize_requirements_from_extraction(db, extraction)
            return

    directive.extraction_status = "needs_review"
    directive.review_status = "pending"
    existing_review = db.scalar(select(ADExtractionReview).where(ADExtractionReview.extraction_id == extraction.id))
    if existing_review:
        return
    db.add(
        ADExtractionReview(
            extraction_id=extraction.id,
            status="pending",
            proposed_output=extraction.output,
        )
    )
    db.flush()


def structured_output_hash(output: dict[str, Any] | None) -> str:
    normalized = json.dumps(
        output or {},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_extraction_output(directive: AirworthinessDirective) -> tuple[dict[str, Any], float, list[dict[str, str]]]:
    record = directive.discovery_record
    source_text = "\n".join(filter(None, [record.title, record.abstract, record.excerpts])) if record else directive.title
    title = record.title if record else directive.title
    title_subject = subject_from_title(title)
    ad_number = directive.ad_number or extract_ad_number(source_text)
    superseded_numbers = sorted({match for match in AD_NUMBER_PATTERN.findall(source_text) if match != ad_number})
    confidence = 0.72
    if ad_number:
        confidence += 0.08
    if title_subject:
        confidence += 0.04
    if "supersed" in source_text.lower():
        confidence += 0.03
    confidence = min(confidence, 0.93)

    output = {
        "adNumber": ad_number,
        "title": title,
        "effectiveDate": record.effective_date.isoformat() if record and record.effective_date else None,
        "publicationDate": record.publication_date.isoformat() if record and record.publication_date else None,
        "applicabilityGroups": [],
        "affectedProducts": [title_subject] if title_subject else [],
        "complianceActions": [],
        "complianceIntervals": [],
        "supersedesAdNumbers": superseded_numbers,
        "requirements": [],
        "amocProvisions": [],
        "sourceUrls": {
            "html": record.html_url if record else None,
            "pdf": record.pdf_url if record else None,
            "publicInspectionPdf": record.public_inspection_pdf_url if record else None,
        },
    }
    if "airworthiness directive" in source_text.lower():
        output["complianceActions"].append("Review source document for required corrective actions.")

    citations = [
        {
            "field": "title",
            "source": "federal_register" if record else "directive",
            "text": title,
        }
    ]
    return output, confidence, citations


def validate_extraction_output(
    output: dict[str, Any],
    *,
    require_v2_requirements: bool = True,
    require_nonempty_requirements: bool = False,
    require_nonempty_applicability: bool = False,
) -> None:
    required_keys = {
        "adNumber",
        "title",
        "effectiveDate",
        "publicationDate",
        "applicabilityGroups",
        "complianceActions",
        "complianceIntervals",
        "supersedesAdNumbers",
        "sourceUrls",
        "amocProvisions",
    }
    if require_v2_requirements:
        required_keys.add("requirements")
    missing = required_keys.difference(output)
    if missing:
        raise ValueError(f"AD extraction output is missing required keys: {', '.join(sorted(missing))}")
    for list_key in ["applicabilityGroups", "complianceActions", "complianceIntervals", "supersedesAdNumbers", "amocProvisions"]:
        if not isinstance(output[list_key], list):
            raise ValueError(f"AD extraction field {list_key} must be a list")
    validate_applicability_groups(
        output["applicabilityGroups"],
        require_nonempty=require_nonempty_applicability,
    )
    if not isinstance(output["sourceUrls"], dict):
        raise ValueError("AD extraction field sourceUrls must be an object")
    if "requirements" not in output:
        return
    if not isinstance(output["requirements"], list):
        raise ValueError("AD extraction field requirements must be a list")
    if require_nonempty_requirements and not output["requirements"]:
        raise ValueError("AD extraction v3 must include at least one compliance requirement")
    group_keys = {
        clean_schema_text(group.get("groupKey"))
        for group in output["applicabilityGroups"]
        if isinstance(group, dict)
    }
    for index, requirement in enumerate(output["requirements"]):
        validate_requirement(requirement, index, group_keys=group_keys)
    for index, provision in enumerate(output["amocProvisions"]):
        validate_amoc_provision(provision, index)


def validate_applicability_groups(groups: Any, *, require_nonempty: bool) -> None:
    if not isinstance(groups, list):
        raise ValueError("AD extraction field applicabilityGroups must be a list")
    if require_nonempty and not groups:
        raise ValueError("AD extraction v3 must include at least one applicability group")
    seen_keys: set[str] = set()
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"AD applicability group {index} must be an object")
        required = {
            "groupKey", "productType", "productSubtype", "manufacturer", "modelApplicability",
            "serialNumberApplicability", "equipmentCombinationLogic", "equipmentConditions", "conditions",
            "citations", "confidence", "uncertaintyReasons",
        }
        missing = required.difference(group)
        if missing:
            raise ValueError(f"AD applicability group {index} is missing: {', '.join(sorted(missing))}")
        group_key = clean_schema_text(group.get("groupKey"))
        if not group_key:
            raise ValueError(f"AD applicability group {index} must include groupKey")
        if group_key in seen_keys:
            raise ValueError(f"AD applicability group key {group_key} is duplicated")
        seen_keys.add(group_key)
        if group.get("productType") not in {
            "aircraft", "rotorcraft", "engine", "propeller", "appliance", "equipment", "other",
        }:
            raise ValueError(f"AD applicability group {index} has an unsupported productType")
        manufacturer = group.get("manufacturer")
        if not isinstance(manufacturer, dict) or not clean_schema_text(manufacturer.get("sourceName")):
            raise ValueError(f"AD applicability group {index} must include manufacturer.sourceName")
        model_scope = group.get("modelApplicability")
        if not isinstance(model_scope, dict):
            raise ValueError(f"AD applicability group {index} modelApplicability must be an object")
        if model_scope.get("kind") not in {"listed", "all", "expression", "unknown"}:
            raise ValueError(f"AD applicability group {index} has unsupported model applicability")
        models = model_scope.get("models")
        if not isinstance(models, list):
            raise ValueError(f"AD applicability group {index} models must be a list")
        if model_scope.get("kind") == "listed" and not models:
            raise ValueError(f"AD applicability group {index} with listed models must include a model")
        for model_index, model in enumerate(models):
            if not isinstance(model, dict) or not clean_schema_text(model.get("sourceDesignation")):
                raise ValueError(
                    f"AD applicability group {index} model {model_index} must include sourceDesignation"
                )
            if not isinstance(model.get("aliases"), list):
                raise ValueError(f"AD applicability group {index} model {model_index} aliases must be a list")
        serial_scope = group.get("serialNumberApplicability")
        if not isinstance(serial_scope, dict) or serial_scope.get("kind") not in {
            "all", "values", "ranges", "expression", "unknown",
        }:
            raise ValueError(f"AD applicability group {index} has invalid serialNumberApplicability")
        for field in ("values", "ranges", "excludedValues"):
            if not isinstance(serial_scope.get(field), list):
                raise ValueError(f"AD applicability group {index} serial field {field} must be a list")
        for field in ("equipmentConditions", "conditions", "citations", "uncertaintyReasons"):
            if not isinstance(group.get(field), list):
                raise ValueError(f"AD applicability group {index} field {field} must be a list")
        validate_page_citations(group.get("citations"), f"AD applicability group {index}")
        for condition_index, condition in enumerate(group.get("equipmentConditions") or []):
            if not isinstance(condition, dict):
                raise ValueError(
                    f"AD applicability group {index} equipment condition {condition_index} must be an object"
                )
            condition_manufacturer = condition.get("manufacturer")
            if not isinstance(condition_manufacturer, dict) or not clean_schema_text(condition_manufacturer.get("sourceName")):
                raise ValueError(
                    f"AD applicability group {index} equipment condition {condition_index} must include manufacturer.sourceName"
                )
            validate_page_citations(
                condition.get("citations"),
                f"AD applicability group {index} equipment condition {condition_index}",
            )


def affected_products_from_applicability(db: Session, directive_id: str) -> list[str]:
    targets = db.scalars(
        select(ApplicabilityTarget)
        .join(
            ADTargetApplicability,
            ADTargetApplicability.target_id == ApplicabilityTarget.id,
        )
        .where(
            ADTargetApplicability.directive_id == directive_id,
            ADTargetApplicability.status.in_({"current", "active", "unknown", "historical"}),
        )
        .distinct()
    ).all()
    products = []
    for target in targets:
        identity = " ".join(
            value.strip()
            for value in (target.make, target.model)
            if value and value.strip()
        )
        label = identity or target.product_subtype or target.product_type
        if label and label not in products:
            products.append(label)
    return sorted(products)


def validate_requirement(requirement: Any, index: int, *, group_keys: set[str] | None = None) -> None:
    if not isinstance(requirement, dict):
        raise ValueError(f"AD extraction requirement {index} must be an object")
    required = {
        "requirementKey", "applicabilityGroupKeys", "requirementType", "actionText", "initialThresholds",
        "recurringTriggers", "combinationLogic", "conditions", "terminatingAction",
        "citations", "confidence", "uncertaintyReasons",
    }
    missing = required.difference(requirement)
    if missing:
        raise ValueError(f"AD extraction requirement {index} is missing: {', '.join(sorted(missing))}")
    if not str(requirement["actionText"]).strip():
        raise ValueError(f"AD extraction requirement {index} must include actionText")
    if requirement["requirementType"] not in {
        "one_time", "recurring", "alternative", "conditional", "installation_prohibition"
    }:
        raise ValueError(f"AD extraction requirement {index} has an unsupported requirementType")
    if requirement["combinationLogic"] not in {"all", "whichever_first", "whichever_later", "alternative"}:
        raise ValueError(f"AD extraction requirement {index} has unsupported combinationLogic")
    for field in ("initialThresholds", "recurringTriggers", "conditions", "uncertaintyReasons"):
        if not isinstance(requirement[field], list):
            raise ValueError(f"AD extraction requirement {index} field {field} must be a list")
    for threshold in requirement["initialThresholds"] + requirement["recurringTriggers"]:
        if not isinstance(threshold, dict) or not all(
            key in threshold for key in ("metric", "value", "unit", "anchorKind", "sourceText")
        ):
            raise ValueError(f"AD extraction requirement {index} has an invalid threshold or trigger")
    applicability_group_keys = requirement.get("applicabilityGroupKeys")
    if not isinstance(applicability_group_keys, list) or not applicability_group_keys:
        raise ValueError(f"AD extraction requirement {index} must include applicabilityGroupKeys")
    referenced_keys = {
        clean_schema_text(key) for key in applicability_group_keys if clean_schema_text(key)
    }
    unknown_keys = referenced_keys.difference(group_keys or set())
    if unknown_keys:
        raise ValueError(
            f"AD extraction requirement {index} references unknown applicability group(s): {', '.join(sorted(unknown_keys))}"
        )
    validate_page_citations(requirement.get("citations"), f"AD extraction requirement {index}")


def validate_page_citations(citations: Any, label: str) -> None:
    if not isinstance(citations, list) or not citations:
        raise ValueError(f"{label} must include page citations")
    for citation in citations:
        if not isinstance(citation, dict) or not citation.get("sourceDocumentId") or not citation.get("pageNumber") or not citation.get("text"):
            raise ValueError(f"{label} has an invalid page citation")


def validate_amoc_provision(provision: Any, index: int) -> None:
    if not isinstance(provision, dict):
        raise ValueError(f"AD AMOC provision {index} must be an object")
    required = {
        "provisionKey", "authorityText", "approvingAuthority", "submissionInstructions",
        "conditions", "citations", "confidence", "uncertaintyReasons",
    }
    missing = required.difference(provision)
    if missing:
        raise ValueError(
            f"AD AMOC provision {index} is missing: {', '.join(sorted(missing))}"
        )
    if not clean_schema_text(provision.get("provisionKey")):
        raise ValueError(f"AD AMOC provision {index} must include provisionKey")
    if not clean_schema_text(provision.get("authorityText")):
        raise ValueError(f"AD AMOC provision {index} must include authorityText")
    for field in ("conditions", "uncertaintyReasons"):
        if not isinstance(provision.get(field), list):
            raise ValueError(f"AD AMOC provision {index} field {field} must be a list")
    validate_page_citations(provision.get("citations"), f"AD AMOC provision {index}")


def clean_schema_text(value: Any) -> str | None:
    text = " ".join(str(value or "").strip().split())
    return text or None


def validate_requirement_evidence(output: dict[str, Any], source_pages: list[dict[str, Any]]) -> None:
    page_index = {
        (page["sourceDocumentId"], page["pageNumber"]): normalize_regulatory_text(page["text"])
        for page in source_pages
    }
    validate_top_level_date_evidence(output, source_pages)
    for index, group in enumerate(output.get("applicabilityGroups") or []):
        group_citations = validate_citations_against_pages(
            group.get("citations") or [],
            page_index,
            f"AD applicability group {index}",
        )
        validate_applicability_evidence(group, group_citations, index)
        for condition_index, condition in enumerate(group.get("equipmentConditions") or []):
            condition_citations = validate_citations_against_pages(
                condition.get("citations") or [],
                page_index,
                f"AD applicability group {index} equipment condition {condition_index}",
            )
            validate_equipment_condition_evidence(
                condition,
                condition_citations,
                f"AD applicability group {index} equipment condition {condition_index}",
            )
    for index, requirement in enumerate(output.get("requirements") or []):
        normalized_citations: list[str] = []
        normalized_citations.extend(validate_citations_against_pages(
            requirement.get("citations") or [],
            page_index,
            f"AD extraction requirement {index}",
        ))
        action_text = normalize_regulatory_text(requirement.get("actionText"))
        combined_citations = " ".join(normalized_citations)
        if action_text and not (
            any(action_text in citation for citation in normalized_citations)
            or action_text in combined_citations
        ):
            raise ValueError(
                f"AD extraction requirement {index} actionText must preserve wording from a page citation"
            )
        timings = [
            ("initial", timing)
            for timing in requirement.get("initialThresholds") or []
        ] + [
            ("recurring", timing)
            for timing in requirement.get("recurringTriggers") or []
        ]
        for timing_index, (trigger_kind, timing) in enumerate(timings):
            validate_timing_evidence(
                timing,
                normalized_citations,
                f"AD extraction requirement {index} timing {timing_index}",
                trigger_kind=trigger_kind,
            )
        validate_requirement_semantics(
            requirement,
            combined_citations,
            f"AD extraction requirement {index}",
        )
        for condition_index, condition in enumerate(requirement.get("conditions") or []):
            require_cited_wording(
                condition,
                normalized_citations,
                f"AD extraction requirement {index} condition {condition_index}",
            )
        terminating_action = normalize_regulatory_text(requirement.get("terminatingAction"))
        if terminating_action and not (
            any(terminating_action in citation for citation in normalized_citations)
            or terminating_action in combined_citations
        ):
            raise ValueError(
                f"AD extraction requirement {index} terminatingAction must preserve wording from a page citation"
            )
    for index, provision in enumerate(output.get("amocProvisions") or []):
        normalized_citations = validate_citations_against_pages(
            provision.get("citations") or [],
            page_index,
            f"AD AMOC provision {index}",
        )
        authority_text = normalize_regulatory_text(provision.get("authorityText"))
        if not authority_text or not any(
            authority_text in citation for citation in normalized_citations
        ):
            raise ValueError(
                f"AD AMOC provision {index} authorityText must preserve wording from a page citation"
            )
        for field in ("approvingAuthority", "submissionInstructions"):
            require_cited_wording(
                provision.get(field),
                normalized_citations,
                f"AD AMOC provision {index} {field}",
                allow_empty=True,
            )
        for condition_index, condition in enumerate(provision.get("conditions") or []):
            require_cited_wording(
                condition,
                normalized_citations,
                f"AD AMOC provision {index} condition {condition_index}",
            )


def validate_applicability_evidence(
    group: dict[str, Any],
    citations: list[str],
    index: int,
) -> None:
    label = f"AD applicability group {index}"
    validate_product_type_semantics(group, citations, label)
    manufacturer = group.get("manufacturer") or {}
    require_cited_wording(
        manufacturer.get("sourceName"),
        citations,
        f"{label} manufacturer.sourceName",
    )
    require_source_identity_or_null(
        manufacturer.get("sourceName"),
        manufacturer.get("normalizedName"),
        f"{label} manufacturer.normalizedName",
    )
    model_scope = group.get("modelApplicability") or {}
    validate_model_scope_semantics(model_scope, group, label)
    require_cited_wording(
        model_scope.get("sourceText"),
        citations,
        f"{label} modelApplicability.sourceText",
    )
    for model_index, model in enumerate(model_scope.get("models") or []):
        require_cited_wording(
            model.get("sourceDesignation") if isinstance(model, dict) else None,
            citations,
            f"{label} model {model_index} sourceDesignation",
        )
        if isinstance(model, dict):
            require_source_identity_or_null(
                model.get("sourceDesignation"),
                model.get("normalizedDesignation"),
                f"{label} model {model_index} normalizedDesignation",
            )
    serial_scope = group.get("serialNumberApplicability") or {}
    validate_serial_scope_semantics(serial_scope, group, label)
    serial_source = normalize_regulatory_text(serial_scope.get("sourceText"))
    require_cited_wording(
        serial_scope.get("sourceText"),
        citations,
        f"{label} serialNumberApplicability.sourceText",
    )
    for value in serial_scope.get("values") or []:
        if normalize_regulatory_text(value) not in serial_source:
            raise ValueError(f"{label} serial value is not present in serial sourceText")
    for serial_range in serial_scope.get("ranges") or []:
        for endpoint in (serial_range.get("start"), serial_range.get("end")):
            if endpoint and normalize_regulatory_text(endpoint) not in serial_source:
                raise ValueError(f"{label} serial range endpoint is not present in serial sourceText")
    for value in serial_scope.get("excludedValues") or []:
        if normalize_regulatory_text(value) not in serial_source:
            raise ValueError(f"{label} excluded serial is not present in serial sourceText")
    for condition_index, condition in enumerate(group.get("conditions") or []):
        require_cited_wording(
            condition,
            citations,
            f"{label} condition {condition_index}",
        )


def validate_equipment_condition_evidence(
    condition: dict[str, Any],
    citations: list[str],
    label: str,
) -> None:
    manufacturer = condition.get("manufacturer") or {}
    require_cited_wording(
        manufacturer.get("sourceName"),
        citations,
        f"{label} manufacturer.sourceName",
    )
    require_source_identity_or_null(
        manufacturer.get("sourceName"),
        manufacturer.get("normalizedName"),
        f"{label} manufacturer.normalizedName",
    )
    model = condition.get("model") or {}
    if model:
        require_cited_wording(
            model.get("sourceDesignation"),
            citations,
            f"{label} model.sourceDesignation",
        )
        require_source_identity_or_null(
            model.get("sourceDesignation"),
            model.get("normalizedDesignation"),
            f"{label} model.normalizedDesignation",
        )
    require_cited_wording(
        condition.get("conditionText"),
        citations,
        f"{label} conditionText",
    )
    for version in condition.get("softwareVersions") or []:
        require_cited_wording(version, citations, f"{label} softwareVersion")


def validate_product_type_semantics(
    group: dict[str, Any],
    citations: list[str],
    label: str,
) -> None:
    product_type = normalize_regulatory_text(group.get("productType"))
    combined = " ".join(citations)
    supported_terms = {
        "aircraft": ("aircraft", "airplane"),
        "airplane": ("aircraft", "airplane"),
        "rotorcraft": ("rotorcraft", "helicopter"),
        "engine": ("engine",),
        "propeller": ("propeller",),
        "appliance": ("appliance", "equipment"),
    }
    terms = supported_terms.get(product_type)
    if terms and not any(term in combined for term in terms):
        raise ValueError(f"{label} productType is not supported by cited text")
    subtype = normalize_regulatory_text(group.get("productSubtype"))
    if subtype and subtype not in combined:
        raise ValueError(f"{label} productSubtype is not supported by cited text")


def require_cited_wording(
    value: Any,
    citations: list[str],
    label: str,
    *,
    allow_empty: bool = False,
) -> None:
    normalized = normalize_regulatory_text(value)
    if not normalized:
        if allow_empty:
            return
        raise ValueError(f"{label} must preserve wording from a page citation")
    combined = " ".join(citations)
    if normalized not in combined:
        raise ValueError(f"{label} must preserve wording from a page citation")


def require_source_identity_or_null(
    source_value: Any,
    normalized_value: Any,
    label: str,
) -> None:
    """Do not let an unreviewed canonicalization replace source identity."""

    normalized = normalize_regulatory_text(normalized_value)
    if not normalized:
        return
    source = normalize_regulatory_text(source_value)
    if normalized != source:
        raise ValueError(
            f"{label} must be null or equal the cited source identity until a reviewed canonical identity mapping exists"
        )


def validate_timing_evidence(
    timing: dict[str, Any],
    normalized_citations: list[str],
    label: str,
    *,
    trigger_kind: str,
) -> None:
    source_text = normalize_regulatory_text(timing.get("sourceText"))
    combined_citations = " ".join(normalized_citations)
    if not source_text or source_text not in combined_citations:
        raise ValueError(f"{label} sourceText must preserve wording from a page citation")
    try:
        decimal_value = Decimal(str(timing.get("value")))
        value_text = format(decimal_value.normalize(), "f")
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{label} value must be numeric") from None
    if value_text and value_text not in source_text.split():
        raise ValueError(f"{label} value is not present in its sourceText")
    unit = str(timing.get("unit") or "").lower()
    unit_stems = {
        "days": ("day",),
        "months": ("month", "year"),
        "hours": ("hour",),
        "cycles": ("cycle",),
    }
    if unit in unit_stems and not any(stem in source_text for stem in unit_stems[unit]):
        raise ValueError(f"{label} unit is not present in its sourceText")
    anchor_kind = str(timing.get("anchorKind") or "")
    anchor_terms = {
        "effective_date": ("effective date",),
        "installation": ("install",),
        "manufacture": ("manufactur",),
        "last_compliance": (
            "last compliance",
            "last inspection",
            "time since last",
            "thereafter",
            "repetitively",
            "interval",
            "every",
        ),
    }
    if anchor_kind == "unknown":
        raise ValueError(f"{label} anchorKind unknown requires adjudication")
    if anchor_kind not in anchor_terms:
        raise ValueError(f"{label} has unsupported anchorKind")
    if not any(term in source_text for term in anchor_terms[anchor_kind]):
        raise ValueError(f"{label} anchorKind is not supported by its sourceText")
    if trigger_kind == "initial" and anchor_kind == "last_compliance" and not any(
        term in source_text for term in ("last compliance", "last inspection")
    ):
        raise ValueError(f"{label} initial last_compliance anchor is not explicit")


def validate_model_scope_semantics(
    model_scope: dict[str, Any],
    group: dict[str, Any],
    label: str,
) -> None:
    kind = str(model_scope.get("kind") or "")
    models = model_scope.get("models") or []
    source_text = normalize_regulatory_text(model_scope.get("sourceText"))
    uncertainty = group.get("uncertaintyReasons") or []
    if kind == "listed" and not models:
        raise ValueError(f"{label} listed model scope must include cited models")
    if kind == "all":
        if models:
            raise ValueError(f"{label} all-model scope cannot also list selected models")
        if "all" not in source_text or not any(
            term in source_text
            for term in ("model", "airplane", "aircraft", "engine", "propeller")
        ):
            raise ValueError(f"{label} all-model scope is not explicit in sourceText")
    if kind in {"expression", "unknown"} and not uncertainty:
        raise ValueError(f"{label} unresolved model scope requires uncertaintyReasons")


def validate_serial_scope_semantics(
    serial_scope: dict[str, Any],
    group: dict[str, Any],
    label: str,
) -> None:
    kind = str(serial_scope.get("kind") or "")
    values = serial_scope.get("values") or []
    ranges = serial_scope.get("ranges") or []
    source_text = normalize_regulatory_text(serial_scope.get("sourceText"))
    uncertainty = group.get("uncertaintyReasons") or []
    if kind == "all":
        if values or ranges:
            raise ValueError(f"{label} all-serial scope cannot also list selected serials")
        if "all" not in source_text or not any(
            term in source_text for term in ("serial", "s n")
        ):
            raise ValueError(f"{label} all-serial scope is not explicit in sourceText")
    elif kind == "values" and not values:
        raise ValueError(f"{label} values serial scope must include cited values")
    elif kind == "ranges" and not ranges:
        raise ValueError(f"{label} ranges serial scope must include cited ranges")
    elif kind in {"expression", "unknown"} and not uncertainty:
        raise ValueError(f"{label} unresolved serial scope requires uncertaintyReasons")


def validate_requirement_semantics(
    requirement: dict[str, Any],
    cited_text: str,
    label: str,
) -> None:
    requirement_type = str(requirement.get("requirementType") or "")
    recurring = requirement.get("recurringTriggers") or []
    conditions = requirement.get("conditions") or []
    action_text = normalize_regulatory_text(requirement.get("actionText"))
    if requirement_type == "recurring" and not recurring:
        raise ValueError(f"{label} recurring type requires a recurring trigger")
    if requirement_type == "one_time" and recurring:
        raise ValueError(f"{label} one_time type cannot contain recurring triggers")
    if requirement_type == "installation_prohibition" and not any(
        phrase in action_text for phrase in ("do not install", "must not install", "may not install")
    ):
        raise ValueError(f"{label} installation_prohibition is not explicit in actionText")
    if requirement_type == "conditional" and not conditions:
        raise ValueError(f"{label} conditional type requires cited conditions")

    logic = str(requirement.get("combinationLogic") or "")
    if logic == "whichever_first" and "whichever occurs first" not in cited_text:
        raise ValueError(f"{label} whichever_first logic is not explicit in cited text")
    if logic == "whichever_later" and "whichever occurs later" not in cited_text:
        raise ValueError(f"{label} whichever_later logic is not explicit in cited text")
    if logic == "alternative" and " or " not in f" {cited_text} ":
        raise ValueError(f"{label} alternative logic is not explicit in cited text")


def validate_top_level_date_evidence(
    output: dict[str, Any],
    source_pages: list[dict[str, Any]],
) -> None:
    """Bind reviewed date fields to the retained official text.

    Effective date drives calendar due-state anchors. Publication date is also
    retained here so both reviewed dates share one provenance rule.
    """

    source_text = normalize_regulatory_text(
        " ".join(str(page.get("text") or "") for page in source_pages)
    )
    for field in ("effectiveDate",):
        raw_value = output.get(field)
        if raw_value in (None, ""):
            continue
        try:
            parsed = date.fromisoformat(str(raw_value))
        except ValueError:
            raise ValueError(f"AD extraction {field} must be an ISO date") from None
        month_name = parsed.strftime("%B")
        variants = {
            str(raw_value),
            f"{month_name} {parsed.day}, {parsed.year}",
            f"{month_name} {parsed.day} {parsed.year}",
            f"{parsed.month}/{parsed.day}/{parsed.year}",
        }
        if not any(normalize_regulatory_text(value) in source_text for value in variants):
            raise ValueError(
                f"AD extraction {field} must be present in retained official source text"
            )


def validate_citations_against_pages(
    citations: list[dict[str, Any]],
    page_index: dict[tuple[Any, Any], str],
    label: str,
) -> list[str]:
    normalized_citations: list[str] = []
    for citation in citations:
        page_text = page_index.get((citation.get("sourceDocumentId"), citation.get("pageNumber")))
        cited_text = normalize_regulatory_text(citation.get("text"))
        if page_text is None:
            raise ValueError(f"{label} cites a page outside retained evidence")
        if not cited_text or cited_text not in page_text:
            raise ValueError(f"{label} citation text is not present on the retained page")
        normalized_citations.append(cited_text)
    return normalized_citations


def subject_from_title(title: str | None) -> str | None:
    if not title:
        return None
    if ";" in title:
        return title.split(";", 1)[1].strip() or None
    return None


def source_text_for_directive(directive: AirworthinessDirective) -> str:
    pages = full_text_pages_for_directive(directive)
    if pages:
        return "\n\n".join(
            f"[Source document {page['sourceDocumentId']}, page {page['pageNumber']}]\n{page['text']}"
            for page in pages
        )
    documents = retained_pdf_documents(directive)
    if documents:
        return "\n".join(
            f"[Retained PDF {document.id} could not produce reliable native text; extraction requires adjudication.]"
            for document in documents
        )
    record = directive.discovery_record
    if record:
        fields = [
            f"Title: {record.title}",
            f"Abstract: {record.abstract}",
            f"Excerpts: {record.excerpts}",
            f"Federal Register document number: {record.federal_register_document_number}",
            f"Publication date: {record.publication_date.isoformat() if record.publication_date else None}",
            f"Effective date: {record.effective_date.isoformat() if record.effective_date else None}",
            f"HTML URL: {record.html_url}",
            f"PDF URL: {record.pdf_url}",
            f"Public inspection PDF URL: {record.public_inspection_pdf_url}",
        ]
        return "\n".join(field for field in fields if not field.endswith(": None"))
    return directive.title


def full_text_pages_for_directive(directive: AirworthinessDirective) -> list[dict[str, Any]]:
    """Read retained primary PDFs and preserve page boundaries for extraction/review."""
    for extraction in reversed(getattr(directive, "extractions", []) or []):
        cached, pages = persisted_source_pages(directive, extraction)
        if cached:
            return pages
    return extract_full_text_pages(directive)


def full_text_pages_for_extraction(extraction: ADExtraction) -> list[dict[str, Any]]:
    cached, pages = persisted_source_pages(extraction.directive, extraction)
    if cached:
        return pages
    return extract_full_text_pages(extraction.directive)


def ensure_persisted_source_pages(
    directive: AirworthinessDirective,
    extraction: ADExtraction,
) -> list[dict[str, Any]]:
    cached, pages = persisted_source_pages(directive, extraction)
    if cached:
        return pages
    pages = extract_full_text_pages(directive)
    extraction.raw_response = {
        **(extraction.raw_response or {}),
        "retainedSourcePagesCached": True,
        "retainedSourcePages": pages,
        "sourcePageParser": "pypdf-native-text-v1",
    }
    return pages


def persisted_source_pages(
    directive: AirworthinessDirective,
    extraction: ADExtraction,
) -> tuple[bool, list[dict[str, Any]]]:
    raw_response = extraction.raw_response or {}
    if not raw_response.get("retainedSourcePagesCached"):
        return False, []
    pages = raw_response.get("retainedSourcePages")
    if not isinstance(pages, list):
        return False, []
    documents = {document.id: document for document in retained_pdf_documents(directive)}
    document_hashes = {document_id: document.content_hash for document_id, document in documents.items()}
    derived_text: dict[tuple[str, int], str] = {}
    try:
        for document in documents.values():
            payload = verified_retained_document_bytes(document)
            reader = PdfReader(io.BytesIO(payload))
            document_pages = []
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:
                    document_pages.append({
                        "sourceDocumentId": document.id,
                        "pageNumber": page_number,
                        "text": text,
                    })
            if getattr(document, "source_type", None) == "issue_pdf":
                document_pages = bounded_issue_pages(
                    document_pages,
                    ad_number=getattr(directive, "ad_number", None),
                    title=getattr(directive, "title", None),
                )
            derived_text.update({
                (page["sourceDocumentId"], page["pageNumber"]): page["text"]
                for page in document_pages
            })
    except Exception:
        return False, []
    validated: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            return False, []
        document_id = page.get("sourceDocumentId")
        if document_id not in document_hashes or page.get("contentHash") != document_hashes[document_id]:
            return False, []
        if not isinstance(page.get("pageNumber"), int) or not isinstance(page.get("text"), str):
            return False, []
        if page["text"] != derived_text.get((document_id, page["pageNumber"])):
            return False, []
        validated.append(page)
    if documents and {
        (page["sourceDocumentId"], page["pageNumber"])
        for page in validated
    } != set(derived_text):
        return False, []
    return True, validated


def extract_full_text_pages(directive: AirworthinessDirective) -> list[dict[str, Any]]:
    """Perform the expensive retained-PDF read used during preparation only."""
    settings = get_settings()
    pages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for document in retained_pdf_documents(directive):
        if document.id in seen:
            continue
        seen.add(document.id)
        try:
            payload = verified_retained_document_bytes(document, settings=settings)
            actual_hash = hashlib.sha256(payload).hexdigest()
            reader = PdfReader(io.BytesIO(payload))
            document_pages: list[dict[str, Any]] = []
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:
                    document_pages.append({
                        "sourceDocumentId": document.id,
                        "contentHash": actual_hash,
                        "pageNumber": page_number,
                        "text": text,
                    })
            if getattr(document, "source_type", None) == "issue_pdf":
                document_pages = bounded_issue_pages(
                    document_pages,
                    ad_number=getattr(directive, "ad_number", None),
                    title=getattr(directive, "title", None),
                )
            pages.extend(document_pages)
        except Exception:
            # Retention and reconciliation remain authoritative; unreadable source
            # documents must route the extraction to review, not disappear.
            continue
    return pages


def verified_retained_document_bytes(document: Any, *, settings: Any | None = None) -> bytes:
    """Read once and return only the exact retained bytes whose identity verifies."""

    payload = read_stored_file_bytes(
        settings=settings or get_settings(),
        storage_backend=document.storage_backend,
        storage_key=document.storage_key,
    )
    if (
        hashlib.sha256(payload).hexdigest() != document.content_hash
        or len(payload) != document.storage_bytes
    ):
        raise ValueError("Retained AD source document hash or size mismatch")
    return payload


def retained_document_bytes_match(document: Any) -> bool:
    try:
        verified_retained_document_bytes(document)
    except Exception:
        return False
    return True


def retained_pdf_documents(directive: AirworthinessDirective) -> list[Any]:
    documents: list[Any] = []
    seen: set[str] = set()
    for publication in getattr(directive, "publications", []) or []:
        document = publication.source_document
        if document is None or document.id in seen or document.media_type != "application/pdf":
            continue
        seen.add(document.id)
        documents.append(document)
    return documents


def bounded_issue_pages(
    pages: list[dict[str, Any]],
    *,
    ad_number: str | None,
    title: str | None = None,
    context_pages: int = 0,
) -> list[dict[str, Any]]:
    """Keep only one AD section from a complete Federal Register issue.

    Federal Register pages routinely contain the end of one rule and the start
    of another. Returning whole neighboring pages therefore creates false
    evidence. This function slices the page text from the target Part 39
    heading through that rule's FR Doc footer and preserves page provenance.
    ``context_pages`` remains in the signature for backwards compatibility but
    is intentionally ignored.
    """
    _ = context_pages
    if not ad_number:
        return []
    normalized = ad_number.upper().removeprefix("AD ").strip()
    parts = normalized.split("-")
    if len(parts) != 3:
        return []
    year, sequence, item = (re.escape(part) for part in parts)
    short_year = re.escape(parts[0][2:]) if len(parts[0]) == 4 else year
    separator = r"[\s\-‐‑‒–—±]*"
    identifier_expression = rf"(?:{year}|{short_year}){separator}{sequence}{separator}{item}"
    identifier_pattern = re.compile(
        rf"\b(?:AD\s*)?{identifier_expression}\b",
        re.IGNORECASE,
    )
    if not pages:
        return []

    separator_token = "\n\n<<<PAPRNAV_PAGE_BREAK>>>\n\n"
    page_offsets: list[tuple[int, int]] = []
    chunks: list[str] = []
    cursor = 0
    for page in pages:
        text = page.get("text", "")
        chunks.append(text)
        page_offsets.append((cursor, cursor + len(text)))
        cursor += len(text) + len(separator_token)
    combined = separator_token.join(chunks)

    formal_matches = [
        match
        for pattern in formal_ad_identity_patterns(identifier_expression)
        if (match := pattern.search(combined)) is not None
    ]
    identifier_match = min(formal_matches, key=lambda match: match.start()) if formal_matches else identifier_pattern.search(combined)
    anchor_start = identifier_match.start() if identifier_match else None
    if anchor_start is None and title:
        title_terms = {
            term.lower()
            for term in re.findall(r"[A-Za-z0-9]+", title)
            if len(term) >= 5
            and term.lower() not in {"airworthiness", "directive", "directives"}
        }
        required_hits = max(1, min(2, len(title_terms)))
        if title_terms:
            lowered = combined.lower()
            candidate_offsets = [lowered.find(term) for term in title_terms]
            candidate_offsets = [offset for offset in candidate_offsets if offset >= 0]
            if len(candidate_offsets) >= required_hits:
                anchor_start = min(candidate_offsets)
    if anchor_start is None:
        return []

    heading_patterns = (
        re.compile(r"14\s+CFR\s+Part\s+39", re.IGNORECASE),
        re.compile(r"PART\s+39\s*[\-‐‑‒–—]+\s*AIRWORTHINESS\s+DIRECTIVES", re.IGNORECASE),
        re.compile(r"\[Docket\s+No\.[^\]]+\]", re.IGNORECASE),
    )
    section_start = anchor_start
    search_floor = max(0, anchor_start - 5000)
    prior_footers = list(
        re.finditer(r"\[(?:FR|PR)\s+Doc\.[^\]]+\]", combined[search_floor:anchor_start], re.IGNORECASE)
    )
    if prior_footers:
        search_floor += prior_footers[-1].end()
    prefix = combined[search_floor:anchor_start]
    heading_offsets = [
        search_floor + match.start()
        for pattern in heading_patterns
        for match in pattern.finditer(prefix)
    ]
    if heading_offsets:
        section_start = min(heading_offsets)

    footer = re.search(
        r"\[(?:FR|PR)\s+Doc\.[^\]]+\]",
        combined[anchor_start:],
        re.IGNORECASE,
    )
    if footer is None:
        # A missing/mangled footer is not permission to admit the remainder of
        # a Federal Register issue. The tail can contain an unrelated AD whose
        # genuine wording would otherwise become citation-eligible.
        return []
    footer_start = anchor_start + footer.start()
    intervening_text = combined[anchor_start + 1:footer_start]
    intervening_agency_boundary = re.search(
        r"(?:^|\n)\s*(?:"
        r"DEPARTMENT\s+OF\s+[A-Z][A-Z &-]+"
        r"|[A-Z][A-Z &-]+\s+(?:AGENCY|ADMINISTRATION|COMMISSION|BOARD|OFFICE)"
        r")\s*(?:\n|$)",
        intervening_text,
    )
    later_part39_numbers = [
        "-".join(match.groups())
        for match in re.finditer(
            r"(?:^|\n)\s*14\s+CFR\s+Part\s+39\b[\s\S]{0,500}?"
            r"(?:^|\n)\s*(?:AD\s*)?(\d{2,4})[\s\-‐‑‒–—±]+(\d{2})[\s\-‐‑‒–—±]+(\d{2})\b",
            intervening_text,
            re.IGNORECASE | re.MULTILINE,
        )
    ]
    target_numbers = {normalized}
    if len(parts[0]) == 4:
        target_numbers.add(f"{parts[0][2:]}-{parts[1]}-{parts[2]}")
    has_different_later_ad = any(
        number.upper() not in target_numbers for number in later_part39_numbers
    )
    if intervening_agency_boundary is not None or has_different_later_ad:
        # A recognizable later-document header or closing billing marker before
        # the first valid footer means that footer cannot be attributed to the
        # target rule. This also rejects a non-Part-39 neighbor after an
        # OCR-corrupted target footer.
        return []
    section_end = anchor_start + footer.end()

    selected: list[dict[str, Any]] = []
    for page, (page_start, page_end) in zip(pages, page_offsets, strict=True):
        overlap_start = max(section_start, page_start)
        overlap_end = min(section_end, page_end)
        if overlap_start >= overlap_end:
            continue
        scoped_text = combined[overlap_start:overlap_end].strip()
        if scoped_text:
            selected.append({**page, "text": scoped_text})
    return selected


def bounded_source_document_pages(
    pages: list[dict[str, Any]],
    *,
    ad_number: str | None,
    title: str | None = None,
) -> list[dict[str, Any]]:
    """Bound each retained document independently and combine its AD sections.

    A directive can have an original final rule plus a later correction. Bounding
    concatenated documents stops at the first matching FR Doc footer and can hide
    the other authoritative document from a reviewer.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for index, page in enumerate(pages):
        document_id = str(page.get("sourceDocumentId") or f"__document_{index}")
        if document_id not in grouped:
            grouped[document_id] = []
            order.append(document_id)
        grouped[document_id].append(page)
    bounded_by_document: dict[str, list[dict[str, Any]]] = {
        document_id: bounded_issue_pages(
            grouped[document_id],
            ad_number=ad_number,
            title=title,
        )
        for document_id in order
    }
    statuses = {
        document_id: source_evidence_status(ad_number, document_pages)[0]
        for document_id, document_pages in bounded_by_document.items()
    }
    has_primary_rule = any(status == "verified" for status in statuses.values())
    admitted: list[dict[str, Any]] = []
    for document_id in order:
        document_pages = bounded_by_document[document_id]
        status = statuses[document_id]
        if status == "verified" or (
            has_primary_rule
            and status == "identity_unverified"
            and correction_document_mentions_ad(document_pages, ad_number)
        ):
            admitted.extend(document_pages)
    return admitted


def correction_document_mentions_ad(
    pages: list[dict[str, Any]],
    ad_number: str | None,
) -> bool:
    official_number = official_ad_number(ad_number)
    if not pages or not official_number:
        return False
    text = "\n".join(str(page.get("text") or "") for page in pages)
    parts = official_number.split("-")
    if len(parts) != 3:
        return False
    separator = r"[\s\-‐‑‒–—±]*"
    identifier = separator.join(re.escape(part) for part in parts)
    return bool(
        re.search(rf"\b(?:AD\s*)?{identifier}\b", text, re.IGNORECASE)
        and re.search(r"\b(?:correction|correcting|technical\s+amendment)\b", text, re.IGNORECASE)
        and re.search(r"(?:14\s+CFR\s+Part\s+39|AIRWORTHINESS\s+DIRECTIVES)", text, re.IGNORECASE)
    )


def official_ad_number(ad_number: str | None) -> str | None:
    """Return the FAA source designation while retaining normalized IDs in storage."""
    if not ad_number:
        return None
    normalized = ad_number.upper().removeprefix("AD ").strip()
    parts = normalized.split("-")
    if len(parts) != 3:
        return normalized
    try:
        year = int(parts[0])
    except ValueError:
        return normalized
    if len(parts[0]) == 4 and year < 2000:
        return f"{parts[0][2:]}-{parts[1]}-{parts[2]}"
    return normalized


def source_evidence_status(
    ad_number: str | None,
    pages: list[dict[str, Any]],
) -> tuple[str, str]:
    """Classify whether retained text proves the directive identity."""
    if not pages:
        return "missing", "No retained source section is available. Approval is blocked."
    official_number = official_ad_number(ad_number)
    if not official_number:
        return "unverified", "The directive has no AD number to verify against the source."
    parts = official_number.split("-")
    if len(parts) != 3:
        return "unverified", "The directive identifier is not in a recognized FAA AD format."
    separator = r"[\s\-‐‑‒–—±]*"
    identifier_expression = rf"{re.escape(parts[0])}{separator}{re.escape(parts[1])}{separator}{re.escape(parts[2])}"
    identifier_pattern = re.compile(
        rf"\b(?:AD\s*)?{identifier_expression}\b",
        re.IGNORECASE,
    )
    source_text = "\n".join(page.get("text", "") for page in pages)
    if not identifier_pattern.search(source_text):
        return (
            "identity_unverified",
            f"Retained text does not contain official designation AD {official_number}. Approval is blocked.",
        )
    if not re.search(r"(?:14\s+CFR\s+Part\s+39|AIRWORTHINESS\s+DIRECTIVES)", source_text, re.IGNORECASE):
        return "unverified", "The retained section does not include a Part 39 / Airworthiness Directives heading."
    formal_identity_patterns = formal_ad_identity_patterns(identifier_expression)
    if not any(pattern.search(source_text) for pattern in formal_identity_patterns):
        formal_heading = re.search(
            r"adding\s+the\s+following\s+new\s+airworthiness\s+directive\s*:\s*(?:AD\s*)?(\d{2,4})[\s\-‐‑‒–—±]+(\d{2})[\s\-‐‑‒–—±]+(\d{2})\b",
            source_text,
            re.IGNORECASE,
        )
        if formal_heading:
            found = "-".join(formal_heading.groups())
            return (
                "identity_mismatch",
                f"The retained Part 39 section is AD {found}, not AD {official_number}. Approval is blocked.",
            )
        return (
            "identity_unverified",
            f"AD {official_number} appears only as a reference, not as the retained Part 39 directive heading. Approval is blocked.",
        )
    return "verified", f"Retained source section contains official designation AD {official_number}."


def formal_ad_identity_patterns(identifier_expression: str) -> tuple[re.Pattern[str], ...]:
    """Patterns that identify an AD as the rule body, not as a cross-reference."""
    return (
        re.compile(
            rf"(?:adding|adds)\s+(?:the\s+following\s+)?(?:new\s+)?(?:airworthiness\s+directive|AD)(?:\s+to\s+read\s+as\s+follows)?\s*:\s*(?:AD\s*)?{identifier_expression}\b",
            re.IGNORECASE,
        ),
        re.compile(
            rf"\[[^\]]{{0,300}}(?:Amendment[^\]]{{0,120}})?\bAD\s*{identifier_expression}\b[^\]]*\]",
            re.IGNORECASE,
        ),
        re.compile(
            rf"(?:^|\n)\s*(?:AD\s*)?{identifier_expression}\s+[^\n]{{0,180}}?\bAmendment\b",
            re.IGNORECASE,
        ),
    )


def extraction_approval_blocker_details(
    extraction: ADExtraction,
    output: dict[str, Any],
    source_pages: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Return stable codes plus messages for fail-closed approval reasons."""
    blockers: list[dict[str, str]] = []

    def add(code: str, message: str) -> None:
        blockers.append({"code": code, "message": message})

    evidence_status, evidence_message = source_evidence_status(
        extraction.directive.ad_number,
        source_pages,
    )
    if evidence_status != "verified":
        add("source_evidence_unverified", evidence_message)
    if extraction.schema_version != SCHEMA_VERSION:
        add(
            "schema_version_mismatch",
            f"Extraction schema {extraction.schema_version} is audit-only; {SCHEMA_VERSION} is required for approval."
        )
    proposed_number = str(output.get("adNumber") or "").upper().removeprefix("AD ").strip()
    expected_number = (extraction.directive.ad_number or "").upper().removeprefix("AD ").strip()
    if proposed_number != expected_number:
        add(
            "ad_number_mismatch",
            f"Proposed AD number {proposed_number or 'missing'} does not match normalized directive {expected_number or 'missing'}."
        )
    if (
        getattr(extraction, "input_content_hash", None) is not None
        and extraction.input_content_hash != extraction_input_hash(extraction.directive)
    ):
        add(
            "source_set_changed",
            "Retained source document set changed after extraction; generate and review a new extraction."
        )
    publication_date = getattr(
        getattr(extraction.directive, "discovery_record", None),
        "publication_date",
        None,
    )
    proposed_publication_date = output.get("publicationDate")
    if publication_date is not None and proposed_publication_date != publication_date.isoformat():
        add(
            "publication_date_mismatch",
            "Proposed publicationDate does not match immutable discovery metadata."
        )
    if extraction.schema_version == SCHEMA_VERSION:
        try:
            validate_extraction_json_schema(output)
            validate_extraction_output(
                output,
                require_v2_requirements=True,
                require_nonempty_requirements=True,
                require_nonempty_applicability=True,
            )
            validate_requirement_evidence(output, source_pages)
        except ValueError as exc:
            add("schema_or_evidence_invalid", str(exc))
        unresolved = [
            str(reason).strip()
            for requirement in output.get("requirements") or []
            for reason in requirement.get("uncertaintyReasons") or []
            if str(reason).strip()
        ]
        if unresolved:
            add(
                "requirement_uncertainty",
                f"Resolve {len(unresolved)} requirement uncertainty reason(s) before approval."
            )
        applicability_unresolved = [
            str(reason).strip()
            for group in output.get("applicabilityGroups") or []
            for reason in group.get("uncertaintyReasons") or []
            if str(reason).strip()
        ]
        if applicability_unresolved:
            add(
                "applicability_uncertainty",
                f"Resolve {len(applicability_unresolved)} applicability uncertainty reason(s) before approval."
            )
        amoc_unresolved = [
            str(reason).strip()
            for provision in output.get("amocProvisions") or []
            for reason in provision.get("uncertaintyReasons") or []
            if str(reason).strip()
        ]
        if amoc_unresolved:
            add(
                "amoc_uncertainty",
                f"Resolve {len(amoc_unresolved)} AMOC uncertainty reason(s) before approval."
            )
    return blockers


def extraction_approval_blockers(
    extraction: ADExtraction,
    output: dict[str, Any],
    source_pages: list[dict[str, Any]],
) -> list[str]:
    """Return presentation messages for fail-closed approval reasons."""
    return [
        blocker["message"]
        for blocker in extraction_approval_blocker_details(
            extraction,
            output,
            source_pages,
        )
    ]


def extraction_input_hash(directive: AirworthinessDirective) -> str:
    documents = retained_pdf_documents(directive)
    if not documents:
        return directive.source_content_hash
    material = {
        "directiveHash": directive.source_content_hash,
        "documents": sorted((document.id, document.content_hash) for document in documents),
        "schemaVersion": SCHEMA_VERSION,
    }
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()


def response_output_text(payload: dict[str, Any]) -> str:
    for output_item in payload.get("output", []) or []:
        for content_item in output_item.get("content", []) or []:
            if "text" in content_item:
                return str(content_item["text"])
    raise ValueError("OpenAI response did not include output text")


def prompt_hash() -> str:
    material = json.dumps(
        {
            "promptVersion": OPENAI_PROMPT_VERSION,
            "prompt": AD_EXTRACTION_SYSTEM_PROMPT,
            "schema": AD_EXTRACTION_JSON_SCHEMA,
        },
        sort_keys=True,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def normalize_scalar(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def normalize_regulatory_text(value: Any) -> str:
    """Compare regulatory wording while ignoring layout-only punctuation.

    Federal Register PDF extraction inserts line-wrap hyphens and typography
    variants. Token comparison preserves the word sequence while preventing a
    paraphrase from passing as a verbatim action.
    """
    def join_wrapped_token(match: re.Match[str]) -> str:
        left, right = match.groups()
        return f"{left}{right}" if left.isalpha() and right.isalpha() else f"{left} {right}"

    text = re.sub(r"(\w)-\s*\n\s*(\w)", join_wrapped_token, str(value or ""))
    return " ".join(re.findall(r"\w+", text.casefold()))


def normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(normalize_scalar(item) for item in value if normalize_scalar(item))
