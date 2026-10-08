import { Anchor, Badge, Button, Card, Group, Modal, Stack, Text, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import dayjs from 'dayjs';
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useLessons } from '../../api/lessons';
import { useParents } from '../../api/parents';
import { useResetStudentPassword, useStudent, useUpdateStudent } from '../../api/students';
import type { StudentUpdate } from '../../api/types';
import { LessonList } from '../../components/LessonList';
import { showPassword } from '../../components/PasswordModal';
import { StatsBadges } from '../../components/StatsBadges';
import { StudentForm } from '../../components/StudentForm';
import { describeSeries } from '../../lib/dates';
import { fmtMoney, formatLabel, gradeLabel } from '../../lib/format';

const lessonsFrom = dayjs().subtract(2, 'month').startOf('day').toDate();
const lessonsTo = dayjs().add(1, 'month').endOf('day').toDate();

export function StudentCardPage() {
  const studentId = Number(useParams().studentId);
  const navigate = useNavigate();
  const student = useStudent(studentId);
  const lessons = useLessons(lessonsFrom, lessonsTo, studentId);
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
          <StatsBadges stats={data.stats} />
        </Stack>
      </Card>
      <Card>
        <Title order={4} mb="xs">
          Расписание
        </Title>
        {data.series.length === 0 && (
          <Text c="dimmed">
            Регулярных занятий нет. Добавьте их в{' '}
            <Anchor component={Link} to="/schedule">
              расписании
            </Anchor>
            .
          </Text>
        )}
        {data.series.map((series) => (
          <Text key={series.id}>
            {describeSeries(series)}
            {series.title ? ` — ${series.title}` : ''}
            {series.students.length > 1 ? ` (группа: ${series.students.map((s) => s.full_name).join(', ')})` : ''}
          </Text>
        ))}
      </Card>
      <Card>
        <Title order={4} mb="xs">
          Занятия
        </Title>
        <LessonList
          lessons={lessons.data ?? []}
          showParticipants={false}
          onOpen={(lesson) => navigate(`/lessons/${lesson.id}`)}
          emptyText="За последние два месяца и ближайший месяц занятий нет"
        />
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
