# FOLDER_STRUCTURE.md — Directory Layout (Source of Truth)

> Update this whenever a folder is added, removed, or its purpose changes.

## Tree

```
project-root/
├── MEMORY.md, ARCHITECTURE.md, FLOW.md, PROGRESS.md, FOLDER_STRUCTURE.md
├── PROJECT_PLAN.md, PRD.md
├── docker-compose.yml, .env.example
├── archive/                    # Clinical dialogue datasets for Hybrid RAG (CSV)
├── Combined Data/              # Sentiment & distress dataset (CSV)
├── .github/workflows/ci.yml
├── backend/                    # FastAPI Backend Service
│   ├── alembic.ini, requirements.txt, alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── seed_vr.py          # VR scenario seeder script
│   │   ├── api/
│   │   │   ├── deps.py         # Auth + doctor + admin dependencies
│   │   │   └── v1/             # 15 route modules (auth, patient, screening, mood,
│   │   │                       #   chat, panic, community, doctor, doctor_alerts,
│   │   │                       #   doctor_moderation, doctor_vr, patient_vr, admin, health)
│   │   ├── core/               # config.py, database.py, security.py
│   │   ├── models/             # 12 ORM modules (user, patient, screening, mood, note,
│   │   │                       #   appointment, chat, alert, community, vr, anonymized,
│   │   │                       #   __init__)
│   │   ├── schemas/            # Pydantic validation (vr.py, chat.py, alert.py, community.py, etc.)
│   │   └── services/           # Business logic (rag_engine, ai_companion, risk_engine,
│   │                           #   vr_engine, anonymizer)
│   └── tests/                  # 19 Pytest tests across 7 files
└── frontend/                   # React 19 + A-Frame WebXR Frontend
    ├── package.json            # Includes aframe dependency
    ├── vite.config.ts, tsconfig.json, tsconfig.app.json
    ├── public/
    └── src/
        ├── App.tsx, main.tsx
        ├── api/client.ts
        ├── components/
        │   ├── PanicModal.tsx
        │   └── HeartRateMonitor.ts   # Web BLE HR/HRV hook + simulated fallback
        ├── contexts/AuthContext.tsx
        ├── layouts/MainLayout.tsx
        ├── types/aframe.d.ts
        └── pages/
            ├── Home.tsx
            ├── auth/             # Login, Signup (with state/city for patients)
            ├── patient/
            │   ├── Dashboard.tsx
            │   ├── AppointmentsPage.tsx
            │   ├── onboarding/   # ConsentScreen, ProfileSetup
            │   ├── screening/    # ScreeningPage
            │   ├── mood/         # MoodTrackerPage
            │   ├── chat/         # AIChatPage (AURA)
            │   ├── community/    # CommunityPage
            │   └── vr/           # VRTherapyPage, VRSessionRunner
            ├── doctor/
            │   ├── TriageDashboard.tsx, PatientDetail.tsx, DoctorAppointments.tsx
            │   ├── ModerationQueuePage.tsx
            │   └── VRAssignmentPage.tsx
            └── admin/
                └── AdminDashboard.tsx   # Admin-only analytics (Recharts, spike alerts)
```

## Change Log
- 2026-08-11: Created persistent memory files and documented complete full-stack directory layout.
- 2026-08-11: Updated with Phase 3 (AI Companion, Groq LLM, RAG, Panic SOS).
- 2026-08-11: Updated with Phase 4 — Iteration 10 (Community Forum, Moderation Queue).
- 2026-08-11: Updated with Phase 4 — Iteration 11 (WebXR VR Therapy Module).
- 2026-08-11: Updated with Phase 5 — Iterations 12 & 13: `admin.py` API, `anonymized.py` RegionalAggregate, `anonymizer.py` ETL service, `AdminDashboard.tsx`, `state`/`city` on User, `Signup.tsx` region capture.
