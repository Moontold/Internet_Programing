import { Button, Input, NumberInput, PasswordInput, SegmentedControl, Stack, TextInput } from '@mantine/core';
import { useState, type FormEvent } from 'react';

import type { LessonFormat, Parent, Student, StudentCreate, StudentUpdate } from '../api/types';
import { ParentPicker } from './ParentPicker';

interface Props {
  initial?: Student;
  parents: Parent[];
  defaultParentId?: number;
  busy?: boolean;
  onSubmit: (data: StudentCreate | StudentUpdate) => void;
}

export function StudentForm({ initial, parents, defaultParentId, busy, onSubmit }: Props) {
  const startParent = initial?.parent.id ?? defaultParentId;
  const [fullName, setFullName] = useState(initial?.full_name ?? '');
  const [login, setLogin] = useState(initial?.login ?? '');
  const [password, setPassword] = useState('');
  const [parentId, setParentId] = useState<string | null>(startParent ? String(startParent) : null);
  const [grade, setGrade] = useState<number | string>(initial?.grade ?? '');
  const [gradeNote, setGradeNote] = useState(initial?.grade_note ?? '');
  const [format, setFormat] = useState<LessonFormat>(initial?.format ?? 'offline');
  const [price, setPrice] = useState<number | string>(initial?.price_per_lesson ?? 0);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!parentId) return;
    const common = {
      full_name: fullName,
      parent_id: Number(parentId),
      grade: grade === '' ? null : Number(grade),
      grade_note: gradeNote,
      format,
      price_per_lesson: Number(price) || 0,
    };
    if (initial) onSubmit(common);
    else onSubmit({ ...common, login, password });
  };

  return (
    <form onSubmit={submit}>
      <Stack>
        <TextInput label="ФИО" value={fullName} onChange={(e) => setFullName(e.currentTarget.value)} required />
        {!initial && (
          <>
            <TextInput
              label="Логин"
              description="Латиница, цифры, точка, дефис, подчёркивание"
              value={login}
              onChange={(e) => setLogin(e.currentTarget.value)}
              pattern="[a-zA-Z0-9_.\-]+"
              minLength={3}
              required
            />
            <PasswordInput
              label="Пароль"
              description="Не меньше 8 символов"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              minLength={8}
              required
            />
          </>
        )}
        <ParentPicker parents={parents} value={parentId} onChange={setParentId} />
        <NumberInput label="Класс" min={1} max={11} value={grade} onChange={setGrade} allowDecimal={false} />
        <TextInput
          label="Уточнение"
          placeholder="например, студент 1 курса"
          value={gradeNote}
          onChange={(e) => setGradeNote(e.currentTarget.value)}
        />
        <Input.Wrapper label="Формат занятий">
          <SegmentedControl
            fullWidth
            data={[
              { value: 'offline', label: 'Очно' },
              { value: 'online', label: 'Онлайн' },
            ]}
            value={format}
            onChange={(v) => setFormat(v as LessonFormat)}
          />
        </Input.Wrapper>
        <NumberInput
          label="Цена занятия, ₽"
          min={0}
          step={100}
          value={price}
          onChange={setPrice}
          thousandSeparator=" "
          allowDecimal={false}
        />
        <Button type="submit" loading={busy}>
          {initial ? 'Сохранить' : 'Создать'}
        </Button>
      </Stack>
    </form>
  );
}
