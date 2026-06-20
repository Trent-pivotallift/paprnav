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
    ad_match_results = relationship("ADMatchResult", back_populates="aircraft")


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


class AirworthinessDirective(TimestampMixin, Base):
    __tablename__ = "airworthiness_directives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("ad"))
    discovery_record_id: Mapped[str] = mapped_column(
        ForeignKey("ad_discovery_records.id"),
        nullable=False,
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
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    match_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    unresolved_reasons: Mapped[list] = mapped_column(JSON, nullable=True)
    algorithm_name: Mapped[str] = mapped_column(String(128), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(128), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    computed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    aircraft = relationship("Aircraft", back_populates="ad_match_results")
    directive = relationship("AirworthinessDirective", back_populates="match_results")
    extraction = relationship("ADExtraction", back_populates="match_results")
    evidence_links = relationship("ADMatchEvidence", back_populates="match_result")
    adjudication = relationship("ADMatchAdjudication", back_populates="match_result", uselist=False)


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
