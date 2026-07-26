from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.core import (
    Aircraft,
    AircraftAssignment,
    LogbookEntry,
    LogbookSection,
    Organization,
    OrganizationMembership,
    PageVerification,
    Upload,
    User,
    new_id,
)
from app.services.cost_tags import normalize_tag_value, upload_cost_tags
from app.services.ingestion import create_ingestion_job, extract_entries_from_job, process_ingestion_job
from app.services.layout_first_ocr import LayoutFirstVLMOCRProvider
from app.services.ocr_provider import OCRProvider, TextractOCRProvider, get_ocr_provider
from app.services.ocr_benchmark import (
    materialize_ocr_benchmark_selection,
    resolve_ocr_benchmark_selection,
)
from app.services.storage import store_s3_file

DEFAULT_INPUT = Path("backend/.data/ocr-feasibility/input/N3671L_page2.pdf")
DEFAULT_OUTPUT = Path("backend/.data/ocr-feasibility/output/N3671L_page2_summary.json")
DEFAULT_ACCOUNT_TAG = "paprnav-internal-test"
DEFAULT_N_NUMBER = "N3671L"
DEFAULT_MAX_PAGES = 3
FEASIBILITY_EMAIL = "ocr.feasibility@paprnav.local"
FEASIBILITY_PASSWORD_HASH = hash_password("demo-password")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the paprnav OCR feasibility slice against a guarded PDF sample.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--n-number", default=DEFAULT_N_NUMBER)
    parser.add_argument("--account-tag", default=DEFAULT_ACCOUNT_TAG)
    parser.add_argument("--section", choices=["airframe", "engine", "propeller"], default="airframe")
    parser.add_argument(
        "--provider",
        choices=["configured", "textract", "layout_first_vlm"],
        default="configured",
        help="Select the OCR engine explicitly for reproducible comparisons.",
    )
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--extract-entries", action="store_true")
    parser.add_argument(
        "--benchmark-partition",
        choices=["ocr_refinement", "full_ingestion", "ingestion_ad_holdout"],
    )
    parser.add_argument("--benchmark-document", choices=["aircraft", "engine"])
    return parser.parse_args()


def pdf_page_count(path: Path) -> int:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for OCR feasibility page guardrails; install backend requirements") from exc

    reader = PdfReader(str(path))
    return len(reader.pages)


def build_provider(provider_name: str) -> OCRProvider:
    if provider_name == "textract":
        return TextractOCRProvider()
    if provider_name == "layout_first_vlm":
        return LayoutFirstVLMOCRProvider()
    return get_ocr_provider()


def get_or_create_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == FEASIBILITY_EMAIL))
    if user:
        user.status = "active"
        return user
    user = User(
        email=FEASIBILITY_EMAIL,
        name="Paprnav OCR Feasibility",
        password_hash=FEASIBILITY_PASSWORD_HASH,
        status="active",
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_organization(db: Session, *, account_tag: str) -> Organization:
    organization = db.scalar(select(Organization).where(Organization.customer_account_tag == account_tag))
    if organization:
        organization.name = "Paprnav Internal Test"
        organization.type = "internal_test"
        return organization
    organization = Organization(
        name="Paprnav Internal Test",
        type="internal_test",
        customer_account_tag=account_tag,
    )
    db.add(organization)
    db.flush()
    return organization


def get_or_create_membership(db: Session, *, organization: Organization, user: User) -> OrganizationMembership:
    membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization.id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if membership:
        membership.role = "owner_admin"
        membership.status = "active"
        return membership
    membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=user.id,
        role="owner_admin",
        status="active",
    )
    db.add(membership)
    db.flush()
    return membership


def get_or_create_aircraft(db: Session, *, organization: Organization, user: User, n_number: str) -> Aircraft:
    normalized = n_number.upper().replace("-", "").replace(" ", "")
    aircraft = db.scalar(select(Aircraft).where(Aircraft.n_number_normalized == normalized))
    aircraft_tag = normalize_tag_value(f"aircraft-{normalized}", fallback=normalized)
    if aircraft:
        aircraft.owner_organization_id = organization.id
        aircraft.cost_allocation_tag = aircraft_tag
        aircraft.status = "active"
        return aircraft
    aircraft = Aircraft(
        owner_organization_id=organization.id,
        n_number_raw=n_number.upper(),
        n_number_normalized=normalized,
        make="Unknown",
        model="Unknown",
        serial_number=None,
        year=None,
        status="active",
        created_by_user_id=user.id,
        cost_allocation_tag=aircraft_tag,
    )
    db.add(aircraft)
    db.flush()
    return aircraft


