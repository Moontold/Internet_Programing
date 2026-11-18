import { ActionIcon, Anchor, Button, FileButton, Group, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';

import { fileUrl, useDeleteFile, useUploadFile } from '../api/files';
import type { Lesson } from '../api/types';
import { fmtSize } from '../lib/format';

export function HomeworkFiles({ lesson, canEdit }: { lesson: Lesson; canEdit: boolean }) {
  const upload = useUploadFile(lesson.id);
  const remove = useDeleteFile(lesson.id);
  const onError = (error: Error) => notifications.show({ color: 'red', message: error.message });

  return (
    <Stack gap="xs">
      {lesson.files.length === 0 && (
        <Text size="sm" c="dimmed">
          Файлов нет
        </Text>
      )}
      {lesson.files.map((file) => (
        <Group key={file.id} justify="space-between" wrap="nowrap">
          <Anchor href={fileUrl(file.id)} download={file.original_name} lineClamp={1}>
            {file.original_name}
          </Anchor>
          <Group gap="xs" wrap="nowrap">
            <Text size="xs" c="dimmed">
              {fmtSize(file.size)}
            </Text>
            {canEdit && (
              <ActionIcon
                variant="subtle"
                color="red"
                aria-label={`Удалить ${file.original_name}`}
                loading={remove.isPending && remove.variables === file.id}
                onClick={() => remove.mutate(file.id, { onError })}
              >
                ✕
              </ActionIcon>
            )}
          </Group>
        </Group>
      ))}
      {canEdit && (
        <Group>
          <FileButton onChange={(file) => file && upload.mutate(file, { onError })}>
            {(props) => (
              <Button {...props} variant="default" size="xs" loading={upload.isPending}>
                Прикрепить файл
              </Button>
            )}
          </FileButton>
        </Group>
      )}
    </Stack>
  );
}
