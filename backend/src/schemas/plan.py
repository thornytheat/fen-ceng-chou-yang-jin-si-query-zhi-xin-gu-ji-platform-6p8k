"""抽样方案：创建 / 分配明细。"""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.constants.enums import AllocationMethod, PlanStatus


class PlanCreateRequest(BaseModel):
    dataset_id: int
    name: str = Field(min_length=2, max_length=120)
    confidence_level: float = Field(ge=0.8, le=0.99)
    target_error_pct: float = Field(gt=0.1, le=20)
    method: AllocationMethod = AllocationMethod.NEYMAN
    note: str | None = Field(default=None, max_length=400)


class AllocationRowOut(BaseModel):
    code: str
    label: str
    population: int
    prior_std: float
    neyman_weight: float
    sample_size: int
    stratum_share_pct: float
    expected_ci_contribution_pct: float


class PlanOut(BaseModel):
    id: int
    code: str
    dataset_id: int
    dataset_code: str
    dataset_name: str
    metric_label: str
    name: str
    confidence_level: float
    target_error_pct: float
    method: str
    method_label: str
    status: str
    status_label: str
    sample_size: int
    expected_ci_pct: float
    z_value: float
    allocation: list[AllocationRowOut]
    note: str | None
    created_by: str
    approved_by: str | None
    approved_at: str | None
    query_count: int
    created_at: str
    capacity_warning: str | None = None
