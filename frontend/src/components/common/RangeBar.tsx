import { formatMetric } from '../../utils/format';

interface Props {
  estimate: number;
  ciLow: number;
  ciHigh: number;
  truth: number;
  tolerancePct: number;
  unit: string;
  scale: number;
}

/** 自绘 SVG：点估计、95% CI 区间、全量真值与精度容差带放在同一把尺上。 */
export default function RangeBar({ estimate, ciLow, ciHigh, truth, tolerancePct, unit, scale }: Props) {
  const width = 560;
  const height = 96;
  const pad = 14;
  const min = Math.min(ciLow, truth * (1 - tolerancePct / 100)) * 0.985;
  const max = Math.max(ciHigh, truth * (1 + tolerancePct / 100)) * 1.015;
  const span = Math.max(max - min, 1);
  const x = (value: number) => pad + ((value - min) / span) * (width - pad * 2);
  const bandLeft = x(truth * (1 - tolerancePct / 100));
  const bandRight = x(truth * (1 + tolerancePct / 100));
  const midY = 46;

  return (
    <div className="range-bar">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="点估计与置信区间">
        <rect className="range-tolerance" x={bandLeft} y={18} width={Math.max(2, bandRight - bandLeft)} height={62} rx={2} />
        <text className="chart-axis" x={pad} y={12}>
          精度容差带 ±{tolerancePct.toFixed(2)}%
        </text>
        <line className="range-axis" x1={pad} y1={midY} x2={width - pad} y2={midY} />
        {Array.from({ length: 9 }).map((_, index) => {
          const r = index / 8;
          return (
            <line
              key={index}
              className="range-tick"
              x1={pad + r * (width - pad * 2)}
              y1={midY}
              x2={pad + r * (width - pad * 2)}
              y2={midY + 6}
            />
          );
        })}
        <line className="range-ci" x1={x(ciLow)} y1={midY} x2={x(ciHigh)} y2={midY} />
        <line className="range-cap" x1={x(ciLow)} y1={midY - 9} x2={x(ciLow)} y2={midY + 9} />
        <line className="range-cap" x1={x(ciHigh)} y1={midY - 9} x2={x(ciHigh)} y2={midY + 9} />
        <circle className="range-point" cx={x(estimate)} cy={midY} r={6} />
        <line className="range-truth" x1={x(truth)} y1={midY - 26} x2={x(truth)} y2={midY + 16} />
        <text className="range-truth-text" x={width - pad} y={12} textAnchor="end">
          真值 {formatMetric(truth, unit, scale)}
        </text>
        <text className="range-est-text" x={x(estimate)} y={midY + 28} textAnchor="middle">
          Ŷ {formatMetric(estimate, unit, scale)}
        </text>
        <text className="chart-axis" x={pad} y={height - 4}>
          {formatMetric(min, unit, scale)}
        </text>
        <text className="chart-axis" x={width - pad} y={height - 4} textAnchor="end">
          {formatMetric(max, unit, scale)}
        </text>
      </svg>
    </div>
  );
}
