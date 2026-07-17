"""add moderation comparisons

Revision ID: e7c18a45d2f1
Revises: b62d91f47e30
Create Date: 2026-07-16 23:50:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7c18a45d2f1"
down_revision: Union[str, None] = "b62d91f47e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "moderation_comparisons",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("content_id", sa.String(length=36), nullable=False),
        sa.Column("primary_record_id", sa.String(length=36), nullable=False),
        sa.Column("secondary_provider", sa.String(length=40), nullable=False),
        sa.Column("secondary_model_version", sa.String(length=80), nullable=False),
        sa.Column("secondary_prompt_version", sa.String(length=40), nullable=False),
        sa.Column("secondary_decision", sa.String(length=30), nullable=False),
        sa.Column("secondary_risk_level", sa.Integer(), nullable=False),
        sa.Column("secondary_risk_types", sa.JSON(), nullable=False),
        sa.Column("secondary_evidence", sa.JSON(), nullable=False),
        sa.Column("secondary_evidence_valid", sa.Boolean(), nullable=False),
        sa.Column("secondary_raw_response", sa.JSON(), nullable=False),
        sa.Column("divergent", sa.Boolean(), nullable=False),
        sa.Column("divergence_reasons", sa.JSON(), nullable=False),
        sa.Column("system_resolution", sa.String(length=30), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"]),
        sa.ForeignKeyConstraint(["primary_record_id"], ["moderation_records.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("primary_record_id"),
    )
    op.create_index(op.f("ix_moderation_comparisons_content_id"), "moderation_comparisons", ["content_id"], unique=False)
    op.create_index(op.f("ix_moderation_comparisons_divergent"), "moderation_comparisons", ["divergent"], unique=False)


def downgrade() -> None:
    op.drop_table("moderation_comparisons")
