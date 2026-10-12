import React, { useEffect, useRef } from 'react';
import { X, BookOpen, Sparkles } from 'lucide-react';
import { Citation } from '../../types';

export interface CitationModalProps {
  citation: Citation | null;
  filename: string;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({
  citation,
  filename,
  onClose,
}) => {
  const closeBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (citation) {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      closeBtnRef.current?.focus();
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [citation, onClose]);

  if (!citation) return null;

  const relevancePercentage = Math.round(citation.relevance_score * 100);

  return (
    <div
      className="dialog-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      role="presentation"
    >
      <div
        className="dialog-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="citation-title"
        style={{
          maxWidth: '560px',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: '1rem',
            marginBottom: '1.25rem',
          }}
        >
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.375rem',
              }}
            >
              <span className="badge badge--caramel">
                <BookOpen size={12} aria-hidden="true" />
                <span>Page {citation.page}</span>
              </span>
              <span className="badge badge--sand">
                <Sparkles size={11} aria-hidden="true" />
                <span>{relevancePercentage}% Match</span>
              </span>
            </div>
            <h3
              id="citation-title"
              style={{
                fontFamily: 'var(--font-serif)',
                fontSize: 'var(--text-lg)',
                color: 'var(--color-espresso)',
                margin: 0,
              }}
            >
              Source Grounding Excerpt
            </h3>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                color: 'var(--color-taupe)',
                marginTop: '2px',
                wordBreak: 'break-all',
              }}
            >
              {filename} • Page {citation.page}
            </div>
          </div>

          <button
            ref={closeBtnRef}
            type="button"
            onClick={onClose}
            aria-label="Close citation details"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-taupe)',
              cursor: 'pointer',
              padding: '0.375rem',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
            }}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {/* Verbatim Excerpt */}
        <div
          style={{
            backgroundColor: 'var(--color-oat-milk)',
            border: '1px solid var(--color-sand)',
            borderLeft: '4px solid var(--color-caramel)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
            maxHeight: '360px',
            overflowY: 'auto',
          }}
        >
          <div
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: 'var(--text-base)',
              color: 'var(--color-dark-roast)',
              lineHeight: 'var(--leading-relaxed)',
              whiteSpace: 'pre-wrap',
            }}
          >
            {citation.snippet}
          </div>
        </div>

        {/* Footer note */}
        <div
          style={{
            marginTop: '1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--color-taupe)',
            }}
          >
            Retrieved via semantic cosine vector similarity.
          </div>

          <button
            type="button"
            className="btn btn--secondary btn--sm"
            onClick={onClose}
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
