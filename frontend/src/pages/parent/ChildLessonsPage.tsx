import { Stack, Title } from '@mantine/core';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { useChildLessons, useChildren } from '../../api/cabinet';
import { LessonList } from '../../components/LessonList';
import { monthRange, MonthSwitcher } from '../../components/MonthSwitcher';

export function ChildLessonsPage() {
  const studentId = Number(useParams().studentId);
  const navigate = useNavigate();
  const children = useChildren();
  const [monthOffset, setMonthOffset] = useState(0);
  const { start, end } = monthRange(monthOffset);
  const lessons = useChildLessons(studentId, start, end);
  const child = children.data?.children.find((c) => c.student.id === studentId);

  return (
    <Stack>
      <Title order={2}>{child?.student.full_name ?? 'Занятия'}</Title>
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
