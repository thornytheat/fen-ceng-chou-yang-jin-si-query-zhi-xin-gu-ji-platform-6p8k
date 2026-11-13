import { useEffect, useState } from 'react';
import { useStore } from '../hooks/useStore';
import { datasetStore } from '../stores/datasetStore';
import { authStore } from '../stores/authStore';
import { useAsync } from '../hooks/useAsync';
import { useToast } from '../hooks/useToast';
import StatTile from '../components/common/StatTile';
import StratumChart from '../components/common/StratumChart';
import VialTag from '../components/common/VialTag';
import EmptyState from '../components/common/EmptyState';
import { formatInt, formatMetric, formatMs, formatNumber } from '../utils/format';

export default function Datasets() {
  const auth = useStore(authStore);
  const state = useStore(datasetStore);
  const toast = useToast();
  const isAdmin = auth.user?.role === 'admin';
  const selected = state.detail;
  const [target, setTarget] = useState(2);
  const [confidence, setConfidence] = useState(0.95);
  const [note, setNote] = useState('');

  useEffect(() => {
    void datasetStore.load().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!selected) return;
    setTarget(selected.precision_target_pct);
    setConfidence(selected.confidence_level);
    setNote(selected.note ?? '');
  }, [selected?.id, selected?.updated_at]);

  const save = useAsync(async () => {
    if (!selected) return null;
    const detail = await datasetStore.patch(selected.id, {
      precision_target_pct: target,
      confidence_level: confidence,
      note,
    });
    toast.ok(`精度标准已更新：相对误差 ≤ ${detail.precision_target_pct.toFixed(2)}%`);
    return detail;
  });

  const refresh = useAsync(async () => {
    if (!selected) return null;
    const result = await datasetStore.refreshTruth(selected.id);
    toast.info(result.message);
    return result;
  });

  const strata = selected?.strata ?? [];
  const chartRows = strata.map((row) => ({
    code: row.code,
    label: row.label,
    population: row.population,
    populationSharePct: row.population_share_pct,
  }));

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <div className="eyebrow">DATASET INVENTORY · 分层抽样框</div>
          <h2>三份数据集，五个线路层</h2>
          <p className="page-lead">
            分层字段、层容量 N_h 与先验标准差 S_h 都来自上一期普查。抽样方案与近似查询只读这里，
            不改明细；精度标准由分析负责人校准。
          </p>
        </div>
        <div className="page-head-meta mono">
          <span>{formatInt(state.items.reduce((sum, item) => sum + item.row_count, 0))} ROWS</span>
          <span>5 STRATA</span>
          <span>{state.items.length || 3} SETS</span>
        </div>
      </header>

      {state.error && !state.items.length ? (
        <EmptyState
          tone="error"
          title="数据集没有加载出来"
          hint="后端或数据库可能还在启动。重试即可，不会丢数据。"
          action={{ label: '重新加载', onClick: () => void datasetStore.load().catch(() => undefined) }}
        />
      ) : null}

      <div className="lab-grid">
        <section className="panel panel-list">
          <div className="panel-head">
            <h3>样品档案</h3>
            <span className="tiny mono">{state.items.length} SETS</span>
          </div>
          <div className="dataset-list">
            {state.items.map((item, index) => (
              <button
                key={item.id}
                className={`dataset-card ${selected?.id === item.id ? 'is-active' : ''}`}
                onClick={() => void datasetStore.select(item.id)}
              >
                <div className="dataset-card-top">
                  <VialTag code={`DS-${String(index + 1).padStart(2, '0')}`} tone={index === 0 ? 'brass' : 'steel'} />
                  <span className={`mini-state ${item.row_count ? 'is-loaded' : 'is-empty'}`}>
                    {item.row_count ? '已载入' : '空'}
                  </span>
                </div>
                <div className="dataset-card-name">{item.name}</div>
                <div className="dataset-card-meta mono">
                  {formatInt(item.row_count)} 行 · {item.strata_count} 层 · 目标 {item.precision_target_pct.toFixed(1)}%
                </div>
                <div className="dataset-card-bars" aria-hidden="true">
                  {item.strata?.length
                    ? null
                    : Array.from({ length: 5 }).map((_, idx) => (
                        <i key={idx} style={{ width: `${18 + idx * 9}%` }} />
                      ))}
                </div>
              </button>
            ))}
          </div>
          {!state.items.length && !state.error ? <div className="tiny muted">正在读取数据集 …</div> : null}
        </section>

        {selected ? (
          <section className="panel panel-detail">
            <div className="panel-head">
              <div>
                <div className="eyebrow">
                  {selected.code} · 先验口径 {selected.prior_period}
                </div>
                <h3>{selected.name}</h3>
              </div>
              <VialTag code={`${selected.strata_count} STRATA`} label={selected.strata_field} />
            </div>
            <p className="panel-body-text">{selected.scenario}</p>

            <div className="stat-grid">
              <StatTile label="演示明细行" value={formatInt(selected.row_count)} unit="行" hint={`生产表 ${formatInt(selected.source_rows)} 行`} />
              <StatTile label="全量真值" value={formatMetric(selected.truth_total, selected.unit, selected.unit_scale)} hint="真实 SUM 聚合" tone="brass" />
              <StatTile label="全量基线" value={formatMs(selected.full_scan_baseline_ms)} hint="生产扫描耗时" tone="steel" />
              <StatTile
                label="精度标准"
                value={`±${selected.precision_target_pct.toFixed(2)}`}
                unit="%"
                hint={`置信 ${(selected.confidence_level * 100).toFixed(0)}%`}
                tone={isAdmin ? 'pass' : 'plain'}
              />
            </div>

            <div className="chart-row">
              <StratumChart rows={chartRows} caption="层容量占比（N_h / N）" showSample={false} />
              <div className="detail-side">
                <h4>字段口径</h4>
                <dl className="kv">
                  <div>
                    <dt>分层字段</dt>
                    <dd className="mono">{selected.strata_field}</dd>
                  </div>
                  <div>
                    <dt>指标字段</dt>
                    <dd className="mono">{selected.value_field}</dd>
                  </div>
                  <div>
                    <dt>指标</dt>
                    <dd>{selected.metric_label}</dd>
                  </div>
                  <div>
                    <dt>单位</dt>
                    <dd>
                      {selected.unit}（×{selected.unit_scale} 最小单位）
                    </dd>
                  </div>
                  <div>
                    <dt>已建方案</dt>
                    <dd className="mono">{selected.plan_count}</dd>
                  </div>
                  <div>
                    <dt>已跑查询</dt>
                    <dd className="mono">{selected.query_count}</dd>
                  </div>
                </dl>
                <button className="btn btn-sm" disabled={!isAdmin || refresh.busy} onClick={() => void refresh.run()}>
                  {refresh.busy ? '投递中 …' : '刷新全量真值'}
                </button>
                {!isAdmin ? <div className="tiny muted">刷新基线需要分析负责人权限</div> : null}
                {selected.measured_full_scan_ms ? (
                  <div className="tiny muted">演示库实测全量聚合 {formatMs(selected.measured_full_scan_ms)}</div>
                ) : null}
              </div>
            </div>

            <h4 className="section-title">分层明细（N_h / 先验 S_h / 层均值）</h4>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>层</th>
                    <th className="num">层容量 N_h</th>
                    <th className="num">占比</th>
                    <th className="num">先验 S_h</th>
                    <th className="num">层均值</th>
                    <th className="num">最小样本</th>
                  </tr>
                </thead>
                <tbody>
                  {strata.map((row) => (
                    <tr key={row.code}>
                      <td>
                        <span className="stratum-name">{row.label}</span>
                        <span className="mono tiny muted"> {row.code}</span>
                      </td>
                      <td className="num mono">{formatInt(row.population)}</td>
                      <td className="num mono">{formatNumber(row.population_share_pct, 2)}%</td>
                      <td className="num mono">{formatMetric(row.prior_std, selected.unit, selected.unit_scale)}</td>
                      <td className="num mono">{formatMetric(row.mean_value, selected.unit, selected.unit_scale)}</td>
                      <td className="num mono">{row.min_sample}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className={`calibrate ${isAdmin ? '' : 'is-readonly'}`}>
              <div className="panel-head">
                <h4>精度标准 · {isAdmin ? '可校准' : '只读'}</h4>
                <span className="tiny mono">ADMIN ONLY</span>
              </div>
              <div className="calibrate-grid">
                <label className="field">
                  <span>目标相对误差（%）</span>
                  <input
                    className="input"
                    type="number"
                    min={0.5}
                    max={20}
                    step={0.1}
                    value={target}
                    disabled={!isAdmin}
                    onChange={(event) => setTarget(Number(event.target.value))}
                  />
                </label>
                <label className="field">
                  <span>默认置信度</span>
                  <select
                    className="input"
                    value={confidence}
                    disabled={!isAdmin}
                    onChange={(event) => setConfidence(Number(event.target.value))}
                  >
                    {[0.8, 0.9, 0.95, 0.99].map((item) => (
                      <option key={item} value={item}>
                        {(item * 100).toFixed(0)}%
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field field-wide">
                  <span>口径备注</span>
                  <input
                    className="input"
                    value={note}
                    disabled={!isAdmin}
                    onChange={(event) => setNote(event.target.value)}
                    placeholder="例如：经营会口径，误差超过 2% 不上会"
                  />
                </label>
                <button id="save-standard" className="btn btn-primary" disabled={!isAdmin || save.busy} onClick={() => void save.run()}>
                  {save.busy ? '写入口径 …' : '保存精度标准'}
                </button>
              </div>
              {save.error ? <div className="form-error">{save.error}</div> : null}
              <div className="tiny muted">
                站点口径：精度标准只影响「精度自检」的判定，不改抽样算法；判定永远按当前标准实时计算。
              </div>
            </div>
          </section>
        ) : (
          <section className="panel">
            <EmptyState title="先选一个数据集" hint="左侧样品档案里选一份，就能看到分层与精度标准。" />
          </section>
        )}
      </div>
    </div>
  );
}
