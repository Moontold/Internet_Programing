import { Group, Text } from '@mantine/core';

import type { StudentStats } from '../api/types';

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <Text fw={700} fz="1.375rem" lh={1.1} style={{ letterSpacing: '-0.02em' }}>
        {value}
      </Text>
      <Text size="xs" c="dimmed">
        {label}
      </Text>
    </div>
  );
}

const fmtAverage = (value: number) => value.toLocaleString('ru-RU', { maximumFractionDigits: 1 });

export function StatsBadges({ stats }: { stats: StudentStats }) {
  return (
    <Group gap="xl">
      <Stat
        value={stats.homework_done_percent === null ? '—' : `${stats.homework_done_percent}%`}
        label="домашек выполнено"
      />
      <Stat
        value={stats.homework_avg_grade === null ? '—' : fmtAverage(stats.homework_avg_grade)}
        label="средняя оценка"
      />
    </Group>
  );
}
