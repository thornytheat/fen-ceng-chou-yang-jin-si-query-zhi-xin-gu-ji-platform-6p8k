import { http } from './client';
import type { LoginResult, UserInfo } from '../types/models';

export const authApi = {
  login: (email: string, password: string) =>
    http.post<LoginResult>('/auth/login', { email, password }),
  me: () => http.get<{ user: UserInfo }>('/auth/me'),
};
