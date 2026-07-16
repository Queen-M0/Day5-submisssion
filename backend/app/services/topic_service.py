from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Content, Topic


def publish_content(db: Session, content: Content, restored: bool = False) -> int:
    topic = db.scalar(select(Topic).where(Topic.id == content.topic_id).with_for_update())
    if not topic:
        raise ValueError("content topic does not exist")
    if content.floor_number is None:
        current_max = db.scalar(select(func.max(Content.floor_number)).where(Content.topic_id == topic.id)) or 0
        content.floor_number = current_max + 1
    content.status = "appeal_approved" if restored else "published"
    content.visible_to_public = True
    topic.last_active_at = datetime.now(timezone.utc)
    if content.content_type == "topic_root":
        topic.status = content.status
        topic.visible_to_public = True
    return content.floor_number


def hide_content(content: Content, status: str) -> None:
    content.status = status
    content.visible_to_public = False
    content.floor_number = None
    if content.content_type == "topic_root":
        content.topic.status = status
        content.topic.visible_to_public = False
