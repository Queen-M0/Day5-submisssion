"""add appeal analysis records

Revision ID: b62d91f47e30
Revises: c2417b9a6e12
Create Date: 2026-07-16 19:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b62d91f47e30"
down_revision: Union[str, None] = "c2417b9a6e12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appeal_analysis_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("appeal_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("evidence_valid", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["appeal_id"], ["appeals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_appeal_analysis_records_appeal_id"),
        "appeal_analysis_records",
        ["appeal_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_appeal_analysis_records_appeal_id"), table_name="appeal_analysis_records")
    op.drop_table("appeal_analysis_records")
