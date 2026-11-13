"""精度自检：相对误差 / CI 宽度 / 层最小样本 / 覆盖率 + 三角色复核链。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, DECIMAL, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base
from src.models.approx_query import ApproxQuery


class QcCheck(Base):
    __tablename__ = "qc_checks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("approx_queries.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    target_pct: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False)
    rel_error_pct: Mapped[Decimal] = mapped_column(DECIMAL(7, 4), nullable=False)
    ci_pct: Mapped[Decimal] = mapped_column(DECIMAL(7, 4), nullable=False)
    min_stratum_sample: Mapped[int] = mapped_column(Integer, nullable=False)
    coverage_pct: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), nullable=False)
    checks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)
    review_state: Mapped[str] = mapped_column(String(16), nullable=False)
    signoffs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    query: Mapped[ApproxQuery] = relationship()
