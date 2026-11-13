import { uiStore } from '../stores/uiStore';

/** 统一提示入口（toast 生命周期由 uiStore 管理）。 */
export function useToast() {
  return {
    info: (text: string) => uiStore.toast(text, 'info'),
    ok: (text: string) => uiStore.toast(text, 'ok'),
    warn: (text: string) => uiStore.toast(text, 'warn'),
    error: (text: string) => uiStore.toast(text, 'error'),
  };
}
