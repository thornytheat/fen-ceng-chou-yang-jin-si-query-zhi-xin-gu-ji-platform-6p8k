import { http } from './client';
import type { HealthInfo } from '../types/models';

export const healthApi = {
  check: () => http.get<HealthInfo>('/health'),
};
