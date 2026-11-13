const FALLBACK: Record<string, string> = {
  AUTH_MISSING: '请先登录再操作',
  AUTH_INVALID: '账号或密码不正确',
  FORBIDDEN: '当前角色没有该操作权限（服务端 403）',
  NOT_FOUND: '对象不存在或已被删除',
  VALIDATION: '请求参数不合法',
  RATE_LIMITED: '请求过于频繁，请稍后再试',
  PLAN_NOT_ACTIVE: '只有已审批的方案才能跑近似查询',
  QC_ORDER: '复核链必须按 分析师 → 负责人 → 业务方 顺序签署',
  QC_DUPLICATE_SIGNOFF: '该复核链已经签完',
  DATASET_EMPTY: '数据集还没有明细行',
  INTERNAL: '服务内部错误，请稍后重试',
};

export function errorMessage(payload: unknown, fallback = '操作失败'): string {
  if (!payload) return fallback;
  if (typeof payload === 'string') return payload;
  const value = payload as { code?: string; message?: string; detail?: unknown };
  if (value.code && FALLBACK[value.code]) return FALLBACK[value.code];
  if (value.message) return value.message;
  return fallback;
}
