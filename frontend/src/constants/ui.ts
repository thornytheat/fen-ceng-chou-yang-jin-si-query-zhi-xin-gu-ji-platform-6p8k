export const NAV_ITEMS = [
  { to: '/datasets', label: '数据集', sub: 'STRATA', permission: 'dataset:read' },
  { to: '/plans', label: '抽样方案', sub: 'PLANS', permission: 'plan:read' },
  { to: '/queries', label: '近似查询', sub: 'ESTIMATE', permission: 'query:read' },
  { to: '/qc', label: '精度自检', sub: 'QC', permission: 'qc:read' },
];

export const LAB_META = {
  client: '远舟物流 · 数据分析组',
  headcount: 7,
  sourceRows: 80_000_000,
  rowCount: 120_000,
  defaultPassword: 'Demo@2026',
};

export const DEMO_ACCOUNTS = [
  { email: 'admin@sampleaqp.io', role: 'admin', who: '沈望', desc: '数据集 / 精度标准 / 方案审批' },
  { email: 'analyst@sampleaqp.io', role: 'analyst', who: '陆珂', desc: '建方案 / 跑近似查询 / 自检' },
  { email: 'viewer@sampleaqp.io', role: 'viewer', who: '周岚', desc: '只读估算结果与置信区间' },
];
