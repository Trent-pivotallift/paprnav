import uuid

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class TimestampMixin:
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("usr"))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    external_auth_subject: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    memberships = relationship("OrganizationMembership", back_populates="user")
    sessions = relationship("AuthSession", back_populates="user")


class AuthSession(TimestampMixin, Base):
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ses"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(512), nullable=True)

    user = relationship("User", back_populates="sessions")


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("org"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)

    memberships = relationship("OrganizationMembership", back_populates="organization")
    owned_aircraft = relationship("Aircraft", back_populates="owner_organization")
    aircraft_assignments = relationship("AircraftAssignment", back_populates="organization")


class OrganizationMembership(TimestampMixin, Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_membership_organization_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("mem"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class Aircraft(TimestampMixin, Base):
    __tablename__ = "aircraft"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ac"))
    owner_organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    n_number_raw: Mapped[str] = mapped_column(String(32), nullable=False)
    n_number_normalized: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    make: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(128), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    airframe_serial_number: Mapped[str] = mapped_column(String(128), nullable=True)
    engine_make: Mapped[str] = mapped_column(String(128), nullable=True)
    engine_model: Mapped[str] = mapped_column(String(128), nullable=True)
    engine_serial_number: Mapped[str] = mapped_column(String(128), nullable=True)
    propeller_make: Mapped[str] = mapped_column(String(128), nullable=True)
    propeller_model: Mapped[str] = mapped_column(String(128), nullable=True)
    propeller_serial_number: Mapped[str] = mapped_column(String(128), nullable=True)

    owner_organization = relationship("Organization", back_populates="owned_aircraft")
    created_by_user = relationship("User")
    assignments = relationship("AircraftAssignment", back_populates="aircraft")
    logbook_entries = relationship("LogbookEntry", back_populates="aircraft")
    uploads = relationship("Upload", back_populates="aircraft")


class AircraftAssignment(TimestampMixin, Base):
    __tablename__ = "aircraft_assignments"
    __table_args__ = (UniqueConstraint("aircraft_id", "organization_id", name="uq_aircraft_assignment"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("asn"))
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    assigned_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    aircraft = relationship("Aircraft", back_populates="assignments")
    organization = relationship("Organization", back_populates="aircraft_assignments")
    assigned_by_user = relationship("User")


class LogbookSection(Base):
    __tablename__ = "logbook_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("lbs"))
    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    entries = relationship("LogbookEntry", back_populates="logbook_section")


class LogbookEntry(TimestampMixin, Base):
    __tablename__ = "logbook_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("lbe"))
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    logbook_section_id: Mapped[str] = mapped_column(ForeignKey("logbook_sections.id"), nullable=False, index=True)
    entry_date: Mapped[Date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    performer_name: Mapped[str] = mapped_column(String(255), nullable=True)
    performer_credential: Mapped[str] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    tach_time: Mapped[float] = mapped_column(Float, nullable=True)
    hobbs_time: Mapped[float] = mapped_column(Float, nullable=True)
    total_time: Mapped[float] = mapped_column(Float, nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")

    aircraft = relationship("Aircraft", back_populates="logbook_entries")
    logbook_section = relationship("LogbookSection", back_populates="entries")
    created_by_user = relationship("User")
    evidence_links = relationship("LogbookEntryEvidence", back_populates="logbook_entry")


class Upload(TimestampMixin, Base):
    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("upl"))
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    uploaded_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="received")

    aircraft = relationship("Aircraft", back_populates="uploads")
    uploaded_by_user = relationship("User")
    ingestion_jobs = relationship("IngestionJob", back_populates="upload")


class IngestionJob(TimestampMixin, Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("job"))
    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id"), nullable=False, index=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="queued")
    page_extraction_status: Mapped[str] = mapped_column(String(64), nullable=False, default="queued")
    ocr_status: Mapped[str] = mapped_column(String(64), nullable=False, default="queued")
    verification_status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_started")
    entry_extraction_status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_started")
    logbook_section_key: Mapped[str] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    completed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    upload = relationship("Upload", back_populates="ingestion_jobs")
    aircraft = relationship("Aircraft")
    created_by_user = relationship("User")
    pages = relationship("IngestionPage", back_populates="ingestion_job", order_by="IngestionPage.current_page_order")
    ocr_runs = relationship("OCRRun", back_populates="ingestion_job")
    verifications = relationship("PageVerification", back_populates="ingestion_job")
    corrections = relationship("OCRCorrection", back_populates="ingestion_job")
    evidence_links = relationship("LogbookEntryEvidence", back_populates="ingestion_job")


class IngestionPage(TimestampMixin, Base):
    __tablename__ = "ingestion_pages"
    __table_args__ = (UniqueConstraint("ingestion_job_id", "source_page_number", name="uq_ingestion_page_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("pg"))
    ingestion_job_id: Mapped[str] = mapped_column(ForeignKey("ingestion_jobs.id"), nullable=False, index=True)
    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id"), nullable=False, index=True)
    source_page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    current_page_order: Mapped[int] = mapped_column(Integer, nullable=False)
    page_label: Mapped[str] = mapped_column(String(128), nullable=True)
    image_storage_backend: Mapped[str] = mapped_column(String(64), nullable=True)
    image_storage_key: Mapped[str] = mapped_column(String(1024), nullable=True)
    width_px: Mapped[int] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int] = mapped_column(Integer, nullable=True)
    rotation_degrees: Mapped[float] = mapped_column(Float, nullable=True)
    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    ingestion_job = relationship("IngestionJob", back_populates="pages")
    upload = relationship("Upload")
    ocr_spans = relationship("OCRTextSpan", back_populates="ingestion_page", order_by="OCRTextSpan.reading_order")
    corrections = relationship("OCRCorrection", back_populates="ingestion_page")
    evidence_links = relationship("LogbookEntryEvidence", back_populates="ingestion_page")


class PageVerification(Base):
    __tablename__ = "page_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ver"))
    ingestion_job_id: Mapped[str] = mapped_column(ForeignKey("ingestion_jobs.id"), nullable=False, index=True)
    verified_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    is_order_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False)
    missing_or_uncertain_notes: Mapped[str] = mapped_column(Text, nullable=True)
    page_order_snapshot: Mapped[dict] = mapped_column(JSON, nullable=True)
    verified_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ingestion_job = relationship("IngestionJob", back_populates="verifications")
    verified_by_user = relationship("User")


class OCRRun(Base):
    __tablename__ = "ocr_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ocr"))
    ingestion_job_id: Mapped[str] = mapped_column(ForeignKey("ingestion_jobs.id"), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(128), nullable=False)
    configuration_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="queued")
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ingestion_job = relationship("IngestionJob", back_populates="ocr_runs")
    spans = relationship("OCRTextSpan", back_populates="ocr_run")


