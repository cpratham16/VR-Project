import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { apiClient } from '../../../api/client';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { Select } from '../../../components/ui/Select';
import { STATE_OPTIONS, LANGUAGE_OPTIONS } from '../../../constants/regions';

const SPECIALTIES = [
  'Psychiatrist',
  'Clinical Psychologist',
  'Counselor / Therapist',
  'Psychiatric Social Worker',
  'Other',
];

interface FormState {
  full_name: string;
  phone: string;
  emergency_contact_phone: string;
  state: string;
  city: string;
  specialty: string;
  languages: string[];
}

interface FormErrors {
  phone?: string;
  emergency_contact_phone?: string;
  languages?: string;
}

export default function UpdateProfilePage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState<FormState>({
    full_name: user?.full_name ?? '',
    phone: user?.phone ?? '',
    emergency_contact_phone: user?.emergency_contact_phone ?? '',
    state: user?.state ?? '',
    city: user?.city ?? '',
    specialty: user?.specialty ?? '',
    languages: Array.isArray(user?.languages) ? user?.languages : [],
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const isPatient = user?.role === 'patient';

  const set = (key: keyof FormState, value: string | string[]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const validate = (): boolean => {
    const next: FormErrors = {};
    const phoneRe = /^\+?[0-9]{10,13}$/;
    if (form.phone && !phoneRe.test(form.phone.replace(/[\s-]/g, ''))) {
      next.phone = 'Enter a valid 10–13 digit phone number.';
    }
    if (form.emergency_contact_phone && !phoneRe.test(form.emergency_contact_phone.replace(/[\s-]/g, ''))) {
      next.emergency_contact_phone = 'Enter a valid 10–13 digit phone number.';
    }
    if (!isPatient && form.languages.length === 0) {
      next.languages = 'Select at least one language you counsel in.';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    try {
      const payload: Record<string, string | string[]> = {
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        emergency_contact_phone: form.emergency_contact_phone.trim(),
        state: form.state,
        city: form.city.trim(),
      };
      if (!isPatient) {
        payload.specialty = form.specialty;
        payload.languages = form.languages;
      }
      const res = await apiClient.put('/auth/me', payload);
      setUser(res.data);
      setSaved(true);
    } catch (err: unknown) {
      const detail =
        typeof err === 'object' && err !== null && 'response' in err
          ? String((err as { response: { data?: { detail?: unknown } } }).response?.data?.detail ?? '')
          : '';
      setErrors({ phone: detail || 'Could not save changes. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-8">
        <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">Profile & Contact Info</h1>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted-foreground">
          Keep your contact details and professional information up to date. Changes save instantly and show up
          across your {isPatient ? 'care team' : 'patient-facing'} profile.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6">
        <section className="card-editorial space-y-5 p-6 sm:p-8">
          <h2 className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-accent">
            Personal details
          </h2>

          <Input
            label="Full name"
            required
            id="profile-full-name"
            value={form.full_name}
            onChange={(e) => set('full_name', e.target.value)}
            placeholder="Your full name"
          />

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <Select
              label="State"
              placeholder="Select your state"
              options={STATE_OPTIONS}
              value={form.state || ''}
              onChange={(e) => set('state', e.target.value)}
            />
            <Input
              label="City"
              id="profile-city"
              value={form.city}
              onChange={(e) => set('city', e.target.value)}
              placeholder="Your city"
            />
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <Input
              label="Phone number"
              id="profile-phone"
              value={form.phone}
              onChange={(e) => set('phone', e.target.value)}
              error={errors.phone}
              placeholder="e.g. +91 98765 43210"
              helperText={`Only visible to your ${isPatient ? 'care team' : 'patients and admins'}.`}
            />
            <Input
              label="Emergency contact phone"
              id="profile-emergency-phone"
              value={form.emergency_contact_phone}
              onChange={(e) => set('emergency_contact_phone', e.target.value)}
              error={errors.emergency_contact_phone}
              placeholder="e.g. +91 98765 43210"
              helperText="Used if we need to reach someone for you."
            />
          </div>
        </section>

        {!isPatient && (
          <section className="card-editorial space-y-5 p-6 sm:p-8">
            <h2 className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-accent">
              Professional details
            </h2>
            <Select
              label="Specialty"
              placeholder="Select your specialty"
              options={SPECIALTIES.map((sp) => ({ value: sp, label: sp }))}
              value={form.specialty}
              onChange={(e) => set('specialty', e.target.value)}
              helperText="Shown on your profile."
            />
            <div>
              <span className="mb-2 block font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                Languages you counsel in <span className="ml-1 text-accent">*</span>
              </span>
              <div className="flex flex-wrap gap-2">
                {LANGUAGE_OPTIONS.map((lang) => {
                  const active = form.languages.includes(lang.value);
                  return (
                    <button
                      key={lang.value}
                      type="button"
                      aria-pressed={active}
                      onClick={() =>
                        set(
                          'languages',
                          active
                            ? form.languages.filter((l) => l !== lang.value)
                            : [...form.languages, lang.value]
                        )
                      }
                      className={`cursor-pointer rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-all ${
                        active
                          ? 'border-accent bg-accent text-white'
                          : 'border-[#e8e4df] bg-white text-muted-foreground hover:border-[#d6cfc7] hover:bg-muted'
                      }`}
                    >
                      {lang.label}
                    </button>
                  );
                })}
              </div>
              {errors.languages && <p className="mt-1.5 text-xs font-medium text-red-700">{errors.languages}</p>}
            </div>
          </section>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" isLoading={saving} disabled={saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </Button>
          <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
            Cancel
          </Button>
          {saved && (
            <span className="flex items-center gap-1.5 text-sm font-medium text-emerald-700" role="status">
              Saved successfully
            </span>
          )}
        </div>
      </form>
    </div>
  );
}