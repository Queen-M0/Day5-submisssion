from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Content
from app.providers.ai_provider import ContextMessage, ModerationInput


class ContextService:
    def build(self, db: Session, content: Content) -> ModerationInput:
        messages: List[Content] = list(
            db.scalars(
                select(Content)
                .options(joinedload(Content.author))
                .where(
                    Content.topic_id == content.topic_id,
                    Content.visible_to_public.is_(True),
                    Content.created_at < content.created_at,
                )
                .order_by(Content.created_at.desc())
                .limit(5)
            ).all()
        )
        messages.reverse()
        context = [
            ContextMessage(
                id=item.id,
                author_id=item.author_id,
                author_name=item.author.display_name,
                text=item.text,
                parent_id=item.parent_id,
            )
            for item in messages
        ]
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
            messages=context,
        )