class OCRTextSpan(TimestampMixin, Base):
    __tablename__ = "ocr_text_spans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("spn"))
    ocr_run_id: Mapped[str] = mapped_column(ForeignKey("ocr_runs.id"), nullable=False, index=True)
    ingestion_page_id: Mapped[str] = mapped_column(ForeignKey("ingestion_pages.id"), nullable=False, index=True)
    provider_block_id: Mapped[str] = mapped_column(String(255), nullable=True)
    span_type: Mapped[str] = mapped_column(String(64), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    confidence_scale: Mapped[str] = mapped_column(String(32), nullable=False, default="0_100")
    bbox_left: Mapped[float] = mapped_column(Float, nullable=True)
    bbox_top: Mapped[float] = mapped_column(Float, nullable=True)
    bbox_width: Mapped[float] = mapped_column(Float, nullable=True)
    bbox_height: Mapped[float] = mapped_column(Float, nullable=True)
    bbox_units: Mapped[str] = mapped_column(String(32), nullable=False, default="ratio")
    polygon: Mapped[list] = mapped_column(JSON, nullable=True)
    rotation_degrees: Mapped[float] = mapped_column(Float, nullable=True)
    reading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    relationships: Mapped[list] = mapped_column(JSON, nullable=True)

    ocr_run = relationship("OCRRun", back_populates="spans")
    ingestion_page = relationship("IngestionPage", back_populates="ocr_spans")
    corrections = relationship("OCRCorrection", back_populates="ocr_text_span")
    evidence_links = relationship("LogbookEntryEvidence", back_populates="ocr_text_span")


class OCRCorrection(TimestampMixin, Base):
    __tablename__ = "ocr_corrections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("cor"))
    ingestion_job_id: Mapped[str] = mapped_column(ForeignKey("ingestion_jobs.id"), nullable=False, index=True)
    ingestion_page_id: Mapped[str] = mapped_column(ForeignKey("ingestion_pages.id"), nullable=False, index=True)
    ocr_text_span_id: Mapped[str] = mapped_column(ForeignKey("ocr_text_spans.id"), nullable=False, index=True)
    corrected_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    original_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    correction_reason: Mapped[str] = mapped_column(String(64), nullable=False, default="low_confidence")
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    ingestion_job = relationship("IngestionJob", back_populates="corrections")
    ingestion_page = relationship("IngestionPage", back_populates="corrections")
    ocr_text_span = relationship("OCRTextSpan", back_populates="corrections")
    corrected_by_user = relationship("User")
    evidence_links = relationship("LogbookEntryEvidence", back_populates="ocr_correction")


class LogbookEntryEvidence(Base):
    __tablename__ = "logbook_entry_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("evd"))
    logbook_entry_id: Mapped[str] = mapped_column(ForeignKey("logbook_entries.id"), nullable=False, index=True)
    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id"), nullable=False, index=True)
    ingestion_job_id: Mapped[str] = mapped_column(ForeignKey("ingestion_jobs.id"), nullable=False, index=True)
    ingestion_page_id: Mapped[str] = mapped_column(ForeignKey("ingestion_pages.id"), nullable=True, index=True)
    ocr_text_span_id: Mapped[str] = mapped_column(ForeignKey("ocr_text_spans.id"), nullable=True, index=True)
    ocr_correction_id: Mapped[str] = mapped_column(ForeignKey("ocr_corrections.id"), nullable=True, index=True)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    field_name: Mapped[str] = mapped_column(String(128), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    extraction_provider_name: Mapped[str] = mapped_column(String(128), nullable=True)
    extraction_provider_version: Mapped[str] = mapped_column(String(128), nullable=True)
    extraction_schema_version: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    logbook_entry = relationship("LogbookEntry", back_populates="evidence_links")
    upload = relationship("Upload")
    ingestion_job = relationship("IngestionJob", back_populates="evidence_links")
    ingestion_page = relationship("IngestionPage", back_populates="evidence_links")
    ocr_text_span = relationship("OCRTextSpan", back_populates="evidence_links")
    ocr_correction = relationship("OCRCorrection", back_populates="evidence_links")
