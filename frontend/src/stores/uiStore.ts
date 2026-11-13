import { createStore } from './base';

export type ToastKind = 'info' | 'ok' | 'warn' | 'error';

export interface Toast {
  id: number;
  kind: ToastKind;
  text: string;
}

export interface UiState {
  toasts: Toast[];
}

const store = createStore<UiState>({ toasts: [] });
let seq = 1;

export const uiStore = {
  subscribe: store.subscribe,
  getState: store.getState,
  toast(text: string, kind: ToastKind = 'info') {
    const id = seq++;
    store.set((state) => ({ toasts: [...state.toasts, { id, kind, text }] }));
    setTimeout(() => uiStore.dismiss(id), 4200);
  },
  dismiss(id: number) {
    store.set((state) => ({ toasts: state.toasts.filter((item) => item.id !== id) }));
  },
};
