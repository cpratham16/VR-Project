import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'dark';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className = '',
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'group relative inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium tracking-[0.02em] transition-all duration-200 ease-out touch-manipulation focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer min-h-[44px]';

    const variantStyles = {
      primary:
        'bg-accent text-white shadow-sm hover:bg-accent-secondary hover:shadow-md motion-safe:hover:-translate-y-0.5 motion-safe:active:translate-y-0',
      secondary:
        'bg-[#1a1a1a] text-white shadow-sm hover:bg-black/80 focus-visible:ring-[#1a1a1a]',
      outline:
        'border border-[#1a1a1a] bg-transparent text-[#1a1a1a] hover:bg-muted hover:border-accent hover:text-accent',
      ghost:
        'bg-transparent text-muted-foreground hover:text-foreground hover:underline decoration-accent underline-offset-4',
      danger:
        'border border-red-800 bg-transparent text-red-800 hover:bg-red-50 focus-visible:ring-red-700',
      dark: variant_secondaryDark(),
    };

    function variant_secondaryDark() {
      return 'bg-white/10 text-white border border-white/30 hover:bg-white/20';
    }

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-xs gap-1.5 min-h-0',
      md: 'px-5 py-2.5 text-sm',
      lg: 'px-7 py-3 text-base',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      >
        {isLoading ? (
          <svg
            className="h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : (
          leftIcon && <span className="inline-flex shrink-0">{leftIcon}</span>
        )}
        <span>{children}</span>
        {!isLoading && rightIcon && (
          <span className="inline-flex shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);
Button.displayName = 'Button';
