"""审计日志路由（admin）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import audit_controller
from src.middlewares.rbac import require_permission

router = APIRouter(tags=["audit"])


@router.get("/audit")
def list_audit(
    request: Request,
    limit: int = Query(default=40, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_permission("audit:read")),
):
    return audit_controller.list_audit(db, limit)
