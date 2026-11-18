import { Menu, Text } from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';

import { useCancelLesson, useDeleteLesson } from '../api/lessons';
import type { LessonShort, Scope } from '../api/types';
import { fmtDateTime } from '../lib/dates';
import { askCancelScope } from './ScopeDialog';

export interface MenuTarget {
  lesson: LessonShort;
  x: number;
  y: number;
}

interface Props {
  target: MenuTarget | null;
  onClose: () => void;
  onOpen: (lesson: LessonShort) => void;
  onMove: (lesson: LessonShort) => void;
}

function confirmDelete(lesson: LessonShort, scope: Scope): Promise<boolean> {
  return new Promise((resolve) => {
    modals.openConfirmModal({
      title: 'Удалить занятие',
      children: (
        <Text size="sm">
          {scope === 'following'
            ? `Занятие ${fmtDateTime(lesson.scheduled_start)} и все последующие в серии будут удалены.`
            : `Занятие ${fmtDateTime(lesson.scheduled_start)} будет удалено без возможности восстановления.`}
        </Text>
      ),
      labels: { confirm: 'Удалить', cancel: 'Отмена' },
      confirmProps: { color: 'red' },
      onConfirm: () => resolve(true),
      onCancel: () => resolve(false),
      onClose: () => resolve(false),
    });
  });
}

export function LessonContextMenu({ target, onClose, onOpen, onMove }: Props) {
  const lesson = target?.lesson ?? null;
  const cancel = useCancelLesson();
  const remove = useDeleteLesson();
  const onError = (error: Error) => notifications.show({ color: 'red', message: error.message });

  const doCancel = async () => {
    if (!lesson) return;
    const scope = await askCancelScope(lesson, 'Отменить занятие');
    if (!scope || scope === 'all') return;
    cancel.mutate(
      { id: lesson.id, scope },
      { onSuccess: () => notifications.show({ color: 'green', message: 'Занятие отменено' }), onError },
    );
  };

  const doDelete = async () => {
    if (!lesson) return;
    const scope = await askCancelScope(lesson, 'Удалить занятие');
    if (!scope || scope === 'all') return;
    if (!(await confirmDelete(lesson, scope))) return;
    remove.mutate(
      { id: lesson.id, scope },
      { onSuccess: () => notifications.show({ color: 'green', message: 'Занятие удалено' }), onError },
    );
  };

  return (
    <Menu opened={target !== null} onClose={onClose} position="bottom-start" offset={2} shadow="md" withinPortal>
      <Menu.Target>
        <div
          style={{
            position: 'fixed',
            left: target?.x ?? 0,
            top: target?.y ?? 0,
            width: 1,
            height: 1,
            pointerEvents: 'none',
          }}
        />
      </Menu.Target>
      {lesson && (
        <Menu.Dropdown>
          <Menu.Label>{fmtDateTime(lesson.scheduled_start)}</Menu.Label>
          <Menu.Item onClick={() => onOpen(lesson)}>Открыть</Menu.Item>
          {lesson.status === 'planned' && <Menu.Item onClick={() => onMove(lesson)}>Перенести…</Menu.Item>}
          {lesson.status !== 'cancelled' && <Menu.Item onClick={doCancel}>Отменить</Menu.Item>}
          {lesson.status !== 'held' && (
            <>
              <Menu.Divider />
              <Menu.Item color="red" onClick={doDelete}>
                Удалить
              </Menu.Item>
            </>
          )}
        </Menu.Dropdown>
      )}
    </Menu>
  );
}
