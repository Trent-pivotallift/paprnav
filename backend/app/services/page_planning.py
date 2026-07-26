from __future__ import annotations

from difflib import SequenceMatcher
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import IngestionPage, LogicalPageRegion


PLAN_PROFILE = "provider-neutral-page-plan-v2"
REGION_PROFILE = "logical-page-regions-v1"
NATIVE_ROUTING_GATE_PROFILE = "native-text-routing-gate-v1"
NATIVE_ROUTING_ACTIVATED = True
NATIVE_ROUTING_ACTIVATION_STATUS = "active_controlled_fixture_gate_v1"


def native_text_routing_assessment(
    native_text: dict[str, Any] | None,
    classification: dict[str, Any] | None,
    *,
    activated: bool | None = None,
) -> dict[str, Any]:
    native = native_text or {}
    page_classification = classification or {}
    attributes = set(page_classification.get("attributes") or [])
    disqualifying_attributes = sorted(
        attributes
        & {
            "handwritten",
            "side_by_side",
            "faint",
            "degraded",
            "orientation_unverified",
            "layout_uncertain",
            "text_mode_uncertain",
        }
    )
    criteria = {
        "reliableNativeText": native.get("reliableCandidate") is True,
        "routingClassNativeText": page_classification.get("routingClass")
        == "native_text",
        "noDisqualifyingVisualAttributes": not disqualifying_attributes,
        "validGlyphRatio": float(native.get("validGlyphRatio") or 0) >= 0.995,
        "positionedSampleRatio": float(native.get("positionedSampleRatio") or 0)
        >= 0.98,
        "plausibleFontRatio": float(native.get("plausibleFontRatio") or 0)
        >= 0.98,
        "duplicateLineRatio": float(native.get("duplicateLineRatio", 1)) <= 0.05,
        "extractorAgreement": float(native.get("extractorAgreement") or 0) >= 0.98,
        "estimatedImageCoverage": float(
            native.get("estimatedImageCoverage") or 0
        )
        <= 0.25,
    }
    eligible = all(criteria.values())
    routing_activated = (
        NATIVE_ROUTING_ACTIVATED if activated is None else activated
    )
    return {
        "profile": NATIVE_ROUTING_GATE_PROFILE,
        "activationStatus": (
            NATIVE_ROUTING_ACTIVATION_STATUS
            if routing_activated
            else "calibration_pre_activation"
        ),
        "criteria": criteria,
        "disqualifyingAttributes": disqualifying_attributes,
        "eligibleIfActivated": eligible,
        "wouldBypassTextract": eligible and routing_activated,
        "reason": (
            "native_text_gate_passed"
            if eligible and routing_activated
            else "activation_not_enabled"
            if eligible
            else "page_does_not_meet_native_text_gate"
        ),
    }


def logical_region_specs(classification: dict[str, Any] | None) -> list[dict[str, Any]]:
    attributes = set((classification or {}).get("attributes") or [])
    if "side_by_side" in attributes:
        return [
            {
                "regionKey": "left",
                "regionType": "physical_page_side",
                "bboxLeft": 0.0,
                "bboxTop": 0.0,
                "bboxWidth": 0.5,
                "bboxHeight": 1.0,
                "readingOrder": 1,
            },
            {
                "regionKey": "right",
                "regionType": "physical_page_side",
                "bboxLeft": 0.5,
                "bboxTop": 0.0,
                "bboxWidth": 0.5,
                "bboxHeight": 1.0,
                "readingOrder": 2,
            },
        ]
    return [
        {
            "regionKey": "full",
            "regionType": "source_page",
            "bboxLeft": 0.0,
            "bboxTop": 0.0,
            "bboxWidth": 1.0,
            "bboxHeight": 1.0,
            "readingOrder": 1,
        }
    ]


def finalize_page_extraction_plan(
    db: Session,
    *,
    page: IngestionPage,
    provider_name: str,
    provider_version: str,
) -> None:
    specs = logical_region_specs(page.page_classification)
    existing = {
        region.region_key: region
        for region in db.scalars(
            select(LogicalPageRegion).where(
                LogicalPageRegion.ingestion_page_id == page.id
            )
        )
    }
    for spec in specs:
        region = existing.get(spec["regionKey"])
        if region is None:
            region = LogicalPageRegion(
                ingestion_page_id=page.id,
                region_key=spec["regionKey"],
                region_type=spec["regionType"],
                bbox_left=spec["bboxLeft"],
                bbox_top=spec["bboxTop"],
                bbox_width=spec["bboxWidth"],
                bbox_height=spec["bboxHeight"],
                bbox_units="ratio",
                reading_order=spec["readingOrder"],
            )
            db.add(region)
        region.classification = {
            "profile": REGION_PROFILE,
            "sourcePagePreserved": True,
            "coordinatesRelativeToCanonicalPage": True,
        }

    recognized_text = "\n".join(
        span.text for span in page.ocr_spans if span.span_type.upper() == "LINE"
    )
    native = page.native_text_evaluation or {}
    native_routing = native_text_routing_assessment(
        native,
        page.page_classification,
    )
    native_preview = native.get("textPreview") or ""
    agreement = None
    if native.get("reliableCandidate") and native_preview and recognized_text:
        agreement = round(
            SequenceMatcher(
                None,
                normalize_comparison_text(native_preview),
                normalize_comparison_text(recognized_text),
            ).ratio(),
            6,
        )

    attributes = set((page.page_classification or {}).get("attributes") or [])
    mandatory_review_reasons = []
    if "orientation_unverified" in attributes:
        mandatory_review_reasons.append("orientation_unverified")
    if (page.page_classification or {}).get("routingClass") in {"mixed", "uncertain"}:
        mandatory_review_reasons.append("routing_class_uncertain")
    if agreement is not None and agreement < 0.90:
        mandatory_review_reasons.append("native_textract_disagreement")

    page.extraction_plan = {
        "profile": PLAN_PROFILE,
        "mode": "shadow",
        "selectedProvider": provider_name,
        "selectedProviderVersion": provider_version,
        "nativeTextMayBypassOCR": False,
        "nativeTextRouting": native_routing,
        "logicalRegions": specs,
        "nativeTextAgreement": agreement,
        "mandatoryHumanReview": bool(mandatory_review_reasons),
        "mandatoryReviewReasons": mandatory_review_reasons,
        "retryEligibleStages": ["recognition", "validation"],
    }
    stages = dict(page.stage_results or {})
    stages["classification"] = stage_result("complete", 1)
    stages["recognition"] = stage_result("complete", 1, provider=provider_name)
    stages["extraction_plan"] = stage_result("complete", 1, profile=PLAN_PROFILE)
    page.stage_results = stages


def mark_page_stage_failure(
    page: IngestionPage,
    *,
    stage: str,
    error_code: str,
    retry_eligible: bool,
) -> None:
    stages = dict(page.stage_results or {})
    previous = stages.get(stage) or {}
    stages[stage] = stage_result(
        "failed",
        int(previous.get("attemptNumber") or 0) + 1,
        errorCode=error_code,
        retryEligible=retry_eligible,
    )
    page.stage_results = stages


def stage_result(status: str, attempt_number: int, **metadata: Any) -> dict[str, Any]:
    return {
        "status": status,
        "attemptNumber": attempt_number,
        **metadata,
    }


def normalize_comparison_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()
