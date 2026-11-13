interface Props {
  title: string;
  hint: string;
  action?: { label: string; onClick: () => void };
  tone?: 'plain' | 'error';
}

export default function EmptyState({ title, hint, action, tone = 'plain' }: Props) {
  return (
    <div className={`empty-state ${tone === 'error' ? 'is-error' : ''}`}>
      <div className="empty-ruler" aria-hidden="true">
        {Array.from({ length: 13 }).map((_, index) => (
          <i key={index} className={index % 3 === 0 ? 'tall' : ''} />
        ))}
      </div>
      <h3>{title}</h3>
      <p>{hint}</p>
      {action ? (
        <button className="btn btn-sm" onClick={action.onClick}>
          {action.label}
        </button>
      ) : null}
    </div>
  );
}
