import { Badge, Button, Card, Group, Stack, Text, Textarea, TextInput, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { useCancelLesson, useLesson, useSaveHomework, useUpdateLesson } from '../../api/lessons';
import type { Lesson } from '../../api/types';
import { useAuth } from '../../auth/AuthContext';
import { HomeworkFiles } from '../../components/HomeworkFiles';
import { MoveLessonModal } from '../../components/MoveLessonModal';
import { ParticipantsTable } from '../../components/ParticipantsTable';
import { askCancelScope } from '../../components/ScopeDialog';
import { fmtDateTime, weekdayName } from '../../lib/dates';
import { formatLabel, statusColor, statusLabel } from '../../lib/format';

const metaLine = (lesson: Lesson) =>
  [
    `${lesson.duration_minutes} мин`,
    lesson.title,
    lesson.format ? formatLabel[lesson.format] : null,
    lesson.detached ? 'изменено отдельно от серии' : null,
  ]
    .filter(Boolean)
    .join(' · ');

function useDraft(saved: string | null | undefined) {
  const [draft, setDraft] = useState(saved ?? '');
  useEffect(() => {
    if (saved !== undefined && saved !== null) setDraft(saved);
  }, [saved]);
  return [draft, setDraft] as const;
}

export function LessonPage() {
  const lessonId = Number(useParams().lessonId);
  const { user } = useAuth();
  const lesson = useLesson(lessonId);
  const update = useUpdateLesson(lessonId);
  const cancel = useCancelLesson();
  const saveHomework = useSaveHomework(lessonId);
  const isTutor = user?.role === 'tutor';

  const [topic, setTopic] = useDraft(lesson.data?.topic);
  const [homework, setHomework] = useDraft(lesson.data?.homework_text);
  const [comment, setComment] = useDraft(lesson.data?.parent_comment);
  const [notes, setNotes] = useDraft(lesson.data?.tutor_notes);
  const [moveOpen, setMoveOpen] = useState(false);

  if (lesson.isError) return <Text c="dimmed">{lesson.error.message}</Text>;
  if (!lesson.data) return null;
  const data = lesson.data;
  const onError = (error: Error) => notifications.show({ color: 'red', message: error.message });
  const ok = (message: string) => () => notifications.show({ color: 'green', message });

  const doCancel = async () => {
    const scope = await askCancelScope(data, 'Отменить занятие');
    if (!scope || scope === 'all') return;
    cancel.mutate({ id: data.id, scope }, { onSuccess: ok('Занятие отменено'), onError });
  };

  return (
    <Stack maw={860}>
      <Group justify="space-between" align="flex-start">
        <div>
          <Title order={2} className="first-upper">
            {weekdayName(data.scheduled_start)}, {fmtDateTime(data.scheduled_start)}
          </Title>
          <Group gap="xs" mt={4}>
            <Badge color={statusColor[data.status]} variant="light">
              {statusLabel[data.status]}
            </Badge>
            <Text size="sm" c="dimmed">
              {metaLine(data)}
            </Text>
          </Group>
        </div>
        {isTutor && data.status !== 'cancelled' && (
          <Group>
            {data.status === 'planned' && (
              <Button variant="default" onClick={() => setMoveOpen(true)}>
                Перенести
              </Button>
            )}
            <Button variant="light" color="red" onClick={doCancel} loading={cancel.isPending}>
              Отменить
            </Button>
          </Group>
        )}
      </Group>

      <Card>
        <Title order={4} mb="xs">
          Тема
        </Title>
        {isTutor ? (
          <Group align="flex-end" wrap="nowrap">
            <TextInput
              style={{ flex: 1 }}
              aria-label="Тема занятия"
              value={topic}
              onChange={(e) => setTopic(e.currentTarget.value)}
              placeholder="Что проходили"
            />
            <Button
              variant="default"
              disabled={topic === data.topic}
              loading={update.isPending}
              onClick={() => update.mutate({ topic }, { onSuccess: ok('Тема сохранена'), onError })}
            >
              Сохранить
            </Button>
          </Group>
        ) : (
          <Text>{data.topic || '—'}</Text>
        )}
      </Card>

      <Card>
        <Title order={4} mb="xs">
          Участники
        </Title>
        <ParticipantsTable lesson={data} canEdit={isTutor} />
        {data.previous_grade !== null && (
          <Text size="sm" c="dimmed" mt="xs">
            Оценка за предыдущую домашку: {data.previous_grade}
          </Text>
        )}
      </Card>

      <Card>
        <Title order={4} mb="xs">
          Домашнее задание
        </Title>
        {isTutor ? (
          <Stack gap="xs">
            <Textarea
              aria-label="Текст домашнего задания"
              value={homework}
              onChange={(e) => setHomework(e.currentTarget.value)}
              autosize
              minRows={3}
              placeholder="Текст домашки"
            />
            <Group justify="space-between">
              <Text size="xs" c="dimmed">
                {data.homework_saved_at ? `Сохранено ${fmtDateTime(data.homework_saved_at)}` : 'Ещё не сохранялось'}
              </Text>
              <Button
                disabled={homework === data.homework_text}
                loading={saveHomework.isPending}
                onClick={() => saveHomework.mutate(homework, { onSuccess: ok('Домашка сохранена'), onError })}
              >
                Сохранить домашку
              </Button>
            </Group>
          </Stack>
        ) : (
          <Text style={{ whiteSpace: 'pre-wrap' }} c={data.homework_text ? undefined : 'dimmed'}>
            {data.homework_text || 'Домашки нет'}
          </Text>
        )}
        <Title order={5} mt="md" mb="xs">
          Файлы
        </Title>
        <HomeworkFiles lesson={data} canEdit={isTutor} />
      </Card>

      {data.parent_comment !== null && (
        <Card>
          <Title order={4} mb="xs">
            Комментарий для родителя
          </Title>
          {isTutor ? (
            <Stack gap="xs">
              <Textarea
                aria-label="Комментарий для родителя"
                value={comment}
                onChange={(e) => setComment(e.currentTarget.value)}
                autosize
                minRows={2}
                placeholder="Что стоит знать родителю об этом занятии"
              />
              <Group justify="flex-end">
                <Button
                  variant="default"
                  disabled={comment === data.parent_comment}
                  loading={update.isPending}
                  onClick={() =>
                    update.mutate({ parent_comment: comment }, { onSuccess: ok('Комментарий сохранён'), onError })
                  }
                >
                  Сохранить
                </Button>
              </Group>
            </Stack>
          ) : (
            <Text style={{ whiteSpace: 'pre-wrap' }} c={data.parent_comment ? undefined : 'dimmed'}>
              {data.parent_comment || 'Комментария нет'}
            </Text>
          )}
        </Card>
      )}

      {isTutor && data.tutor_notes !== null && (
        <Card>
          <Title order={4} mb="xs">
            Заметки (видите только вы)
          </Title>
          <Stack gap="xs">
            <Textarea
              aria-label="Заметки репетитора"
              value={notes}
              onChange={(e) => setNotes(e.currentTarget.value)}
              autosize
              minRows={2}
            />
            <Group justify="flex-end">
              <Button
                variant="default"
                disabled={notes === data.tutor_notes}
                loading={update.isPending}
                onClick={() => update.mutate({ tutor_notes: notes }, { onSuccess: ok('Заметки сохранены'), onError })}
              >
                Сохранить
              </Button>
            </Group>
          </Stack>
        </Card>
      )}

      <MoveLessonModal lesson={moveOpen ? data : null} onClose={() => setMoveOpen(false)} />
    </Stack>
  );
}
