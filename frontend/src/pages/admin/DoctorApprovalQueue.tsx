import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { Card, CardContent, Button, Badge, Container, SectionHeading } from '../../components/ui';

interface DoctorRow {
  user_id: string;
  email: string;
  full_name: string | null;
  state: string | null;
  city: string | null;
  is_verified: boolean;
  has_credentials: boolean;
  license_number: string | null;
  specialty: string | null;
  languages: string[];
  review_status: 'pending' | 'approved' | 'rejected' | null;
  rejection_reason: string | null;
  uploaded_at: string | null;
}

const TABS = [
  { key: 'pending', label: 'Pending review' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
] as const;

export default function DoctorApprovalQueue() {
  const [doctors, setDoctors] = useState<DoctorRow[]>([]);
  const [tab, setTab] = useState<'pending' | 'approved' | 'rejected'>('pending');
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState('');
  const [rejecting, setRejecting] = useState<DoctorRow | null>(null);
  const [reason, setReason] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);

  const fetchDoctors = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/admin/doctors');
      setDoctors(res.data);
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to load doctor registrations.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDoctors();
  }, [fetchDoctors]);

  const approve = async (doc: DoctorRow) => {
    setBusyId(doc.user_id);
    setActionError('');
    try {
      await apiClient.post(`/admin/doctors/${doc.user_id}/approve`, {});
      await fetchDoctors();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Approve failed.');
    } finally {
      setBusyId(null);
    }
  };

  const reject = async () => {
    if (!rejecting) return;
    if (!reason.trim()) {
      setActionError('A rejection reason is required.');
      return;
    }
    setBusyId(rejecting.user_id);
    setActionError('');
    try {
      await apiClient.post(`/admin/doctors/${rejecting.user_id}/reject`, { reason: reason.trim() });
      setRejecting(null);
      setReason('');
      await fetchDoctors();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Reject failed.');
    } finally {
      setBusyId(null);
    }
  };

  const downloadCredential = async (doc: DoctorRow) => {
    try {
      const res = await apiClient.get(`/admin/doctors/${doc.user_id}/credential`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = doc.license_number ? `${doc.license_number}-credential` : 'credential';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setActionError('Could not download the credential document.');
    }
  };

  const filtered = doctors.filter((d) => (d.review_status ?? 'pending') === tab);

  return (
    <Container className="py-10">
      <SectionHeading
        eyebrow="Administration"
        title="Doctor approval queue"
        description="Review credential submissions before granting doctors patient visibility and clinical access."
        className="mb-8"
      />

      {actionError && (
        <div role="alert" className="mb-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
          {actionError}
        </div>
      )}

      <div className="mb-6 flex gap-2">
        {TABS.map((t) => {
          const count = doctors.filter((d) => (d.review_status ?? 'pending') === t.key).length;
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              aria-pressed={tab === t.key}
              className={`cursor-pointer rounded-xl px-4 py-2 text-sm font-semibold transition-all ${
                tab === t.key
                  ? 'bg-teal-600 text-white shadow-sm shadow-teal-600/25'
                  : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
              }`}
            >
              {t.label}{' '}
              <span className={`ml-1 rounded-full px-1.5 text-xs ${tab === t.key ? 'bg-white/20' : 'bg-slate-100'}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <p className="text-sm text-slate-400">Loading registrations…</p>
      ) : filtered.length === 0 ? (
        <Card variant="outline" className="p-10 text-center">
          <p className="text-sm text-slate-500">No doctors in this queue.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {filtered.map((doc) => (
            <Card key={doc.user_id} variant="elevated">
              <CardContent className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[15px] font-bold text-slate-900">{doc.full_name || doc.email}</span>
                    {!doc.has_credentials && <Badge variant="warning" size="sm">No document</Badge>}
                    {doc.review_status === 'rejected' && <Badge variant="danger" size="sm">Rejected</Badge>}
                    {doc.review_status === 'approved' && <Badge variant="success" size="sm" dot>Approved</Badge>}
                  </div>
                  <p className="text-xs text-slate-500">{doc.email}</p>
                  <p className="text-xs text-slate-500">
                    📍 {[doc.city, doc.state].filter(Boolean).join(', ') || '—'}
                    {doc.specialty ? ` · ${doc.specialty}` : ''}
                    {doc.license_number ? ` · License ${doc.license_number}` : ''}
                  </p>
                  {doc.languages.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-0.5">
                      {doc.languages.map((l) => (
                        <span key={l} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">{l}</span>
                      ))}
                    </div>
                  )}
                  {doc.review_status === 'rejected' && doc.rejection_reason && (
                    <p className="rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">Reason: {doc.rejection_reason}</p>
                  )}
                </div>

                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!doc.has_credentials}
                    onClick={() => downloadCredential(doc)}
                  >
                    📄 Credential
                  </Button>
                  {tab !== 'approved' && (
                    <Button variant="primary" size="sm" isLoading={busyId === doc.user_id} onClick={() => approve(doc)}>
                      Approve
                    </Button>
                  )}
                  {tab !== 'rejected' && (
                    <Button variant="danger" size="sm" onClick={() => { setRejecting(doc); setReason(''); }}>
                      Reject
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {rejecting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label="Reject doctor">
          <Card variant="elevated" className="w-full max-w-md p-6">
            <h3 className="text-base font-bold text-slate-900">Reject {rejecting.full_name || rejecting.email}</h3>
            <p className="mt-1 text-xs text-slate-500">The doctor will see this feedback and can re-submit a corrected document.</p>
            <textarea
              rows={3}
              autoFocus
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. License number could not be verified with the state medical council."
              className="mt-4 w-full resize-y rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm focus:border-teal-500 focus:outline-none focus:ring-4 focus:ring-teal-500/15"
            />
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => { setRejecting(null); setReason(''); }}>
                Cancel
              </Button>
              <Button variant="danger" size="sm" isLoading={busyId === rejecting.user_id} onClick={reject}>
                Reject registration
              </Button>
            </div>
          </Card>
        </div>
      )}
    </Container>
  );
}
