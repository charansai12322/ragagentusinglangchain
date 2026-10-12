import {
  ChatRequest,
  ChatResponse,
  DocumentIngestResponse,
  HealthResponse,
  SessionStatusResponse,
} from '../types';

const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const BASE_URL = RAW_BASE_URL.replace(/\/+$/, '');

export class ApiErrorResponse extends Error {
  code: string;
  detail: string;
  requestId?: string;
  status: number;

  constructor(status: number, error: string, detail: string, code: string, requestId?: string) {
    super(detail || error);
    this.name = 'ApiErrorResponse';
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.requestId = requestId;
  }
}

class ApiClient {
  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${BASE_URL}${path}`;

    let res: Response;
    try {
      res = await fetch(url, {
        ...options,
        headers: {
          Accept: 'application/json',
          ...options?.headers,
        },
      });
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        throw err;
      }
      throw new ApiErrorResponse(
        0,
        'NETWORK_ERROR',
        'Could not reach the backend service. Please check your internet connection or verify the server is running.',
        'NETWORK_ERROR'
      );
    }

    const requestId = res.headers.get('x-request-id') || undefined;

    if (!res.ok) {
      let errorData: { error?: string; detail?: string; code?: string; request_id?: string } = {};
      try {
        errorData = await res.json();
      } catch {
        const text = await res.text().catch(() => '');
        errorData = {
          error: 'SERVER_ERROR',
          detail: text || `Server returned error status ${res.status}`,
          code: 'SERVER_ERROR',
        };
      }

      throw new ApiErrorResponse(
        res.status,
        errorData.error || 'ERROR',
        errorData.detail || `Request failed with status ${res.status}`,
        errorData.code || 'UNKNOWN_ERROR',
        errorData.request_id || requestId
      );
    }

    return res.json();
  }

  async getHealth(signal?: AbortSignal): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health', { signal });
  }

  async uploadDocument(file: File, signal?: AbortSignal): Promise<DocumentIngestResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.request<DocumentIngestResponse>('/api/documents/upload', {
      method: 'POST',
      body: formData,
      signal,
    });
  }

  async ingestFromUrl(url: string, signal?: AbortSignal): Promise<DocumentIngestResponse> {
    return this.request<DocumentIngestResponse>('/api/documents/url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
      signal,
    });
  }

  async ingestUrl(url: string, signal?: AbortSignal): Promise<DocumentIngestResponse> {
    return this.ingestFromUrl(url, signal);
  }

  async getSessionStatus(sessionId: string, signal?: AbortSignal): Promise<SessionStatusResponse> {
    return this.request<SessionStatusResponse>(`/api/documents/${sessionId}/status`, { signal });
  }

  async deleteSession(sessionId: string, signal?: AbortSignal): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/documents/${sessionId}`, {
      method: 'DELETE',
      signal,
    });
  }

  async askQuestion(
    sessionId: string,
    payload: string | ChatRequest,
    signal?: AbortSignal
  ): Promise<ChatResponse> {
    const bodyObj = typeof payload === 'string' ? { question: payload } : payload;
    return this.request<ChatResponse>(`/api/documents/${sessionId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyObj),
      signal,
    });
  }
}

export const apiClient = new ApiClient();
export const api = apiClient;
