"""近似查询：运行请求 / 结果明细。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRunRequest(BaseModel):
    plan_id: int
    strata: list[str] = Field(default_factory=list, max_length=5)
    note: str | None = Field(default=None, max_length=200)


class StratumContributionOut(BaseModel):
    code: str
    label: str
    population: int
    sample_size: int
    sample_mean: float
    contribution: float
    ci_half: float
    contribution_share_pct: float
    variance_share_pct: float
    verified: bool


class CompositionRowOut(BaseModel):
    code: str
    label: str
    sample_size: int
    point_share_pct: float
    point_share_raw_pct: float
    std_error_pct: float
    marginal_half_pct: float
    joint_half_pct: float
    joint_low_pct: float
    joint_high_pct: float
    interval_clipped: bool


class CompositionOut(BaseModel):
    publishable: bool
    confidence: float
    family_size: int
    z_marginal: float
    z_joint: float
    method: str
    min_stratum_sample: int
    point_total_pct: float
    rows: list[CompositionRowOut]
    reasons: list[str]


class QueryOut(BaseModel):
    id: int
    code: str
    plan_id: int
    plan_name: str
    dataset_id: int
    dataset_code: str
    dataset_name: str
    metric_label: str
    unit: str
    filter_strata: list[str]
    sample_size: int
    value_estimate: float
    ci_low: float
    ci_high: float
    ci_half: float
    rel_error_pct: float
    true_value: float
    truth_rel_error_pct: float
    speed_ratio: float
    sample_ms: float
    truth_ms: float
    full_scan_baseline_ms: int
    status: str
    run_by: str
    created_at: str
    strata_detail: list[StratumContributionOut]
    composition: CompositionOut | None = None
    qc_id: int | None = None
    qc_verdict: str | None = None
