import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { apiClient } from '../../api/client';
import { useNavigate } from 'react-router-dom';

interface TriagePatient {
  user_id: string;
  email: string;
  pseudonym?: string;
  latest_phq9_score?: number;
  latest_phq9_severity?: string;
  latest_gad7_score?: number;
  latest_gad7_severity?: string;
  latest_mood_score?: number;
  last_activity?: string;
  risk_level: 'High' | 'Moderate' | 'Low' | 'Unassessed';
  risk_numeric: number;
}

interface RiskAlert {
  id: string;
  user_id: string;
  patient_pseudonym: string;
  severity: string;
  trigger_source: string;
  details: string;
  status: string;
  created_at: string;
}

export default function DoctorTriageDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [patients, setPatients] = useState<TriagePatient[]>([]);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isVerified, setIsVerified] = useState<boolean>(user?.is_verified || false);

  // Filter & Search states
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'risk' | 'recency'>('risk');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    fetchTriageData();
    fetchDoctorAlerts();
  }, [riskFilter, sortBy]);

  const fetchTriageData = async () => {
    setLoading(true);
    setError('');
    try {
      const filterParam = riskFilter !== 'all' ? `&severity_filter=${riskFilter}` : '';
      const res = await apiClient.get(`/doctor/triage?sort_by=${sortBy}${filterParam}`);
      setPatients(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load triage patient list');
    } finally {
      setLoading(false);
    }
  };

  const fetchDoctorAlerts = async () => {
    try {
      const res = await apiClient.get('/doctor/alerts');
      setAlerts(res.data.filter((a: RiskAlert) => a.status === 'pending'));
    } catch {
      // ignore
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await apiClient.post(`/doctor/alerts/${alertId}/acknowledge`, { resolution_notes: 'Reviewed by doctor' });
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch {
      alert('Failed to acknowledge alert');
    }
  };

  const handleVerifySelf = async () => {
    try {
      const res = await apiClient.post('/doctor/verify-self');
      setIsVerified(res.data.is_verified);
    } catch {
      alert('Verification failed');
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'High':
        return 'bg-red-100 text-red-800 border-red-300 animate-pulse';
      case 'Moderate':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'Low':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getMoodEmoji = (score?: number) => {
    if (!score) return '—';
    const emojis = ['😞', '😟', '😐', '🙂', '😊'];
    return `${score}/5 ${emojis[score - 1] || ''}`;
  };

  const filteredPatients = patients.filter((p) => {
    const term = searchTerm.toLowerCase();
    const name = (p.pseudonym || '').toLowerCase();
    const email = p.email.toLowerCase();
    return name.includes(term) || email.includes(term);
  });

  const highCount = patients.filter((p) => p.risk_level === 'High').length;
  const modCount = patients.filter((p) => p.risk_level === 'Moderate').length;
  const lowCount = patients.filter((p) => p.risk_level === 'Low').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Pending Emergency Alerts Banner */}
      {alerts.length > 0 && (
        <div className="bg-red-600 border-2 border-red-700 p-4 rounded-xl shadow-lg text-white space-y-3">
          <div className="flex items-center gap-2 font-bold text-lg">
            <span className="text-2xl animate-bounce">🚨</span>
            <span>CRITICAL RISK ALERTS ({alerts.length} Pending)</span>
          </div>
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div key={alert.id} className="bg-red-700 p-3 rounded-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div>
                  <span className="font-semibold text-red-100">{alert.patient_pseudonym}:</span>{' '}
                  <span className="text-sm text-white">{alert.details}</span>
                  <span className="text-xs text-red-200 ml-2">({new Date(alert.created_at).toLocaleTimeString()})</span>
                </div>
                <button
                  onClick={() => handleAcknowledgeAlert(alert.id)}
                  aria-label={`Acknowledge alert for ${alert.patient_pseudonym}`}
                  className="bg-white text-red-700 hover:bg-red-50 text-xs font-bold px-3 py-1.5 rounded shadow cursor-pointer"
                >
                  Acknowledge Alert
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Header Bar */}
      <div className="bg-white p-6 rounded-lg shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-2xl font-bold text-gray-800">Clinical Triage Dashboard</h2>
            {isVerified ? (
              <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-800 rounded-full border border-emerald-300">
                ✓ Verified Clinical Staff
              </span>
            ) : (
              <span className="px-2.5 py-0.5 text-xs font-semibold bg-amber-100 text-amber-800 rounded-full border border-amber-300">
                Pending Verification
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600 mt-1">Real-time prioritized clinical view of campus students and risk alerts.</p>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => navigate('/doctor/appointments')}
            className="px-4 py-2 text-sm text-teal-700 bg-teal-50 border border-teal-200 rounded-md hover:bg-teal-100 transition font-medium"
          >
            Counseling Schedule Queue
          </button>
          <button
            onClick={logout}
            className="px-4 py-2 text-sm text-red-600 border border-red-600 rounded-md hover:bg-red-50 transition"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Verification Warning (if not verified) */}
      {!isVerified && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="text-sm text-amber-900">
            <strong className="font-semibold">Account Unverified:</strong> Clinical verification is required to perform treatment overrides and full patient management.
          </div>
          <button
            onClick={handleVerifySelf}
            className="px-3 py-1.5 bg-amber-600 text-white text-xs font-medium rounded hover:bg-amber-700 transition"
          >
            Verify Account (Demo Mode)
          </button>
        </div>
      )}

      {/* Triage Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Total Patients</span>
          <div className="text-2xl font-bold text-gray-800 mt-1">{patients.length}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-red-100">
          <span className="text-xs font-semibold text-red-600 uppercase tracking-wide">High Risk / Alert</span>
          <div className="text-2xl font-bold text-red-600 mt-1">{highCount}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-amber-100">
          <span className="text-xs font-semibold text-amber-600 uppercase tracking-wide">Moderate Risk</span>
          <div className="text-2xl font-bold text-amber-600 mt-1">{modCount}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-emerald-100">
          <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">Low Risk / Stable</span>
          <div className="text-2xl font-bold text-emerald-600 mt-1">{lowCount}</div>
        </div>
      </div>

      {/* Filter and Control Bar */}
      <div className="bg-white p-4 rounded-lg shadow-sm flex flex-col md:flex-row justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-gray-500">Filter Risk:</span>
          {['all', 'high', 'moderate', 'low', 'unassessed'].map((f) => (
            <button
              key={f}
              onClick={() => setRiskFilter(f)}
              className={`px-3 py-1 text-xs font-medium rounded-full border transition capitalize ${
                riskFilter === f
                  ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-4">
          <input
            type="text"
            placeholder="Search patient pseudonym/email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-xs w-full sm:w-64 focus:ring-teal-500 focus:border-teal-500"
          />

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'risk' | 'recency')}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-xs bg-white text-gray-700"
          >
            <option value="risk">Sort by Priority (Risk)</option>
            <option value="recency">Sort by Last Active</option>
          </select>
        </div>
      </div>

      {error && <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}

      {/* Triage Patient List */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        {loading ? (
          <div className="p-12 text-center text-gray-500 text-sm">Loading patient triage list...</div>
        ) : filteredPatients.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm">No patients match the selected filter criteria.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">Patient Pseudonym / Account</th>
                  <th className="px-6 py-3 font-semibold">Triage Risk Band</th>
                  <th className="px-6 py-3 font-semibold">Latest PHQ-9</th>
                  <th className="px-6 py-3 font-semibold">Latest GAD-7</th>
                  <th className="px-6 py-3 font-semibold">Latest Mood</th>
                  <th className="px-6 py-3 font-semibold">Last Active</th>
                  <th className="px-6 py-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredPatients.map((patient) => (
                  <tr key={patient.user_id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 font-medium text-gray-900">
                      <div>{patient.pseudonym || 'Anonymous Student'}</div>
                      <div className="text-xs text-gray-400 font-normal">{patient.email}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-block px-3 py-1 text-xs font-semibold rounded-full border ${getRiskBadge(
                          patient.risk_level
                        )}`}
                      >
                        {patient.risk_level}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {patient.latest_phq9_score !== undefined && patient.latest_phq9_score !== null ? (
                        <div>
                          <span className="font-semibold text-gray-800">{patient.latest_phq9_score}</span>
                          <span className="text-xs text-gray-500 ml-1">({patient.latest_phq9_severity})</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {patient.latest_gad7_score !== undefined && patient.latest_gad7_score !== null ? (
                        <div>
                          <span className="font-semibold text-gray-800">{patient.latest_gad7_score}</span>
                          <span className="text-xs text-gray-500 ml-1">({patient.latest_gad7_severity})</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">{getMoodEmoji(patient.latest_mood_score)}</td>
                    <td className="px-6 py-4 text-xs text-gray-500">
                      {patient.last_activity ? new Date(patient.last_activity).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => navigate(`/doctor/patient/${patient.user_id}`)}
                        className="px-3 py-1.5 bg-teal-50 text-teal-700 hover:bg-teal-100 rounded text-xs font-medium transition border border-teal-200"
                      >
                        View Patient Context
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
