from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import Appeal, AuditLog, Content
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
        status="submitted",
    )
    content.status = "appeal_submitted"
    db.add(appeal)
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=user.id,
            action="appeal.submitted",
            entity_type="appeal",
            entity_id=appeal.id,
            detail={"contentId": content.id, "appealType": payload.appeal_type},
        )
    )
    db.commit()
    return {"appealId": appeal.id, "status": appeal.status, "message": "申诉已提交，等待审核人员复核。"}


@router.get("/me/appeals")
def list_my_appeals(
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    appeals = db.scalars(
        select(Appeal)
        .options(joinedload(Appeal.content))
        .where(Appeal.user_id == user.id)
        .order_by(Appeal.created_at.desc())
    ).all()
    return {
        "items": [
            {
                "id": appeal.id,
                "contentId": appeal.content_id,
                "contentText": appeal.content.text,
                "appealType": appeal.appeal_type,
                "reason": appeal.reason,
                "status": appeal.status,
                "createdAt": iso_utc(appeal.created_at),
                "updatedAt": iso_utc(appeal.updated_at),
            }
            for appeal in appeals
        ]
    }
