import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

interface ScreeningResult {
  id: string;
  screening_type: string;
  total_score: number;
  severity_band: string;
  created_at: string;
}

interface MoodEntry {
  id: string;
  mood_score: number;
  tags: string[];
  journal_text?: string;
  created_at: string;
}

interface ClinicalNote {
  id: string;
  doctor_id: string;
  note_text: string;
  created_at: string;
}

interface PatientDetail {
  user_id: string;
  email: string;
  pseudonym?: string;
  risk_level: string;
  screenings: ScreeningResult[];
  mood_entries: MoodEntry[];
  clinical_notes: ClinicalNote[];
}

export default function DoctorPatientDetail() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newNote, setNewNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [activeTab, setActiveTab] = useState<'notes' | 'screenings' | 'mood' | 'vr'>('notes');
  const [vrSessions, setVrSessions] = useState<any[]>([]);

  useEffect(() => {
    if (patientId) fetchDetail();
  }, [patientId]);

  useEffect(() => {
    if (activeTab === 'vr') {
      apiClient.get(`/doctor/vr/sessions?patient_id=${patientId}`).then(res => setVrSessions(res.data)).catch(console.error);
    }
  }, [activeTab, patientId]);

  const fetchDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.get(`/doctor/patient/${patientId}`);
      setPatient(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load patient detail');
    } finally {
      setLoading(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    setSavingNote(true);
    try {
      await apiClient.post(`/doctor/patient/${patientId}/notes`, {
        note_text: newNote
      });
      setNewNote('');
      await fetchDetail();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save note');
    } finally {
      setSavingNote(false);
    }
  };

  const getRiskBadge = (level?: string) => {
    switch (level) {
      case 'High': return 'bg-red-100 text-red-800 border-red-300';
      case 'Moderate': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'Low': return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getMoodEmoji = (score: number) => {
    const emojis = ['😞', '😟', '😐', '🙂', '😊'];
    return `${score}/5 ${emojis[score - 1] || ''}`;
  };

  if (loading) return <div className="p-12 text-center text-gray-500">Loading patient clinical profile...</div>;
  if (error || !patient) return <div className="p-8 text-center text-red-600 bg-red-50 rounded-lg">{error || 'Patient not found'}</div>;

  const chartData = [...patient.mood_entries].reverse().map((entry) => ({
    date: new Date(entry.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    score: entry.mood_score
  }));

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back Link */}
      <button
        onClick={() => navigate('/doctor/dashboard')}
        className="text-xs font-medium text-teal-700 hover:text-teal-800 flex items-center space-x-1"
      >
        <span>← Back to Clinical Triage</span>
      </button>

      {/* Patient Header Card */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-2xl font-bold text-gray-800">{patient.pseudonym || 'Anonymous Student'}</h2>
            <span className={`px-3 py-0.5 text-xs font-semibold rounded-full border ${getRiskBadge(patient.risk_level)}`}>
              Risk: {patient.risk_level}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">Account ID: {patient.email}</p>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('notes')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition ${
              activeTab === 'notes' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Clinical Notes ({patient.clinical_notes.length})
          </button>
          <button
            onClick={() => setActiveTab('screenings')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition ${
              activeTab === 'screenings' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Screenings ({patient.screenings.length})
          </button>
          <button
            onClick={() => setActiveTab('mood')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition ${
              activeTab === 'mood' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Mood Logs ({patient.mood_entries.length})
          </button>
          <button
            onClick={() => setActiveTab('vr')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition ${
              activeTab === 'vr' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            VR Sessions
          </button>
        </div>
      </div>

      {/* Tab: Clinical Notes */}
      {activeTab === 'notes' && (
        <div className="space-y-6">
          {/* Add Note Form */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Add Clinical Note</h3>
            <form onSubmit={handleAddNote} className="space-y-3">
              <textarea
                rows={3}
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Enter clinical observations, session notes, or treatment plan updates..."
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-teal-500 focus:border-teal-500"
              />
              <button
                type="submit"
                disabled={savingNote}
                className="px-4 py-2 bg-teal-600 text-white text-xs font-medium rounded hover:bg-teal-700 transition disabled:opacity-50"
              >
                {savingNote ? 'Saving Note...' : 'Save Clinical Note'}
              </button>
            </form>
          </div>

          {/* Past Notes List */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Past Clinical Notes</h3>
            {patient.clinical_notes.length === 0 ? (
              <p className="text-sm text-gray-400">No clinical notes recorded yet for this patient.</p>
            ) : (
              <div className="divide-y divide-gray-100">
                {patient.clinical_notes.map((note) => (
                  <div key={note.id} className="py-3 space-y-1">
                    <div className="flex justify-between items-center text-xs text-gray-500">
                      <span className="font-semibold text-teal-700">Authoring Doctor</span>
                      <span>{new Date(note.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-gray-800 bg-gray-50 p-3 rounded border border-gray-100">
                      {note.note_text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Screenings */}
      {activeTab === 'screenings' && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Screening Submissions (PHQ-9 & GAD-7)</h3>
          {patient.screenings.length === 0 ? (
            <p className="text-sm text-gray-400">No screening questionnaires submitted by patient yet.</p>
          ) : (
            <div className="divide-y divide-gray-100">
              {patient.screenings.map((s) => (
                <div key={s.id} className="py-3 flex justify-between items-center">
                  <div>
                    <span className="font-semibold text-gray-800">{s.screening_type}</span>
                    <span className="text-xs text-gray-400 ml-2">{new Date(s.created_at).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-700 font-medium">Score: {s.total_score}</span>
                    <span className="px-2.5 py-0.5 text-xs font-semibold rounded bg-teal-50 text-teal-800 border border-teal-200">
                      {s.severity_band}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab: Mood & Journal Logs */}
      {activeTab === 'mood' && (
        <div className="space-y-6">
          {/* Trend Chart */}
          {chartData.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-3">
              <h3 className="text-lg font-semibold text-gray-800">Mood Score History</h3>
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[1, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="score" stroke="#0d9488" fill="#ccfbf1" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Log List */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Patient Mood & Journal Entries</h3>
            {patient.mood_entries.length === 0 ? (
              <p className="text-sm text-gray-400">No mood logs recorded by patient.</p>
            ) : (
              <div className="divide-y divide-gray-100">
                {patient.mood_entries.map((m) => (
                  <div key={m.id} className="py-3 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-sm text-gray-800">Mood: {getMoodEmoji(m.mood_score)}</span>
                      <span className="text-xs text-gray-400">{new Date(m.created_at).toLocaleString()}</span>
                    </div>

                    {m.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {m.tags.map((t) => (
                          <span key={t} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}

                    {m.journal_text && (
                      <p className="text-xs text-gray-700 bg-gray-50 p-2.5 rounded border border-gray-100 italic">
                        "{m.journal_text}"
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: VR Sessions */}
      {activeTab === 'vr' && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">VR Therapy Sessions</h3>
          {vrSessions.length === 0 ? <p className="text-sm text-gray-400">No VR sessions assigned.</p> : (
            <div className="space-y-3">
              {vrSessions.map(vs => (
                <div key={vs.id} className="p-4 border rounded-lg border-gray-100 bg-gray-50 text-sm">
                  <div className="font-bold">{vs.scenario_name} ({vs.intensity_level})</div>
                  <div>Status: {vs.status}</div>
                  {vs.time_in_scene != null && (<div>Engagement: {vs.time_in_scene.toFixed(0)}s, {vs.interaction_count} interactions</div>)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
