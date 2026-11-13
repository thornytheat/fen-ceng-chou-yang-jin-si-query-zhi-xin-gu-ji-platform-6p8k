"""近似查询路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import query_controller
from src.middlewares.rbac import require_permission
from src.schemas.query import QueryOut, QueryRunRequest

router = APIRouter(tags=["queries"])


@router.get("/queries")
def list_queries(
    request: Request,
    plan_id: int | None = Query(default=None),
    limit: int = Query(default=40, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_permission("query:read")),
):
    return query_controller.list_queries(db, plan_id, limit)


@router.get("/queries/{query_id}", response_model=QueryOut)
def get_query(
    query_id: int, request: Request, db: Session = Depends(get_db), _=Depends(require_permission("query:read"))
):
    return query_controller.get_query(db, query_id)


@router.post("/queries/run", response_model=QueryOut, status_code=201)
def run_query(
    payload: QueryRunRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("query:run")),
):
    ip = request.client.host if request.client else None
    return query_controller.run_query(db, payload, actor, ip)


@router.get("/queries/{query_id}/export")
def export_query(
    query_id: int, request: Request, db: Session = Depends(get_db), _=Depends(require_permission("export:read"))
):
    return query_controller.export_query(db, query_id)
