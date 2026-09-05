import React from 'react';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label: React.ReactNode;
  error?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className = '', label, error, ...props }, ref) => {
    const checkboxId = React.useId();

    return (
      <div className="w-full">
        <div className="flex items-start gap-3">
          <input
            id={checkboxId}
            ref={ref}
            type="checkbox"
            aria-invalid={!!error || undefined}
            className={`mt-1 h-4 w-4 shrink-0 cursor-pointer rounded border-[#d6cfc7] accent-[#b8860b] transition focus:outline-none focus:ring-2 focus:ring-accent/20 ${className}`}
            {...props}
          />
          <label htmlFor={checkboxId} className="cursor-pointer text-sm leading-relaxed text-slate-700">
            {label}
          </label>
        </div>
        {error && (
          <p className="mt-1.5 pl-7 text-xs font-medium text-red-700" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Checkbox.displayName = 'Checkbox';
