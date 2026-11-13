interface Props {
  code: string;
  label?: string;
  tone?: 'brass' | 'steel';
}

/** 样品瓶标签：实验室里的编号牌。 */
export default function VialTag({ code, label, tone = 'brass' }: Props) {
  return (
    <span className={`vial-tag tone-${tone}`}>
      <i aria-hidden="true" />
      <b>{code}</b>
      {label ? <em>{label}</em> : null}
    </span>
  );
}
