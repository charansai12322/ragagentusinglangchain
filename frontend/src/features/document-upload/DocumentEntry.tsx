import React, { useState } from 'react';
import { Upload, Globe } from 'lucide-react';
import { BRANDING } from '../../config/branding';
import { PdfDropzone } from './PdfDropzone';
import { PdfUrlForm } from './PdfUrlForm';
import { IngestionProgress } from './IngestionProgress';
import { InlineNotice } from '../../components/ui/InlineNotice';
import { ApiErrorResponse } from '../../services/api';
import { formatApiError } from '../../lib/errors';

export interface DocumentEntryProps {
  onFileUpload: (file: File) => void;
  onUrlUpload: (url: string) => void;
  isLoading: boolean;
  activeSource: string | null;
  error: ApiErrorResponse | null;
  onClearError: () => void;
}

export const DocumentEntry: React.FC<DocumentEntryProps> = ({
  onFileUpload,
  onUrlUpload,
  isLoading,
  activeSource,
  error,
  onClearError,
}) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'url'>('upload');

  const formattedError = error ? formatApiError(error) : null;

  return (
    <div
      className="workspace-container"
      style={{
        paddingTop: '3.5rem',
        paddingBottom: '3.5rem',
        maxWidth: '680px',
      }}
    >
      {/* Intro Header */}
      <div style={{ textAlign: 'center', marginBottom: '2.25rem' }}>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--color-caramel-hover)',
            marginBottom: '0.625rem',
          }}
        >
          {BRANDING.productName}
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-serif)',
            fontSize: 'var(--text-3xl)',
            fontWeight: 600,
            color: 'var(--color-espresso)',
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            marginBottom: '0.875rem',
          }}
        >
          Bring a document into the room.
        </h1>
        <p
          style={{
            fontSize: 'var(--text-base)',
            color: 'var(--color-roasted-cocoa)',
            maxWidth: '520px',
            margin: '0 auto',
            lineHeight: var_to_string('--leading-relaxed'),
          }}
        >
          {BRANDING.tagline}
        </p>
      </div>

      {/* Global Ingestion Error Notice */}
      {formattedError && (
        <div style={{ marginBottom: '1.5rem' }}>
          <InlineNotice
            variant="error"
            title={formattedError.title}
            message={`${formattedError.detail} ${formattedError.recovery ? `Advice: ${formattedError.recovery}` : ''}`}
            onDismiss={onClearError}
          />
        </div>
      )}

      {/* Conditional Rendering: Progress or Input Tabs */}
      {isLoading ? (
        <IngestionProgress sourceName={activeSource || 'Document'} />
      ) : (
        <div>
          {/* Tabs */}
          <div
            role="tablist"
            aria-label="Document entry methods"
            style={{
              display: 'flex',
              gap: '0.5rem',
              backgroundColor: 'var(--color-sand-light)',
              padding: '0.25rem',
              borderRadius: 'var(--radius-lg)',
              marginBottom: '1.5rem',
              width: 'fit-content',
              margin: '0 auto 1.5rem',
            }}
          >
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'upload'}
              aria-controls="upload-tab-panel"
              id="tab-upload"
              onClick={() => {
                setActiveTab('upload');
                onClearError();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--text-sm)',
                fontWeight: 500,
                border: 'none',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
                backgroundColor:
                  activeTab === 'upload' ? 'var(--color-paper)' : 'transparent',
                color:
                  activeTab === 'upload'
                    ? 'var(--color-espresso)'
                    : 'var(--color-roasted-cocoa)',
                boxShadow:
                  activeTab === 'upload' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
              }}
            >
              <Upload size={15} aria-hidden="true" />
              <span>Upload PDF</span>
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'url'}
              aria-controls="url-tab-panel"
              id="tab-url"
              onClick={() => {
                setActiveTab('url');
                onClearError();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--text-sm)',
                fontWeight: 500,
                border: 'none',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
                backgroundColor:
                  activeTab === 'url' ? 'var(--color-paper)' : 'transparent',
                color:
                  activeTab === 'url'
                    ? 'var(--color-espresso)'
                    : 'var(--color-roasted-cocoa)',
                boxShadow:
                  activeTab === 'url' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
              }}
            >
              <Globe size={15} aria-hidden="true" />
              <span>Document URL</span>
            </button>
          </div>

          {/* Tab Panels */}
          <div
            id="upload-tab-panel"
            role="tabpanel"
            aria-labelledby="tab-upload"
            hidden={activeTab !== 'upload'}
          >
            {activeTab === 'upload' && (
              <PdfDropzone
                onFileSubmit={onFileUpload}
                isLoading={isLoading}
              />
            )}
          </div>

          <div
            id="url-tab-panel"
            role="tabpanel"
            aria-labelledby="tab-url"
            hidden={activeTab !== 'url'}
          >
            {activeTab === 'url' && (
              <PdfUrlForm
                onUrlSubmit={onUrlUpload}
                isLoading={isLoading}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

function var_to_string(varName: string): string {
  return `var(${varName})`;
}
