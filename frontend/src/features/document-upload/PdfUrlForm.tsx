import React, { useState } from 'react';
import { Globe, AlertCircle } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export interface PdfUrlFormProps {
  onUrlSubmit: (url: string) => void;
  isLoading: boolean;
  error?: string | null;
}

export const PdfUrlForm: React.FC<PdfUrlFormProps> = ({
  onUrlSubmit,
  isLoading,
  error: externalError,
}) => {
  const [url, setUrl] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const validateUrl = (value: string): boolean => {
    setLocalError(null);
    const trimmed = value.trim();

    if (!trimmed) {
      setLocalError('Please enter a document URL.');
      return false;
    }

    try {
      const parsed = new URL(trimmed);
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        setLocalError('Only http:// and https:// URLs are supported.');
        return false;
      }
    } catch {
      setLocalError('Please enter a valid, well-formed web address.');
      return false;
    }

    return true;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateUrl(url) && !isLoading) {
      onUrlSubmit(url.trim());
    }
  };

  const errorToShow = localError || externalError;

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        backgroundColor: 'var(--color-paper)',
        border: '1px solid var(--color-sand-border)',
        borderRadius: 'var(--radius-xl)',
        padding: '2rem 1.5rem',
        boxShadow: 'var(--shadow-subtle)',
      }}
    >
      <div
        style={{
          width: '3.5rem',
          height: '3.5rem',
          margin: '0 auto 1.25rem',
          borderRadius: 'var(--radius-full)',
          backgroundColor: 'var(--color-oat-milk)',
          border: '1px solid var(--color-sand)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-roasted-cocoa)',
        }}
      >
        <Globe size={26} aria-hidden="true" />
      </div>

      <h3
        style={{
          fontFamily: 'var(--font-serif)',
          fontSize: 'var(--text-lg)',
          color: 'var(--color-espresso)',
          marginBottom: '0.375rem',
          textAlign: 'center',
        }}
      >
        Fetch from a public web link
      </h3>

      <p
        style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--color-taupe)',
          marginBottom: '1.5rem',
          textAlign: 'center',
          maxWidth: '420px',
          margin: '0 auto 1.5rem',
        }}
      >
        Provide a direct link to an accessible PDF document. The backend securely
        verifies and indexes its pages into your session.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <label
          htmlFor="pdf-url-input"
          style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--color-coffee-bean)',
          }}
        >
          Document Web Address
        </label>
        <input
          id="pdf-url-input"
          type="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            if (localError) setLocalError(null);
          }}
          placeholder="https://example.com/research-paper.pdf"
          disabled={isLoading}
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: 'var(--text-base)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            border: `1px solid ${
              errorToShow ? 'var(--color-burnt-terracotta)' : 'var(--color-sand-border)'
            }`,
            backgroundColor: 'var(--color-paper)',
            color: 'var(--color-espresso)',
            width: '100%',
            outline: 'none',
          }}
        />

        {errorToShow && (
          <div
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.625rem 0.875rem',
              backgroundColor: 'var(--color-burnt-terracotta-bg)',
              border: '1px solid var(--color-burnt-terracotta-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-burnt-terracotta)',
              fontSize: 'var(--text-sm)',
            }}
          >
            <AlertCircle size={16} aria-hidden="true" style={{ flexShrink: 0 }} />
            <span>{errorToShow}</span>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.75rem' }}>
          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={isLoading}
            disabled={!url.trim() || isLoading}
          >
            Fetch & Ingest
          </Button>
        </div>
      </div>
    </form>
  );
};
