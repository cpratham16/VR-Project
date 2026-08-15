import { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import VRSessionRunner, { type VRASession } from './VRSessionRunner';

export default function VRTherapyPage() {
  const [sessions, setSessions] = useState<VRASession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSession, setActiveSession] = useState<VRASession | null>(null);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/patient/vr/assigned');
      setSessions(res.data);
    } catch {
      setError('Unable to load your VR therapy sessions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const launch = async (session: VRASession) => {
    try {
      await apiClient.post(`/patient/vr/sessions/${session.id}/start`);
      setActiveSession({ ...session, status: 'in_progress' });
    } catch {
      setError('Failed to start session. Please try again.');
    }
  };

  const available = sessions.filter((s) => s.status === 'assigned' || s.status === 'in_progress');
  const completed = sessions.filter((s) => s.status === 'completed' || s.status === 'cancelled');

  const intensityColor: Record<string, string> = {
    low: 'bg-emerald-100 text-emerald-800',
    medium: 'bg-amber-100 text-amber-800',
    high: 'bg-red-100 text-red-800',
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 px-4 py-4">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🥽</span>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">VR Exposure Therapy</h1>
            <p className="text-sm text-gray-600 mt-1">
              Browser-based exposure sessions assigned by your doctor. Runs on any laptop — a VR headset is optional.
            </p>
          </div>
        </div>
      </div>

      {error && <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl">{error}</div>}

      {loading ? (
        <div className="bg-white p-12 rounded-2xl text-center text-gray-600 text-sm">Loading your therapy sessions...</div>
      ) : available.length === 0 && completed.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl text-center border border-gray-100">
          <div className="text-4xl mb-3">🌱</div>
          <p className="text-gray-600 text-sm">You don't have any VR sessions assigned yet.</p>
          <p className="text-gray-600 text-xs mt-1">Your doctor will assign an exposure scenario here when it's part of your care plan.</p>
        </div>
      ) : (
        <>
          {available.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider">Assigned Sessions</h2>
              {available.map((s) => (
                <div key={s.id} className="bg-white p-6 rounded-2xl shadow-sm border border-indigo-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-gray-900">{s.scenario_name}</h3>
                      <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${intensityColor[s.intensity_level]}`}>
                        {s.intensity_level} intensity
                      </span>
                      {s.status === 'in_progress' && (
                        <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700">in progress</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-1 capitalize">{s.phobia_type} · {s.duration_minutes} min · {s.exposure_steps} steps</p>
                    {s.instructions && <p className="text-sm text-gray-700 mt-2"><strong>Doctor:</strong> {s.instructions}</p>}
                  </div>
                  <button
                    onClick={() => launch(s)}
                    aria-label={`Launch ${s.scenario_name} VR session, ${s.duration_minutes} minutes, ${s.exposure_steps} exposure steps`}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-6 py-3 rounded-xl shadow cursor-pointer whitespace-nowrap"
                  >
                    {s.status === 'in_progress' ? 'Resume Session ▶' : 'Launch Session ▶'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {completed.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider pt-4">Past Sessions</h2>
              {completed.map((s) => (
                <div key={s.id} className="bg-gray-50 p-5 rounded-2xl border border-gray-100">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-gray-800">{s.scenario_name}</span>
                      <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${s.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-200 text-gray-600'}`}>
                        {s.status}
                      </span>
                    </div>
                    <span className="text-xs text-gray-600">{s.completed_at ? new Date(s.completed_at).toLocaleDateString() : ''}</span>
                  </div>
                  {s.suds_pre != null && (
                    <div className="text-xs text-gray-600 mt-2">
                      SUDS: <strong>{s.suds_pre}</strong> → <strong>{s.suds_post}</strong>
                      {(s.suds_pre ?? 0) > (s.suds_post ?? 0) && <span className="text-emerald-600 font-semibold ml-2">✓ improvement</span>}
                    </div>
                  )}
                  {s.patient_feedback && <p className="text-xs text-gray-600 mt-1 italic">"{s.patient_feedback}"</p>}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {activeSession && (
        <VRSessionRunner session={activeSession} onExit={() => { setActiveSession(null); fetchSessions(); }} />
      )}
    </div>
  );
}
