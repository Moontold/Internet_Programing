import { Button, PasswordInput, Stack, Textarea, TextInput } from '@mantine/core';
import { useState, type FormEvent } from 'react';

import type { Parent, ParentCreate, ParentUpdate } from '../api/types';

interface Props {
  initial?: Parent;
  busy?: boolean;
  onSubmit: (data: ParentCreate | ParentUpdate) => void;
}

export function ParentForm({ initial, busy, onSubmit }: Props) {
  const [fullName, setFullName] = useState(initial?.full_name ?? '');
  const [login, setLogin] = useState(initial?.login ?? '');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState(initial?.phone ?? '');
  const [note, setNote] = useState(initial?.contacts_note ?? '');

  const submit = (event: FormEvent) => {
    event.preventDefault();
    event.stopPropagation();
    if (initial) onSubmit({ full_name: fullName, phone, contacts_note: note });
    else onSubmit({ full_name: fullName, login, password, phone, contacts_note: note });
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
        <TextInput label="Телефон" value={phone} onChange={(e) => setPhone(e.currentTarget.value)} />
        <Textarea
          label="Контакты, заметки"
          value={note}
          onChange={(e) => setNote(e.currentTarget.value)}
          autosize
          minRows={2}
        />
        <Button type="submit" loading={busy}>
          {initial ? 'Сохранить' : 'Создать'}
        </Button>
      </Stack>
    </form>
  );
}
