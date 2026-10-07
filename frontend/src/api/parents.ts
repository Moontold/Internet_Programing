import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from './client';
import type { Parent, ParentCreate, ParentUpdate } from './types';

const KEY = 'parents';

export const useParents = () =>
  useQuery({ queryKey: [KEY], queryFn: () => api.get<{ parents: Parent[] }>('/parents').then((r) => r.parents) });

export const useParent = (id: number) =>
  useQuery({ queryKey: [KEY, id], queryFn: () => api.get<Parent>(`/parents/${id}`), enabled: Number.isFinite(id) });

export function useCreateParent() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (data: ParentCreate) => api.post<{ parent: Parent; password: string }>('/parents', data),
    onSuccess: () => client.invalidateQueries({ queryKey: [KEY] }),
  });
}

export function useUpdateParent(id: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (data: ParentUpdate) => api.patch<Parent>(`/parents/${id}`, data),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: [KEY] });
      client.invalidateQueries({ queryKey: ['students'] });
    },
  });
}

export const useResetParentPassword = (id: number) =>
  useMutation({
    mutationFn: () => api.post<{ password: string }>(`/parents/${id}/reset-password`).then((r) => r.password),
  });
