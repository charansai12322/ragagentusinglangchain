import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, X, AlertCircle } from 'lucide-react';
import { BRANDING } from '../../config/branding';
import { Button } from '../../components/ui/Button';

export interface PdfDropzoneProps {
  onFileSubmit: (file: File) => void;
  isLoading: boolean;
  error?: string | null;
}

export const PdfDropzone: React.FC<PdfDropzoneProps> = ({
  onFileSubmit,
  isLoading,
  error: externalError,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const validateAndSelectFile = (file: File) => {
    setLocalError(null);

    // Validate type / extension
    const isPdf =
      file.type === 'application/pdf' ||
      file.name.toLowerCase().endsWith('.pdf');

    if (!isPdf) {
      setLocalError('Please select a valid PDF document (.pdf extension).');
      return;
    }

    // Validate empty file
    if (file.size === 0) {
      setLocalError('The selected PDF file is empty (0 bytes).');
      return;
    }

    // Validate max size
    if (file.size > BRANDING.uploadLimitBytes) {
      setLocalError(
        `File size exceeds the ${BRANDING.uploadLimitMb}MB limit (actual: ${formatFileSize(file.size)}).`
      );
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isLoading) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (isLoading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setLocalError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile && !isLoading) {
      onFileSubmit(selectedFile);
    }
  };

  const errorToShow = localError || externalError;

  return (
    <form onSubmit={handleSubmit} style={{ width: '100%' }}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        accept=".pdf,application/pdf"
        style={{ display: 'none' }}
        id="pdf-file-input"
        disabled={isLoading}
      />

      {!selectedFile ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          tabIndex={0}
          role="button"
          aria-label="Upload PDF by drag and drop or clicking to browse"
          style={{
            border: `2px dashed ${
              isDragOver ? 'var(--color-caramel)' : 'var(--color-sand-border)'
            }`,
            backgroundColor: isDragOver
              ? 'var(--color-caramel-subtle)'
              : 'var(--color-paper)',
            borderRadius: 'var(--radius-xl)',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            transition: 'all var(--transition-base)',
            boxShadow: isDragOver ? 'var(--shadow-paper-elevated)' : 'var(--shadow-subtle)',
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
            <UploadCloud size={26} aria-hidden="true" />
          </div>

          <h3
            style={{
              fontFamily: 'var(--font-serif)',
              fontSize: 'var(--text-lg)',
              color: 'var(--color-espresso)',
              marginBottom: '0.375rem',
            }}
          >
            Choose a PDF or drag it here
          </h3>

          <p
            style={{
              fontSize: 'var(--text-sm)',
              color: 'var(--color-taupe)',
              marginBottom: '1.25rem',
              maxWidth: '380px',
              margin: '0 auto 1.25rem',
            }}
          >
            Text-based research papers, reports, or books up to{' '}
            {BRANDING.uploadLimitMb}MB (scanned PDFs without extractable text are
            not supported).
          </p>

          <Button
            variant="secondary"
            size="md"
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
            disabled={isLoading}
          >
            Browse files
          </Button>
        </div>
      ) : (
        /* Selected file card */
        <div
          style={{
            backgroundColor: 'var(--color-paper)',
            border: '1px solid var(--color-sand-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem',
            boxShadow: 'var(--shadow-paper)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.875rem',
                minWidth: 0,
              }}
            >
              <div
                style={{
                  width: '2.75rem',
                  height: '2.75rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-oat-milk)',
                  border: '1px solid var(--color-sand)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--color-caramel-hover)',
                  flexShrink: 0,
                }}
              >
                <FileText size={22} aria-hidden="true" />
              </div>

              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontWeight: 600,
                    fontSize: 'var(--text-base)',
                    color: 'var(--color-espresso)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={selectedFile.name}
                >
                  {selectedFile.name}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 'var(--text-xs)',
                    color: 'var(--color-taupe)',
                    marginTop: '2px',
                  }}
                >
                  {formatFileSize(selectedFile.size)} • PDF Document
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleRemoveFile}
              disabled={isLoading}
              aria-label="Remove selected file"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-taupe)',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                padding: '0.5rem',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
              }}
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>

          <div
            style={{
              marginTop: '1.25rem',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.75rem',
            }}
          >
            <Button
              variant="secondary"
              size="md"
              type="button"
              onClick={handleRemoveFile}
              disabled={isLoading}
            >
              Choose different file
            </Button>
            <Button
              variant="primary"
              size="md"
              type="submit"
              loading={isLoading}
            >
              Bring into Room
            </Button>
          </div>
        </div>
      )}

      {errorToShow && (
        <div
          role="alert"
          style={{
            marginTop: '0.875rem',
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
    </form>
  );
};
