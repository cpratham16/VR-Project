import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Badge,
  Input,
  Textarea,
  SectionHeading,
} from '../../components/ui';
import { LANGUAGES_SPOKEN } from '../../constants/regions';

interface DoctorCard {
  id: string;
  full_name: string | null;
  specialty: string | null;
  languages: string[];
  city: string | null;
  state: string | null;
}

interface DoctorDirectory {
  patient_location: { city: string | null; state: string | null };
  broadened: boolean;
  language_filter: string | null;
  doctors: DoctorCard[];
}

interface Appointment {
  id: string;
  doctor_id?: string | null;
  scheduled_at: string;
  status: string;
  reason?: string | null;
  preferred_mode?: string | null;
  created_at: string;
  doctor_name?: string | null;
  doctor_specialty?: string | null;
  doctor_city?: string | null;
  doctor_state?: string | null;
}

const STATUS_VARIANT: Record<string, 'success' | 'warning' | 'info' | 'danger' | 'neutral'> = {
  confirmed: 'success',
  requested: 'warning',
  completed: 'info',
  cancelled: 'danger',
  no_show: 'danger',
  waitlisted: 'neutral',
};

export default function PatientAppointmentsPage() {
  const [directory, setDirectory] = useState<DoctorDirectory | null>(null);
  const [broaden, setBroaden] = useState(false);
  const [languageFilter, setLanguageFilter] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorCard | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [scheduledAt, setScheduledAt] = useState('');
  const [reason, setReason] = useState('');
  const [preferredMode, setPreferredMode] = useState('any');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchAppointments();
  }, []);

  useEffect(() => {
    fetchDoctors(broaden, languageFilter);
    setSelectedDoctor(null);
  }, [broaden, languageFilter]);

  const fetchDoctors = async (withBroaden: boolean, withLanguage: string) => {
    try {
      let url = `/patient/doctors?broaden=${withBroaden}`;
      if (withLanguage) url += `&language=${encodeURIComponent(withLanguage)}`;
      const res = await apiClient.get(url);
      setDirectory(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load counselors.');
    }
  };

  const fetchAppointments = async () => {
    setFetching(true);
    setError('');
    try {
      const res = await apiClient.get('/patient/appointments');
      setAppointments(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load appointments.');
    } finally {
      setFetching(false);
    }
  };

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!scheduledAt) {
      setError('Please select a date and time.');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/patient/appointments', {
        scheduled_at: new Date(scheduledAt).toISOString(),
        reason: reason,
        doctor_id: selectedDoctor ? selectedDoctor.id : undefined,
        preferred_mode: preferredMode,
      });
      setSuccess(
        selectedDoctor
          ? `Request sent to ${selectedDoctor.full_name}. You'll be notified once confirmed.`
          : 'Appointment request submitted successfully!'
      );
      setScheduledAt('');
      setReason('');
      setSelectedDoctor(null);
      await fetchAppointments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to book appointment.');
    } finally {
      setLoading(false);
    }
  };

  const loc = directory?.patient_location;
  const localCount = directory
    ? directory.doctors.filter((d) => loc?.state && d.state === loc.state).length
    : 0;

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <SectionHeading
        eyebrow="Appointments"
        title="Schedule a counseling session"
        description="Choose a verified counselor and request a slot that works for you."
      />

      {error && (
        <div role="alert" className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
          ✓ {success}
        </div>
      )}

      {/* Main layout: Left sidebar (Doctor directory) + Right panel (Booking form) */}
      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        {/* Left: Doctor Directory */}
        <aside className="lg:sticky lg:top-24 space-y-6">
          <section className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-base font-bold text-slate-900">Choose your counselor</h3>
              <button
                onClick={() => setBroaden((b) => !b)}
                className="cursor-pointer rounded-full border border-[#e8e4df] bg-muted px-4 py-1.5 text-xs font-bold text-accent transition-colors hover:bg-teal-100"
                aria-pressed={broaden}
              >
                {broaden ? '← Back to my region only' : `Show counselors in other regions${loc?.state ? ` (outside ${loc.state})` : ''}`}
              </button>
            </div>

            {loc && (loc.city || loc.state) && (
              <p className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                📍{' '}
                {broaden ? (
                  <>Showing all regions — counselors near <span className="font-semibold text-slate-700">{[loc.city, loc.state].filter(Boolean).join(', ')}</span> are listed first</>
                ) : (
                  <>Showing counselors near <span className="font-semibold text-slate-700">{[loc.city, loc.state].filter(Boolean).join(', ')}</span></>
                )}
                {!broaden && localCount === 0 && (
                  <span className="text-amber-600">· none in your area yet — broaden to see everyone</span>
                )}
              </p>
            )}

            <div className="space-y-2">
              <p className="text-[11px] font-bold uppercase tracking-[0.08em] text-slate-600">
                Filter by language spoken
                {languageFilter && (
                  <button
                    onClick={() => setLanguageFilter('')}
                    className="ml-2 cursor-pointer rounded-full bg-teal-600 px-2.5 py-0.5 text-[10px] font-bold normal-case tracking-normal text-white transition-colors hover:bg-accent-secondary"
                  >
                    {languageFilter} ✕
                  </button>
                )}
              </p>
              <div className="flex flex-wrap gap-1.5" role="group" aria-label="Language filter">
                {LANGUAGES_SPOKEN.map((lang) => {
                  const active = languageFilter === lang;
                  return (
                    <button
                      key={lang}
                      onClick={() => setLanguageFilter(active ? '' : lang)}
                      aria-pressed={active}
                      className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-semibold transition-all ${
                        active
                          ? 'border-accent bg-accent text-white shadow-sm'
                          : 'border-[#e8e4df] bg-white text-slate-600 hover:border-[#d6cfc7] hover:bg-muted'
                      }`}
                    >
                      {lang}
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Doctor cards list */}
          <section className="space-y-3">
            {!directory ? (
              <p className="text-sm text-slate-400">Loading counselors…</p>
            ) : directory.doctors.length === 0 ? (
              <Card variant="outline" className="p-8 text-center">
                <p className="text-sm text-slate-500">
                  {languageFilter ? (
                    <>
                      No <span className="font-semibold text-slate-700">{languageFilter}</span>-speaking counselors found{' '}
                      {broaden ? 'anywhere yet.' : 'in your region yet — try broadening the search to other regions.'}
                    </>
                  ) : (
                    'No verified counselors found in your area yet. Try broadening the search to other regions.'
                  )}
                </p>
              </Card>
            ) : (
              <div className="space-y-2">
                {directory.doctors.map((doc) => {
                  const isSelected = selectedDoctor?.id === doc.id;
                  const isLocal = !!loc?.state && doc.state === loc.state && !!loc?.city && doc.city === loc.city;
                  return (
                    <Card
                      key={doc.id}
                      hoverEffect
                      onClick={() => setSelectedDoctor(isSelected ? null : doc)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setSelectedDoctor(isSelected ? null : doc)}
                      aria-pressed={isSelected}
                      className={`cursor-pointer ${isSelected ? 'border-teal-500 ring-2 ring-accent/20/25' : ''}`}
                    >
                      <CardHeader className="pb-3">
                        <div className="mb-2 flex items-start justify-between gap-2">
                          <span aria-hidden="true" className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-muted to-[#efe9df] text-lg">
                            🩺
                          </span>
                          <Badge variant={isSelected ? 'primary' : isLocal ? 'success' : 'neutral'} size="sm" dot={isSelected}>
                            {isSelected ? 'Selected' : isLocal ? 'Near you' : broaden ? 'Other region' : 'Your state'}
                          </Badge>
                        </div>
                        <CardTitle className="text-[15px]">{doc.full_name || 'Counselor'}</CardTitle>
                        <CardDescription className="text-xs">
                          {doc.specialty || 'Mental health professional'}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-2 pt-0">
                        <p className="flex items-center gap-1 text-xs font-medium text-slate-500">📍 {[doc.city, doc.state].filter(Boolean).join(', ')}</p>
                        {doc.languages.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {doc.languages.map((lang) => (
                              <span key={lang} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
                                {lang}
                              </span>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </section>
        </aside>

        {/* Right: Booking Form */}
        <main className="space-y-6">
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Request a session</CardTitle>
              <CardDescription>
                {selectedDoctor
                  ? `Your request will go directly to ${selectedDoctor.full_name}.`
                  : 'No counselor selected — the platform will match you with an available professional.'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleBook} className="space-y-4">
                <Input
                  label="Preferred date & time"
                  required
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={(e) => setScheduledAt(e.target.value)}
                  className="sm:max-w-xs"
                />
                <Textarea
                  label="Reason / session notes"
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Follow-up on PHQ-9 results, coping strategies, or stress management..."
                />
                <div className="max-w-xs">
                  <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.08em] text-slate-600">
                    Preferred mode
                  </label>
                  <select
                    value={preferredMode}
                    onChange={(e) => setPreferredMode(e.target.value)}
                    className="w-full cursor-pointer appearance-none rounded-md border border-slate-200 bg-white px-3.5 py-2.5 text-sm shadow-xs transition-all hover:border-slate-300 focus:border-accent focus:outline-none focus:ring-4 focus:ring-accent/15"
                  >
                    <option value="any">No preference</option>
                    <option value="in_person">In person</option>
                    <option value="video_call">Video call</option>
                    <option value="chat">Chat consultation</option>
                  </select>
                </div>
                <Button type="submit" isLoading={loading} size="lg" className="w-full">
                  Submit appointment request
                </Button>
              </form>
            </CardContent>
          </Card>
        </main>
      </div>

      {/* Bottom: My Appointments */}
      <section className="space-y-4">
        <h3 className="text-base font-bold text-slate-900">My appointments</h3>
        {fetching ? (
          <p className="text-sm text-slate-400">Loading appointments…</p>
        ) : appointments.length === 0 ? (
          <Card variant="outline" className="p-8 text-center">
            <p className="text-sm text-slate-500">No appointments yet — request your first session above.</p>
          </Card>
        ) : (
          <div className="space-y-3">
            {appointments.map((appt) => (
              <Card key={appt.id} variant="default" className="p-4">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-slate-900">
                        {new Date(appt.scheduled_at).toLocaleString(undefined, {
                          weekday: 'short',
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      <Badge variant={STATUS_VARIANT[appt.status] ?? 'neutral'} size="sm">
                        {appt.status.replace('_', ' ')}
                      </Badge>
                    </div>
                    {appt.doctor_name ? (
                      <p className="text-xs text-slate-500">
                        with <span className="font-semibold text-slate-700">{appt.doctor_name}</span>
                        {appt.doctor_specialty ? ` · ${appt.doctor_specialty}` : ''}
                        {(appt.doctor_city || appt.doctor_state) && ` · 📍 ${[appt.doctor_city, appt.doctor_state].filter(Boolean).join(', ')}`}
                      </p>
                    ) : (
                      <p className="text-xs italic text-slate-400">Awaiting counselor assignment</p>
                    )}
                    {appt.reason && <p className="text-xs italic text-slate-500">"{appt.reason}"</p>}
                  </div>
                  <span className="text-[11px] text-slate-400">
                    Requested {new Date(appt.created_at).toLocaleDateString()}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}