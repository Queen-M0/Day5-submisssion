from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.dependencies import moderation_service
from app.core.database import get_db
from app.models import AuditLog, Content, Scene
from app.schemas.requests import CreateContentRequest
from app.services.auth_service import demo_user_id, get_current_user
from app.services.serializers import content_dict, moderation_summary
from app.services.text_service import normalize_text


router = APIRouter(prefix="/contents", tags=["contents"])


@router.post("", status_code=201)
def create_content(
    payload: CreateContentRequest,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    if user.role != "user":
        raise HTTPException(status_code=403, detail="请切换到普通用户发布内容")
    if not db.get(Scene, payload.scene_id):
        raise HTTPException(status_code=404, detail="讨论区不存在")
    if payload.parent_id and not db.get(Content, payload.parent_id):
        raise HTTPException(status_code=400, detail="引用的楼层不存在")

    content = Content(
        id=str(uuid4()),
        scene_id=payload.scene_id,
        content_type=payload.content_type,
        author_id=user.id,
        parent_id=payload.parent_id,
        text=payload.text.strip(),
        normalized_text=normalize_text(payload.text),
        status="pending_ai_review",
        visible_to_public=False,
    )
    db.add(content)
    db.flush()
    db.refresh(content, attribute_names=["author", "parent"])
    result = moderation_service.review(db, content)
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=user.id,
            action="content.moderated",
            entity_type="content",
            entity_id=content.id,
            detail={"decision": result.decision, "riskLevel": result.risk_level},
        )
    )
    db.commit()
    return {
        "contentId": content.id,
        "status": content.status,
        "decision": result.decision,
        "riskLevel": result.risk_level,
        "userVisibleReason": result.user_visible_reason,
    }


@router.get("/{content_id}/moderation")
def get_moderation(
    content_id: str,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    content = (
        db.query(Content)
        .options(joinedload(Content.author), selectinload(Content.moderation_records))
        .filter(Content.id == content_id)
        .one_or_none()
    )
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    if content.author_id != user.id and user.role not in {"reviewer", "admin"}:
        raise HTTPException(status_code=403, detail="无权查看该审核详情")
    record = content.moderation_records[-1] if content.moderation_records else None
    data = moderation_summary(record, detailed=user.role in {"reviewer", "admin"}) or {}
    return {
        "contentId": content.id,
        "status": content.status,
        **data,
        "appealable": content.author_id == user.id and content.status in {"limited", "pending_manual_review"},
    }
