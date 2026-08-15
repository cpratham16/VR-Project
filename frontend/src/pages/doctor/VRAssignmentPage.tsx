import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { useNavigate } from 'react-router-dom';

interface Scenario {
  id: string;
  slug: string;
  name: string;
  phobia_type: string;
  description: string;
}

interface Patient {
  id: string;
  email: string;
  pseudonym?: string;
}

export default function VRAssignmentPage() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);

  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [intensity, setIntensity] = useState<'low' | 'medium' | 'high'>('medium');
  const [duration, setDuration] = useState(10);
  const [steps, setSteps] = useState(5);
  const [instructions, setInstructions] = useState('');
  const [loading, setLoading] = useState(true);
  const [assigning, setAssigning] = useState(false);
  const [assignMsg, setAssignMsg] = useState('');

  const intensityConfig: Record<string, { desc: string; color: string }> = {
    low: { desc: 'Gentle exposure — few triggers, minimal intensity', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
    medium: { desc: 'Moderate exposure — balanced intensity for steady progress', color: 'bg-amber-100 text-amber-800 border-amber-200' },
    high: { desc: 'Intensive exposure — peak intensity for advanced patients', color: 'bg-red-100 text-red-800 border-red-200' },
  };

  useEffect(() => {
    (async () => {
      try {
        const [sRes, pRes, sessRes] = await Promise.all([
          apiClient.get('/doctor/vr/scenarios'),
          apiClient.get('/doctor/triage?sort_by=recency'),
          apiClient.get('/doctor/vr/sessions'),
        ]);
        setScenarios(sRes.data);
        setPatients(pRes.data);
        setSessions(sessRes.data);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedScenario || !selectedPatient) return;
    setAssigning(true);
    setAssignMsg('');
    try {
      await apiClient.post('/doctor/vr/assign', {
        patient_id: selectedPatient,
        scenario_id: selectedScenario.id,
        intensity_level: intensity,
        duration_minutes: duration,
        exposure_steps: steps,
        instructions,
      });
      setAssignMsg('VR session assigned successfully!');
      const sessRes = await apiClient.get('/doctor/vr/sessions');
      setSessions(sessRes.data);
    } catch (err: any) {
      setAssignMsg(err?.response?.data?.detail || 'Failed to assign VR session');
    } finally {
      setAssigning(false);
    }
  };

  const sessionStatusColor: Record<string, string> = {
    assigned: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-indigo-100 text-indigo-700',
    completed: 'bg-emerald-100 text-emerald-700',
    cancelled: 'bg-gray-200 text-gray-600',
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 px-4 py-4">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🥽</span>
            <h1 className="text-2xl font-bold text-gray-900">VR Therapy Assignment</h1>
          </div>
          <p className="text-sm text-gray-600 mt-1">Assign browser-based exposure therapy sessions to patients.</p>
        </div>
        <button onClick={() => navigate('/doctor/dashboard')} className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer">
          ← Back to Triage
        </button>
      </div>

      {loading ? (
        <div className="bg-white p-12 rounded-2xl text-center text-gray-400 text-sm">Loading scenarios and patient data...</div>
      ) : (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Assignment Form */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-5">New VR Session Assignment</h2>
            <form onSubmit={handleAssign} className="space-y-5">
              {/* Patient */}
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Assign to Patient</label>
                <select
                  required
                  value={selectedPatient}
                  onChange={(e) => setSelectedPatient(e.target.value)}
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm bg-white"
                >
                  <option value="">Select a patient...</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.pseudonym || p.email}
                    </option>
                  ))}
                </select>
              </div>

              {/* Scenario Selection */}
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Exposure Scenario</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {scenarios.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setSelectedScenario(s)}
                      className={`p-4 rounded-xl border-2 text-left transition cursor-pointer ${
                        selectedScenario?.id === s.id
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="text-sm font-bold text-gray-900">{s.name}</div>
                      <div className="text-[11px] text-gray-500 capitalize mt-0.5">{s.phobia_type}</div>
                      <div className="text-xs text-gray-600 mt-2 leading-relaxed">{s.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Intensity */}
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Intensity Level</label>
                <div className="grid grid-cols-3 gap-2">
                  {(['low', 'medium', 'high'] as const).map((l) => (
                    <button
                      key={l}
                      type="button"
                      onClick={() => setIntensity(l)}
                      className={`py-2.5 rounded-xl text-xs font-bold capitalize transition border cursor-pointer ${
                        intensity === l
                          ? intensityConfig[l].color
                          : 'bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      {l}
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-gray-500 mt-1">{intensityConfig[intensity].desc}</p>
              </div>

              {/* Duration & Steps */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Duration (minutes)</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min={2}
                      max={60}
                      value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                      className="flex-1 accent-indigo-600"
                    />
                    <span className="text-sm font-bold text-gray-800 w-10 text-right">{duration}m</span>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Exposure Steps</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min={2}
                      max={10}
                      value={steps}
                      onChange={(e) => setSteps(Number(e.target.value))}
                      className="flex-1 accent-indigo-600"
                    />
                    <span className="text-sm font-bold text-gray-800 w-10 text-right">{steps}</span>
                  </div>
                </div>
              </div>

              {/* Instructions */}
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Clinical Instructions (for patient)</label>
                <textarea
                  rows={3}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Start with 3 slow breaths. Focus on grounding before advancing to the next stage."
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {assignMsg && (
                <div className={`p-3 rounded-xl text-center text-xs font-semibold ${
                  assignMsg.includes('success') ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' : 'bg-red-50 border border-red-200 text-red-700'
                }`}>
                  {assignMsg}
                </div>
              )}

              <button
                type="submit"
                disabled={assigning || !selectedPatient || !selectedScenario}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl font-bold shadow cursor-pointer"
              >
                {assigning ? 'Assigning...' : 'Assign VR Session'}
              </button>
            </form>
          </div>

          {/* Past Sessions */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Assigned VR Sessions</h2>
            {sessions.length === 0 ? (
              <div className="text-sm text-gray-400 py-8 text-center">No VR sessions assigned yet.</div>
            ) : (
              <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                {sessions.map((s) => (
                  <div key={s.id} className="p-4 rounded-xl border border-gray-100 hover:border-gray-200 transition">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-sm font-bold text-gray-900">{s.scenario_name}</div>
                        <div className="text-xs text-gray-500">{s.duration_minutes}m · {s.exposure_steps} steps · {s.intensity_level}</div>
                        {s.suds_pre != null && (
                          <div className="text-xs text-gray-600 mt-1">
                            SUDS: {s.suds_pre} → {s.suds_post ?? '—'}
                            {(s.suds_pre ?? 0) > (s.suds_post ?? 0) && <span className="text-emerald-600 font-semibold ml-1">✓ improvement</span>}
                          </div>
                        )}
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${sessionStatusColor[s.status] || 'bg-gray-100 text-gray-500'}`}>
                        {s.status}
                      </span>
                    </div>
                    {s.patient_feedback && <p className="text-xs text-gray-500 mt-2 italic">"{s.patient_feedback}"</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
