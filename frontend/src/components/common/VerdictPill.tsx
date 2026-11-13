interface Props {
  verdict: string;
  label?: string;
  size?: 'sm' | 'md';
}

const TEXT: Record<string, string> = { pass: '达标', fail: '未达标', pending: '待签', draft: '草稿', active: '已审批', archived: '已归档' };

export default function VerdictPill({ verdict, label, size = 'md' }: Props) {
  return (
    <span className={`verdict verdict-${verdict} ${size === 'sm' ? 'verdict-sm' : ''}`}>
      <i />
      {label ?? TEXT[verdict] ?? verdict}
    </span>
  );
}
