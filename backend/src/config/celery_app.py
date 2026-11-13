"""Celery 入口：backend 投递全量基线刷新任务，worker 消费并写心跳。"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from src.config.settings import settings

celery_app = Celery(
    "sampleaqp",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
)

celery_app.conf.beat_schedule = {
    "sampleaqp-heartbeat": {"task": "sampleaqp.heartbeat", "schedule": 20.0},
    "sampleaqp-refresh-truth": {"task": "sampleaqp.refresh_truth", "schedule": crontab(minute="*/30")},
}

TASK_HEARTBEAT = "sampleaqp.heartbeat"
TASK_REFRESH_TRUTH = "sampleaqp.refresh_truth"
