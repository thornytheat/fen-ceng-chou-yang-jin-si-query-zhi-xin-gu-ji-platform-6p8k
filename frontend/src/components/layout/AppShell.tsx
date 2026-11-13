import { useEffect, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { authStore } from '../../stores/authStore';
import { uiStore } from '../../stores/uiStore';
import { NAV_ITEMS, LAB_META } from '../../constants/ui';
import { ROLE_LABELS, can } from '../../constants/roles';
import { useStore } from '../../hooks/useStore';
import { healthApi } from '../../api/health';
import Toasts from '../common/Toasts';

const TITLES: Record<string, { title: string; sub: string }> = {
  '/datasets': { title: '数据集概览', sub: 'STRATA INVENTORY · 分层档案与精度标准' },
  '/plans': { title: '抽样方案编辑', sub: 'SAMPLE PLAN · 置信 / 误差 → 层分配' },
  '/queries': { title: '近似查询', sub: 'APPROXIMATE QUERY · 点估计 + 95% CI' },
  '/qc': { title: '精度自检', sub: 'PRECISION QC · 真值对照与三角色复核' },
};

export default function AppShell({ children }: { children: React.ReactNode }) {
  const state = useStore(authStore);
  const location = useLocation();
  const navigate = useNavigate();
  const [beat, setBeat] = useState<number | null>(null);
  const role = state.user?.role;
  const navItems = NAV_ITEMS.filter((item) => can(role, item.permission));
  const meta = TITLES[location.pathname] ?? TITLES['/datasets'];

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const result = await healthApi.check();
        if (alive) setBeat(result.worker_heartbeat);
      } catch {
        if (alive) setBeat(null);
      }
    };
    void tick();
    const timer = window.setInterval(tick, 25000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  function logout() {
    authStore.logout();
    uiStore.toast('已退出量具台', 'info');
    navigate('/login', { replace: true });
  }

  return (
    <div className="shell">
      <aside className="rail">
        <div className="rail-mark">
          <span className="brand">sampleaqp</span>
          <small>STRATIFIED AQP LAB</small>
        </div>
        <div className="rail-ruler" aria-hidden="true">
          {Array.from({ length: 26 }).map((_, index) => (
            <i key={index} className={index % 5 === 0 ? 'tall' : ''} />
          ))}
        </div>
        <nav className="rail-nav">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'active' : '')}>
              <span className="nav-label">{item.label}</span>
              <span className="nav-sub mono">{item.sub}</span>
            </NavLink>
          ))}
        </nav>
        <div className="rail-foot">
          <div>{LAB_META.client}</div>
          <div className="tiny">{LAB_META.headcount} 人 · 运单 8,000 万行</div>
          <div className="rail-role mono">{role ? ROLE_LABELS[role] : '未登录'}</div>
        </div>
      </aside>

      <div className="main">
        <div className="topbar">
          <div className="topbar-title">
            <div className="eyebrow">{meta.sub}</div>
            <h1>{meta.title}</h1>
          </div>
          <div className="topbar-meta">
            <div className={`beat ${beat ? 'is-live' : 'is-idle'}`}>
              <i />
              <span className="mono">
                {beat ? `worker 心跳 ${Math.max(0, Math.round(Date.now() / 1000 - beat))}s 前` : 'worker 心跳未就绪'}
              </span>
            </div>
            <div className="who">
              <b>{state.user?.display_name}</b>
              <div className="tiny">{state.user?.email}</div>
            </div>
            <button className="btn btn-sm" onClick={logout}>
              退出
            </button>
          </div>
        </div>
        {children}
      </div>
      <Toasts />
    </div>
  );
}
