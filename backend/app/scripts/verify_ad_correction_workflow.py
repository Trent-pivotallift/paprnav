from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from reportlab.pdfgen import canvas
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.core import (
    ADAMOCProvision,
    ADComplianceRequirement,
    ADCoverageSet,
    ADCoverageSubscription,
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    ADPublication,
    ADSourceDocument,
    ADMatchResult,
    ADTargetApplicability,
    Aircraft,
    AircraftADDueState,
    AirworthinessDirective,
    InstalledComponent,
    Organization,
    OrganizationMembership,
    User,
)
from app.services.ad_applicability import populate_applicability_from_extraction
from app.services.ad_extraction import (
    extraction_input_hash,
    extract_full_text_pages,
)
from app.services.ad_recurrence import materialize_requirements_from_extraction
from app.services.ad_release import released_signed_extractions
from app.services.ad_matching import ALGORITHM_NAME, ALGORITHM_VERSION


REVIEW_ID = "arv_t081_correction"
EXTRACTION_ID = "adx_t081_correction"
ACTOR_ID = "usr_t081_correction"


def output_packet(action_text: str) -> dict:
    applicability_text = (
        "This AD applies to Cessna Model 172R airplanes, all serial numbers."
    )
    amoc_text = "The Manager has the authority to approve AMOCs for this AD."
    return {
        "adNumber": "2099-00-82",
        "title": "Airworthiness Directives; Cessna 172R Airplanes",
        "effectiveDate": None,
        "publicationDate": None,
        "affectedProducts": ["Cessna 172R airplanes"],
        "applicabilityGroups": [{
            "groupKey": "cessna-172r",
            "productType": "aircraft",
            "productSubtype": None,
            "manufacturer": {"sourceName": "Cessna", "normalizedName": None},
            "modelApplicability": {
                "kind": "listed",
                "models": [{
                    "sourceDesignation": "172R",
                    "normalizedDesignation": None,
                    "aliases": [],
                }],
                "sourceText": applicability_text,
            },
            "serialNumberApplicability": {
                "kind": "all", "values": [], "ranges": [],
                "excludedValues": [], "sourceText": "all serial numbers",
            },
            "equipmentCombinationLogic": "all",
            "equipmentConditions": [],
            "conditions": [],
            "citations": [{
                "sourceDocumentId": "asd_t081_correction",
                "pageNumber": 1,
                "text": applicability_text,
            }],
            "confidence": 1.0,
            "uncertaintyReasons": [],
        }],
        "complianceActions": [action_text],
        "complianceIntervals": [],
        "supersedesAdNumbers": [],
        "sourceUrls": {"html": None, "pdf": None, "publicInspectionPdf": None},
        "confidence": 1.0,
        "citations": [],
        "uncertaintyReasons": [],
        "requirements": [{
            "requirementKey": "seat-rail",
            "applicabilityGroupKeys": ["cessna-172r"],
            "requirementType": "one_time",
            "actionText": action_text,
            "initialThresholds": [],
            "recurringTriggers": [],
            "combinationLogic": "all",
            "conditions": [],
            "terminatingAction": None,
            "citations": [{
                "sourceDocumentId": "asd_t081_correction",
                "pageNumber": 1,
                "text": action_text,
            }],
            "confidence": 1.0,
            "uncertaintyReasons": [],
        }],
        "amocProvisions": [{
            "provisionKey": "paragraph-i",
            "authorityText": amoc_text,
            "approvingAuthority": "Manager",
            "submissionInstructions": None,
            "conditions": [],
            "citations": [{
                "sourceDocumentId": "asd_t081_correction",
                "pageNumber": 1,
                "text": amoc_text,
            }],
            "confidence": 1.0,
            "uncertaintyReasons": [],
        }],
    }


