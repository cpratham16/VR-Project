import React from 'react';
import { FieldWrapper } from './Field';
import { fieldBorderCls } from './fieldStyles';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', label, error, helperText, id, required, rows = 4, ...props }, ref) => {
    const textareaId = id || (label ? `fld-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <FieldWrapper label={label} error={error} helperText={helperText} htmlFor={textareaId} required={required}>
        <textarea
          id={textareaId}
          ref={ref}
          rows={rows}
          required={required}
          aria-invalid={!!error || undefined}
          className={`w-full resize-y rounded-md border bg-transparent px-3.5 py-3 text-sm text-foreground shadow-none transition-all duration-150 ease-out placeholder:text-muted-foreground/60 hover:border-[#d6cfc7] focus:outline-none focus:ring-2 ${fieldBorderCls(
            !!error
          )} ${className}`}
          {...props}
        />
      </FieldWrapper>
    );
  }
);
Textarea.displayName = 'Textarea';
