import { STRATUM_COLORS } from '../../constants/enums';
import { formatInt, formatPct } from '../../utils/format';

export interface StratumChartRow {
  code: string;
  label: string;
  population: number;
  populationSharePct: number;
  sampleSize?: number;
  sampleSharePct?: number;
}

interface Props {
  rows: StratumChartRow[];
  caption: string;
  showSample: boolean;
}

/** 自绘 SVG：每层的层容量占比 vs 本次样本占比。 */
export default function StratumChart({ rows, caption, showSample }: Props) {
  const width = 560;
  const rowHeight = showSample ? 40 : 30;
  const top = 26;
  const height = top + rows.length * rowHeight + 18;
  const labelWidth = 116;
  const barWidth = width - labelWidth - 74;
  const maxShare = Math.max(...rows.map((row) => Math.max(row.populationSharePct, row.sampleSharePct ?? 0)), 10);

  return (
    <figure className="stratum-chart">
      <figcaption>{caption}</figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={caption}>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
          <line
            key={ratio}
            className="chart-grid"
            x1={labelWidth + ratio * barWidth}
            y1={top - 6}
            x2={labelWidth + ratio * barWidth}
            y2={height - 16}
          />
        ))}
        <text className="chart-axis" x={labelWidth} y={13}>
          0%
        </text>
        <text className="chart-axis" x={labelWidth + barWidth} y={13} textAnchor="end">
          {formatPct(maxShare, 0)}
        </text>
        {rows.map((row, index) => {
          const y = top + index * rowHeight;
          const color = STRATUM_COLORS[index % STRATUM_COLORS.length];
          const popWidth = (row.populationSharePct / maxShare) * barWidth;
          const sampleWidth = ((row.sampleSharePct ?? 0) / maxShare) * barWidth;
          return (
            <g key={row.code}>
              <text className="chart-label" x={0} y={y + (showSample ? 14 : 15)}>
                {row.label}
              </text>
              <text className="chart-sub" x={0} y={y + (showSample ? 27 : 26)}>
                {row.code}
              </text>
              <rect className="chart-track" x={labelWidth} y={y + 2} width={barWidth} height={7} rx={1} />
              <rect x={labelWidth} y={y + 2} width={popWidth} height={7} rx={1} fill={color} opacity={0.34} />
              <text className="chart-value" x={width - 4} y={y + 9} textAnchor="end">
                {formatPct(row.populationSharePct, 1)} · {formatInt(row.population)}
              </text>
              {showSample ? (
                <>
                  <rect className="chart-track" x={labelWidth} y={y + 15} width={barWidth} height={7} rx={1} />
                  <rect x={labelWidth} y={y + 15} width={sampleWidth} height={7} rx={1} fill={color} />
                  <text className="chart-value strong" x={width - 4} y={y + 22} textAnchor="end">
                    {formatInt(row.sampleSize ?? 0)} 行
                  </text>
                </>
              ) : null}
            </g>
          );
        })}
      </svg>
      <div className="chart-legend">
        <span>
          <i className="legend-pop" /> 层容量占比
        </span>
        {showSample ? (
          <span>
            <i className="legend-sample" /> 分配样本量
          </span>
        ) : null}
      </div>
    </figure>
  );
}
