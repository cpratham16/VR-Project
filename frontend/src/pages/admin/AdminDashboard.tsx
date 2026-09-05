import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import {
  ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  AreaChart, Area, PieChart, Pie, Cell,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';

interface Overview {
  total_patients: number | string;
  suppressed: boolean;
  screening_count: number | null;
  risk_alert_count: number | null;
  vr_sessions_completed: number | null;
  mood_entry_count: number | null;
  phq9_bands: Record<string, number> | null;
  gad7_bands: Record<string, number> | null;
  regions_covered: number;
}

interface TrendRow {
  region: string;
  period: string;
  total_patients: number | string;
  screening_count: number | null;
  risk_alert_count: number | null;
  vr_sessions_completed: number | null;
}

interface SpikeRow {
  region: string;
  period: string;
  alert_rate: number;
  alert_count: number;
  patients: number;
  threshold: number;
}

const PHQ9_COLORS = ['#e6dfc8', '#d8c27e', '#b8860b', '#8a6508', '#5c4304'];
const GAD7_COLORS = ['#e6dfc8', '#d8c27e', '#b8860b', '#5c4304'];
const PIE_COLORS = ['#b8860b', '#d4a84b', '#8a6508', '#c1a75f'];

const ChartTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="space-y-1 rounded-md border border-[#e8e4df] bg-white px-3 py-2 text-xs shadow-md">
      {label && <p className="font-medium text-foreground">{label}</p>}
      {payload.map((p: any, i: number) => (
        <p key={i} className="flex items-center gap-1.5 text-muted-foreground">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color || p.payload?.fill }} />
          <span className="font-semibold text-foreground">{p.name}:</span>
          {p.value?.toLocaleString?.() ?? p.value}
        </p>
      ))}
    </div>
  );
};

