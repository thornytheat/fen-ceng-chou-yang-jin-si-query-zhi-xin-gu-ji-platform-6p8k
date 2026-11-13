import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useStore } from '../hooks/useStore';
import { useAsync } from '../hooks/useAsync';
import { useToast } from '../hooks/useToast';
import { authStore } from '../stores/authStore';
import { datasetStore } from '../stores/datasetStore';
import { planStore } from '../stores/planStore';
import { queryStore } from '../stores/queryStore';
import { datasetApi } from '../api/datasets';
import { queryApi } from '../api/queries';
import { can } from '../constants/roles';
import StatTile from '../components/common/StatTile';
import RangeBar from '../components/common/RangeBar';
import CiPlot from '../components/common/CiPlot';
import CompositionPanel from '../components/common/CompositionPanel';
import RulerBar from '../components/common/RulerBar';
import VerdictPill from '../components/common/VerdictPill';
import EmptyState from '../components/common/EmptyState';
import VialTag from '../components/common/VialTag';
import { formatInt, formatMetric, formatMs, formatNumber } from '../utils/format';
import type { Dataset } from '../types/models';

export default function Queries() {
  const auth = useStore(authStore);
  const plans = useStore(planStore);
  const queries = useStore(queryStore);
  const toast = useToast();
  const [params] = useSearchParams();
  const role = auth.user?.role;

  const [planId, setPlanId] = useState<number | null>(null);
  const [strata, setStrata] = useState<string[]>([]);
  const [note, setNote] = useState('经营会临时问数');
  const [detail, setDetail] = useState<Dataset | null>(null);

  useEffect(() => {
    void planStore.load().catch(() => undefined);
    void queryStore.load().catch(() => undefined);
    void datasetStore.load().catch(() => undefined);
  }, []);

  const activePlans = useMemo(
    () => plans.items.filter((item) => item.status === 'active').sort((a, b) => a.target_error_pct - b.target_error_pct),
    [plans.items],
  );

  useEffect(() => {
    if (planId !== null || !activePlans.length) return;
    const fromUrl = Number(params.get('plan'));
    const picked = activePlans.find((item) => item.id === fromUrl) ?? activePlans[0];
    setPlanId(picked.id);
  }, [activePlans, planId, params]);

  const plan = activePlans.find((item) => item.id === planId) ?? null;

  useEffect(() => {
    if (!plan) return;
    let alive = true;
    datasetApi
      .detail(plan.dataset_id)
      .then((row) => {
        if (alive) setDetail(row);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [plan?.dataset_id]);

  const run = useAsync(async () => {
    if (!plan) return null;
    const query = await queryStore.run({ plan_id: plan.id, strata, note });
    toast.ok(`估算完成：${formatMetric(query.value_estimate, query.unit, detail?.unit_scale ?? 100)}，CI ±${query.rel_error_pct.toFixed(2)}%`);
    return query;
  });

  const exportMd = useAsync(async (id: number) => {
    const markdown = await queryApi.exportMarkdown(id);
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `sampleaqp-estimate-${id}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast.ok('估算说明 Markdown 已导出');
    return markdown;
  });

  const selected = queries.selected;
  const scale = detail?.unit_scale ?? 100;
  const unit = detail?.unit ?? '元';
  const target = detail?.precision_target_pct ?? 2;

  const ciRows = (selected?.strata_detail ?? []).map((row) => ({
    code: row.code,
    label: row.label,
    contribution: row.contribution,
    ciHalf: row.ci_half,
    sharePct: row.contribution_share_pct,
  }));

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <div className="eyebrow">APPROXIMATE QUERY · HORVITZ–THOMPSON</div>
          <h2>一次抽样，给点估计也给出误差</h2>
          <p className="page-lead">
            按方案的层样本量抽行，后端算 Ŷ = Σ N_h·ȳ_h 与有限总体校正方差，再现场跑一次全量 SUM 做对照。
            抽样是确定性的：同样方案、同样数据集，永远得到同样的样本。
          </p>
        </div>
        <div className="page-head-meta mono">
          <span>{activePlans.length} ACTIVE PLANS</span>
          <span>{queries.items.length} RUNS</span>
        </div>
      </header>

      <div className="queries-layout">
        <section className="panel query-console">
          <div className="panel-head">
            <h3>查询控制台</h3>
            <VialTag code="ALG-2" label="HT+CI" />
          </div>
          <label className="field">
            <span>已审批方案</span>
            <select className="input" value={planId ?? ''} onChange={(event) => setPlanId(Number(event.target.value))}>
              {activePlans.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.code} · n={formatInt(item.sample_size)} · ±{item.expected_ci_pct.toFixed(2)}%
                </option>
              ))}
              {!activePlans.length ? <option value="">没有已审批方案</option> : null}
            </select>
          </label>

          <div className="field">
            <span>查询范围（不选 = 全部层）</span>
            <div className="chip-row">
              {(detail?.strata ?? []).map((row) => {
                const active = strata.includes(row.code);
                return (
                  <button
                    key={row.code}
                    type="button"
                    className={`chip ${active ? 'is-on' : ''}`}
                    onClick={() =>
                      setStrata((current) =>
                        current.includes(row.code) ? current.filter((item) => item !== row.code) : [...current, row.code],
                      )
                    }
                  >
                    {row.label}
                  </button>
                );
              })}
            </div>
          </div>

          <label className="field">
            <span>备注</span>
            <input className="input" value={note} maxLength={120} onChange={(event) => setNote(event.target.value)} />
          </label>

          <div className="console-readout mono">
            <div>
              <span>样本量</span>
              <b>{plan ? formatInt(plan.sample_size) : '—'}</b>
            </div>
            <div>
              <span>置信</span>
              <b>{plan ? `${(plan.confidence_level * 100).toFixed(0)}%` : '—'}</b>
            </div>
            <div>
              <span>全量基线</span>
              <b>{detail ? formatMs(detail.full_scan_baseline_ms) : '—'}</b>
            </div>
          </div>

          <button
            id="run-query"
            className="btn btn-primary"
            disabled={!plan || run.busy || !can(role, 'query:run')}
            onClick={() => void run.run()}
          >
            {run.busy ? '抽样 + 聚合真值 …' : '跑近似查询'}
          </button>
          {!can(role, 'query:run') ? <div className="tiny muted">业务方只读（POST /api/queries/run 会 403）</div> : null}
          {run.error ? <div className="form-error">{run.error}</div> : null}

          <div className="tiny muted">
            查询会顺带跑一次同口径全量聚合（演示库 10 万行，毫秒级），用来给精度自检提供真值。
          </div>
        </section>

        <section className="panel query-result">
          {selected ? (
            <>
              <div className="panel-head">
                <div>
                  <div className="eyebrow">
                    {selected.code} · {selected.plan_name}
                  </div>
                  <h3>{selected.metric_label}的近似估计</h3>
                </div>
                <div className="panel-actions">
                  <VerdictPill verdict={selected.qc_verdict ?? 'pending'} label={selected.qc_verdict ? undefined : '未自检'} size="sm" />
                  <button className="btn btn-sm" disabled={exportMd.busy} onClick={() => void exportMd.run(selected.id)}>
                    导出估算说明
                  </button>
                </div>
              </div>

              <div className="estimate-hero">
                <div className="estimate-main">
                  <span className="readout-label">点估计 Ŷ</span>
                  <b className="mono hero-value">{formatMetric(selected.value_estimate, unit, scale)}</b>
                  <span className="estimate-ci mono">
                    95% CI {formatMetric(selected.ci_low, unit, scale)} ～ {formatMetric(selected.ci_high, unit, scale)}
                    <em>±{selected.rel_error_pct.toFixed(2)}%</em>
                  </span>
                </div>
                <div className="estimate-side mono">
                  <div>
                    <span>全量真值</span>
                    <b>{formatMetric(selected.true_value, unit, scale)}</b>
                  </div>
                  <div>
                    <span>相对误差</span>
                    <b className={selected.truth_rel_error_pct <= target ? 'ok' : 'bad'}>
                      {selected.truth_rel_error_pct.toFixed(2)}%
                    </b>
                  </div>
                  <div>
                    <span>样本</span>
                    <b>{formatInt(selected.sample_size)} 行</b>
                  </div>
                  <div>
                    <span>抽样耗时</span>
                    <b>{formatMs(selected.sample_ms)}</b>
                  </div>
                  <div>
                    <span>提速</span>
                    <b>{formatNumber(selected.speed_ratio, 0)}×</b>
                  </div>
                </div>
              </div>

              <RangeBar
                estimate={selected.value_estimate}
                ciLow={selected.ci_low}
                ciHigh={selected.ci_high}
                truth={selected.true_value}
                tolerancePct={target}
                unit={unit}
                scale={scale}
              />

              <div className="stat-grid three">
                <StatTile label="抽样耗时" value={formatMs(selected.sample_ms)} hint="确定性抽样 + HT 估计" tone="brass" />
                <StatTile label="全量基线" value={formatMs(selected.full_scan_baseline_ms)} hint="生产 8,000 万行扫描" tone="steel" />
                <StatTile
                  label="相对误差"
                  value={`${selected.truth_rel_error_pct.toFixed(2)}%`}
                  hint={`精度标准 ≤ ${target.toFixed(2)}%`}
                  tone={selected.truth_rel_error_pct <= target ? 'pass' : 'fail'}
                />
              </div>

              <RulerBar value={selected.rel_error_pct} target={target} caption="本次 95% CI 半宽 vs 数据集精度标准" />

              <CiPlot rows={ciRows} unit={unit} scale={scale} caption="各层贡献与 95% CI（层内方差分摊）" />

              <CompositionPanel composition={selected.composition} />

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>层</th>
                      <th className="num">N_h</th>
                      <th className="num">n_h</th>
                      <th className="num">样本均值</th>
                      <th className="num">层贡献</th>
                      <th className="num">贡献占比</th>
                      <th className="num">方差占比</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.strata_detail.map((row) => (
                      <tr key={row.code}>
                        <td>
                          {row.label} <span className="mono tiny muted">{row.code}</span>
                        </td>
                        <td className="num mono">{formatInt(row.population)}</td>
                        <td className="num mono">{formatInt(row.sample_size)}</td>
                        <td className="num mono">{formatMetric(row.sample_mean, unit, scale)}</td>
                        <td className="num mono">{formatMetric(row.contribution, unit, scale)}</td>
                        <td className="num mono">{row.contribution_share_pct.toFixed(2)}%</td>
                        <td className="num mono">{row.variance_share_pct.toFixed(2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="tiny muted">
                {selected.created_at} · {selected.run_by} · 过滤：
                {selected.filter_strata.length ? selected.filter_strata.join(' / ') : '全部层'} · 真值聚合实测{' '}
                {formatMs(selected.truth_ms)}
              </div>
            </>
          ) : (
            <EmptyState
              title="还没有跑过查询"
              hint="左侧选一个已审批方案，点「跑近似查询」。会得到点估计、95% 置信区间、全量真值对照与各层贡献。"
              action={plan ? { label: '立即跑一次', onClick: () => void run.run() } : undefined}
            />
          )}
        </section>
      </div>

      <section className="panel query-history">
        <div className="panel-head">
          <h3>查询历史</h3>
          <span className="tiny mono">{queries.items.length} RUNS</span>
        </div>
        {queries.items.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>编号</th>
                  <th>方案</th>
                  <th className="num">样本</th>
                  <th className="num">点估计</th>
                  <th className="num">CI</th>
                  <th className="num">真值</th>
                  <th className="num">相对误差</th>
                  <th className="num">耗时</th>
                  <th>自检</th>
                </tr>
              </thead>
              <tbody>
                {queries.items.map((row) => (
                  <tr key={row.id} className="row-clickable" onClick={() => void queryStore.select(row.id)}>
                    <td className="mono">{row.code}</td>
                    <td>{row.plan_name}</td>
                    <td className="num mono">{formatInt(row.sample_size)}</td>
                    <td className="num mono">{formatMetric(row.value_estimate, unit, scale)}</td>
                    <td className="num mono">±{row.rel_error_pct.toFixed(2)}%</td>
                    <td className="num mono">{formatMetric(row.true_value, unit, scale)}</td>
                    <td className="num mono">{row.truth_rel_error_pct.toFixed(2)}%</td>
                    <td className="num mono">{formatMs(row.sample_ms)}</td>
                    <td>
                      <VerdictPill verdict={row.qc_verdict ?? 'pending'} label={row.qc_verdict ? undefined : '未自检'} size="sm" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="tiny muted">还没有历史查询记录。</div>
        )}
      </section>
    </div>
  );
}
