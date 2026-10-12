import React, { useEffect, useRef } from 'react';
import { Button } from './Button';

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'primary';
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  loading = false,
  onConfirm,
  onCancel,
}) => {
  const confirmBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && !loading) {
          onCancel();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      confirmBtnRef.current?.focus();
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, loading, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="dialog-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) {
          onCancel();
        }
      }}
      role="presentation"
    >
      <div
        className="dialog-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        aria-describedby="dialog-desc"
      >
        <h3
          id="dialog-title"
          style={{
            fontFamily: 'var(--font-serif)',
            fontSize: 'var(--text-lg)',
            color: 'var(--color-espresso)',
            marginBottom: '0.75rem',
          }}
        >
          {title}
        </h3>
        <p
          id="dialog-desc"
          style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--color-roasted-cocoa)',
            lineHeight: 'var(--leading-relaxed)',
            marginBottom: '1.5rem',
          }}
        >
          {message}
        </p>
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.75rem',
          }}
        >
          <Button
            variant="secondary"
            size="md"
            onClick={onCancel}
            disabled={loading}
          >
            {cancelLabel}
          </Button>
          <Button
            ref={confirmBtnRef}
            variant={variant}
            size="md"
            loading={loading}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
};
