"""登录与当前用户。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants.roles import ROLE_LABELS
from src.models.user import User
from src.utils.errors import AppError
from src.utils.security import create_access_token, verify_password


def authenticate(db: Session, email: str, password: str) -> tuple[User, str, int]:
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None or not verify_password(password, user.password_hash):
        raise AppError("AUTH_INVALID", 401, detail="email or password mismatch")
    token, expires_in = create_access_token(user.email, user.role)
    return user, token, expires_in


def by_email(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise AppError("AUTH_MISSING", 401, detail="user vanished")
    return user


def to_out(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "role_label": ROLE_LABELS.get(user.role, user.role),
    }
