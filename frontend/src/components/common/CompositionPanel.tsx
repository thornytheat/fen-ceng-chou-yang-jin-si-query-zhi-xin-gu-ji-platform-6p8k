import { STRATUM_COLORS } from '../../constants/enums';
import { formatPct } from '../../utils/format';
import type { Composition } from '../../types/models';

interface Props {
  composition: Composition | null;
}

/**
 * 线路运费占比与联合误差边界。
 * 点估计最大余数法归一、合计恰为 100.00%；区间为 Bonferroni family-wise 联合边界，
 * 同一组区间同时覆盖全部线路，可直接用于多线路比较。
 * 容量不足时后端拒绝发布：本组件只展示拒绝原因，不渲染任何占比数字。
 */
export default function CompositionPanel({ composition }: Props) {
  if (!composition) {
    return (
      <section className="panel composition-panel">
        <div className="panel-head">
          <h4 className="section-title">线路运费占比与联合误差边界</h4>
        </div>
        <div className="composition-blocked">
          <b>占比结果不可用</b>
          <span className="tiny muted">该查询生成于占比功能上线前，没有占比结果；请重跑近似查询后再查看或导出。</span>
        </div>
      </section>
    );
  }

  const confPct = Math.round(composition.confidence * 100);

  if (!composition.publishable) {
    return (
      <section className="panel composition-panel">
        <div className="panel-head">
          <h4 className="section-title">线路运费占比与联合误差边界</h4>
          <span className="composition-badge is-bad">拒绝发布</span>
        </div>
        <div className="composition-blocked">
          <b>抽样容量不足，占比结果不予发布</b>
          <span className="tiny muted">
            页面、精度自检与导出说明使用同一口径：未通过发布闸门时不输出任何线路占比与误差边界。
          </span>
          <ul className="composition-reasons">
            {composition.reasons.length ? (
              composition.reasons.map((reason) => <li key={reason}>{reason}</li>)
            ) : (
              <li>未提供具体原因，请提高方案样本量后重跑查询。</li>
            )}
          </ul>
        </div>
      </section>
    );
  }

  return (
    <section className="panel composition-panel">
      <div className="panel-head">
        <div>
          <h4 className="section-title">线路运费占比与联合误差边界</h4>
          <span className="tiny muted">
            同一次抽样的 HT 贡献合成，点估计归一后合计 {formatPct(composition.point_total_pct, 2)}
          </span>
        </div>
        <span className="composition-badge is-ok">可发布 · 合计 {formatPct(composition.point_total_pct, 2)}</span>
      </div>

      <div className="composition-stack" role="img" aria-label="各线路运费占比（合计 100%）">
        {composition.rows.map((row, index) => (
          <div
            key={row.code}
            className="composition-segment"
            style={{ width: `${row.point_share_pct}%`, background: STRATUM_COLORS[index % STRATUM_COLORS.length] }}
            title={`${row.label} ${formatPct(row.point_share_pct, 2)}`}
          >
            {row.point_share_pct >= 6 ? <span className="composition-segment-label">{row.point_share_pct.toFixed(1)}%</span> : null}
          </div>
        ))}
      </div>

      <p className="tiny muted composition-method">
        联合边界为 {confPct}% family-wise 置信区间（{composition.method.toUpperCase()}，H={composition.family_size}，z=
        {composition.z_joint}）：同一组区间同时覆盖全部 {composition.family_size} 条线路的真实占比，可直接用于多线路比较；
        单线路边缘区间（z={composition.z_marginal}）仅作参考，不能用于跨线路同时下结论。
      </p>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>线路层</th>
              <th className="num">n_h</th>
              <th className="num">占比点估计</th>
              <th className="num">联合区间（{confPct}% 同时覆盖）</th>
              <th className="num">联合半宽</th>
              <th className="num">单线路边缘半宽</th>
            </tr>
          </thead>
          <tbody>
            {composition.rows.map((row) => (
              <tr key={row.code}>
                <td>
                  {row.label} <span className="mono tiny muted">{row.code}</span>
                  {row.interval_clipped ? <span className="composition-clip-tag">区间已裁剪</span> : null}
                </td>
                <td className="num mono">{row.sample_size}</td>
                <td className="num mono">
                  <b>{formatPct(row.point_share_pct, 2)}</b>
                </td>
                <td className="num mono">
                  {formatPct(row.joint_low_pct, 2)} ～ {formatPct(row.joint_high_pct, 2)}
                </td>
                <td className="num mono">±{formatPct(row.joint_half_pct, 2)} pp</td>
                <td className="num mono muted">±{formatPct(row.marginal_half_pct, 2)} pp</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
