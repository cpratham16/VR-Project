# MEMORY.md — Persistent Session Context & Resume Point

> **System State:** Phase 6 (Iteration 14 — Hardening & Demo Launch) fully completed.
> **Date:** August 11, 2026

---

## 1. Resume Point
- All 14 iterations defined in `PRD.md` and `PROJECT_PLAN.md` are **100% complete**.
- Test suite: **33/33 backend tests passing** across 7 test files (`pytest`).
- Frontend: **Type check clean (`tsc -b`), build clean (`vite build`), lint clean (`oxlint`)**.
- Baseline migration: `alembic/versions/f072cfaf8040_baseline_full_schema.py` covering all 16 tables.
- Demo seed script: `app/seed_demo.py` with simple demo passwords (`admin123`, `doc123`, `pass123`) and full clinical histories + automatic aggregation pipeline run.
- Accessibility: WCAG 2.1 AA spot-checks and aria fixes across 10 key component/page files.

---

## 2. Key Architectural Invariants
- **No FKs in `regional_aggregates`**: `RegionalAggregate` table is strictly un-linked to patient records to preserve anonymization — verified by automated schema test.
- **Deterministic Crisis Engine**: Distress keywords and Panic SOS trigger `RiskAlert` rows directly, independently of LLM responses.
- **Role-Based Access Control**: Enforced at the FastAPI dependency layer (`get_current_user`, `get_current_doctor`, `get_current_admin`). Admin scope is separate from doctor clinical scope.
- **Offline Fallbacks**: Groq API fallback to local rule-based responses; Web Bluetooth fallback to simulated PPG signal; A-Frame WebXR fallback to 2D canvas controls.

---

## 3. Reference Commands
- **Backend tests:** `cd backend && .venv\Scripts\pytest.exe`
- **Seed scenarios:** `cd backend && .venv\Scripts\python.exe -m app.seed_vr`
- **Seed demo:** `cd backend && .venv\Scripts\python.exe -m app.seed_demo`
- **Alembic upgrade:** `cd backend && .venv\Scripts\python.exe -m alembic upgrade head`
- **Frontend lint:** `cd frontend && npm run lint`
- **Frontend build:** `cd frontend && npm run build`
