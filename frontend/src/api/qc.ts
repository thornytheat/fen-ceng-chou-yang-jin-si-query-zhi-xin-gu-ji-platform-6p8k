import { http } from './client';
import type { ListEnvelope, QcCheck } from '../types/models';

export interface QcRun {
  query_id: number;
  target_pct?: number;
}

export interface SignoffPayload {
  stage: string;
  decision: 'approve' | 'reject';
  note?: string;
}

export const qcApi = {
  list: () => http.get<ListEnvelope<QcCheck>>('/qc'),
  detail: (id: number) => http.get<QcCheck>(`/qc/${id}`),
  run: (body: QcRun) => http.post<QcCheck>('/qc', body),
  signoff: (id: number, body: SignoffPayload) =>
    http.post<{ qc: QcCheck; message: string }>(`/qc/${id}/signoff`, body),
};
