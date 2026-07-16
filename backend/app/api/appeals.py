from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import Appeal, AuditLog, Content, ManualReview, Topic
from app.schemas.requests import SubmitAppealRequest
from app.services.auth_service import demo_user_id, get_current_user
from app.services.serializers import iso_utc


router = APIRouter(tags=["appeals"])


@router.post("/contents/{content_id}/appeals", status_code=201)
def submit_appeal(
    content_id: str,
    payload: SubmitAppealRequest,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    content = db.get(Content, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    if content.author_id != user.id:
        raise HTTPException(status_code=403, detail="只能申诉自己发布的内容")
    if content.status not in {"limited", "pending_manual_review"}:
        raise HTTPException(status_code=409, detail="当前内容状态不支持申诉")
    existing = db.scalar(
        select(Appeal).where(Appeal.content_id == content_id, Appeal.status.in_(["submitted", "reviewing"]))
    )
    if existing:
        raise HTTPException(status_code=409, detail="该内容已有待处理申诉")

    appeal = Appeal(
        id=str(uuid4()),
        content_id=content.id,
        user_id=user.id,
        appeal_type=payload.appeal_type,
        reason=payload.reason,
        extra_context=payload.extra_context.strip(),
        counter_analysis={},
        status="submitted",
    )
    content.status = "appeal_submitted"
    db.add(appeal)
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=user.id,
            action="appeal.submitted",
            entity_type="content",
            entity_id=content.id,
            detail={"appealId": appeal.id, "appealType": payload.appeal_type},
        )
    )
    db.commit()
    return {
        "appealId": appeal.id,
        "status": appeal.status,
        "contentStatus": content.status,
        "message": "申诉已提交，等待人工复核。",
    }


@router.get("/me/appeals")
def list_my_appeals(
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    appeals = db.scalars(
        select(Appeal)
        .options(joinedload(Appeal.content).joinedload(Content.topic).joinedload(Topic.author))
        .where(Appeal.user_id == user.id)
        .order_by(Appeal.created_at.desc())
    ).all()
    appeal_ids = [appeal.id for appeal in appeals]
    reviews = {
        review.appeal_id: review
        for review in db.scalars(
            select(ManualReview).where(ManualReview.appeal_id.in_(appeal_ids)).order_by(ManualReview.created_at.desc())
        ).all()
    } if appeal_ids else {}
    return {
        "items": [
            {
                "id": appeal.id,
                "contentId": appeal.content_id,
                "contentText": appeal.content.text,
                "topic": {
                    "id": appeal.content.topic.id,
                    "title": appeal.content.topic.title,
                    "category": appeal.content.topic.category,
                },
                "appealType": appeal.appeal_type,
                "reason": appeal.reason,
                "extraContext": appeal.extra_context,
                "status": appeal.status,
                "counterAnalysis": appeal.counter_analysis or None,
                "finalReason": reviews[appeal.id].review_reason if appeal.id in reviews else None,
                "createdAt": iso_utc(appeal.created_at),
                "updatedAt": iso_utc(appeal.updated_at),
            }
            for appeal in appeals
        ]
    }
