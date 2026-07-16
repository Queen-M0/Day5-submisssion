from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.models import Appeal, Content, Topic
from app.services.auth_service import demo_user_id, get_current_user
from app.services.serializers import content_dict


router = APIRouter(prefix="/me", tags=["me"])


@router.get("/contents")
def list_my_contents(
    status: Optional[str] = None,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    statement = (
        select(Content)
        .options(
            joinedload(Content.author),
            joinedload(Content.parent).joinedload(Content.author),
            joinedload(Content.topic).joinedload(Topic.author),
            selectinload(Content.moderation_records),
        )
        .where(Content.author_id == user.id)
    )
    if status:
        statement = statement.where(Content.status == status)
    contents = db.scalars(statement.order_by(Content.created_at.desc())).unique().all()
    active_appeals = {
        appeal.content_id
        for appeal in db.scalars(
            select(Appeal).where(Appeal.user_id == user.id, Appeal.status.in_(["submitted", "reviewing"]))
        ).all()
    }
    items = []
    for content in contents:
        value = content_dict(content, user.id)
        value["topic"] = {
            "id": content.topic.id,
            "title": content.topic.title,
            "category": content.topic.category,
        }
        value["appealable"] = (
            content.status in {"limited", "pending_manual_review", "need_more_context"}
            and content.id not in active_appeals
        )
        items.append(value)
    return {"items": items}
