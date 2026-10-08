import { Card, Stack, Text, Title } from '@mantine/core';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';

import { useStudentLessons, useStudentSeries } from '../../api/cabinet';
import { LessonList } from '../../components/LessonList';
import { describeSeries } from '../../lib/dates';

const nextTwoWeeks = () => ({
  start: dayjs().startOf('day').toDate(),
  end: dayjs().add(14, 'day').endOf('day').toDate(),
});

export function StudentSchedulePage() {
  const navigate = useNavigate();
  const series = useStudentSeries();
  const { start, end } = nextTwoWeeks();
  const lessons = useStudentLessons(start, end);

  return (
    <Stack>
      <Title order={2}>Расписание</Title>
      <Card>
        <Title order={4} mb="xs">
          Регулярные занятия
        </Title>
        {series.isSuccess && series.data.length === 0 && <Text c="dimmed">Регулярных занятий нет</Text>}
        {(series.data ?? []).map((item) => (
          <Text key={item.id}>
            {describeSeries(item)}
            {item.title ? ` — ${item.title}` : ''}
          </Text>
        ))}
      </Card>
      <Title order={4}>Ближайшие две недели</Title>
      <LessonList
        lessons={(lessons.data ?? []).filter((l) => l.status !== 'cancelled')}
        showParticipants={false}
        onOpen={(lesson) => navigate(`/lessons/${lesson.id}`)}
        emptyText="Занятий не запланировано"
      />
    </Stack>
  );
}
