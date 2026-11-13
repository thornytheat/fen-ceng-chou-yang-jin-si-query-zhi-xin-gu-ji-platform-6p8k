"""Celery 任务：心跳 + 全量基线刷新（真实全表聚合）。"""
from __future__ import annotations

import time

from src.config.celery_app import TASK_HEARTBEAT, TASK_REFRESH_TRUTH, celery_app
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("tasks")


def _redis():
    import redis

    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


@celery_app.task(name=TASK_HEARTBEAT)
def heartbeat_task() -> str:
    try:
        _redis().set("sampleaqp:worker:heartbeat", f"{time.time():.3f}", ex=300)
    except Exception as exc:  # noqa: BLE001
        logger.warning("heartbeat failed: %s", exc)
    return "ok"


@celery_app.task(name=TASK_REFRESH_TRUTH, bind=True, max_retries=1)
def refresh_truth_task(self, dataset_id: int | None = None) -> dict:
    """重算数据集的全量真值与真实扫描耗时（这是 worker 的主要业务职责）。"""
    from sqlalchemy import select

    from src.config.database import session_scope
    from src.models.dataset import Dataset
    from src.services import dataset_service

    results: list[dict] = []
    with session_scope() as db:
        if dataset_id is None:
            ids = [row.id for row in db.scalars(select(Dataset))]
        else:
            ids = [int(dataset_id)]
        for current in ids:
            measured = dataset_service.refresh_truth(db, current, actor_email="celery", actor_role="system")
            measured["dataset_id"] = current
            results.append(measured)
            logger.info("truth refreshed dataset=%s rows=%s", current, measured.get("rows"))
    return {"datasets": results}
