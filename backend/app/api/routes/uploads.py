from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.aircraft import get_visible_aircraft_or_404
from app.core.config import get_settings
from app.db.session import get_db
from app.models.core import Upload, User, new_id
from app.schemas.uploads import UploadCreateResponse, UploadResponse
from app.services.storage import store_local_file

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


@router.post("", response_model=UploadCreateResponse, status_code=status.HTTP_201_CREATED)
def upload_logbook_file(
    aircraft_id: str,
    file: UploadFile = File(...),
    section: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadCreateResponse:
    get_visible_aircraft_or_404(db, current_user, aircraft_id)
    validate_upload(file, section)

    settings = get_settings()
    upload_id = new_id("upl")
    try:
        stored_file = store_local_file(
            source=file.file,
            storage_root=settings.local_storage_path,
            aircraft_id=aircraft_id,
            upload_id=upload_id,
            original_filename=file.filename or "upload.bin",
            max_size_bytes=settings.max_upload_size_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc

    upload = Upload(
        id=upload_id,
        aircraft_id=aircraft_id,
        uploaded_by_user_id=current_user.id,
        original_filename=file.filename or "upload.bin",
        content_type=file.content_type or "application/octet-stream",
        file_size_bytes=stored_file.file_size_bytes,
        storage_backend="local",
        storage_key=stored_file.storage_key,
        sha256=stored_file.sha256,
        status="stored",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return UploadCreateResponse(upload=serialize_upload(upload))


@download_router.get("/{upload_id}/download")
def download_upload(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    upload = get_upload_or_404(db, upload_id)
    get_visible_aircraft_or_404(db, current_user, upload.aircraft_id)

    file_path = local_upload_path(get_settings().local_storage_path, upload.storage_key)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")

    return FileResponse(
        path=file_path,
        media_type=upload.content_type,
        filename=upload.original_filename,
    )
