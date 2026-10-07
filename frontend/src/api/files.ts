import { useMutation, useQueryClient } from '@tanstack/react-query';

import { api } from './client';
import { LESSONS_KEY } from './lessons';
import type { FileInfo } from './types';

export const fileUrl = (fileId: number) => `/api/files/${fileId}`;

export function useUploadFile(lessonId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.upload<FileInfo>(`/lessons/${lessonId}/files`, file),
    onSuccess: () => client.invalidateQueries({ queryKey: [LESSONS_KEY] }),
  });
}

export function useDeleteFile(lessonId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (fileId: number) => api.del<null>(`/lessons/${lessonId}/files/${fileId}`),
    onSuccess: () => client.invalidateQueries({ queryKey: [LESSONS_KEY] }),
  });
}
