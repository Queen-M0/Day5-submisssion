from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.models import Appeal, AuditLog, Content, ManualReview
from app.schemas.requests import ReviewDecisionRequest
from app.services.auth_service import demo_user_id, get_current_user, require_reviewer
from app.services.serializers import content_dict, iso_utc, moderation_summary


router = APIRouter(prefix="/reviewer", tags=["reviewer"])


def task_id_for(content: Content, appeal: Optional[Appeal]) -> str:
    return f"appeal__{appeal.id}" if appeal else f"content__{content.id}"


def resolve_task(db: Session, task_id: str) -> Tuple[Content, Optional[Appeal]]:
    appeal: Optional[Appeal] = None
    content_id = ""
    if task_id.startswith("appeal__"):
        appeal = db.get(Appeal, task_id.removeprefix("appeal__"))
        if not appeal:
            raise HTTPException(status_code=404, detail="复核任务不存在")
        content_id = appeal.content_id
    elif task_id.startswith("content__"):
        content_id = task_id.removeprefix("content__")
    content = (
        db.query(Content)
        .options(
            joinedload(Content.author),
            joinedload(Content.parent).joinedload(Content.author),
            selectinload(Content.moderation_records),
        )
        .filter(Content.id == content_id)
        .one_or_none()
    )
    if not content:
        raise HTTPException(status_code=404, detail="复核任务不存在")
    return content, appeal


@router.get("/tasks")
def list_tasks(
    status: str = "pending",
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    require_reviewer(user)
    tasks: List[Dict[str, Any]] = []

    appeals = db.scalars(
        select(Appeal)
        .options(
            joinedload(Appeal.content).joinedload(Content.author),
            joinedload(Appeal.content).selectinload(Content.moderation_records),
        )
        .where(Appeal.status.in_(["submitted", "reviewing"]))
        .order_by(Appeal.created_at)
    ).all()
    appealed_content_ids = {appeal.content_id for appeal in appeals}
    for appeal in appeals:
        tasks.append(task_summary(appeal.content, appeal))

    manual_contents = db.scalars(
        select(Content)
        .options(joinedload(Content.author), selectinload(Content.moderation_records))
        .where(Content.status == "pending_manual_review")
        .order_by(Content.created_at)
    ).all()
    for content in manual_contents:
        if content.id not in appealed_content_ids:
            tasks.append(task_summary(content, None))
    return {"items": tasks}


def task_summary(content: Content, appeal: Optional[Appeal]) -> Dict[str, Any]:
    record = content.moderation_records[-1] if content.moderation_records else None
    return {
        "taskId": task_id_for(content, appeal),
        "contentId": content.id,
        "appealId": appeal.id if appeal else None,
        "contentText": content.text,
        "authorName": content.author.display_name,
        "riskLevel": record.risk_level if record else 0,
        "riskTypes": record.risk_types if record else [],
        "decision": record.decision if record else "manual_review",
        "hasAppeal": appeal is not None,
        "createdAt": iso_utc(appeal.created_at if appeal else content.created_at),
        "summary": record.reviewer_reason if record else "等待人工判断",
    }


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
        .options(joinedload(Content.author), selectinload(Content.moderation_records))
        .where(Content.scene_id == content.scene_id, Content.created_at <= content.created_at)
        .order_by(Content.created_at.desc())
        .limit(10)
    ).all()
    record = content.moderation_records[-1] if content.moderation_records else None
    return {
        "taskId": task_id,
        "content": content_dict(content, user.id, detailed=True),
        "context": [content_dict(item, user.id, detailed=False) for item in reversed(context_items)],
        "moderation": moderation_summary(record, detailed=True),
        "appeal": None
        if not appeal
        else {
            "id": appeal.id,
            "appealType": appeal.appeal_type,
            "reason": appeal.reason,
            "status": appeal.status,
            "createdAt": iso_utc(appeal.created_at),
        },
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
    allowed = {"maintain_limit", "publish", "require_edit", "escalate", "no_action"}
    if payload.final_decision not in allowed:
        raise HTTPException(status_code=422, detail="不支持的复核结论")
    if db.scalar(select(ManualReview).where(ManualReview.content_id == content.id)):
        raise HTTPException(status_code=409, detail="该任务已完成复核")

    record = content.moderation_records[-1] if content.moderation_records else None
    if payload.final_decision in {"publish", "no_action"}:
        content.status = "published"
        content.visible_to_public = True
        appeal_status = "approved"
    elif payload.final_decision == "require_edit":
        content.status = "appeal_rejected" if appeal else "limited"
        content.visible_to_public = False
        appeal_status = "rejected"
    else:
        content.status = "appeal_rejected" if appeal else "limited"
        content.visible_to_public = False
        appeal_status = "rejected"
    if appeal:
        appeal.status = appeal_status

    review = ManualReview(
        id=str(uuid4()),
        appeal_id=appeal.id if appeal else None,
        content_id=content.id,
        reviewer_id=user.id,
        original_decision=record.decision if record else "manual_review",
        final_decision=payload.final_decision,
        final_risk_level=payload.final_risk_level,
        review_reason=payload.review_reason,
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
                "correctionType": payload.correction_type,
            },
        )
    )
    db.commit()
    return {
        "success": True,
        "contentStatus": content.status,
        "appealStatus": appeal.status if appeal else None,
        "reviewedAt": datetime.now(timezone.utc),
    }
