"""精度自检路由（复核链按角色分签）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import qc_controller
from src.middlewares.rbac import principal_of, require_permission
from src.schemas.qc import QcOut, QcRunRequest, SignoffRequest, SignoffResultOut

router = APIRouter(tags=["qc"])


@router.get("/qc")
def list_checks(
    request: Request,
    limit: int = Query(default=40, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_permission("qc:read")),
):
    return qc_controller.list_checks(db, limit)


@router.get("/qc/{qc_id}", response_model=QcOut)
def get_check(qc_id: int, request: Request, db: Session = Depends(get_db), _=Depends(require_permission("qc:read"))):
    return qc_controller.get_check(db, qc_id)


@router.post("/qc", response_model=QcOut, status_code=201)
def run_check(
    payload: QcRunRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("qc:run")),
):
    ip = request.client.host if request.client else None
    return qc_controller.run_check(db, payload, actor, ip)


@router.post("/qc/{qc_id}/signoff", response_model=SignoffResultOut)
def sign_off(
    qc_id: int,
    payload: SignoffRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # 三角色各签一步：分析师提交、负责人复核、业务方知悉；顺序与角色在 service 内强校验。
    principal = principal_of(request)
    ip = request.client.host if request.client else None
    return qc_controller.sign_off(db, qc_id, payload, principal, ip)
