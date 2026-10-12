import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      icon,
      children,
      className = '',
      disabled,
      type = 'button',
      ...props
    },
    ref
  ) => {
    const classes = [
      'btn',
      `btn--${variant}`,
      `btn--${size}`,
      className,
    ].filter(Boolean).join(' ');

    return (
      <button
        ref={ref}
        type={type}
        className={classes}
        disabled={disabled || loading}
        aria-busy={loading ? 'true' : undefined}
        {...props}
      >
        {loading ? (
          <span
            className="coffee-spinner coffee-spinner--sm"
            role="status"
            aria-label="Loading"
          />
        ) : (
          icon && <span className="btn__icon" aria-hidden="true">{icon}</span>
        )}
        <span>{children}</span>
      </button>
    );
  }
);

Button.displayName = 'Button';
