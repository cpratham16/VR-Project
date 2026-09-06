import { useState, useEffect, useMemo, useCallback } from 'react';
import { apiClient } from '../../../api/client';
import { Card, Button, Input, Textarea } from '../../../components/ui';

interface DiaryEntry {
  id: string;
  title: string | null;
  content: string;
  entry_date: string;
  emotion_tag: string | null;
  created_at: string;
  updated_at: string;
}

interface DiaryFormData {
  title: string;
  content: string;
  entry_date: string;
  emotion_tag: string;
}

type ViewMode = 'list' | 'calendar';

const EMOTION_TAGS = [
  { value: 'happy', label: 'Happy', emoji: '😊' },
  { value: 'calm', label: 'Calm', emoji: '😌' },
  { value: 'sad', label: 'Sad', emoji: '😢' },
  { value: 'anxious', label: 'Anxious', emoji: '😰' },
  { value: 'stressed', label: 'Stressed', emoji: '😫' },
  { value: 'grateful', label: 'Grateful', emoji: '🙏' },
  { value: 'angry', label: 'Angry', emoji: '😠' },
  { value: 'excited', label: 'Excited', emoji: '🤩' },
  { value: 'lonely', label: 'Lonely', emoji: '😔' },
  { value: 'hopeful', label: 'Hopeful', emoji: '🌱' },
];

