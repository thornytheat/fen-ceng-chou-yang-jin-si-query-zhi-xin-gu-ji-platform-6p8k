"""角色与权限（与 frontend/src/constants/roles.ts 对应）。"""
from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"      # 分析负责人：数据集精度标准、方案审批、全量基线刷新
    ANALYST = "analyst"  # 分析师：建方案、跑近似查询、精度自检
    VIEWER = "viewer"    # 业务方：只读估算结果与置信区间


ROLE_LABELS: dict[str, str] = {
    Role.ADMIN.value: "分析负责人",
    Role.ANALYST.value: "分析师",
    Role.VIEWER.value: "业务方",
}

ROLE_ORDER = [Role.ADMIN.value, Role.ANALYST.value, Role.VIEWER.value]

PERMISSIONS: dict[str, set[str]] = {
    Role.ADMIN.value: {
        "dataset:read",
        "dataset:calibrate",
        "dataset:refresh",
        "plan:read",
        "plan:write",
        "plan:approve",
        "query:read",
        "query:run",
        "qc:read",
        "qc:run",
        "qc:signoff",
        "audit:read",
        "export:read",
    },
    Role.ANALYST.value: {
        "dataset:read",
        "plan:read",
        "plan:write",
        "query:read",
        "query:run",
        "qc:read",
        "qc:run",
        "qc:signoff",
        "export:read",
    },
    Role.VIEWER.value: {
        "dataset:read",
        "plan:read",
        "query:read",
        "qc:read",
        "qc:acknowledge",
        "export:read",
    },
}
