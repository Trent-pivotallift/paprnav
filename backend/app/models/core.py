import uuid

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
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
