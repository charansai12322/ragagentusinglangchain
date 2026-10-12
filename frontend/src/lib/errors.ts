import { ApiError } from '../types';
import { ApiErrorResponse } from '../services/api';

export interface FormattedError {
  title: string;
  detail: string;
  recovery?: string;
  code?: string;
  requestId?: string;
}

export function formatApiError(err: unknown): FormattedError {
  if (!err) {
    return {
      title: 'Unexpected Issue',
      detail: 'An unexpected issue occurred. Please try again.',
    };
  }

  // If it is our ApiErrorResponse instance
  if (err instanceof ApiErrorResponse) {
    const code = err.code;
    const detail = err.detail || err.message;
    const requestId = err.requestId;

    switch (code) {
      case 'SECURITY_VIOLATION':
        return {
          title: 'Security Rejection',
          detail,
          recovery: 'Please select a clean, non-restricted PDF within 15MB or a safe public URL.',
          code,
          requestId,
        };
      case 'DOCUMENT_PROCESSING_ERROR':
        return {
          title: 'Document Unreadable',
          detail,
          recovery: 'Ensure the PDF contains extractable text and is not encrypted or an unscanned image.',
          code,
          requestId,
        };
      case 'SESSION_NOT_FOUND':
        return {
          title: 'Session Expired or Missing',
          detail: 'Your document reading session has expired or was cleared.',
          recovery: 'Please bring the document back into the workspace to start fresh.',
          code,
          requestId,
        };
      case 'SESSION_CAPACITY_EXCEEDED':
        return {
          title: 'Room Capacity Reached',
          detail: 'The workspace is temporarily at maximum concurrent session capacity.',
          recovery: 'Please wait a moment while other reading sessions complete.',
          code,
          requestId,
        };
      case 'RATE_LIMIT_EXCEEDED':
        return {
          title: 'Provider Rate Limit',
          detail: 'The upstream language model rate limit was reached.',
          recovery: 'Please wait 10–15 seconds and try asking again.',
          code,
          requestId,
        };
      case 'GROQ_AUTH_ERROR':
      case 'CONFIGURATION_ERROR':
        return {
          title: 'Service Configuration Notice',
          detail,
          recovery: 'Please verify the GROQ_API_KEY environment variable is configured in the backend.',
          code,
          requestId,
        };
      case 'LLM_TIMEOUT':
        return {
          title: 'Generation Timed Out',
          detail: 'The language model took too long to synthesize an answer.',
          recovery: 'Please retry with a more concise question.',
          code,
          requestId,
        };
      case 'VALIDATION_ERROR':
        return {
          title: 'Invalid Question',
          detail,
          recovery: 'Ensure your question is between 1 and 2,000 characters.',
          code,
          requestId,
        };
      case 'NETWORK_ERROR':
        return {
          title: 'Connection Interrupted',
          detail,
          recovery: 'Please ensure the backend API server is running on http://localhost:8000.',
          code,
          requestId,
        };
      default:
        return {
          title: 'Request Failed',
          detail,
          code,
          requestId,
        };
    }
  }

  // If it's a typed ApiError from backend payload
  if (typeof err === 'object' && err !== null && 'code' in err) {
    const apiErr = err as ApiError;
    return {
      title: 'API Error',
      detail: apiErr.detail || 'An error occurred.',
      code: apiErr.code,
      requestId: apiErr.request_id,
    };
  }

  if (err instanceof Error) {
    if (err.name === 'AbortError') {
      return {
        title: 'Request Cancelled',
        detail: 'The operation was cancelled by the user.',
      };
    }
    return {
      title: 'Connection Issue',
      detail: err.message || 'Unable to connect to the backend server.',
      recovery: 'Verify the FastAPI backend is running.',
    };
  }

  return {
    title: 'Unexpected Error',
    detail: String(err),
  };
}

export function formatErrorMessage(err: unknown): { title: string; message: string; code?: string; requestId?: string } {
  const formatted = formatApiError(err);
  return {
    title: formatted.title,
    message: formatted.detail,
    code: formatted.code,
    requestId: formatted.requestId,
  };
}
