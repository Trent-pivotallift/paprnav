import uuid
from datetime import date as PythonDate
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, LargeBinary, Numeric, String, Text, UniqueConstraint, func, text
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
    customer_account_tag: Mapped[str] = mapped_column(String(128), nullable=True, unique=True, index=True)

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
    cost_allocation_tag: Mapped[str] = mapped_column(String(128), nullable=True, unique=True, index=True)

    owner_organization = relationship("Organization", back_populates="owned_aircraft")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    assignments = relationship("AircraftAssignment", back_populates="aircraft")
    logbook_entries = relationship("LogbookEntry", back_populates="aircraft")
    uploads = relationship("Upload", back_populates="aircraft")
    ad_match_results = relationship("ADMatchResult", back_populates="aircraft")
    installed_components = relationship("InstalledComponent", back_populates="aircraft")
    ad_coverage_subscriptions = relationship("ADCoverageSubscription", back_populates="aircraft")
    ad_cost_entries = relationship("ADCostLedgerEntry", back_populates="aircraft")
    ad_compliance_events = relationship("ADComplianceEvent", back_populates="aircraft")
    ad_time_states = relationship("AircraftTimeState", back_populates="aircraft")
    ad_due_states = relationship("AircraftADDueState", back_populates="aircraft")


class InstalledComponent(TimestampMixin, Base):
    __tablename__ = "installed_components"
    __table_args__ = (
        UniqueConstraint(
            "aircraft_id",
            "role",
            "make",
            "model",
            "serial_number",
            "installed_at",
            name="uq_installed_component_identity",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("cmp"))
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    component_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    make: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    serial_number: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    installed_at: Mapped[Date] = mapped_column(Date, nullable=True)
    removed_at: Mapped[Date] = mapped_column(Date, nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="aircraft_facts")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)

    aircraft = relationship("Aircraft", back_populates="installed_components")
    match_results = relationship("ADMatchResult", back_populates="installed_component")
    ad_compliance_events = relationship("ADComplianceEvent", back_populates="installed_component")
    ad_time_states = relationship("AircraftTimeState", back_populates="installed_component")
    ad_due_states = relationship("AircraftADDueState", back_populates="installed_component")


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
    entry_date: Mapped[Optional[PythonDate]] = mapped_column(Date, nullable=True)
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
    reviewed_by_user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    reviewed_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    validation_status: Mapped[str] = mapped_column(String(64), nullable=True)
    validation_results: Mapped[dict] = mapped_column(JSON, nullable=True)

    aircraft = relationship("Aircraft", back_populates="logbook_entries")
    logbook_section = relationship("LogbookSection", back_populates="entries")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id])
    evidence_links = relationship("LogbookEntryEvidence", back_populates="logbook_entry")
    ad_compliance_events = relationship("ADComplianceEvent", back_populates="logbook_entry")
    ad_time_states = relationship("AircraftTimeState", back_populates="source_logbook_entry")


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
    pilot_consent_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    initial_ocr_billable_to_tag: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    cost_allocation_tags: Mapped[dict] = mapped_column(JSON, nullable=True)

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
    document_inspection: Mapped[dict] = mapped_column(JSON, nullable=True)
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
    inspection_status: Mapped[str] = mapped_column(String(64), nullable=True)
    source_page_fingerprint: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    canonical_image_sha256: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    render_profile: Mapped[str] = mapped_column(String(64), nullable=True)
    render_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    page_classification: Mapped[dict] = mapped_column(JSON, nullable=True)
    native_text_evaluation: Mapped[dict] = mapped_column(JSON, nullable=True)
    extraction_plan: Mapped[dict] = mapped_column(JSON, nullable=True)
    stage_results: Mapped[dict] = mapped_column(JSON, nullable=True)

    ingestion_job = relationship("IngestionJob", back_populates="pages")
    upload = relationship("Upload")
    ocr_spans = relationship("OCRTextSpan", back_populates="ingestion_page", order_by="OCRTextSpan.reading_order")
    corrections = relationship("OCRCorrection", back_populates="ingestion_page")
    evidence_links = relationship("LogbookEntryEvidence", back_populates="ingestion_page")
    logical_regions = relationship(
        "LogicalPageRegion",
        back_populates="ingestion_page",
        order_by="LogicalPageRegion.reading_order",
    )


class LogicalPageRegion(TimestampMixin, Base):
    __tablename__ = "logical_page_regions"
    __table_args__ = (
        UniqueConstraint("ingestion_page_id", "region_key", name="uq_logical_page_region_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("lpr"))
    ingestion_page_id: Mapped[str] = mapped_column(ForeignKey("ingestion_pages.id"), nullable=False, index=True)
    region_key: Mapped[str] = mapped_column(String(64), nullable=False)
    region_type: Mapped[str] = mapped_column(String(64), nullable=False)
    bbox_left: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_top: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_width: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_height: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_units: Mapped[str] = mapped_column(String(32), nullable=False, default="ratio")
    reading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    classification: Mapped[dict] = mapped_column(JSON, nullable=True)

    ingestion_page = relationship("IngestionPage", back_populates="logical_regions")


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
    billing_status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_billable")
    billable_account_tag: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    billable_aircraft_tag: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    billable_page_count: Mapped[int] = mapped_column(Integer, nullable=True)
    processing_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    pricing_unit: Mapped[str] = mapped_column(String(64), nullable=True)
    pricing_rate_usd: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=True)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=True)
    cost_allocation_tags: Mapped[dict] = mapped_column(JSON, nullable=True)
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
    corrections = relationship("OCRCorrection", back_populates="ocr_text_span", order_by="OCRCorrection.correction_order")
    evidence_links = relationship("LogbookEntryEvidence", back_populates="ocr_text_span")


class OCRCorrection(TimestampMixin, Base):
    __tablename__ = "ocr_corrections"
    __table_args__ = (
        UniqueConstraint("ocr_text_span_id", "correction_order", name="uq_ocr_corrections_span_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("cor"))
    ingestion_job_id: Mapped[str] = mapped_column(ForeignKey("ingestion_jobs.id"), nullable=False, index=True)
    ingestion_page_id: Mapped[str] = mapped_column(ForeignKey("ingestion_pages.id"), nullable=False, index=True)
    ocr_text_span_id: Mapped[str] = mapped_column(ForeignKey("ocr_text_spans.id"), nullable=False, index=True)
    corrected_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    original_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    correction_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
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
    review_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    logbook_entry = relationship("LogbookEntry", back_populates="evidence_links")
    upload = relationship("Upload")
    ingestion_job = relationship("IngestionJob", back_populates="evidence_links")
    ingestion_page = relationship("IngestionPage", back_populates="evidence_links")
    ocr_text_span = relationship("OCRTextSpan", back_populates="evidence_links")
    ocr_correction = relationship("OCRCorrection", back_populates="evidence_links")


class ADDiscoveryRecord(TimestampMixin, Base):
    __tablename__ = "ad_discovery_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("adr"))
    federal_register_document_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), nullable=True)
    abstract: Mapped[str] = mapped_column(Text, nullable=True)
    publication_date: Mapped[Date] = mapped_column(Date, nullable=True, index=True)
    effective_date: Mapped[Date] = mapped_column(Date, nullable=True)
    html_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    pdf_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    public_inspection_pdf_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    agency_names: Mapped[list] = mapped_column(JSON, nullable=True)
    excerpts: Mapped[str] = mapped_column(Text, nullable=True)
    api_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    classification: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    classification_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    classification_reason: Mapped[str] = mapped_column(Text, nullable=False)
    classifier_name: Mapped[str] = mapped_column(String(128), nullable=False)
    classifier_version: Mapped[str] = mapped_column(String(128), nullable=False)
    classified_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    directive = relationship("AirworthinessDirective", back_populates="discovery_record", uselist=False)


class ADSourceSnapshot(TimestampMixin, Base):
    __tablename__ = "ad_source_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("src"))
    source_system: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    storage_backend: Mapped[str] = mapped_column(String(64), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=True)
    captured_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="complete", index=True)
    parser_name: Mapped[str] = mapped_column(String(128), nullable=True)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=True)
    table_inventory: Mapped[dict] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    storage_bytes: Mapped[int] = mapped_column(BigInteger, nullable=True)

    publications = relationship("ADPublication", back_populates="source_snapshot")
    reconciliation_issues = relationship("ADReconciliationIssue", back_populates="source_snapshot")
    coverage_sets = relationship("ADCoverageSet", back_populates="current_source_snapshot")
    cost_entries = relationship("ADCostLedgerEntry", back_populates="source_snapshot")
    source_documents = relationship("ADSourceDocument", back_populates="source_snapshot")


class ADSourceDocument(TimestampMixin, Base):
    __tablename__ = "ad_source_documents"
    __table_args__ = (
        UniqueConstraint(
            "source_system",
            "source_type",
            "source_identifier",
            "content_hash",
            name="uq_ad_source_document_version",
        ),
        UniqueConstraint("id", "content_hash", name="uq_ad_source_document_id_content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("asd"))
    source_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("ad_source_snapshots.id"), nullable=True, index=True
    )
    source_system: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parent_source_identifier: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    storage_backend: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    media_type: Mapped[str] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    captured_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    publication_date: Mapped[Date] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="retained", index=True)
    parser_name: Mapped[str] = mapped_column(String(128), nullable=True)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)

    source_snapshot = relationship("ADSourceSnapshot", back_populates="source_documents")
    publications = relationship("ADPublication", back_populates="source_document")
    page_renditions = relationship("ADSourcePageRendition", back_populates="source_document")
    evidence_fragments = relationship(
        "ADEvidenceFragment", back_populates="source_document", viewonly=True
    )


