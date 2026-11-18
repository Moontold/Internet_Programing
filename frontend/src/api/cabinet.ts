import { useQuery } from '@tanstack/react-query';

import { toIso } from '../lib/dates';
import { api, qs } from './client';
import type { ChildrenList, LessonShort, Series } from './types';

const KEY = 'cabinet';

export const useChildren = () =>
  useQuery({ queryKey: [KEY, 'children'], queryFn: () => api.get<ChildrenList>('/parent/children') });

export const useChildLessons = (studentId: number, start: Date, end: Date) =>
  useQuery({
    queryKey: [KEY, 'child-lessons', studentId, toIso(start), toIso(end)],
    queryFn: () =>
      api
        .get<{ lessons: LessonShort[] }>(
          `/parent/children/${studentId}/lessons${qs({ start: toIso(start), end: toIso(end) })}`,
        )
        .then((r) => r.lessons),
    enabled: Number.isFinite(studentId),
  });

export const useStudentLessons = (start: Date, end: Date) =>
  useQuery({
    queryKey: [KEY, 'student-lessons', toIso(start), toIso(end)],
    queryFn: () =>
      api
        .get<{ lessons: LessonShort[] }>(`/student/lessons${qs({ start: toIso(start), end: toIso(end) })}`)
        .then((r) => r.lessons),
  });

export const useStudentSeries = () =>
  useQuery({
    queryKey: [KEY, 'student-series'],
    queryFn: () => api.get<{ series: Series[] }>('/student/series').then((r) => r.series),
  });
