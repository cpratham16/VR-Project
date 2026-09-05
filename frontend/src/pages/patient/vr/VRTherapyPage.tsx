import { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import VRSessionRunner, { type VRASession } from './VRSessionRunner';

interface ScenarioCard {
  id: string;
  slug: string;
  name: string;
  phobia_type: string;
  description: string;
}

export default function VRTherapyPage() {
  const [sessions, setSessions] = useState<VRASession[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioCard[]>([]);
  const [intensityChoice, setIntensityChoice] = useState<Record<string, 'low' | 'medium' | 'high'>>({});
  const [launchingId, setLaunchingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSession, setActiveSession] = useState<VRASession | null>(null);

  useEffect(() => {
    fetchSessions();
    fetchScenarios();
  }, []);

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

  const fetchScenarios = async () => {
    try {
      const res = await apiClient.get('/patient/vr/scenarios');
      setScenarios(res.data);
    } catch {
      /* catalog optional */
    }
  };

  const launch = async (session: VRASession) => {
    try {
      await apiClient.post(`/patient/vr/sessions/${session.id}/start`);
      setActiveSession({ ...session, status: 'in_progress' });
    } catch {
      setError('Failed to start session. Please try again.');
    }
  };

  const selfInitiate = async (scenario: ScenarioCard) => {
    setLaunchingId(scenario.id);
    setError('');
    try {
      const intensity = intensityChoice[scenario.id] ?? 'low';
      const res = await apiClient.post('/patient/vr/self-initiate', {
        scenario_id: scenario.id,
        intensity_level: intensity,
      });
      await launch(res.data);
    } catch {
      setError('Failed to launch this module. Please try again.');
    } finally {
      setLaunchingId(null);
    }
  };

  const available = sessions.filter((s) => s.status === 'assigned' || s.status === 'in_progress');
  const completed = sessions.filter((s) => s.status === 'completed' || s.status === 'cancelled');

  // Scenario IDs already having an open session are launched from that session instead
  const openScenarioIds = new Set(available.map((s) => s.scenario_id));
  const browsable = scenarios.filter((sc) => !openScenarioIds.has(sc.id));

  const intensityColor: Record<string, string> = {
    low: 'bg-emerald-100 text-emerald-800',
    medium: 'bg-amber-100 text-amber-800',
    high: 'bg-red-100 text-red-800',
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 px-4 py-4">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🥽</span>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">VR Exposure Therapy</h1>
            <p className="text-sm text-gray-600 mt-1">
              Explore guided exposure modules at your own pace — no referral needed. Counselor-recommended sessions appear with a badge.
            </p>
          </div>
        </div>
      </div>

      {error && <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-md">{error}</div>}

      {loading ? (
        <div className="bg-white p-12 rounded-lg text-center text-gray-600 text-sm">Loading your therapy modules...</div>
      ) : (
        <>
          {/* Open sessions (assigned or in progress) */}
          {available.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider">Your Sessions</h2>
              {available.map((s) => (
                <div key={s.id} className="bg-white p-6 rounded-lg shadow-sm border border-[#e8e4df] flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-lg font-bold text-gray-900">{s.scenario_name}</h3>
                      <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${intensityColor[s.intensity_level]}`}>
                        {s.intensity_level} intensity
                      </span>
                      {s.status === 'in_progress' && (
                        <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700">in progress</span>
                      )}
                      {s.source === 'assigned' && (
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-muted text-accent border border-[#e8e4df]">
                          Recommended by your counselor
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-1 capitalize">{s.phobia_type} · {s.duration_minutes} min · {s.exposure_steps} steps</p>
                    {s.source === 'assigned' && s.instructions && (
                      <p className="text-sm text-gray-700 mt-2"><strong>Counselor:</strong> {s.instructions}</p>
                    )}
                  </div>
                  <button
                    onClick={() => launch(s)}
                    aria-label={`Launch ${s.scenario_name} VR session, ${s.duration_minutes} minutes, ${s.exposure_steps} exposure steps`}
                    className="bg-[#1a1a1a] hover:bg-black/80 text-white font-bold px-6 py-3 rounded-md shadow cursor-pointer whitespace-nowrap"
                  >
                    {s.status === 'in_progress' ? 'Resume Session ▶' : 'Launch Session ▶'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Module browser */}
          <div className="space-y-4">
            <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider pt-2">Explore all modules</h2>
            {browsable.length === 0 ? (
              <p className="text-xs text-slate-400">All available modules already have an open session above.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {browsable.map((sc) => {
                  const chosen = intensityChoice[sc.id] ?? 'low';
                  return (
                    <div key={sc.id} className="bg-white p-5 rounded-lg shadow-sm border border-gray-100 flex flex-col gap-3">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="text-base font-bold text-gray-900">{sc.name}</h3>
                          <p className="text-xs text-gray-500 capitalize">{sc.phobia_type} · self-guided</p>
                        </div>
                        <span className="text-2xl" aria-hidden="true">🥽</span>
                      </div>
                      <p className="text-xs text-gray-600 leading-relaxed">{sc.description}</p>
                      <div className="mt-auto space-y-2.5">
                        <div>
                          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Intensity</p>
                          <div className="flex gap-1.5">
                            {(['low', 'medium', 'high'] as const).map((lvl) => (
                              <button
                                key={lvl}
                                onClick={() => setIntensityChoice((c) => ({ ...c, [sc.id]: lvl }))}
                                aria-pressed={chosen === lvl}
                                className={`cursor-pointer px-3 py-1 rounded-lg text-xs font-bold capitalize transition-all ${
                                  chosen === lvl
                                    ? 'bg-indigo-600 text-white shadow'
                                    : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                                }`}
                              >
                                {lvl}
                              </button>
                            ))}
                          </div>
                        </div>
                        <button
                          onClick={() => selfInitiate(sc)}
                          disabled={launchingId === sc.id}
                          aria-label={`Start self-guided ${sc.name} module at ${chosen} intensity`}
                          className="w-full bg-[#1a1a1a] hover:bg-black/80 disabled:opacity-50 text-white font-bold px-4 py-2.5 rounded-md shadow cursor-pointer"
                        >
                          {launchingId === sc.id ? 'Preparing…' : `Try it now (${chosen}) ▶`}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Past sessions */}
          {completed.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider pt-4">Past Sessions</h2>
              {completed.map((s) => (
                <div key={s.id} className="bg-gray-50 p-5 rounded-lg border border-gray-100">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-lg font-bold text-gray-800">{s.scenario_name}</span>
                      <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${s.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-200 text-gray-600'}`}>
                        {s.status}
                      </span>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${s.source === 'self_initiated' ? 'bg-muted text-accent' : 'bg-muted text-accent'}`}>
                        {s.source === 'self_initiated' ? 'Self-guided' : 'Counselor-assigned'}
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
