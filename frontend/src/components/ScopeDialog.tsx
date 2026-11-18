import { Button, Group, Radio, Stack } from '@mantine/core';
import { modals } from '@mantine/modals';
import { useState } from 'react';

import type { ColorScope, LessonShort, Scope } from '../api/types';
import { fmtDateTime, toIso } from '../lib/dates';

const SCOPE_LABELS: Record<Scope, string> = {
  this: 'Только это занятие',
  following: 'Это и последующие занятия',
  all: 'Все занятия серии',
};

function ScopeBody<T extends Scope>({ options, onPick }: { options: T[]; onPick: (scope: T | null) => void }) {
  const [value, setValue] = useState<T>(options[0]);
  return (
    <Stack>
      <Radio.Group value={value} onChange={(v) => setValue(v as T)}>
        <Stack gap="xs">
          {options.map((option) => (
            <Radio key={option} value={option} label={SCOPE_LABELS[option]} />
          ))}
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

export function askScope<T extends Scope>(title: string, options: T[]): Promise<T | null> {
  return new Promise((resolve) => {
    let settled = false;
    const settle = (scope: T | null) => {
      if (settled) return;
      settled = true;
      resolve(scope);
    };
    const id = modals.open({
      title,
      onClose: () => settle(null),
      children: (
        <ScopeBody
          options={options}
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
  lesson.series_id && lesson.status !== 'held'
    ? askScope<Scope>(`Перенести на ${fmtDateTime(toIso(newStart))}`, ['this', 'following', 'all'])
    : Promise.resolve<Scope>('this');

export const askCancelScope = (lesson: LessonShort, title: string) =>
  lesson.series_id
    ? askScope<Exclude<Scope, 'all'>>(title, ['this', 'following'])
    : Promise.resolve<Exclude<Scope, 'all'>>('this');

export const askColorScope = (lesson: LessonShort) =>
  lesson.series_id ? askScope<ColorScope>('Применить цвет', ['this', 'all']) : Promise.resolve<ColorScope>('this');
