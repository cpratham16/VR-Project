import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import {
  Card,
  Button,
  Badge,
  Input,
  Select,
  Checkbox,
  Stepper,
} from '../../components/ui';
import { STATE_OPTIONS, LANGUAGE_OPTIONS } from '../../constants/regions';

type Role = 'patient' | 'doctor';

interface DraftForm {
  role: Role;
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  phone: string;
  emergencyContactPhone: string;
  state: string;
  city: string;
  ageGroup: string;
  gender: string;
  licenseNumber: string;
  specialty: string;
  languages: string[];
  agreeTerms: boolean;
  agreePrivacy: boolean;
  agreeAiDisclosure: boolean;
  agreeCrisisPolicy: boolean;
}

const INITIAL_DRAFT: DraftForm = {
  role: 'patient',
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  phone: '',
  emergencyContactPhone: '',
  state: '',
  city: '',
  ageGroup: '',
  gender: '',
  licenseNumber: '',
  specialty: '',
  languages: [],
  agreeTerms: false,
  agreePrivacy: false,
  agreeAiDisclosure: false,
  agreeCrisisPolicy: false,
};

const STEPS = [
  { id: 1, label: 'Account' },
  { id: 2, label: 'Contact' },
  { id: 3, label: 'Profile' },
  { id: 4, label: 'Consent' },
  { id: 5, label: 'Confirm' },
];

const DRAFT_KEY = 'vrmh-signup-draft';

const AGE_GROUPS = ['Under 18', '18-24', '25-34', '35-44', '45-54', '55+', 'Prefer not to say'];
const GENDERS = ['Female', 'Male', 'Non-binary', 'Prefer not to say'];
const SPECIALTIES = ['Psychiatrist', 'Clinical Psychologist', 'Counselor / Therapist', 'Psychiatric Social Worker', 'Other'];

const digitsOnly = (v: string) => v.replace(/\D/g, '');

