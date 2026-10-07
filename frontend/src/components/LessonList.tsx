import { Stack, Text, UnstyledButton } from '@mantine/core';
import dayjs from 'dayjs';

import type { LessonShort } from '../api/types';
import { fmtTime } from '../lib/dates';
import { statusLabel } from '../lib/format';

interface Props {
  lessons: LessonShort[];
  onOpen: (lesson: LessonShort) => void;
  emptyText?: string;
  showParticipants?: boolean;
}

function singleGrade(lesson: LessonShort): number | null {
  const visible = lesson.participants.filter((p) => p.homework_status !== null);
  return visible.length === 1 ? visible[0].homework_grade : null;
}

const homeworkMissed = (lesson: LessonShort) =>
  lesson.status === 'held' && lesson.participants.some((p) => p.homework_status === 'not_done');

function groupByDay(lessons: LessonShort[]): [string, LessonShort[]][] {
  const groups = new Map<string, LessonShort[]>();
  for (const lesson of lessons) {
    const key = dayjs(lesson.scheduled_start).format('YYYY-MM-DD');
    groups.set(key, [...(groups.get(key) ?? []), lesson]);
  }
  return [...groups.entries()];
}

export function LessonList({ lessons, onOpen, emptyText = 'Занятий нет', showParticipants = true }: Props) {
  if (lessons.length === 0) return <Text c="dimmed">{emptyText}</Text>;
  const today = dayjs().format('YYYY-MM-DD');
  const sorted = [...lessons].sort((a, b) => a.scheduled_start.localeCompare(b.scheduled_start));

  return (
    <Stack gap="lg">
      {groupByDay(sorted).map(([day, items]) => (
        <Stack key={day} gap="xs">
          <div className={`day-head${day === today ? ' day-head--today' : ''}`}>
            <span className="day-head__num">{dayjs(day).format('D')}</span>
            <span className="day-head__label">
              {dayjs(day).format('D MMMM, dddd').replace(/^\d+\s/, '')}
              {day === today ? ', сегодня' : ''}
            </span>
          </div>
          {items.map((lesson) => {
            const grade = singleGrade(lesson);
            const missed = homeworkMissed(lesson);
            const names = lesson.participants.map((p) => p.full_name).join(', ');
            return (
              <UnstyledButton
                key={lesson.id}
                className={`lesson-row lesson-row--${lesson.status}`}
                onClick={() => onOpen(lesson)}
              >
                <span className="lesson-row__bar" aria-hidden />
                <span className="lesson-row__time">
                  {fmtTime(lesson.scheduled_start)}
                  <span className="lesson-row__dur">{lesson.duration_minutes} мин</span>
                </span>
                <span>
                  <span className="lesson-row__title">{lesson.title || lesson.topic || 'Занятие'}</span>
                  {lesson.title && lesson.topic && <div className="lesson-row__meta">{lesson.topic}</div>}
                  {showParticipants && names && <div className="lesson-row__meta">{names}</div>}
                  {lesson.status === 'cancelled' && <div className="lesson-row__meta">{statusLabel.cancelled}</div>}
                </span>
                <span className="lesson-row__side">
                  {grade !== null && (
                    <span className="grade-mark" title="Оценка за домашку">
                      {grade}
                    </span>
                  )}
                  {missed && <span className="alert-pill">Домашка не выполнена</span>}
                  {lesson.status === 'held' && grade === null && !missed && (
                    <span className="lesson-row__meta">{statusLabel.held}</span>
                  )}
                </span>
              </UnstyledButton>
            );
          })}
        </Stack>
      ))}
    </Stack>
  );
}
