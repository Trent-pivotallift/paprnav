"""add initial schema

Revision ID: 20260617_0001
Revises:
Create Date: 2026-06-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260617_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("external_auth_subject", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_unique_constraint("uq_users_external_auth_subject", "users", ["external_auth_subject"])

    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "logbook_sections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_membership_organization_user"),
    )
    op.create_index(op.f("ix_organization_memberships_organization_id"), "organization_memberships", ["organization_id"])
    op.create_index(op.f("ix_organization_memberships_user_id"), "organization_memberships", ["user_id"])

    op.create_table(
        "aircraft",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_organization_id", sa.String(length=36), nullable=False),
        sa.Column("n_number_raw", sa.String(length=32), nullable=False),
        sa.Column("n_number_normalized", sa.String(length=32), nullable=False),
        sa.Column("make", sa.String(length=128), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("serial_number", sa.String(length=128), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("airframe_serial_number", sa.String(length=128), nullable=True),
        sa.Column("engine_make", sa.String(length=128), nullable=True),
        sa.Column("engine_model", sa.String(length=128), nullable=True),
        sa.Column("engine_serial_number", sa.String(length=128), nullable=True),
        sa.Column("propeller_make", sa.String(length=128), nullable=True),
        sa.Column("propeller_model", sa.String(length=128), nullable=True),
        sa.Column("propeller_serial_number", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["owner_organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_aircraft_created_by_user_id"), "aircraft", ["created_by_user_id"])
    op.create_index(op.f("ix_aircraft_n_number_normalized"), "aircraft", ["n_number_normalized"], unique=True)
    op.create_index(op.f("ix_aircraft_owner_organization_id"), "aircraft", ["owner_organization_id"])

    op.create_table(
        "aircraft_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("assigned_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aircraft_id", "organization_id", name="uq_aircraft_assignment"),
    )
    op.create_index(op.f("ix_aircraft_assignments_aircraft_id"), "aircraft_assignments", ["aircraft_id"])
    op.create_index(op.f("ix_aircraft_assignments_assigned_by_user_id"), "aircraft_assignments", ["assigned_by_user_id"])
    op.create_index(op.f("ix_aircraft_assignments_organization_id"), "aircraft_assignments", ["organization_id"])

    op.create_table(
        "logbook_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("logbook_section_id", sa.String(length=36), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("performer_name", sa.String(length=255), nullable=True),
        sa.Column("performer_credential", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("tach_time", sa.Float(), nullable=True),
        sa.Column("hobbs_time", sa.Float(), nullable=True),
        sa.Column("total_time", sa.Float(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["logbook_section_id"], ["logbook_sections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_logbook_entries_aircraft_id"), "logbook_entries", ["aircraft_id"])
    op.create_index(op.f("ix_logbook_entries_created_by_user_id"), "logbook_entries", ["created_by_user_id"])
    op.create_index(op.f("ix_logbook_entries_logbook_section_id"), "logbook_entries", ["logbook_section_id"])

    op.create_table(
        "uploads",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("aircraft_id", sa.String(length=36), nullable=False),
        sa.Column("uploaded_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_backend", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_uploads_aircraft_id"), "uploads", ["aircraft_id"])
    op.create_index(op.f("ix_uploads_sha256"), "uploads", ["sha256"])
    op.create_index(op.f("ix_uploads_uploaded_by_user_id"), "uploads", ["uploaded_by_user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_uploads_uploaded_by_user_id"), table_name="uploads")
    op.drop_index(op.f("ix_uploads_sha256"), table_name="uploads")
    op.drop_index(op.f("ix_uploads_aircraft_id"), table_name="uploads")
    op.drop_table("uploads")

    op.drop_index(op.f("ix_logbook_entries_logbook_section_id"), table_name="logbook_entries")
    op.drop_index(op.f("ix_logbook_entries_created_by_user_id"), table_name="logbook_entries")
    op.drop_index(op.f("ix_logbook_entries_aircraft_id"), table_name="logbook_entries")
    op.drop_table("logbook_entries")

    op.drop_index(op.f("ix_aircraft_assignments_organization_id"), table_name="aircraft_assignments")
    op.drop_index(op.f("ix_aircraft_assignments_assigned_by_user_id"), table_name="aircraft_assignments")
    op.drop_index(op.f("ix_aircraft_assignments_aircraft_id"), table_name="aircraft_assignments")
    op.drop_table("aircraft_assignments")

    op.drop_index(op.f("ix_aircraft_owner_organization_id"), table_name="aircraft")
    op.drop_index(op.f("ix_aircraft_n_number_normalized"), table_name="aircraft")
    op.drop_index(op.f("ix_aircraft_created_by_user_id"), table_name="aircraft")
    op.drop_table("aircraft")

    op.drop_index(op.f("ix_organization_memberships_user_id"), table_name="organization_memberships")
    op.drop_index(op.f("ix_organization_memberships_organization_id"), table_name="organization_memberships")
    op.drop_table("organization_memberships")

    op.drop_table("logbook_sections")
    op.drop_table("organizations")
    op.drop_constraint("uq_users_external_auth_subject", "users", type_="unique")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
