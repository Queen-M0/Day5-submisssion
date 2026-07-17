from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.models import User
from app.schemas.requests import LoginRequest
from app.services.auth_service import create_access_token, demo_user_id, get_current_user, verify_password
from app.services.serializers import user_dict


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username.strip()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return {
        "accessToken": create_access_token(user),
        "tokenType": "bearer",
        "expiresIn": get_settings().auth_token_hours * 3600,
        "user": user_dict(user),
    }


@router.get("/me")
def current_user(user_id: str = Depends(demo_user_id), db: Session = Depends(get_db)):
    return user_dict(get_current_user(db, user_id))


@router.get("/demo-users")
def list_demo_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.role, User.username)).all()
    return {"items": [user_dict(user) for user in users]}

