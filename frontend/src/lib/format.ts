import type { LessonFormat } from '../api/types';

export const fmtMoney = (value: number) => `${value.toLocaleString('ru-RU')} ₽`;

export const formatLabel: Record<LessonFormat, string> = { offline: 'Очно', online: 'Онлайн' };

export const gradeLabel = (student: { grade: number | null; grade_note: string }) =>
  [student.grade ? `${student.grade} класс` : null, student.grade_note || null].filter(Boolean).join(', ') || '—';
