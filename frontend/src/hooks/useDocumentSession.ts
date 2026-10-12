import { useState, useCallback } from 'react';
import { apiClient, ApiErrorResponse } from '../services/api';
import { DocumentIngestResponse } from '../types';

export function useDocumentSession() {
  const [session, setSession] = useState<DocumentIngestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeSource, setActiveSource] = useState<string | null>(null);
  const [error, setError] = useState<ApiErrorResponse | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const ingestFile = useCallback(async (file: File) => {
    setIsLoading(true);
    setActiveSource(file.name);
    setError(null);

    try {
      const response = await apiClient.uploadDocument(file);
      setSession(response);
      return response;
    } catch (err) {
      const apiErr = err as ApiErrorResponse;
      setError(apiErr);
      setSession(null);
      throw err;
    } finally {
      setIsLoading(false);
      setActiveSource(null);
    }
  }, []);

  const ingestUrl = useCallback(async (url: string) => {
    setIsLoading(true);
    // Display URL domain/filename as source
    try {
      const parsed = new URL(url);
      const pathname = parsed.pathname.split('/').pop() || parsed.hostname;
      setActiveSource(pathname);
    } catch {
      setActiveSource(url);
    }
    setError(null);

    try {
      const response = await apiClient.ingestUrl(url);
      setSession(response);
      return response;
    } catch (err) {
      const apiErr = err as ApiErrorResponse;
      setError(apiErr);
      setSession(null);
      throw err;
    } finally {
      setIsLoading(false);
      setActiveSource(null);
    }
  }, []);

  const deleteSession = useCallback(async () => {
    if (!session?.session_id) return;

    setIsLoading(true);
    try {
      await apiClient.deleteSession(session.session_id);
    } catch (err) {
      // If 404, session was already deleted or expired, which is acceptable
      const apiErr = err as ApiErrorResponse;
      if (apiErr.status !== 404) {
        console.warn('Session deletion returned non-404 error:', apiErr);
      }
    } finally {
      setSession(null);
      setIsLoading(false);
      setError(null);
    }
  }, [session]);

  const resetSession = useCallback(() => {
    setSession(null);
    setIsLoading(false);
    setError(null);
    setActiveSource(null);
  }, []);

  return {
    session,
    sessionId: session?.session_id || null,
    filename: session?.filename || '',
    totalPages: session?.total_pages || 0,
    chunkCount: session?.chunk_count || 0,
    isReady: session?.status === 'ready',
    isLoading,
    activeSource,
    error,
    clearError,
    ingestFile,
    ingestUrl,
    deleteSession,
    resetSession,
  };
}
