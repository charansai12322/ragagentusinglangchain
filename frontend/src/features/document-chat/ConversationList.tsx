import React, { useEffect, useRef } from 'react';
import { Sparkles, HelpCircle } from 'lucide-react';
import { BRANDING } from '../../config/branding';
import { Citation } from '../../types';
import { ChatMessage, MessageItem } from './MessageItem';

export interface ConversationListProps {
  messages: ChatMessage[];
  filename: string;
  onCitationClick: (citation: Citation) => void;
  onSelectSuggestedQuestion: (question: string) => void;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  messages,
  filename,
  onCitationClick,
  onSelectSuggestedQuestion,
}) => {
  const bottomAnchorRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomAnchorRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div
      style={{
        flex: 1,
        padding: '2rem 0',
      }}
    >
      <div className="workspace-container">
        {messages.length === 0 ? (
          /* Empty conversation state with suggested inquiries */
          <div
            style={{
              padding: '3rem 1rem',
              textAlign: 'center',
              maxWidth: '580px',
              margin: '0 auto',
            }}
          >
            <div
              style={{
                width: '3rem',
                height: '3rem',
                margin: '0 auto 1.25rem',
                borderRadius: 'var(--radius-full)',
                backgroundColor: 'var(--color-caramel-subtle)',
                color: 'var(--color-caramel-hover)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Sparkles size={20} aria-hidden="true" />
            </div>

            <h2
              style={{
                fontFamily: 'var(--font-serif)',
                fontSize: 'var(--text-2xl)',
                color: 'var(--color-espresso)',
                marginBottom: '0.625rem',
              }}
            >
              The document is ready for inquiry.
            </h2>

            <p
              style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--color-roasted-cocoa)',
                lineHeight: 'var(--leading-relaxed)',
                marginBottom: '2rem',
              }}
            >
              Ask any question regarding <strong style={{ color: 'var(--color-espresso)' }}>{filename}</strong>.
              Every answer will be grounded in relevant pages with traceable citations.
            </p>

            {/* Suggested Question Starters */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.625rem',
                textAlign: 'left',
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--color-taupe)',
                  marginBottom: '0.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.375rem',
                }}
              >
                <HelpCircle size={12} aria-hidden="true" />
                <span>Suggested points of inquiry</span>
              </div>

              {BRANDING.suggestedQuestions.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSelectSuggestedQuestion(q)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem 1rem',
                    backgroundColor: 'var(--color-paper)',
                    border: '1px solid var(--color-sand)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--color-espresso)',
                    fontSize: 'var(--text-sm)',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all var(--transition-fast)',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.02)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--color-caramel)';
                    e.currentTarget.style.backgroundColor = 'var(--color-paper-pure)';
                    e.currentTarget.style.transform = 'translateY(-1px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--color-sand)';
                    e.currentTarget.style.backgroundColor = 'var(--color-paper)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  <span>{q}</span>
                  <span
                    style={{
                      color: 'var(--color-caramel)',
                      fontSize: 'var(--text-xs)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    →
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Conversation message turns */
          <div>
            {messages.map((msg) => (
              <MessageItem
                key={msg.id}
                message={msg}
                onCitationClick={onCitationClick}
              />
            ))}
            <div ref={bottomAnchorRef} />
          </div>
        )}
      </div>
    </div>
  );
};
