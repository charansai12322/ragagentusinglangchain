import React from 'react';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  ariaLabel: string;
  size?: 'sm' | 'md';
  variant?: 'ghost' | 'secondary' | 'danger';
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  ariaLabel,
  size = 'md',
  variant = 'ghost',
  className = '',
  disabled,
  type = 'button',
  ...props
}) => {
  const classes = [
    'icon-btn',
    size === 'sm' ? 'icon-btn--sm' : '',
    variant === 'danger' ? 'icon-btn--danger' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <button
      type={type}
      aria-label={ariaLabel}
      title={ariaLabel}
      className={classes}
      disabled={disabled}
      {...props}
    >
      <span aria-hidden="true">{icon}</span>
    </button>
  );
};
