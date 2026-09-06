import { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import { Card, Button, Input, Textarea } from '../../../components/ui';

interface DiaryEntry {
  id: string;
  title: string | null;
  content: string;
  entry_date: string;
  created_at: string;
  updated_at: string;
}

interface DiaryFormData {
  title: string;
  content: string;
  entry_date: string;
}

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
  });

  const fetchEntries = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.get('/patient/diary/');
      setEntries(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load diary entries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, []);

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
      setFormData({ title: '', content: '', entry_date: new Date().toISOString().slice(0, 16) });
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
    setFormData({ title: '', content: '', entry_date: new Date().toISOString().slice(0, 16) });
    setShowForm(true);
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Private Diary</h2>
          <p className="text-sm text-gray-600 mt-1">Your personal journal — only you can see this.</p>
        </div>
        <Button onClick={handleNewEntry} variant="primary" size="md">
          New Entry
        </Button>
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

      {!loading && !showForm && (
        <div className="space-y-4">
          {entries.length === 0 ? (
            <Card variant="outline" className="p-8 text-center">
              <p className="text-gray-500">No diary entries yet.</p>
              <Button onClick={handleNewEntry} variant="primary" className="mt-4">Write your first entry</Button>
            </Card>
          ) : (
            entries.map((entry) => (
              <Card key={entry.id} variant="glass" className="p-5 space-y-3">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    {entry.title && <h4 className="font-semibold text-gray-800">{entry.title}</h4>}
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{entry.content}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {formatDate(entry.entry_date)} · Updated {new Date(entry.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(entry)}>Edit</Button>
                    <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => handleDelete(entry.id)}>Delete</Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}