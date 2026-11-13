"""错误码 → 中文文案（前端 errorMessage 会把 code 翻成提示）。"""
from __future__ import annotations

ERROR_MESSAGES: dict[str, str] = {
    "AUTH_MISSING": "请先登录再操作",
    "AUTH_INVALID": "账号或密码不正确",
    "FORBIDDEN": "当前角色没有该操作权限",
    "NOT_FOUND": "对象不存在或已被删除",
    "VALIDATION": "请求参数不合法",
    "RATE_LIMITED": "请求过于频繁，请稍后再试",
    "DATASET_EMPTY": "数据集还没有载入明细行",
    "PLAN_NOT_ACTIVE": "只有已审批的方案才能跑近似查询",
    "PLAN_CAPACITY": "层容量不足，已截断并按权重重分配",
    "QC_ORDER": "复核链必须按 分析师 → 负责人 → 业务方 顺序签署",
    "QC_DUPLICATE_SIGNOFF": "该角色已经签过这一步",
    "QUERY_FAILED": "抽样或估计过程失败",
    "INTERNAL": "服务内部错误",
}
