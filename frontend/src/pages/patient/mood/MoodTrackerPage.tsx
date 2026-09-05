import { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Select } from '../../../components/ui/Select';
import { Textarea } from '../../../components/ui/Textarea';

interface MoodEntry {
  id: string;
  mood_score: number;
  tags: string[];
  journal_text?: string;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
}

const MOOD_SCALES = [
  { score: 1, emoji: '😞', label: 'Severe Distress', active: 'bg-red-600 text-white border-transparent' },
  { score: 2, emoji: '😟', label: 'Low / Stressed', active: 'bg-orange-500 text-white border-transparent' },
  { score: 3, emoji: '😐', label: 'Neutral / Okay', active: 'bg-amber-400 text-gray-900 border-transparent' },
  { score: 4, emoji: '🙂', label: 'Good / Positive', active: 'bg-emerald-500 text-white border-transparent' },
  { score: 5, emoji: '😊', label: 'Excellent / Calm', active: 'bg-accent text-white border-transparent' }
];

const INACTIVE_MOOD_CLS =
  'bg-white text-muted-foreground border-[#e8e4df] hover:bg-muted hover:border-[#d6cfc7]';

const PREDEFINED_TAGS = [
  '📚 Academic / Exams',
  '😴 Sleep / Fatigue',
  '👥 Social / Relationships',
  '🏃 Physical Health',
  '🏠 Family / Personal',
  '⚡ Anxiety / Overwhelmed',
  '💼 Career / Future'
];

const TIME_RANGE_OPTIONS = [
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' }
];

