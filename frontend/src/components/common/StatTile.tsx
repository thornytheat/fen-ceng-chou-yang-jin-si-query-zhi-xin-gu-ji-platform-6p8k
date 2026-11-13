interface Props {
  label: string;
  value: string;
  unit?: string;
  hint?: string;
  tone?: 'plain' | 'brass' | 'steel' | 'pass' | 'fail';
}

export default function StatTile({ label, value, unit, hint, tone = 'plain' }: Props) {
  return (
    <div className={`stat-tile tone-${tone}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">
        {value}
        {unit ? <small>{unit}</small> : null}
      </div>
      {hint ? <div className="stat-hint">{hint}</div> : null}
    </div>
  );
}
