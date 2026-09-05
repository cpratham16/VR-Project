import React from 'react';
import { FieldWrapper } from './Field';
import { fieldBorderCls } from './fieldStyles';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', label, error, helperText, leftIcon, id, required, ...props }, ref) => {
    const inputId = id || (label ? `fld-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <FieldWrapper label={label} error={error} helperText={helperText} htmlFor={inputId} required={required}>
        <div className="relative">
          {leftIcon && (
            <div
              className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted-foreground"
              aria-hidden="true"
            >
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            required={required}
            aria-invalid={!!error || undefined}
            className={`h-12 w-full rounded-md border bg-transparent px-3.5 text-sm text-foreground shadow-none transition-all duration-150 ease-out placeholder:text-muted-foreground/60 hover:border-[#d6cfc7] focus:outline-none focus:ring-2 disabled:bg-muted ${
              leftIcon ? 'pl-10' : ''
            } ${fieldBorderCls(!!error)} ${className}`}
            {...props}
          />
        </div>
      </FieldWrapper>
    );
  }
);
Input.displayName = 'Input';
