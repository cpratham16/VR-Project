# VR MindHealth — VR-Based Digital Mental Health Platform for Campus Settings

A full-stack mental health support platform designed for university campuses, combining **standardized screening (PHQ-9 / GAD-7)**, **mood tracking**, **pseudonymous peer community**, **AI-assisted supportive chat**, **deterministic crisis escalation**, **doctor tele-triage**, and **in-browser WebXR virtual reality exposure therapy** — with a hard-anonymized regional dashboard for administrative planning.

> Built as the implementation artifact for the accompanying research paper on VR-based digital mental health interventions for campus populations (see [Research Context](#research-context)).

---

## 1. Problem & Rationale (Research Framing)

University students face a disproportionately high prevalence of depression, anxiety, and academic stress, yet consistently underutilize traditional mental health services due to stigma, cost, and accessibility barriers. The evidence base for **internet-delivered cognitive behavioral interventions (iCBT)** and **virtual reality exposure therapy (VRET)** shows meaningful effect sizes for phobias, social anxiety, and depression, while **screening-to-intervention pipelines** can close the detection gap when embedded in existing campus infrastructure.

This platform operationalizes four research-backed principles:

1. **Screening → triage → intervention continuity.** Standardized instruments (PHQ-9, GAD-7) feed a deterministic risk engine that routes patients to the right care path, including VR exposure therapy.
2. **AI as a support layer, not a clinician.** A guardrailed conversational agent (AURA) offers psychoeducation and support while a deterministic distress scanner — independent of LLM judgment — owns crisis detection.
3. **VRET without hardware dependence.** WebXR (A-Frame) delivers exposure scenarios in the browser so therapy remains portable and demoable without headsets.
4. **Privacy-by-architecture for administrative visibility.** Regional planning data is produced by a one-way anonymization pipeline into an identifier-free reporting store — no patient-identifiable record is ever reachable from the admin panel.

---

## 2. Architecture

```
                          ┌─────────────────────────────────────────────┐
                          │                  React 19 SPA                │
                          │   Patient / Doctor / Admin / Auth           │
                          └──────────────┬──────────────────────────────┘
                                         │ HTTPS / JWT (Bearer)
┌────────────────────────────────────────▼──────────────────────────────┐
│                          FastAPI (async, PostgreSQL)                    │
│                                                                        │
│  /api/v1/auth        signup, login, JWT, RBAC                          │
│  /api/v1/patient     onboarding, screening, mood, chat, panic, VR      │
│  /api/v1/doctor      triage, notes, appointments, alerts, moderation,  │
│                       VR assignment, telemetry review                  │
│  /api/v1/admin       anonymized analytics + manual pipeline trigger    │
│  /api/v1/community   pseudonymous peer forum                           │
│                                                                        │
│  AI Layer:  Hybrid RAG (doctor–patient exemplar dataset) →             │
│             Groq LLM  with zero-downtime local fallback                │
│  Safety:    Deterministic distress scanner + Panic SOS escalation      │
│  VR Engine: HR/HRV → stress-index telemetry                            │
└──────────────────────────────────────┬─────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────────┐
              ▼                        ▼                            ▼
        PostgreSQL              Anonymization ETL              Groq Cloud
        (clinical store)        (regional_aggregates)          (LLM API)
                                └→ identifier-free              └→ local fallback
                                   reporting store
```

### Data flows
- **Patient onboarding** → consent record → pseudonym profile → PHQ-9/GAD-7 screening → risk band.
- **Crisis path** → Panic SOS or AI-chat distress keyword → `RiskAlert` (CRITICAL/HIGH) → live doctor triage feed.
- **VR path** → doctor assigns scenario/intensity → patient launches WebXR session → telemetry (HR/HRV/stress index) recorded → SUDS pre/post → completion.
- **Admin path** → manual pipeline trigger aggregates screenings/mood/alerts/VR by `region + YYYY-MM` → charts and spike detection read **only** the anonymized store.

---

## 3. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2 (async), Pydantic v2 | Fast iteration, async PostgreSQL, OpenAPI auto-docs |
| Frontend | React 19, React Router 7, Tailwind CSS v4, Recharts | Component reuse across the three panels, interactive charts |
| VR | A-Frame (WebXR) | Browser-based VRET, headset-optional |
| Database | PostgreSQL 16/17 + Alembic | Relational integrity + reproducible schema migrations |
| AI | Groq `llama-3.3-70b-versatile` + hybrid RAG | Cost-effective supportive responses with local fallback |
| Auth | JWT (python-jose) + bcrypt (passlib) + RBAC | Simple, auditable, adequate for prototype scope |
| CI | GitHub Actions (lint + test) | Quality gate on every push |

---

## 4. Getting Started

### Prerequisites
- Python 3.11+ (3.13 recommended)
- Node.js 20+
- PostgreSQL 14+ running locally (default `postgres:postgres@localhost:5432/vr_mental_health`)

### 4.1 Database

Create the database and run the baseline migration:

```bash
createdb vr_mental_health      # or via psql: CREATE DATABASE vr_mental_health;
cd backend
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
alembic upgrade head            # applies baseline schema (all 16 tables)
```

> The baseline migration (`f072cfaf..._baseline_full_schema.py`) creates the full schema including `users.state` / `users.city` and the identifier-free `regional_aggregates` reporting store.

### 4.2 Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

- Interactive API docs: http://localhost:8000/api/v1/openapi.json
- Swagger UI (FastAPI auto-docs): visit `http://localhost:8000/api/v1/openapi.json` in a browser, or mount the default docs at `http://localhost:8000/docs`.

### 4.3 Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

### 4.4 Seed Data (Demo)

```bash
cd backend
python -m app.seed_vr       # idempotent — two VR exposure scenarios
python -m app.seed_demo     # idempotent — admin/doctors/patients + clinical data
```

### 4.5 Demo Credentials

| Role | Email | Password | Region |
|---|---|---|---|
| Admin | `admin@campus.edu` | `admin123` | Pune, Maharashtra |
| Doctor | `doctor1@campus.edu` | `doc123` | New Delhi, Delhi |
| Doctor | `doctor2@campus.edu` | `doc123` | Bengaluru, Karnataka |
| Patient | `alice@campus.edu` | `pass123` | Pune, Maharashtra |
| Patient | `bob@campus.edu` | `pass123` | New Delhi, Delhi |
| Patient | `carol@campus.edu` | `pass123` | Bengaluru, Karnataka |
| Patient | `dave@campus.edu` | `pass123` | Chennai, Tamil Nadu |
| Patient | `eve@campus.edu` | `pass123` | Kochi, Kerala |

---

## 5. Feature Map (by PRD Phase)

| Phase | Iteration | Feature |
|---|---|---|
| 0 | 0 | Monorepo, FastAPI + React + Postgres skeleton, CI |
| 1 | 1–4 | Auth/RBAC, onboarding & consent, PHQ-9/GAD-7, mood tracker |
| 2 | 5–7 | Doctor verification & triage, clinical notes, appointments |
| 3 | 8–9 | AURA chatbot (RAG + guardrails), Panic SOS + deterministic risk engine |
| 4 | 10–11 | Pseudonymous community + moderation, WebXR VR therapy with telemetry |
| 5 | 12–13 | Anonymization pipeline, admin analytics dashboard |
| 6 | 14 | Security/RBAC tests, WCAG 2.1 AA spot-check, seed data, migrations, docs |

---

## 6. Testing & Quality

```bash
cd backend
pytest -q                    # 33 tests: health, security, AI chat, screening,
                             # community, VR engine, anonymization, RBAC
cd ../frontend
npm run lint                 # oxlint
npm run build                # tsc -b && vite build (type-safe production build)
```

Notable coverage:
- **RBAC test pass** (`tests/test_rbac.py`): role gating for doctor/admin deps, invalid/expired token rejection, and a schema-contract assertion that every non-public route requires OAuth2 security.
- **Anonymization schema review** (`tests/test_anonymization.py`): introspects `RegionalAggregate` columns and asserts no identifier or foreign-key columns exist.
- **Deterministic risk logic** is exercised in `test_vr.py` (stress-index math) and `test_ai_chat.py`.

---

## 7. Environment Configuration

Create `.env` in the project root (see `.env.example`):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vr_mental_health
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
GROQ_API_KEY=your-groq-key    # optional — local fallback engine engages without it
VITE_API_BASE_URL=http://localhost:8000
```

> A startup warning is emitted if the default `SECRET_KEY` is detected — set a strong value before any shared or public deployment.

---

## 8. Security & Privacy Notes

- **Role-based access control:** `patient` / `doctor` / `admin` enforced via FastAPI dependencies (`get_current_user`, `get_current_doctor`, `get_current_admin`). Admin analytics are strictly separated.
- **Hard anonymization boundary:** `regional_aggregates` contains no foreign keys, no user IDs, no emails, no pseudonyms, no free text — verified by an automated schema-review test.
- **Deterministic crisis escalation:** distress detection never depends solely on LLM output; a hard-coded keyword scanner and Panic SOS trigger `RiskAlert` rows routed to the doctor triage feed.
- **Consent-first AI:** explicit consent for AI processing and data usage is captured before any patient input reaches the AI layer.
- **Informed compliance posture:** designed with the spirit of India's DPDP Act 2023 and Mental Healthcare Act 2017 in mind; PHQ-9/GAD-7 usage terms should be confirmed before any public/published deployment.

---

## 9. Accessibility (WCAG 2.1 AA)

Key patient/doctor flows were spot-checked and remediated:

- Skip-to-content link and `aria-current` active-state on navigation
- `role="dialog"`, `aria-modal`, Escape-to-close, and initial focus in the Panic SOS modal
- `aria-label` / `aria-required` / associated `<label>` on all form controls (signup, login, screening, mood, chat)
- `aria-live="polite"` / `role="status"` on chat log, screening results, save confirmations, and admin pipeline banners
- Color contrast fixes (`text-gray-400` → `text-gray-600`; `teal-600` → `teal-700` on white-text buttons)
- Decorative emoji marked `aria-hidden="true"`

---

## 10. Deployment Notes

Recommended free/low-cost targets for the academic build:

- **Backend + Postgres:** Render / Railway — add `DATABASE_URL`, `SECRET_KEY`, `BACKEND_CORS_ORIGINS`, and `GROQ_API_KEY` to env. Run `alembic upgrade head` in a release command.
- **Frontend:** Vercel/Netlify — set `VITE_API_BASE_URL` to the deployed backend URL, build with `npm run build`.

VR content runs fully in-browser (WebXR), so no headset or special hosting is required for the demo.

---

## 11. Project Structure

```
├── PRD.md, PROJECT_PLAN.md, MEMORY.md, ARCHITECTURE.md, FLOW.md
├── docker-compose.yml, .env.example
├── archive/                    # doctor–patient dialogue dataset (RAG exemplars)
├── backend/
│   ├── alembic/                # env.py (compare_type/server_default on) + baseline migration
│   ├── app/
│   │   ├── api/v1/             # 15 route modules (auth … admin)
│   │   ├── core/               # config, database, security
│   │   ├── models/             # 12 ORM modules incl. RegionalAggregate
│   │   ├── schemas/            # Pydantic validation + severity scoring
│   │   ├── services/           # rag_engine, ai_companion, risk_engine,
│   │   │                       # vr_engine, anonymizer
│   │   ├── seed_vr.py          # VR scenario seeder
│   │   └── seed_demo.py        # full demo dataset + analytics pipeline run
│   └── tests/                  # 33 tests (7 files)
└── frontend/
    └── src/
        ├── pages/{auth,patient,doctor,admin}/
        ├── components/          # PanicModal, HeartRateMonitor
        └── layouts/MainLayout.tsx
```

---

## 12. Research Context

This repository is the implementation companion to a research paper on **VR-based digital mental health interventions in campus settings**. It demonstrates:

- **Digital screening & stepped care:** evidence-based instruments and a deterministic risk engine rather than discretionary clinician-only intake.
- **AI augmentation with human oversight:** conversational AI bounded by guardrails, with escalation owned by deterministic rules.
- **Exposure therapy accessibility:** VRET delivered via commodity browsers (WebXR), sidestepping hardware-cost barriers.
- **Aggregate visibility without surveillance:** anonymized regional dashboards for planning that cannot resolve to individuals.

To cite or reference this work, use the citation entry provided in the paper (Springer LNCS-style). For any use of the PHQ-9/GAD-7 instruments in public or published work, verify current licensing terms.

---

## 13. License & Disclaimer

This is an academic prototype. It is **not** a substitute for professional mental health care, emergency services, or clinical judgment. Crisis resources referenced in-app (Tele-MANAS `14416`, campus lines) should be validated against your deployment region before any live use.
