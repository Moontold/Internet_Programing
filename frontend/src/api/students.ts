import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api, qs } from './client';
import type { Student, StudentCreate, StudentListItem, StudentUpdate } from './types';

const KEY = 'students';

export const useStudents = (isActive?: boolean) =>
  useQuery({
    queryKey: [KEY, { isActive }],
    queryFn: () =>
      api.get<{ students: StudentListItem[] }>(`/students${qs({ is_active: isActive })}`).then((r) => r.students),
  });

export const useStudent = (id: number) =>
  useQuery({ queryKey: [KEY, id], queryFn: () => api.get<Student>(`/students/${id}`), enabled: Number.isFinite(id) });

export function useCreateStudent() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (data: StudentCreate) => api.post<{ student: Student; password: string }>('/students', data),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: [KEY] });
      client.invalidateQueries({ queryKey: ['parents'] });
    },
  });
}

export function useUpdateStudent(id: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (data: StudentUpdate) => api.patch<Student>(`/students/${id}`, data),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: [KEY] });
      client.invalidateQueries({ queryKey: ['parents'] });
    },
  });
}

export const useResetStudentPassword = (id: number) =>
  useMutation({
    mutationFn: () => api.post<{ password: string }>(`/students/${id}/reset-password`).then((r) => r.password),
  });
