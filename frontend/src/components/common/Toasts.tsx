import { useStore } from '../../hooks/useStore';
import { uiStore } from '../../stores/uiStore';

export default function Toasts() {
  const state = useStore(uiStore);
  if (!state.toasts.length) return null;
  return (
    <div className="toast-stack" role="status" aria-live="polite">
      {state.toasts.map((toast) => (
        <button key={toast.id} className={`toast toast-${toast.kind}`} onClick={() => uiStore.dismiss(toast.id)}>
          <span className="toast-mark" />
          {toast.text}
        </button>
      ))}
    </div>
  );
}
