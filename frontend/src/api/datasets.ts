import { http } from './client';
import type { Dataset, ListEnvelope, Stratum } from '../types/models';

export interface DatasetPatch {
  precision_target_pct?: number;
  confidence_level?: number;
  note?: string;
}

export const datasetApi = {
  list: () => http.get<ListEnvelope<Dataset>>('/datasets'),
  detail: (id: number) => http.get<Dataset>(`/datasets/${id}`),
  strata: (id: number) => http.get<ListEnvelope<Stratum>>(`/datasets/${id}/strata`),
  patch: (id: number, body: DatasetPatch) => http.patch<Dataset>(`/datasets/${id}`, body),
  refreshTruth: (id: number) =>
    http.post<{ task_id: string | null; queued: boolean; message: string }>(`/datasets/${id}/refresh-truth`),
};
