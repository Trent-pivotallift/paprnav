from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.aircraft import get_visible_aircraft_or_404
from app.core.config import get_settings
from app.db.session import get_db
from app.models.core import Upload, User, new_id
from app.schemas.ingestion import IngestionJobSummary
from app.schemas.uploads import UploadCreateResponse, UploadResponse
from app.services.ingestion import create_ingestion_job
from app.services.cost_tags import upload_cost_tags
from app.services.observability import record_product_event, record_workflow_status
from app.services.storage import get_s3_client, store_upload_file

router = APIRouter(prefix="/api/v1/aircraft/{aircraft_id}/uploads", tags=["uploads"])
download_router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_SECTIONS = {"airframe", "engine", "propeller"}


def validate_upload(file: UploadFile, section: Optional[str]) -> None:
    if section and section not in ALLOWED_SECTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown logbook section")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file extension")


def serialize_upload(upload: Upload) -> UploadResponse:
    return UploadResponse(
        id=upload.id,
        aircraftId=upload.aircraft_id,
        originalFilename=upload.original_filename,
        contentType=upload.content_type,
        fileSizeBytes=upload.file_size_bytes,
        sha256=upload.sha256,
        status=upload.status,
        downloadUrl=f"/api/v1/uploads/{upload.id}/download",
        pilotConsentAccepted=upload.pilot_consent_accepted,
        initialOcrBillableToTag=upload.initial_ocr_billable_to_tag,
        costAllocationTags=upload.cost_allocation_tags,
    )


def serialize_ingestion_job(job) -> IngestionJobSummary:
    return IngestionJobSummary(
        id=job.id,
        uploadId=job.upload_id,
        uploadDownloadUrl=f"/api/v1/uploads/{job.upload_id}/download",
        aircraftId=job.aircraft_id,
        status=job.status,
        pageExtractionStatus=job.page_extraction_status,
        ocrStatus=job.ocr_status,
        verificationStatus=job.verification_status,
        entryExtractionStatus=job.entry_extraction_status,
        logbookSection=job.logbook_section_key,
        errorCode=job.error_code,
        errorMessage=job.error_message,
    )


def get_upload_or_404(db: Session, upload_id: str) -> Upload:
    upload = db.scalar(select(Upload).where(Upload.id == upload_id))
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    return upload


def local_upload_path(storage_root: str, storage_key: str) -> Path:
    root = Path(storage_root).resolve()
    path = (root / storage_key).resolve()
    if root not in path.parents and path != root:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage key")
    return path


def s3_body_iterator(body):
    if hasattr(body, "iter_chunks"):
        yield from body.iter_chunks()
        return

    while True:
        chunk = body.read(1024 * 1024)
        if not chunk:
            break
        yield chunk


def content_disposition(upload: Upload) -> str:
    disposition = "inline" if upload.content_type in ALLOWED_CONTENT_TYPES else "attachment"
    filename = quote(upload.original_filename)
    return f"{disposition}; filename*=UTF-8''{filename}"


@router.post("", response_model=UploadCreateResponse, status_code=status.HTTP_201_CREATED)
def upload_logbook_file(
    aircraft_id: str,
    file: UploadFile = File(...),
    section: Optional[str] = Form(default=None),
    pilotConsentAccepted: bool = Form(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadCreateResponse:
    aircraft = get_visible_aircraft_or_404(db, current_user, aircraft_id)
    validate_upload(file, section)
    if not pilotConsentAccepted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pilot consent is required before upload processing")

    settings = get_settings()
    upload_id = new_id("upl")
    tags = upload_cost_tags(
        organization=aircraft.owner_organization,
        aircraft=aircraft,
        upload_id=upload_id,
        stage="initial-ocr",
    )
    try:
        stored_file = store_upload_file(
            source=file.file,
            settings=settings,
            aircraft_id=aircraft_id,
            upload_id=upload_id,
            original_filename=file.filename or "upload.bin",
            content_type=file.content_type or "application/octet-stream",
            max_size_bytes=settings.max_upload_size_bytes,
            cost_allocation_tags=tags,
        )
    except ValueError as exc:
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if str(exc) == "Uploaded file is too large"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    upload = Upload(
        id=upload_id,
        aircraft_id=aircraft_id,
        uploaded_by_user_id=current_user.id,
        original_filename=file.filename or "upload.bin",
        content_type=file.content_type or "application/octet-stream",
        file_size_bytes=stored_file.file_size_bytes,
        storage_backend=stored_file.storage_backend,
        storage_key=stored_file.storage_key,
        sha256=stored_file.sha256,
        status="stored",
        pilot_consent_accepted=pilotConsentAccepted,
        initial_ocr_billable_to_tag=tags["BillableAccount"],
        cost_allocation_tags=tags,
    )
    db.add(upload)
    db.flush()
    ingestion_job = create_ingestion_job(db, upload, current_user.id, section)
    record_product_event(
        db,
        event_type="upload_created",
        subject_type="upload",
        subject_id=upload.id,
        actor=current_user,
        aircraft_id=aircraft_id,
        properties={
            "contentType": upload.content_type,
            "fileSizeBytes": upload.file_size_bytes,
            "section": section,
            "ingestionJobId": ingestion_job.id,
            "pilotConsentAccepted": upload.pilot_consent_accepted,
            "costAllocationTags": upload.cost_allocation_tags,
            "initialOcrBillableToTag": upload.initial_ocr_billable_to_tag,
        },
    )
    record_workflow_status(
        db,
        workflow_type="upload_ingestion",
        workflow_id=ingestion_job.id,
        previous_status=None,
        new_status=ingestion_job.status,
        reason="upload_created",
        actor_type="user",
        actor=current_user,
    )
    db.commit()
    db.refresh(upload)
    db.refresh(ingestion_job)
    return UploadCreateResponse(upload=serialize_upload(upload), ingestionJob=serialize_ingestion_job(ingestion_job))


@download_router.get("/{upload_id}/download")
def download_upload(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    upload = get_upload_or_404(db, upload_id)
    get_visible_aircraft_or_404(db, current_user, upload.aircraft_id)

    settings = get_settings()
    if upload.storage_backend == "s3":
        if not settings.s3_upload_bucket:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="S3 upload bucket is not configured")
        try:
            response = get_s3_client(settings.aws_region).get_object(Bucket=settings.s3_upload_bucket, Key=upload.storage_key)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found") from exc

        return StreamingResponse(
            s3_body_iterator(response["Body"]),
            media_type=upload.content_type,
            headers={"Content-Disposition": content_disposition(upload)},
        )

    file_path = local_upload_path(settings.local_storage_path, upload.storage_key)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")

    return FileResponse(
        path=file_path,
        media_type=upload.content_type,
        headers={"Content-Disposition": content_disposition(upload)},
    )
