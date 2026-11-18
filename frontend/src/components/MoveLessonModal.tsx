import { Button, Modal, Stack } from '@mantine/core';
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

export function MoveLessonModal({ lesson, onClose }: Props) {
  const move = useMoveLesson();
  const [moveTo, setMoveTo] = useState<Date | null>(null);

  useEffect(() => {
    setMoveTo(lesson ? new Date(lesson.scheduled_start) : null);
  }, [lesson]);

  const doMove = async () => {
    if (!lesson || !moveTo) return;
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
    <Modal opened={lesson !== null} onClose={onClose} title="Перенести занятие">
      <Stack>
        <DateTimePicker label="Новое время" value={moveTo} onChange={setMoveTo} valueFormat="D MMMM YYYY, HH:mm" />
        <Button onClick={doMove} loading={move.isPending}>
          Перенести
        </Button>
      </Stack>
    </Modal>
  );
}
