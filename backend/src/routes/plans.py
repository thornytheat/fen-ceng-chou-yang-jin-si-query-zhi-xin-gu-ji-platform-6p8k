"""抽样方案路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import plan_controller
from src.middlewares.rbac import require_permission
from src.schemas.plan import PlanCreateRequest, PlanOut

router = APIRouter(tags=["plans"])


@router.get("/plans")
def list_plans(
    request: Request,
    dataset_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_permission("plan:read")),
):
    return plan_controller.list_plans(db, dataset_id)


@router.get("/plans/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: int, request: Request, db: Session = Depends(get_db), _=Depends(require_permission("plan:read"))):
    return plan_controller.get_plan(db, plan_id)


@router.post("/plans", response_model=PlanOut, status_code=201)
def create_plan(
    payload: PlanCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("plan:write")),
):
    ip = request.client.host if request.client else None
    return plan_controller.create_plan(db, payload, actor, ip)


@router.post("/plans/{plan_id}/approve", response_model=PlanOut)
def approve_plan(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("plan:approve")),
):
    ip = request.client.host if request.client else None
    return plan_controller.approve_plan(db, plan_id, actor, ip)


@router.post("/plans/{plan_id}/archive", response_model=PlanOut)
def archive_plan(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("plan:approve")),
):
    ip = request.client.host if request.client else None
    return plan_controller.archive_plan(db, plan_id, actor, ip)
