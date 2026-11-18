import { api } from './client';
import { useScheduleMutation } from './lessons';
import type { Series, SeriesCreate } from './types';

export const useCreateSeries = () => useScheduleMutation((data: SeriesCreate) => api.post<Series>('/series', data));
