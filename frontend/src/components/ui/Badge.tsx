import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'dark';
  size?: 'sm' | 'md';
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  className = '',
  variant = 'neutral',
  size = 'md',
  dot = false,
  children,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center gap-1.5 rounded-md border font-mono uppercase tracking-[0.12em] whitespace-nowrap';

  const variantStyles = {
    neutral: 'bg-muted text-muted-foreground border-[#e8e4df]',
    success: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    warning: 'bg-amber-50 text-amber-800 border-amber-200',
    danger: 'bg-red-50 text-red-800 border-red-200',
    info: 'bg-sky-50 text-sky-800 border-sky-200',
    primary: 'bg-accent-muted text-accent border-accent/30',
    dark: 'bg-white/10 text-white border-white/20',
  };

  const dotStyles = {
    neutral: 'bg-slate-400',
    success: 'bg-emerald-600',
    warning: 'bg-amber-500',
    danger: 'bg-red-600',
    info: 'bg-sky-600',
    primary: 'bg-accent animate-pulse-soft',
    dark: 'bg-white',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-[11px] font-medium',
  };

  return (
    <span className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`} {...props}>
      {dot && <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${dotStyles[variant]}`} />}
      {children}
    </span>
  );
};
