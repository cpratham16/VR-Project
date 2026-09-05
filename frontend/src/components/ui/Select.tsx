import React from 'react';
import { FieldWrapper } from './Field';
import { fieldBorderCls } from './fieldStyles';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options?: SelectOption[];
  placeholder?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className = '', label, error, helperText, options = [], placeholder, id, required, children, ...props }, ref) => {
    const selectId = id || (label ? `fld-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <FieldWrapper label={label} error={error} helperText={helperText} htmlFor={selectId} required={required}>
        <div className="relative">
          <select
            id={selectId}
            ref={ref}
            required={required}
            aria-invalid={!!error || undefined}
            className={`h-12 w-full cursor-pointer appearance-none rounded-md border bg-transparent px-3.5 pr-10 text-sm text-foreground shadow-none transition-all duration-150 ease-out hover:border-[#d6cfc7] focus:outline-none focus:ring-2 disabled:bg-muted ${fieldBorderCls(
              !!error
            )} ${className}`}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.length > 0
              ? options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))
              : children}
          </select>
          <svg
            className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      </FieldWrapper>
    );
  }
);
Select.displayName = 'Select';
