import { Button, Group, Modal, Stack, Text, Title } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import dayjs from 'dayjs';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useCreateLesson, useLessons, useMoveLesson } from '../../api/lessons';
import { useCreateSeries } from '../../api/series';
import { useStudents } from '../../api/students';
import type { LessonShort } from '../../api/types';
import { Calendar } from '../../components/Calendar';
import { LessonContextMenu, type MenuTarget } from '../../components/LessonContextMenu';
import { LessonForm } from '../../components/LessonForm';
import { LessonList } from '../../components/LessonList';
import { MoveLessonModal } from '../../components/MoveLessonModal';
import { askMoveScope } from '../../components/ScopeDialog';
import { addDays, startOfWeek } from '../../lib/dates';

const currentWeek = () => ({ start: startOfWeek(new Date()), end: addDays(startOfWeek(new Date()), 7) });

function weekLabel(start: Date): string {
  const first = dayjs(start);
  const last = dayjs(addDays(start, 6));
  return first.month() === last.month()
    ? `${first.format('D')}–${last.format('D MMMM')}`
    : `${first.format('D MMMM')} — ${last.format('D MMMM')}`;
}

export function SchedulePage() {
  const navigate = useNavigate();
  const isMobile = useMediaQuery('(max-width: 48em)');
  const [range, setRange] = useState(currentWeek);
  const lessons = useLessons(range.start, range.end);
  const students = useStudents(true);
  const createLesson = useCreateLesson();
  const createSeries = useCreateSeries();
  const move = useMoveLesson();
  const [createAt, setCreateAt] = useState<Date | null>(null);
  const [menu, setMenu] = useState<MenuTarget | null>(null);
  const [movingTo, setMovingTo] = useState<LessonShort | null>(null);

  const onError = (error: Error) => notifications.show({ color: 'red', message: error.message });
  const openLesson = (id: number) => navigate(`/lessons/${id}`);
  const shiftWeek = (days: number) => setRange((r) => ({ start: addDays(r.start, days), end: addDays(r.end, days) }));
  const created = (message: string) => () => {
    setCreateAt(null);
    notifications.show({ color: 'green', message });
  };

  const moveDropped = async (lesson: LessonShort, newStart: Date, revert: () => void) => {
    const scope = await askMoveScope(lesson, newStart);
    if (!scope) {
      revert();
      return;
    }
    move.mutate(
      { id: lesson.id, scope, scheduledStart: newStart },
      {
        onSuccess: () => notifications.show({ color: 'green', message: 'Занятие перенесено' }),
        onError: (error) => {
          revert();
          onError(error);
        },
      },
    );
  };

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Расписание</Title>
        <Button onClick={() => setCreateAt(dayjs().add(1, 'hour').startOf('hour').toDate())}>Добавить занятие</Button>
      </Group>

      {isMobile ? (
        <>
          <Stack gap={6} mb="sm">
            <Group justify="space-between" wrap="nowrap">
              <Button variant="default" onClick={() => shiftWeek(-7)}>
                ← Неделя
              </Button>
              <Button variant="default" onClick={() => shiftWeek(7)}>
                Неделя →
              </Button>
            </Group>
            <Text size="sm" c="dimmed" ta="center">
              {weekLabel(range.start)}
            </Text>
          </Stack>
          <LessonList lessons={lessons.data ?? []} onOpen={(lesson) => openLesson(lesson.id)} emptyText="На этой неделе занятий нет" />
        </>
      ) : (
        <Calendar
          lessons={lessons.data ?? []}
          onRangeChange={(start, end) => setRange({ start, end })}
          onOpen={openLesson}
          onMove={moveDropped}
          onCreate={setCreateAt}
          onContextMenu={(lesson, x, y) => setMenu({ lesson, x, y })}
        />
      )}

      <LessonContextMenu
        target={menu}
        onClose={() => setMenu(null)}
        onOpen={(lesson) => openLesson(lesson.id)}
        onMove={setMovingTo}
      />
      <MoveLessonModal lesson={movingTo} onClose={() => setMovingTo(null)} />

      <Modal opened={createAt !== null} onClose={() => setCreateAt(null)} title="Новое занятие">
        {createAt && (
          <LessonForm
            students={students.data ?? []}
            initialStart={createAt}
            busy={createLesson.isPending || createSeries.isPending}
            onCreateLesson={(data) => createLesson.mutate(data, { onSuccess: created('Занятие создано'), onError })}
            onCreateSeries={(data) => createSeries.mutate(data, { onSuccess: created('Серия занятий создана'), onError })}
          />
        )}
      </Modal>
    </>
  );
}
