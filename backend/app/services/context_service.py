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
                .where(Content.scene_id == content.scene_id, Content.created_at <= content.created_at)
                .order_by(Content.created_at.desc())
                .limit(11)
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
            if item.id != content.id
        ]
        parent_text: Optional[str] = content.parent.text if content.parent else None
        return ModerationInput(
            content_id=content.id,
            author_id=content.author_id,
            author_name=content.author.display_name,
            text=content.text,
            parent_text=parent_text,
            messages=context,
        )

