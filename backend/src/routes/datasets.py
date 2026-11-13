"""数据集路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import dataset_controller
from src.middlewares.rbac import principal_of, require_permission
from src.schemas.dataset import DatasetDetailOut, DatasetPatchRequest, RefreshTruthOut

router = APIRouter(tags=["datasets"])


@router.get("/datasets")
def list_datasets(request: Request, db: Session = Depends(get_db), _=Depends(require_permission("dataset:read"))):
    return dataset_controller.list_datasets(db)


@router.get("/datasets/{dataset_id}", response_model=DatasetDetailOut)
def get_dataset(
    dataset_id: int, request: Request, db: Session = Depends(get_db), _=Depends(require_permission("dataset:read"))
):
    return dataset_controller.get_dataset(db, dataset_id)


@router.get("/datasets/{dataset_id}/strata")
def get_strata(
    dataset_id: int, request: Request, db: Session = Depends(get_db), _=Depends(require_permission("dataset:read"))
):
    return dataset_controller.get_strata(db, dataset_id)


@router.patch("/datasets/{dataset_id}", response_model=DatasetDetailOut)
def patch_dataset(
    dataset_id: int,
    payload: DatasetPatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("dataset:calibrate")),
):
    ip = request.client.host if request.client else None
    return dataset_controller.patch_dataset(db, dataset_id, payload, actor, ip)


@router.post("/datasets/{dataset_id}/refresh-truth", response_model=RefreshTruthOut)
def refresh_truth(
    dataset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("dataset:refresh")),
):
    ip = request.client.host if request.client else None
    return dataset_controller.refresh_truth(db, dataset_id, actor, ip)
