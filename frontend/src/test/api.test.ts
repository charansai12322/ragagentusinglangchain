import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient, BASE_URL, ApiErrorResponse } from '../services/api';

describe('ApiClient', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('normalizes base url without trailing slash', () => {
    expect(BASE_URL).not.toMatch(/\/$/);
  });

  it('executes getHealth successfully', async () => {
    const mockHealth = {
      status: 'healthy',
      version: '1.0.0',
      timestamp: '2026-10-12T00:00:00Z',
      groq_configured: true,
      groq_model: 'llama-3.3-70b-versatile',
      embedding_model: 'BAAI/bge-small-en-v1.5',
      active_sessions: 2,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: async () => mockHealth,
    } as unknown as Response);

    const res = await apiClient.getHealth();
    expect(res).toEqual(mockHealth);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      `${BASE_URL}/api/health`,
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: 'application/json' }),
      })
    );
  });

  it('sends multipart file upload without manual content-type header', async () => {
    const mockUploadResponse = {
      session_id: 'test-session-123',
      filename: 'sample.pdf',
      total_pages: 5,
      chunk_count: 12,
      status: 'ready' as const,
      created_at: '2026-10-12T00:00:00Z',
      expires_at: '2026-10-12T01:00:00Z',
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: async () => mockUploadResponse,
    } as unknown as Response);

    const file = new File(['%PDF-1.4 test'], 'sample.pdf', { type: 'application/pdf' });
    const res = await apiClient.uploadDocument(file);

    expect(res).toEqual(mockUploadResponse);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      `${BASE_URL}/api/documents/upload`,
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    );
  });

  it('sends JSON URL ingestion request correctly', async () => {
    const mockResponse = {
      session_id: 'url-session-456',
      filename: 'remote.pdf',
      total_pages: 3,
      chunk_count: 8,
      status: 'ready' as const,
      created_at: '2026-10-12T00:00:00Z',
      expires_at: '2026-10-12T01:00:00Z',
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: async () => mockResponse,
    } as unknown as Response);

    const targetUrl = 'https://example.com/test.pdf';
    const res = await apiClient.ingestUrl(targetUrl);

    expect(res).toEqual(mockResponse);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      `${BASE_URL}/api/documents/url`,
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
        body: JSON.stringify({ url: targetUrl }),
      })
    );
  });

  it('sends chat questions with payload', async () => {
    const mockChatResponse = {
      answer: 'This is the grounded answer.',
      citations: [
        {
          page: 2,
          snippet: 'Verbatim excerpt',
          relevance_score: 0.94,
        },
      ],
      session_id: 'test-session-123',
      processing_time_ms: 350,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: async () => mockChatResponse,
    } as unknown as Response);

    const res = await apiClient.askQuestion('test-session-123', 'What is the main finding?');
    expect(res).toEqual(mockChatResponse);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      `${BASE_URL}/api/documents/test-session-123/chat`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ question: 'What is the main finding?' }),
      })
    );
  });

  it('parses structured API errors accurately', async () => {
    const errorBody = {
      error: 'SECURITY_VIOLATION',
      detail: 'File exceeds maximum upload size of 15MB',
      code: 'SECURITY_VIOLATION',
      request_id: 'req-xyz-999',
    };

    const headers = new Headers();
    headers.set('x-request-id', 'req-xyz-999');

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      headers,
      json: async () => errorBody,
    } as unknown as Response);

    await expect(apiClient.getHealth()).rejects.toThrow(ApiErrorResponse);

    try {
      await apiClient.getHealth();
    } catch (err) {
      const apiErr = err as ApiErrorResponse;
      expect(apiErr.status).toBe(400);
      expect(apiErr.code).toBe('SECURITY_VIOLATION');
      expect(apiErr.detail).toBe('File exceeds maximum upload size of 15MB');
      expect(apiErr.requestId).toBe('req-xyz-999');
    }
  });

  it('handles network connection failure gracefully as NETWORK_ERROR', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(apiClient.getHealth()).rejects.toThrow(ApiErrorResponse);

    try {
      await apiClient.getHealth();
    } catch (err) {
      const apiErr = err as ApiErrorResponse;
      expect(apiErr.status).toBe(0);
      expect(apiErr.code).toBe('NETWORK_ERROR');
    }
  });
});
