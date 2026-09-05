import React from 'react';

export interface FieldWrapperProps {
  label?: string;
  error?: string;
  helperText?: string;
  htmlFor?: string;
  required?: boolean;
  children: React.ReactNode;
}

export const FieldWrapper: React.FC<FieldWrapperProps> = ({
  label,
  error,
  helperText,
  htmlFor,
  required,
  children,
}) => (
  <div className="w-full">
    {label && (
      <label
        htmlFor={htmlFor}
        className="mb-1.5 block font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground"
      >
        {label}
        {required && (
          <span className="ml-1 text-accent" aria-hidden="true">
            *
          </span>
        )}
      </label>
    )}
    {children}
    {error ? (
      <p className="mt-1.5 flex items-center gap-1 text-xs font-medium text-red-700" role="alert">
        <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path
            fillRule="evenodd"
            d="M18 10A8 8 0 11 2 10a8 8 0 0116 0zm-8-4a1 1 0 00-1 1v3a1 1 0 002 0V7a1 1 0 00-1-1zm0 8a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        {error}
      </p>
    ) : helperText ? (
      <p className="mt-1.5 text-xs text-muted-foreground">{helperText}</p>
    ) : null}
  </div>
);
