"""共享枚举（前端对应文件 frontend/src/constants/enums.ts）。

AllocationMethod / PlanStatus / QueryStatus / QcVerdict / ReviewState
"""
from __future__ import annotations

from enum import StrEnum


class AllocationMethod(StrEnum):
    NEYMAN = "neyman"            # Neyman：n_h ∝ N_h·S_h（考虑层内波动）
    PROPORTIONAL = "proportional"  # 比例分配：n_h ∝ N_h（S_h 缺失时退化口径）

    @property
    def label(self) -> str:
        return {"neyman": "Neyman 分配", "proportional": "比例分配"}[self.value]


class PlanStatus(StrEnum):
    DRAFT = "draft"      # 草稿：可改参数
    ACTIVE = "active"    # 已审批：可被近似查询引用
    ARCHIVED = "archived"  # 归档：只读


class QueryStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class QcVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class ReviewState(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"


class SignoffStage(StrEnum):
    ANALYST = "analyst"    # 分析师提交自检
    ADMIN = "admin"        # 分析负责人复核
    VIEWER = "viewer"      # 业务方确认已知悉误差说明

    @property
    def label(self) -> str:
        return {"analyst": "自检提交", "admin": "负责人复核", "viewer": "业务方知悉"}[self.value]


class CheckCode(StrEnum):
    REL_ERROR = "rel_error_vs_standard"
    CI_WIDTH = "ci_within_standard"
    MIN_STRATUM = "min_stratum_sample"
    COVERAGE = "sampling_coverage"
    SPEED = "speed_vs_full_scan"
    SHARE_PUBLISHABLE = "share_publishable"


PLAN_STATUS_LABELS: dict[str, str] = {
    PlanStatus.DRAFT.value: "草稿",
    PlanStatus.ACTIVE.value: "已审批",
    PlanStatus.ARCHIVED.value: "已归档",
}

QC_VERDICT_LABELS: dict[str, str] = {
    QcVerdict.PASS.value: "达标",
    QcVerdict.FAIL.value: "未达标",
}

REVIEW_STATE_LABELS: dict[str, str] = {
    ReviewState.PENDING.value: "待签",
    ReviewState.CONFIRMED.value: "三签完成",
}

CONFIDENCE_CHOICES: tuple[float, ...] = (0.80, 0.90, 0.95, 0.99)
SIGNOFF_ORDER: tuple[str, ...] = (SignoffStage.ANALYST.value, SignoffStage.ADMIN.value, SignoffStage.VIEWER.value)
