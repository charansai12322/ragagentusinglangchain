import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDocumentSession } from '../hooks/useDocumentSession';
import { apiClient, ApiErrorResponse } from '../services/api';

describe('useDocumentSession hook', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('initializes in empty idle state', () => {
    const { result } = renderHook(() => useDocumentSession());

    expect(result.current.session).toBeNull();
    expect(result.current.sessionId).toBeNull();
    expect(result.current.isReady).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('updates state to ready upon successful file ingestion', async () => {
    const mockIngest = {
      session_id: 'session-abc',
      filename: 'research.pdf',
      total_pages: 10,
      chunk_count: 24,
      status: 'ready' as const,
      created_at: '2026-10-12T00:00:00Z',
      expires_at: '2026-10-12T01:00:00Z',
    };

    vi.spyOn(apiClient, 'uploadDocument').mockResolvedValue(mockIngest);

    const { result } = renderHook(() => useDocumentSession());

    const file = new File(['dummy content'], 'research.pdf', { type: 'application/pdf' });

    await act(async () => {
      await result.current.ingestFile(file);
    });

    expect(result.current.session).toEqual(mockIngest);
    expect(result.current.sessionId).toBe('session-abc');
    expect(result.current.filename).toBe('research.pdf');
    expect(result.current.totalPages).toBe(10);
    expect(result.current.chunkCount).toBe(24);
    expect(result.current.isReady).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('stores error and keeps session null upon ingestion failure', async () => {
    const apiError = new ApiErrorResponse(
      422,
      'DOCUMENT_PROCESSING_ERROR',
      'Scanned PDF containing no extractable text',
      'DOCUMENT_PROCESSING_ERROR'
    );

    vi.spyOn(apiClient, 'uploadDocument').mockRejectedValue(apiError);

    const { result } = renderHook(() => useDocumentSession());
    const file = new File(['empty text'], 'scanned.pdf', { type: 'application/pdf' });

    await act(async () => {
      try {
        await result.current.ingestFile(file);
      } catch {
        // Expected throw
      }
    });

    expect(result.current.session).toBeNull();
    expect(result.current.isReady).toBe(false);
    expect(result.current.error).toEqual(apiError);
    expect(result.current.isLoading).toBe(false);
  });

  it('resets session correctly on resetSession call', async () => {
    const mockIngest = {
      session_id: 'session-abc',
      filename: 'research.pdf',
      total_pages: 10,
      chunk_count: 24,
      status: 'ready' as const,
      created_at: '2026-10-12T00:00:00Z',
      expires_at: '2026-10-12T01:00:00Z',
    };

    vi.spyOn(apiClient, 'uploadDocument').mockResolvedValue(mockIngest);

    const { result } = renderHook(() => useDocumentSession());
    const file = new File(['dummy'], 'research.pdf', { type: 'application/pdf' });

    await act(async () => {
      await result.current.ingestFile(file);
    });

    expect(result.current.isReady).toBe(true);

    act(() => {
      result.current.resetSession();
    });

    expect(result.current.session).toBeNull();
    expect(result.current.sessionId).toBeNull();
    expect(result.current.isReady).toBe(false);
  });

  it('calls deleteSession API and clears local session state', async () => {
    const mockIngest = {
      session_id: 'session-to-delete',
      filename: 'old.pdf',
      total_pages: 2,
      chunk_count: 4,
      status: 'ready' as const,
      created_at: '2026-10-12T00:00:00Z',
      expires_at: '2026-10-12T01:00:00Z',
    };

    vi.spyOn(apiClient, 'uploadDocument').mockResolvedValue(mockIngest);
    const deleteSpy = vi.spyOn(apiClient, 'deleteSession').mockResolvedValue({ message: 'Deleted' });

    const { result } = renderHook(() => useDocumentSession());
    const file = new File(['dummy'], 'old.pdf', { type: 'application/pdf' });

    await act(async () => {
      await result.current.ingestFile(file);
    });

    expect(result.current.sessionId).toBe('session-to-delete');

    await act(async () => {
      await result.current.deleteSession();
    });

    expect(deleteSpy).toHaveBeenCalledWith('session-to-delete');
    expect(result.current.session).toBeNull();
  });
});
