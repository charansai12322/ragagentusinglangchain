/**
 * Typed API models mirroring backend schemas.
 */

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  groq_configured: boolean;
  groq_model: string;
  embedding_model: string;
  active_sessions: number;
}

export interface Citation {
  page: number;
  snippet: string;
  relevance_score: number;
}

export interface DocumentIngestResponse {
  session_id: string;
  filename: string;
  total_pages: number;
  chunk_count: number;
  status: 'processing' | 'ready' | 'failed';
  created_at: string;
  expires_at: string;
}

export interface ChatRequest {
  question: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  session_id: string;
  processing_time_ms: number;
}

export interface SessionStatusResponse {
  session_id: string;
  filename: string;
  status: 'processing' | 'ready' | 'failed' | 'expired';
  total_pages: number;
  chunk_count: number;
  created_at: string;
  expires_at: string;
  turns_count: number;
}

export interface ApiError {
  error: string;
  detail: string;
  code: string;
  request_id?: string;
}
