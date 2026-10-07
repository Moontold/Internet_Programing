import { Anchor, Badge, Button, Card, Group, Modal, Stack, Text, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useParents } from '../../api/parents';
import { useResetStudentPassword, useStudent, useUpdateStudent } from '../../api/students';
import type { StudentUpdate } from '../../api/types';
import { showPassword } from '../../components/PasswordModal';
import { StudentForm } from '../../components/StudentForm';
import { fmtMoney, formatLabel, gradeLabel } from '../../lib/format';

export function StudentCardPage() {
  const studentId = Number(useParams().studentId);
  const student = useStudent(studentId);
  const parents = useParents();
  const update = useUpdateStudent(studentId);
  const reset = useResetStudentPassword(studentId);
  const [editing, setEditing] = useState(false);

  if (!student.data) return null;
  const data = student.data;
  const onError = (error: Error) => notifications.show({ color: 'red', message: error.message });

  return (
    <Stack maw={860}>
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
            <b>Класс:</b> {gradeLabel(data)}
          </Text>
          <Text>
            <b>Формат:</b> {formatLabel[data.format]}
          </Text>
          <Text>
            <b>Родитель:</b>{' '}
            <Anchor component={Link} to={`/parents/${data.parent.id}`}>
              {data.parent.full_name}
            </Anchor>
            {data.parent.phone ? `, ${data.parent.phone}` : ''}
          </Text>
          <Text>
            <b>Цена занятия:</b> {fmtMoney(data.price_per_lesson)}
          </Text>
          <Text>
            <b>Логин:</b> {data.login}
          </Text>
        </Stack>
      </Card>
      <Modal opened={editing} onClose={() => setEditing(false)} title="Редактировать ученика" closeOnEscape={false}>
        <StudentForm
          initial={data}
          parents={parents.data ?? []}
          busy={update.isPending}
          onSubmit={(d) => update.mutate(d as StudentUpdate, { onSuccess: () => setEditing(false), onError })}
        />
      </Modal>
    </Stack>
  );
}