class ADSourcePageRendition(Base):
    """Immutable, content-addressed rendering of one retained source page."""

    __tablename__ = "ad_source_page_renditions"
    __table_args__ = (
        CheckConstraint("page_number >= 1", name="ck_ad_source_page_rendition_page_number"),
        CheckConstraint("storage_bytes > 0", name="ck_ad_source_page_rendition_storage_bytes"),
        CheckConstraint("width_px > 0 AND height_px > 0", name="ck_ad_source_page_rendition_dimensions"),
        CheckConstraint("length(source_content_hash) = 64", name="ck_ad_source_page_rendition_source_hash"),
        CheckConstraint("length(renderer_configuration_hash) = 64", name="ck_ad_source_page_rendition_config_hash"),
        CheckConstraint("length(rendition_hash) = 64", name="ck_ad_source_page_rendition_hash"),
        ForeignKeyConstraint(
            ["source_document_id", "source_content_hash"],
            ["ad_source_documents.id", "ad_source_documents.content_hash"],
            name="fk_ad_source_page_rendition_document_hash",
        ),
        UniqueConstraint(
            "id", "source_document_id", "source_content_hash", "page_number",
            name="uq_ad_source_page_rendition_chain",
        ),
        UniqueConstraint(
            "source_document_id",
            "source_content_hash",
            "page_number",
            "renderer_configuration_hash",
            name="uq_ad_source_page_rendition_identity",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("asr"))
    source_document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    renderer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    renderer_version: Mapped[str] = mapped_column(String(128), nullable=False)
    renderer_configuration_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    media_type: Mapped[str] = mapped_column(String(255), nullable=False)
    width_px: Mapped[int] = mapped_column(Integer, nullable=False)
    height_px: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    rendition_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source_document = relationship("ADSourceDocument", back_populates="page_renditions")
    text_versions = relationship("ADSourcePageTextVersion", back_populates="rendition")


class ADSourcePageTextVersion(Base):
    """Immutable server-derived text bound to an immutable page rendition."""

    __tablename__ = "ad_source_page_text_versions"
    __table_args__ = (
        CheckConstraint("length(extractor_configuration_hash) = 64", name="ck_ad_source_page_text_config_hash"),
        CheckConstraint("length(text_hash) = 64", name="ck_ad_source_page_text_hash"),
        ForeignKeyConstraint(
            ["rendition_id", "source_document_id", "source_content_hash", "page_number"],
            [
                "ad_source_page_renditions.id",
                "ad_source_page_renditions.source_document_id",
                "ad_source_page_renditions.source_content_hash",
                "ad_source_page_renditions.page_number",
            ],
            name="fk_ad_source_page_text_rendition_chain",
        ),
        UniqueConstraint(
            "id", "rendition_id", "source_document_id", "source_content_hash", "page_number",
            name="uq_ad_source_page_text_chain",
        ),
        UniqueConstraint(
            "rendition_id",
            "extractor_configuration_hash",
            "text_hash",
            name="uq_ad_source_page_text_version_identity",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ast"))
    rendition_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    extractor_name: Mapped[str] = mapped_column(String(128), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(128), nullable=False)
    extractor_configuration_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    page_text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    coordinate_map_storage_key: Mapped[str] = mapped_column(String(1024), nullable=True)
    coordinate_map_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    extraction_quality: Mapped[float] = mapped_column(Float, nullable=True)
    text_classification: Mapped[str] = mapped_column(String(64), nullable=False, default="native")
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    rendition = relationship("ADSourcePageRendition", back_populates="text_versions")
    evidence_fragments = relationship(
        "ADEvidenceFragment", back_populates="page_text_version", viewonly=True
    )


class ADEvidenceFragment(Base):
    """One immutable exact clause; semantic consumers reference this row."""

    __tablename__ = "ad_evidence_fragments"
    __table_args__ = (
        CheckConstraint("page_start >= 1", name="ck_ad_evidence_fragment_page_start"),
        CheckConstraint("page_end = page_start", name="ck_ad_evidence_fragment_single_page"),
        CheckConstraint("character_start >= 0", name="ck_ad_evidence_fragment_character_start"),
        CheckConstraint("character_end > character_start", name="ck_ad_evidence_fragment_character_end"),
        CheckConstraint("length(source_content_hash) = 64", name="ck_ad_evidence_fragment_source_hash"),
        CheckConstraint("length(fragment_hash) = 64", name="ck_ad_evidence_fragment_hash"),
        CheckConstraint("length(exact_text) > 0", name="ck_ad_evidence_fragment_exact_text"),
        ForeignKeyConstraint(
            ["directive_id", "source_document_id"],
            ["ad_publications.directive_id", "ad_publications.source_document_id"],
            name="fk_ad_evidence_fragment_publication",
        ),
        ForeignKeyConstraint(
            ["source_document_id", "source_content_hash"],
            ["ad_source_documents.id", "ad_source_documents.content_hash"],
            name="fk_ad_evidence_fragment_document_hash",
        ),
        ForeignKeyConstraint(
            [
                "page_text_version_id", "rendition_id", "source_document_id",
                "source_content_hash", "page_start",
            ],
            [
                "ad_source_page_text_versions.id", "ad_source_page_text_versions.rendition_id",
                "ad_source_page_text_versions.source_document_id",
                "ad_source_page_text_versions.source_content_hash",
                "ad_source_page_text_versions.page_number",
            ],
            name="fk_ad_evidence_fragment_text_chain",
        ),
        UniqueConstraint(
            "page_text_version_id",
            "character_start",
            "character_end",
            "paragraph_locator",
            "table_locator",
            "row_locator",
            "note_locator",
            name="uq_ad_evidence_fragment_selection",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("aef"))
    directive_id: Mapped[str] = mapped_column(
        ForeignKey("airworthiness_directives.id"), nullable=False, index=True
    )
    source_document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rendition_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    page_text_version_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    paragraph_locator: Mapped[str] = mapped_column(String(255), nullable=True)
    table_locator: Mapped[str] = mapped_column(String(255), nullable=True)
    row_locator: Mapped[str] = mapped_column(String(255), nullable=True)
    note_locator: Mapped[str] = mapped_column(String(255), nullable=True)
    character_start: Mapped[int] = mapped_column(Integer, nullable=False)
    character_end: Mapped[int] = mapped_column(Integer, nullable=False)
    region_map_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    exact_text: Mapped[str] = mapped_column(Text, nullable=False)
    fragment_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    parser_name: Mapped[str] = mapped_column(String(128), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(128), nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source_document = relationship(
        "ADSourceDocument", back_populates="evidence_fragments", viewonly=True
    )
    directive = relationship("AirworthinessDirective", back_populates="evidence_fragments")
    page_text_version = relationship(
        "ADSourcePageTextVersion", back_populates="evidence_fragments", viewonly=True
    )
    created_by = relationship("User")
    lifecycle_events = relationship("ADEvidenceFragmentLifecycleEvent", back_populates="fragment")


class ADEvidenceFragmentLifecycleEvent(Base):
    """Append-only fragment usability history; fragments have no mutable status."""

    __tablename__ = "ad_evidence_fragment_lifecycle_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('admitted', 'superseded', 'quarantined')",
            name="ck_ad_evidence_fragment_lifecycle_event_type",
        ),
        CheckConstraint("length(event_hash) = 64", name="ck_ad_evidence_fragment_event_hash"),
        CheckConstraint(
            "predecessor_event_hash IS NULL OR length(predecessor_event_hash) = 64",
            name="ck_ad_evidence_fragment_predecessor_hash",
        ),
        CheckConstraint("sequence_number >= 0", name="ck_ad_evidence_fragment_event_sequence"),
        CheckConstraint(
            "(event_type = 'admitted' AND sequence_number = 0 AND predecessor_event_hash IS NULL) "
            "OR (event_type <> 'admitted' AND sequence_number > 0 AND predecessor_event_hash IS NOT NULL)",
            name="ck_ad_evidence_fragment_event_root",
        ),
        ForeignKeyConstraint(
            ["fragment_id", "predecessor_event_hash"],
            ["ad_evidence_fragment_lifecycle_events.fragment_id", "ad_evidence_fragment_lifecycle_events.event_hash"],
            name="fk_ad_evidence_fragment_event_predecessor",
        ),
        UniqueConstraint(
            "fragment_id", "event_hash", name="uq_ad_evidence_fragment_event_chain_identity"
        ),
        UniqueConstraint(
            "fragment_id", "sequence_number", name="uq_ad_evidence_fragment_event_sequence"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("afe"))
    fragment_id: Mapped[str] = mapped_column(
        ForeignKey("ad_evidence_fragments.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    predecessor_event_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    occurred_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    fragment = relationship("ADEvidenceFragment", back_populates="lifecycle_events")
    actor = relationship("User")


class ADV4CandidateProposal(Base):
    """Immutable candidate-only canonical V4 content; never a released decision."""

    __tablename__ = "ad_v4_candidate_proposals"
    __table_args__ = (
        CheckConstraint("schema_version = 'ad_extraction_v4'", name="ck_ad_v4_proposal_schema"),
        CheckConstraint("gate = 'candidate_only'", name="ck_ad_v4_proposal_gate"),
        CheckConstraint("length(canonical_hash) = 64", name="ck_ad_v4_proposal_hash"),
        CheckConstraint("length(evidence_binding_hash) = 64", name="ck_ad_v4_binding_hash"),
        UniqueConstraint(
            "directive_id", "canonicalization_version", "canonical_hash",
            name="uq_ad_v4_proposal_content",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("avp"))
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False)
    validator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    parsed_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    evidence_binding_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    evidence_binding_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    binding_count: Mapped[int] = mapped_column(Integer, nullable=False)
    gate: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate_only")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateEvidenceBinding(Base):
    __tablename__ = "ad_v4_candidate_evidence_bindings"
    __table_args__ = (
        UniqueConstraint("proposal_id", "evidence_key", name="uq_ad_v4_binding_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("avb"))
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False, index=True)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
    evidence_key: Mapped[str] = mapped_column(String(128), nullable=False)
    fragment_id: Mapped[str] = mapped_column(ForeignKey("ad_evidence_fragments.id"), nullable=False, index=True)
    fragment_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    admitted_event_id: Mapped[str] = mapped_column(ForeignKey("ad_evidence_fragment_lifecycle_events.id"), nullable=False)
    admitted_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    validator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-validator-1")
    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-c14n-1")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateSubmission(Base):
    __tablename__ = "ad_v4_candidate_submissions"
    __table_args__ = (
        CheckConstraint("actor_kind = 'platform_admin'", name="ck_ad_v4_submission_actor"),
        CheckConstraint("actor_role = 'platform_admin'", name="ck_ad_v4_submission_role"),
        CheckConstraint("actor_status = 'active'", name="ck_ad_v4_submission_status"),
        UniqueConstraint(
            "actor_user_id", "authorizing_membership_id", "endpoint_action",
            "auth_policy_version", "idempotency_key", name="uq_ad_v4_submission_idempotency",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("avs"))
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False, index=True)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
    actor_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    authorizing_membership_id: Mapped[str] = mapped_column(ForeignKey("organization_memberships.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_status: Mapped[str] = mapped_column(String(32), nullable=False)
    auth_policy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    auth_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    auth_claims_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint_action: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    raw_transport_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    validator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-validator-1")
    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-c14n-1")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateSubmissionRelationship(Base):
    __tablename__ = "ad_v4_candidate_submission_relationships"
    __table_args__ = (
        CheckConstraint(
            "relation_type IN ('corrects_candidate', 'replaces_candidate')",
            name="ck_ad_v4_relationship_type",
        ),
        UniqueConstraint("submission_id", "relationship_key", name="uq_ad_v4_relationship_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("avr"))
    submission_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_submissions.id"), nullable=False, index=True)
    relationship_key: Mapped[str] = mapped_column(String(128), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    predecessor_proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_keys: Mapped[list] = mapped_column(JSON, nullable=False)
    canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    relationship_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    validator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-validator-1")
    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-c14n-1")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateProposalEvent(Base):
    __tablename__ = "ad_v4_candidate_proposal_events"
    __table_args__ = (
        CheckConstraint("event_type = 'candidate_created'", name="ck_ad_v4_event_type"),
        CheckConstraint("sequence_number = 0", name="ck_ad_v4_event_sequence"),
        UniqueConstraint("proposal_id", "sequence_number", name="uq_ad_v4_event_sequence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ave"))
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False, index=True)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
    created_by_submission_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_submissions.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    proposal_canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_binding_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    predecessor_event_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    validator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-validator-1")
    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False, default="paprnav-ad-v4-c14n-1")
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4FeatureGate(Base):
    __tablename__ = "ad_v4_feature_gates"

    gate_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    changed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(128), nullable=False, default="migration")


class ADV4CandidateAppProjection(Base):
    __tablename__ = "ad_v4_candidate_app_projections"
    __table_args__ = (
        CheckConstraint("gate = 'candidate_only'", name="ck_ad_v4_app_projection_gate"),
        UniqueConstraint("proposal_id", "materializer_version", name="uq_ad_v4_app_projection_parent"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_app_projection_identity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False, index=True)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    validator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_binding_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    materializer_version: Mapped[str] = mapped_column(String(64), nullable=False)
    applicability_subtree_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    applicability_subtree_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    projection_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    gate: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate_only")
    semantic_node_count: Mapped[int] = mapped_column(Integer, nullable=False)
    datum_count: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_link_count: Mapped[int] = mapped_column(Integer, nullable=False)
    identity_mapping_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateAppMaterializationRequest(Base):
    __tablename__ = "ad_v4_candidate_app_materialization_requests"
    __table_args__ = (
        CheckConstraint("actor_role = 'platform_admin'", name="ck_ad_v4_app_request_role"),
        CheckConstraint("actor_status = 'active'", name="ck_ad_v4_app_request_status"),
        UniqueConstraint(
            "actor_user_id", "authorizing_membership_id", "endpoint_action",
            "auth_policy_version", "idempotency_key", name="uq_ad_v4_app_request_idempotency",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    authorizing_membership_id: Mapped[str] = mapped_column(ForeignKey("organization_memberships.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_status: Mapped[str] = mapped_column(String(32), nullable=False)
    auth_policy_name: Mapped[str] = mapped_column(String(96), nullable=False)
    auth_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    auth_claims_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint_action: Mapped[str] = mapped_column(String(96), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateAppSemanticNode(Base):
    __tablename__ = "ad_v4_candidate_app_semantic_nodes"
    __table_args__ = (
        CheckConstraint("canonical_ordinal >= 0", name="ck_ad_v4_app_node_ordinal"),
        CheckConstraint("node_type IN ('product_scope','designation_scope','value_assertion','identity_mapping','designation_value','designation_range','designation_group','designation_group_member','condition','expression','applicability_rule','search_hint','search_hint_group','search_hint_model','change_dependency')", name="ck_ad_v4_app_node_type"),
        UniqueConstraint("projection_id", "node_type", "node_key", name="uq_ad_v4_app_node_key"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_app_node_identity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    parent_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    node_key: Mapped[str] = mapped_column(Text, nullable=False)
    source_pointer: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_node_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateAppDatum(Base):
    """Closed scalar/container projection used for byte-exact subtree reconstruction."""

    __tablename__ = "ad_v4_candidate_app_data"
    __table_args__ = (
        CheckConstraint("value_kind IN ('object','array','string','boolean')", name="ck_ad_v4_app_datum_kind"),
        UniqueConstraint("projection_id", "json_pointer", name="uq_ad_v4_app_datum_pointer"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    semantic_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    json_pointer: Mapped[str] = mapped_column(Text, nullable=False)
    parent_pointer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    property_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    array_ordinal: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    value_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    string_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    boolean_value: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    value_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ADV4CandidateAppEvidenceLink(Base):
    __tablename__ = "ad_v4_candidate_app_evidence_links"
    __table_args__ = (
        UniqueConstraint("semantic_node_id", "purpose", "evidence_key", name="uq_ad_v4_app_evidence_link"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    candidate_binding_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_evidence_bindings.id"), nullable=False)
    evidence_key: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    link_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ADV4CandidateAppIdentityMapping(Base):
    __tablename__ = "ad_v4_candidate_app_identity_mappings"
    __table_args__ = (
        CheckConstraint("identity_kind IN ('manufacturer','model','series','model_or_series')", name="ck_ad_v4_app_identity_kind"),
        CheckConstraint("normalization_origin IN ('candidate_payload','source_only','no_normalized_identity')", name="ck_ad_v4_app_identity_origin"),
        CheckConstraint("normalized_state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_identity_state"),
        CheckConstraint(
            "(normalization_origin='candidate_payload' AND ((normalized_state='known' AND normalized_value IS NOT NULL AND reason IS NULL AND temporal_scope IS NULL AND normalization_namespace IS NOT NULL AND normalization_version IS NOT NULL) OR (normalized_state='unknown' AND normalized_value IS NULL AND reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND temporal_scope IS NOT NULL AND normalization_namespace IS NULL AND normalization_version IS NULL) OR (normalized_state='not_applicable' AND normalized_value IS NULL AND reason IS NOT NULL AND length(reason) BETWEEN 1 AND 512 AND temporal_scope IS NOT NULL AND normalization_namespace IS NULL AND normalization_version IS NULL))) OR "
            "(normalization_origin IN ('source_only','no_normalized_identity') AND normalized_state='unknown' AND normalized_value IS NULL AND reason IN ('not_extracted','not_yet_reviewed') AND temporal_scope IN ('source_observation','directive_version') AND normalization_namespace IS NULL AND normalization_version IS NULL)",
            name="ck_ad_v4_app_identity_union",
        ),
        CheckConstraint("review_state = 'unreviewed_candidate'", name="ck_ad_v4_app_identity_review"),
        UniqueConstraint("projection_id", "identity_kind", "source_occurrence_node_id", name="uq_ad_v4_app_identity_occurrence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False, unique=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    source_occurrence_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    evidence_parent_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    identity_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalization_origin: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_state: Mapped[str] = mapped_column(String(32), nullable=False)
    normalized_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    normalization_namespace: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    normalization_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    review_state: Mapped[str] = mapped_column(String(32), nullable=False, default="unreviewed_candidate")
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class ADV4CandidateAppValueAssertion(Base):
    __tablename__ = "ad_v4_candidate_app_value_assertions"
    __table_args__ = (
        CheckConstraint("state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_value_state"),
        CheckConstraint("value_type='text'", name="ck_ad_v4_app_value_type"),
        CheckConstraint("field_code IN ('manufacturer','model_or_series','part_number','serial_number','stc_number','attribute_value','source_display_text')", name="ck_ad_v4_app_value_field"),
        CheckConstraint(
            "(state='known' AND text_value IS NOT NULL AND length(text_value) BETWEEN 1 AND 512 AND reason IS NULL AND temporal_scope IS NULL) OR "
            "(state='unknown' AND text_value IS NULL AND reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND temporal_scope IS NOT NULL) OR "
            "(state='not_applicable' AND text_value IS NULL AND reason IS NOT NULL AND length(reason) BETWEEN 1 AND 512 AND temporal_scope IS NOT NULL)",
            name="ck_ad_v4_app_value_union",
        ),
        CheckConstraint("temporal_scope IS NULL OR temporal_scope IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')", name="ck_ad_v4_app_value_temporal"),
        UniqueConstraint("parent_semantic_node_id", "field_code", name="uq_ad_v4_app_value_parent_field"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    parent_semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    field_code: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    value_type: Mapped[str] = mapped_column(String(16), nullable=False, default="text")
    text_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class ADV4CandidateAppProductScope(Base):
    __tablename__ = "ad_v4_candidate_app_product_scopes"
    __table_args__ = (
        CheckConstraint("product_role IN ('airframe','engine','propeller','appliance','installed_part','modification')", name="ck_ad_v4_app_product_role"),
        CheckConstraint("manufacturer_presence IN ('property_absent','present')", name="ck_ad_v4_app_product_manufacturer_presence"),
        CheckConstraint(
            "(manufacturer_presence='present' AND manufacturer_source_value IS NOT NULL AND manufacturer_identity_mapping_node_id IS NOT NULL) OR "
            "(manufacturer_presence='property_absent' AND manufacturer_source_value IS NULL AND manufacturer_identity_mapping_node_id IS NULL)",
            name="ck_ad_v4_app_product_manufacturer_union",
        ),
        CheckConstraint("model_presence IN ('property_absent','present') AND serial_presence IN ('property_absent','present') AND part_number_presence IN ('property_absent','present')", name="ck_ad_v4_app_product_designation_presence"),
        UniqueConstraint("projection_id", "scope_key", name="uq_ad_v4_app_product_scope_key"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False)
    product_role: Mapped[str] = mapped_column(String(32), nullable=False)
    manufacturer_presence: Mapped[str] = mapped_column(String(32), nullable=False)
    manufacturer_source_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_identity_mapping_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    model_presence: Mapped[str] = mapped_column(String(32), nullable=False)
    serial_presence: Mapped[str] = mapped_column(String(32), nullable=False)
    part_number_presence: Mapped[str] = mapped_column(String(32), nullable=False)


class ADV4CandidateAppDesignationScope(Base):
    __tablename__ = "ad_v4_candidate_app_designation_scopes"
    __table_args__ = (
        CheckConstraint("field_kind IN ('model','serial','part_number')", name="ck_ad_v4_app_designation_field"),
        CheckConstraint("scope_kind IN ('all','listed','series_expression','ranges','unknown','not_applicable')", name="ck_ad_v4_app_designation_kind"),
        CheckConstraint(
            "(scope_kind='series_expression' AND series_expression IS NOT NULL AND reason IS NULL AND temporal_scope IS NULL AND evaluation_state='unknown' AND evaluator_contract='unsupported_expression') OR "
            "(scope_kind IN ('unknown','not_applicable') AND series_expression IS NULL AND reason IS NOT NULL AND temporal_scope IS NOT NULL AND evaluation_state='unevaluated' AND evaluator_contract='none') OR "
            "(scope_kind IN ('all','listed','ranges') AND series_expression IS NULL AND reason IS NULL AND temporal_scope IS NULL AND evaluation_state='unevaluated' AND evaluator_contract='none')",
            name="ck_ad_v4_app_designation_union",
        ),
        UniqueConstraint("product_scope_node_id", "field_kind", name="uq_ad_v4_app_designation_scope_field"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    product_scope_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    field_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    series_expression: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evaluation_state: Mapped[str] = mapped_column(String(32), nullable=False)
    evaluator_contract: Mapped[str] = mapped_column(String(64), nullable=False)


class ADV4CandidateAppDesignationValue(Base):
    __tablename__ = "ad_v4_candidate_app_designation_values"
    __table_args__ = (
        CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_designation_value_ordinal"),
        UniqueConstraint("designation_scope_id", "source_value", name="uq_ad_v4_app_designation_value_source"),
        UniqueConstraint("designation_scope_id", "canonical_ordinal", name="uq_ad_v4_app_designation_value_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    designation_scope_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    source_value: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    identity_mapping_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)


class ADV4CandidateAppDesignationRange(Base):
    __tablename__ = "ad_v4_candidate_app_designation_ranges"
    __table_args__ = (
        CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_designation_range_ordinal"),
        CheckConstraint("polarity IN ('included','excluded')", name="ck_ad_v4_app_designation_range_polarity"),
        CheckConstraint("comparator_version='lexical_source_only_v1'", name="ck_ad_v4_app_designation_range_comparator"),
        UniqueConstraint("designation_scope_id", "lower_value", "upper_value", "lower_inclusive", "upper_inclusive", "polarity", name="uq_ad_v4_app_designation_range_identity"),
        UniqueConstraint("designation_scope_id", "canonical_ordinal", name="uq_ad_v4_app_designation_range_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    designation_scope_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    lower_value: Mapped[str] = mapped_column(Text, nullable=False)
    upper_value: Mapped[str] = mapped_column(Text, nullable=False)
    lower_inclusive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    upper_inclusive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    polarity: Mapped[str] = mapped_column(String(16), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    comparator_version: Mapped[str] = mapped_column(String(64), nullable=False, default="lexical_source_only_v1")


class ADV4CandidateAppCondition(Base):
    __tablename__ = "ad_v4_candidate_app_conditions"
    __table_args__ = (
        CheckConstraint("condition_type IN ('identity','identifier_range','installed_equipment','modification_or_stc','configuration_attribute','temporal_overlap','source_inclusion','source_exclusion','reviewed_manual_predicate')", name="ck_ad_v4_app_condition_type"),
        CheckConstraint("operator IN ('identity_equals','identity_in','identifier_in_range','is_installed','is_not_installed','equals','overlaps','includes','excludes','requires_review')", name="ck_ad_v4_app_condition_operator"),
        CheckConstraint("comparator_presence IN ('property_absent','present') AND subject_product_role_presence IN ('property_absent','present') AND subject_attribute_key_presence IN ('property_absent','present') AND designation_group_presence IN ('property_absent','present')", name="ck_ad_v4_app_condition_presence"),
        CheckConstraint("(comparator_presence='present')=(comparator_version IS NOT NULL)", name="ck_ad_v4_app_condition_comparator"),
        CheckConstraint("(subject_product_role_presence='present')=(subject_product_role IS NOT NULL)", name="ck_ad_v4_app_condition_role_presence"),
        CheckConstraint("subject_product_role IS NULL OR subject_product_role IN ('airframe','engine','propeller','appliance','installed_part','modification')", name="ck_ad_v4_app_condition_role"),
        CheckConstraint("(subject_attribute_key_presence='present')=(subject_attribute_key IS NOT NULL)", name="ck_ad_v4_app_condition_attribute"),
        CheckConstraint("(designation_group_presence='present')=(designation_group_node_id IS NOT NULL)", name="ck_ad_v4_app_condition_group"),
        CheckConstraint("evaluation_state='unevaluated' AND evaluator_contract='none'", name="ck_ad_v4_app_condition_evaluation"),
        UniqueConstraint("projection_id", "condition_key", name="uq_ad_v4_app_condition_key"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    condition_key: Mapped[str] = mapped_column(String(128), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(64), nullable=False)
    temporal_basis: Mapped[str] = mapped_column(String(64), nullable=False)
    comparator_presence: Mapped[str] = mapped_column(String(32), nullable=False)
    comparator_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject_product_role_presence: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_product_role: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    subject_attribute_key_presence: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_attribute_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    designation_group_presence: Mapped[str] = mapped_column(String(32), nullable=False)
    designation_group_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    evaluation_state: Mapped[str] = mapped_column(String(32), nullable=False, default="unevaluated")
    evaluator_contract: Mapped[str] = mapped_column(String(64), nullable=False, default="none")


class ADV4CandidateAppDesignationGroup(Base):
    __tablename__ = "ad_v4_candidate_app_designation_groups"
    __table_args__ = (
        CheckConstraint("association IN ('all_members','any_member','source_group','unknown')", name="ck_ad_v4_app_group_association"),
        CheckConstraint("(association='unknown' AND reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND temporal_scope IS NOT NULL) OR (association<>'unknown' AND reason IS NULL AND temporal_scope IS NULL)", name="ck_ad_v4_app_group_unknown"),
        CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_group_ordinal"),
        UniqueConstraint("condition_node_id", "group_key", name="uq_ad_v4_app_group_key"),
        UniqueConstraint("condition_node_id", "canonical_ordinal", name="uq_ad_v4_app_group_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    condition_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    group_key: Mapped[str] = mapped_column(String(128), nullable=False)
    association: Mapped[str] = mapped_column(String(32), nullable=False)
    source_display_assertion_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ADV4CandidateAppDesignationGroupMember(Base):
    __tablename__ = "ad_v4_candidate_app_designation_group_members"
    __table_args__ = (
        CheckConstraint("designation_kind IN ('model','series_expression')", name="ck_ad_v4_app_group_member_kind"),
        CheckConstraint("(designation_kind='model' AND source_designation IS NOT NULL AND expression_text IS NULL AND evaluation_state IS NULL AND evaluation_reason IS NULL) OR (designation_kind='series_expression' AND source_designation IS NULL AND expression_text IS NOT NULL AND evaluation_state='unevaluated' AND evaluation_reason='unsupported_expression')", name="ck_ad_v4_app_group_member_union"),
        CheckConstraint("manufacturer_state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_group_member_manufacturer_state"),
        CheckConstraint("(manufacturer_state='known' AND manufacturer_value IS NOT NULL AND manufacturer_reason IS NULL AND manufacturer_temporal_scope IS NULL) OR (manufacturer_state='unknown' AND manufacturer_value IS NULL AND manufacturer_reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND manufacturer_temporal_scope IS NOT NULL) OR (manufacturer_state='not_applicable' AND manufacturer_value IS NULL AND manufacturer_reason IS NOT NULL AND length(manufacturer_reason) BETWEEN 1 AND 512 AND manufacturer_temporal_scope IS NOT NULL)", name="ck_ad_v4_app_group_member_manufacturer_union"),
        CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_group_member_ordinal"),
        UniqueConstraint("group_node_id", "member_key", name="uq_ad_v4_app_group_member_key"),
        UniqueConstraint("group_node_id", "canonical_ordinal", name="uq_ad_v4_app_group_member_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    group_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    member_key: Mapped[str] = mapped_column(String(128), nullable=False)
    designation_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_designation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expression_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_assertion_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    manufacturer_state: Mapped[str] = mapped_column(String(32), nullable=False)
    manufacturer_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evaluation_state: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    evaluation_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    designation_identity_mapping_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)


class ADV4CandidateAppRule(Base):
    __tablename__ = "ad_v4_candidate_app_rules"
    __table_args__ = (
        CheckConstraint("condition_presence IN ('property_absent','present')", name="ck_ad_v4_app_rule_condition_presence"),
        CheckConstraint("(condition_presence='present')=(condition_expression_node_id IS NOT NULL)", name="ck_ad_v4_app_rule_condition_union"),
        CheckConstraint("evaluator_contract='none'", name="ck_ad_v4_app_rule_evaluator"),
        UniqueConstraint("projection_id", "rule_key", name="uq_ad_v4_app_rule_key"),
        ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["scope_expression_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["condition_expression_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    scope_expression_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    condition_presence: Mapped[str] = mapped_column(String(32), nullable=False)
    condition_expression_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    evaluator_contract: Mapped[str] = mapped_column(String(64), nullable=False, default="none")


class ADV4CandidateAppExpression(Base):
    __tablename__ = "ad_v4_candidate_app_expressions"
    __table_args__ = (
        CheckConstraint("expression_context IN ('scope','condition')", name="ck_ad_v4_app_expression_context"),
        CheckConstraint("expression_node_type IN ('scope_ref','predicate_ref','rule_ref','not','all','any')", name="ck_ad_v4_app_expression_type"),
        CheckConstraint("result_domain='true_false_unknown' AND evaluator_contract='none'", name="ck_ad_v4_app_expression_evaluator"),
        CheckConstraint(
            "(expression_node_type='scope_ref' AND scope_node_id IS NOT NULL AND condition_node_id IS NULL AND referenced_rule_node_id IS NULL) OR "
            "(expression_node_type='predicate_ref' AND scope_node_id IS NULL AND condition_node_id IS NOT NULL AND referenced_rule_node_id IS NULL) OR "
            "(expression_node_type='rule_ref' AND scope_node_id IS NULL AND condition_node_id IS NULL AND referenced_rule_node_id IS NOT NULL) OR "
            "(expression_node_type IN ('not','all','any') AND scope_node_id IS NULL AND condition_node_id IS NULL AND referenced_rule_node_id IS NULL)",
            name="ck_ad_v4_app_expression_reference_union",
        ),
        UniqueConstraint("owning_rule_node_id", "expression_context", "expression_path", name="uq_ad_v4_app_expression_path"),
        ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["owning_rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["scope_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["condition_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["referenced_rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    owning_rule_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    expression_context: Mapped[str] = mapped_column(String(16), nullable=False)
    expression_path: Mapped[str] = mapped_column(Text, nullable=False)
    expression_node_type: Mapped[str] = mapped_column(String(32), nullable=False)
    result_domain: Mapped[str] = mapped_column(String(32), nullable=False, default="true_false_unknown")
    evaluator_contract: Mapped[str] = mapped_column(String(64), nullable=False, default="none")
    scope_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    condition_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    referenced_rule_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)


class ADV4CandidateAppExpressionEdge(Base):
    __tablename__ = "ad_v4_candidate_app_expression_edges"
    __table_args__ = (
        CheckConstraint("expression_context IN ('scope','condition')", name="ck_ad_v4_app_expression_edge_context"),
        CheckConstraint("sequence>=0", name="ck_ad_v4_app_expression_edge_sequence"),
        UniqueConstraint("parent_expression_id", "child_expression_id", name="uq_ad_v4_app_expression_edge_pair"),
        UniqueConstraint("child_expression_id", name="uq_ad_v4_app_expression_child"),
        ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"]),
        ForeignKeyConstraint(["owning_rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["parent_expression_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["child_expression_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
    )

    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    owning_rule_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    expression_context: Mapped[str] = mapped_column(String(16), nullable=False)
    parent_expression_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    child_expression_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)


class ADV4CandidateAppRuleExclusion(Base):
    __tablename__ = "ad_v4_candidate_app_rule_exclusions"
    __table_args__ = (
        CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_rule_exclusion_ordinal"),
        UniqueConstraint("rule_node_id", "excluded_rule_node_id", name="uq_ad_v4_app_rule_exclusion_pair"),
        ForeignKeyConstraint(["projection_id", "proposal_id"], ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"]),
        ForeignKeyConstraint(["rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["excluded_rule_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
    )

    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    rule_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    excluded_rule_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, primary_key=True)


class ADV4CandidateAppSearchHint(Base):
    __tablename__ = "ad_v4_candidate_app_search_hints"
    __table_args__ = (
        CheckConstraint("product_role IN ('airframe','engine','propeller','appliance','installed_part','modification')", name="ck_ad_v4_app_search_hint_role"),
        CheckConstraint("controlling=false AND exhaustive=false", name="ck_ad_v4_app_search_hint_noncontrolling"),
        UniqueConstraint("projection_id", "hint_key", name="uq_ad_v4_app_search_hint_key"),
        ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["source_display_assertion_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    hint_key: Mapped[str] = mapped_column(String(128), nullable=False)
    product_role: Mapped[str] = mapped_column(String(32), nullable=False)
    source_display_assertion_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    controlling: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    exhaustive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ADV4CandidateAppSearchHintGroup(Base):
    __tablename__ = "ad_v4_candidate_app_search_hint_groups"
    __table_args__ = (
        CheckConstraint("association IN ('paired','source_group','unknown')", name="ck_ad_v4_app_search_hint_group_association"),
        CheckConstraint("(association='unknown' AND reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND temporal_scope IS NOT NULL) OR (association<>'unknown' AND reason IS NULL AND temporal_scope IS NULL)", name="ck_ad_v4_app_search_hint_group_unknown"),
        CheckConstraint("temporal_scope IS NULL OR temporal_scope IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')", name="ck_ad_v4_app_search_hint_group_temporal"),
        CheckConstraint("manufacturer_state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_search_hint_group_manufacturer_state"),
        CheckConstraint("(manufacturer_state='known' AND manufacturer_value IS NOT NULL AND manufacturer_reason IS NULL AND manufacturer_temporal_scope IS NULL) OR (manufacturer_state='unknown' AND manufacturer_value IS NULL AND manufacturer_reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND manufacturer_temporal_scope IS NOT NULL) OR (manufacturer_state='not_applicable' AND manufacturer_value IS NULL AND manufacturer_reason IS NOT NULL AND length(manufacturer_reason) BETWEEN 1 AND 512 AND manufacturer_temporal_scope IS NOT NULL)", name="ck_ad_v4_app_search_hint_group_manufacturer_union"),
        CheckConstraint("manufacturer_temporal_scope IS NULL OR manufacturer_temporal_scope IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')", name="ck_ad_v4_app_search_hint_group_manufacturer_temporal"),
        CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_search_hint_group_ordinal"),
        UniqueConstraint("hint_node_id", "group_key", name="uq_ad_v4_app_search_hint_group_key"),
        UniqueConstraint("hint_node_id", "canonical_ordinal", name="uq_ad_v4_app_search_hint_group_ordinal"),
        ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["hint_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["manufacturer_assertion_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    hint_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    group_key: Mapped[str] = mapped_column(String(128), nullable=False)
    manufacturer_assertion_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    manufacturer_state: Mapped[str] = mapped_column(String(32), nullable=False)
    manufacturer_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    association: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateAppSearchHintMember(Base):
    __tablename__ = "ad_v4_candidate_app_search_hint_members"
    __table_args__ = (
        CheckConstraint("designation_kind IN ('model','series_expression')", name="ck_ad_v4_app_search_hint_member_kind"),
        CheckConstraint("(designation_kind='model' AND source_designation IS NOT NULL AND expression_text IS NULL AND evaluation_state IS NULL AND evaluation_reason IS NULL) OR (designation_kind='series_expression' AND source_designation IS NULL AND expression_text IS NOT NULL AND evaluation_state='unevaluated' AND evaluation_reason='unsupported_expression')", name="ck_ad_v4_app_search_hint_member_union"),
        CheckConstraint("(source_designation IS NULL OR length(source_designation) BETWEEN 1 AND 512) AND (expression_text IS NULL OR length(expression_text) BETWEEN 1 AND 512)", name="ck_ad_v4_app_search_hint_member_text_length"),
        CheckConstraint("manufacturer_state IN ('known','unknown','not_applicable')", name="ck_ad_v4_app_search_hint_member_manufacturer_state"),
        CheckConstraint("(manufacturer_state='known' AND manufacturer_value IS NOT NULL AND manufacturer_reason IS NULL AND manufacturer_temporal_scope IS NULL) OR (manufacturer_state='unknown' AND manufacturer_value IS NULL AND manufacturer_reason IN ('not_observed','unavailable','not_obtained','not_extracted','not_yet_reviewed','not_yet_verified','conflicting_evidence','source_ambiguous','unsupported_expression') AND manufacturer_temporal_scope IS NOT NULL) OR (manufacturer_state='not_applicable' AND manufacturer_value IS NULL AND manufacturer_reason IS NOT NULL AND length(manufacturer_reason) BETWEEN 1 AND 512 AND manufacturer_temporal_scope IS NOT NULL)", name="ck_ad_v4_app_search_hint_member_manufacturer_union"),
        CheckConstraint("manufacturer_temporal_scope IS NULL OR manufacturer_temporal_scope IN ('directive_version','publication_version','at_applicability_evaluation','at_compliance_evaluation','source_observation')", name="ck_ad_v4_app_search_hint_member_manufacturer_temporal"),
        CheckConstraint("canonical_ordinal>=0", name="ck_ad_v4_app_search_hint_member_ordinal"),
        UniqueConstraint("group_node_id", "member_key", name="uq_ad_v4_app_search_hint_member_key"),
        UniqueConstraint("group_node_id", "canonical_ordinal", name="uq_ad_v4_app_search_hint_member_ordinal"),
        ForeignKeyConstraint(["semantic_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["group_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["manufacturer_assertion_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
        ForeignKeyConstraint(["designation_identity_mapping_node_id", "projection_id", "proposal_id"], ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"]),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    group_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    member_key: Mapped[str] = mapped_column(String(128), nullable=False)
    designation_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_designation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expression_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_assertion_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    manufacturer_state: Mapped[str] = mapped_column(String(32), nullable=False)
    manufacturer_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manufacturer_temporal_scope: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evaluation_state: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    evaluation_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    designation_identity_mapping_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)


class ADV4CandidateCorrection(Base):
    __tablename__ = "ad_v4_candidate_corrections"
    __table_args__ = (
        CheckConstraint("canonical_ordinal >= 0", name="ck_ad_v4_correction_ordinal_nonnegative"),
        UniqueConstraint("proposal_id", "correction_key", name="uq_ad_v4_correction_key"),
        UniqueConstraint("proposal_id", "canonical_ordinal", name="uq_ad_v4_correction_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False, index=True)
    correction_key: Mapped[str] = mapped_column(String(128), nullable=False)
    correction_type: Mapped[str] = mapped_column(String(64), nullable=False)
    original_document_ref_key: Mapped[str] = mapped_column(String(128), nullable=False)
    correcting_document_ref_key: Mapped[str] = mapped_column(String(128), nullable=False)
    original_document_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    correcting_document_identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    foundation_version: Mapped[str] = mapped_column(String(64), nullable=False)
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_ref_count: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateCorrectionRef(Base):
    __tablename__ = "ad_v4_candidate_correction_refs"
    __table_args__ = (
        CheckConstraint("canonical_ordinal >= 0", name="ck_ad_v4_correction_ref_ordinal_nonnegative"),
        UniqueConstraint("correction_id", "namespace", "semantic_key", name="uq_ad_v4_correction_ref_key"),
        UniqueConstraint("correction_id", "canonical_ordinal", name="uq_ad_v4_correction_ref_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    correction_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_corrections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    namespace: Mapped[str] = mapped_column(String(64), nullable=False)
    semantic_key: Mapped[str] = mapped_column(String(128), nullable=False)
    owner_slice: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ADV4CandidateCorrectionSemanticBinding(Base):
    __tablename__ = "ad_v4_candidate_correction_semantic_bindings"
    __table_args__ = (
        CheckConstraint(
            "(binding_slice='slice_3a' AND projection_id IS NOT NULL AND semantic_node_id IS NOT NULL "
            "AND obligation_projection_id IS NULL AND obligation_semantic_node_id IS NULL) OR "
            "(binding_slice='slice_3b' AND projection_id IS NULL AND semantic_node_id IS NULL "
            "AND obligation_projection_id IS NOT NULL AND obligation_semantic_node_id IS NOT NULL)",
            name="ck_ad_v4_correction_binding_owner_slice",
        ),
        ForeignKeyConstraint(
            ["obligation_projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            name="fk_ad_v4_correction_binding_obligation_projection",
        ),
        ForeignKeyConstraint(
            ["obligation_semantic_node_id", "obligation_projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_semantic_nodes.id", "ad_v4_candidate_obligation_semantic_nodes.projection_id", "ad_v4_candidate_obligation_semantic_nodes.proposal_id"],
            name="fk_ad_v4_correction_binding_obligation_node",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    correction_ref_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_correction_refs.id"), nullable=False, unique=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=True)
    semantic_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    obligation_projection_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    obligation_semantic_node_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    binding_slice: Mapped[str] = mapped_column(String(32), nullable=False)
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    binding_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class ADV4CandidateCorrectionEvidenceLink(Base):
    __tablename__ = "ad_v4_candidate_correction_evidence_links"
    __table_args__ = (
        CheckConstraint("canonical_ordinal >= 0", name="ck_ad_v4_correction_evidence_ordinal_nonnegative"),
        UniqueConstraint("correction_id", "evidence_key", name="uq_ad_v4_correction_evidence"),
        UniqueConstraint("correction_id", "canonical_ordinal", name="uq_ad_v4_correction_evidence_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    correction_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_corrections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    candidate_binding_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_evidence_bindings.id"), nullable=False)
    evidence_key: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    link_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ADV4CandidateAppChangeDependency(Base):
    __tablename__ = "ad_v4_candidate_app_change_dependencies"
    __table_args__ = (
        CheckConstraint(
            "dependency_kind IN ('outgoing_supersedes','outgoing_partially_supersedes','incoming_supersession_signal')",
            name="ck_ad_v4_app_dependency_kind",
        ),
        UniqueConstraint("id", "projection_id", name="uq_ad_v4_app_dependency_parent_identity"),
        UniqueConstraint("projection_id", "dependency_key", name="uq_ad_v4_app_dependency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=False)
    dependency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    dependency_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    predecessor_ad_number: Mapped[str] = mapped_column(String(64), nullable=False)
    successor_ad_number: Mapped[str] = mapped_column(String(64), nullable=False)
    resolution_state: Mapped[str] = mapped_column(String(32), nullable=False)
    unresolved_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_projection_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=True)
    source_dependency_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_change_dependencies.id"), nullable=True)
    dependency_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class ADV4CandidateAppProjectionEvent(Base):
    __tablename__ = "ad_v4_candidate_app_projection_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["causing_dependency_id", "projection_id"],
            ["ad_v4_candidate_app_change_dependencies.id", "ad_v4_candidate_app_change_dependencies.projection_id"],
            name="fk_ad_v4_app_event_same_projection_dependency",
        ),
        UniqueConstraint("projection_id", "sequence_number", name="uq_ad_v4_app_event_sequence"),
        UniqueConstraint("projection_id", "event_hash", name="uq_ad_v4_app_event_hash"),
        Index(
            "uq_ad_v4_app_event_dependency_cause", "projection_id", "event_type", "causing_dependency_id",
            unique=True, postgresql_where=text("causing_dependency_id IS NOT NULL"),
        ),
        Index(
            "uq_ad_v4_app_event_relationship_cause", "projection_id", "event_type", "causing_relationship_id",
            unique=True, postgresql_where=text("causing_relationship_id IS NOT NULL"),
        ),
        Index(
            "uq_ad_v4_app_event_lifecycle_cause", "projection_id", "event_type", "causing_lifecycle_event_id",
            unique=True, postgresql_where=text("causing_lifecycle_event_id IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    causing_request_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_materialization_requests.id"), nullable=True)
    causing_relationship_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_submission_relationships.id"), nullable=True)
    causing_lifecycle_event_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_evidence_fragment_lifecycle_events.id"), nullable=True)
    causing_dependency_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_change_dependencies.id"), nullable=True)
    predecessor_event_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateObligationProjection(Base):
    __tablename__ = "ad_v4_candidate_obligation_projections"
    __table_args__ = (
        CheckConstraint("gate='candidate_only'", name="ck_ad_v4_obligation_projection_gate"),
        CheckConstraint(
            "validator_version='paprnav-ad-v4-validator-2' AND canonicalization_version='paprnav-ad-v4-c14n-2'",
            name="ck_ad_v4_obligation_projection_v2",
        ),
        CheckConstraint("materializer_version='paprnav-ad-v4-obligation-materializer-1'", name="ck_ad_v4_obligation_materializer"),
        CheckConstraint("mapping_version='paprnav-ad-v4-obligation-mapping-1'", name="ck_ad_v4_obligation_mapping_version"),
        UniqueConstraint("id", "proposal_id", name="uq_ad_v4_obligation_projection_parent_identity"),
        UniqueConstraint("proposal_id", "materializer_version", name="uq_ad_v4_obligation_projection_parent"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_projection_identity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False, index=True)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
    validator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    canonicalization_version: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_binding_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    app_projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False)
    app_projection_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    app_materializer_version: Mapped[str] = mapped_column(String(64), nullable=False)
    materializer_version: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_version: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    obligation_subtree_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    obligation_subtree_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    projection_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    gate: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate_only")
    semantic_node_count: Mapped[int] = mapped_column(Integer, nullable=False)
    datum_count: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_link_count: Mapped[int] = mapped_column(Integer, nullable=False)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False)
    value_assertion_count: Mapped[int] = mapped_column(Integer, nullable=False)
    requirement_count: Mapped[int] = mapped_column(Integer, nullable=False)
    action_count: Mapped[int] = mapped_column(Integer, nullable=False)
    action_step_count: Mapped[int] = mapped_column(Integer, nullable=False)
    action_document_ref_count: Mapped[int] = mapped_column(Integer, nullable=False)
    branch_count: Mapped[int] = mapped_column(Integer, nullable=False)
    expression_count: Mapped[int] = mapped_column(Integer, nullable=False)
    expression_edge_count: Mapped[int] = mapped_column(Integer, nullable=False)
    requirement_dependency_count: Mapped[int] = mapped_column(Integer, nullable=False)
    timing_group_count: Mapped[int] = mapped_column(Integer, nullable=False)
    timing_term_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recurrence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    terminating_effect_count: Mapped[int] = mapped_column(Integer, nullable=False)
    termination_edge_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recurrence_group_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recurrence_group_member_count: Mapped[int] = mapped_column(Integer, nullable=False)
    amoc_provision_count: Mapped[int] = mapped_column(Integer, nullable=False)
    correction_binding_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateObligationMaterializationRequest(Base):
    __tablename__ = "ad_v4_candidate_obligation_materialization_requests"
    __table_args__ = (
        CheckConstraint("actor_role='platform_admin' AND actor_status='active'", name="ck_ad_v4_obligation_request_actor"),
        CheckConstraint("endpoint_action='materialize_ad_v4_obligations'", name="ck_ad_v4_obligation_request_action"),
        UniqueConstraint(
            "actor_user_id", "authorizing_membership_id", "endpoint_action",
            "auth_policy_version", "idempotency_key",
            name="uq_ad_v4_obligation_request_idempotency",
        ),
        ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            name="fk_ad_v4_obligation_request_projection",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    projection_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(String(36), nullable=False)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False)
    app_projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    authorizing_membership_id: Mapped[str] = mapped_column(ForeignKey("organization_memberships.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_status: Mapped[str] = mapped_column(String(32), nullable=False)
    auth_policy_name: Mapped[str] = mapped_column(String(96), nullable=False)
    auth_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    auth_claims_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint_action: Mapped[str] = mapped_column(String(96), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateObligationSemanticNode(Base):
    __tablename__ = "ad_v4_candidate_obligation_semantic_nodes"
    __table_args__ = (
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 2147483647", name="ck_ad_v4_obligation_node_ordinal"),
        CheckConstraint(
            "node_type IN ('incorporated_document','value_assertion','requirement','action','action_step','branch','expression','timing_group','timing_term','recurrence','terminating_effect','recurrence_group','amoc_provision')",
            name="ck_ad_v4_obligation_node_type",
        ),
        UniqueConstraint("id", "projection_id", "proposal_id", name="uq_ad_v4_obligation_node_parent_identity"),
        UniqueConstraint("projection_id", "node_type", "node_key", name="uq_ad_v4_obligation_node_key"),
        UniqueConstraint("projection_id", "source_pointer", name="uq_ad_v4_obligation_node_pointer"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_node_identity"),
        ForeignKeyConstraint(
            ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            name="fk_ad_v4_obligation_node_projection",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(String(36), nullable=False)
    parent_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=True)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    node_key: Mapped[str] = mapped_column(Text, nullable=False)
    source_pointer: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_node_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ADV4CandidateObligationDatum(Base):
    __tablename__ = "ad_v4_candidate_obligation_data"
    __table_args__ = (
        CheckConstraint("value_kind IN ('object','array','string','boolean')", name="ck_ad_v4_obligation_datum_kind"),
        CheckConstraint(
            "(value_kind='string' AND string_value IS NOT NULL AND boolean_value IS NULL) OR "
            "(value_kind='boolean' AND string_value IS NULL AND boolean_value IS NOT NULL) OR "
            "(value_kind IN ('object','array') AND string_value IS NULL AND boolean_value IS NULL)",
            name="ck_ad_v4_obligation_datum_union",
        ),
        UniqueConstraint("projection_id", "json_pointer", name="uq_ad_v4_obligation_datum_pointer"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_datum_identity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    semantic_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=True)
    json_pointer: Mapped[str] = mapped_column(Text, nullable=False)
    parent_pointer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    property_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    array_ordinal: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    value_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    string_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    boolean_value: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    value_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ADV4CandidateObligationEvidenceLink(Base):
    __tablename__ = "ad_v4_candidate_obligation_evidence_links"
    __table_args__ = (
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 2147483647", name="ck_ad_v4_obligation_evidence_ordinal"),
        CheckConstraint(
            "purpose IN ('incorporated_document_clause','document_identity','document_retention','requirement_clause','action_clause','branch_clause','timing_clause','timing_term_clause','recurrence_clause','termination_clause','amoc_authority_clause')",
            name="ck_ad_v4_obligation_evidence_purpose",
        ),
        UniqueConstraint("semantic_node_id", "purpose", "evidence_key", name="uq_ad_v4_obligation_evidence_link"),
        UniqueConstraint("semantic_node_id", "purpose", "canonical_ordinal", name="uq_ad_v4_obligation_evidence_ordinal"),
        UniqueConstraint("link_hash", name="uq_ad_v4_obligation_evidence_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    candidate_binding_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_evidence_bindings.id"), nullable=False)
    evidence_key: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    link_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ADV4CandidateObligationDocument(Base):
    __tablename__ = "ad_v4_candidate_obligation_documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('service_bulletin','service_letter','service_instruction','maintenance_manual','approved_data','other_reviewed')",
            name="ck_ad_v4_obligation_document_type",
        ),
        UniqueConstraint("projection_id", "document_ref_key", name="uq_ad_v4_obligation_document_key"),
        UniqueConstraint("projection_id", "canonical_ordinal", name="uq_ad_v4_obligation_document_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    document_ref_key: Mapped[str] = mapped_column(String(128), nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    document_number_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    revision_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    retention_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)


class ADV4CandidateObligationValueAssertion(Base):
    __tablename__ = "ad_v4_candidate_obligation_value_assertions"
    __table_args__ = (
        CheckConstraint("field_code IN ('document_number','revision','retention','approving_authority')", name="ck_ad_v4_obligation_assertion_field"),
        CheckConstraint("state IN ('known','unknown','not_applicable')", name="ck_ad_v4_obligation_assertion_state"),
        CheckConstraint(
            "(state='known' AND value IS NOT NULL AND reason IS NULL AND temporal_kind IS NULL) OR "
            "(state IN ('unknown','not_applicable') AND value IS NULL AND reason IS NOT NULL AND temporal_kind IS NOT NULL)",
            name="ck_ad_v4_obligation_assertion_union",
        ),
        CheckConstraint("field_code<>'retention' OR state='unknown'", name="ck_ad_v4_obligation_retention_unknown"),
        UniqueConstraint("projection_id", "semantic_node_id", name="uq_ad_v4_obligation_assertion_node"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    field_code: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temporal_kind: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class ADV4CandidateObligationRequirement(Base):
    __tablename__ = "ad_v4_candidate_obligation_requirements"
    __table_args__ = (
        CheckConstraint("sequence_value BETWEEN 1 AND 2000", name="ck_ad_v4_obligation_requirement_sequence"),
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_requirement_ordinal"),
        CheckConstraint("requirement_type IN ('inspection','replacement','modification','software_update','limitation','reporting','installation_prohibition','corrective_action','other_reviewed')", name="ck_ad_v4_obligation_requirement_type"),
        CheckConstraint("recurrence_group_present=(recurrence_group_key IS NOT NULL)", name="ck_ad_v4_obligation_requirement_group_presence"),
        UniqueConstraint("projection_id", "requirement_key", name="uq_ad_v4_obligation_requirement_key"),
        UniqueConstraint("projection_id", "sequence_value", name="uq_ad_v4_obligation_requirement_sequence"),
        UniqueConstraint("projection_id", "canonical_ordinal", name="uq_ad_v4_obligation_requirement_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    requirement_key: Mapped[str] = mapped_column(String(128), nullable=False)
    sequence_text: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_value: Mapped[int] = mapped_column(Integer, nullable=False)
    requirement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    recurrence_group_present: Mapped[bool] = mapped_column(Boolean, nullable=False)
    recurrence_group_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    action_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    activation_root_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    branch_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    initial_timing_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    recurrence_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    terminating_effect_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)


class ADV4CandidateObligationAction(Base):
    __tablename__ = "ad_v4_candidate_obligation_actions"
    __table_args__ = (
        CheckConstraint("action_type IN ('inspect','replace','repair','modify','software_update','revise_limitation','report','installation_prohibition','remove','rework','other_reviewed')", name="ck_ad_v4_obligation_action_type"),
        CheckConstraint("step_count BETWEEN 0 AND 2000 AND document_ref_count BETWEEN 0 AND 2000", name="ck_ad_v4_obligation_action_counts"),
        CheckConstraint("ordered_steps_present OR step_count=0", name="ck_ad_v4_obligation_action_step_presence"),
        UniqueConstraint("projection_id", "requirement_node_id", name="uq_ad_v4_obligation_action_requirement"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ordered_steps_present: Mapped[bool] = mapped_column(Boolean, nullable=False)
    step_count: Mapped[int] = mapped_column(Integer, nullable=False)
    document_ref_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationActionStep(Base):
    __tablename__ = "ad_v4_candidate_obligation_action_steps"
    __table_args__ = (
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_action_step_ordinal"),
        UniqueConstraint("action_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_action_step_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    action_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    step_text: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationActionDocumentRef(Base):
    __tablename__ = "ad_v4_candidate_obligation_action_document_refs"
    __table_args__ = (
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_action_document_ordinal"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_action_document_identity"),
        UniqueConstraint("action_node_id", "document_node_id", name="uq_ad_v4_obligation_action_document_target"),
        UniqueConstraint("action_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_action_document_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    action_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    document_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    document_ref_key: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationBranch(Base):
    __tablename__ = "ad_v4_candidate_obligation_branches"
    __table_args__ = (
        CheckConstraint("kind IN ('required','conditional','exception','alternative_member')", name="ck_ad_v4_obligation_branch_kind"),
        CheckConstraint(
            "(kind='required' AND alternative_group_key IS NULL AND exclusive IS NULL AND condition_root_node_id IS NULL) OR "
            "(kind IN ('conditional','exception') AND alternative_group_key IS NULL AND exclusive IS NULL AND condition_root_node_id IS NOT NULL) OR "
            "(kind='alternative_member' AND alternative_group_key IS NOT NULL AND exclusive IS NOT NULL AND condition_root_node_id IS NULL)",
            name="ck_ad_v4_obligation_branch_union",
        ),
        UniqueConstraint("projection_id", "requirement_node_id", name="uq_ad_v4_obligation_branch_requirement"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    alternative_group_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    exclusive: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    condition_root_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=True)


class ADV4CandidateObligationExpression(Base):
    __tablename__ = "ad_v4_candidate_obligation_expressions"
    __table_args__ = (
        CheckConstraint("context IN ('activation','branch_condition','recurrence_condition')", name="ck_ad_v4_obligation_expression_context"),
        CheckConstraint("node_type IN ('scope_ref','predicate_ref','rule_ref','requirement_state_ref','not','all','any')", name="ck_ad_v4_obligation_expression_type"),
        CheckConstraint(
            "(node_type IN ('scope_ref','predicate_ref','rule_ref') AND required_state IS NULL AND app_target_projection_id IS NOT NULL AND app_target_node_id IS NOT NULL AND requirement_target_node_id IS NULL) OR "
            "(node_type='requirement_state_ref' AND required_state IS NOT NULL AND app_target_projection_id IS NULL AND app_target_node_id IS NULL AND requirement_target_node_id IS NOT NULL) OR "
            "(node_type IN ('not','all','any') AND required_state IS NULL AND app_target_projection_id IS NULL AND app_target_node_id IS NULL AND requirement_target_node_id IS NULL)",
            name="ck_ad_v4_obligation_expression_union",
        ),
        UniqueConstraint("projection_id", "requirement_node_id", "context", "expression_path", name="uq_ad_v4_obligation_expression_path"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    context: Mapped[str] = mapped_column(String(32), nullable=False)
    expression_path: Mapped[str] = mapped_column(Text, nullable=False)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False)
    required_state: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    app_target_projection_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=True)
    app_target_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_app_semantic_nodes.id"), nullable=True)
    requirement_target_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=True)


class ADV4CandidateObligationExpressionEdge(Base):
    __tablename__ = "ad_v4_candidate_obligation_expression_edges"
    __table_args__ = (
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_expression_edge_ordinal"),
        CheckConstraint("context IN ('activation','branch_condition','recurrence_condition')", name="ck_ad_v4_obligation_expression_edge_context"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_expression_edge_identity"),
        UniqueConstraint("parent_expression_id", "child_expression_id", name="uq_ad_v4_obligation_expression_edge_target"),
        UniqueConstraint("parent_expression_id", "canonical_ordinal", name="uq_ad_v4_obligation_expression_edge_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    context: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_expression_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    child_expression_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationRequirementDependency(Base):
    __tablename__ = "ad_v4_candidate_obligation_requirement_dependencies"
    __table_args__ = (
        CheckConstraint("dependency_kind='prerequisite'", name="ck_ad_v4_obligation_requirement_dependency_kind"),
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_requirement_dependency_ordinal"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_requirement_dependency_identity"),
        UniqueConstraint("requirement_node_id", "prerequisite_requirement_node_id", name="uq_ad_v4_obligation_requirement_dependency_target"),
        UniqueConstraint("requirement_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_requirement_dependency_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    prerequisite_requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    prerequisite_requirement_key: Mapped[str] = mapped_column(String(128), nullable=False)
    dependency_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="prerequisite")
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationTimingGroup(Base):
    __tablename__ = "ad_v4_candidate_obligation_timing_groups"
    __table_args__ = (
        CheckConstraint("owner_kind IN ('requirement_initial','requirement_recurrence','recurrence_group_initial','recurrence_group_recurring')", name="ck_ad_v4_obligation_timing_owner_kind"),
        CheckConstraint("state IN ('known','unknown','not_applicable')", name="ck_ad_v4_obligation_timing_state"),
        CheckConstraint(
            "(state='known' AND logic IS NOT NULL AND logic IN ('all','whichever_first','whichever_later') AND reason IS NULL AND temporal_kind IS NULL AND term_count>=1) OR "
            "(state IN ('unknown','not_applicable') AND logic IS NULL AND reason IS NOT NULL AND temporal_kind IS NOT NULL AND term_count=0)",
            name="ck_ad_v4_obligation_timing_union",
        ),
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999 AND term_count BETWEEN 0 AND 2000", name="ck_ad_v4_obligation_timing_counts"),
        UniqueConstraint("projection_id", "owner_node_id", "owner_kind", name="uq_ad_v4_obligation_timing_owner"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    owner_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    logic: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temporal_kind: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    term_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationTimingTerm(Base):
    __tablename__ = "ad_v4_candidate_obligation_timing_terms"
    __table_args__ = (
        CheckConstraint("metric IN ('calendar','aircraft_time','component_time','cycles','other_reviewed')", name="ck_ad_v4_obligation_timing_metric"),
        CheckConstraint("unit IN ('days','months','years','hours','cycles','source_defined')", name="ck_ad_v4_obligation_timing_unit"),
        CheckConstraint("comparator IN ('within','before','at_or_before','after','at_or_after')", name="ck_ad_v4_obligation_timing_comparator"),
        CheckConstraint("anchor IN ('effective_date','last_compliance','installation','manufacture','source_defined')", name="ck_ad_v4_obligation_timing_anchor"),
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_timing_term_ordinal"),
        UniqueConstraint("timing_group_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_timing_term_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    timing_group_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    interval_text: Mapped[str] = mapped_column(Text, nullable=False)
    interval_numeric: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    comparator: Mapped[str] = mapped_column(String(32), nullable=False)
    anchor: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationRecurrence(Base):
    __tablename__ = "ad_v4_candidate_obligation_recurrences"
    __table_args__ = (
        CheckConstraint("kind IN ('none','interval','conditioned','unknown')", name="ck_ad_v4_obligation_recurrence_kind"),
        CheckConstraint(
            "(kind='none' AND timing_node_id IS NULL AND condition_root_node_id IS NULL AND reason IS NULL AND temporal_kind IS NULL) OR "
            "(kind='interval' AND timing_node_id IS NOT NULL AND condition_root_node_id IS NULL AND reason IS NULL AND temporal_kind IS NULL) OR "
            "(kind='conditioned' AND timing_node_id IS NOT NULL AND condition_root_node_id IS NOT NULL AND reason IS NULL AND temporal_kind IS NULL) OR "
            "(kind='unknown' AND timing_node_id IS NULL AND condition_root_node_id IS NULL AND reason IS NOT NULL AND temporal_kind IS NOT NULL)",
            name="ck_ad_v4_obligation_recurrence_union",
        ),
        UniqueConstraint("projection_id", "requirement_node_id", name="uq_ad_v4_obligation_recurrence_requirement"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    timing_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=True)
    condition_root_node_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temporal_kind: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class ADV4CandidateObligationTerminatingEffect(Base):
    __tablename__ = "ad_v4_candidate_obligation_terminating_effects"
    __table_args__ = (
        CheckConstraint("kind IN ('none','terminates')", name="ck_ad_v4_obligation_termination_kind"),
        CheckConstraint("(kind='none' AND edge_count=0) OR (kind='terminates' AND edge_count>=0)", name="ck_ad_v4_obligation_termination_union"),
        UniqueConstraint("projection_id", "requirement_node_id", name="uq_ad_v4_obligation_termination_requirement"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    edge_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationTerminationEdge(Base):
    __tablename__ = "ad_v4_candidate_obligation_termination_edges"
    __table_args__ = (
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_termination_edge_ordinal"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_termination_edge_identity"),
        UniqueConstraint("effect_node_id", "terminated_requirement_node_id", name="uq_ad_v4_obligation_termination_edge_target"),
        UniqueConstraint("effect_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_termination_edge_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    effect_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    terminated_requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    terminated_requirement_key: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationRecurrenceGroup(Base):
    __tablename__ = "ad_v4_candidate_obligation_recurrence_groups"
    __table_args__ = (
        CheckConstraint("completion_policy='all_active_requirements'", name="ck_ad_v4_obligation_group_completion"),
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999 AND member_count BETWEEN 2 AND 2000", name="ck_ad_v4_obligation_group_counts"),
        UniqueConstraint("projection_id", "recurrence_group_key", name="uq_ad_v4_obligation_group_key"),
        UniqueConstraint("projection_id", "canonical_ordinal", name="uq_ad_v4_obligation_group_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    recurrence_group_key: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_policy: Mapped[str] = mapped_column(String(32), nullable=False)
    initial_timing_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    recurring_timing_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationRecurrenceGroupMember(Base):
    __tablename__ = "ad_v4_candidate_obligation_recurrence_group_members"
    __table_args__ = (
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_group_member_ordinal"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_group_member_identity"),
        UniqueConstraint("group_node_id", "requirement_node_id", name="uq_ad_v4_obligation_group_member_target"),
        UniqueConstraint("group_node_id", "canonical_ordinal", name="uq_ad_v4_obligation_group_member_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    group_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    requirement_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)
    requirement_key: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)


class ADV4CandidateObligationAmocProvision(Base):
    __tablename__ = "ad_v4_candidate_obligation_amoc_provisions"
    __table_args__ = (
        CheckConstraint("canonical_ordinal BETWEEN 0 AND 1999", name="ck_ad_v4_obligation_amoc_ordinal"),
        UniqueConstraint("projection_id", "provision_key", name="uq_ad_v4_obligation_amoc_key"),
        UniqueConstraint("projection_id", "canonical_ordinal", name="uq_ad_v4_obligation_amoc_ordinal"),
    )

    semantic_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    provision_key: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    authority_assertion_node_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_semantic_nodes.id"), nullable=False)


class ADV4CandidateObligationProjectionEvent(Base):
    __tablename__ = "ad_v4_candidate_obligation_projection_events"
    __table_args__ = (
        CheckConstraint("sequence_number BETWEEN 0 AND 2147483647", name="ck_ad_v4_obligation_event_sequence"),
        CheckConstraint("event_type IN ('materialized','evidence_invalidated','parent_app_stale','candidate_corrected','candidate_replaced')", name="ck_ad_v4_obligation_event_type"),
        CheckConstraint(
            "(event_type='materialized' AND sequence_number=0 AND predecessor_event_hash IS NULL AND cause_kind IS NULL AND cause_id IS NULL AND cause_hash IS NULL) OR "
            "(event_type<>'materialized' AND sequence_number>0 AND predecessor_event_hash IS NOT NULL AND cause_kind IS NOT NULL AND cause_id IS NOT NULL AND cause_hash IS NOT NULL)",
            name="ck_ad_v4_obligation_event_union",
        ),
        UniqueConstraint("projection_id", "sequence_number", name="uq_ad_v4_obligation_event_sequence"),
        UniqueConstraint("projection_id", "event_hash", name="uq_ad_v4_obligation_event_hash"),
        UniqueConstraint("identity_hash", name="uq_ad_v4_obligation_event_identity"),
        Index(
            "uq_ad_v4_obligation_event_cause", "projection_id", "cause_kind", "cause_id",
            unique=True, postgresql_where=text("cause_id IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_projections.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_proposals.id"), nullable=False)
    app_projection_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_app_projections.id"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    predecessor_event_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    proposal_canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_binding_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    app_projection_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    obligation_subtree_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    correction_binding_set_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    causing_request_id: Mapped[str] = mapped_column(ForeignKey("ad_v4_candidate_obligation_materialization_requests.id"), nullable=False)
    cause_kind: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cause_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    cause_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    canonical_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _install_ad_v4_obligation_model_constraints() -> None:
    """Keep ORM joins aligned with the migration's same-projection boundary."""

    owner_tables = (
        "ad_v4_candidate_obligation_documents",
        "ad_v4_candidate_obligation_value_assertions",
        "ad_v4_candidate_obligation_requirements",
        "ad_v4_candidate_obligation_actions",
        "ad_v4_candidate_obligation_action_steps",
        "ad_v4_candidate_obligation_branches",
        "ad_v4_candidate_obligation_expressions",
        "ad_v4_candidate_obligation_timing_groups",
        "ad_v4_candidate_obligation_timing_terms",
        "ad_v4_candidate_obligation_recurrences",
        "ad_v4_candidate_obligation_terminating_effects",
        "ad_v4_candidate_obligation_recurrence_groups",
        "ad_v4_candidate_obligation_amoc_provisions",
    )
    relationship_tables = (
        "ad_v4_candidate_obligation_action_document_refs",
        "ad_v4_candidate_obligation_expression_edges",
        "ad_v4_candidate_obligation_requirement_dependencies",
        "ad_v4_candidate_obligation_termination_edges",
        "ad_v4_candidate_obligation_recurrence_group_members",
    )

    def attach(table_name: str, columns: list[str], target: list[str], name: str) -> None:
        ForeignKeyConstraint(
            columns, target, name=name, ondelete="RESTRICT",
            table=Base.metadata.tables[table_name],
        )

    for ordinal, table_name in enumerate(owner_tables):
        attach(
            table_name, ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            f"fk_aob_owner_projection_{ordinal}",
        )
        attach(
            table_name, ["semantic_node_id", "projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_semantic_nodes.id", "ad_v4_candidate_obligation_semantic_nodes.projection_id", "ad_v4_candidate_obligation_semantic_nodes.proposal_id"],
            f"fk_aob_owner_node_{ordinal}",
        )
    for ordinal, table_name in enumerate(relationship_tables):
        attach(
            table_name, ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            f"fk_aob_relation_projection_{ordinal}",
        )

    for ordinal, table_name in enumerate((
        "ad_v4_candidate_obligation_semantic_nodes",
        "ad_v4_candidate_obligation_data",
        "ad_v4_candidate_obligation_evidence_links",
    )):
        attach(
            table_name, ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            f"fk_aob_generic_projection_{ordinal}",
        )

    attach(
        "ad_v4_candidate_obligation_semantic_nodes",
        ["parent_node_id", "projection_id", "proposal_id"],
        ["ad_v4_candidate_obligation_semantic_nodes.id", "ad_v4_candidate_obligation_semantic_nodes.projection_id", "ad_v4_candidate_obligation_semantic_nodes.proposal_id"],
        "fk_aob_node_parent",
    )
    for table_name, column, name in (
        ("ad_v4_candidate_obligation_data", "semantic_node_id", "fk_aob_data_node"),
        ("ad_v4_candidate_obligation_evidence_links", "semantic_node_id", "fk_aob_evidence_node"),
        ("ad_v4_candidate_obligation_documents", "document_number_node_id", "fk_aob_doc_number"),
        ("ad_v4_candidate_obligation_documents", "revision_node_id", "fk_aob_doc_revision"),
        ("ad_v4_candidate_obligation_documents", "retention_node_id", "fk_aob_doc_retention"),
        ("ad_v4_candidate_obligation_requirements", "action_node_id", "fk_aob_req_action"),
        ("ad_v4_candidate_obligation_requirements", "activation_root_node_id", "fk_aob_req_activation"),
        ("ad_v4_candidate_obligation_requirements", "branch_node_id", "fk_aob_req_branch"),
        ("ad_v4_candidate_obligation_requirements", "initial_timing_node_id", "fk_aob_req_initial_timing"),
        ("ad_v4_candidate_obligation_requirements", "recurrence_node_id", "fk_aob_req_recurrence"),
        ("ad_v4_candidate_obligation_requirements", "terminating_effect_node_id", "fk_aob_req_termination"),
        ("ad_v4_candidate_obligation_actions", "requirement_node_id", "fk_aob_action_requirement"),
        ("ad_v4_candidate_obligation_action_steps", "action_node_id", "fk_aob_step_action"),
        ("ad_v4_candidate_obligation_branches", "requirement_node_id", "fk_aob_branch_requirement"),
        ("ad_v4_candidate_obligation_branches", "condition_root_node_id", "fk_aob_branch_condition"),
        ("ad_v4_candidate_obligation_expressions", "requirement_node_id", "fk_aob_expr_requirement"),
        ("ad_v4_candidate_obligation_expressions", "requirement_target_node_id", "fk_aob_expr_req_target"),
        ("ad_v4_candidate_obligation_timing_groups", "owner_node_id", "fk_aob_timing_owner"),
        ("ad_v4_candidate_obligation_timing_terms", "timing_group_node_id", "fk_aob_term_timing"),
        ("ad_v4_candidate_obligation_recurrences", "requirement_node_id", "fk_aob_recurrence_requirement"),
        ("ad_v4_candidate_obligation_recurrences", "timing_node_id", "fk_aob_recurrence_timing"),
        ("ad_v4_candidate_obligation_recurrences", "condition_root_node_id", "fk_aob_recurrence_condition"),
        ("ad_v4_candidate_obligation_terminating_effects", "requirement_node_id", "fk_aob_effect_requirement"),
        ("ad_v4_candidate_obligation_recurrence_groups", "initial_timing_node_id", "fk_aob_group_initial_timing"),
        ("ad_v4_candidate_obligation_recurrence_groups", "recurring_timing_node_id", "fk_aob_group_recurring_timing"),
        ("ad_v4_candidate_obligation_amoc_provisions", "authority_assertion_node_id", "fk_aob_amoc_authority"),
        ("ad_v4_candidate_obligation_action_document_refs", "action_node_id", "fk_aob_docref_action"),
        ("ad_v4_candidate_obligation_action_document_refs", "document_node_id", "fk_aob_docref_document"),
        ("ad_v4_candidate_obligation_expression_edges", "requirement_node_id", "fk_aob_expr_edge_requirement"),
        ("ad_v4_candidate_obligation_expression_edges", "parent_expression_id", "fk_aob_expr_edge_parent"),
        ("ad_v4_candidate_obligation_expression_edges", "child_expression_id", "fk_aob_expr_edge_child"),
        ("ad_v4_candidate_obligation_requirement_dependencies", "requirement_node_id", "fk_aob_dep_requirement"),
        ("ad_v4_candidate_obligation_requirement_dependencies", "prerequisite_requirement_node_id", "fk_aob_dep_prerequisite"),
        ("ad_v4_candidate_obligation_termination_edges", "effect_node_id", "fk_aob_term_edge_effect"),
        ("ad_v4_candidate_obligation_termination_edges", "terminated_requirement_node_id", "fk_aob_term_edge_requirement"),
        ("ad_v4_candidate_obligation_recurrence_group_members", "group_node_id", "fk_aob_member_group"),
        ("ad_v4_candidate_obligation_recurrence_group_members", "requirement_node_id", "fk_aob_member_requirement"),
    ):
        attach(
            table_name, [column, "projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_semantic_nodes.id", "ad_v4_candidate_obligation_semantic_nodes.projection_id", "ad_v4_candidate_obligation_semantic_nodes.proposal_id"],
            name,
        )
    attach(
        "ad_v4_candidate_obligation_expressions",
        ["app_target_projection_id", "proposal_id"],
        ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"],
        "fk_aob_expr_app_projection",
    )
    attach(
        "ad_v4_candidate_obligation_expressions",
        ["app_target_node_id", "app_target_projection_id", "proposal_id"],
        ["ad_v4_candidate_app_semantic_nodes.id", "ad_v4_candidate_app_semantic_nodes.projection_id", "ad_v4_candidate_app_semantic_nodes.proposal_id"],
        "fk_aob_expr_app_node",
    )
    attach(
        "ad_v4_candidate_obligation_projections",
        ["app_projection_id", "proposal_id"],
        ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"],
        "fk_aob_projection_app",
    )
    for table_name, name in (
        ("ad_v4_candidate_obligation_materialization_requests", "fk_aob_request_app"),
        ("ad_v4_candidate_obligation_projection_events", "fk_aob_event_app"),
    ):
        attach(
            table_name, ["app_projection_id", "proposal_id"],
            ["ad_v4_candidate_app_projections.id", "ad_v4_candidate_app_projections.proposal_id"],
            name,
        )
    for table_name, name in (
        ("ad_v4_candidate_obligation_materialization_requests", "fk_aob_request_projection"),
        ("ad_v4_candidate_obligation_projection_events", "fk_aob_event_projection"),
    ):
        attach(
            table_name, ["projection_id", "proposal_id"],
            ["ad_v4_candidate_obligation_projections.id", "ad_v4_candidate_obligation_projections.proposal_id"],
            name,
        )
    attach(
        "ad_v4_candidate_obligation_evidence_links",
        ["proposal_id", "candidate_binding_id", "evidence_key"],
        ["ad_v4_candidate_evidence_bindings.proposal_id", "ad_v4_candidate_evidence_bindings.id", "ad_v4_candidate_evidence_bindings.evidence_key"],
        "fk_aob_evidence_candidate_binding",
    )


_install_ad_v4_obligation_model_constraints()


class AirworthinessDirective(TimestampMixin, Base):
    __tablename__ = "airworthiness_directives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ad"))
    discovery_record_id: Mapped[str] = mapped_column(
        ForeignKey("ad_discovery_records.id"),
        nullable=True,
        unique=True,
        index=True,
    )
    ad_number: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="candidate", index=True)
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    extraction_status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_started", index=True)
    review_status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_started", index=True)
    approved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    discovery_record = relationship("ADDiscoveryRecord", back_populates="directive")
    extractions = relationship("ADExtraction", back_populates="directive")
    match_results = relationship("ADMatchResult", back_populates="directive")
    publications = relationship("ADPublication", back_populates="directive")
    evidence_fragments = relationship("ADEvidenceFragment", back_populates="directive")
    target_applicabilities = relationship("ADTargetApplicability", back_populates="directive")
    compliance_requirements = relationship("ADComplianceRequirement", back_populates="directive")
    amoc_provisions = relationship("ADAMOCProvision", back_populates="directive")
    supersedes_edges = relationship(
        "ADSupersession",
        foreign_keys="ADSupersession.superseding_ad_id",
        back_populates="superseding_ad",
    )
    superseded_by_edges = relationship(
        "ADSupersession",
        foreign_keys="ADSupersession.superseded_ad_id",
        back_populates="superseded_ad",
    )


class ADSupersession(TimestampMixin, Base):
    __tablename__ = "ad_supersessions"
    __table_args__ = (
        UniqueConstraint("superseding_ad_id", "superseded_ad_id", "relationship_type", name="uq_ad_supersession_edge"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ads"))
    superseding_ad_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False, index=True)
    superseded_ad_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False, default="supersedes")
    evidence_text: Mapped[str] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    superseding_ad = relationship(
        "AirworthinessDirective",
        foreign_keys=[superseding_ad_id],
        back_populates="supersedes_edges",
    )
    superseded_ad = relationship(
        "AirworthinessDirective",
        foreign_keys=[superseded_ad_id],
        back_populates="superseded_by_edges",
    )


class ApplicabilityTarget(TimestampMixin, Base):
    __tablename__ = "applicability_targets"
    __table_args__ = (
        UniqueConstraint(
            "product_type",
            "product_subtype",
            "make",
            "model",
            name="uq_applicability_target_identity",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("tgt"))
    product_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_subtype: Mapped[str] = mapped_column(String(512), nullable=True, index=True)
    make: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    model: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    normalized_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)

    applicabilities = relationship("ADTargetApplicability", back_populates="target")


class ADPublication(TimestampMixin, Base):
    __tablename__ = "ad_publications"
    __table_args__ = (
        UniqueConstraint(
            "directive_id",
            "source_system",
            "source_type",
            "source_identifier",
            name="uq_ad_publication_identity",
        ),
        UniqueConstraint(
            "directive_id", "source_document_id",
            name="uq_ad_publication_directive_document",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("pub"))
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False, index=True)
    source_snapshot_id: Mapped[str] = mapped_column(ForeignKey("ad_source_snapshots.id"), nullable=True, index=True)
    source_document_id: Mapped[str] = mapped_column(ForeignKey("ad_source_documents.id"), nullable=True, index=True)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=True)
    publication_date: Mapped[Date] = mapped_column(Date, nullable=True, index=True)
    effective_date: Mapped[Date] = mapped_column(Date, nullable=True)
    html_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    pdf_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)

    directive = relationship("AirworthinessDirective", back_populates="publications")
    source_snapshot = relationship("ADSourceSnapshot", back_populates="publications")
    source_document = relationship("ADSourceDocument", back_populates="publications")


class ADTargetApplicability(TimestampMixin, Base):
    __tablename__ = "ad_target_applicability"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ata"))
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(ForeignKey("applicability_targets.id"), nullable=False, index=True)
    source_publication_id: Mapped[str] = mapped_column(ForeignKey("ad_publications.id"), nullable=True, index=True)
    source_extraction_id: Mapped[str] = mapped_column(ForeignKey("ad_extractions.id"), nullable=True, index=True)
    applicability_basis: Mapped[str] = mapped_column(String(64), nullable=False, default="source_row")
    applicability_group_key: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    serial_range: Mapped[dict] = mapped_column(JSON, nullable=True)
    source_identity: Mapped[dict] = mapped_column(JSON, nullable=True)
    equipment_conditions: Mapped[list] = mapped_column(JSON, nullable=True)
    conditions: Mapped[list] = mapped_column(JSON, nullable=True)
    compliance_actions: Mapped[list] = mapped_column(JSON, nullable=True)
    compliance_intervals: Mapped[list] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    citations: Mapped[list] = mapped_column(JSON, nullable=True)
    source_payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="current", index=True)

    directive = relationship("AirworthinessDirective", back_populates="target_applicabilities")
    target = relationship("ApplicabilityTarget", back_populates="applicabilities")
    source_publication = relationship("ADPublication")
    source_extraction = relationship("ADExtraction", back_populates="target_applicabilities")
    match_results = relationship("ADMatchResult", back_populates="target_applicability")
    compliance_requirements = relationship("ADComplianceRequirement", back_populates="target_applicability")


Index(
    "uq_ad_target_applicability_identity_v3",
    ADTargetApplicability.directive_id,
    ADTargetApplicability.target_id,
    func.coalesce(ADTargetApplicability.source_publication_id, ""),
    ADTargetApplicability.applicability_basis,
    func.coalesce(ADTargetApplicability.applicability_group_key, ""),
    func.coalesce(ADTargetApplicability.source_extraction_id, ""),
    unique=True,
)


class ADComplianceRequirement(TimestampMixin, Base):
    __tablename__ = "ad_compliance_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("acr"))
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False, index=True)
    target_applicability_id: Mapped[str] = mapped_column(
        ForeignKey("ad_target_applicability.id"), nullable=False, index=True
    )
    source_extraction_id: Mapped[str] = mapped_column(ForeignKey("ad_extractions.id"), nullable=False, index=True)
    requirement_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    requirement_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    combination_logic: Mapped[str] = mapped_column(String(32), nullable=False, default="all")
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    terminating_action_text: Mapped[str] = mapped_column(Text, nullable=True)
    effective_date: Mapped[PythonDate] = mapped_column(Date, nullable=True)
    review_status: Mapped[str] = mapped_column(String(64), nullable=False, default="needs_adjudication", index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    citations: Mapped[list] = mapped_column(JSON, nullable=True)
    source_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="current", index=True)

    directive = relationship("AirworthinessDirective", back_populates="compliance_requirements")
    target_applicability = relationship("ADTargetApplicability", back_populates="compliance_requirements")
    source_extraction = relationship("ADExtraction", back_populates="compliance_requirements")
    triggers = relationship("ADComplianceTrigger", back_populates="requirement")
    compliance_events = relationship("ADComplianceEvent", back_populates="requirement")
    due_states = relationship("AircraftADDueState", back_populates="requirement")


class ADComplianceTrigger(TimestampMixin, Base):
    __tablename__ = "ad_compliance_triggers"
    __table_args__ = (
        UniqueConstraint(
            "requirement_id",
            "sequence",
            name="uq_ad_compliance_trigger_sequence",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("act"))
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("ad_compliance_requirements.id"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="recurring")
    metric: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    interval_value: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    interval_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    anchor_kind: Mapped[str] = mapped_column(String(64), nullable=False, default="last_compliance")
    source_text: Mapped[str] = mapped_column(Text, nullable=True)

    requirement = relationship("ADComplianceRequirement", back_populates="triggers")


class ADAMOCProvision(TimestampMixin, Base):
    __tablename__ = "ad_amoc_provisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("aam"))
    directive_id: Mapped[str] = mapped_column(
        ForeignKey("airworthiness_directives.id"), nullable=False, index=True
    )
    source_extraction_id: Mapped[str] = mapped_column(
        ForeignKey("ad_extractions.id"), nullable=False, index=True
    )
    provision_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    provision_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    authority_text: Mapped[str] = mapped_column(Text, nullable=False)
    approving_authority: Mapped[str] = mapped_column(String(512), nullable=True, index=True)
    submission_instructions: Mapped[str] = mapped_column(Text, nullable=True)
    conditions: Mapped[list] = mapped_column(JSON, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="current", index=True)

    directive = relationship("AirworthinessDirective", back_populates="amoc_provisions")
    source_extraction = relationship("ADExtraction", back_populates="amoc_provisions")


class ADComplianceEvent(TimestampMixin, Base):
    __tablename__ = "ad_compliance_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ace"))
    evidence_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("ad_compliance_requirements.id"), nullable=False, index=True
    )
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    installed_component_id: Mapped[str] = mapped_column(
        ForeignKey("installed_components.id"), nullable=True, index=True
    )
    logbook_entry_id: Mapped[str] = mapped_column(ForeignKey("logbook_entries.id"), nullable=False, index=True)
    occurred_on: Mapped[PythonDate] = mapped_column(Date, nullable=False, index=True)
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    tach_hours: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=True)
    hobbs_hours: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=True)
    total_time_hours: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=True)
    cycle_count: Mapped[int] = mapped_column(Integer, nullable=True)
    is_terminating_action: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verification_status: Mapped[str] = mapped_column(String(64), nullable=False, default="verified_logbook", index=True)

    requirement = relationship("ADComplianceRequirement", back_populates="compliance_events")
    aircraft = relationship("Aircraft", back_populates="ad_compliance_events")
    installed_component = relationship("InstalledComponent", back_populates="ad_compliance_events")
    logbook_entry = relationship("LogbookEntry", back_populates="ad_compliance_events")
    due_states = relationship("AircraftADDueState", back_populates="last_compliance_event")


class AircraftTimeState(TimestampMixin, Base):
    __tablename__ = "aircraft_time_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ats"))
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    installed_component_id: Mapped[str] = mapped_column(
        ForeignKey("installed_components.id"), nullable=True, index=True
    )
    source_logbook_entry_id: Mapped[str] = mapped_column(
        ForeignKey("logbook_entries.id"), nullable=True, index=True
    )
    observed_on: Mapped[PythonDate] = mapped_column(Date, nullable=False, index=True)
    tach_hours: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=True)
    hobbs_hours: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=True)
    total_time_hours: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=True)
    cycle_count: Mapped[int] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(64), nullable=False, default="verified_logbook", index=True)

    aircraft = relationship("Aircraft", back_populates="ad_time_states")
    installed_component = relationship("InstalledComponent", back_populates="ad_time_states")
    source_logbook_entry = relationship("LogbookEntry", back_populates="ad_time_states")


class AircraftADDueState(TimestampMixin, Base):
    __tablename__ = "aircraft_ad_due_states"
    __table_args__ = (
        UniqueConstraint(
            "aircraft_id",
            "requirement_id",
            "installed_component_id",
            "algorithm_version",
            "input_hash",
            name="uq_aircraft_ad_due_state_replay",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("adu"))
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("ad_compliance_requirements.id"), nullable=False, index=True
    )
    installed_component_id: Mapped[str] = mapped_column(
        ForeignKey("installed_components.id"), nullable=True, index=True
    )
    last_compliance_event_id: Mapped[str] = mapped_column(
        ForeignKey("ad_compliance_events.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    due_date: Mapped[PythonDate] = mapped_column(Date, nullable=True, index=True)
    due_metric: Mapped[str] = mapped_column(String(64), nullable=True)
    due_value: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=True)
    trigger_states: Mapped[list] = mapped_column(JSON, nullable=True)
    unresolved_reasons: Mapped[list] = mapped_column(JSON, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(64), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    computed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    aircraft = relationship("Aircraft", back_populates="ad_due_states")
    requirement = relationship("ADComplianceRequirement", back_populates="due_states")
    installed_component = relationship("InstalledComponent", back_populates="ad_due_states")
    last_compliance_event = relationship("ADComplianceEvent", back_populates="due_states")
    match_results = relationship("ADMatchResult", back_populates="due_state")
    match_links = relationship("ADMatchDueStateLink", back_populates="due_state")


class ADCoverageSet(TimestampMixin, Base):
    __tablename__ = "ad_coverage_sets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("cov"))
    target_id: Mapped[str] = mapped_column(
        ForeignKey("applicability_targets.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    current_source_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("ad_source_snapshots.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="awaiting_source_snapshot", index=True)
    coverage_version: Mapped[str] = mapped_column(String(128), nullable=False, default="unversioned")
    first_triggered_by_aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=True, index=True)
    first_triggered_by_organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=True,
        index=True,
    )
    directive_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    derived_storage_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    last_built_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_resolved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)

    target = relationship("ApplicabilityTarget")
    current_source_snapshot = relationship("ADSourceSnapshot", back_populates="coverage_sets")
    first_triggered_by_aircraft = relationship("Aircraft", foreign_keys=[first_triggered_by_aircraft_id])
    first_triggered_by_organization = relationship("Organization", foreign_keys=[first_triggered_by_organization_id])
    subscriptions = relationship("ADCoverageSubscription", back_populates="coverage_set")
    cost_entries = relationship("ADCostLedgerEntry", back_populates="coverage_set")


class ADCoverageSubscription(TimestampMixin, Base):
    __tablename__ = "ad_coverage_subscriptions"
    __table_args__ = (
        UniqueConstraint("coverage_set_id", "aircraft_id", name="uq_ad_coverage_subscription"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("cvs"))
    coverage_set_id: Mapped[str] = mapped_column(ForeignKey("ad_coverage_sets.id"), nullable=False, index=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active", index=True)
    triggered_creation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    linked_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_resolved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    coverage_set = relationship("ADCoverageSet", back_populates="subscriptions")
    aircraft = relationship("Aircraft", back_populates="ad_coverage_subscriptions")
    organization = relationship("Organization")


class ADCostLedgerEntry(TimestampMixin, Base):
    __tablename__ = "ad_cost_ledger_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("acl"))
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=True, unique=True, index=True)
    scope_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cost_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_snapshot_id: Mapped[str] = mapped_column(ForeignKey("ad_source_snapshots.id"), nullable=True, index=True)
    coverage_set_id: Mapped[str] = mapped_column(ForeignKey("ad_coverage_sets.id"), nullable=True, index=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=True, index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    usage_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    usage_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    actual_cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    allocated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    attribution_status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="informational_unallocated",
        index=True,
    )
    allocation_policy_version: Mapped[str] = mapped_column(String(64), nullable=True)
    incurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)

    source_snapshot = relationship("ADSourceSnapshot", back_populates="cost_entries")
    coverage_set = relationship("ADCoverageSet", back_populates="cost_entries")
    aircraft = relationship("Aircraft", back_populates="ad_cost_entries")
    organization = relationship("Organization")


class ADReconciliationIssue(TimestampMixin, Base):
    __tablename__ = "ad_reconciliation_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ari"))
    issue_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="medium", index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open", index=True)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=True, index=True)
    publication_id: Mapped[str] = mapped_column(ForeignKey("ad_publications.id"), nullable=True, index=True)
    target_id: Mapped[str] = mapped_column(ForeignKey("applicability_targets.id"), nullable=True, index=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=True, index=True)
    source_snapshot_id: Mapped[str] = mapped_column(ForeignKey("ad_source_snapshots.id"), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    resolved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    directive = relationship("AirworthinessDirective")
    publication = relationship("ADPublication")
    target = relationship("ApplicabilityTarget")
    aircraft = relationship("Aircraft")
    source_snapshot = relationship("ADSourceSnapshot", back_populates="reconciliation_issues")


class ADExtraction(TimestampMixin, Base):
    __tablename__ = "ad_extractions"
    __table_args__ = (
        UniqueConstraint(
            "directive_id",
            "input_content_hash",
            "provider_name",
            "provider_version",
            "schema_version",
            name="uq_ad_extraction_idempotency",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("adx"))
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    input_content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="needs_review", index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    output: Mapped[dict] = mapped_column(JSON, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, nullable=True)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=True)
    extracted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    directive = relationship("AirworthinessDirective", back_populates="extractions")
    reviews = relationship("ADExtractionReview", back_populates="extraction")
    match_results = relationship("ADMatchResult", back_populates="extraction")
    compliance_requirements = relationship("ADComplianceRequirement", back_populates="source_extraction")
    amoc_provisions = relationship("ADAMOCProvision", back_populates="source_extraction")
    target_applicabilities = relationship("ADTargetApplicability", back_populates="source_extraction")
    review_decisions = relationship("ADExtractionReviewDecision", back_populates="extraction")


class ADExtractionReview(TimestampMixin, Base):
    __tablename__ = "ad_extraction_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("arv"))
    extraction_id: Mapped[str] = mapped_column(ForeignKey("ad_extractions.id"), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending", index=True)
    proposed_output: Mapped[dict] = mapped_column(JSON, nullable=False)
    decision_output: Mapped[dict] = mapped_column(JSON, nullable=True)
    decision: Mapped[str] = mapped_column(String(64), nullable=True)
    reviewer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    extraction = relationship("ADExtraction", back_populates="reviews")
    reviewer = relationship("User")
    decision_history = relationship("ADExtractionReviewDecision", back_populates="review")


class ADExtractionReviewDecision(TimestampMixin, Base):
    __tablename__ = "ad_extraction_review_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ard"))
    review_id: Mapped[str] = mapped_column(ForeignKey("ad_extraction_reviews.id"), nullable=False, index=True)
    extraction_id: Mapped[str] = mapped_column(ForeignKey("ad_extractions.id"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    output_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_output: Mapped[dict] = mapped_column(JSON, nullable=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    decided_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, default="review_decision", index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)

    review = relationship("ADExtractionReview", back_populates="decision_history")
    extraction = relationship("ADExtraction", back_populates="review_decisions")
    actor = relationship("User")


class ADMatchResult(TimestampMixin, Base):
    __tablename__ = "ad_match_results"
    __table_args__ = (
        UniqueConstraint(
            "aircraft_id",
            "directive_id",
            "algorithm_name",
            "algorithm_version",
            "input_hash",
            name="uq_ad_match_result_replay",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("adm"))
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=False, index=True)
    directive_id: Mapped[str] = mapped_column(ForeignKey("airworthiness_directives.id"), nullable=False, index=True)
    extraction_id: Mapped[str] = mapped_column(ForeignKey("ad_extractions.id"), nullable=False, index=True)
    installed_component_id: Mapped[str] = mapped_column(ForeignKey("installed_components.id"), nullable=True, index=True)
    target_applicability_id: Mapped[str] = mapped_column(ForeignKey("ad_target_applicability.id"), nullable=True, index=True)
    due_state_id: Mapped[str] = mapped_column(ForeignKey("aircraft_ad_due_states.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    match_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    unresolved_reasons: Mapped[list] = mapped_column(JSON, nullable=True)
    applicability_snapshot: Mapped[dict] = mapped_column(JSON, nullable=True)
    algorithm_name: Mapped[str] = mapped_column(String(128), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(128), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    computed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    aircraft = relationship("Aircraft", back_populates="ad_match_results")
    directive = relationship("AirworthinessDirective", back_populates="match_results")
    extraction = relationship("ADExtraction", back_populates="match_results")
    installed_component = relationship("InstalledComponent", back_populates="match_results")
    target_applicability = relationship("ADTargetApplicability", back_populates="match_results")
    due_state = relationship("AircraftADDueState", back_populates="match_results")
    evidence_links = relationship("ADMatchEvidence", back_populates="match_result")
    adjudication = relationship("ADMatchAdjudication", back_populates="match_result", uselist=False)
    due_state_links = relationship("ADMatchDueStateLink", back_populates="match_result")


class ADMatchDueStateLink(TimestampMixin, Base):
    __tablename__ = "ad_match_due_state_links"
    __table_args__ = (
        UniqueConstraint(
            "match_result_id",
            "due_state_id",
            name="uq_ad_match_due_state_link",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("mdl"))
    match_result_id: Mapped[str] = mapped_column(ForeignKey("ad_match_results.id"), nullable=False, index=True)
    due_state_id: Mapped[str] = mapped_column(ForeignKey("aircraft_ad_due_states.id"), nullable=False, index=True)

    match_result = relationship("ADMatchResult", back_populates="due_state_links")
    due_state = relationship("AircraftADDueState", back_populates="match_links")


class ADMatchEvidence(TimestampMixin, Base):
    __tablename__ = "ad_match_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ame"))
    match_result_id: Mapped[str] = mapped_column(ForeignKey("ad_match_results.id"), nullable=False, index=True)
    logbook_entry_id: Mapped[str] = mapped_column(ForeignKey("logbook_entries.id"), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    field_name: Mapped[str] = mapped_column(String(128), nullable=True)
    matched_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    match_result = relationship("ADMatchResult", back_populates="evidence_links")
    logbook_entry = relationship("LogbookEntry")


class ADMatchAdjudication(TimestampMixin, Base):
    __tablename__ = "ad_match_adjudications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("adj"))
    match_result_id: Mapped[str] = mapped_column(ForeignKey("ad_match_results.id"), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending", index=True)
    decision: Mapped[str] = mapped_column(String(64), nullable=True)
    reviewer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    future_improvement_tags: Mapped[list] = mapped_column(JSON, nullable=True)
    reviewed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    match_result = relationship("ADMatchResult", back_populates="adjudication")
    reviewer = relationship("User")


class ProductEvent(Base):
    __tablename__ = "product_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("pev"))
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    event_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    properties_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    request_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    actor = relationship("User", foreign_keys=[actor_user_id])
    organization = relationship("Organization")
    aircraft = relationship("Aircraft")


class UserFeedback(TimestampMixin, Base):
    __tablename__ = "user_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ufb"))
    submitted_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), nullable=True, index=True)
    subject_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    feedback_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="medium", index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open", index=True)

    submitted_by = relationship("User", foreign_keys=[submitted_by_user_id])
    organization = relationship("Organization")
    aircraft = relationship("Aircraft")


class WorkflowStatusEvent(Base):
    __tablename__ = "workflow_status_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("wse"))
    workflow_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    previous_status: Mapped[str] = mapped_column(String(128), nullable=True)
    new_status: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    actor_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    actor = relationship("User", foreign_keys=[actor_user_id])
