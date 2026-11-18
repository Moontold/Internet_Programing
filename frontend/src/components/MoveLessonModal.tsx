import { Button, Modal, Stack, Text } from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { notifications } from '@mantine/notifications';
import { useEffect, useState } from 'react';

import { useMoveLesson } from '../api/lessons';
import type { LessonShort } from '../api/types';
import { askMoveScope } from './ScopeDialog';

interface Props {
  lesson: LessonShort | null;
  onClose: () => void;
}

const endsBeforeNow = (start: Date, durationMinutes: number) =>
  start.getTime() + durationMinutes * 60000 <= Date.now();

export function MoveLessonModal({ lesson, onClose }: Props) {
  const move = useMoveLesson();
  const [moveTo, setMoveTo] = useState<Date | null>(null);
  const isHeld = lesson?.status === 'held';
  const heldInFuture = isHeld && moveTo !== null && !endsBeforeNow(moveTo, lesson.duration_minutes);

  useEffect(() => {
    setMoveTo(lesson ? new Date(lesson.scheduled_start) : null);
  }, [lesson]);

  const doMove = async () => {
    if (!lesson || !moveTo || heldInFuture) return;
    const scope = await askMoveScope(lesson, moveTo);
    if (!scope) return;
    move.mutate(
      { id: lesson.id, scope, scheduledStart: moveTo },
      {
        onSuccess: () => {
          notifications.show({ color: 'green', message: 'Занятие перенесено' });
          onClose();
        },
        onError: (error) => notifications.show({ color: 'red', message: error.message }),
      },
    );
  };

  return (
    <Modal opened={lesson !== null} onClose={onClose} title={isHeld ? 'Перенести проведённое занятие' : 'Перенести занятие'}>
      <Stack>
        {isHeld && (
          <Text size="sm" c="dimmed">
            Исправление записи о том, когда занятие прошло: только это занятие и только на прошедшее время. Уведомления не
            отправляются.
          </Text>
        )}
        <DateTimePicker
          label="Новое время"
          value={moveTo}
          onChange={setMoveTo}
          valueFormat="D MMMM YYYY, HH:mm"
          maxDate={isHeld ? new Date() : undefined}
          error={heldInFuture ? 'Занятие должно закончиться раньше текущего момента' : undefined}
        />
        <Button onClick={doMove} loading={move.isPending} disabled={heldInFuture}>
          Перенести
        </Button>
      </Stack>
    </Modal>
  );
}
