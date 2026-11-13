"""通用响应结构。"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ListEnvelope(BaseModel, Generic[T]):
    items: list[T]
    total: int


class HealthOut(BaseModel):
    status: str
    db: bool
    redis: bool
    worker_heartbeat: float | None = None
    brand: str = "sampleaqp"


class MessageOut(BaseModel):
    ok: bool
    message: str
    detail: dict | None = None
