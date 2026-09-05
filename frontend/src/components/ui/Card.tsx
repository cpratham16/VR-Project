import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'elevated' | 'outline' | 'dark';
  hoverEffect?: boolean;
  accentTop?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = '', variant = 'default', hoverEffect = false, accentTop = false, children, ...props }, ref) => {
    const baseStyles = 'rounded-lg transition-all duration-200 ease-out overflow-hidden';

    const variantStyles: Record<string, string> = {
      default: 'bg-white border border-[#e8e4df] shadow-sm',
      glass: 'card-editorial',
      elevated: 'bg-white border border-[#e8e4df] shadow-[0_4px_12px_rgba(26,26,26,0.06)]',
      outline: 'bg-transparent border border-[#e8e4df]',
      dark: 'bg-[#1a1a1a] border border-[#1a1a1a] text-white',
    };

    const hoverStyles = hoverEffect
      ? 'hover:bg-[#fafaf8]/60 hover:border-[#d6cfc7] hover:shadow-[0_4px_12px_rgba(26,26,26,0.06)]'
      : '';

    return (
      <div
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${hoverStyles} ${className}`}
        {...props}
      >
        {accentTop && <div aria-hidden="true" className="h-0.5 w-full bg-accent" />}
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <div className={`p-8 pb-3 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <h3 className={`font-display text-xl font-semibold leading-snug tracking-normal ${className || ''}`} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <p className={`mt-1.5 text-sm leading-relaxed text-muted-foreground ${className}`} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <div className={`p-8 pt-3 ${className}`} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <div className={`flex items-center p-8 pt-0 ${className}`} {...props}>
    {children}
  </div>
);
