import { http } from './client';
import type { ApproxQuery, ListEnvelope } from '../types/models';

export interface QueryRun {
  plan_id: number;
  strata?: string[];
  note?: string;
}

export const queryApi = {
  list: (planId?: number) =>
    http.get<ListEnvelope<ApproxQuery>>(`/queries${planId ? `?plan_id=${planId}` : ''}`),
  detail: (id: number) => http.get<ApproxQuery>(`/queries/${id}`),
  run: (body: QueryRun) => http.post<ApproxQuery>('/queries/run', body),
  exportMarkdown: (id: number) => http.text(`/queries/${id}/export`),
};
