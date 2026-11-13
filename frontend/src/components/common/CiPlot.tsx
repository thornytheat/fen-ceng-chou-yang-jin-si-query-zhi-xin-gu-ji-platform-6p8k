import { STRATUM_COLORS } from '../../constants/enums';
import { formatMetric } from '../../utils/format';

export interface CiRow {
  code: string;
  label: string;
  contribution: number;
  ciHalf: number;
  sharePct: number;
}

interface Props {
  rows: CiRow[];
  unit: string;
  scale: number;
  caption: string;
}

/** 自绘 SVG：各层贡献点估计 + 95% CI 误差棒（层内方差分摊）。 */
export default function CiPlot({ rows, unit, scale, caption }: Props) {
  const width = 560;
  const rowHeight = 34;
  const top = 24;
  const height = top + rows.length * rowHeight + 30;
  const labelWidth = 118;
  const plotWidth = width - labelWidth - 116;
  const maxValue = Math.max(...rows.map((row) => row.contribution + row.ciHalf), 1);
  const x = (value: number) => labelWidth + (value / maxValue) * plotWidth;

  return (
    <figure className="ci-plot">
      <figcaption>{caption}</figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={caption}>
        {[0, 0.5, 1].map((ratio) => (
          <line
            key={ratio}
            className="chart-grid"
            x1={labelWidth + ratio * plotWidth}
            y1={top - 8}
            x2={labelWidth + ratio * plotWidth}
            y2={height - 24}
          />
        ))}
        <text className="chart-axis" x={labelWidth} y={13}>
          0
        </text>
        <text className="chart-axis" x={labelWidth + plotWidth} y={13} textAnchor="end">
          {formatMetric(maxValue, unit, scale)}
        </text>
        {rows.map((row, index) => {
          const y = top + index * rowHeight + 10;
          const color = STRATUM_COLORS[index % STRATUM_COLORS.length];
          const left = x(Math.max(0, row.contribution - row.ciHalf));
          const right = x(row.contribution + row.ciHalf);
          return (
            <g key={row.code}>
              <text className="chart-label" x={0} y={y + 2}>
                {row.label}
              </text>
              <text className="chart-sub" x={0} y={y + 14}>
                贡献 {row.sharePct.toFixed(1)}%
              </text>
              <line className="ci-line" x1={left} y1={y} x2={right} y2={y} stroke={color} />
              <line className="ci-cap" x1={left} y1={y - 5} x2={left} y2={y + 5} stroke={color} />
              <line className="ci-cap" x1={right} y1={y - 5} x2={right} y2={y + 5} stroke={color} />
              <circle cx={x(row.contribution)} cy={y} r={4.2} fill={color} />
              <text className="chart-value" x={width - 4} y={y + 3} textAnchor="end">
                {formatMetric(row.contribution, unit, scale)}
              </text>
              <text className="chart-sub" x={width - 4} y={y + 15} textAnchor="end">
                ±{formatMetric(row.ciHalf, unit, scale)}
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
