import { Stack, Title } from '@mantine/core';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useStudentLessons } from '../../api/cabinet';
import { LessonList } from '../../components/LessonList';
import { monthRange, MonthSwitcher } from '../../components/MonthSwitcher';

export function StudentLessonsPage() {
  const navigate = useNavigate();
  const [monthOffset, setMonthOffset] = useState(0);
  const { start, end } = monthRange(monthOffset);
  const lessons = useStudentLessons(start, end);

  return (
    <Stack>
      <Title order={2}>Занятия</Title>
      <MonthSwitcher month={start} onShift={(months) => setMonthOffset((v) => v + months)} />
      <LessonList
        lessons={lessons.data ?? []}
        showParticipants={false}
        onOpen={(lesson) => navigate(`/lessons/${lesson.id}`)}
        emptyText="В этом месяце занятий нет"
      />
    </Stack>
  );
}
