import React, { useRef, useEffect } from 'react';
import { Send, CornerDownLeft } from 'lucide-react';
import { BRANDING } from '../../config/branding';

export interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const ChatComposer: React.FC<ChatComposerProps> = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  disabled = false,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height up to 160px
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim().length > 0 && !isLoading && !disabled) {
        onSubmit();
      }
    }
  };

  const currentLength = value.length;
  const isNearLimit = currentLength > 1800;
  const isOverLimit = currentLength > BRANDING.maxQuestionChars;
  const canSubmit =
    value.trim().length > 0 &&
    !isOverLimit &&
    !isLoading &&
    !disabled;

  return (
    <div
      style={{
        position: 'sticky',
        bottom: 0,
        backgroundColor: 'var(--color-oat-milk)',
        padding: '1rem 0 1.5rem',
        borderTop: '1px solid var(--color-sand)',
      }}
    >
      <div className="workspace-container">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (canSubmit) onSubmit();
          }}
          style={{
            backgroundColor: 'var(--color-paper)',
            border: `1px solid ${
              isOverLimit ? 'var(--color-burnt-terracotta)' : 'var(--color-sand-border)'
            }`,
            borderRadius: 'var(--radius-xl)',
            padding: '0.75rem 1rem',
            boxShadow: 'var(--shadow-paper)',
            display: 'flex',
            flexDirection: 'column',
            transition: 'border-color var(--transition-fast)',
          }}
        >
          <textarea
            ref={textareaRef}
            rows={2}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isLoading}
            placeholder={
              disabled
                ? 'Document is being prepared…'
                : 'Ask something about this document… (Enter to submit, Shift+Enter for newline)'
            }
            aria-label="Ask a question about this document"
            style={{
              width: '100%',
              fontFamily: 'var(--font-sans)',
              fontSize: 'var(--text-base)',
              color: 'var(--color-espresso)',
              backgroundColor: 'transparent',
              border: 'none',
              outline: 'none',
              resize: 'none',
              lineHeight: 'var(--leading-normal)',
            }}
          />

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: '0.5rem',
              paddingTop: '0.5rem',
              borderTop: '1px solid var(--color-sand-light)',
            }}
          >
            {/* Keyboard shortcut hint & Character limit */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                fontSize: 'var(--text-xs)',
                color: isOverLimit
                  ? 'var(--color-burnt-terracotta)'
                  : isNearLimit
                  ? 'var(--color-caramel-hover)'
                  : 'var(--color-taupe)',
              }}
            >
              <span
                style={{
                  display: 'none',
                  alignItems: 'center',
                  gap: '0.25rem',
                }}
                className="desktop-hint"
              >
                <CornerDownLeft size={11} aria-hidden="true" />
                <span>Enter to ask</span>
              </span>

              <span>
                {currentLength} / {BRANDING.maxQuestionChars} chars
              </span>
            </div>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!canSubmit}
              aria-label="Send question"
              className="btn btn--primary btn--sm"
              style={{
                borderRadius: 'var(--radius-full)',
                padding: '0.4rem 0.875rem',
              }}
            >
              {isLoading ? (
                <span
                  className="coffee-spinner coffee-spinner--sm"
                  aria-hidden="true"
                />
              ) : (
                <Send size={14} aria-hidden="true" />
              )}
              <span>Ask</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
