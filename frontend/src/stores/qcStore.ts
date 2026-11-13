/** 精度自检 store：检查项 + 三角色复核链。 */
import { qcApi, type SignoffPayload } from '../api/qc';
import type { QcCheck } from '../types/models';
import { createStore } from './base';

export interface QcState {
  items: QcCheck[];
  selected: QcCheck | null;
  loading: boolean;
  running: boolean;
  signing: boolean;
  error: string | null;
}

const store = createStore<QcState>({
  items: [],
  selected: null,
  loading: false,
  running: false,
  signing: false,
  error: null,
});

async function load(): Promise<void> {
  store.set({ loading: true, error: null });
  try {
    const result = await qcApi.list();
    store.set((state) => ({ loading: false, items: result.items, selected: state.selected ?? result.items[0] ?? null }));
  } catch (error) {
    store.set({ loading: false, error: '自检记录加载失败' });
    throw error;
  }
}

async function run(queryId: number): Promise<QcCheck> {
  store.set({ running: true, error: null });
  try {
    const qc = await qcApi.run({ query_id: queryId });
    store.set((state) => ({
      running: false,
      items: [qc, ...state.items.filter((item) => item.id !== qc.id)],
      selected: qc,
    }));
    return qc;
  } catch (error) {
    store.set({ running: false });
    throw error;
  }
}

async function signoff(id: number, payload: SignoffPayload): Promise<QcCheck> {
  store.set({ signing: true });
  try {
    const result = await qcApi.signoff(id, payload);
    store.set((state) => ({
      signing: false,
      items: state.items.map((item) => (item.id === id ? result.qc : item)),
      selected: result.qc,
    }));
    return result.qc;
  } catch (error) {
    store.set({ signing: false });
    throw error;
  }
}

function select(qc: QcCheck | null) {
  store.set({ selected: qc });
}

export const qcStore = {
  subscribe: store.subscribe,
  getState: store.getState,
  load,
  run,
  signoff,
  select,
};
