"""路由汇总：全部挂在 /api 前缀下（与 Nginx 反代前缀一致）。"""
from __future__ import annotations

from fastapi import APIRouter

from src.routes.audit import router as audit_router
from src.routes.auth import router as auth_router
from src.routes.datasets import router as dataset_router
from src.routes.health import router as health_router
from src.routes.plans import router as plan_router
from src.routes.qc import router as qc_router
from src.routes.queries import router as query_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dataset_router)
api_router.include_router(plan_router)
api_router.include_router(query_router)
api_router.include_router(qc_router)
api_router.include_router(audit_router)
