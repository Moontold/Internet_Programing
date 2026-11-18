import { Anchor, Badge, Button, Card, Group, Modal, Stack, Text, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useParent, useParents, useResetParentPassword, useUpdateParent } from '../../api/parents';
import { useCreateStudent } from '../../api/students';
import type { ParentUpdate, StudentCreate } from '../../api/types';
import { ParentForm } from '../../components/ParentForm';
import { showPassword } from '../../components/PasswordModal';
import { StudentForm } from '../../components/StudentForm';

export function ParentCardPage() {
  const parentId = Number(useParams().parentId);
  const parent = useParent(parentId);
  const parents = useParents();
  const update = useUpdateParent(parentId);
  const reset = useResetParentPassword(parentId);
  const createChild = useCreateStudent();
  const [editing, setEditing] = useState(false);
  const [addingChild, setAddingChild] = useState(false);

  if (!parent.data) return null;
  const data = parent.data;
  const onError = (error: Error) => notifications.show({ color: 'red', message: error.message });

  const submitChild = (form: StudentCreate) =>
    createChild.mutate(form, {
      onSuccess: (result) => {
        setAddingChild(false);
        showPassword(result.password, `Пароль для ${result.student.full_name}`);
      },
      onError,
    });

  return (
    <Stack maw={720}>
      <Group justify="space-between" align="flex-start">
        <div>
          <Title order={2}>{data.full_name}</Title>
          {!data.is_active && (
            <Badge color="gray" variant="light" mt={4}>
              Неактивен
            </Badge>
          )}
        </div>
        <Group>
          <Button variant="default" onClick={() => setEditing(true)}>
            Редактировать
          </Button>
          <Button
            variant="default"
            loading={reset.isPending}
            onClick={() => reset.mutate(undefined, { onSuccess: (p) => showPassword(p, 'Новый пароль'), onError })}
          >
            Сбросить пароль
          </Button>
          <Button
            variant={data.is_active ? 'light' : 'filled'}
            color={data.is_active ? 'red' : 'green'}
            loading={update.isPending}
            onClick={() => update.mutate({ is_active: !data.is_active }, { onError })}
          >
            {data.is_active ? 'Деактивировать' : 'Активировать'}
          </Button>
        </Group>
      </Group>
      <Card>
        <Stack gap="xs">
          <Text>
            <b>Логин:</b> {data.login}
          </Text>
          <Text>
            <b>Телефон:</b> {data.phone || '—'}
          </Text>
          <Text style={{ whiteSpace: 'pre-wrap' }}>
            <b>Контакты:</b> {data.contacts_note || '—'}
          </Text>
        </Stack>
      </Card>
      <Card>
        <Group justify="space-between" mb="xs">
          <Title order={4}>Дети</Title>
          {data.is_active && (
            <Button size="xs" variant="default" onClick={() => setAddingChild(true)}>
              Добавить ребёнка
            </Button>
          )}
        </Group>
        {data.children.length === 0 && <Text c="dimmed">Пока нет</Text>}
        {data.children.map((child) => (
          <Text key={child.id}>
            <Anchor component={Link} to={`/students/${child.id}`}>
              {child.full_name}
            </Anchor>
            {child.grade ? `, ${child.grade} класс` : ''}
            {!child.is_active && ' (неактивен)'}
          </Text>
        ))}
      </Card>
      <Modal opened={editing} onClose={() => setEditing(false)} title="Редактировать родителя">
        <ParentForm
          initial={data}
          busy={update.isPending}
          onSubmit={(d) => update.mutate(d as ParentUpdate, { onSuccess: () => setEditing(false), onError })}
        />
      </Modal>
      <Modal opened={addingChild} onClose={() => setAddingChild(false)} title="Новый ученик" closeOnEscape={false}>
        <StudentForm
          parents={parents.data ?? []}
          defaultParentId={data.id}
          busy={createChild.isPending}
          onSubmit={(d) => submitChild(d as StudentCreate)}
        />
      </Modal>
    </Stack>
  );
}
