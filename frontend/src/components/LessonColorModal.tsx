import { Button, Group, Modal, SimpleGrid, Stack, Text, UnstyledButton } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useEffect, useState } from 'react';

import { useSetLessonColor } from '../api/lessons';
import type { LessonShort } from '../api/types';
import { LESSON_COLORS, normalizeColor } from '../lib/colors';
import { askColorScope } from './ScopeDialog';

interface Props {
  lesson: LessonShort | null;
  onClose: () => void;
}

export function LessonColorModal({ lesson, onClose }: Props) {
  const setColor = useSetLessonColor();
  const [picked, setPicked] = useState<string | null>(null);

  useEffect(() => {
    setPicked(normalizeColor(lesson?.color ?? null));
  }, [lesson]);

  const apply = async () => {
    if (!lesson) return;
    const scope = await askColorScope(lesson);
    if (!scope) return;
    setColor.mutate(
      { id: lesson.id, scope, color: picked },
      {
        onSuccess: () => {
          notifications.show({ color: 'green', message: 'Цвет сохранён' });
          onClose();
        },
        onError: (error) => notifications.show({ color: 'red', message: error.message }),
      },
    );
  };

  return (
    <Modal opened={lesson !== null} onClose={onClose} title="Цвет занятия">
      <Stack>
        <SimpleGrid cols={7} spacing="xs" pt={4}>
          <UnstyledButton
            title="Без цвета"
            aria-label="Без цвета"
            className={`swatch swatch--none${picked === null ? ' swatch--picked' : ''}`}
            onClick={() => setPicked(null)}
          />
          {LESSON_COLORS.map((item) => (
            <UnstyledButton
              key={item.value}
              title={item.label}
              aria-label={item.label}
              className={`swatch${picked === item.value ? ' swatch--picked' : ''}`}
              style={{ background: item.value }}
              onClick={() => setPicked(item.value)}
            />
          ))}
        </SimpleGrid>
        <Text size="sm" c="dimmed">
          Без цвета занятие показывается по статусу: запланированное — бирюзовым, проведённое — серым. Если у серии
          есть цвет, «Без цвета» для одного занятия вернёт ему цвет серии.
        </Text>
        <Group justify="flex-end">
          <Button variant="default" onClick={onClose}>
            Отмена
          </Button>
          <Button onClick={apply} loading={setColor.isPending}>
            Применить
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
