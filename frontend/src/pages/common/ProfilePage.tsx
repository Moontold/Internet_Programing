import { Button, Card, PasswordInput, Stack, Text, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useState, type FormEvent } from 'react';

import { authApi } from '../../api/auth';
import { useAuth } from '../../auth/AuthContext';

export function ProfilePage() {
  const { user } = useAuth();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [repeat, setRepeat] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (newPassword !== repeat) {
      notifications.show({ color: 'red', message: 'Пароли не совпадают' });
      return;
    }
    setBusy(true);
    try {
      await authApi.changePassword(oldPassword, newPassword);
      notifications.show({ color: 'green', message: 'Пароль изменён' });
      setOldPassword('');
      setNewPassword('');
      setRepeat('');
    } catch (error) {
      notifications.show({ color: 'red', message: (error as Error).message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Stack maw={480}>
      <Title order={2}>Профиль</Title>
      <div>
        <Text fw={600}>{user?.full_name}</Text>
        <Text size="sm" c="dimmed">
          Логин: {user?.login}
        </Text>
      </div>
      <Card component="form" onSubmit={submit}>
        <Stack>
          <Title order={4}>Смена пароля</Title>
          <PasswordInput
            label="Старый пароль"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.currentTarget.value)}
            autoComplete="current-password"
            required
          />
          <PasswordInput
            label="Новый пароль"
            description="Не меньше 8 символов"
            value={newPassword}
            onChange={(e) => setNewPassword(e.currentTarget.value)}
            autoComplete="new-password"
            minLength={8}
            required
          />
          <PasswordInput
            label="Повторите новый пароль"
            value={repeat}
            onChange={(e) => setRepeat(e.currentTarget.value)}
            autoComplete="new-password"
            required
          />
          <Button type="submit" loading={busy}>
            Сменить пароль
          </Button>
        </Stack>
      </Card>
    </Stack>
  );
}
