export class ApiError extends Error {
  constructor(
    message: string,
    public status: number = 200,
  ) {
    super(message);
  }
}

interface Envelope<T> {
  error: boolean;
  message: string;
  payload: T;
}

export const AUTH_LOGOUT_EVENT = 'auth:logout';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, { credentials: 'include', ...init });
  if (response.status === 401) {
    window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT));
    throw new ApiError('Требуется вход', 401);
  }
  if (response.status === 403) throw new ApiError('Нет доступа', 403);
  if (response.status === 422) throw new ApiError('Проверьте заполнение формы', 422);
  if (!response.ok) throw new ApiError(`Ошибка сервера (${response.status})`, response.status);
  const body = (await response.json()) as Envelope<T>;
  if (body.error) throw new ApiError(body.message);
  return body.payload;
}

const json = (method: string, data?: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: data === undefined ? undefined : JSON.stringify(data),
});

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) => request<T>(path, json('POST', data)),
  patch: <T>(path: string, data?: unknown) => request<T>(path, json('PATCH', data)),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  upload: <T>(path: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<T>(path, { method: 'POST', body: form });
  },
};

export function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const entries = Object.entries(params).filter(([, value]) => value !== undefined && value !== null);
  if (entries.length === 0) return '';
  return (
    '?' +
    entries.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`).join('&')
  );
}
