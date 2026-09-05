import React from 'react';

export interface StepItem {
  id: number;
  label: string;
  description?: string;
}

export interface StepperProps {
  steps: StepItem[];
  currentStep: number;
  onStepClick?: (stepId: number) => void;
  className?: string;
}

export const Stepper: React.FC<StepperProps> = ({ steps, currentStep, onStepClick, className = '' }) => {
  return (
    <nav aria-label="Progress" className={`w-full ${className}`}>
      <ol className="flex w-full items-start">
        {steps.map((step, idx) => {
          const isCompleted = currentStep > step.id;
          const isCurrent = currentStep === step.id;
          const isLast = idx === steps.length - 1;
          const isClickable = !!onStepClick && isCompleted;

          return (
            <li
              key={step.id}
              className={`relative flex flex-col items-center ${isLast ? '' : 'flex-1'}`}
              aria-current={isCurrent ? 'step' : undefined}
            >
              {!isLast && (
                <div
                  aria-hidden="true"
                  className="absolute left-[calc(50%+26px)] right-[calc(-50%+26px)] top-[17px] h-px bg-[#e8e4df]"
                >
                  <div
                    className={`h-full transition-all duration-500 ${isCompleted ? 'w-full bg-accent' : 'w-0'}`}
                  />
                </div>
              )}

              <button
                type="button"
                disabled={!isClickable}
                onClick={() => isClickable && onStepClick?.(step.id)}
                aria-label={`Step ${step.id}: ${step.label}${isCompleted ? ' (completed)' : ''}`}
                className={`relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-md border font-display text-sm transition-all duration-200 ${
                  isCompleted
                    ? 'border-accent bg-accent text-white'
                    : isCurrent
                      ? 'border-accent bg-white text-accent ring-2 ring-accent/20'
                      : 'border-[#e8e4df] bg-muted text-muted-foreground'
                } ${isClickable ? 'cursor-pointer hover:border-accent hover:text-accent' : 'cursor-default'}`}
              >
                {isCompleted ? (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  step.id
                )}
              </button>

              <span
                className={`mt-2 hidden text-center font-mono text-[10px] font-medium uppercase tracking-[0.12em] sm:block ${
                  isCurrent ? 'text-accent' : isCompleted ? 'text-foreground' : 'text-muted-foreground'
                }`}
              >
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
