from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.models import User


def get_current_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的演示用户")
    return user


def require_reviewer(user: User) -> None:
    if user.role not in {"reviewer", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要审核员权限")


def demo_user_id(x_user_id: str = Header(default="student_a")) -> str:
    return x_user_id

