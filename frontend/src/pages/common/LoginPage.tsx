import { Button, Card, Center, PasswordInput, Stack, Text, TextInput, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { homeFor, useAuth } from '../../auth/AuthContext';

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [loginValue, setLoginValue] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homeFor(user.role)} replace />;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      const profile = await login(loginValue.trim(), password);
      navigate(homeFor(profile.role), { replace: true });
    } catch (error) {
      notifications.show({ color: 'red', message: (error as Error).message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Center mih="100vh" p="md">
      <Stack w={380} gap="lg">
        <div>
          <Title order={1}>Занятия</Title>
          <Text c="dimmed" mt={4}>
            Расписание, домашние задания и оценки
          </Text>
        </div>
        <Card component="form" onSubmit={submit}>
          <Stack>
            <TextInput
              label="Логин"
              value={loginValue}
              onChange={(e) => setLoginValue(e.currentTarget.value)}
              autoFocus
              autoComplete="username"
              required
            />
            <PasswordInput
              label="Пароль"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              autoComplete="current-password"
              required
            />
            <Button type="submit" loading={busy} fullWidth mt="xs">
              Войти
            </Button>
          </Stack>
        </Card>
        <Text size="sm" c="dimmed">
          Логин и пароль выдаёт преподаватель. Забыли пароль? Попросите преподавателя сбросить его.
        </Text>
      </Stack>
    </Center>
  );
}
