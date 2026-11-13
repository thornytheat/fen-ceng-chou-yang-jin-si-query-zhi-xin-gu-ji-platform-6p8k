/** 近似查询 store：跑一次抽样估计，保留历史结果。 */
import { queryApi, type QueryRun } from '../api/queries';
import type { ApproxQuery } from '../types/models';
import { createStore } from './base';

export interface QueryState {
  items: ApproxQuery[];
  selected: ApproxQuery | null;
  loading: boolean;
  running: boolean;
  error: string | null;
}

const store = createStore<QueryState>({ items: [], selected: null, loading: false, running: false, error: null });

async function load(planId?: number): Promise<void> {
  store.set({ loading: true, error: null });
  try {
    const result = await queryApi.list(planId);
    store.set((state) => ({ loading: false, items: result.items, selected: state.selected ?? result.items[0] ?? null }));
  } catch (error) {
    store.set({ loading: false, error: '查询历史加载失败' });
    throw error;
  }
}

async function run(body: QueryRun): Promise<ApproxQuery> {
  store.set({ running: true, error: null });
  try {
    const query = await queryApi.run(body);
    store.set((state) => ({ running: false, items: [query, ...state.items], selected: query }));
    return query;
  } catch (error) {
    store.set({ running: false });
    throw error;
  }
}

async function select(id: number): Promise<void> {
  try {
    const query = await queryApi.detail(id);
    store.set({ selected: query });
  } catch (error) {
    store.set({ error: '查询详情加载失败' });
    throw error;
  }
}

function clearSelection() {
  store.set({ selected: null });
}

export const queryStore = {
  subscribe: store.subscribe,
  getState: store.getState,
  load,
  run,
  select,
  clearSelection,
};
