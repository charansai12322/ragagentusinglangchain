import React from 'react';
import { BookOpen } from 'lucide-react';
import { Citation } from '../../types';

export interface CitationPillProps {
  citation: Citation;
  onClick: () => void;
}

export const CitationPill: React.FC<CitationPillProps> = ({
  citation,
  onClick,
}) => {
  const matchPercent = Math.round(citation.relevance_score * 100);

  return (
    <button
      type="button"
      onClick={onClick}
      aria-haspopup="dialog"
      aria-label={`View excerpt from Page ${citation.page} (${matchPercent}% relevance)`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.25rem 0.625rem',
        borderRadius: 'var(--radius-full)',
        backgroundColor: 'var(--color-caramel-subtle)',
        border: '1px solid var(--color-caramel-border)',
        color: 'var(--color-caramel-hover)',
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--text-xs)',
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'all var(--transition-fast)',
      }}
      className="citation-pill"
      title={`Click to view Page ${citation.page} source excerpt (${matchPercent}% match)`}
    >
      <BookOpen size={12} aria-hidden="true" />
      <span>Page {citation.page}</span>
    </button>
  );
};
