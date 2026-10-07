import { Anchor, Badge, Button, Card, Group, Modal, Switch, Table, Text, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useParents } from '../../api/parents';
import { useCreateStudent, useStudents } from '../../api/students';
import type { StudentCreate } from '../../api/types';
import { showPassword } from '../../components/PasswordModal';
import { StudentForm } from '../../components/StudentForm';
import { formatLabel, gradeLabel } from '../../lib/format';

export function StudentsPage() {
  const [onlyActive, setOnlyActive] = useState(true);
  const students = useStudents(onlyActive ? true : undefined);
  const parents = useParents();
  const create = useCreateStudent();
  const [open, setOpen] = useState(false);

  const submit = (data: StudentCreate) =>
    create.mutate(data, {
      onSuccess: (result) => {
        setOpen(false);
        showPassword(result.password, `Пароль для ${result.student.full_name}`);
      },
      onError: (error) => notifications.show({ color: 'red', message: error.message }),
    });

  const rows = students.data ?? [];

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Ученики</Title>
        <Group>
          <Switch
            label="Только активные"
            checked={onlyActive}
            onChange={(e) => setOnlyActive(e.currentTarget.checked)}
          />
          <Button onClick={() => setOpen(true)}>Добавить</Button>
        </Group>
      </Group>
      {students.isSuccess && rows.length === 0 ? (
        <Text c="dimmed">{onlyActive ? 'Активных учеников нет.' : 'Учеников пока нет.'}</Text>
      ) : (
        <Card className="data-card">
          <Table.ScrollContainer minWidth={600}>
            <Table highlightOnHover verticalSpacing="sm" horizontalSpacing="lg">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>ФИО</Table.Th>
                  <Table.Th>Класс</Table.Th>
                  <Table.Th>Формат</Table.Th>
                  <Table.Th>Родитель</Table.Th>
                  <Table.Th>Статус</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {rows.map((student) => (
                  <Table.Tr key={student.id}>
                    <Table.Td>
                      <Anchor component={Link} to={`/students/${student.id}`}>
                        {student.full_name}
                      </Anchor>
                    </Table.Td>
                    <Table.Td>{gradeLabel(student)}</Table.Td>
                    <Table.Td>{formatLabel[student.format]}</Table.Td>
                    <Table.Td>
                      <Anchor component={Link} to={`/parents/${student.parent.id}`}>
                        {student.parent.full_name}
                      </Anchor>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={student.is_active ? 'green' : 'gray'} variant="light">
                        {student.is_active ? 'Активен' : 'Неактивен'}
                      </Badge>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>
      )}
      <Modal opened={open} onClose={() => setOpen(false)} title="Новый ученик" closeOnEscape={false}>
        <StudentForm parents={parents.data ?? []} busy={create.isPending} onSubmit={(d) => submit(d as StudentCreate)} />
      </Modal>
    </>
  );
}
