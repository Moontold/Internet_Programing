import type { HomeworkStatus, LessonFormat, LessonStatus } from '../api/types';

export const fmtMoney = (value: number) => `${value.toLocaleString('ru-RU')} ₽`;

export const fmtSize = (bytes: number) =>
  bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} МБ` : `${Math.max(1, Math.round(bytes / 1024))} КБ`;

export const formatLabel: Record<LessonFormat, string> = { offline: 'Очно', online: 'Онлайн' };

export const statusLabel: Record<LessonStatus, string> = {
  planned: 'Запланировано',
  held: 'Проведено',
  cancelled: 'Отменено',
};
export const statusColor: Record<LessonStatus, string> = { planned: 'blue', held: 'green', cancelled: 'gray' };

export const homeworkStatusLabel: Record<HomeworkStatus, string> = {
  not_checked: 'Не проверено',
  done: 'Выполнено',
  not_done: 'Не выполнено',
};

export const gradeLabel = (student: { grade: number | null; grade_note: string }) =>
  [student.grade ? `${student.grade} класс` : null, student.grade_note || null].filter(Boolean).join(', ') || '—';
