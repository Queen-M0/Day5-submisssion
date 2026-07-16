"""add topics and review contract

Revision ID: c2417b9a6e12
Revises: 08f687c751fd
Create Date: 2026-07-16 16:30:00
"""

from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "c2417b9a6e12"
down_revision: Union[str, None] = "08f687c751fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scene_id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("visible_to_public", sa.Boolean(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_topics_author_id"), "topics", ["author_id"], unique=False)
    op.create_index(op.f("ix_topics_category"), "topics", ["category"], unique=False)
    op.create_index(op.f("ix_topics_last_active_at"), "topics", ["last_active_at"], unique=False)
    op.create_index(op.f("ix_topics_scene_id"), "topics", ["scene_id"], unique=False)
    op.create_index(op.f("ix_topics_status"), "topics", ["status"], unique=False)

    op.add_column("contents", sa.Column("topic_id", sa.String(length=36), nullable=True))
    op.add_column("contents", sa.Column("floor_number", sa.Integer(), nullable=True))
    op.add_column("contents", sa.Column("target_user_id", sa.String(length=36), nullable=True))

    # Preserve installations that already contain the original single-thread seed.
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT c.scene_id, c.author_id, c.created_at, s.title "
            "FROM contents c JOIN scenes s ON s.id = c.scene_id "
            "ORDER BY c.scene_id, c.created_at"
        )
    ).mappings()
    legacy_topics = {}
    for row in rows:
        if row["scene_id"] in legacy_topics:
            continue
        topic_id = str(uuid4())
        legacy_topics[row["scene_id"]] = topic_id
        created_at = row["created_at"] or datetime.now(timezone.utc)
        connection.execute(
            sa.text(
                "INSERT INTO topics "
                "(id, scene_id, author_id, title, summary, category, status, visible_to_public, "
                "view_count, created_at, updated_at, last_active_at) "
                "VALUES (:id, :scene_id, :author_id, :title, :summary, :category, "
                ":status, :visible, 0, :created_at, :created_at, :created_at)"
            ),
            {
                "id": topic_id,
                "scene_id": row["scene_id"],
                "author_id": row["author_id"],
                "title": row["title"],
                "summary": "由旧版讨论区数据迁移生成的话题",
                "category": "历史讨论",
                "status": "published",
                "visible": True,
                "created_at": created_at,
            },
        )

    for scene_id, topic_id in legacy_topics.items():
        connection.execute(
            sa.text("UPDATE contents SET topic_id = :topic_id WHERE scene_id = :scene_id"),
            {"topic_id": topic_id, "scene_id": scene_id},
        )
        public_rows = connection.execute(
            sa.text(
                "SELECT id FROM contents WHERE scene_id = :scene_id AND visible_to_public = :visible "
                "ORDER BY created_at"
            ),
            {"scene_id": scene_id, "visible": True},
        ).mappings()
        for floor_number, content_row in enumerate(public_rows, start=1):
            connection.execute(
                sa.text("UPDATE contents SET floor_number = :floor WHERE id = :id"),
                {"floor": floor_number, "id": content_row["id"]},
            )

    with op.batch_alter_table("contents") as batch_op:
        batch_op.alter_column("topic_id", existing_type=sa.String(length=36), nullable=False)
        batch_op.create_foreign_key("fk_contents_topic_id_topics", "topics", ["topic_id"], ["id"])
        batch_op.create_foreign_key("fk_contents_target_user_id_users", "users", ["target_user_id"], ["id"])
        batch_op.create_unique_constraint("uq_contents_topic_floor", ["topic_id", "floor_number"])
    op.create_index(op.f("ix_contents_topic_id"), "contents", ["topic_id"], unique=False)

    moderation_columns = [
        sa.Column("suggested_action", sa.String(length=30), nullable=True),
        sa.Column("system_decision", sa.String(length=30), nullable=True),
        sa.Column("evidence_valid", sa.Boolean(), nullable=True),
        sa.Column("context_tags", sa.JSON(), nullable=True),
        sa.Column("intent", sa.Text(), nullable=True),
        sa.Column("target_user_ids", sa.JSON(), nullable=True),
        sa.Column("context_used", sa.JSON(), nullable=True),
        sa.Column("uncertainties", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("rule_version", sa.String(length=30), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
    ]
    for column in moderation_columns:
        op.add_column("moderation_records", column)
    connection.execute(
        sa.text(
            "UPDATE moderation_records SET suggested_action = decision, system_decision = decision, "
            "evidence_valid = :valid, context_tags = :empty_json, intent = :empty_text, "
            "target_user_ids = :empty_json, context_used = :empty_json, uncertainties = :empty_json, "
            "model_version = :model_version, rule_version = :rule_version"
        ),
        {
            "valid": True,
            "empty_json": "[]",
            "empty_text": "",
            "model_version": "legacy",
            "rule_version": "legacy",
        },
    )
    with op.batch_alter_table("moderation_records") as batch_op:
        for name, type_ in (
            ("suggested_action", sa.String(length=30)),
            ("system_decision", sa.String(length=30)),
            ("evidence_valid", sa.Boolean()),
            ("context_tags", sa.JSON()),
            ("intent", sa.Text()),
            ("target_user_ids", sa.JSON()),
            ("context_used", sa.JSON()),
            ("uncertainties", sa.JSON()),
            ("model_version", sa.String(length=50)),
            ("rule_version", sa.String(length=30)),
        ):
            batch_op.alter_column(name, existing_type=type_, nullable=False)

    op.add_column("appeals", sa.Column("extra_context", sa.Text(), nullable=True))
    op.add_column("appeals", sa.Column("counter_analysis", sa.JSON(), nullable=True))
    op.add_column("appeals", sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True))
    connection.execute(
        sa.text("UPDATE appeals SET extra_context = :empty_text, counter_analysis = :empty_json"),
        {"empty_text": "", "empty_json": "{}"},
    )
    with op.batch_alter_table("appeals") as batch_op:
        batch_op.alter_column("extra_context", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("counter_analysis", existing_type=sa.JSON(), nullable=False)

    with op.batch_alter_table("manual_reviews") as batch_op:
        batch_op.alter_column("final_risk_level", existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column("correction_type", existing_type=sa.String(length=50), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("manual_reviews") as batch_op:
        batch_op.alter_column("correction_type", existing_type=sa.String(length=50), nullable=False)
        batch_op.alter_column("final_risk_level", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("appeals") as batch_op:
        batch_op.drop_column("analyzed_at")
        batch_op.drop_column("counter_analysis")
        batch_op.drop_column("extra_context")

    with op.batch_alter_table("moderation_records") as batch_op:
        for name in (
            "failure_reason",
            "rule_version",
            "model_version",
            "uncertainties",
            "context_used",
            "target_user_ids",
            "intent",
            "context_tags",
            "evidence_valid",
            "system_decision",
            "suggested_action",
        ):
            batch_op.drop_column(name)

    op.drop_index(op.f("ix_contents_topic_id"), table_name="contents")
    with op.batch_alter_table("contents") as batch_op:
        batch_op.drop_constraint("uq_contents_topic_floor", type_="unique")
        batch_op.drop_constraint("fk_contents_target_user_id_users", type_="foreignkey")
        batch_op.drop_constraint("fk_contents_topic_id_topics", type_="foreignkey")
        batch_op.drop_column("target_user_id")
        batch_op.drop_column("floor_number")
        batch_op.drop_column("topic_id")

    op.drop_index(op.f("ix_topics_status"), table_name="topics")
    op.drop_index(op.f("ix_topics_scene_id"), table_name="topics")
    op.drop_index(op.f("ix_topics_last_active_at"), table_name="topics")
    op.drop_index(op.f("ix_topics_category"), table_name="topics")
    op.drop_index(op.f("ix_topics_author_id"), table_name="topics")
    op.drop_table("topics")
