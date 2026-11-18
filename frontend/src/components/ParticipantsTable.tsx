import { Group, Select, Stack, Table, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';

import { useUpdateParticipant } from '../api/lessons';
import type { HomeworkStatus, Lesson } from '../api/types';
import { homeworkStatusLabel } from '../lib/format';

const STATUS_OPTIONS = (Object.keys(homeworkStatusLabel) as HomeworkStatus[]).map((value) => ({
  value,
  label: homeworkStatusLabel[value],
}));
const GRADE_OPTIONS = ['2', '3', '4', '5'];

function ParticipantsReadOnly({ lesson }: { lesson: Lesson }) {
  const visible = lesson.participants.filter((p) => p.homework_status !== null);
  const others = lesson.participants.filter((p) => p.homework_status === null);
  return (
    <Stack gap="sm">
      {visible.map((p) => (
        <Group key={p.student_id} justify="space-between" wrap="nowrap">
          <div>
            <Text fw={600}>{p.full_name}</Text>
            <Text size="sm" c="dimmed">
              Домашка: {homeworkStatusLabel[p.homework_status ?? 'not_checked'].toLowerCase()}
            </Text>
          </div>
          {p.homework_grade !== null && (
            <span className="grade-mark grade-mark--lg" title="Оценка за домашку">
              {p.homework_grade}
            </span>
          )}
        </Group>
      ))}
      {others.length > 0 && (
        <Text size="sm" c="dimmed">
          Также на занятии: {others.map((p) => p.full_name).join(', ')}
        </Text>
      )}
    </Stack>
  );
}

export function ParticipantsTable({ lesson, canEdit }: { lesson: Lesson; canEdit: boolean }) {
  const update = useUpdateParticipant(lesson.id);
  const onError = (error: Error) => notifications.show({ color: 'red', message: error.message });

  if (!canEdit) return <ParticipantsReadOnly lesson={lesson} />;

  return (
    <Table.ScrollContainer minWidth={460}>
      <Table verticalSpacing="xs">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Ученик</Table.Th>
            <Table.Th w={190}>Домашка</Table.Th>
            <Table.Th w={120}>Оценка</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {lesson.participants.map((p) => (
            <Table.Tr key={p.student_id}>
              <Table.Td>{p.full_name}</Table.Td>
              <Table.Td>
                <Select
                  size="xs"
                  aria-label={`Домашка: ${p.full_name}`}
                  data={STATUS_OPTIONS}
                  value={p.homework_status ?? 'not_checked'}
                  allowDeselect={false}
                  onChange={(v) =>
                    v &&
                    update.mutate(
                      { studentId: p.student_id, data: { homework_status: v as HomeworkStatus } },
                      { onError },
                    )
                  }
                />
              </Table.Td>
              <Table.Td>
                <Select
                  size="xs"
                  aria-label={`Оценка: ${p.full_name}`}
                  data={GRADE_OPTIONS}
                  value={p.homework_grade ? String(p.homework_grade) : null}
                  placeholder="—"
                  clearable
                  w={90}
                  onChange={(v) =>
                    update.mutate(
                      {
                        studentId: p.student_id,
                        data: v ? { homework_grade: Number(v) } : { clear_grade: true },
                      },
                      { onError },
                    )
                  }
                />
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  );
}
