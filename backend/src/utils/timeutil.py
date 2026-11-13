"""时间工具：统一按 APP_TIMEZONE_OFFSET_MINUTES 输出本地时间。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.config.settings import settings


def local_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.app_timezone_offset_minutes)


def local_iso(dt: datetime | None = None) -> str:
    value = dt or local_now()
    return value.strftime("%Y-%m-%d %H:%M:%S")


def business_date(dt: datetime | None = None) -> str:
    return (dt or local_now()).strftime("%Y-%m-%d")
