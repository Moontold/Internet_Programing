import { Button, Code, CopyButton, Stack, Text } from '@mantine/core';
import { modals } from '@mantine/modals';
import type { ReactNode } from 'react';

export function PasswordReveal({ password, children }: { password: string; children?: ReactNode }) {
  return (
    <Stack>
      <Text size="sm">Пароль показывается один раз. Передайте его пользователю.</Text>
      <Code block fz="lg">
        {password}
      </Code>
      <CopyButton value={password}>
        {({ copied, copy }) => <Button onClick={copy}>{copied ? 'Скопировано' : 'Скопировать'}</Button>}
      </CopyButton>
      {children}
    </Stack>
  );
}

export function showPassword(password: string, title = 'Пароль') {
  modals.open({ title, children: <PasswordReveal password={password} /> });
}
