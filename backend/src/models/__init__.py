"""SQLAlchemy 2.0 模型汇总（Base + 4 个核心实体 + 支撑表）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


from src.models.approx_query import ApproxQuery  # noqa: E402
from src.models.audit import AuditLog  # noqa: E402
from src.models.dataset import Dataset, DatasetStratum  # noqa: E402
from src.models.qc_check import QcCheck  # noqa: E402
from src.models.sample_plan import SamplePlan  # noqa: E402
from src.models.user import User  # noqa: E402
from src.models.waybill import Waybill  # noqa: E402

__all__ = [
    "Base",
    "ApproxQuery",
    "AuditLog",
    "Dataset",
    "DatasetStratum",
    "QcCheck",
    "SamplePlan",
    "User",
    "Waybill",
    "TimestampMixin",
    "Any",
]
