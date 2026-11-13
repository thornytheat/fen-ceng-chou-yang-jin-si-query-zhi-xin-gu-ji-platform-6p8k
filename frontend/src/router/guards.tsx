import { Navigate } from 'react-router-dom';
import { useStore } from '../hooks/useStore';
import { authStore } from '../stores/authStore';
import { can } from '../constants/roles';

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const state = useStore(authStore);
  if (!state.bootstrapped) {
    return <div className="boot-screen">正在加载量具台 …</div>;
  }
  if (!state.token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function RequirePermission({ permission, children }: { permission: string; children: React.ReactNode }) {
  const state = useStore(authStore);
  if (!can(state.user?.role, permission)) {
    return (
      <div className="denied">
        <div className="denied-code mono">403</div>
        <h2>这个工位没有该权限</h2>
        <p>
          当前角色 <b>{state.user?.role_label ?? state.user?.role}</b> 不能访问 <code>{permission}</code>。
          服务端同样会返回 403，不是前端藏按钮。
        </p>
      </div>
    );
  }
  return <>{children}</>;
}
