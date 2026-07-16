from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.models import Appeal, AuditLog, Content, ManualReview, Topic, User
from app.schemas.requests import ReviewDecisionRequest
from app.services.auth_service import demo_user_id, get_current_user, require_reviewer
from app.services.serializers import content_dict, iso_utc, moderation_summary, topic_dict
from app.services.topic_service import hide_content, publish_content


router = APIRouter(prefix="/reviewer", tags=["reviewer"])


def task_id_for(content: Content, appeal: Optional[Appeal]) -> str:
    return f"appeal__{appeal.id}" if appeal else f"content__{content.id}"


def content_options():
    return (
        joinedload(Content.author),
        joinedload(Content.parent).joinedload(Content.author),
        joinedload(Content.topic).options(
            joinedload(Topic.author),
            selectinload(Topic.contents).joinedload(Content.author),
        ),
        selectinload(Content.moderation_records),
    )


def load_content(db: Session, content_id: str) -> Optional[Content]:
    return db.scalar(select(Content).options(*content_options()).where(Content.id == content_id))


def resolve_task(db: Session, task_id: str) -> Tuple[Content, Optional[Appeal]]:
    appeal: Optional[Appeal] = None
    if task_id.startswith("appeal__"):
        appeal = db.get(Appeal, task_id.removeprefix("appeal__"))
        content_id = appeal.content_id if appeal else ""
    elif task_id.startswith("content__"):
        content_id = task_id.removeprefix("content__")
    else:
        content_id = ""
    content = load_content(db, content_id) if content_id else None
    if not content:
        raise HTTPException(status_code=404, detail="复核任务不存在")
    return content, appeal


def task_summary(
    content: Content,
    appeal: Optional[Appeal],
    review: Optional[ManualReview] = None,
) -> Dict[str, Any]:
    record = content.moderation_records[-1] if content.moderation_records else None
    source = "user_appeal" if appeal else "ai_escalation"
    value = {
        "taskId": task_id_for(content, appeal),
        "contentId": content.id,
        "appealId": appeal.id if appeal else None,
        "source": source,
        "priority": "high" if appeal else "normal",
        "status": "resolved" if review else "pending",
        "topicTitle": content.topic.title,
        "contentText": content.text,
        "authorName": content.author.display_name,
        "riskLevel": record.risk_level if record else 0,
        "riskScore": record.risk_score if record else 0,
        "riskTypes": (record.risk_types or []) if record else [],
        "contextTags": (record.context_tags or []) if record else [],
        "evidenceCount": len(record.evidence or []) if record else 0,
        "createdAt": iso_utc(appeal.created_at if appeal else content.created_at),
    }
    if review:
        value.update(
            {
                "resolvedAt": iso_utc(review.created_at),
                "finalDecision": review.final_decision,
                "reviewReason": review.review_reason,
            }
        )
    return value


