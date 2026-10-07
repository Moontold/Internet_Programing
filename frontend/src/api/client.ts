/** Единый конверт ответа backend: все эндпоинты отвечают только им. */
export type BaseResponse<T> = {
  error: boolean;
  message: string;
  payload: T;
};

export type HealthStatus = {
  service: string;
  version: string;
  database: string;
  timezone: string;
};

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`/api${path}`, { credentials: 'include' });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const body = (await response.json()) as BaseResponse<T>;
  if (body.error) {
    throw new Error(body.message);
  }
  return body.payload;
}

export const fetchHealth = () => apiGet<HealthStatus>('/health');
