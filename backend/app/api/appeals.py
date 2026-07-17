from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.dependencies import appeal_service
from app.core.database import get_db
from app.models import Appeal, AuditLog, Content, ManualReview, Topic
from app.schemas.requests import AppealSupplementRequest, SubmitAppealRequest
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
    db.flush()
    appeal_service.analyze(db, appeal)
    db.commit()
    return {
        "appealId": appeal.id,
        "status": appeal.status,
        "contentStatus": content.status,
        "message": "申诉反证分析已完成，等待人工复核。",
    }


@router.post("/appeals/{appeal_id}/supplement")
def supplement_appeal(
    appeal_id: str,
    payload: AppealSupplementRequest,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    appeal = db.scalar(
        select(Appeal)
        .options(joinedload(Appeal.content).selectinload(Content.moderation_records))
        .where(Appeal.id == appeal_id)
    )
    if not appeal:
        raise HTTPException(status_code=404, detail="申诉不存在")
    if appeal.user_id != user.id:
        raise HTTPException(status_code=403, detail="只能补充自己的申诉")
    if appeal.status != "need_more_context":
        raise HTTPException(status_code=409, detail="当前申诉未要求补充上下文")
    previous = appeal.extra_context.strip()
    appeal.extra_context = (
        f"{previous}\n\n【用户追加上下文】\n{payload.extra_context.strip()}" if previous else payload.extra_context.strip()
    )
    appeal.status = "submitted"
    appeal.content.status = "appeal_submitted"
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=user.id,
            action="appeal.context_supplemented",
            entity_type="content",
            entity_id=appeal.content_id,
            detail={"appealId": appeal.id, "description": "用户已补充申诉上下文"},
        )
    )
    appeal_service.analyze(db, appeal)
    db.commit()
    return {
        "appealId": appeal.id,
        "status": appeal.status,
        "contentStatus": appeal.content.status,
        "analysisCount": len(appeal.analysis_records),
    }


@router.get("/me/appeals")
def list_my_appeals(
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    appeals = db.scalars(
        select(Appeal)
        .options(
            joinedload(Appeal.content).joinedload(Content.topic).joinedload(Topic.author),
            selectinload(Appeal.analysis_records),
        )
        .where(Appeal.user_id == user.id)
        .order_by(Appeal.created_at.desc())
    ).all()
    appeal_ids = [appeal.id for appeal in appeals]
    reviews = {}
    if appeal_ids:
        for review in db.scalars(
            select(ManualReview).where(ManualReview.appeal_id.in_(appeal_ids)).order_by(ManualReview.created_at.desc())
        ).all():
            reviews.setdefault(review.appeal_id, review)
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
                "analysisRun": None
                if not appeal.analysis_records
                else {
                    "provider": appeal.analysis_records[-1].provider,
                    "modelVersion": appeal.analysis_records[-1].model_version,
                    "promptVersion": appeal.analysis_records[-1].prompt_version,
                    "evidenceValid": appeal.analysis_records[-1].evidence_valid,
                    "failureReason": appeal.analysis_records[-1].failure_reason,
                    "createdAt": iso_utc(appeal.analysis_records[-1].created_at),
                },
                "analysisCount": len(appeal.analysis_records),
                "finalReason": reviews[appeal.id].review_reason if appeal.id in reviews else None,
                "createdAt": iso_utc(appeal.created_at),
                "updatedAt": iso_utc(appeal.updated_at),
            }
            for appeal in appeals
        ]
    }
