import React from 'react';
import { BookOpen } from 'lucide-react';
import { Citation } from '../../types';
import { CitationPill } from './CitationPill';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp?: string;
  isPending?: boolean;
}

export interface MessageItemProps {
  message: ChatMessage;
  onCitationClick?: (citation: Citation) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onCitationClick,
}) => {
  const isUser = message.role === 'user';

  // Format assistant content into clean paragraphs
  const renderFormattedContent = (text: string) => {
    const paragraphs = text.split('\n\n').filter((p) => p.trim().length > 0);
    if (paragraphs.length <= 1) {
      return (
        <div style={{ whiteSpace: 'pre-wrap', lineHeight: 'var(--leading-relaxed)' }}>
          {text}
        </div>
      );
    }
    return paragraphs.map((para, i) => (
      <p
        key={i}
        style={{
          marginBottom: i === paragraphs.length - 1 ? 0 : '0.875rem',
          lineHeight: 'var(--leading-relaxed)',
        }}
      >
        {para}
      </p>
    ));
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '1.75rem',
        width: '100%',
      }}
    >
      {/* Sender Label & Timestamp */}
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: 'var(--color-taupe)',
          marginBottom: '0.375rem',
          padding: '0 0.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        <span>{isUser ? 'You' : 'Reading Room'}</span>
        {message.timestamp && <span>• {message.timestamp}</span>}
      </div>

      {/* Message Bubble / Surface */}
      <div
        style={{
          maxWidth: isUser ? '85%' : '94%',
          backgroundColor: isUser ? 'var(--color-sand-light)' : 'var(--color-paper)',
          border: `1px solid ${
            isUser ? 'var(--color-sand-border)' : 'var(--color-sand)'
          }`,
          borderRadius: isUser
            ? 'var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg)'
            : 'var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm)',
          padding: isUser ? '0.875rem 1.125rem' : '1.25rem 1.5rem',
          boxShadow: isUser ? 'var(--shadow-subtle)' : 'var(--shadow-paper)',
          color: 'var(--color-espresso)',
          fontSize: 'var(--text-base)',
        }}
      >
        {message.isPending ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'var(--color-taupe)',
              fontStyle: 'italic',
              padding: '0.25rem 0',
            }}
            role="status"
            aria-label="Generating grounded answer"
          >
            <span
              className="coffee-spinner coffee-spinner--sm"
              aria-hidden="true"
            />
            <span>Consulting document pages…</span>
          </div>
        ) : (
          renderFormattedContent(message.content)
        )}
      </div>

      {/* Grounded Citations (if assistant response has citations) */}
      {!isUser &&
        !message.isPending &&
        message.citations &&
        message.citations.length > 0 && (
          <div
            style={{
              marginTop: '0.75rem',
              padding: '0 0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              flexWrap: 'wrap',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                color: 'var(--color-taupe)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
            >
              <BookOpen size={12} aria-hidden="true" />
              <span>Grounded in:</span>
            </span>

            {message.citations.map((citation, idx) => (
              <CitationPill
                key={`${citation.page}-${idx}`}
                citation={citation}
                onClick={() => onCitationClick?.(citation)}
              />
            ))}
          </div>
        )}
    </div>
  );
};
