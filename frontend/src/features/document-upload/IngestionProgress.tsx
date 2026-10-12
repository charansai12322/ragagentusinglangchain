import React from 'react';
import { FileText } from 'lucide-react';
import { Spinner } from '../../components/ui/Spinner';

export interface IngestionProgressProps {
  sourceName: string;
}

export const IngestionProgress: React.FC<IngestionProgressProps> = ({
  sourceName,
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        backgroundColor: 'var(--color-paper)',
        border: '1px solid var(--color-sand)',
        borderRadius: 'var(--radius-xl)',
        padding: '3rem 2rem',
        textAlign: 'center',
        boxShadow: 'var(--shadow-paper)',
        maxWidth: '520px',
        margin: '0 auto',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          marginBottom: '1.5rem',
        }}
      >
        <div
          style={{
            position: 'relative',
            width: '4rem',
            height: '4rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--color-oat-milk)',
          }}
        >
          <FileText
            size={24}
            style={{ color: 'var(--color-roasted-cocoa)' }}
            aria-hidden="true"
          />
          <div
            style={{
              position: 'absolute',
              inset: '-4px',
            }}
          >
            <Spinner size="lg" label="Processing document" />
          </div>
        </div>
      </div>

      <h3
        style={{
          fontFamily: 'var(--font-serif)',
          fontSize: 'var(--text-xl)',
          color: 'var(--color-espresso)',
          marginBottom: '0.5rem',
        }}
      >
        Preparing your document…
      </h3>

      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: 'var(--color-caramel-hover)',
          backgroundColor: 'var(--color-caramel-subtle)',
          padding: '0.25rem 0.75rem',
          borderRadius: 'var(--radius-full)',
          display: 'inline-block',
          marginBottom: '1rem',
          maxWidth: '360px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
        title={sourceName}
      >
        {sourceName}
      </div>

      <p
        style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--color-taupe)',
          lineHeight: 'var(--leading-relaxed)',
          maxWidth: '400px',
          margin: '0 auto',
        }}
      >
        Extracting page text, generating semantic chunks, and building FastEmbed
        vectors for fast, grounded question answering.
      </p>
    </div>
  );
};
