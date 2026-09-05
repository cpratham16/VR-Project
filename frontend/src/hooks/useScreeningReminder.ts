import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../api/client';

export type ScreeningType = 'PHQ-9' | 'GAD-7';

const CHECKED_CACHE_KEY = 'screening_reminder_checked';
const SKIP_PREFIX = 'screening_reminder_skip_';

interface ReminderStatus {
  should_remind: boolean;
  reason: string;
  next_due_at?: string | null;
  interval_days?: number;
}

type ReminderResponse = Record<ScreeningType, ReminderStatus>;

const dayKey = () => new Date().toISOString().slice(0, 10);

const skipKey = (type: ScreeningType) => `${SKIP_PREFIX}${type}_${dayKey()}`;

export function isSkippedToday(type: ScreeningType): boolean {
  return localStorage.getItem(skipKey(type)) === '1';
}

/**
 * Per-instrument daily screening reminder.
 *
 * - Fetches /patient/screening/reminder at most once per calendar day
 *   (result cached in sessionStorage; re-fetch happens on a new day).
 * - "Skip today" persists to localStorage so the reminder stays hidden for
 *   that instrument until midnight.
 */
export function useScreeningReminder(enabled = true) {
  const [dueTypes, setDueTypes] = useState<ScreeningType[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    const key = `${CHECKED_CACHE_KEY}_${dayKey()}`;
    const cached = sessionStorage.getItem(key);

    const applyResponse = (data: ReminderResponse) => {
      if (cancelled) return;
      const due = (Object.keys(data) as ScreeningType[]).filter(
        (type) => data[type].should_remind && !isSkippedToday(type)
      );
      setDueTypes(due);
      setLoaded(true);
      if (!cancelled) sessionStorage.setItem(key, JSON.stringify(data));
    };

    if (cached) {
      try {
        applyResponse(JSON.parse(cached) as ReminderResponse);
        return;
      } catch {
        sessionStorage.removeItem(key);
      }
    }

    apiClient
      .get<ReminderResponse>('/patient/screening/reminder')
      .then((res) => applyResponse(res.data))
      .catch(() => {
        if (!cancelled) {
          setDueTypes([]);
          setLoaded(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [enabled]);

  const skipToday = useCallback((type: ScreeningType) => {
    localStorage.setItem(skipKey(type), '1');
    setDueTypes((prev) => prev.filter((t) => t !== type));
  }, []);

  const takeLater = useCallback(() => {
    setDueTypes([]);
  }, []);

  return { dueTypes, loaded, skipToday, takeLater, isSkippedToday };
}