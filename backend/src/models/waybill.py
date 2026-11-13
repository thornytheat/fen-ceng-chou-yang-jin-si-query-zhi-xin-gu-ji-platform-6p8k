"""运单明细行（抽样框）：value_minor 为最小货币单位，sample_rank 为确定性抽样秩。

sample_rank 用 20 位零填充字符串存 64bit 哈希：定宽字符串的字典序等价于数值序，
MySQL / SQLite 都能索引排序，也不会踩 BIGINT 有符号溢出。
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Waybill(Base):
    __tablename__ = "waybills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    stratum_code: Mapped[str] = mapped_column(String(32), nullable=False)
    value_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sample_rank: Mapped[str] = mapped_column(String(20), nullable=False)
    biz_date: Mapped[date] = mapped_column(Date, nullable=False)
