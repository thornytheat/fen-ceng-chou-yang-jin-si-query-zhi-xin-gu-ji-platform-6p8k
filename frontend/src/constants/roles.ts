/** 角色权限（与 backend/src/constants/roles.py 对应）。 */
export const ROLE_LABELS: Record<string, string> = {
  admin: '分析负责人',
  analyst: '分析师',
  viewer: '业务方',
};

export const ROLE_ORDER = ['admin', 'analyst', 'viewer'];

export const PERMISSIONS: Record<string, string[]> = {
  admin: [
    'dataset:read',
    'dataset:calibrate',
    'dataset:refresh',
    'plan:read',
    'plan:write',
    'plan:approve',
    'query:read',
    'query:run',
    'qc:read',
    'qc:run',
    'qc:signoff',
    'audit:read',
    'export:read',
  ],
  analyst: [
    'dataset:read',
    'plan:read',
    'plan:write',
    'query:read',
    'query:run',
    'qc:read',
    'qc:run',
    'qc:signoff',
    'export:read',
  ],
  viewer: ['dataset:read', 'plan:read', 'query:read', 'qc:read', 'qc:acknowledge', 'export:read'],
};

export function can(role: string | undefined, permission: string): boolean {
  if (!role) return false;
  return (PERMISSIONS[role] || []).includes(permission);
}