const fmt = (value: number | string | null) =>
  typeof value === 'number' ? value.toLocaleString() : (value ?? '—');

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

  const [adminForm, setAdminForm] = useState({ email: '', password: '', full_name: '', state: '', city: '' });
  const [adminSaving, setAdminSaving] = useState(false);
  const [adminMsg, setAdminMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

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
      await fetchAll(selectedRegion || undefined);
    } catch {
      setError('Pipeline execution failed');
    } finally {
      setRefreshing(false);
    }
  };

  const handleRegionChange = (r: string) => {
    setSelectedRegion(r);
    fetchAll(r || undefined);
  };

  const handleAddAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdminSaving(true);
    setAdminMsg(null);
    try {
      await apiClient.post('/admin/users', adminForm);
      setAdminMsg({ type: 'success', text: `Administrator ${adminForm.email} created and verified.` });
      setAdminForm({ email: '', password: '', full_name: '', state: '', city: '' });
    } catch (err: any) {
      setAdminMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to create administrator.' });
    } finally {
      setAdminSaving(false);
    }
  };

  const phq9Data = overview?.phq9_bands
    ? Object.entries(overview.phq9_bands).map(([name, count]) => ({ name, count }))
    : [];
  const gad7Data = overview?.gad7_bands
    ? Object.entries(overview.gad7_bands).map(([name, count]) => ({ name, count }))
    : [];

  const summaryPie = overview
    ? [
        { name: 'Screenings', value: overview.screening_count ?? 0 },
        { name: 'Risk Alerts', value: overview.risk_alert_count ?? 0 },
        { name: 'VR Sessions', value: overview.vr_sessions_completed ?? 0 },
        { name: 'Mood Entries', value: overview.mood_entry_count ?? 0 },
      ]
    : [];

  const statCards = overview
    ? [
        { label: 'Total Patients', value: overview.total_patients },
        { label: 'Screenings', value: overview.screening_count },
        { label: 'Risk Alerts', value: overview.risk_alert_count },
        { label: 'VR Sessions Done', value: overview.vr_sessions_completed },
        { label: 'Mood Entries', value: overview.mood_entry_count },
      ]
    : [];

  const regionOptions = [{ value: '', label: 'All Regions' }, ...regions.map((r) => ({ value: r, label: r }))];

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="small-caps text-accent">Administration</p>
          <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">Analytics Portal</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            Aggregated, anonymized regional health visibility — no individual patient data is ever displayed.
          </p>
        </div>
        <Button onClick={handleRefresh} isLoading={refreshing} disabled={refreshing} size="md">
          {refreshing ? 'Running…' : 'Refresh Analytics (Run Pipeline)'}
        </Button>
      </header>

      {error && (
        <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}

      {pipelineResult && (
        <div role="status" aria-live="polite" className="flex items-center justify-between gap-3 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
          <span>
            Pipeline complete: {pipelineResult.rows_written} region-periods written, {pipelineResult.screening_count} screenings,
            {pipelineResult.risk_alert_count} alerts, {pipelineResult.vr_sessions_completed} VR sessions.
          </span>
          <Button type="button" variant="ghost" size="sm" onClick={() => setPipelineResult(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {/* Region filter */}
      <Card variant="outline">
        <CardContent className="flex flex-wrap items-end gap-4">
          <Select
            aria-label="Filter by region"
            label="Filter by Region"
            value={selectedRegion}
            onChange={(e) => handleRegionChange(e.target.value)}
            options={regionOptions}
            className="min-w-[220px]"
          />
          {regions.length > 0 && (
            <span className="pb-3 text-xs text-muted-foreground">{regions.length} regions in dataset</span>
          )}
        </CardContent>
      </Card>

      {loading ? (
        <div className="py-16 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground/70">Loading analytics</p>
        </div>
      ) : !overview ? (
        <div className="py-16 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground/70">No aggregated data yet</p>
          <p className="mt-2 text-sm text-muted-foreground">Run the pipeline to populate this dashboard.</p>
        </div>
      ) : overview.suppressed ? (
        <Card variant="glass" accentTop>
          <CardHeader>
            <CardTitle>Data suppressed</CardTitle>
            <CardDescription>
              Cohort sizes per region-period fall below the anonymization threshold of 10 patients, so the dashboard hides
              aggregate figures to protect patient identities. Seed additional patients or wait for more activity, then refresh.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Regions covered: <span className="font-semibold text-foreground">{overview.regions_covered}</span>
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            {statCards.map((s) => (
              <Card key={s.label} variant="glass">
                <CardContent className="p-5">
                  <div className="mb-1 flex items-center gap-1">
                    <span aria-hidden="true" className="h-1 w-1 rotate-45 bg-accent" />
                    <span className="small-caps text-muted-foreground">{s.label}</span>
                  </div>
                  <div className="font-display text-3xl font-semibold text-foreground">{fmt(s.value)}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Charts row */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card variant="glass">
              <CardHeader>
                <CardTitle>PHQ-9 Depression Severity Distribution</CardTitle>
                <CardDescription>Patient-reported symptom bands across all regions.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={phq9Data} margin={{ top: 5, right: 16, left: -16, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e4df" />
                      <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#6b6b6b' }} tickLine={false} axisLine={{ stroke: '#e8e4df' }} />
                      <YAxis tick={{ fontSize: 11, fill: '#6b6b6b' }} tickLine={false} axisLine={false} allowDecimals={false} />
                      <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(184, 134, 11, 0.06)' }} />
                      <Bar dataKey="count" name="Patients" radius={[4, 4, 0, 0]}>
                        {phq9Data.map((_, i) => (
                          <Cell key={`phq9-${i}`} fill={PHQ9_COLORS[i % PHQ9_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card variant="glass">
              <CardHeader>
                <CardTitle>GAD-7 Anxiety Severity Distribution</CardTitle>
                <CardDescription>Patient-reported anxiety bands across all regions.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={gad7Data} margin={{ top: 5, right: 16, left: -16, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e4df" />
                      <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#6b6b6b' }} tickLine={false} axisLine={{ stroke: '#e8e4df' }} />
                      <YAxis tick={{ fontSize: 11, fill: '#6b6b6b' }} tickLine={false} axisLine={false} allowDecimals={false} />
                      <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(184, 134, 11, 0.06)' }} />
                      <Bar dataKey="count" name="Patients" radius={[4, 4, 0, 0]}>
                        {gad7Data.map((_, i) => (
                          <Cell key={`gad7-${i}`} fill={GAD7_COLORS[i % GAD7_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Activity breakdown pie + trend */}
          <div className="grid gap-6 lg:grid-cols-3">
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Activity Breakdown</CardTitle>
                <CardDescription>Share of clinical activity across all patients.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={summaryPie}
                        cx="50%" cy="50%" outerRadius={80}
                        dataKey="value" nameKey="name"
                        label={({ name, percent }) => `${name} ${percent != null ? (percent * 100).toFixed(0) : 0}%`}
                        labelLine={false}
                      >
                        {summaryPie.map((_, i) => (
                          <Cell key={`pie-${i}`} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<ChartTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card variant="glass" className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Monthly Volume Trend (by Region)</CardTitle>
                <CardDescription>Screenings, alerts and VR sessions over time.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  {trend.length === 0 ? (
                    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                      No trend data available
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={trend} margin={{ top: 5, right: 16, left: -16, bottom: 5 }}>
                        <defs>
                          <linearGradient id="colorScreenings" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#b8860b" stopOpacity={0.35} />
                            <stop offset="95%" stopColor="#b8860b" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e4df" />
                        <XAxis dataKey="period" tick={{ fontSize: 10, fill: '#6b6b6b' }} tickLine={false} axisLine={{ stroke: '#e8e4df' }} />
                        <YAxis tick={{ fontSize: 11, fill: '#6b6b6b' }} tickLine={false} axisLine={false} allowDecimals={false} />
                        <Tooltip content={<ChartTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '11px', color: '#6b6b6b' }} />
                        <Area type="monotone" dataKey="screening_count" name="Screenings" stroke="#b8860b" fill="url(#colorScreenings)" strokeWidth={2} />
                        <Area type="monotone" dataKey="risk_alert_count" name="Alerts" stroke="#8a6508" fill="#d8c27e" fillOpacity={0.15} strokeWidth={2} />
                        <Area type="monotone" dataKey="vr_sessions_completed" name="VR Sessions" stroke="#d4a84b" fill="#e6dfc8" fillOpacity={0.2} strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Spike alerts */}
          <Card variant="glass">
            <CardHeader className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>Spike / Anomaly Alerts</CardTitle>
                <CardDescription>Regions whose alert rate exceeds two standard deviations above their mean.</CardDescription>
              </div>
              {spikes.length > 0 && (
                <span className="rounded-full border border-[#e8e4df] bg-muted px-3 py-1 small-caps text-accent">
                  {spikes.length} detected
                </span>
              )}
            </CardHeader>
            <CardContent>
              {spikes.length === 0 ? (
                <p className="py-6 text-center text-sm text-muted-foreground">
                  No anomalies detected across any region or period.
                </p>
              ) : (
                <div className="divide-y divide-[#e8e4df]">
                  {spikes.map((s, i) => (
                    <article key={i} className="flex flex-wrap items-center justify-between gap-3 py-4 first:pt-0 last:pb-0">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="rounded-full border border-[#e8e4df] bg-muted px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-accent">
                            Spike
                          </span>
                          <span className="text-sm font-semibold text-foreground">{s.region}</span>
                          <span className="text-xs text-muted-foreground">{s.period}</span>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          Alert rate: <span className="font-semibold text-foreground">{(s.alert_rate * 100).toFixed(1)}%</span> ({s.alert_count} alerts / {s.patients} patients) — threshold: {(s.threshold * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="font-display text-2xl font-semibold text-foreground">{s.alert_count}</div>
                        <div className="small-caps text-muted-foreground">Critical + High</div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Administrator account management */}
      <Card variant="glass" accentTop>
        <CardHeader>
          <CardTitle>Administrator Accounts</CardTitle>
          <CardDescription>
            Provision a new admin account. Admins are created and verified here — self-registration never grants the admin role.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {adminMsg && (
            <div
              role={adminMsg.type === 'error' ? 'alert' : 'status'}
              className={`mb-4 rounded-md border px-4 py-3 text-sm font-medium ${
                adminMsg.type === 'error'
                  ? 'border-red-200 bg-red-50 text-red-700'
                  : 'border-emerald-200 bg-emerald-50 text-emerald-700'
              }`}
            >
              {adminMsg.text}
            </div>
          )}
          <form onSubmit={handleAddAdmin} className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Email address"
              type="email"
              required
              value={adminForm.email}
              onChange={(e) => setAdminForm({ ...adminForm, email: e.target.value })}
            />
            <Input
              label="Temporary password"
              type="password"
              required
              minLength={8}
              value={adminForm.password}
              onChange={(e) => setAdminForm({ ...adminForm, password: e.target.value })}
            />
            <Input
              label="Full name"
              value={adminForm.full_name}
              onChange={(e) => setAdminForm({ ...adminForm, full_name: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="State"
                value={adminForm.state}
                onChange={(e) => setAdminForm({ ...adminForm, state: e.target.value })}
              />
              <Input
                label="City"
                value={adminForm.city}
                onChange={(e) => setAdminForm({ ...adminForm, city: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <Button type="submit" isLoading={adminSaving} disabled={adminSaving}>
                {adminSaving ? 'Creating…' : 'Create Administrator'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}