from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.services.serializers import user_dict


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/demo-users")
def list_demo_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.role, User.username)).all()
    return {"items": [user_dict(user) for user in users]}

