import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { toIso } from '../lib/dates';
import { api, qs } from './client';
import type { Lesson, LessonCreate, LessonShort, LessonUpdate, ParticipantUpdate, Scope } from './types';

export const LESSONS_KEY = 'lessons';

export type CancelScope = Exclude<Scope, 'all'>;

export const useLessons = (start: Date, end: Date, studentId?: number) =>
  useQuery({
    queryKey: [LESSONS_KEY, 'range', toIso(start), toIso(end), studentId ?? null],
    queryFn: () =>
      api
        .get<{ lessons: LessonShort[] }>(`/lessons${qs({ start: toIso(start), end: toIso(end), student_id: studentId })}`)
        .then((r) => r.lessons),
  });

export const useLesson = (id: number) =>
  useQuery({ queryKey: [LESSONS_KEY, id], queryFn: () => api.get<Lesson>(`/lessons/${id}`), enabled: Number.isFinite(id) });

export function useScheduleMutation<TVars>(fn: (vars: TVars) => Promise<unknown>) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: [LESSONS_KEY] });
      client.invalidateQueries({ queryKey: ['students'] });
      client.invalidateQueries({ queryKey: ['cabinet'] });
    },
  });
}

export const useCreateLesson = () => useScheduleMutation((data: LessonCreate) => api.post<Lesson>('/lessons', data));

export const useUpdateLesson = (id: number) =>
  useScheduleMutation((data: LessonUpdate) => api.patch<Lesson>(`/lessons/${id}`, data));

export const useMoveLesson = () =>
  useScheduleMutation(({ id, scope, scheduledStart }: { id: number; scope: Scope; scheduledStart: Date }) =>
    api.patch<Lesson>(`/lessons/${id}`, { scope, scheduled_start: toIso(scheduledStart) }),
  );

export const useCancelLesson = () =>
  useScheduleMutation(({ id, scope }: { id: number; scope: CancelScope }) =>
    api.post<Lesson>(`/lessons/${id}/cancel`, { scope }),
  );

export const useDeleteLesson = () =>
  useScheduleMutation(({ id, scope }: { id: number; scope: CancelScope }) =>
    api.del<null>(`/lessons/${id}${qs({ scope })}`),
  );

export const useSaveHomework = (id: number) =>
  useScheduleMutation((homework_text: string) => api.patch<Lesson>(`/lessons/${id}/homework`, { homework_text }));

export const useUpdateParticipant = (id: number) =>
  useScheduleMutation(({ studentId, data }: { studentId: number; data: ParticipantUpdate }) =>
    api.patch<Lesson>(`/lessons/${id}/students/${studentId}`, data),
  );