def seed(storage_dir: Path) -> Path:
    pdf_path = storage_dir / "official.pdf"
    writer = canvas.Canvas(str(pdf_path))
    writer.drawString(72, 740, "14 CFR Part 39")
    writer.drawString(72, 720, "Section 39.13 is amended by adding the following new airworthiness directive: AD 2099-00-82.")
    writer.drawString(72, 700, "This AD applies to Cessna Model 172R airplanes, all serial numbers.")
    writer.drawString(72, 680, "Inspect the seat rail.")
    writer.drawString(72, 660, "Replace the seat rail.")
    writer.drawString(72, 640, "The Manager has the authority to approve AMOCs for this AD.")
    writer.drawString(72, 620, "[FR Doc. 2099-00082]")
    writer.save()
    payload = pdf_path.read_bytes()
    now = datetime.now(timezone.utc)
    original = output_packet("Inspect the seat rail.")

    with SessionLocal() as db:
        actor = User(
            id=ACTOR_ID,
            email="t081-correction@example.invalid",
            name="T081 Correction Admin",
            password_hash="not-a-login-credential",
            status="active",
        )
        organization = Organization(
            id="org_t081_correction", name="T081 Correction Operations", type="platform",
        )
        db.add_all([actor, organization])
        db.flush()
        db.add(OrganizationMembership(
            organization_id=organization.id,
            user_id=actor.id,
            role="platform_admin",
            status="active",
        ))
        aircraft = Aircraft(
            id="ac_t081_correction",
            owner_organization_id=organization.id,
            n_number_raw="N81082",
            n_number_normalized="N81082",
            make="Cessna",
            model="172R",
            serial_number="172R-T081",
            status="active",
            created_by_user_id=actor.id,
            airframe_serial_number="172R-T081",
        )
        component = InstalledComponent(
            id="cmp_t081_correction",
            aircraft=aircraft,
            role="airframe",
            component_type="aircraft",
            make="Cessna",
            model="172R",
            serial_number="172R-T081",
            source="aircraft_facts",
            confidence=1.0,
        )
        db.add_all([aircraft, component])
        directive = AirworthinessDirective(
            id="ad_t081_correction",
            ad_number="2099-00-82",
            title=original["title"],
            status="candidate",
            source_content_hash="a" * 64,
            extraction_status="complete",
            review_status="approved",
            approved_at=now,
        )
        document = ADSourceDocument(
            id="asd_t081_correction",
            source_system="federal_register",
            source_type="rule_pdf",
            source_identifier="T081-CORRECTION",
            storage_backend="local",
            storage_key=pdf_path.name,
            media_type="application/pdf",
            content_hash=hashlib.sha256(payload).hexdigest(),
            storage_bytes=len(payload),
            captured_at=now,
            status="retained",
        )
        publication = ADPublication(
            directive=directive,
            source_document=document,
            source_system="federal_register",
            source_type="rule_pdf",
            source_identifier="T081-CORRECTION",
            content_hash=document.content_hash,
            status="retained",
        )
        db.add_all([directive, document, publication])
        db.flush()
        extraction = ADExtraction(
            id=EXTRACTION_ID,
            directive=directive,
            provider_name="t081-verifier",
            provider_version="1",
            schema_version="ad_extraction_v3",
            input_content_hash=extraction_input_hash(directive),
            status="approved",
            confidence=1.0,
            output=original,
            citations=[],
            raw_response={"amocEnvelopeOrigin": "verification"},
        )
        db.add(extraction)
        db.flush()
        pages = extract_full_text_pages(directive)
        extraction.raw_response = {
            **extraction.raw_response,
            "retainedSourcePagesCached": True,
            "retainedSourcePages": pages,
            "sourcePageParser": "pypdf-native-text-v1",
        }
        db.add(ADExtractionReview(
            id=REVIEW_ID,
            extraction=extraction,
            status="approved",
            proposed_output=original,
            decision_output=original,
            decision="approved",
            reviewer_user_id=actor.id,
            reviewed_at=now,
        ))
        populate_applicability_from_extraction(db, extraction)
        materialize_requirements_from_extraction(db, extraction)
        db.flush()
        applicability = db.scalar(select(ADTargetApplicability).where(
            ADTargetApplicability.source_extraction_id == EXTRACTION_ID,
            ADTargetApplicability.status == "current",
        ))
        requirement = db.scalar(select(ADComplianceRequirement).where(
            ADComplianceRequirement.source_extraction_id == EXTRACTION_ID,
            ADComplianceRequirement.status == "current",
        ))
        if applicability is None or requirement is None:
            raise RuntimeError("Correction verifier failed to materialize signed rows")
        due_state = AircraftADDueState(
            id="adu_t081_correction",
            aircraft_id=aircraft.id,
            requirement_id=requirement.id,
            installed_component_id=component.id,
            status="not_due",
            due_metric=None,
            due_value=None,
            trigger_states=[],
            unresolved_reasons=[],
            algorithm_version="t081-verifier",
            input_hash="e" * 64,
            is_current=True,
        )
        coverage_set = ADCoverageSet(
            id="cov_t081_correction",
            target_id=applicability.target_id,
            status="current",
            coverage_version="t081-verifier",
            first_triggered_by_aircraft_id=aircraft.id,
            first_triggered_by_organization_id=organization.id,
            directive_count=1,
            source_document_count=1,
            derived_storage_bytes=len(payload),
            last_built_at=now,
            last_resolved_at=now,
            metadata_json={"fixture": True},
        )
        db.add_all([due_state, coverage_set])
        db.flush()
        db.add_all([
            ADCoverageSubscription(
                id="cvs_t081_correction",
                coverage_set_id=coverage_set.id,
                aircraft_id=aircraft.id,
                organization_id=organization.id,
                status="active",
                triggered_creation=True,
                last_resolved_at=now,
            ),
            ADMatchResult(
                id="adm_t081_correction",
                aircraft_id=aircraft.id,
                directive_id=directive.id,
                extraction_id=extraction.id,
                installed_component_id=component.id,
                target_applicability_id=applicability.id,
                due_state_id=due_state.id,
                status="candidate_satisfied",
                match_type="exact_component",
                confidence=1.0,
                rationale="PostgreSQL correction verifier fixture",
                unresolved_reasons=[],
                applicability_snapshot={},
                algorithm_name=ALGORITHM_NAME,
                algorithm_version=ALGORITHM_VERSION,
                input_hash="f" * 64,
                is_current=True,
            ),
        ])
        db.commit()

    patch_path = storage_dir / "correction.json"
    patch_path.write_text(json.dumps({
        "requirements": output_packet("Replace the seat rail.")["requirements"],
    }), encoding="utf-8")
    return patch_path


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="paprnav-t081-correction-") as tmp:
        storage_dir = Path(tmp)
        os.environ["PAPRNAV_LOCAL_STORAGE_PATH"] = str(storage_dir)
        patch_path = seed(storage_dir)
        result = subprocess.run(
            [
                sys.executable, "-m", "app.scripts.correct_approved_ad_review",
                "--review-id", REVIEW_ID,
                "--actor-user-id", ACTOR_ID,
                "--input", str(patch_path),
                "--reason", "PostgreSQL correction workflow verification",
                "--commit",
            ],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PAPRNAV_LOCAL_STORAGE_PATH": str(storage_dir)},
        )
        if result.returncode != 0:
            raise SystemExit(result.stdout + result.stderr)

        with SessionLocal() as db:
            review = db.get(ADExtractionReview, REVIEW_ID)
            checks = {
                "review_reopened": review.status == "pending",
                "decision_snapshot_retained": db.scalar(select(ADExtractionReviewDecision.id).where(
                    ADExtractionReviewDecision.review_id == REVIEW_ID,
                    ADExtractionReviewDecision.event_type == "approved_correction_snapshot",
                )) is not None,
                "extraction_revoked": review.extraction.status == "needs_review",
                "directive_revoked": review.extraction.directive.review_status == "pending",
                "applicability_revoked": all(
                    row.status != "current"
                    for row in db.scalars(select(ADTargetApplicability).where(
                        ADTargetApplicability.source_extraction_id == EXTRACTION_ID
                    )).all()
                ),
                "requirements_revoked": all(
                    row.status != "current"
                    for row in db.scalars(select(ADComplianceRequirement).where(
                        ADComplianceRequirement.source_extraction_id == EXTRACTION_ID
                    )).all()
                ),
                "amoc_revoked": all(
                    row.status != "current"
                    for row in db.scalars(select(ADAMOCProvision).where(
                        ADAMOCProvision.source_extraction_id == EXTRACTION_ID
                    )).all()
                ),
                "due_state_invalidated": db.get(
                    AircraftADDueState, "adu_t081_correction"
                ).is_current is False,
                "match_invalidated": db.get(
                    ADMatchResult, "adm_t081_correction"
                ).is_current is False,
                "coverage_quarantined": (
                    db.get(ADCoverageSet, "cov_t081_correction").status
                    == "pending_recalculation"
                    and db.get(ADCoverageSet, "cov_t081_correction").metadata_json
                    == {
                        "reason": "approved_ad_correction_staged",
                        "extractionId": EXTRACTION_ID,
                    }
                ),
                "released_reader_excludes_correction": released_signed_extractions(db)
                == [],
                "corrected_output_staged": review.proposed_output["requirements"][0]["actionText"]
                == "Replace the seat rail.",
            }
        passed = sum(checks.values())
        print(json.dumps(checks, sort_keys=True))
        print(f"{passed} passed out of {len(checks)}")
        if passed != len(checks):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