def get_or_create_assignment(db: Session, *, organization: Organization, aircraft: Aircraft, user: User) -> AircraftAssignment:
    assignment = db.scalar(
        select(AircraftAssignment).where(
            AircraftAssignment.aircraft_id == aircraft.id,
            AircraftAssignment.organization_id == organization.id,
        )
    )
    if assignment:
        assignment.role = "owner"
        assignment.status = "active"
        return assignment
    assignment = AircraftAssignment(
        aircraft_id=aircraft.id,
        organization_id=organization.id,
        assigned_by_user_id=user.id,
        role="owner",
        status="active",
    )
    db.add(assignment)
    db.flush()
    return assignment


def get_or_create_section(db: Session, *, section_key: str) -> LogbookSection:
    names = {"airframe": "Airframe", "engine": "Engine", "propeller": "Propeller"}
    sort_orders = {"airframe": 1, "engine": 2, "propeller": 3}
    section = db.scalar(select(LogbookSection).where(LogbookSection.key == section_key))
    if section:
        return section
    section = LogbookSection(key=section_key, name=names[section_key], sort_order=sort_orders[section_key])
    db.add(section)
    db.flush()
    return section


def create_s3_upload(db: Session, *, pdf_path: Path, organization: Organization, aircraft: Aircraft, user: User) -> Upload:
    settings = get_settings()
    if not settings.s3_upload_bucket:
        raise RuntimeError("PAPRNAV_S3_UPLOAD_BUCKET is required")

    upload_id = new_id("upl")
    tags = upload_cost_tags(organization=organization, aircraft=aircraft, upload_id=upload_id, stage="initial-ocr")
    key = f"{settings.s3_upload_prefix}/{aircraft.id}/{upload_id}/{pdf_path.name}"
    with pdf_path.open("rb") as source:
        stored = store_s3_file(
            source,
            bucket=settings.s3_upload_bucket,
            key=key,
            content_type="application/pdf",
            max_size_bytes=settings.max_upload_size_bytes,
            cost_allocation_tags=tags,
            region_name=settings.aws_region,
        )

    upload = Upload(
        id=upload_id,
        aircraft_id=aircraft.id,
        uploaded_by_user_id=user.id,
        original_filename=pdf_path.name,
        content_type="application/pdf",
        file_size_bytes=stored.file_size_bytes,
        storage_backend=stored.storage_backend,
        storage_key=stored.storage_key,
        sha256=stored.sha256,
        status="stored",
        pilot_consent_accepted=True,
        initial_ocr_billable_to_tag=tags["BillableAccount"],
        cost_allocation_tags=tags,
    )
    db.add(upload)
    db.flush()
    return upload


def summarize_job(db: Session, *, job_id: str, entries: list[LogbookEntry]) -> dict:
    from app.models.core import IngestionJob

    job = db.get(IngestionJob, job_id)
    if job is None:
        raise RuntimeError(f"Ingestion job disappeared: {job_id}")
    latest_run = job.ocr_runs[-1] if job.ocr_runs else None
    ocr_metadata = latest_run.cost_allocation_tags if latest_run and latest_run.cost_allocation_tags else {}
    pages = sorted(job.pages, key=lambda page: page.current_page_order)
    return {
        "jobId": job.id,
        "uploadId": job.upload_id,
        "aircraftId": job.aircraft_id,
        "status": job.status,
        "ocrStatus": job.ocr_status,
        "verificationStatus": job.verification_status,
        "entryExtractionStatus": job.entry_extraction_status,
        "billableAccountTag": latest_run.billable_account_tag if latest_run else None,
        "billableAircraftTag": latest_run.billable_aircraft_tag if latest_run else None,
        "billablePageCount": latest_run.billable_page_count if latest_run else None,
        "ocrProvider": latest_run.provider_name if latest_run else None,
        "ocrProviderVersion": latest_run.provider_version if latest_run else None,
        "ocrProviderMode": ocr_metadata.get("provider_mode"),
        "ocrProviderChannel": ocr_metadata.get("provider_channel"),
        "ocrFeatureTypes": ocr_metadata.get("textract_feature_types"),
        "ocrBlockCounts": ocr_metadata.get("textract_block_counts"),
        "processingSeconds": optional_float(latest_run.processing_seconds) if latest_run else None,
        "pricingUnit": latest_run.pricing_unit if latest_run else None,
        "pricingRateUsd": optional_float(latest_run.pricing_rate_usd) if latest_run else None,
        "estimatedCostUsd": optional_float(latest_run.estimated_cost_usd) if latest_run else None,
        "pages": [
            {
                "pageId": page.id,
                "sourcePageNumber": page.source_page_number,
                "currentPageOrder": page.current_page_order,
                "spanCount": len(page.ocr_spans),
                "spanCountsByType": span_counts_by_type(page.ocr_spans),
                "linePreview": [
                    span.text
                    for span in page.ocr_spans
                    if span.span_type.upper() == "LINE"
                    or span.span_type.upper().startswith("REGION_")
                ][:8],
                "structurePreview": [
                    {
                        "type": span.span_type,
                        "text": span.text,
                        "bbox": {
                            "left": span.bbox_left,
                            "top": span.bbox_top,
                            "width": span.bbox_width,
                            "height": span.bbox_height,
                        },
                    }
                    for span in sorted(page.ocr_spans, key=lambda item: item.reading_order)
                    if span.span_type.upper().startswith("REGION_")
                    or span.span_type.upper()
                    in {
                        "TABLE",
                        "CELL",
                        "MERGED_CELL",
                        "SIGNATURE",
                        "LAYOUT_TEXT",
                        "LAYOUT_TABLE",
                        "LAYOUT_HEADER",
                        "LAYOUT_SECTION_HEADER",
                    }
                ][:20],
            }
            for page in pages
        ],
        "entries": [
            {
                "id": entry.id,
                "entryDate": entry.entry_date.isoformat() if entry.entry_date else None,
                "description": entry.description,
                "performerName": entry.performer_name,
                "performerCredential": entry.performer_credential,
                "tachTime": entry.tach_time,
                "hobbsTime": entry.hobbs_time,
                "totalTime": entry.total_time,
                "reviewStatus": entry.review_status,
            }
            for entry in entries
        ],
    }


