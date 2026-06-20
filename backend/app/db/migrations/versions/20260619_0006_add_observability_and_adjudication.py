"""add observability and adjudication metadata

Revision ID: 20260619_0006
Revises: 20260618_0005
Create Date: 2026-06-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260619_0006"
down_revision: Union[str, None] = "20260618_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ad_match_adjudications", sa.Column("future_improvement_tags", sa.JSON(), nullable=True))

    op.create_table(
        "product_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("aircraft_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("event_source", sa.String(length=64), nullable=False),
        sa.Column("subject_type", sa.String(length=128), nullable=False),
        sa.Column("subject_id", sa.String(length=128), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("properties_json", sa.JSON(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "actor_user_id",
        "organization_id",
        "aircraft_id",
        "event_type",
        "event_source",
        "subject_type",
        "subject_id",
        "event_time",
        "request_id",
        "session_id",
    ]:
        op.create_index(op.f(f"ix_product_events_{column}"), "product_events", [column])

    op.create_table(
        "user_feedback",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("submitted_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("aircraft_id", sa.String(length=36), nullable=True),
        sa.Column("subject_type", sa.String(length=128), nullable=False),
        sa.Column("subject_id", sa.String(length=128), nullable=True),
        sa.Column("feedback_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "submitted_by_user_id",
        "organization_id",
        "aircraft_id",
        "subject_type",
        "subject_id",
        "feedback_type",
        "severity",
        "status",
    ]:
        op.create_index(op.f(f"ix_user_feedback_{column}"), "user_feedback", [column])

    op.create_table(
        "workflow_status_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workflow_type", sa.String(length=128), nullable=False),
        sa.Column("workflow_id", sa.String(length=128), nullable=False),
        sa.Column("previous_status", sa.String(length=128), nullable=True),
        sa.Column("new_status", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor_type", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["workflow_type", "workflow_id", "new_status", "actor_type", "actor_user_id", "created_at"]:
        op.create_index(op.f(f"ix_workflow_status_events_{column}"), "workflow_status_events", [column])


def downgrade() -> None:
    for column in ["workflow_type", "workflow_id", "new_status", "actor_type", "actor_user_id", "created_at"]:
        op.drop_index(op.f(f"ix_workflow_status_events_{column}"), table_name="workflow_status_events")
    op.drop_table("workflow_status_events")

    for column in [
        "submitted_by_user_id",
        "organization_id",
        "aircraft_id",
        "subject_type",
        "subject_id",
        "feedback_type",
        "severity",
        "status",
    ]:
        op.drop_index(op.f(f"ix_user_feedback_{column}"), table_name="user_feedback")
    op.drop_table("user_feedback")

    for column in [
        "actor_user_id",
        "organization_id",
        "aircraft_id",
        "event_type",
        "event_source",
        "subject_type",
        "subject_id",
        "event_time",
        "request_id",
        "session_id",
    ]:
        op.drop_index(op.f(f"ix_product_events_{column}"), table_name="product_events")
    op.drop_table("product_events")

    op.drop_column("ad_match_adjudications", "future_improvement_tags")