export default function MoodTrackerPage() {
  const [entries, setEntries] = useState<MoodEntry[]>([]);
  const [selectedScore, setSelectedScore] = useState<number>(3);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [journalText, setJournalText] = useState<string>('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [timeRange, setTimeRange] = useState<number>(30);

  useEffect(() => {
    fetchEntries();
  }, [timeRange]);

  const fetchEntries = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.get(`/patient/mood/history?days=${timeRange}`);
      setEntries(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch mood logs.');
    } finally {
      setLoading(false);
    }
  };

  const handleTagToggle = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter((t) => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const resetForm = () => {
    setSelectedScore(3);
    setSelectedTags([]);
    setJournalText('');
    setEditingId(null);
  };

  const handleStartEdit = (entry: MoodEntry) => {
    setEditingId(entry.id);
    setSelectedScore(entry.mood_score);
    setSelectedTags(entry.tags);
    setJournalText(entry.journal_text || '');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (editingId) {
        await apiClient.put(`/patient/mood/${editingId}`, {
          mood_score: selectedScore,
          tags: selectedTags,
          journal_text: journalText
        });
        setSuccess('Mood log updated successfully.');
      } else {
        await apiClient.post('/patient/mood/', {
          mood_score: selectedScore,
          tags: selectedTags,
          journal_text: journalText
        });
        setSuccess('Daily mood log saved successfully.');
      }
      resetForm();
      await fetchEntries();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save entry.');
    } finally {
      setLoading(false);
    }
  };

  // Format data for Recharts (chronological order)
  const chartData = [...entries].reverse().map((entry) => ({
    date: new Date(entry.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    fullDate: new Date(entry.created_at).toLocaleString(),
    score: entry.mood_score,
    tags: entry.tags,
    journal: entry.journal_text
  }));

  const getMoodItem = (score: number) => MOOD_SCALES.find((m) => m.score === score) || MOOD_SCALES[2];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const mood = getMoodItem(data.score);
      return (
        <div className="space-y-1 rounded-md border border-[#e8e4df] bg-white px-3 py-2 text-xs shadow-md">
          <p className="font-medium text-foreground">{data.fullDate}</p>
          <div className="flex items-center gap-1.5 font-bold text-foreground">
            <span aria-hidden="true">{mood.emoji}</span>
            <span>
              {mood.label} · {data.score}/5
            </span>
          </div>
          {data.tags.length > 0 && <p className="text-muted-foreground">Tags: {data.tags.join(', ')}</p>}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      {/* Title */}
      <header className="mb-2">
        <p className="small-caps text-accent">Well-being journal</p>
        <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">Mood Tracker & Journal</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Record your daily feelings, tag influencing factors, and keep a private personal journal.
        </p>
      </header>

      {error && (
        <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div role="status" aria-live="polite" className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
          {success}
        </div>
      )}

      {/* Check-In / Edit Form */}
      <Card variant="glass">
        <CardHeader className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>{editingId ? 'Edit Recent Mood Entry' : 'Daily Check-In'}</CardTitle>
            <CardDescription>
              {editingId ? 'Adjusting an existing log — your journal is appended to your history.' : 'A few seconds a day helps you spot patterns early.'}
            </CardDescription>
          </div>
          {editingId && (
            <Button type="button" variant="ghost" size="sm" onClick={resetForm}>
              Cancel Edit
            </Button>
          )}
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Mood Scale Buttons */}
            <div>
              <span className="mb-3 block font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                How are you feeling right now?
              </span>
              <div className="grid grid-cols-5 gap-2" role="group" aria-label="Mood score selector">
                {MOOD_SCALES.map((item) => {
                  const selected = selectedScore === item.score;
                  return (
                    <button
                      key={item.score}
                      type="button"
                      onClick={() => setSelectedScore(item.score)}
                      aria-label={`Mood score ${item.score} of 5 — ${item.label}`}
                      aria-pressed={selected}
                      className={`flex min-h-0 flex-col items-center justify-center gap-1 rounded-md border p-2 transition-all duration-200 cursor-pointer ${
                        selected
                          ? `${item.active} ring-2 ring-accent/20 scale-[1.03] shadow-sm`
                          : INACTIVE_MOOD_CLS
                      }`}
                    >
                      <span aria-hidden="true" className="text-2xl sm:text-3xl">
                        {item.emoji}
                      </span>
                      <span className="hidden text-[10px] font-medium leading-tight text-center sm:inline">
                        {item.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Tags */}
            <div>
              <span className="mb-2 block font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                What factors affected your mood today?
              </span>
              <div className="flex flex-wrap gap-2">
                {PREDEFINED_TAGS.map((tag) => {
                  const active = selectedTags.includes(tag);
                  return (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => handleTagToggle(tag)}
                      aria-pressed={active}
                      className={`cursor-pointer rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-all ${
                        active
                          ? 'border-accent bg-accent text-white shadow-sm'
                          : 'border-[#e8e4df] bg-white text-muted-foreground hover:border-[#d6cfc7] hover:bg-muted'
                      }`}
                    >
                      {tag}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Journal Text */}
            <Textarea
              id="mood-journal"
              label="Private Journal Entry"
              rows={3}
              value={journalText}
              onChange={(e) => setJournalText(e.target.value)}
              placeholder="Write down your thoughts, events of the day, or anything on your mind..."
              helperText="Optional — visible only to you and your treating doctor."
            />

            <Button type="submit" variant="primary" size="lg" className="w-full" isLoading={loading}>
              {loading ? 'Saving…' : editingId ? 'Update Entry' : 'Save Mood Log'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Mood Analytics Chart (Recharts) */}
      <Card variant="glass">
        <CardHeader className="flex flex-wrap items-center gap-3">
          <div className="min-w-0">
            <CardTitle>Mood Trends over Time</CardTitle>
            <CardDescription>Your reported mood, on a 1–5 scale, over the selected window.</CardDescription>
          </div>
          <Select
            aria-label="Mood history time range"
            options={TIME_RANGE_OPTIONS}
            value={String(timeRange)}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="w-40"
          />
        </CardHeader>
        <CardContent>
          {chartData.length === 0 ? (
            <div className="py-12 text-center">
              <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground/70">
                No mood logs yet
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                Add your first entry above to start spotting patterns.
              </p>
            </div>
          ) : (
            <div className="h-64 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#b8860b" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#b8860b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e4df" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b6b6b' }} />
                  <YAxis domain={[1, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 11, fill: '#6b6b6b' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="score" stroke="#b8860b" strokeWidth={3} fillOpacity={1} fill="url(#colorMood)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Historical Entries Timeline */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle>Recent Journal Logs</CardTitle>
          <CardDescription>Every check-in you have recorded, most recent first.</CardDescription>
        </CardHeader>
        <CardContent>
          {entries.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">No journal entries recorded yet.</div>
          ) : (
            <div className="divide-y divide-[#e8e4df]">
              {entries.map((entry) => {
                const mood = getMoodItem(entry.mood_score);
                return (
                  <article key={entry.id} className="space-y-2 py-4 first:pt-0 last:pb-0">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <span aria-hidden="true" className="text-2xl">
                          {mood.emoji}
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-foreground">{mood.label}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(entry.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      {entry.can_edit && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleStartEdit(entry)}
                        >
                          Edit
                        </Button>
                      )}
                    </div>

                    {entry.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {entry.tags.map((t) => (
                          <span
                            key={t}
                            className="rounded-full border border-[#e8e4df] bg-muted px-2.5 py-0.5 text-xs text-muted-foreground"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    )}

                    {entry.journal_text && (
                      <p className="rounded-md border border-[#e8e4df] bg-muted p-3 text-sm italic leading-relaxed text-muted-foreground">
                        “{entry.journal_text}”
                      </p>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}