import { Alert, Badge, Card, Container, Group, Loader, Stack, Text, Title } from '@mantine/core';
import { useEffect, useState } from 'react';

import { fetchHealth, type HealthStatus } from './api/client';

type State =
  | { kind: 'loading' }
  | { kind: 'ready'; health: HealthStatus }
  | { kind: 'failed'; message: string };

export function App() {
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    fetchHealth()
      .then((health) => setState({ kind: 'ready', health }))
      .catch((error: Error) => setState({ kind: 'failed', message: error.message }));
  }, []);

  return (
    <Container size="sm" py="xl">
      <Stack gap="md">
        <Title order={1}>Сайт репетитора</Title>
        <Text c="dimmed">
          Базовый проект первого спринта: каркас стека и проверка связности
          фронтенда, backend и базы данных.
        </Text>

        <Card withBorder radius="md" padding="lg">
          {state.kind === 'loading' && (
            <Group gap="sm">
              <Loader size="sm" />
              <Text>Проверяем backend…</Text>
            </Group>
          )}

          {state.kind === 'failed' && (
            <Alert color="red" title="Backend недоступен">
              {state.message}
            </Alert>
          )}

          {state.kind === 'ready' && (
            <Stack gap="xs">
              <Group justify="space-between">
                <Text>Backend</Text>
                <Badge color="green">ok, версия {state.health.version}</Badge>
              </Group>
              <Group justify="space-between">
                <Text>База данных</Text>
                <Badge color={state.health.database === 'ok' ? 'green' : 'red'}>
                  {state.health.database}
                </Badge>
              </Group>
              <Group justify="space-between">
                <Text>Часовой пояс</Text>
                <Badge variant="light">{state.health.timezone}</Badge>
              </Group>
            </Stack>
          )}
        </Card>
      </Stack>
    </Container>
  );
}