@router.get("/tasks")
def list_tasks(
    status: Literal["pending", "resolved"] = "pending",
    source: Optional[Literal["ai_escalation", "user_appeal"]] = None,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    require_reviewer(user)
    tasks: List[Dict[str, Any]] = []

    if status == "resolved":
        reviews = db.scalars(select(ManualReview).order_by(ManualReview.created_at.desc())).all()
        for review in reviews:
            appeal = db.get(Appeal, review.appeal_id) if review.appeal_id else None
            if source and source != ("user_appeal" if appeal else "ai_escalation"):
                continue
            content = load_content(db, review.content_id)
            if content:
                tasks.append(task_summary(content, appeal, review))
        return {"items": tasks}

    reviewed_content_ids = set(db.scalars(select(ManualReview.content_id)).all())
    appeals = db.scalars(
        select(Appeal)
        .options(joinedload(Appeal.content).options(*content_options()))
        .where(Appeal.status.in_(["submitted", "reviewing"]))
        .order_by(Appeal.created_at)
    ).unique().all()
    appealed_content_ids = {appeal.content_id for appeal in appeals}
    if source in {None, "user_appeal"}:
        for appeal in appeals:
            if appeal.content_id not in reviewed_content_ids:
                tasks.append(task_summary(appeal.content, appeal))

    if source in {None, "ai_escalation"}:
        manual_contents = db.scalars(
            select(Content)
            .options(*content_options())
            .where(Content.status == "pending_manual_review")
            .order_by(Content.created_at)
        ).unique().all()
        for content in manual_contents:
            if content.id not in appealed_content_ids and content.id not in reviewed_content_ids:
                tasks.append(task_summary(content, None))
    tasks.sort(key=lambda item: (item["priority"] != "high", item["createdAt"]))
    return {"items": tasks}


def timeline_items(db: Session, content_id: str) -> List[Dict[str, Any]]:
    events = db.scalars(
        select(AuditLog).where(AuditLog.entity_type == "content", AuditLog.entity_id == content_id).order_by(AuditLog.created_at)
    ).all()
    actor_ids = {event.actor_id for event in events if event.actor_id != "system"}
    actors = {user.id: user.display_name for user in db.scalars(select(User).where(User.id.in_(actor_ids))).all()} if actor_ids else {}
    return [
        {
            "id": event.id,
            "actor": "系统" if event.actor_id == "system" else actors.get(event.actor_id, "社区用户"),
            "action": event.action,
            "description": event.detail.get("description", ""),
            "createdAt": iso_utc(event.created_at),
        }
        for event in events
    ]


@router.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    require_reviewer(user)
    content, appeal = resolve_task(db, task_id)
    context_items = db.scalars(
        select(Content)
        .options(*content_options())
        .where(
            Content.topic_id == content.topic_id,
            Content.created_at <= content.created_at,
            or_(Content.visible_to_public.is_(True), Content.id == content.id),
        )
        .order_by(Content.created_at.desc())
        .limit(6)
    ).unique().all()
    record = content.moderation_records[-1] if content.moderation_records else None
    return {
        "taskId": task_id,
        "topic": topic_dict(content.topic),
        "content": content_dict(content, user.id, detailed=True),
        "replyTo": content_dict(content.parent, user.id, detailed=True) if content.parent else None,
        "context": [content_dict(item, user.id, detailed=True) for item in reversed(context_items) if item.id != content.id],
        "moderation": moderation_summary(record, detailed=True),
        "evidenceValidation": {
            "valid": record.evidence_valid if record else False,
            "items": record.evidence if record else [],
        },
        "appeal": None
        if not appeal
        else {
            "id": appeal.id,
            "appealType": appeal.appeal_type,
            "reason": appeal.reason,
            "extraContext": appeal.extra_context,
            "status": appeal.status,
            "createdAt": iso_utc(appeal.created_at),
        },
        "counterAnalysis": appeal.counter_analysis or None if appeal else None,
        "timeline": timeline_items(db, content.id),
    }


@router.post("/tasks/{task_id}/decision")
def decide_task(
    task_id: str,
    payload: ReviewDecisionRequest,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    require_reviewer(user)
    content, appeal = resolve_task(db, task_id)
    if db.scalar(select(ManualReview).where(ManualReview.content_id == content.id)):
        raise HTTPException(status_code=409, detail="该任务已完成复核")

    record = content.moderation_records[-1] if content.moderation_records else None
    if payload.final_decision == "allow":
        publish_content(db, content, restored=appeal is not None)
        appeal_status = "approved"
    elif payload.final_decision == "maintain_limit":
        hide_content(content, "appeal_rejected" if appeal else "limited")
        appeal_status = "rejected"
    else:
        hide_content(content, "need_more_context")
        appeal_status = "need_more_context"
    if appeal:
        appeal.status = appeal_status

    review = ManualReview(
        id=str(uuid4()),
        appeal_id=appeal.id if appeal else None,
        content_id=content.id,
        reviewer_id=user.id,
        original_decision=record.system_decision if record else "manual_review",
        final_decision=payload.final_decision,
        final_risk_level=payload.final_risk_level if payload.final_risk_level is not None else (0 if payload.final_decision == "allow" else (record.risk_level if record else None)),
        review_reason=payload.review_reason.strip(),
        correction_type=payload.correction_type,
    )
    db.add(review)
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=user.id,
            action="manual_review.decided",
            entity_type="content",
            entity_id=content.id,
            detail={
                "taskId": task_id,
                "finalDecision": payload.final_decision,
                "description": payload.review_reason.strip(),
            },
        )
    )
    followup_action = {
        "allow": "content.restored" if appeal else "content.published",
        "maintain_limit": "content.limited",
        "need_more_context": "context.requested",
    }[payload.final_decision]
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id="system",
            action=followup_action,
            entity_type="content",
            entity_id=content.id,
            detail={"status": content.status, "floorNumber": content.floor_number},
        )
    )
    db.commit()
    reviewed_at = datetime.now(timezone.utc)
    return {
        "success": True,
        "contentStatus": content.status,
        "appealStatus": appeal.status if appeal else None,
        "floorNumber": content.floor_number,
        "visibleToPublic": content.visible_to_public,
        "reviewedAt": reviewed_at,
    }
