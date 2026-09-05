import React from 'react';

export interface SectionHeadingProps {
  eyebrow?: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  align?: 'left' | 'center';
  tone?: 'light' | 'dark';
  className?: string;
  rules?: boolean;
}

export const SectionHeading: React.FC<SectionHeadingProps> = ({
  eyebrow,
  title,
  description,
  align = 'left',
  tone = 'light',
  className = '',
  rules = false,
}) => {
  const alignCls = align === 'center' ? 'text-center items-center' : 'text-left items-start';
  const titleCls = tone === 'dark' ? 'text-white' : 'text-foreground';
  const descCls = tone === 'dark' ? 'text-white/70' : 'text-muted-foreground';
  const eyebrowText = tone === 'dark' ? 'text-accent-secondary' : 'text-accent';

  return (
    <div className={`flex flex-col gap-4 ${alignCls} ${className}`}>
      {eyebrow && rules ? (
        <div className="flex w-full items-center gap-4">
          <span aria-hidden="true" className="h-px flex-1 bg-[#e8e4df]" />
          <span className={`small-caps ${eyebrowText}`}>{eyebrow}</span>
          <span aria-hidden="true" className="h-px flex-1 bg-[#e8e4df]" />
        </div>
      ) : eyebrow ? (
        <span
          className={`inline-flex w-fit items-center rounded-md border border-[#e8e4df] bg-muted px-3 py-1 small-caps ${
            tone === 'dark' ? 'border-white/15 bg-white/5 text-accent-secondary' : 'bg-muted text-accent'
          }`}
        >
          {eyebrow}
        </span>
      ) : null}
      <h2 className={`font-display text-3xl font-semibold leading-tight tracking-normal sm:text-4xl ${titleCls}`}>
        {title}
      </h2>
      {description && (
        <p className={`max-w-2xl text-base leading-relaxed ${descCls}`}>{description}</p>
      )}
    </div>
  );
};
