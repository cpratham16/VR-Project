# PROJECT_PLAN.md — 14-Iteration Implementation Roadmap

## Overview
Full-stack VR-based Digital Mental Health Platform for Campus Settings (FastAPI + React 19 + PostgreSQL + A-Frame WebXR + Recharts + Groq LLM RAG).

---

## Phase Status Summary

| Phase | Iterations | Description | Status |
|---|---|---|---|
| Phase 0 | Iteration 0 | Project Skeleton, Architecture & CI Pipeline | **COMPLETED** |
| Phase 1 | Iterations 1–4 | Auth, Onboarding, Screening & Mood Tracking | **COMPLETED** |
| Phase 2 | Iterations 5–7 | Doctor Verification, Clinical Triage & Appointments | **COMPLETED** |
| Phase 3 | Iterations 8–9 | AI Companion (AURA), Panic SOS & Risk Engine | **COMPLETED** |
| Phase 4 | Iterations 10–11 | Community Forum & WebXR VR Therapy Engine | **COMPLETED** |
| Phase 5 | Iterations 12–13 | Anonymization Pipeline & Admin Analytics Dashboard | **COMPLETED** |
| Phase 6 | Iteration 14 | Hardening, Security Audit, Seed Script & Demo Launch | **COMPLETED** |

---

## Detailed Iteration Tracker

### Phase 0: Foundations & Architecture
- [x] **Iteration 0: Skeleton & Setup** — Monorepo setup, FastAPI structure, React + Tailwind v4 + React Router 7 configuration, PostgreSQL connection pool, initial health endpoints, CI pipeline.

### Phase 1: Authentication & Patient Onboarding
- [x] **Iteration 1: Auth & User Model** — Bcrypt password hashing, JWT token generation/validation, User ORM model (`patient`, `doctor`, `admin` roles), signup/login endpoints and UI pages.
- [x] **Iteration 2: Onboarding & Consent** — `PatientProfile` (pseudonyms) and `ConsentRecord` models, consent collection form (agreed to AI processing & data usage), patient onboarding flow.
- [x] **Iteration 3: Standardized Screening** — `ScreeningResult` model, PHQ-9 (depression) & GAD-7 (anxiety) questionnaire engine, score calculation & severity banding (`Minimal` … `Severe`), patient screening UI & history view.
- [x] **Iteration 4: Daily Mood Tracker** — `MoodEntry` model (1–5 scale, tags, optional journal text), patient mood check-in page, Recharts interactive mood history chart.

### Phase 2: Doctor Panel & Clinical Workflow
- [x] **Iteration 5: Doctor Verification & Triage Dashboard** — Doctor self-verification route, `TriageDashboard` UI with patient severity sorting, filtering, and risk badges.
- [x] **Iteration 6: Patient Detail & Clinical Notes** — `ClinicalNote` model, `PatientDetail` view aggregating screening scores, mood trends, and doctor SOAP notes.
- [x] **Iteration 7: Appointment Management** — `Appointment` model, appointment booking modal for patients, doctor appointment management calendar view.

### Phase 3: AI Companion & Crisis Interventions
- [x] **Iteration 8: AI Companion (AURA)** — `ChatSession` & `ChatMessage` models, hybrid RAG engine using doctor-patient dialogue dataset, Groq LLM integration with offline fallback, `AIChatPage` interface.
- [x] **Iteration 9: Panic SOS & Risk Escalation Engine** — `RiskAlert` model, Panic SOS button + modal with emergency helplines (Tele-MANAS `14416`), deterministic distress scanner, live alert feed on doctor dashboard.

### Phase 4: Peer Community & VR Therapy
- [x] **Iteration 10: Pseudonymous Community Forum** — `CommunityPost` & `CommunityComment` models, category filtering, flagging system, doctor moderation queue page.
- [x] **Iteration 11: WebXR VR Exposure Therapy** — `VRScenario`, `VRSession`, `VRTelemetry` models, A-Frame scenes ("Skyline Terrace" acrophobia, "Lecture Hall" glossophobia), Web Bluetooth PPG heart rate monitor integration + simulator fallback, doctor assignment page, patient VR launcher + SUDS rating.

### Phase 5: Anonymization & Admin Analytics
- [x] **Iteration 12: Anonymization Pipeline** — `RegionalAggregate` ORM model (strictly zero foreign keys or patient identifiers), ETL aggregation service (`anonymizer.py`) grouping by region (`City, State`) and `YYYY-MM` period, schema-review test.
- [x] **Iteration 13: Admin Analytics Dashboard** — Admin RBAC dependency (`get_current_admin`), `/admin/analytics/*` endpoints, Recharts analytics page (overview KPIs, regional distribution, month-over-month trend line, anomaly spike detection, manual pipeline trigger).

### Phase 6: Hardening, Security Audit & Launch
- [x] **Iteration 14: Hardening & Demo Launch**
  - [x] RBAC security test suite (`tests/test_rbac.py` — 14 tests verifying role gating, token validation, OpenAPI security contracts).
  - [x] Full demo seed script (`app/seed_demo.py` with simple passwords: `admin123`, `doc123`, `pass123`, 5 patients, full clinical histories, and automatic aggregation run).
  - [x] Alembic baseline migration (`alembic/versions/f072cfaf8040_baseline_full_schema.py`) with `compare_type=True` and `compare_server_default=True` configured in `env.py`.
  - [x] WCAG 2.1 AA accessibility remediation (skip links, `aria-label`/`aria-required` on forms, `role="dialog"` + Escape key on PanicModal, `aria-live="polite"` status regions, contrast fixes).
  - [x] Comprehensive research-backed `README.md` referencing the Springer LNCS paper context.
  - [x] Verification: 33/33 pytest tests passing, `tsc -b` type-check clean, `oxlint` lint clean, `vite build` succeeded.
