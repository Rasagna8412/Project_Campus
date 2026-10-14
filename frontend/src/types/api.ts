export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unavailable' | 'unknown';
  version: string;
  database?: string | null;
}

export type ConnectionState = 'checking' | 'connected' | 'disconnected' | 'error';
