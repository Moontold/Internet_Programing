import { Button, Group, Title } from '@mantine/core';
import dayjs from 'dayjs';

interface Props {
  month: Date;
  onShift: (months: number) => void;
}

export function MonthSwitcher({ month, onShift }: Props) {
  return (
    <Group justify="space-between">
      <Button variant="default" aria-label="Предыдущий месяц" onClick={() => onShift(-1)}>
        ←
      </Button>
      <Title order={4} className="first-upper">
        {dayjs(month).format('MMMM YYYY')}
      </Title>
      <Button variant="default" aria-label="Следующий месяц" onClick={() => onShift(1)}>
        →
      </Button>
    </Group>
  );
}

export function monthRange(offset: number) {
  const month = dayjs().add(offset, 'month');
  return { start: month.startOf('month').toDate(), end: month.endOf('month').toDate() };
}
