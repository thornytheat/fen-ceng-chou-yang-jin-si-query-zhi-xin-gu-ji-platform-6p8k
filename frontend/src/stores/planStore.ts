/** 抽样方案 store：创建即算分配，审批后才可跑查询。 */
import { planApi, type PlanCreate } from '../api/plans';
import type { Plan } from '../types/models';
import { createStore } from './base';

export interface PlanState {
  items: Plan[];
  selected: Plan | null;
  loading: boolean;
  creating: boolean;
  error: string | null;
}

const store = createStore<PlanState>({ items: [], selected: null, loading: false, creating: false, error: null });

async function load(datasetId?: number): Promise<void> {
  store.set({ loading: true, error: null });
  try {
    const result = await planApi.list(datasetId);
    // 默认选“已审批且精度最高”的方案，避免误把草稿/粗口径当成主口径
    const actives = result.items
      .filter((item) => item.status === 'active')
      .sort((a, b) => a.target_error_pct - b.target_error_pct);
    const preferred = actives[0] ?? result.items[0] ?? null;
    store.set((state) => ({
      loading: false,
      items: result.items,
      selected: state.selected ?? preferred,
    }));
  } catch (error) {
    store.set({ loading: false, error: '方案加载失败' });
    throw error;
  }
}

async function create(body: PlanCreate): Promise<Plan> {
  store.set({ creating: true });
  try {
    const plan = await planApi.create(body);
    store.set((state) => ({ creating: false, items: [plan, ...state.items], selected: plan }));
    return plan;
  } catch (error) {
    store.set({ creating: false });
    throw error;
  }
}

function select(plan: Plan | null) {
  store.set({ selected: plan });
}

async function approve(id: number): Promise<Plan> {
  const plan = await planApi.approve(id);
  store.set((state) => ({
    items: state.items.map((item) => (item.id === id ? plan : item)),
    selected: state.selected?.id === id ? plan : state.selected,
  }));
  return plan;
}

async function archive(id: number): Promise<Plan> {
  const plan = await planApi.archive(id);
  store.set((state) => ({
    items: state.items.map((item) => (item.id === id ? plan : item)),
    selected: state.selected?.id === id ? plan : state.selected,
  }));
  return plan;
}

export const planStore = {
  subscribe: store.subscribe,
  getState: store.getState,
  load,
  create,
  select,
  approve,
  archive,
};
