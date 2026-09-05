import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { checkHealth } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  Container,
  SectionHeading,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Badge,
} from '../components/ui';

const FEATURES = [
  {
    icon: '🤖',
    title: 'AURA AI Companion',
    description:
      'A 24/7 conversational companion grounded in evidence-based CBT protocols, with source-cited answers and built-in crisis detection.',
  },
  {
    icon: '🥽',
    title: 'WebXR Exposure Therapy',
    description:
      'Immersive scenarios for phobias and social anxiety — self-guided open access or counselor-recommended, with live heart-rate telemetry.',
  },
  {
    icon: '📍',
    title: 'Location & Language Match',
    description:
      'Admin-verified counselors ranked nearest to you first, filterable by the language you speak, on video, in person, or chat.',
  },
  {
    icon: '🛡️',
    title: 'Crisis Support, Always On',
    description:
      'When risk is detected, your emergency contact and on-call counselors are notified automatically inside a tracked response window that escalates if no one responds.',
  },
];

const STEPS = [
  {
    num: '01',
    title: 'Register privately',
    description:
      'Create an account in minutes with an optional pseudonym. Journal entries are encrypted before they ever touch storage.',
  },
  {
    num: '02',
    title: 'Screen & talk it out',
    description:
      'Take clinically validated PHQ-9 / GAD-7 screenings and talk with AURA anytime — day or night, judgment-free.',
  },
  {
    num: '03',
    title: 'Meet the right counselor',
    description:
      'Get matched with verified professionals near you, in your language — then choose video, in-person, or chat sessions.',
  },
];

const TRUST_POINTS = [
  'Validated PHQ-9 & GAD-7 screening',
  'AI companion grounded in CBT',
  'Counselors matched by location & language',
  'Emergency contacts notified in a crisis',
];

