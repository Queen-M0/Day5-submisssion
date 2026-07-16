from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(20), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(30), default="forum_thread")
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    contents: Mapped[List["Content"]] = relationship(back_populates="scene")
    topics: Mapped[List["Topic"]] = relationship(back_populates="scene")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str] = mapped_column(ForeignKey("scenes.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending_ai_review", index=True)
    visible_to_public: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    scene: Mapped[Scene] = relationship(back_populates="topics")
    author: Mapped[User] = relationship(foreign_keys=[author_id])
    contents: Mapped[List["Content"]] = relationship(back_populates="topic")


class Content(Base):
    __tablename__ = "contents"
    __table_args__ = (UniqueConstraint("topic_id", "floor_number", name="uq_contents_topic_floor"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str] = mapped_column(ForeignKey("scenes.id"), index=True)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), index=True)
    floor_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str] = mapped_column(String(30), default="forum_reply")
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("contents.id"), nullable=True)
    target_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending_ai_review", index=True)
    visible_to_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    scene: Mapped[Scene] = relationship(back_populates="contents")
    topic: Mapped[Topic] = relationship(back_populates="contents")
    author: Mapped[User] = relationship(foreign_keys=[author_id])
    parent: Mapped[Optional["Content"]] = relationship(remote_side=[id])
    target_user: Mapped[Optional[User]] = relationship(foreign_keys=[target_user_id])
    moderation_records: Mapped[List["ModerationRecord"]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )


class ModerationRecord(Base):
    __tablename__ = "moderation_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("contents.id"), index=True)
    provider: Mapped[str] = mapped_column(String(40))
    prompt_version: Mapped[str] = mapped_column(String(30), default="mock-v1")
    risk_level: Mapped[int] = mapped_column(Integer)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_types: Mapped[List[str]] = mapped_column(JSON, default=list)
    decision: Mapped[str] = mapped_column(String(30))
    suggested_action: Mapped[str] = mapped_column(String(30), default="manual_review")
    system_decision: Mapped[str] = mapped_column(String(30), default="manual_review")
    confidence: Mapped[float] = mapped_column(Float)
    evidence: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    evidence_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    context_tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    intent: Mapped[str] = mapped_column(Text, default="")
    target_user_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    context_used: Mapped[List[str]] = mapped_column(JSON, default=list)
    uncertainties: Mapped[List[str]] = mapped_column(JSON, default=list)
    context_summary: Mapped[str] = mapped_column(Text, default="")
    user_visible_reason: Mapped[str] = mapped_column(Text)
    reviewer_reason: Mapped[str] = mapped_column(Text)
    raw_ai_response: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    model_version: Mapped[str] = mapped_column(String(50), default="mock-rules-v1")
    rule_version: Mapped[str] = mapped_column(String(30), default="community-v1")
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    content: Mapped[Content] = relationship(back_populates="moderation_records")


class Appeal(Base):
    __tablename__ = "appeals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("contents.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    appeal_type: Mapped[str] = mapped_column(String(40), default="other")
    reason: Mapped[str] = mapped_column(Text)
    extra_context: Mapped[str] = mapped_column(Text, default="")
    counter_analysis: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="submitted", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    content: Mapped[Content] = relationship()
    user: Mapped[User] = relationship()


class ManualReview(Base):
    __tablename__ = "manual_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    appeal_id: Mapped[Optional[str]] = mapped_column(ForeignKey("appeals.id"), nullable=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("contents.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    original_decision: Mapped[str] = mapped_column(String(30))
    final_decision: Mapped[str] = mapped_column(String(30))
    final_risk_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_reason: Mapped[str] = mapped_column(Text)
    correction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    detail: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
