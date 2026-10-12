import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';

export interface InlineNoticeProps {
  variant: 'error' | 'warning' | 'info' | 'success';
  title?: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  onDismiss?: () => void;
  className?: string;
}

export const InlineNotice: React.FC<InlineNoticeProps> = ({
  variant,
  title,
  message,
  action,
  onDismiss,
  className = '',
}) => {
  const isAlert = variant === 'error' || variant === 'warning';

  const iconMap = {
    error: <AlertCircle size={18} aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />,
    warning: <AlertTriangle size={18} aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />,
    info: <Info size={18} aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />,
    success: <CheckCircle2 size={18} aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />,
  };

  return (
    <div
      role={isAlert ? 'alert' : 'status'}
      className={`notice notice--${variant} ${className}`}
    >
      {iconMap[variant]}
      <div className="notice__content">
        {title && <div className="notice__title">{title}</div>}
        <div style={{ wordBreak: 'break-word' }}>{message}</div>
        {action && (
          <div style={{ marginTop: '0.5rem' }}>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={action.onClick}
              style={{ fontSize: 'var(--text-xs)', padding: '0.25rem 0.625rem' }}
            >
              {action.label}
            </button>
          </div>
        )}
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss notice"
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '2px',
            color: 'inherit',
            opacity: 0.7,
            display: 'flex',
          }}
        >
          <X size={15} aria-hidden="true" />
        </button>
      )}
    </div>
  );
};
