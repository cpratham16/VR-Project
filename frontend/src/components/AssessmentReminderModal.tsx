import { useEffect, useRef } from 'react';
import { Button } from './ui/Button';
import type { ScreeningType } from '../hooks/useScreeningReminder';

interface AssessmentReminderModalProps {
  dueTypes: ScreeningType[];
  onTakeNow: (type?: ScreeningType) => void;
  onTakeLater: () => void;
  onSkip: (type: ScreeningType) => void;
}

const TYPE_LABELS: Record<ScreeningType, string> = {
  'PHQ-9': 'PHQ-9 (depression)',
  'GAD-7': 'GAD-7 (anxiety)',
};

export default function AssessmentReminderModal({
  dueTypes,
  onTakeNow,
  onTakeLater,
  onSkip,
}: AssessmentReminderModalProps) {
  const primaryButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (dueTypes.length === 0) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onTakeLater();
    };
    document.addEventListener('keydown', onKeyDown);
    primaryButtonRef.current?.focus();
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [dueTypes, onTakeLater]);

  if (dueTypes.length === 0) return null;

  const primary = dueTypes[0];
  const secondary = dueTypes[1];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="assessment-reminder-title"
    >
      <div className="w-full max-w-md rounded-2xl border border-[#e8e4df] bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center gap-3">
          <span
            aria-hidden="true"
            className="flex h-11 w-11 items-center justify-center rounded-md bg-muted text-2xl"
          >
            📝
          </span>
          <div>
            <h2 id="assessment-reminder-title" className="font-display text-xl font-bold text-foreground">
              Your check-in is due
            </h2>
            <p className="text-sm text-muted-foreground">
              A quick 2-minute screening helps us support you better.
            </p>
          </div>
        </div>

        <p className="mb-5 text-sm leading-relaxed text-muted-foreground">
          You haven&apos;t completed{' '}
          {dueTypes.length === 1
            ? TYPE_LABELS[primary]
            : `${TYPE_LABELS[primary]} or ${TYPE_LABELS[secondary]}`}{' '}
          recently. Tracking your mood and stress over time lets your counselor see trends between sessions.
        </p>

        <div className="space-y-2.5">
          <Button ref={primaryButtonRef} variant="primary" size="lg" className="w-full" onClick={() => onTakeNow(primary)}>
            Take {dueTypes.length === 2 ? 'a' : TYPE_LABELS[primary]}
          </Button>
          {secondary && (
            <Button variant="outline" size="lg" className="w-full" onClick={() => onTakeNow(secondary)}>
              Take {TYPE_LABELS[secondary]} instead
            </Button>
          )}
          <div className="flex items-center justify-between pt-2">
            <Button variant="ghost" size="sm" onClick={onTakeLater}>
              Take later
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onSkip(primary)}>
              Skip today
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}