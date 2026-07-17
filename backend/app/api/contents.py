from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.dependencies import moderation_service
from app.core.database import get_db
from app.models import AuditLog, Content, Scene, Topic, User
from app.schemas.requests import CreateContentRequest
from app.services.auth_service import demo_user_id, get_current_user
from app.services.serializers import content_dict, iso_utc, moderation_summary
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
    parent = db.get(Content, payload.parent_id) if payload.parent_id else None
    if payload.parent_id and (
        not parent
        or parent.scene_id != payload.scene_id
        or (not parent.visible_to_public and parent.author_id != user.id)
    ):
        raise HTTPException(status_code=400, detail="引用的楼层不存在")
    topic = parent.topic if parent else db.scalar(
        select(Topic).where(Topic.scene_id == payload.scene_id, Topic.visible_to_public.is_(True)).order_by(Topic.created_at)
    )
    if not topic:
        raise HTTPException(status_code=409, detail="请先通过话题接口发起话题")

    content = Content(
        id=str(uuid4()),
        scene_id=payload.scene_id,
        topic_id=topic.id,
        content_type=payload.content_type,
        author_id=user.id,
        parent_id=payload.parent_id,
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
            detail={"topicId": topic.id, "legacyEndpoint": True},
        )
    )
    result = moderation_service.review(db, content)
    db.commit()
    record = content.moderation_records[-1] if content.moderation_records else None
    return {
        "contentId": content.id,
        "status": content.status,
        "decision": record.system_decision if record else result.decision,
        "riskLevel": result.risk_level,
        "floorNumber": content.floor_number,
        "visibleToPublic": content.visible_to_public,
        "moderation": moderation_summary(record),
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


TIMELINE_COPY = {
    "content.submitted": ("提交内容", "内容进入发布前审核"),
    "moderation.context_built": ("构建审核上下文", "已读取话题、回复对象和最近公开楼层"),
    "moderation.completed": ("上下文审核完成", "系统已保存审核建议和分流结果"),
    "moderation.failed": ("审核异常", "内容已转入人工复核"),
    "moderation.dual_review_completed": ("双模型一致性检查完成", "主模型与辅助模型判断一致"),
    "moderation.divergence_detected": ("检测到双模型分歧", "内容已转入人工复核"),
    "moderation.dual_review_failed": ("辅助模型检查异常", "双模型检查未完成，内容已转人工"),
    "evidence.validated": ("证据真实性校验", "引用片段和证据定位已完成"),
    "content.published": ("内容已公开", "内容已分配公开楼层号"),
    "content.limited": ("内容暂时限制", "内容未公开，可由作者发起申诉"),
    "content.manual_review_requested": ("转人工复核", "内容暂不公开，等待审核员判断"),
    "appeal.submitted": ("提交申诉", "作者已补充理由和上下文"),
    "appeal.counter_analyzed": ("申诉反证分析完成", "正反依据已提交给审核员"),
    "appeal.counter_analysis_failed": ("申诉反证分析异常", "系统已安全转交人工复核"),
    "appeal.context_supplemented": ("补充申诉上下文", "作者已提交新的上下文材料"),
    "manual_review.decided": ("人工复核完成", "审核员已提交最终决定"),
    "content.restored": ("内容恢复公开", "内容已追加到最新公开楼层"),
    "context.requested": ("要求补充上下文", "内容保持非公开状态"),
}


@router.get("/{content_id}/timeline")
def get_timeline(
    content_id: str,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    content = db.get(Content, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    if not content.visible_to_public and content.author_id != user.id and user.role not in {"reviewer", "admin"}:
        raise HTTPException(status_code=403, detail="无权查看该处理时间线")
    events = db.scalars(
        select(AuditLog).where(AuditLog.entity_type == "content", AuditLog.entity_id == content.id).order_by(AuditLog.created_at)
    ).all()
    actor_ids = {event.actor_id for event in events if event.actor_id != "system"}
    actors = {item.id: item.display_name for item in db.scalars(select(User).where(User.id.in_(actor_ids))).all()} if actor_ids else {}
    return {
        "items": [
            {
                "id": event.id,
                "actor": "系统" if event.actor_id == "system" else actors.get(event.actor_id, "社区用户"),
                "action": event.action,
                "title": TIMELINE_COPY.get(event.action, (event.action, ""))[0],
                "description": event.detail.get("description") or TIMELINE_COPY.get(event.action, ("", ""))[1],
                "createdAt": iso_utc(event.created_at),
            }
            for event in events
        ]
    }
