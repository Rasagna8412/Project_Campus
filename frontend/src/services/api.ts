import { HealthResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Fetch with timeout utility to detect network latency or service unreachability.
 */
async function fetchWithTimeout(resource: string, options: RequestInit = {}, timeoutMs = 5000): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(resource, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(id);
  }
}

/**
 * Call the live backend health endpoint.
 * Genuinely inspects application and database connectivity.
 */
export async function checkBackendHealth(verifyDatabase = true): Promise<HealthResponse> {
  const endpoint = verifyDatabase
    ? `${API_BASE_URL}/api/v1/health?check_db=true`
    : `${API_BASE_URL}/health`;

  try {
    const response = await fetchWithTimeout(endpoint, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    }, 4000);

    if (!response.ok && response.status !== 503) {
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }

    const data: HealthResponse = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.name === 'AbortError') {
        throw new Error('Backend request timed out (service unreachable)');
      }
      throw err;
    }
    throw new Error('Unknown connection error occurred while contacting backend');
  }
}
