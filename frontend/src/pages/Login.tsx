import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/auth';
import { authStore } from '../stores/authStore';
import { DEMO_ACCOUNTS } from '../constants/ui';
import { errorMessage } from '../utils/errorMessage';
import VialTag from '../components/common/VialTag';

const VIALS = [
  { code: 'LTL-01', label: '干线长途', n: '30,000 行' },
  { code: 'RGN-02', label: '区域支线', n: '24,000 行' },
  { code: 'URB-03', label: '同城配送', n: '26,000 行' },
  { code: 'CLD-04', label: '冷链专线', n: '12,000 行' },
  { code: 'HVY-05', label: '大件重货', n: '8,000 行' },
];

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('admin@sampleaqp.io');
  const [password, setPassword] = useState('Demo@2026');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const result = await authApi.login(email, password);
      authStore.setSession(result.access_token, result.user);
      navigate('/datasets', { replace: true });
    } catch (err) {
      setError(errorMessage((err as { payload?: unknown }).payload, '登录失败'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login">
      <section className="login-bench">
        <div className="login-headline">
          <div className="eyebrow">YUANZHOU LOGISTICS · DATA ANALYSIS LAB</div>
          <h1>
            用 <em>2,742</em> 行样本
            <br />
            回答 8,000 万行的
            <br />
            「大概多少」
          </h1>
          <p>
            远舟物流 · 数据分析组（7 人）。业务方在会上要 GMV，全表聚合要跑 40 分钟；
            裸抽样又说不清误差。这一版把分层分配、点估计、置信区间和全量对照放进同一个量具台。
          </p>
        </div>

        <div className="login-vials">
          {VIALS.map((vial, index) => (
            <div className="login-vial" key={vial.code} style={{ animationDelay: `${index * 60}ms` }}>
              <VialTag code={vial.code} tone={index % 2 === 0 ? 'brass' : 'steel'} />
              <span className="login-vial-name">{vial.label}</span>
              <span className="login-vial-n mono">{vial.n}</span>
            </div>
          ))}
        </div>

        <div className="login-readouts">
          <div>
            <b className="mono">3</b>
            <span>数据集</span>
          </div>
          <div>
            <b className="mono">5</b>
            <span>线路分层</span>
          </div>
          <div>
            <b className="mono">120,000</b>
            <span>演示明细行</span>
          </div>
          <div>
            <b className="mono">38.6s</b>
            <span>生产全量扫描基线</span>
          </div>
        </div>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <div className="eyebrow">LAB ACCESS · 采样台登录</div>
          <h2>进台 · 抽样量具</h2>
          <p className="sub">数据集、抽样方案、近似查询和精度自检都在同一套权限下。</p>

          <label className="field">
            <span>邮箱</span>
            <input
              className="input"
              type="email"
              value={email}
              autoComplete="username"
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="field">
            <span>密码</span>
            <input
              className="input"
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          <button className="btn btn-primary" style={{ width: '100%' }} type="submit" disabled={busy}>
            {busy ? '核对工牌 …' : '进台'}
          </button>
          {error ? <div className="form-error">{error}</div> : null}

          <div className="quick-accounts">
            <span className="tiny">演示账号（密码统一 Demo@2026）：</span>
            {DEMO_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                type="button"
                onClick={() => {
                  setEmail(account.email);
                  setPassword('Demo@2026');
                }}
              >
                <b>{account.who}</b> · {account.desc}
              </button>
            ))}
          </div>
        </form>
        <div className="tiny muted login-note">
          权限差异在服务端生效：业务方（viewer）调用建方案 / 跑查询 / 改精度标准会真实返回 403；
          分析师改精度标准、审批方案同样 403。只有分析负责人（admin）能校准数据集与审批方案。
        </div>
      </section>
    </div>
  );
}