export default function DiaryPage() {
  const [entries, setEntries] = useState<DiaryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingEntry, setEditingEntry] = useState<DiaryEntry | null>(null);
  const [formData, setFormData] = useState<DiaryFormData>({
    title: '',
    content: '',
    entry_date: new Date().toISOString().slice(0, 16),
    emotion_tag: '',
  });
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [calendarMonth, setCalendarMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [emotionFilter, setEmotionFilter] = useState('');

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (emotionFilter) params.append('emotion_tag', emotionFilter);
      const res = await apiClient.get(`/patient/diary/?${params.toString()}`);
      setEntries(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load diary entries');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, emotionFilter]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.content.trim()) {
      setError('Content is required');
      return;
    }
    setError('');
    setLoading(true);
    try {
      if (editingEntry) {
        await apiClient.put(`/patient/diary/${editingEntry.id}`, formData);
      } else {
        await apiClient.post('/patient/diary/', formData);
      }
      setShowForm(false);
      setEditingEntry(null);
      setFormData({ title: '', content: '', entry_date: new Date().toISOString().slice(0, 16), emotion_tag: '' });
      fetchEntries();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save entry');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (entry: DiaryEntry) => {
    setEditingEntry(entry);
    setFormData({
      title: entry.title || '',
      content: entry.content,
      entry_date: entry.entry_date.slice(0, 16),
      emotion_tag: entry.emotion_tag || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this diary entry?')) return;
    setError('');
    try {
      await apiClient.delete(`/patient/diary/${id}`);
      fetchEntries();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete entry');
    }
  };

  const handleNewEntry = () => {
    setEditingEntry(null);
    const now = new Date();
    setSelectedDate(now);
    setFormData({ title: '', content: '', entry_date: now.toISOString().slice(0, 16), emotion_tag: '' });
    setShowForm(true);
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const getEntriesForDate = (date: Date) => {
    const dateStr = date.toISOString().slice(0, 10);
    return entries.filter(e => e.entry_date.slice(0, 10) === dateStr);
  };

  const monthDays = useMemo(() => {
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDay = firstDay.getDay(); // 0 = Sunday
    const daysInMonth = lastDay.getDate();
    const days = [];

    // Previous month trailing days
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startDay - 1; i >= 0; i--) {
      const day = prevMonthLastDay - i;
      const d = new Date(year, month - 1, day);
      days.push({ date: d, isCurrentMonth: false });
    }

    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      const d = new Date(year, month, day);
      days.push({ date: d, isCurrentMonth: true });
    }

    // Next month leading days to fill 6 weeks (42 days)
    const remaining = 42 - days.length;
    for (let day = 1; day <= remaining; day++) {
      const d = new Date(year, month + 1, day);
      days.push({ date: d, isCurrentMonth: false });
    }

    return days;
  }, [calendarMonth]);

  const goPrevMonth = () => setCalendarMonth(d => new Date(d.getFullYear(), d.getMonth() - 1, 1));
  const goNextMonth = () => setCalendarMonth(d => new Date(d.getFullYear(), d.getMonth() + 1, 1));

  const handleDateClick = (date: Date) => {
    if (!date) return;
    setSelectedDate(date);
    setViewMode('list');
  };

  const formatMonthYear = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const selectedDateEntries = selectedDate ? getEntriesForDate(selectedDate) : [];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Private Diary</h2>
          <p className="text-sm text-gray-600 mt-1">Your personal journal — only you can see this.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex border border-gray-300 rounded-md overflow-hidden">
            <Button
              variant={viewMode === 'list' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
            >
              List
            </Button>
            <Button
              variant={viewMode === 'calendar' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setViewMode('calendar')}
            >
              Calendar
            </Button>
          </div>
          <Input
            type="search"
            placeholder="Search entries..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-64"
          />
<select
            value={emotionFilter}
            onChange={(e) => setEmotionFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-accent w-full"
          >
            <option value="">All emotions</option>
            {EMOTION_TAGS.map((tag) => (
              <option key={tag.value} value={tag.value}>{tag.emoji} {tag.label}</option>
            ))}
          </select>
          <Button onClick={handleNewEntry} variant="primary" size="md">
            New Entry
          </Button>
        </div>
      </div>

      {error && <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}

      {showForm && (
        <Card variant="glass" className="p-6 space-y-4">
          <h3 className="text-xl font-semibold">{editingEntry ? 'Edit Entry' : 'New Entry'}</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Title (optional)"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Entry title"
              maxLength={255}
            />
            <Textarea
              label="Content"
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              placeholder="Write your thoughts..."
              rows={6}
              required
            />
            <Input
              type="datetime-local"
              label="Entry Date"
              value={formData.entry_date}
              onChange={(e) => setFormData({ ...formData, entry_date: e.target.value })}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Emotion Tag (optional)</label>
              <div className="grid grid-cols-5 gap-2">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, emotion_tag: '' })}
                  className={`p-3 rounded-lg border-2 text-center transition ${
                    formData.emotion_tag === ''
                      ? 'border-accent bg-accent/10'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-lg">✕</span>
                  <p className="text-xs text-gray-500 mt-1">None</p>
                </button>
                {EMOTION_TAGS.map((tag) => (
                  <button
                    key={tag.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, emotion_tag: tag.value })}
                    className={`p-3 rounded-lg border-2 text-center transition ${
                      formData.emotion_tag === tag.value
                        ? 'border-accent bg-accent/10'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <span className="text-2xl">{tag.emoji}</span>
                    <p className="text-xs text-gray-700 mt-1 capitalize">{tag.label}</p>
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-end space-x-3 pt-2">
              <Button type="button" variant="ghost" onClick={() => { setShowForm(false); setEditingEntry(null); }}>Cancel</Button>
              <Button type="submit" variant="primary" isLoading={loading}>
                {editingEntry ? 'Save Changes' : 'Create Entry'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {loading && <div className="text-center py-8 text-gray-500">Loading diary entries...</div>}

      {!loading && !showForm && viewMode === 'calendar' && (
        <Card variant="glass" className="p-6">
          <div className="flex justify-between items-center mb-4">
            <Button variant="ghost" size="sm" onClick={goPrevMonth} aria-label="Previous month">
              ← Prev
            </Button>
            <h3 className="text-lg font-semibold text-gray-800">{formatMonthYear(calendarMonth)}</h3>
            <Button variant="ghost" size="sm" onClick={goNextMonth} aria-label="Next month">
              Next →
            </Button>
          </div>
          <div className="grid grid-cols-7 gap-1 text-center text-xs text-gray-500 mb-2">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => <div key={d}>{d}</div>)}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {monthDays.map((day, idx) => {
              const dayEntries = getEntriesForDate(day.date);
              const isToday = day.date.toDateString() === new Date().toDateString();
              const isSelected = selectedDate && day.date.toDateString() === selectedDate.toDateString();
              return (
                <button
                  key={idx}
                  onClick={() => handleDateClick(day.date)}
                  className={`aspect-square flex flex-col items-center justify-center p-1 rounded transition ${
                    day.isCurrentMonth ? 'text-gray-800' : 'text-gray-400'
                  } ${isToday ? 'ring-2 ring-accent' : ''} ${isSelected ? 'bg-accent/20' : ''} ${
                    dayEntries.length > 0 ? 'relative' : ''
                  }`}
                  disabled={!day.isCurrentMonth}
                  aria-label={day.date.toLocaleDateString()}
                >
                  <span className="font-medium">{day.date.getDate()}</span>
                  {dayEntries.length > 0 && (
                    <span className="absolute bottom-1 text-lg" aria-label={`${dayEntries.length} entries`}>
                      📖
                    </span>
                  )}
                  {dayEntries.length > 1 && (
                    <span className="absolute top-1 right-1 text-xs bg-accent text-white rounded-full w-4 h-4 flex items-center justify-center">
                      {dayEntries.length}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </Card>
      )}

      {!loading && !showForm && viewMode === 'list' && (
        <div className="space-y-4">
          {selectedDate && (
            <Card variant="outline" className="p-4">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-gray-800">
                  Entries for {selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                </h3>
                <Button variant="ghost" size="sm" onClick={() => setSelectedDate(null)}>Clear filter</Button>
              </div>
            </Card>
          )}
          {selectedDateEntries.length > 0 && !selectedDate ? (
            <div className="space-y-4">
              {entries.map((entry) => (
                <Card key={entry.id} variant="glass" className="p-5 space-y-3">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      {entry.title && <h4 className="font-semibold text-gray-800">{entry.title}</h4>}
                      <p className="text-gray-700 whitespace-pre-wrap mt-1">{entry.content}</p>
                      <div className="flex flex-wrap items-center gap-2 mt-2">
                        <p className="text-xs text-gray-500">
                          {formatDate(entry.entry_date)} · {formatTime(entry.entry_date)} · Updated {new Date(entry.updated_at).toLocaleString()}
                        </p>
                        {entry.emotion_tag && (
                          <span className="px-2 py-0.5 text-xs bg-accent/10 text-accent rounded-full">
                            {entry.emotion_tag.charAt(0).toUpperCase() + entry.emotion_tag.slice(1)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(entry)}>Edit</Button>
                      <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => handleDelete(entry.id)}>Delete</Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : selectedDateEntries.length > 0 ? (
            <div className="space-y-4">
              {selectedDateEntries.map((entry) => (
                <Card key={entry.id} variant="glass" className="p-5 space-y-3">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      {entry.title && <h4 className="font-semibold text-gray-800">{entry.title}</h4>}
                      <p className="text-gray-700 whitespace-pre-wrap mt-1">{entry.content}</p>
                      <div className="flex flex-wrap items-center gap-2 mt-2">
                        <p className="text-xs text-gray-500">
                          {formatDate(entry.entry_date)} · {formatTime(entry.entry_date)} · Updated {new Date(entry.updated_at).toLocaleString()}
                        </p>
                        {entry.emotion_tag && (
                          <span className="px-2 py-0.5 text-xs bg-accent/10 text-accent rounded-full">
                            {entry.emotion_tag.charAt(0).toUpperCase() + entry.emotion_tag.slice(1)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(entry)}>Edit</Button>
                      <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => handleDelete(entry.id)}>Delete</Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : entries.length === 0 ? (
            <Card variant="outline" className="p-8 text-center">
              <p className="text-gray-500">No diary entries yet.</p>
              <Button onClick={handleNewEntry} variant="primary" className="mt-4">Write your first entry</Button>
            </Card>
          ) : (
            <div className="space-y-4">
              {entries.map((entry) => (
                <Card key={entry.id} variant="glass" className="p-5 space-y-3">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      {entry.title && <h4 className="font-semibold text-gray-800">{entry.title}</h4>}
                      <p className="text-gray-700 whitespace-pre-wrap mt-1">{entry.content}</p>
                      <div className="flex flex-wrap items-center gap-2 mt-2">
                        <p className="text-xs text-gray-500">
                          {formatDate(entry.entry_date)} · {formatTime(entry.entry_date)} · Updated {new Date(entry.updated_at).toLocaleString()}
                        </p>
                        {entry.emotion_tag && (
                          <span className="px-2 py-0.5 text-xs bg-accent/10 text-accent rounded-full">
                            {entry.emotion_tag.charAt(0).toUpperCase() + entry.emotion_tag.slice(1)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(entry)}>Edit</Button>
                      <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => handleDelete(entry.id)}>Delete</Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}