import { AppShell as MantineShell, Button, Container, Group, Text } from '@mantine/core';
import { type ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

import type { Role } from '../api/types';
import { useAuth } from '../auth/AuthContext';

interface NavItem {
  to: string;
  label: string;
}

const NAV: Record<Role, NavItem[]> = {
  tutor: [
    { to: '/schedule', label: 'Расписание' },
    { to: '/students', label: 'Ученики' },
    { to: '/parents', label: 'Родители' },
  ],
  parent: [
    { to: '/children', label: 'Дети' },
  ],
  student: [
    { to: '/my/schedule', label: 'Расписание' },
    { to: '/my/lessons', label: 'Занятия' },
  ],
};

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return <>{children}</>;
  const items = [...NAV[user.role], { to: '/profile', label: 'Профиль' }];

  return (
    <MantineShell header={{ height: 60 }} footer={{ height: 56, collapsed: false }} padding={0}>
      <MantineShell.Header className="app-header" withBorder={false}>
        <Container size="lg" h="100%">
          <Group h="100%" justify="space-between">
            <Group gap="xl">
              <NavLink to="/" className="app-brand">
                Занятия
              </NavLink>
              <Group gap={0} visibleFrom="sm">
                {items.map((item) => (
                  <NavLink key={item.to} to={item.to} className="app-nav-link">
                    {item.label}
                  </NavLink>
                ))}
              </Group>
            </Group>
            <Group gap="sm">
              <Text size="sm" c="dimmed" visibleFrom="sm">
                {user.full_name}
              </Text>
              <Button
                size="xs"
                variant="default"
                onClick={async () => {
                  await logout();
                  navigate('/login');
                }}
              >
                Выйти
              </Button>
            </Group>
          </Group>
        </Container>
      </MantineShell.Header>
      <MantineShell.Main pb={80}>
        <Container size="lg" py="xl">
          {children}
        </Container>
      </MantineShell.Main>
      <MantineShell.Footer className="app-footer" hiddenFrom="sm" withBorder={false}>
        <Group h="100%" grow gap={0}>
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} className="app-tab">
              {item.label}
            </NavLink>
          ))}
        </Group>
      </MantineShell.Footer>
    </MantineShell>
  );
}
