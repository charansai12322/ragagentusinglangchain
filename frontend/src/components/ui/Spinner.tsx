import React from 'react';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  label = 'Processing...',
  className = '',
}) => {
  const sizeClass = size === 'sm' ? 'coffee-spinner--sm' : size === 'lg' ? 'coffee-spinner--lg' : '';

  return (
    <div
      role="status"
      aria-label={label}
      style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
      className={className}
    >
      <span className={`coffee-spinner ${sizeClass}`} aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );
};
