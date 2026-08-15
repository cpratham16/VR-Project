import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import {
  ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  AreaChart, Area, PieChart, Pie, Cell,
} from 'recharts';

interface Overview {
  total_patients: number;
  screening_count: number;
  risk_alert_count: number;
  vr_sessions_completed: number;
  mood_entry_count: number;
  phq9_bands: Record<string, number>;
  gad7_bands: Record<string, number>;
  regions_covered: number;
}

interface TrendRow {
  region: string;
  period: string;
  total_patients: number;
  screening_count: number;
  risk_alert_count: number;
  vr_sessions_completed: number;
}

interface SpikeRow {
  region: string;
  period: string;
  alert_rate: number;
  alert_count: number;
  patients: number;
  threshold: number;
}

const PHQ9_COLORS = ['#34d399', '#60a5fa', '#fbbf24', '#f97316', '#ef4444'];
const GAD7_COLORS = ['#34d399', '#60a5fa', '#f97316', '#ef4444'];
const PIE_COLORS = ['#6366f1', '#22d3ee', '#f43f5e', '#f59e0b'];

export default function AdminDashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [trend, setTrend] = useState<TrendRow[]>([]);
  const [spikes, setSpikes] = useState<SpikeRow[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState('');

  const fetchAll = async (regionFilter?: string) => {
    setLoading(true);
    setError('');
    try {
      const [oRes, tRes, sRes, rRes] = await Promise.all([
        apiClient.get('/admin/analytics/overview'),
        apiClient.get(`/admin/analytics/trend${regionFilter ? `?region=${encodeURIComponent(regionFilter)}` : ''}`),
        apiClient.get('/admin/analytics/spikes'),
        apiClient.get('/admin/analytics/regions'),
      ]);
      setOverview(oRes.data);
      setTrend(tRes.data);
      setSpikes(sRes.data);
      setRegions(rRes.data);
    } catch {
      setError('Unable to load analytics. Run the anonymization pipeline first.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError('');
    try {
      const res = await apiClient.post('/admin/analytics/run-pipeline');
      setPipelineResult(res.data);
      await fetchAll(selectedRegion);
    } catch {
      setError('Pipeline execution failed');
    } finally {
      setRefreshing(false);
    }
  };

  const handleRegionChange = async (r: string) => {
    setSelectedRegion(r);
    await fetchAll(r || undefined);
  };

  const phq9Data = overview
    ? Object.entries(overview.phq9_bands).map(([band, count]) => ({ name: band, count }))
    : [];
  const gad7Data = overview
    ? Object.entries(overview.gad7_bands).map(([band, count]) => ({ name: band, count }))
    : [];

  const summaryPie = overview
    ? [
        { name: 'Screenings', value: overview.screening_count },
        { name: 'Risk Alerts', value: overview.risk_alert_count },
        { name: 'VR Sessions', value: overview.vr_sessions_completed },
        { name: 'Mood Entries', value: overview.mood_entry_count },
      ]
    : [];

  return (
    <div className="max-w-7xl mx-auto space-y-6 px-4 py-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 rounded-2xl shadow-lg text-white flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-3xl">📊</span>
            <h1 className="text-2xl font-bold">Administrative Analytics Portal</h1>
          </div>
          <p className="text-sm text-indigo-200 mt-1">
            Aggregated, anonymized regional health visibility — no individual patient data is ever displayed.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          aria-label={refreshing ? 'Running the anonymization pipeline' : 'Refresh analytics by running the anonymization pipeline'}
          className="bg-white/20 hover:bg-white/30 backdrop-blur text-white font-bold px-6 py-3 rounded-xl cursor-pointer disabled:opacity-50 flex items-center gap-2"
        >
          {refreshing ? '⏳ Running...' : '🔄 Refresh Analytics (Run Pipeline)'}
        </button>
      </div>

      {error && <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">{error}</div>}

      {pipelineResult && (
        <div role="status" aria-live="polite" className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm flex items-center justify-between">
          <span>✓ Pipeline complete: {pipelineResult.rows_written} region-periods written, {pipelineResult.screening_count} screenings, {pipelineResult.risk_alert_count} alerts, {pipelineResult.vr_sessions_completed} VR sessions.</span>
          <button onClick={() => setPipelineResult(null)} className="text-emerald-600 font-bold cursor-pointer">✕</button>
        </div>
      )}

      {/* Region filter */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
        <label htmlFor="region-filter" className="text-xs font-bold text-gray-600">Filter by Region:</label>
        <select
          id="region-filter"
          value={selectedRegion}
          onChange={(e) => handleRegionChange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-xl text-sm bg-white min-w-[200px]"
        >
          <option value="">All Regions</option>
          {regions.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        {regions.length > 0 && <span className="text-xs text-gray-400">{regions.length} regions in dataset</span>}
      </div>

      {loading ? (
        <div className="bg-white p-12 rounded-2xl text-center text-gray-400 text-sm">Loading analytics...</div>
      ) : !overview || overview.screening_count === 0 ? (
        <div className="bg-white p-12 rounded-2xl text-center border border-gray-100 space-y-3">
          <div className="text-4xl">📋</div>
          <p className="text-gray-700 font-medium">No aggregated data yet.</p>
          <p className="text-sm text-gray-400">Click <strong>Refresh Analytics</strong> to run the anonymization pipeline and populate this dashboard.</p>
        </div>
      ) : (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: 'Total Patients', value: overview.total_patients, color: 'text-indigo-600', icon: '👥' },
              { label: 'Screenings', value: overview.screening_count, color: 'text-cyan-600', icon: '📝' },
              { label: 'Risk Alerts', value: overview.risk_alert_count, color: 'text-rose-600', icon: '🚨' },
              { label: 'VR Sessions Done', value: overview.vr_sessions_completed, color: 'text-emerald-600', icon: '🥽' },
              { label: 'Mood Entries', value: overview.mood_entry_count, color: 'text-amber-600', icon: '😊' },
            ].map((s) => (
              <div key={s.label} className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
                <div className="text-xs text-gray-500 uppercase tracking-wide flex items-center gap-1">
                  <span>{s.icon}</span> {s.label}
                </div>
                <div className={`text-3xl font-black mt-1 ${s.color}`}>{s.value.toLocaleString()}</div>
              </div>
            ))}
          </div>

          {/* Charts row */}
          <div className="grid lg:grid-cols-2 gap-6">
            {/* PHQ-9 band distribution */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-4">PHQ-9 Depression Severity Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={phq9Data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {phq9Data.map((_, i) => (
                        <Cell key={`phq9-${i}`} fill={PHQ9_COLORS[i % PHQ9_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* GAD-7 band distribution */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-4">GAD-7 Anxiety Severity Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={gad7Data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {gad7Data.map((_, i) => (
                        <Cell key={`gad7-${i}`} fill={GAD7_COLORS[i % GAD7_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Activity breakdown pie + summary list */}
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-4">Activity Breakdown</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={summaryPie}
                      cx="50%" cy="50%" outerRadius={80}
                      dataKey="value" label={({ name, percent }) => `${name} ${percent != null ? (percent * 100).toFixed(0) : 0}%`}
                      labelLine={false}
                    >
                      {summaryPie.map((_, i) => (
                        <Cell key={`pie-${i}`} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Trend area chart */}
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-4">Monthly Volume Trend (by Region)</h3>
              <div className="h-64">
                {trend.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-sm text-gray-400">No trend data available</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trend} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="period" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Area type="monotone" dataKey="screening_count" name="Screenings" stroke="#06b6d4" fill="#ecfeff" strokeWidth={2} />
                      <Area type="monotone" dataKey="risk_alert_count" name="Alerts" stroke="#f43f5e" fill="#fff1f2" strokeWidth={2} />
                      <Area type="monotone" dataKey="vr_sessions_completed" name="VR Sessions" stroke="#8b5cf6" fill="#ede9fe" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>

          {/* Spike alerts */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide flex items-center gap-2">
                ⚡ Spike / Anomaly Alerts
                {spikes.length > 0 && (
                  <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-0.5 rounded-full">{spikes.length}</span>
                )}
              </h3>
            </div>
            {spikes.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-400">No anomalies detected across any region or period.</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {spikes.map((s, i) => (
                  <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="bg-red-100 text-red-700 text-[10px] font-bold px-2 py-0.5 rounded">⚠ SPIKE</span>
                        <span className="text-sm font-bold text-gray-900">{s.region}</span>
                        <span className="text-xs text-gray-400">{s.period}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Alert rate: <strong>{(s.alert_rate * 100).toFixed(1)}%</strong> ({s.alert_count} alerts / {s.patients} patients) — threshold: {(s.threshold * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-black text-red-600">{s.alert_count}</div>
                      <div className="text-[10px] text-gray-400">CRITICAL+HIGH</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
