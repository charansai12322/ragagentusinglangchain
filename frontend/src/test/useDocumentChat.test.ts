import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDocumentChat } from '../hooks/useDocumentChat';
import { apiClient, ApiErrorResponse } from '../services/api';

describe('useDocumentChat hook', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('rejects sending question when no session is present', async () => {
    const { result } = renderHook(() => useDocumentChat(null));

    await act(async () => {
      await result.current.askQuestion('What is this about?');
    });

    expect(result.current.error?.code).toBe('NO_ACTIVE_SESSION');
    expect(result.current.messages).toHaveLength(0);
  });

  it('rejects empty or whitespace question', async () => {
    const { result } = renderHook(() => useDocumentChat('active-session'));

    await act(async () => {
      await result.current.askQuestion('   ');
    });

    expect(result.current.error?.code).toBe('VALIDATION_ERROR');
    expect(result.current.messages).toHaveLength(0);
  });

  it('appends user message and replaces pending assistant message on success', async () => {
    const mockChatResponse = {
      answer: 'This is the verified answer grounded in page 4.',
      citations: [
        {
          page: 4,
          snippet: 'Key findings are detailed here.',
          relevance_score: 0.89,
        },
      ],
      session_id: 'active-session',
      processing_time_ms: 220,
    };

    vi.spyOn(apiClient, 'askQuestion').mockResolvedValue(mockChatResponse);

    const { result } = renderHook(() => useDocumentChat('active-session'));

    act(() => {
      result.current.setInput('What are the key findings?');
    });

    await act(async () => {
      await result.current.askQuestion();
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('What are the key findings?');
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toBe('This is the verified answer grounded in page 4.');
    expect(result.current.messages[1].citations).toEqual(mockChatResponse.citations);
    expect(result.current.messages[1].isPending).toBe(false);
    expect(result.current.input).toBe('');
    expect(result.current.isAsking).toBe(false);
  });

  it('restores input and triggers callback when session expires (404)', async () => {
    const onSessionExpired = vi.fn();
    const notFoundError = new ApiErrorResponse(
      404,
      'SESSION_NOT_FOUND',
      'Session expired or missing',
      'SESSION_NOT_FOUND'
    );

    vi.spyOn(apiClient, 'askQuestion').mockRejectedValue(notFoundError);

    const { result } = renderHook(() => useDocumentChat('expired-session', onSessionExpired));

    act(() => {
      result.current.setInput('Tell me about section 2.');
    });

    await act(async () => {
      await result.current.askQuestion();
    });

    expect(onSessionExpired).toHaveBeenCalledTimes(1);
    expect(result.current.error?.code).toBe('SESSION_NOT_FOUND');
    // Input is restored so the user can retry without re-typing
    expect(result.current.input).toBe('Tell me about section 2.');
    // Pending assistant message is removed
    expect(result.current.messages.filter((m) => m.isPending)).toHaveLength(0);
  });

  it('allows selecting and clearing active citations', () => {
    const { result } = renderHook(() => useDocumentChat('active-session'));

    const citation = {
      page: 3,
      snippet: 'Excerpt text',
      relevance_score: 0.95,
    };

    act(() => {
      result.current.inspectCitation(citation);
    });

    expect(result.current.activeCitation).toEqual(citation);

    act(() => {
      result.current.closeCitation();
    });

    expect(result.current.activeCitation).toBeNull();
  });
});
