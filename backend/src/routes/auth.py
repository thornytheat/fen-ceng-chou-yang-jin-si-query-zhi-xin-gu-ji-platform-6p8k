"""认证路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import auth_controller
from src.middlewares.rbac import principal_of
from src.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    return auth_controller.login(db, payload, ip)


@router.get("/auth/me")
def me(request: Request, db: Session = Depends(get_db)):
    principal = principal_of(request)
    return auth_controller.me(db, principal["email"])
