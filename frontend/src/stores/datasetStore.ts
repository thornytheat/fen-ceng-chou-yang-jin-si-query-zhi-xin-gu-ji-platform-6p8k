/** 数据集 store：列表 + 当前档案 + 精度标准维护。 */
import { datasetApi, type DatasetPatch } from '../api/datasets';
import type { Dataset } from '../types/models';
import { createStore } from './base';

export interface DatasetState {
  items: Dataset[];
  detail: Dataset | null;
  selectedId: number | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
}

const store = createStore<DatasetState>({
  items: [],
  detail: null,
  selectedId: null,
  loading: false,
  saving: false,
  error: null,
});

async function load(): Promise<void> {
  store.set({ loading: true, error: null });
  try {
    const result = await datasetApi.list();
    const selectedId = store.getState().selectedId ?? result.items[0]?.id ?? null;
    store.set({ items: result.items, loading: false });
    if (selectedId) await select(selectedId);
  } catch (error) {
    store.set({ loading: false, error: '数据集加载失败' });
    throw error;
  }
}

async function select(id: number): Promise<void> {
  store.set({ selectedId: id });
  try {
    const detail = await datasetApi.detail(id);
    store.set({ detail });
  } catch (error) {
    store.set({ error: '数据集详情加载失败' });
    throw error;
  }
}

async function patch(id: number, body: DatasetPatch): Promise<Dataset> {
  store.set({ saving: true });
  try {
    const detail = await datasetApi.patch(id, body);
    store.set((state) => ({
      saving: false,
      detail,
      items: state.items.map((item) => (item.id === id ? detail : item)),
    }));
    return detail;
  } catch (error) {
    store.set({ saving: false });
    throw error;
  }
}

async function refreshTruth(id: number) {
  const result = await datasetApi.refreshTruth(id);
  window.setTimeout(() => {
    void select(id).catch(() => undefined);
  }, 1400);
  return result;
}

export const datasetStore = {
  subscribe: store.subscribe,
  getState: store.getState,
  load,
  select,
  patch,
  refreshTruth,
};
