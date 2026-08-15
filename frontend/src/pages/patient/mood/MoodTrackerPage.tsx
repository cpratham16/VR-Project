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
  { score: 1, emoji: '😞', label: 'Severe Distress', color: 'bg-red-500 text-white' },
  { score: 2, emoji: '😟', label: 'Low / Stressed', color: 'bg-orange-400 text-white' },
  { score: 3, emoji: '😐', label: 'Neutral / Okay', color: 'bg-amber-400 text-gray-900' },
  { score: 4, emoji: '🙂', label: 'Good / Positive', color: 'bg-emerald-400 text-gray-900' },
  { score: 5, emoji: '😊', label: 'Excellent / Calm', color: 'bg-teal-600 text-white' }
];

const PREDEFINED_TAGS = [
  '📚 Academic / Exams',
  '😴 Sleep / Fatigue',
  '👥 Social / Relationships',
  '🏃 Physical Health',
  '🏠 Family / Personal',
  '⚡ Anxiety / Overwhelmed',
  '💼 Career / Future'
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
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-md text-xs space-y-1">
          <p className="font-semibold text-gray-800">{data.fullDate}</p>
          <div className="flex items-center space-x-1 font-bold text-teal-700">
            <span>{mood.emoji}</span>
            <span>Score: {data.score}/5 ({mood.label})</span>
          </div>
          {data.tags.length > 0 && (
            <p className="text-gray-600">Tags: {data.tags.join(', ')}</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Title Card */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h2 className="text-2xl font-bold text-gray-800">Mood Tracker & Journal</h2>
        <p className="text-sm text-gray-600 mt-1">Record your daily feelings, tag influencing factors, and keep a private personal journal.</p>
      </div>

      {error && <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}
      {success && <div role="status" aria-live="polite" className="p-4 text-sm text-emerald-700 bg-emerald-100 rounded-lg">{success}</div>}

      {/* Check-In / Edit Form */}
      <div className="bg-white p-6 rounded-lg shadow-sm space-y-6">
        <div className="flex justify-between items-center border-b border-gray-200 pb-3">
          <h3 className="text-lg font-semibold text-gray-800">
            {editingId ? 'Edit Recent Mood Entry' : 'Daily Check-In'}
          </h3>
          {editingId && (
            <button
              onClick={resetForm}
              className="text-xs text-gray-500 hover:text-gray-700 underline"
            >
              Cancel Edit
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Mood Scale Buttons */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">How are you feeling right now?</label>
            <div className="grid grid-cols-5 gap-2" role="group" aria-label="Mood score selector">
              {MOOD_SCALES.map((item) => (
                <button
                  key={item.score}
                  type="button"
                  onClick={() => setSelectedScore(item.score)}
                  aria-label={`Mood score ${item.score} of 5 — ${item.label}`}
                  aria-pressed={selectedScore === item.score}
                  className={`p-3 rounded-xl flex flex-col items-center justify-center transition border ${
                    selectedScore === item.score
                      ? `${item.color} border-transparent ring-2 ring-teal-500 scale-105 shadow`
                      : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  <span aria-hidden="true" className="text-2xl sm:text-3xl">{item.emoji}</span>
                  <span className="text-xs mt-1 font-medium text-center hidden sm:inline">{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">What factors affected your mood today?</label>
            <div className="flex flex-wrap gap-2">
              {PREDEFINED_TAGS.map((tag) => {
                const active = selectedTags.includes(tag);
                return (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => handleTagToggle(tag)}
                    aria-pressed={active}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                      active
                        ? 'bg-teal-700 text-white border-teal-700 shadow-sm'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {tag}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Journal Text */}
          <div>
            <label htmlFor="mood-journal" className="block text-sm font-medium text-gray-700 mb-1">
              Private Journal Entry <span className="text-xs text-gray-600 font-normal">(Optional — visible only to you and your treating doctor)</span>
            </label>
            <textarea
              id="mood-journal"
              rows={3}
              value={journalText}
              onChange={(e) => setJournalText(e.target.value)}
              placeholder="Write down your thoughts, events of the day, or anything on your mind..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-teal-500 focus:border-teal-500 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-teal-700 text-white font-medium rounded-md shadow hover:bg-teal-800 transition disabled:opacity-50"
          >
            {loading ? 'Saving...' : editingId ? 'Update Entry' : 'Save Mood Log'}
          </button>
        </form>
      </div>

      {/* Mood Analytics Chart (Recharts) */}
      <div className="bg-white p-6 rounded-lg shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-800">Mood Trends over Time</h3>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="text-xs border border-gray-300 rounded px-2 py-1 bg-white text-gray-700"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
        </div>

        {chartData.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">
            No mood logs available for this period. Add your first entry above!
          </div>
        ) : (
          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0d9488" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis domain={[1, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="score" stroke="#0d9488" strokeWidth={3} fillOpacity={1} fill="url(#colorMood)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Historical Entries Timeline */}
      <div className="bg-white p-6 rounded-lg shadow-sm space-y-4">
        <h3 className="text-lg font-semibold text-gray-800">Recent Journal Logs</h3>

        {entries.length === 0 ? (
          <div className="text-center py-6 text-gray-400 text-sm">No journal entries recorded yet.</div>
        ) : (
          <div className="divide-y divide-gray-100">
            {entries.map((entry) => {
              const mood = getMoodItem(entry.mood_score);
              return (
                <div key={entry.id} className="py-4 space-y-2">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{mood.emoji}</span>
                      <div>
                        <span className="font-semibold text-gray-800 text-sm">{mood.label}</span>
                        <span className="text-xs text-gray-400 block sm:inline sm:ml-2">
                          {new Date(entry.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    {entry.can_edit && (
                      <button
                        onClick={() => handleStartEdit(entry)}
                        className="text-xs text-teal-600 hover:text-teal-700 font-medium px-2 py-1 bg-teal-50 rounded border border-teal-200"
                      >
                        Edit
                      </button>
                    )}
                  </div>

                  {entry.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {entry.tags.map((t) => (
                        <span key={t} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}

                  {entry.journal_text && (
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-100 italic">
                      "{entry.journal_text}"
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
