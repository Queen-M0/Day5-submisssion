from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.models import Content, Scene
from app.services.auth_service import demo_user_id, get_current_user
from app.services.serializers import content_dict, iso_utc


router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.get("")
def list_scenes(db: Session = Depends(get_db)):
    scenes = db.scalars(select(Scene).order_by(Scene.created_at)).all()
    return {
        "items": [
            {
                "id": scene.id,
                "type": scene.type,
                "title": scene.title,
                "description": scene.description,
                "createdAt": iso_utc(scene.created_at),
            }
            for scene in scenes
        ]
    }


@router.get("/{scene_id}/contents")
def list_scene_contents(
    scene_id: str,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    if not db.get(Scene, scene_id):
        raise HTTPException(status_code=404, detail="讨论区不存在")
    contents = db.scalars(
        select(Content)
        .options(
            joinedload(Content.author),
            joinedload(Content.parent).joinedload(Content.author),
            selectinload(Content.moderation_records),
        )
        .where(Content.scene_id == scene_id)
        .order_by(Content.created_at)
    ).all()
    detailed = user.role in {"reviewer", "admin"}
    return {"items": [content_dict(item, user.id, detailed=detailed) for item in contents]}
