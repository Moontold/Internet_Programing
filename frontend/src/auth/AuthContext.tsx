import { useQuery, useQueryClient } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, type ReactNode } from 'react';

import { authApi } from '../api/auth';
import { ApiError, AUTH_LOGOUT_EVENT } from '../api/client';
import type { Profile } from '../api/types';

interface AuthValue {
  user: Profile | null;
  isLoading: boolean;
  login: (login: string, password: string) => Promise<Profile>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);
const ME_KEY = ['auth', 'me'];

export function AuthProvider({ children }: { children: ReactNode }) {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        return await authApi.me();
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    const handler = () => {
      client.setQueryData(ME_KEY, null);
      client.removeQueries({ predicate: (item) => item.queryKey[0] !== 'auth' });
    };
    window.addEventListener(AUTH_LOGOUT_EVENT, handler);
    return () => window.removeEventListener(AUTH_LOGOUT_EVENT, handler);
  }, [client]);

  const login = useCallback(
    async (loginValue: string, password: string) => {
      const profile = await authApi.login(loginValue, password);
      client.setQueryData(ME_KEY, profile);
      return profile;
    },
    [client],
  );

  const logout = useCallback(async () => {
    await authApi.logout();
    client.setQueryData(ME_KEY, null);
    client.clear();
  }, [client]);

  return (
    <AuthContext.Provider value={{ user: query.data ?? null, isLoading: query.isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth outside AuthProvider');
  return value;
}

export function homeFor(role: Profile['role']): string {
  if (role === 'tutor') return '/schedule';
  if (role === 'parent') return '/children';
  return '/my/schedule';
}
