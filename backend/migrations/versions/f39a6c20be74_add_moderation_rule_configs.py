"""add moderation rule configs

Revision ID: f39a6c20be74
Revises: e7c18a45d2f1
Create Date: 2026-07-17 00:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f39a6c20be74"
down_revision: Union[str, None] = "e7c18a45d2f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "moderation_rule_configs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("enabled_risk_types", sa.JSON(), nullable=False),
        sa.Column("auto_limit_min_risk_level", sa.Integer(), nullable=False),
        sa.Column("manual_review_min_risk_level", sa.Integer(), nullable=False),
        sa.Column("min_confidence", sa.Float(), nullable=False),
        sa.Column("require_grounded_evidence", sa.Boolean(), nullable=False),
        sa.Column("route_divergence_to_manual", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_moderation_rule_configs_is_active"), "moderation_rule_configs", ["is_active"], unique=False)
    op.create_index(op.f("ix_moderation_rule_configs_version"), "moderation_rule_configs", ["version"], unique=True)


def downgrade() -> None:
    op.drop_table("moderation_rule_configs")
