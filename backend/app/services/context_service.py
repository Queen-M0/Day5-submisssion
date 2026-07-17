from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Content
from app.providers.ai_provider import ContextMessage, ModerationInput


class ContextService:
    @staticmethod
    def _to_messages(items: List[Content]) -> List[ContextMessage]:
        return [
            ContextMessage(
                id=item.id,
                author_id=item.author_id,
                author_name=item.author.display_name,
                text=item.text,
                parent_id=item.parent_id,
            )
            for item in items
        ]

    @staticmethod
    def _recent(db: Session, *conditions) -> List[Content]:
        items = list(
            db.scalars(
                select(Content)
                .options(joinedload(Content.author))
                .where(Content.visible_to_public.is_(True), *conditions)
                .order_by(Content.created_at.desc())
                .limit(5)
            ).all()
        )
        items.reverse()
        return items

    def build(self, db: Session, content: Content) -> ModerationInput:
        messages = self._recent(
            db,
            Content.topic_id == content.topic_id,
            Content.created_at < content.created_at,
        )
        author_history = self._recent(
            db,
            Content.scene_id == content.scene_id,
            Content.author_id == content.author_id,
            Content.created_at < content.created_at,
        )
        target_id = content.target_user_id or (content.parent.author_id if content.parent else None)
        target_history = (
            self._recent(
                db,
                Content.scene_id == content.scene_id,
                Content.created_at < content.created_at,
                or_(Content.author_id == target_id, Content.target_user_id == target_id),
            )
            if target_id
            else []
        )
        parent_text: Optional[str] = content.parent.text if content.parent else None
        return ModerationInput(
            content_id=content.id,
            author_id=content.author_id,
            author_name=content.author.display_name,
            text=content.text,
            parent_text=parent_text,
            topic_title=content.topic.title,
            parent_id=content.parent_id,
            parent_author_id=content.parent.author_id if content.parent else None,
            messages=self._to_messages(messages),
            author_history=self._to_messages(author_history),
            target_history=self._to_messages(target_history),
        )