def span_counts_by_type(spans) -> dict[str, int]:
    counts: dict[str, int] = {}
    for span in spans:
        counts[span.span_type] = counts.get(span.span_type, 0) + 1
    return dict(sorted(counts.items()))


def optional_float(value) -> Optional[float]:
    return float(value) if value is not None else None


def main() -> None:
    args = parse_args()
    source_path = args.input.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if bool(args.benchmark_partition) != bool(args.benchmark_document):
        raise RuntimeError(
            "--benchmark-partition and --benchmark-document must be provided together"
        )

    with TemporaryDirectory(prefix="paprnav-ocr-benchmark-") as temp_dir:
        selection = None
        pdf_path = source_path
        if args.benchmark_partition and args.benchmark_document:
            selection = resolve_ocr_benchmark_selection(
                source_path=source_path,
                document=args.benchmark_document,
                partition=args.benchmark_partition,
            )
            pdf_path = Path(temp_dir) / (
                f"{source_path.stem}_{selection.partition}.pdf"
            )
            materialize_ocr_benchmark_selection(
                source_path=source_path,
                output_path=pdf_path,
                selection=selection,
            )

        page_count = pdf_page_count(pdf_path)
        if page_count > args.max_pages:
            raise RuntimeError(
                f"Refusing to OCR {page_count} pages; max-pages is {args.max_pages}"
            )

        with SessionLocal() as db:
            user = get_or_create_user(db)
            organization = get_or_create_organization(db, account_tag=args.account_tag)
            get_or_create_membership(db, organization=organization, user=user)
            aircraft = get_or_create_aircraft(db, organization=organization, user=user, n_number=args.n_number)
            get_or_create_assignment(db, organization=organization, aircraft=aircraft, user=user)
            get_or_create_section(db, section_key=args.section)
            upload = create_s3_upload(db, pdf_path=pdf_path, organization=organization, aircraft=aircraft, user=user)
            job = create_ingestion_job(db, upload, user.id, args.section)
            db.commit()

            processed_job = process_ingestion_job(db, job, provider=build_provider(args.provider))
            entries: list[LogbookEntry] = []
            if args.extract_entries and processed_job.ocr_status == "complete":
                db.add(
                    PageVerification(
                        ingestion_job_id=processed_job.id,
                        verified_by_user_id=user.id,
                        is_order_confirmed=True,
                        is_complete=True,
                        missing_or_uncertain_notes=(
                            f"Auto-confirmed for guarded {page_count}-page OCR feasibility run."
                        ),
                        page_order_snapshot={
                            "pages": [
                                {"pageId": page.id, "currentPageOrder": page.current_page_order}
                                for page in processed_job.pages
                            ]
                        },
                    )
                )
                processed_job.verification_status = "verified"
                processed_job.status = "ready_for_entry_extraction"
                processed_job.entry_extraction_status = "ready"
                db.commit()
                entries = extract_entries_from_job(db, processed_job)

            summary = summarize_job(db, job_id=processed_job.id, entries=entries)
            if selection is not None:
                summary["benchmark"] = {
                    "manifestVersion": selection.manifest_version,
                    "partition": selection.partition,
                    "document": selection.document,
                    "sourceSha256": selection.source_sha256,
                    "sourcePages": selection.source_pages,
                }

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(summary, indent=2, sort_keys=True))
        print(f"summary={args.output}")


if __name__ == "__main__":
    main()
