import { Anchor, Button, Card, Group, Modal, Switch, Table, Text, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useCreateParent, useParents } from '../../api/parents';
import type { ParentCreate } from '../../api/types';
import { ParentForm } from '../../components/ParentForm';
import { showPassword } from '../../components/PasswordModal';

export function ParentsPage() {
  const parents = useParents();
  const create = useCreateParent();
  const [open, setOpen] = useState(false);
  const [onlyActive, setOnlyActive] = useState(true);

  const submit = (data: ParentCreate) =>
    create.mutate(data, {
      onSuccess: (result) => {
        setOpen(false);
        showPassword(result.password, `Пароль для ${result.parent.full_name}`);
      },
      onError: (error) => notifications.show({ color: 'red', message: error.message }),
    });

  const rows = (parents.data ?? []).filter((parent) => !onlyActive || parent.is_active);

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Родители</Title>
        <Group>
          <Switch
            label="Только активные"
            checked={onlyActive}
            onChange={(e) => setOnlyActive(e.currentTarget.checked)}
          />
          <Button onClick={() => setOpen(true)}>Добавить</Button>
        </Group>
      </Group>
      {parents.isSuccess && rows.length === 0 ? (
        <Text c="dimmed">{onlyActive ? 'Активных родителей нет.' : 'Родителей пока нет.'}</Text>
      ) : (
        <Card className="data-card">
          <Table.ScrollContainer minWidth={480}>
            <Table highlightOnHover verticalSpacing="sm" horizontalSpacing="lg">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>ФИО</Table.Th>
                  <Table.Th>Телефон</Table.Th>
                  <Table.Th>Дети</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {rows.map((parent) => (
                  <Table.Tr key={parent.id}>
                    <Table.Td>
                      <Anchor component={Link} to={`/parents/${parent.id}`}>
                        {parent.full_name}
                      </Anchor>
                      {!parent.is_active && ' (неактивен)'}
                    </Table.Td>
                    <Table.Td>{parent.phone || '—'}</Table.Td>
                    <Table.Td>{parent.children.map((c) => c.full_name).join(', ') || '—'}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>
      )}
      <Modal opened={open} onClose={() => setOpen(false)} title="Новый родитель">
        <ParentForm onSubmit={(data) => submit(data as ParentCreate)} busy={create.isPending} />
      </Modal>
    </>
  );
}
