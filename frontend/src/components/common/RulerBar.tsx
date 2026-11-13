interface Props {
  value: number;
  target: number;
  max?: number;
  unit?: string;
  caption: string;
  lowerIsBetter?: boolean;
}

/** 量具刻度条：把「实测值 / 目标阈值」画在带刻度的尺子上。 */
export default function RulerBar({ value, target, max, unit = '%', caption, lowerIsBetter = true }: Props) {
  const ceiling = max ?? Math.max(target * 2.4, value * 1.35, 1);
  const ratio = Math.min(1.06, Math.max(0, value / ceiling));
  const targetRatio = Math.min(1.06, Math.max(0, target / ceiling));
  const width = 520;
  const height = 58;
  const x = (r: number) => 8 + r * (width - 16);
  const ok = lowerIsBetter ? value <= target : value >= target;

  return (
    <div className="ruler-bar">
      <div className="ruler-caption">
        <span>{caption}</span>
        <span className={`ruler-reading ${ok ? 'is-ok' : 'is-bad'}`}>
          {value.toFixed(2)}
          {unit}
          <em>阈值 {target.toFixed(2)}{unit}</em>
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={caption}>
        <line className="ruler-rail" x1={x(0)} y1={30} x2={x(1)} y2={30} />
        {Array.from({ length: 21 }).map((_, index) => {
          const r = index / 20;
          const tall = index % 5 === 0;
          return (
            <line
              key={index}
              className={tall ? 'ruler-tick tall' : 'ruler-tick'}
              x1={x(r)}
              y1={30}
              x2={x(r)}
              y2={tall ? 16 : 22}
            />
          );
        })}
        <line className="ruler-target" x1={x(targetRatio)} y1={10} x2={x(targetRatio)} y2={44} />
        <text className="ruler-target-text" x={x(targetRatio)} y={8} textAnchor="middle">
          {target.toFixed(2)}
          {unit}
        </text>
        <g transform={`translate(${x(ratio)},30)`}>
          <polygon className="ruler-needle" points="0,-9 5,0 0,9 -5,0" />
          <line className="ruler-needle-stem" x1="0" y1="0" x2="0" y2="18" />
        </g>
        <text className="ruler-min" x={x(0)} y={54}>
          0
        </text>
        <text className="ruler-max" x={x(1)} y={54} textAnchor="end">
          {ceiling.toFixed(2)}
          {unit}
        </text>
      </svg>
    </div>
  );
}
