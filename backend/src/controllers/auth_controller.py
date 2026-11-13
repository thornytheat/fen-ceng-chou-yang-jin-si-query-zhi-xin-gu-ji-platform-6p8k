"""登录 / 当前用户 controller。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.services import auth_service, audit_service


def login(db: Session, payload, ip: str | None = None) -> dict:
    user, token, expires_in = auth_service.authenticate(db, payload.email, payload.password)
    audit_service.record(
        db,
        actor_email=user.email,
        actor_role=user.role,
        action="auth.login",
        entity="user",
        entity_id=str(user.id),
        detail={"role": user.role},
        ip=ip,
    )
    db.commit()
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": auth_service.to_out(user),
    }


def me(db: Session, email: str) -> dict:
    return {"user": auth_service.to_out(auth_service.by_email(db, email))}
