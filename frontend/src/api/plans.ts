import { http } from './client';
import type { ListEnvelope, Plan } from '../types/models';

export interface PlanCreate {
  dataset_id: number;
  name: string;
  confidence_level: number;
  target_error_pct: number;
  method: string;
  note?: string;
}

export const planApi = {
  list: (datasetId?: number) =>
    http.get<ListEnvelope<Plan>>(`/plans${datasetId ? `?dataset_id=${datasetId}` : ''}`),
  detail: (id: number) => http.get<Plan>(`/plans/${id}`),
  create: (body: PlanCreate) => http.post<Plan>('/plans', body),
  approve: (id: number) => http.post<Plan>(`/plans/${id}/approve`),
  archive: (id: number) => http.post<Plan>(`/plans/${id}/archive`),
};
