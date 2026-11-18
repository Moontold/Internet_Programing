import { Button, MultiSelect, NumberInput, Stack, Switch, TextInput } from '@mantine/core';
import { DateInput, DateTimePicker } from '@mantine/dates';
import { useState, type FormEvent } from 'react';

import type { LessonCreate, SeriesCreate, StudentListItem } from '../api/types';
import { toDateOnly, toIso } from '../lib/dates';

interface Props {
  students: StudentListItem[];
  initialStart?: Date;
  busy?: boolean;
  onCreateLesson: (data: LessonCreate) => void;
  onCreateSeries: (data: SeriesCreate) => void;
}

export function LessonForm({ students, initialStart, busy, onCreateLesson, onCreateSeries }: Props) {
  const [start, setStart] = useState<Date | null>(initialStart ?? null);
  const [duration, setDuration] = useState<number | string>(60);
  const [studentIds, setStudentIds] = useState<string[]>([]);
  const [title, setTitle] = useState('');
  const [repeat, setRepeat] = useState(true);
  const [interval, setInterval] = useState<number | string>(1);
  const [until, setUntil] = useState<Date | null>(null);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!start || studentIds.length === 0) return;
    const ids = studentIds.map(Number);
    if (repeat) {
      onCreateSeries({
        first_start: toIso(start),
        duration_minutes: Number(duration),
        interval_weeks: Number(interval) || 1,
        until: until ? toDateOnly(until) : null,
        title,
        student_ids: ids,
      });
      return;
    }
    onCreateLesson({ scheduled_start: toIso(start), duration_minutes: Number(duration), title, student_ids: ids });
  };

  return (
    <form onSubmit={submit}>
      <Stack>
        <DateTimePicker
          label="Дата и время"
          value={start}
          onChange={setStart}
          valueFormat="D MMMM YYYY, HH:mm"
          withAsterisk
        />
        <NumberInput
          label="Длительность, мин"
          min={15}
          max={480}
          step={15}
          value={duration}
          onChange={setDuration}
          required
        />
        <MultiSelect
          label="Ученики"
          data={students.filter((s) => s.is_active).map((s) => ({ value: String(s.id), label: s.full_name }))}
          value={studentIds}
          onChange={setStudentIds}
          searchable
          withAsterisk
        />
        <TextInput
          label="Название"
          description="Необязательно, например «Мини-группа ОГЭ»"
          value={title}
          onChange={(e) => setTitle(e.currentTarget.value)}
        />
        <Switch label="Повторять каждую неделю" checked={repeat} onChange={(e) => setRepeat(e.currentTarget.checked)} />
        {repeat && (
          <>
            <NumberInput label="Раз в N недель" min={1} max={8} value={interval} onChange={setInterval} />
            <DateInput
              label="До какой даты (необязательно)"
              value={until}
              onChange={setUntil}
              clearable
              valueFormat="D MMMM YYYY"
            />
          </>
        )}
        <Button type="submit" loading={busy} disabled={!start || studentIds.length === 0}>
          {repeat ? 'Создать серию' : 'Создать занятие'}
        </Button>
      </Stack>
    </form>
  );
}
