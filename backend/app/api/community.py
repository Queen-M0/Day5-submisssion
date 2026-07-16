from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Appeal, Content, Scene, Topic, User


router = APIRouter(tags=["community"])


@router.get("/community")
def get_community(db: Session = Depends(get_db)):
    scene = db.scalar(select(Scene).where(Scene.type == "community").order_by(Scene.created_at))
    if not scene:
        raise HTTPException(status_code=404, detail="固定社区不存在")
    topic_count = db.scalar(
        select(func.count()).select_from(Topic).where(Topic.scene_id == scene.id, Topic.visible_to_public.is_(True))
    )
    public_floor_count = db.scalar(
        select(func.count())
        .select_from(Content)
        .where(Content.scene_id == scene.id, Content.visible_to_public.is_(True))
    )
    member_count = db.scalar(select(func.count()).select_from(User).where(User.role == "user"))
    manual_count = db.scalar(
        select(func.count()).select_from(Content).where(Content.status == "pending_manual_review")
    )
    appeal_count = db.scalar(
        select(func.count()).select_from(Appeal).where(Appeal.status.in_(["submitted", "reviewing"]))
    )
    return {
        "id": scene.id,
        "title": scene.title,
        "description": scene.description,
        "topicCount": topic_count or 0,
        "publicFloorCount": public_floor_count or 0,
        "memberCount": member_count or 0,
        "pendingReviewCount": (manual_count or 0) + (appeal_count or 0),
    }
