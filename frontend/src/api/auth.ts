import { api } from './client';
import type { Profile } from './types';

export const authApi = {
  me: () => api.get<Profile>('/auth/me'),
  login: (login: string, password: string) => api.post<Profile>('/auth/login', { login, password }),
  logout: () => api.post<null>('/auth/logout'),
  changePassword: (old_password: string, new_password: string) =>
    api.post<null>('/auth/change-password', { old_password, new_password }),
};
