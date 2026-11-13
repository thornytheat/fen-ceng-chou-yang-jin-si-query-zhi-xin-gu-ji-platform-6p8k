"""数据集 / 分层响应。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class StratumOut(BaseModel):
    code: str
    label: str
    population: int
    population_share_pct: float
    mean_value: float
    prior_std: float
    min_sample: int
    sort_order: int


class DatasetOut(BaseModel):
    id: int
    code: str
    name: str
    scenario: str
    metric_label: str
    unit: str
    unit_scale: int
    row_count: int
    source_rows: int
    strata_field: str
    value_field: str
    precision_target_pct: float
    confidence_level: float
    prior_period: str
    full_scan_baseline_ms: int
    truth_total: float
    measured_full_scan_ms: int | None
    note: str | None
    strata_count: int
    plan_count: int
    query_count: int
    updated_at: str


class DatasetDetailOut(DatasetOut):
    strata: list[StratumOut]


class DatasetPatchRequest(BaseModel):
    precision_target_pct: float | None = Field(default=None, ge=0.5, le=20)
    confidence_level: float | None = Field(default=None, ge=0.8, le=0.99)
    note: str | None = Field(default=None, max_length=400)


class RefreshTruthOut(BaseModel):
    task_id: str | None
    queued: bool
    message: str
