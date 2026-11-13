import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../hooks/useStore';
import { useAsync } from '../hooks/useAsync';
import { useToast } from '../hooks/useToast';
import { authStore } from '../stores/authStore';
import { datasetStore } from '../stores/datasetStore';
import { planStore } from '../stores/planStore';
import { ALLOCATION_METHODS, CONFIDENCE_OPTIONS, TARGET_ERROR_OPTIONS } from '../constants/enums';
import { can } from '../constants/roles';
import StratumChart from '../components/common/StratumChart';
import RulerBar from '../components/common/RulerBar';
import VerdictPill from '../components/common/VerdictPill';
import EmptyState from '../components/common/EmptyState';
import VialTag from '../components/common/VialTag';
import { formatInt, formatMetric, formatNumber } from '../utils/format';

export default function Plans() {
  const auth = useStore(authStore);
  const datasets = useStore(datasetStore);
  const plans = useStore(planStore);
  const navigate = useNavigate();
  const toast = useToast();
  const role = auth.user?.role;

  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [name, setName] = useState('经营会 GMV · 95% / 2%');
  const [confidence, setConfidence] = useState(0.95);
  const [targetError, setTargetError] = useState(2);
  const [method, setMethod] = useState('neyman');

  useEffect(() => {
    void datasetStore.load().catch(() => undefined);
    void planStore.load().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (datasetId === null && datasets.items.length) {
      setDatasetId(datasets.items[0].id);
    }
  }, [datasets.items, datasetId]);

  const activeDataset = useMemo(
    () => datasets.items.find((item) => item.id === (plans.selected?.dataset_id ?? datasetId)) ?? null,
    [datasets.items, plans.selected, datasetId],
  );

  const create = useAsync(async () => {
    if (!datasetId) return null;
    const plan = await planStore.create({
      dataset_id: datasetId,
      name: name.trim() || '未命名方案',
      confidence_level: confidence,
      target_error_pct: targetError,
      method,
      note: `由 ${auth.user?.display_name ?? role} 在方案页创建`,
    });
    toast.ok(`方案 ${plan.code} 已生成：n=${formatInt(plan.sample_size)}，预计 CI ±${plan.expected_ci_pct.toFixed(2)}%`);
    return plan;
  });

  const approve = useAsync(async (id: number) => {
    const plan = await planStore.approve(id);
    toast.ok(`方案 ${plan.code} 已审批，可被近似查询引用`);
    return plan;
  });

  const archive = useAsync(async (id: number) => {
    const plan = await planStore.archive(id);
    toast.warn(`方案 ${plan.code} 已归档`);
    return plan;
  });

  const selected = plans.selected;
  const selectedDataset = useMemo(
    () => datasets.items.find((item) => item.id === selected?.dataset_id) ?? null,
    [datasets.items, selected],
  );

  const chartRows = (selected?.allocation ?? []).map((row) => ({
    code: row.code,
    label: row.label,
    population: row.population,
    populationSharePct: row.stratum_share_pct,
    sampleSize: row.sample_size,
    sampleSharePct: selected ? (row.sample_size / Math.max(1, selected.sample_size)) * 100 : 0,
  }));

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <div className="eyebrow">SAMPLE PLAN · NEYMAN / PROPORTIONAL</div>
          <h2>先算样本量，再决定要不要跑</h2>
          <p className="page-lead">
            输入置信度与目标相对误差，后端按 Neyman 分配算出每层样本量、预计 CI 与层容量约束；
            草稿方案必须由分析负责人审批后才能跑近似查询。
          </p>
        </div>
        <div className="page-head-meta mono">
          <span>{plans.items.length} PLANS</span>
          <span>{plans.items.filter((item) => item.status === 'active').length} ACTIVE</span>
        </div>
      </header>

      <div className="plans-layout">
        <section className="panel plan-form">
          <div className="panel-head">
            <h3>新建方案</h3>
            <VialTag code="NEW" label="算法 1" />
          </div>
          <label className="field">
            <span>数据集</span>
            <select className="input" value={datasetId ?? ''} onChange={(event) => setDatasetId(Number(event.target.value))}>
              {datasets.items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}（{formatInt(item.row_count)} 行）
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>方案名称</span>
            <input className="input" value={name} onChange={(event) => setName(event.target.value)} maxLength={80} />
          </label>
          <div className="form-row">
            <label className="field">
              <span>置信度</span>
              <select className="input" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))}>
                {CONFIDENCE_OPTIONS.map((item) => (
                  <option key={item} value={item}>
                    {(item * 100).toFixed(0)}%
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>目标误差</span>
              <select className="input" value={targetError} onChange={(event) => setTargetError(Number(event.target.value))}>
                {TARGET_ERROR_OPTIONS.map((item) => (
                  <option key={item} value={item}>
                    ±{item.toFixed(1)}%
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="field">
            <span>分配算法</span>
            <select className="input" value={method} onChange={(event) => setMethod(event.target.value)}>
              {ALLOCATION_METHODS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <div className="tiny muted">{ALLOCATION_METHODS.find((item) => item.value === method)?.hint}</div>
          <button
            className="btn btn-primary"
            disabled={!can(role, 'plan:write') || create.busy || !datasetId}
            onClick={() => void create.run()}
          >
            {create.busy ? '正在分配 …' : '计算样本量并保存草稿'}
          </button>
          {!can(role, 'plan:write') ? <div className="tiny muted">业务方只读，不能建方案（服务端 403）</div> : null}
          {create.error ? <div className="form-error">{create.error}</div> : null}
        </section>

        <section className="panel plan-list">
          <div className="panel-head">
            <h3>方案台账</h3>
            <span className="tiny mono">DRAFT → ACTIVE</span>
          </div>
          <div className="plan-cards">
            {plans.items.map((plan) => (
              <button
                key={plan.id}
                className={`plan-card ${selected?.id === plan.id ? 'is-active' : ''}`}
                onClick={() => planStore.select(plan)}
              >
                <div className="plan-card-top">
                  <span className="mono plan-code">{plan.code}</span>
                  <VerdictPill verdict={plan.status} label={plan.status_label} size="sm" />
                </div>
                <div className="plan-card-name">{plan.name}</div>
                <div className="plan-card-meta mono">
                  n={formatInt(plan.sample_size)} · ±{plan.expected_ci_pct.toFixed(2)}% · {plan.method_label}
                </div>
                <div className="plan-card-meta tiny">
                  {plan.dataset_code} · 已跑 {plan.query_count} 次
                </div>
              </button>
            ))}
            {!plans.items.length ? <div className="tiny muted">还没有方案，先在左侧建一个。</div> : null}
          </div>
        </section>

        <section className="panel plan-detail">
          {selected ? (
            <>
              <div className="panel-head">
                <div>
                  <div className="eyebrow">{selected.code} · {selected.dataset_code}</div>
                  <h3>{selected.name}</h3>
                </div>
                <div className="panel-actions">
                  {selected.status === 'draft' && can(role, 'plan:approve') ? (
                    <button className="btn btn-sm btn-primary" disabled={approve.busy} onClick={() => void approve.run(selected.id)}>
                      {approve.busy ? '审批中 …' : '审批通过'}
                    </button>
                  ) : null}
                  {selected.status !== 'archived' && can(role, 'plan:approve') ? (
                    <button className="btn btn-sm" disabled={archive.busy} onClick={() => void archive.run(selected.id)}>
                      归档
                    </button>
                  ) : null}
                </div>
              </div>

              <div className="detail-readouts">
                <div>
                  <span className="readout-label">总样本量</span>
                  <b className="mono">{formatInt(selected.sample_size)}</b>
                  <em>行</em>
                </div>
                <div>
                  <span className="readout-label">置信度</span>
                  <b className="mono">{(selected.confidence_level * 100).toFixed(0)}</b>
                  <em>%</em>
                </div>
                <div>
                  <span className="readout-label">目标误差</span>
                  <b className="mono">±{selected.target_error_pct.toFixed(1)}</b>
                  <em>%</em>
                </div>
                <div>
                  <span className="readout-label">预计 CI</span>
                  <b className="mono">±{selected.expected_ci_pct.toFixed(2)}</b>
                  <em>%</em>
                </div>
                <div>
                  <span className="readout-label">z 值</span>
                  <b className="mono">{selected.z_value.toFixed(3)}</b>
                  <em>σ</em>
                </div>
              </div>

              <RulerBar
                value={selected.expected_ci_pct}
                target={selectedDataset?.precision_target_pct ?? 2}
                caption="预计 CI 半宽 vs 数据集精度标准"
              />

              {selected.capacity_warning ? <div className="notice">{selected.capacity_warning}</div> : null}

              <StratumChart rows={chartRows} caption="层容量占比 vs 本方案分配样本量" showSample />

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>层</th>
                      <th className="num">N_h</th>
                      <th className="num">先验 S_h</th>
                      <th className="num">Neyman 权重</th>
                      <th className="num">样本 n_h</th>
                      <th className="num">层 CI 贡献</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.allocation.map((row) => (
                      <tr key={row.code}>
                        <td>{row.label}</td>
                        <td className="num mono">{formatInt(row.population)}</td>
                        <td className="num mono">
                          {selectedDataset
                            ? formatMetric(row.prior_std, selectedDataset.unit, selectedDataset.unit_scale)
                            : row.prior_std.toFixed(2)}
                        </td>
                        <td className="num mono">{formatNumber(row.neyman_weight * 100, 2)}%</td>
                        <td className="num mono strong">{formatInt(row.sample_size)}</td>
                        <td className="num mono">±{row.expected_ci_contribution_pct.toFixed(3)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="plan-cta">
                <div className="tiny muted">
                  算法口径：n = (z·ΣN_hS_h/(e·Y))²，向下取整；n_h 按最大余数法取整，每层最小 30 行、超层容量截断重分配。
                </div>
                <button className="btn btn-sm btn-primary" onClick={() => navigate(`/queries?plan=${selected.id}`)}>
                  用这个方案跑查询 →
                </button>
              </div>
              {!can(role, 'plan:approve') && selected.status === 'draft' ? (
                <div className="tiny muted">审批需要分析负责人角色（analyst 调用会 403）。</div>
              ) : null}
            </>
          ) : (
            <EmptyState title="还没有选中的方案" hint="左边选一个方案，或直接新建一个草稿。" />
          )}
        </section>
      </div>
    </div>
  );
}
