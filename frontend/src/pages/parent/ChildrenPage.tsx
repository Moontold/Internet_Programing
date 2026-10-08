import { Card, SimpleGrid, Stack, Text, Title, UnstyledButton } from '@mantine/core';
import { useNavigate } from 'react-router-dom';

import { useChildren } from '../../api/cabinet';
import { StatsBadges } from '../../components/StatsBadges';
import { describeSeries } from '../../lib/dates';
import { gradeLabel } from '../../lib/format';

export function ChildrenPage() {
  const children = useChildren();
  const navigate = useNavigate();
  const cards = children.data?.children ?? [];

  return (
    <Stack>
      <Title order={2}>Дети</Title>
      {children.isSuccess && cards.length === 0 && (
        <Text c="dimmed">Пока ни один ребёнок не привязан к вашей учётной записи.</Text>
      )}
      <SimpleGrid cols={{ base: 1, sm: 2 }}>
        {cards.map((card) => (
          <UnstyledButton key={card.student.id} onClick={() => navigate(`/children/${card.student.id}/lessons`)}>
            <Card h="100%" className="child-card">
              <Stack gap="xs">
                <Title order={4}>{card.student.full_name}</Title>
                <Text size="sm" c="dimmed">
                  {gradeLabel(card.student)}
                </Text>
                <div>
                  <Text size="sm" fw={600}>
                    Расписание
                  </Text>
                  {card.series.length === 0 && (
                    <Text size="sm" c="dimmed">
                      Регулярных занятий нет
                    </Text>
                  )}
                  {card.series.map((series) => (
                    <Text key={series.id} size="sm">
                      {describeSeries(series)}
                    </Text>
                  ))}
                </div>
                <StatsBadges stats={card.stats} />
                <Text size="sm" c="ink.7" fw={600}>
                  Все занятия
                </Text>
              </Stack>
            </Card>
          </UnstyledButton>
        ))}
      </SimpleGrid>
    </Stack>
  );
}
