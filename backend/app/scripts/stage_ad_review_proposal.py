from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    ADPublication,
    AirworthinessDirective,
    User,
)
from app.services.ad_extraction import (
    SCHEMA_VERSION,
    bounded_source_document_pages,
    derive_compliance_action_summaries,
    ensure_persisted_source_pages,
    extraction_approval_blocker_details,
    extraction_approval_blockers,
    normalize_regulatory_text,
    structured_output_hash,
    validate_extraction_json_schema,
    validate_extraction_output,
    validate_requirement_evidence,
)
from app.services.observability import record_product_event, record_workflow_status


VISUAL_OCR_REASON_PATTERN = re.compile(
    r"^visual_ocr_model_cell_mismatch"
    r"\|modelIndex=(?P<model_index>\d+)"
    r"\|visual=(?P<visual>[^|]+)"
    r"\|parsed=(?P<parsed>[^|]+)"
    r"\|sourceDocumentId=(?P<document_id>[^|]+)"
    r"\|pageNumber=(?P<page_number>\d+)$"
)


def contains_normalized_phrase(haystack: str, needle: str) -> bool:
    return f" {needle} " in f" {haystack} "


def visual_ocr_validation_shadow(
    proposal: dict[str, Any],
    source_pages: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Substitute only explicitly recorded visual-vs-parser model cells for draft validation.

    The returned shadow is never persisted. Authenticated approval validates the
    unmodified proposal, so every visual correction remains fail-closed until
    retained source text is remediated and reviewed.
    """

    shadow = copy.deepcopy(proposal)
    page_index = {
        (str(page["sourceDocumentId"]), int(page["pageNumber"])):
        normalize_regulatory_text(page["text"])
        for page in source_pages
    }
    records: list[dict[str, Any]] = []
    for group_index, (group, shadow_group) in enumerate(zip(
        proposal.get("applicabilityGroups") or [],
        shadow.get("applicabilityGroups") or [],
        strict=True,
    )):
        for reason in group.get("uncertaintyReasons") or []:
            match = VISUAL_OCR_REASON_PATTERN.fullmatch(str(reason).strip())
            if match is None:
                continue
            model_index = int(match.group("model_index"))
            visual = match.group("visual").strip()
            parsed = match.group("parsed").strip()
            document_id = match.group("document_id").strip()
            page_number = int(match.group("page_number"))
            models = group.get("modelApplicability", {}).get("models") or []
            shadow_models = shadow_group.get("modelApplicability", {}).get("models") or []
            if model_index >= len(models) or model_index >= len(shadow_models):
                raise ValueError(
                    f"AD applicability group {group_index} visual OCR model index is out of range"
                )
            model = models[model_index]
            shadow_model = shadow_models[model_index]
            if str(model.get("sourceDesignation") or "").strip() != visual:
                raise ValueError(
                    f"AD applicability group {group_index} visual OCR record does not match sourceDesignation"
                )
            if model.get("normalizedDesignation") is not None:
                raise ValueError(
                    f"AD applicability group {group_index} visual OCR model normalizedDesignation must be null"
                )
            cited_keys = {
                (str(citation.get("sourceDocumentId")), int(citation.get("pageNumber")))
                for citation in group.get("citations") or []
                if citation.get("sourceDocumentId") and citation.get("pageNumber")
            }
            page_key = (document_id, page_number)
            if page_key not in cited_keys or page_key not in page_index:
                raise ValueError(
                    f"AD applicability group {group_index} visual OCR record must identify an admitted cited page"
                )
            parsed_text = page_index[page_key]
            if not contains_normalized_phrase(
                parsed_text, normalize_regulatory_text(parsed)
            ):
                raise ValueError(
                    f"AD applicability group {group_index} visual OCR parsed token is not present on the cited page"
                )
            if contains_normalized_phrase(
                parsed_text, normalize_regulatory_text(visual)
            ):
                raise ValueError(
                    f"AD applicability group {group_index} visual OCR correction is already present in retained text"
                )
            shadow_model["sourceDesignation"] = parsed
            records.append({
                "groupIndex": group_index,
                "modelIndex": model_index,
                "visual": visual,
                "parsed": parsed,
                "sourceDocumentId": document_id,
                "pageNumber": page_number,
            })
    return shadow, records


def allowed_incomplete_blockers(
    proposal: dict[str, Any],
    source_pages: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    """Validate a complete draft and return its narrowly typed allowed blockers."""

    validate_extraction_json_schema(proposal)
    validate_extraction_output(
        proposal,
        require_v2_requirements=True,
        require_nonempty_requirements=True,
        require_nonempty_applicability=True,
    )
    shadow, visual_records = visual_ocr_validation_shadow(proposal, source_pages)
    validate_requirement_evidence(shadow, source_pages)
    codes: list[str] = []
    applicability_count = sum(
        len(group.get("uncertaintyReasons") or [])
        for group in proposal.get("applicabilityGroups") or []
    )
    requirement_count = sum(
        len(requirement.get("uncertaintyReasons") or [])
        for requirement in proposal.get("requirements") or []
    )
    amoc_count = sum(
        len(provision.get("uncertaintyReasons") or [])
        for provision in proposal.get("amocProvisions") or []
    )
    if applicability_count:
        codes.append("applicability_uncertainty")
    if requirement_count:
        codes.append("requirement_uncertainty")
    if amoc_count:
        codes.append("amoc_uncertainty")
    if visual_records:
        codes.append("visual_ocr_model_cell_mismatch")
    return shadow, codes, visual_records


def stage_review_proposal(
    db: Session,
    *,
    ad_number: str,
    review_id: str,
    actor_user_id: str,
    loaded_proposal: dict[str, Any],
    allow_incomplete: bool,
) -> dict[str, Any]:
    if not isinstance(loaded_proposal, dict):
        raise ValueError("Proposal input must be a complete v3 JSON object")
    actor = db.scalar(
        select(User)
        .where(User.id == actor_user_id)
        .options(selectinload(User.memberships))
    )
    if actor is None or actor.status != "active" or not any(
        membership.status == "active" and membership.role == "platform_admin"
        for membership in actor.memberships
    ):
        raise ValueError("An active Paprnav platform administrator actor is required")
    review = db.scalar(
        select(ADExtractionReview)
        .where(ADExtractionReview.id == review_id)
        .with_for_update()
        .options(
            selectinload(ADExtractionReview.extraction)
            .selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.discovery_record),
            selectinload(ADExtractionReview.extraction)
            .selectinload(ADExtraction.directive)
            .selectinload(AirworthinessDirective.publications)
            .selectinload(ADPublication.source_document),
        )
    )
    if review is None:
        raise ValueError(f"AD extraction review {review_id} was not found")
    directive = review.extraction.directive
    if directive.ad_number != ad_number:
        raise ValueError(
            f"Review {review_id} belongs to AD {directive.ad_number}, not {ad_number}"
        )
    if review.extraction.schema_version != SCHEMA_VERSION:
        raise ValueError(f"Review {review_id} is not a {SCHEMA_VERSION} extraction")
    if review.status != "pending" or review.extraction.status != "needs_review":
        raise ValueError(
            f"Review {review_id} is terminal or its extraction is not awaiting review"
        )

    proposal = derive_compliance_action_summaries(copy.deepcopy(loaded_proposal))
    pages = bounded_source_document_pages(
        ensure_persisted_source_pages(directive, review.extraction),
        ad_number=directive.ad_number,
        title=directive.title,
    )
    visual_records: list[dict[str, Any]] = []
    blocker_codes: list[str] = []
    if allow_incomplete:
        validation_output, blocker_codes, visual_records = allowed_incomplete_blockers(
            proposal, pages,
        )
        approval_blocker_details = extraction_approval_blocker_details(
            review.extraction, validation_output, pages,
        )
        allowed_codes = {
            "applicability_uncertainty",
            "requirement_uncertainty",
            "amoc_uncertainty",
        }
        fatal_blockers = [
            blocker["message"]
            for blocker in approval_blocker_details
            if blocker["code"] not in allowed_codes
        ]
        if fatal_blockers:
            raise ValueError(" ".join(fatal_blockers))
    else:
        validate_extraction_json_schema(proposal)
        validate_extraction_output(
            proposal,
            require_v2_requirements=True,
            require_nonempty_requirements=True,
            require_nonempty_applicability=True,
        )
        validate_requirement_evidence(proposal, pages)
        approval_blockers = extraction_approval_blockers(
            review.extraction, proposal, pages,
        )
        if approval_blockers:
            raise ValueError(" ".join(approval_blockers))

    prior_output = copy.deepcopy(review.proposed_output)
    prior_extraction_output = copy.deepcopy(review.extraction.output)
    if structured_output_hash(prior_output) != structured_output_hash(prior_extraction_output):
        raise ValueError(
            "Review proposed output and extraction output diverge; use the audited correction workflow before staging"
        )
    prior_hash = structured_output_hash(prior_output)
    new_hash = structured_output_hash(proposal)
    if prior_hash == new_hash:
        return {
            "review": review,
            "actor": actor,
            "proposal": proposal,
            "pages": pages,
            "blockerCodes": blocker_codes,
            "visualOcrRecords": visual_records,
            "stagingDecisionId": None,
            "idempotent": True,
        }

    staged_at = datetime.now(timezone.utc)
    staging_decision = ADExtractionReviewDecision(
        review_id=review.id,
        extraction_id=review.extraction_id,
        decision="proposal_staged",
        output_hash=new_hash,
        decision_output=proposal,
        actor_user_id=actor.id,
        decided_at=staged_at,
        notes="Complete cited v3 proposal staged for human review; no approval performed.",
        event_type="proposal_staged",
        metadata_json={
            "directiveId": review.extraction.directive_id,
            "adNumber": ad_number,
            "reviewId": review.id,
            "extractionId": review.extraction_id,
            "priorOutputHash": prior_hash,
            "priorOutput": prior_output,
            "priorExtractionOutputHash": structured_output_hash(prior_extraction_output),
            "priorExtractionOutput": prior_extraction_output,
            "newOutputHash": new_hash,
            "sourceInputHash": review.extraction.input_content_hash,
            "allowIncomplete": allow_incomplete,
            "allowedBlockerCodes": blocker_codes,
            "visualOcrRecords": visual_records,
        },
    )
    db.add(staging_decision)
    db.flush()
    review.proposed_output = proposal
    review.extraction.output = proposal
    review.extraction.confidence = float(
        proposal.get("confidence", review.extraction.confidence)
    )
    review.extraction.raw_response = {
        **(review.extraction.raw_response or {}),
        "latestProposalStagingDecisionId": staging_decision.id,
    }
    record_product_event(
        db,
        event_type="ad_extraction_proposal_staged",
        subject_type="ad_review",
        subject_id=review.id,
        actor=actor,
        properties={
            "directiveId": review.extraction.directive_id,
            "adNumber": ad_number,
            "stagingDecisionId": staging_decision.id,
            "priorOutputHash": prior_hash,
            "newOutputHash": new_hash,
            "requirementCount": len(proposal["requirements"]),
            "allowedBlockerCodes": blocker_codes,
        },
    )
    record_workflow_status(
        db,
        workflow_type="ad_extraction",
        workflow_id=review.extraction_id,
        previous_status="needs_review",
        new_status="needs_review",
        reason="cited_proposal_staged_for_human_review",
        actor_type="reviewer",
        actor=actor,
    )
    return {
        "review": review,
        "actor": actor,
        "proposal": proposal,
        "pages": pages,
        "blockerCodes": blocker_codes,
        "visualOcrRecords": visual_records,
        "stagingDecisionId": staging_decision.id,
        "idempotent": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage a complete cited AD extraction proposal for human review without approving it"
    )
    parser.add_argument("--ad-number", required=True)
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--actor-user-id", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    loaded_proposal = json.loads(Path(args.input).read_text(encoding="utf-8"))
    try:
        with SessionLocal() as db:
            result = stage_review_proposal(
                db,
                ad_number=args.ad_number,
                review_id=args.review_id,
                actor_user_id=args.actor_user_id,
                loaded_proposal=loaded_proposal,
                allow_incomplete=args.allow_incomplete,
            )
            checks = [
                ("exact_pending_review_locked", result["review"].status == "pending"),
                ("requirements_staged", len(result["proposal"]["requirements"]) > 0),
                ("retained_pages_available", len(result["pages"]) > 0),
                (
                    "no_approval_or_materialization",
                    result["review"].extraction.status == "needs_review",
                ),
            ]
            if args.commit:
                db.commit()
            else:
                db.rollback()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    passed = sum(value for _, value in checks)
    print(json.dumps({
        "adNumber": args.ad_number,
        "reviewId": args.review_id,
        "actorUserId": args.actor_user_id,
        "allowIncomplete": args.allow_incomplete,
        "blockerCodes": result["blockerCodes"],
        "visualOcrRecords": result["visualOcrRecords"],
        "stagingDecisionId": result["stagingDecisionId"],
        "idempotent": result["idempotent"],
        "committed": args.commit,
        "checks": dict(checks),
    }, sort_keys=True))
    print(f"{passed} passed out of {len(checks)}")
    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