export default function Home() {
  const [health, setHealth] = useState<string>('checking...');
  const { user } = useAuth();

  useEffect(() => {
    checkHealth()
      .then((data) => setHealth(data.status))
      .catch(() => setHealth('API offline'));
  }, []);

  const dashboardPath =
    user?.role === 'patient'
      ? '/patient/dashboard'
      : user?.role === 'doctor'
        ? '/doctor/dashboard'
        : user?.role === 'admin'
          ? '/admin/dashboard'
          : null;

  return (
    <div className="pb-16">
      {/* Crisis banner */}
      <aside aria-label="Crisis support notice" className="border-b border-amber-200 bg-amber-50 text-amber-950">
        <Container className="flex flex-col items-center justify-center gap-2 py-3 text-center sm:flex-row sm:gap-4">
          <p className="text-sm">
            In crisis or struggling right now?{' '}
            <a
              href="tel:14416"
              className="font-semibold underline decoration-accent decoration-2 underline-offset-2 hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded"
            >
              Call Tele-MANAS 14416
            </a>{' '}
            — free, 24/7, all languages.
          </p>
          <a
            href="tel:112"
            className="shrink-0 rounded-md border border-red-800 px-3 py-1 text-xs font-semibold tracking-[0.04em] text-red-800 transition-colors duration-200 hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-700"
          >
            Emergency? Call 112
          </a>
        </Container>
      </aside>

      {/* Hero */}
      <section className="relative overflow-hidden" aria-labelledby="hero-heading">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute left-1/2 top-1/3 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-accent opacity-[0.02] blur-3xl"
        />
        <div className="absolute inset-0 paper-texture opacity-40" aria-hidden="true" />

        <Container size="md" className="relative py-24 sm:py-36">
          <div className="flex flex-col items-center gap-7 text-center">
            <span style={{ animationDelay: '40ms' }} className="motion-safe:animate-fade-in-up small-caps text-accent">
              Private · Evidence-based · Always available
            </span>

            <h1
              id="hero-heading"
              style={{ animationDelay: '120ms' }}
              className="motion-safe:animate-fade-in-up font-display text-[2.75rem] font-medium leading-[1.12] tracking-[-0.02em] text-foreground sm:text-6xl lg:text-[4.25rem]"
            >
              Mental health support that meets you where you are
            </h1>

            <div aria-hidden="true" className="flex w-full max-w-xs items-center gap-4 pt-1">
              <span className="h-px flex-1 bg-[#e8e4df]" />
              <span className="h-1 w-1 rotate-45 bg-accent" />
              <span className="h-px flex-1 bg-[#e8e4df]" />
            </div>

            <p
              style={{ animationDelay: '200ms' }}
              className="motion-safe:animate-fade-in-up max-w-2xl text-pretty text-lg leading-[1.75] text-muted-foreground"
            >
              Mindora pairs an AI companion grounded in clinical practice with verified human counselors,
              self-guided therapy modules, and safety systems that act even when no one is watching.
            </p>

            <div
              style={{ animationDelay: '280ms' }}
              className="motion-safe:animate-fade-in-up flex flex-wrap items-center justify-center gap-4 pt-4"
            >
              {!user ? (
                <>
                  <Link to="/auth/signup">
                    <Button size="lg">Create free account</Button>
                  </Link>
                  <Link to="/auth/login">
                    <Button size="lg" variant="outline">
                      I already have one
                    </Button>
                  </Link>
                </>
              ) : (
                dashboardPath && (
                  <Link to={dashboardPath}>
                    <Button size="lg">Continue to your dashboard</Button>
                  </Link>
                )
              )}
            </div>

            <ul
              style={{ animationDelay: '380ms' }}
              className="motion-safe:animate-fade-in-up mt-8 flex flex-wrap items-center justify-center gap-x-3 gap-y-2"
              aria-label="Platform highlights"
            >
              {TRUST_POINTS.map((point, i) => (
                <li key={point} className="flex items-center gap-3 text-xs text-muted-foreground">
                  {i > 0 && <span aria-hidden="true" className="h-0.5 w-0.5 rotate-45 bg-accent" />}
                  <span className="font-mono uppercase tracking-[0.08em]">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </Container>
        <div className="rule-line relative" aria-hidden="true" />
      </section>

      {/* Features */}
      <section className="py-24 sm:py-32" aria-labelledby="features-heading">
        <Container>
          <SectionHeading
            align="center"
            rules
            eyebrow="The platform"
            title={
              <>
                Complete care, <span className="italic text-accent">one platform</span>
              </>
            }
            description="Every layer of the system works together — from first screening to long-term therapy, nothing falls through the cracks."
            className="mb-14"
          />
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((feature) => (
              <Card key={feature.title} hoverEffect accentTop className="flex">
                <CardHeader className="grow pb-2">
                  <span aria-hidden="true" className="mb-4 inline-block text-2xl">
                    {feature.icon}
                  </span>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                  <CardDescription className="text-[13px] leading-relaxed">{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </Container>
      </section>

      {/* How it works */}
      <section className="border-y border-[#e8e4df] bg-muted/50 py-24" aria-labelledby="how-heading">
        <Container>
          <SectionHeading
            align="center"
            rules
            eyebrow="How it works"
            title="Three steps to feeling better"
            description="No waiting rooms, no paperwork mountains. Start where you are comfortable."
            className="mb-16"
          />
          <ol className="grid grid-cols-1 gap-12 md:grid-cols-3 md:gap-10">
            {STEPS.map((step) => (
              <li key={step.num} className="flex flex-col items-center text-center">
                <span aria-hidden="true" className="font-display text-6xl font-medium text-accent/35">
                  {step.num}
                </span>
                <h3 className="mt-3 font-display text-xl font-semibold text-foreground">{step.title}</h3>
                <p className="mt-3 max-w-sm text-sm leading-relaxed text-muted-foreground">{step.description}</p>
              </li>
            ))}
          </ol>
        </Container>
      </section>

      {/* Portal gateways */}
      <section className="py-24" aria-labelledby="portals-heading">
        <Container>
          <SectionHeading
            align="center"
            rules
            eyebrow="Get access"
            title="Choose your portal"
            description="Role-based access keeps clinical data exactly where it belongs."
            className="mb-12"
          />
          <div className="mx-auto grid max-w-4xl grid-cols-1 gap-6 md:grid-cols-3">
            <PortalCard
              badge={{ label: 'For individuals' }}
              icon="🌱"
              title="Patient Portal"
              description="Screening, mood tracking, the AURA companion, peer community, VR therapy, and appointments."
              cta={user?.role === 'patient' ? 'Open dashboard' : 'Enter patient portal'}
              to={user?.role === 'patient' ? '/patient/dashboard' : '/auth/login'}
              featured
            />
            <PortalCard
              badge={{ label: 'For clinicians' }}
              icon="🩺"
              title="Doctor Portal"
              description="Triage alerts, appointment management, longitudinal insights, and VR assignment."
              cta={user?.role === 'doctor' || user?.role === 'admin' ? 'Open dashboard' : 'Clinician sign in'}
              to={user?.role === 'doctor' || user?.role === 'admin' ? '/doctor/dashboard' : '/auth/login'}
            />
            <PortalCard
              badge={{ label: 'For administrators' }}
              icon="📊"
              title="Admin Analytics"
              description="Anonymized regional trends, spike detection, screening scale management, and exports."
              cta={user?.role === 'admin' ? 'Open panel' : 'Admin sign in'}
              to={user?.role === 'admin' ? '/admin/dashboard' : '/auth/login'}
            />
          </div>
        </Container>
      </section>

      {/* Compliance, privacy & trust */}
      <section className="border-t border-[#e8e4df] bg-white py-24" aria-labelledby="trust-heading">
        <Container>
          <SectionHeading
            align="center"
            rules
            eyebrow="Privacy & compliance"
            title="Your data, your control"
            description="Mindora is built privacy-first: identity stays with you, analytics never see a name, and safety systems are transparent about exactly what they do."
            className="mb-10"
          />

          <div className="mb-12 flex flex-wrap items-center justify-center gap-3">
            <Badge variant="success" size="md" dot>DPDP Act 2023 aligned</Badge>
            <Badge variant="primary" size="md">Encrypted journal entries</Badge>
            <Badge variant="info" size="md">Pseudonymous community</Badge>
            <Badge variant="neutral" size="md">WCAG 2.1 AA target</Badge>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card accentTop>
              <CardHeader>
                <CardTitle>How anonymized analytics work</CardTitle>
                <CardDescription>What leaves your account — and what never does.</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 text-sm leading-relaxed text-muted-foreground">
                  {[
                    'Reporting dashboards only ever see regional aggregates (state + month) — zero names, IDs, or contact details.',
                    'Any cohort smaller than 10 people is suppressed and shown as "insufficient data" instead of a number.',
                    'Journal entries are encrypted before storage; community posts use your chosen pseudonym.',
                    'You can export or request deletion of your entire record at any time.',
                  ].map((point) => (
                    <li key={point} className="flex items-start gap-2.5">
                      <span aria-hidden="true" className="mt-2 h-px w-4 shrink-0 bg-accent" />
                      {point}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card accentTop>
              <CardHeader>
                <CardTitle>What actually happens in a crisis</CardTitle>
                <CardDescription>No vague promises — this is the exact protocol that runs.</CardDescription>
              </CardHeader>
              <CardContent>
                <ol className="space-y-4 text-sm leading-relaxed text-muted-foreground">
                  {[
                    'Automated screening flags serious risk signals (self-harm language, critical questionnaire items) the moment they appear — no AI guesswork involved in detection.',
                    'Your registered secondary emergency contact is notified immediately through our escalation protocol.',
                    'On-call counselors near you are alerted at the same time, with a tracked response window that starts on detection.',
                    'If no counselor responds within the window, escalation continues automatically to backup pools and emergency services.',
                  ].map((point, i) => (
                    <li key={point} className="flex items-start gap-3.5">
                      <span aria-hidden="true" className="font-display text-2xl font-medium leading-none text-accent/50">
                        {i + 1}
                      </span>
                      <span className="pt-0.5">{point}</span>
                    </li>
                  ))}
                </ol>
                <p className="mt-5 border-l-2 border-accent bg-muted p-3 text-xs text-muted-foreground">
                  Prefer to talk to a person right now? The national helplines above are free and available 24/7.
                </p>
              </CardContent>
            </Card>
          </div>
        </Container>
      </section>

      {/* Footer */}
      <footer className="bg-background">
        <Container className="py-10">
          <div className="rule-line mb-6" aria-hidden="true" />
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
              © {new Date().getFullYear()} Mindora · Mental health & psychological support platform
            </p>
            <div className="flex items-center gap-4 font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
              <Badge variant="success" size="sm" dot>
                API {health === 'ok' ? 'online' : health}
              </Badge>
              <span>Privacy-first</span>
              <span aria-hidden="true" className="h-0.5 w-0.5 rotate-45 bg-accent" />
              <span>Accessible</span>
            </div>
          </div>
        </Container>
      </footer>
    </div>
  );
}

interface PortalCardProps {
  badge: { label: string };
  icon: string;
  title: string;
  description: string;
  cta: string;
  to: string;
  featured?: boolean;
}

function PortalCard({ badge, icon, title, description, cta, to, featured = false }: PortalCardProps) {
  return (
    <Card hoverEffect accentTop={featured} className={`flex flex-col ${featured ? 'shadow-[0_4px_12px_rgba(26,26,26,0.06)]' : ''}`}>
      <CardHeader className="grow pb-4">
        <div className="mb-4 flex items-center justify-between">
          <span aria-hidden="true" className="text-2xl">
            {icon}
          </span>
          <Badge variant={featured ? 'primary' : 'neutral'} size="sm">
            {badge.label}
          </Badge>
        </div>
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription className="text-[13px]">{description}</CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <Link to={to} className="block">
          <Button variant={featured ? 'primary' : 'outline'} className="w-full">
            {cta}
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