export default function Signup() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<DraftForm>(INITIAL_DRAFT);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [restored, setRestored] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(DRAFT_KEY);
      if (raw) {
        const saved = JSON.parse(raw) as { step: number; form: DraftForm };
        if (saved?.form?.email !== undefined) {
          setForm({ ...INITIAL_DRAFT, ...saved.form });
          setStep(Math.min(Math.max(saved.step || 1, 1), 5));
          setRestored(true);
        }
      }
    } catch {
      sessionStorage.removeItem(DRAFT_KEY);
    }
  }, []);

  useEffect(() => {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ step, form }));
  }, [step, form]);

  const set = <K extends keyof DraftForm>(key: K, value: DraftForm[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: '' }));
    setApiError('');
  };

  const passwordStrength = useMemo(() => {
    const p = form.password;
    let score = 0;
    if (p.length >= 6) score++;
    if (p.length >= 10) score++;
    if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++;
    if (/\d/.test(p)) score++;
    if (/[^A-Za-z0-9]/.test(p)) score++;
    return score;
  }, [form.password]);

  const strengthMeta =
    form.password.length === 0
      ? null
      : passwordStrength <= 2
        ? { label: 'Weak', cls: 'bg-rose-500 w-1/5', text: 'text-rose-600' }
        : passwordStrength <= 3
          ? { label: 'Fair', cls: 'bg-amber-500 w-3/5', text: 'text-amber-600' }
          : { label: 'Strong', cls: 'bg-emerald-500 w-full', text: 'text-emerald-600' };

  const validateStep = (s: number): boolean => {
    const e: Record<string, string> = {};
    if (s === 1) {
      if (form.fullName.trim().length < 2) e.fullName = 'Please enter your full name';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email address';
      if (form.password.length < 6) e.password = 'Password must be at least 6 characters';
      if (form.confirmPassword !== form.password) e.confirmPassword = 'Passwords do not match';
    }
    if (s === 2) {
      const phoneDigits = digitsOnly(form.phone);
      if (phoneDigits.length < 10 || phoneDigits.length > 13)
        e.phone = 'Enter a valid phone number (10-13 digits)';
      if (form.role === 'patient') {
        const ecDigits = digitsOnly(form.emergencyContactPhone);
        if (ecDigits.length < 10 || ecDigits.length > 13)
          e.emergencyContactPhone = 'Enter a valid contact number (10-13 digits)';
      }
    }
    if (s === 3) {
      if (!form.state) e.state = 'Select your state or union territory';
      if (!form.city.trim()) e.city = 'Enter your city or district';
      if (form.role === 'doctor' && !form.licenseNumber.trim())
        e.licenseNumber = 'License / registration number is required';
      if (form.role === 'doctor' && form.languages.length === 0)
        e.languages = 'Select at least one language you counsel in';
    }
    if (s === 4) {
      if (!form.agreeTerms) e.agreeTerms = 'Required';
      if (!form.agreePrivacy) e.agreePrivacy = 'Required';
      if (!form.agreeAiDisclosure) e.agreeAiDisclosure = 'Required';
      if (!form.agreeCrisisPolicy) e.agreeCrisisPolicy = 'Required';
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const next = () => {
    if (validateStep(step)) setStep((s) => Math.min(s + 1, 5));
  };
  const back = () => setStep((s) => Math.max(s - 1, 1));

  const startOver = () => {
    sessionStorage.removeItem(DRAFT_KEY);
    setForm(INITIAL_DRAFT);
    setStep(1);
    setErrors({});
    setApiError('');
    setRestored(false);
  };

  const handleSubmit = async () => {
    for (let s = 1; s <= 4; s++) {
      if (!validateStep(s)) {
        setStep(s);
        return;
      }
    }
    setSubmitting(true);
    setApiError('');
    try {
      await apiClient.post('/auth/signup', {
        email: form.email.trim(),
        password: form.password,
        role: form.role,
        full_name: form.fullName.trim(),
        phone: form.phone.trim(),
        emergency_contact_phone: form.role === 'patient' ? form.emergencyContactPhone.trim() : undefined,
        state: form.state,
        city: form.city.trim(),
        license_number: form.role === 'doctor' ? form.licenseNumber.trim() : undefined,
        specialty: form.role === 'doctor' && form.specialty ? form.specialty : undefined,
        languages: form.role === 'doctor' ? form.languages : undefined,
      });

      const params = new URLSearchParams();
      params.append('username', form.email.trim());
      params.append('password', form.password);
      const loginRes = await apiClient.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      const token: string = loginRes.data.access_token;
      const meRes = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      login(token, meRes.data);

      sessionStorage.removeItem(DRAFT_KEY);
      const dest =
        meRes.data.role === 'patient'
          ? '/patient/dashboard'
          : meRes.data.role === 'doctor'
            ? '/doctor/dashboard'
            : '/admin/dashboard';
      navigate(dest);
    } catch (err: any) {
      setApiError(err.response?.data?.detail || 'Registration failed. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto flex max-w-6xl items-center justify-center px-4 py-10">
      <div className="grid w-full gap-0 overflow-hidden rounded-lg border border-[#e8e4df] bg-white shadow-[0_20px_60px_-24px_rgba(15,23,42,0.18)] lg:grid-cols-[420px_1fr]">
        {/* Brand panel */}
        <aside className="relative hidden flex-col justify-between overflow-hidden border-r border-[#e8e4df] bg-muted p-10 lg:flex">
          <div
            aria-hidden="true"
            className="absolute -left-16 top-24 h-64 w-64 rounded-full bg-accent opacity-[0.04] blur-3xl"
          />
          <div className="relative">
            <Link to="/" className="flex items-center gap-2.5">
              <span aria-hidden="true" className="flex h-10 w-10 items-center justify-center rounded-md border border-[#e8e4df] bg-white text-lg shadow-sm">
                🧠
              </span>
              <span className="font-display text-xl font-bold text-foreground">
                Mindora
              </span>
            </Link>
            <h2 className="mt-14 font-display text-4xl font-medium leading-tight tracking-normal text-foreground">
              A few minutes now.
              <br />
              <span className="italic text-accent">Support that lasts.</span>
            </h2>
            <div aria-hidden="true" className="mt-6 h-px w-16 bg-accent" />
            <p className="mt-5 max-w-xs text-sm leading-relaxed text-muted-foreground">
              Your information is encrypted, your identity stays yours, and help is available whenever you need it.
            </p>
          </div>
          <ul className="relative space-y-3 pt-10">
            {[
              'Validated PHQ-9 & GAD-7 clinical screening',
              'Journal entries encrypted end-to-end',
              'Emergency contact used only in crises',
            ].map((point) => (
              <li key={point} className="flex items-center gap-2.5 text-sm text-slate-600">
                <span aria-hidden="true" className="h-px w-4 shrink-0 bg-accent" />
                {point}
              </li>
            ))}
          </ul>
        </aside>

        {/* Wizard */}
        <div className="flex flex-col p-6 sm:p-10">
          <div className="mb-8 flex items-center justify-between">
            <Badge variant="primary" size="sm">
              Step {step} of {STEPS.length}
            </Badge>
            {restored && (
              <button
                onClick={startOver}
                className="cursor-pointer text-xs font-medium text-slate-400 transition-colors hover:text-rose-600"
              >
                Start over
              </button>
            )}
          </div>

          <Stepper steps={STEPS} currentStep={step} onStepClick={(s) => s < step && setStep(s)} className="mb-10" />

          {apiError && (
            <div role="alert" className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
              {apiError}
            </div>
          )}

          <div key={step} className="motion-safe:animate-fade-in-up grow">
            {step === 1 && (
              <div className="space-y-5">
                <WizardHeading title="Let's start with the basics" subtitle="This identifies you securely on the platform." />
                <div>
                  <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.08em] text-slate-600">I am registering as</span>
                  <div className="grid grid-cols-2 gap-3">
                    {(
                      [
                        { value: 'patient', icon: '🌱', label: 'Patient', hint: 'Seeking support' },
                        { value: 'doctor', icon: '🩺', label: 'Doctor', hint: 'Providing care' },
                      ] as const
                    ).map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => set('role', opt.value)}
                        aria-pressed={form.role === opt.value}
                        className={`cursor-pointer rounded-2xl border p-4 text-left transition-all duration-150 ${
                          form.role === opt.value
                            ? 'border-accent bg-accent-muted ring-2 ring-accent/20'
                            : 'border-[#e8e4df] hover:border-[#d6cfc7] hover:bg-muted'
                        }`}
                      >
                        <span aria-hidden="true" className="text-xl">{opt.icon}</span>
                        <span className={`block text-sm font-bold ${form.role === opt.value ? 'text-accent' : 'text-slate-700'}`}>{opt.label}</span>
                        <span className="block text-xs text-slate-500">{opt.hint}</span>
                      </button>
                    ))}
                  </div>
                </div>
                <Input
                  label="Full name"
                  required
                  placeholder="e.g. Priya Sharma"
                  autoComplete="name"
                  value={form.fullName}
                  onChange={(e) => set('fullName', e.target.value)}
                  error={errors.fullName}
                />
                <Input
                  label="Email address"
                  required
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  value={form.email}
                  onChange={(e) => set('email', e.target.value)}
                  error={errors.email}
                />
                <Input
                  label="Password"
                  required
                  type="password"
                  placeholder="At least 6 characters"
                  autoComplete="new-password"
                  value={form.password}
                  onChange={(e) => set('password', e.target.value)}
                  error={errors.password}
                />
                {strengthMeta && (
                  <div className="-mt-3">
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                      <div className={`h-full rounded-full transition-all duration-300 ${strengthMeta.cls}`} />
                    </div>
                    <p className={`mt-1 text-right text-[11px] font-semibold ${strengthMeta.text}`}>{strengthMeta.label}</p>
                  </div>
                )}
                <Input
                  label="Confirm password"
                  required
                  type="password"
                  placeholder="Re-enter your password"
                  autoComplete="new-password"
                  value={form.confirmPassword}
                  onChange={(e) => set('confirmPassword', e.target.value)}
                  error={errors.confirmPassword}
                />
              </div>
            )}

            {step === 2 && (
              <div className="space-y-5">
                <WizardHeading title="How can we reach you?" subtitle="Used for appointment confirmations and safety escalations." />
                <Input
                  label="Phone number"
                  required
                  type="tel"
                  placeholder="+91 98765 43210"
                  autoComplete="tel"
                  value={form.phone}
                  onChange={(e) => set('phone', e.target.value)}
                  error={errors.phone}
                  helperText="Standard appointment and care updates."
                />
                <Input
                  label={form.role === 'patient' ? 'Secondary emergency contact number' : 'Emergency contact number (optional)'}
                  required={form.role === 'patient'}
                  type="tel"
                  placeholder="+91 98765 43211"
                  value={form.emergencyContactPhone}
                  onChange={(e) => set('emergencyContactPhone', e.target.value)}
                  error={errors.emergencyContactPhone}
                  helperText={
                    form.role === 'patient'
                      ? 'A trusted person we notify only if a serious risk to your safety is detected — never for marketing.'
                      : 'Optional for clinicians.'
                  }
                />
                {form.role === 'patient' && (
                  <div className="rounded-xl border border-[#e8e4df] bg-muted p-4 text-xs leading-relaxed text-foreground">
                    🔒 Your emergency contact is confidential. It is contacted <strong>only</strong> through our crisis
                    escalation protocol, and only when automated risk detection flags a serious concern about your safety.
                  </div>
                )}
              </div>
            )}

            {step === 3 && (
              <div className="space-y-5">
                <WizardHeading
                  title={form.role === 'patient' ? 'Where are you based?' : 'Your professional details'}
                  subtitle={
                    form.role === 'patient'
                      ? 'We use this to match you with nearby counselors.'
                      : 'Patients discover counselors by location and language.'
                  }
                />
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                  <Select
                    label="State / Union Territory"
                    required
                    placeholder="Select..."
                    options={[...STATE_OPTIONS]}
                    value={form.state}
                    onChange={(e) => set('state', e.target.value)}
                    error={errors.state}
                  />
                  <Input
                    label="City / District"
                    required
                    placeholder="e.g. Pune"
                    value={form.city}
                    onChange={(e) => set('city', e.target.value)}
                    error={errors.city}
                  />
                </div>

                {form.role === 'patient' ? (
                  <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                    <Select
                      label="Age group"
                      placeholder="Select..."
                      options={AGE_GROUPS.map((a) => ({ value: a, label: a }))}
                      value={form.ageGroup}
                      onChange={(e) => set('ageGroup', e.target.value)}
                      helperText="Optional — helps tailor content."
                    />
                    <Select
                      label="Gender"
                      placeholder="Select..."
                      options={GENDERS.map((g) => ({ value: g, label: g }))}
                      value={form.gender}
                      onChange={(e) => set('gender', e.target.value)}
                      helperText="Optional — prefer not to say is fine."
                    />
                  </div>
                ) : (
                  <>
                    <Input
                      label="Medical council license / registration no."
                      required
                      placeholder="e.g. MCI-2011-45872"
                      value={form.licenseNumber}
                      onChange={(e) => set('licenseNumber', e.target.value)}
                      error={errors.licenseNumber}
                      helperText="Verified by our admin team before your profile goes live."
                    />
                    <Select
                      label="Specialty"
                      placeholder="Select..."
                      options={SPECIALTIES.map((sp) => ({ value: sp, label: sp }))}
                      value={form.specialty}
                      onChange={(e) => set('specialty', e.target.value)}
                      helperText="Shown on your public profile once verified."
                    />
                    <div>
                      <span className="mb-2 block text-[11px] font-bold uppercase tracking-[0.08em] text-slate-600">
                        Languages you counsel in <span className="ml-1 text-rose-500">*</span>
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
                                  : 'border-[#e8e4df] bg-white text-slate-600 hover:border-[#d6cfc7] hover:bg-muted'
                              }`}
                            >
                              {lang.label}
                            </button>
                          );
                        })}
                      </div>
                      {errors.languages && <p className="mt-1.5 text-xs font-medium text-rose-600">{errors.languages}</p>}
                    </div>
                    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-relaxed text-amber-900">
                      📄 Credential documents upload becomes available right after registration. Your account stays{' '}
                      <strong>pending verification</strong> until an administrator approves your credentials.
                    </div>
                  </>
                )}
              </div>
            )}

            {step === 4 && (
              <div className="space-y-4">
                <WizardHeading title="Consent & disclosures" subtitle="Please read each point carefully before agreeing." />
                <Checkbox
                  required
                  checked={form.agreeTerms}
                  onChange={(e) => set('agreeTerms', e.target.checked)}
                  error={errors.agreeTerms}
                  label={
                    <>
                      I agree to the <span className="font-semibold text-accent">Terms of Service</span> and confirm I am at least 18 years old (or have guardian consent).
                    </>
                  }
                />
                <Checkbox
                  required
                  checked={form.agreePrivacy}
                  onChange={(e) => set('agreePrivacy', e.target.checked)}
                  error={errors.agreePrivacy}
                  label={
                    <>
                      I understand my journal entries are encrypted, community posts are pseudonymous, and anonymized analytics never contain my identity (DPDP Act 2023 aligned).
                    </>
                  }
                />
                <Checkbox
                  required
                  checked={form.agreeAiDisclosure}
                  onChange={(e) => set('agreeAiDisclosure', e.target.checked)}
                  error={errors.agreeAiDisclosure}
                  label="I understand the AI companion is a support tool, not a replacement for professional diagnosis or emergency services."
                />
                <Checkbox
                  required
                  checked={form.agreeCrisisPolicy}
                  onChange={(e) => set('agreeCrisisPolicy', e.target.checked)}
                  error={errors.agreeCrisisPolicy}
                  label="If automated screening detects serious risk to my safety, I consent to my emergency contact and on-call professionals being notified under the escalation protocol."
                />
              </div>
            )}

            {step === 5 && (
              <div className="space-y-5">
                <WizardHeading title="Review your details" subtitle="Check everything below, then create your account." />
                <Card variant="default" className="divide-y divide-slate-100">
                  <ReviewRow label="Registering as" value={form.role === 'patient' ? '🌱 Patient' : '🩺 Doctor / Counselor'} />
                  <ReviewRow label="Full name" value={form.fullName} />
                  <ReviewRow label="Email" value={form.email} />
                  <ReviewRow label="Phone" value={form.phone} />
                  {form.role === 'patient' && (
                    <ReviewRow label="Emergency contact" value={form.emergencyContactPhone} />
                  )}
                  <ReviewRow label="Location" value={`${form.city}, ${form.state}`} />
                  {form.role === 'patient' && (form.ageGroup || form.gender) && (
                    <ReviewRow label="Demographics" value={[form.ageGroup, form.gender].filter(Boolean).join(' · ')} />
                  )}
                          {form.role === 'doctor' && (
                    <>
                      <ReviewRow label="License no." value={form.licenseNumber} />
                      {form.specialty && <ReviewRow label="Specialty" value={form.specialty} />}
                      <ReviewRow label="Languages" value={form.languages.join(', ')} />
                    </>
                  )}
                </Card>
                <p className="text-xs text-slate-500">
                  {form.role === 'doctor'
                    ? 'After registration you can upload credential documents. Your profile becomes visible to patients once an admin verifies it.'
                    : 'Next, you\'ll set up your private pseudonym for the community — your real name is never shown to other members.'}
                </p>
              </div>
            )}
          </div>

          <div className="mt-10 flex items-center justify-between gap-4">
            <Button variant="ghost" onClick={back} disabled={step === 1 || submitting}>
              ← Back
            </Button>
            {step < 5 ? (
              <Button onClick={next} size="md">
                Continue →
              </Button>
            ) : (
              <Button onClick={handleSubmit} isLoading={submitting} size="md">
                Create my account
              </Button>
            )}
          </div>

          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/auth/login" className="font-semibold text-accent transition-colors hover:text-accent-secondary">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

function WizardHeading({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-foreground">{title}</h1>
      <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex items-start justify-between gap-6 px-4 py-3 text-sm">
      <dt className="shrink-0 text-slate-500">{label}</dt>
      <dd className="text-right font-medium text-foreground">{value || '—'}</dd>
    </div>
  );
}
