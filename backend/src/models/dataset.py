"""数据集 + 分层统计（N_h / 先验 S_h / 层均值）。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, DECIMAL, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    scenario: Mapped[str] = mapped_column(String(400), nullable=False)
    metric_label: Mapped[str] = mapped_column(String(80), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), default="元", nullable=False)
    unit_scale: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    row_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    source_rows: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    strata_field: Mapped[str] = mapped_column(String(64), nullable=False)
    value_field: Mapped[str] = mapped_column(String(64), nullable=False)
    precision_target_pct: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), default=Decimal("2.00"), nullable=False)
    confidence_level: Mapped[Decimal] = mapped_column(DECIMAL(4, 3), default=Decimal("0.950"), nullable=False)
    prior_period: Mapped[str] = mapped_column(String(24), nullable=False)
    full_scan_baseline_ms: Mapped[int] = mapped_column(Integer, default=38600, nullable=False)
    truth_total_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    measured_full_scan_ms: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(400))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    strata: Mapped[list["DatasetStratum"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan", order_by="DatasetStratum.sort_order"
    )


class DatasetStratum(Base):
    __tablename__ = "dataset_strata"
    __table_args__ = (UniqueConstraint("dataset_id", "code", name="uq_stratum"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    population: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mean_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    prior_std_minor: Mapped[Decimal] = mapped_column(DECIMAL(14, 2), nullable=False)
    min_sample: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    dataset: Mapped[Dataset] = relationship(back_populates="strata")
