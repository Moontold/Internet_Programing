import { Button, Group, Radio, Stack } from '@mantine/core';
import { modals } from '@mantine/modals';
import { useState } from 'react';

import type { LessonShort, Scope } from '../api/types';
import { fmtDateTime, toIso } from '../lib/dates';

function ScopeBody({ allowAll, onPick }: { allowAll: boolean; onPick: (scope: Scope | null) => void }) {
  const [value, setValue] = useState<Scope>('this');
  return (
    <Stack>
      <Radio.Group value={value} onChange={(v) => setValue(v as Scope)}>
        <Stack gap="xs">
          <Radio value="this" label="Только это занятие" />
          <Radio value="following" label="Это и последующие занятия" />
          {allowAll && <Radio value="all" label="Все занятия серии" />}
        </Stack>
      </Radio.Group>
      <Group justify="flex-end">
        <Button variant="default" onClick={() => onPick(null)}>
          Отмена
        </Button>
        <Button onClick={() => onPick(value)}>Применить</Button>
      </Group>
    </Stack>
  );
}

export function askScope(title: string, allowAll: boolean): Promise<Scope | null> {
  return new Promise((resolve) => {
    let settled = false;
    const settle = (scope: Scope | null) => {
      if (settled) return;
      settled = true;
      resolve(scope);
    };
    const id = modals.open({
      title,
      onClose: () => settle(null),
      children: (
        <ScopeBody
          allowAll={allowAll}
          onPick={(scope) => {
            settle(scope);
            modals.close(id);
          }}
        />
      ),
    });
  });
}

export const askMoveScope = (lesson: LessonShort, newStart: Date) =>
  lesson.series_id ? askScope(`Перенести на ${fmtDateTime(toIso(newStart))}`, true) : Promise.resolve<Scope>('this');

export const askCancelScope = (lesson: LessonShort, title: string) =>
  lesson.series_id ? askScope(title, false) : Promise.resolve<Scope>('this');
