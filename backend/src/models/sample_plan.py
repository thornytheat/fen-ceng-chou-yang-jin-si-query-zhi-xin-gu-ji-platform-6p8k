"""抽样方案：置信度 / 目标误差 / 分配算法 / 每层样本量。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, DECIMAL, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base
from src.models.dataset import Dataset


class SamplePlan(Base):
    __tablename__ = "sample_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence_level: Mapped[Decimal] = mapped_column(DECIMAL(4, 3), nullable=False)
    target_error_pct: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    allocation: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    expected_ci_pct: Mapped[Decimal] = mapped_column(DECIMAL(6, 3), nullable=False)
    z_value: Mapped[Decimal] = mapped_column(DECIMAL(6, 4), nullable=False)
    note: Mapped[str | None] = mapped_column(String(400))
    created_by: Mapped[str] = mapped_column(String(160), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(160))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    seed_key: Mapped[str | None] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    dataset: Mapped[Dataset] = relationship()
