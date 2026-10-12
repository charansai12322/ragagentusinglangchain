import { useState, useCallback } from 'react';
import { apiClient, ApiErrorResponse } from '../services/api';
import { Citation } from '../types';
import { ChatMessage } from '../features/document-chat/MessageItem';
import { BRANDING } from '../config/branding';

export function useDocumentChat(sessionId: string | null, onSessionExpired?: () => void) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<ApiErrorResponse | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const clearChatError = useCallback(() => {
    setError(null);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setInput('');
    setError(null);
    setActiveCitation(null);
  }, []);

  const inspectCitation = useCallback((citation: Citation) => {
    setActiveCitation(citation);
  }, []);

  const closeCitation = useCallback(() => {
    setActiveCitation(null);
  }, []);

  const askQuestion = useCallback(
    async (questionOverride?: string) => {
      const questionToAsk = (questionOverride !== undefined ? questionOverride : input).trim();

      if (!sessionId) {
        setError(
          new ApiErrorResponse(
            400,
            'NO_ACTIVE_SESSION',
            'No active document session available for questioning.',
            'NO_ACTIVE_SESSION'
          )
        );
        return;
      }

      if (questionToAsk.length === 0) {
        setError(
          new ApiErrorResponse(
            422,
            'VALIDATION_ERROR',
            'Please enter a question about the document.',
            'VALIDATION_ERROR'
          )
        );
        return;
      }

      if (questionToAsk.length > BRANDING.maxQuestionChars) {
        setError(
          new ApiErrorResponse(
            422,
            'VALIDATION_ERROR',
            `Questions cannot exceed ${BRANDING.maxQuestionChars} characters.`,
            'VALIDATION_ERROR'
          )
        );
        return;
      }

      const timestamp = new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });

      const userMessageId = `user-${Date.now()}`;
      const assistantPendingId = `assistant-pending-${Date.now()}`;

      // 1. Append user message and pending assistant message
      const userMessage: ChatMessage = {
        id: userMessageId,
        role: 'user',
        content: questionToAsk,
        timestamp,
      };

      const pendingAssistantMessage: ChatMessage = {
        id: assistantPendingId,
        role: 'assistant',
        content: '',
        timestamp,
        isPending: true,
      };

      setMessages((prev) => [...prev, userMessage, pendingAssistantMessage]);
      setIsAsking(true);
      setError(null);

      // If user submitted from composer input, clear the input now
      if (!questionOverride) {
        setInput('');
      }

      try {
        const response = await apiClient.askQuestion(sessionId, questionToAsk);

        // Replace pending assistant turn with actual response
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantPendingId
              ? {
                  id: `assistant-${Date.now()}`,
                  role: 'assistant',
                  content: response.answer,
                  citations: response.citations,
                  timestamp: new Date().toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  }),
                  isPending: false,
                }
              : msg
          )
        );
      } catch (err) {
        const apiErr = err as ApiErrorResponse;
        setError(apiErr);

        // Remove the pending assistant message
        setMessages((prev) => prev.filter((msg) => msg.id !== assistantPendingId));

        // Restore input in the composer so user can edit and retry easily
        if (!questionOverride) {
          setInput(questionToAsk);
        }

        // If session not found / expired (404), trigger callback
        if (apiErr.status === 404 || apiErr.code === 'SESSION_NOT_FOUND') {
          onSessionExpired?.();
        }
      } finally {
        setIsAsking(false);
      }
    },
    [sessionId, input, onSessionExpired]
  );

  return {
    messages,
    input,
    setInput,
    isAsking,
    error,
    clearChatError,
    clearMessages,
    activeCitation,
    inspectCitation,
    closeCitation,
    askQuestion,
  };
}
