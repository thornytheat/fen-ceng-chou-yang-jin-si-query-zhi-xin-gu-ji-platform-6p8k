"""数据集 controller：列表 / 详情 / 分层 / 精度标准 / 全量基线刷新。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.services import dataset_service
from src.utils.errors import AppError


def list_datasets(db: Session) -> dict:
    items = [dataset_service.dataset_out(db, row) for row in dataset_service.list_datasets(db)]
    return {"items": items, "total": len(items)}


def get_dataset(db: Session, dataset_id: int) -> dict:
    dataset = dataset_service.get_dataset(db, dataset_id)
    return dataset_service.dataset_out(db, dataset, with_strata=True)


def get_strata(db: Session, dataset_id: int) -> dict:
    dataset = dataset_service.get_dataset(db, dataset_id)
    detail = dataset_service.dataset_out(db, dataset, with_strata=True)
    return {"items": detail["strata"], "total": len(detail["strata"])}


def patch_dataset(db: Session, dataset_id: int, payload, actor: dict, ip: str | None = None) -> dict:
    dataset_service.patch_dataset(db, dataset_id, payload, actor, ip)
    db.commit()
    return dataset_service.dataset_out(db, dataset_service.get_dataset(db, dataset_id), with_strata=True)


def refresh_truth(db: Session, dataset_id: int, actor: dict, ip: str | None = None) -> dict:
    dataset = dataset_service.get_dataset(db, dataset_id)
    if dataset.row_count <= 0:
        raise AppError("DATASET_EMPTY", 422)
    task_id = None
    queued = False
    try:
        from src.tasks import refresh_truth_task

        async_result = refresh_truth_task.delay(dataset_id)
        task_id = getattr(async_result, "id", None)
        queued = True
    except Exception:  # noqa: BLE001 - broker 不可用时同步兜底
        queued = False
    if not queued:
        dataset_service.refresh_truth(db, dataset_id, actor_email=actor["email"], actor_role=actor["role"])
        db.commit()
    return {
        "task_id": task_id,
        "queued": queued,
        "message": "已投递后台刷新任务" if queued else "消息队列不可用，已同步刷新全量基线",
    }
