/** 共享枚举（与 backend/src/constants/enums.py 一一对应）。 */
export const ALLOCATION_METHODS = [
  { value: 'neyman', label: 'Neyman 分配', hint: 'n_h ∝ N_h·S_h，波动大的层多抽' },
  { value: 'proportional', label: '比例分配', hint: 'n_h ∝ N_h，S_h 缺失时退化口径' },
] as const;

export const PLAN_STATUS: Record<string, string> = {
  draft: '草稿',
  active: '已审批',
  archived: '已归档',
};

export const QUERY_STATUS: Record<string, string> = {
  completed: '已完成',
  failed: '失败',
};

export const QC_VERDICT: Record<string, string> = {
  pass: '达标',
  fail: '未达标',
};

export const REVIEW_STATE: Record<string, string> = {
  pending: '待签',
  confirmed: '三签完成',
};

export const SIGNOFF_STAGES = [
  { value: 'analyst', label: '自检提交', role: 'analyst' },
  { value: 'admin', label: '负责人复核', role: 'admin' },
  { value: 'viewer', label: '业务方知悉', role: 'viewer' },
] as const;

export const CHECK_HINTS: Record<string, string> = {
  rel_error_vs_standard: '点估计与全量真值的相对误差',
  ci_within_standard: '95% 置信区间半宽是否落在精度标准内',
  min_stratum_sample: '每层样本量不低于 30 行',
  sampling_coverage: '样本量 / 层容量，仅作参考',
  speed_vs_full_scan: '抽样耗时相对生产全量基线',
  share_publishable: '线路占比能否发布：每层样本达标且联合误差边界可同时覆盖各线路比较',
};

export const CONFIDENCE_OPTIONS = [0.8, 0.9, 0.95, 0.99];
export const TARGET_ERROR_OPTIONS = [1, 2, 3, 5, 10];
export const STRATUM_COLORS = [
  'var(--stratum-1)',
  'var(--stratum-2)',
  'var(--stratum-3)',
  'var(--stratum-4)',
  'var(--stratum-5)',
];
