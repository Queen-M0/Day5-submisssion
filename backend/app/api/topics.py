from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.dependencies import moderation_service
from app.core.database import get_db
from app.models import AuditLog, Content, Scene, Topic
from app.schemas.requests import CreateTopicContentRequest, CreateTopicRequest
from app.services.auth_service import demo_user_id, get_current_user
from app.services.serializers import content_dict, moderation_summary, topic_dict
from app.services.text_service import normalize_text


router = APIRouter(prefix="/topics", tags=["topics"])


def topic_options():
    return (
        joinedload(Topic.author),
        selectinload(Topic.contents).joinedload(Content.author),
        selectinload(Topic.contents).selectinload(Content.moderation_records),
    )


def load_topic(db: Session, topic_id: str) -> Optional[Topic]:
    return db.scalar(select(Topic).options(*topic_options()).where(Topic.id == topic_id))


def require_topic_access(topic: Topic, user_id: str, role: str) -> None:
    if not topic.visible_to_public and topic.author_id != user_id and role not in {"reviewer", "admin"}:
        raise HTTPException(status_code=404, detail="话题不存在")


def content_options():
    return (
        joinedload(Content.author),
        joinedload(Content.parent).joinedload(Content.author),
        joinedload(Content.topic).joinedload(Topic.author),
        selectinload(Content.moderation_records),
    )


def creation_response(content: Content):
    record = content.moderation_records[-1] if content.moderation_records else None
    return {
        "contentId": content.id,
        "status": content.status,
        "floorNumber": content.floor_number,
        "visibleToPublic": content.visible_to_public,
        "moderation": moderation_summary(record),
    }


@router.get("")
def list_topics(
    category: Optional[str] = None,
    q: Optional[str] = Query(default=None, max_length=100),
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    statement = select(Topic).options(*topic_options())
    if user.role not in {"reviewer", "admin"}:
        statement = statement.where(Topic.visible_to_public.is_(True))
    if category:
        statement = statement.where(Topic.category == category)
    if q and q.strip():
        keyword = f"%{q.strip()}%"
        statement = statement.where(or_(Topic.title.like(keyword), Topic.summary.like(keyword)))
    topics = db.scalars(statement.order_by(Topic.last_active_at.desc())).unique().all()
    return {"items": [topic_dict(topic) for topic in topics]}


@router.post("", status_code=201)
def create_topic(
    payload: CreateTopicRequest,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    if user.role != "user":
        raise HTTPException(status_code=403, detail="请切换到普通用户发起话题")
    scene = db.scalar(select(Scene).where(Scene.type == "community").order_by(Scene.created_at))
    if not scene:
        raise HTTPException(status_code=404, detail="固定社区不存在")

    topic = Topic(
        id=str(uuid4()),
        scene_id=scene.id,
        author_id=user.id,
        title=payload.title.strip(),
        summary=payload.body.strip()[:255],
        category=payload.category.strip(),
        status="pending_ai_review",
        visible_to_public=False,
        view_count=0,
    )
    db.add(topic)
    db.flush()
    content = Content(
        id=str(uuid4()),
        scene_id=scene.id,
        topic_id=topic.id,
        content_type="topic_root",
        author_id=user.id,
        text=payload.body.strip(),
        normalized_text=normalize_text(payload.body),
        status="pending_ai_review",
        visible_to_public=False,
    )
    db.add(content)
    db.flush()
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=user.id,
            action="content.submitted",
            entity_type="content",
            entity_id=content.id,
            detail={"topicId": topic.id, "contentType": "topic_root"},
        )
    )
    moderation_service.review(db, content)
    db.commit()
    db.refresh(content)
    return {"topicId": topic.id, **creation_response(content)}


@router.get("/{topic_id}")
def get_topic(
    topic_id: str,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    topic = load_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    require_topic_access(topic, user.id, user.role)
    topic.view_count += 1
    db.commit()
    return topic_dict(topic)


@router.get("/{topic_id}/contents")
def list_topic_contents(
    topic_id: str,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    require_topic_access(topic, user.id, user.role)
    statement = select(Content).options(*content_options()).where(Content.topic_id == topic.id)
    if user.role not in {"reviewer", "admin"}:
        statement = statement.where(or_(Content.visible_to_public.is_(True), Content.author_id == user.id))
    contents = db.scalars(statement.order_by(Content.created_at)).unique().all()
    detailed = user.role in {"reviewer", "admin"}
    return {"items": [content_dict(item, user.id, detailed=detailed) for item in contents]}


@router.post("/{topic_id}/contents", status_code=201)
def create_topic_content(
    topic_id: str,
    payload: CreateTopicContentRequest,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    if user.role != "user":
        raise HTTPException(status_code=403, detail="请切换到普通用户发布内容")
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    require_topic_access(topic, user.id, user.role)
    if not topic.visible_to_public:
        raise HTTPException(status_code=409, detail="话题 1 楼通过审核后才能继续发布楼层")

    parent = None
    if payload.reply_to_content_id:
        parent = db.get(Content, payload.reply_to_content_id)
        if (
            not parent
            or parent.topic_id != topic.id
            or (not parent.visible_to_public and parent.author_id != user.id)
        ):
            raise HTTPException(status_code=400, detail="回复楼层不存在")
    content = Content(
        id=str(uuid4()),
        scene_id=topic.scene_id,
        topic_id=topic.id,
        content_type="forum_reply",
        author_id=user.id,
        parent_id=parent.id if parent else None,
        target_user_id=parent.author_id if parent else None,
        text=payload.text.strip(),
        normalized_text=normalize_text(payload.text),
        status="pending_ai_review",
        visible_to_public=False,
    )
    db.add(content)
    db.flush()
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=user.id,
            action="content.submitted",
            entity_type="content",
            entity_id=content.id,
            detail={"topicId": topic.id, "replyToContentId": content.parent_id},
        )
    )
    moderation_service.review(db, content)
    db.commit()
    db.refresh(content)
    return creation_response(content)
