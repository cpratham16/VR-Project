# AGENTS.md

## Mandatory iteration workflow

Every feature iteration MUST follow the protocol in `RULES.md` (read it first). Short version, in order:

1. Read `RULES.md`, `CLAUDE.md`, `PROGRESS.md`, and the target iteration in `IMPLEMENTATION_PLAN.md`.
2. Inspect existing code, plan minimal change, implement.
3. Test/verify every acceptance criterion, inspect final diff.
4. Overwrite `## Current Status` in `CLAUDE.md` and append one dated entry to `PROGRESS.md`.
5. Stop — do not start the next iteration in the same close-out.

`CLAUDE.md` = live status snapshot (never stack history). `PROGRESS.md` = append-only log (never rewrite old entries).

## Commands

Backend (run from `backend/`; venv is committed at `backend/.venv`, Python 3.13):

```powershell
& .\.venv\Scripts\python.exe -m pytest                    # full suite (~40s; loads cross-encoder model)
& .\.venv\Scripts\python.exe -m pytest tests/test_vr.py   # single file
& .\.venv\Scripts\uvicorn.exe app.main:app --reload       # dev server on :8000
& .\.venv\Scripts\alembic.exe upgrade head                # migrations
& .\.venv\Scripts\alembic.exe revision --autogenerate -m "msg"
```

Frontend (run from `frontend/`): `npm run dev` (:5173), `npm run build` (= `tsc -b && vite build`), `npm run lint` (oxlint).

Seed scripts (after `alembic upgrade head`, from `backend/`): `python -m app.seed_vr` → `python -m app.seed_demo` (SQLAlchemy echo logging is very verbose — normal). RAG ingestion: `python -m app.seed_rag --sources seeds,intents --cap N --recreate`.

## Infrastructure & ports (non-obvious)

- Docker Postgres is exposed on host port **5433**, not 5432 (`5433:5432` in docker-compose). Port 5432 has an unremovable orphaned local Windows listener that rejects all auth — do not "fix" this back to 5432.
- Qdrant: :6333 (HTTP) / :6334, pinned `v1.19.0` matching `qdrant-client==1.19.0`. Backend: :8000. Frontend: :5173.
- Full pytest suite requires Docker Postgres running (`test_tracing.py` uses real `AsyncSessionLocal`). All other tests are hermetic (Qdrant runs in `:memory:` mode).
- `alembic.ini` contains a stale port-5432 URL — harmless: `alembic/env.py` overrides it with `settings.DATABASE_URL` from `.env`. Always run alembic from `backend/`.

## Secrets

Real Groq + Gemini API keys live in gitignored `backend/.env`. Never commit them; `.env.example` must stay key-free. User was advised to rotate both keys (they leaked into `.env.example` once during B1).

## Code gotchas (hard-earned)

- **Groq model**: `llama-3.3-70b-versatile` is decommissioned (caused silent fallback replies in chat). Working model: `openai/gpt-oss-20b` — verify against `GET /openai/v1/models` before switching.
- **httpx**: `resp.json()` is synchronous — never write `await resp.json()` (breaks mocks and wastes a coroutine).
- **asyncpg strict typing**: passing a Python `UUID` into a `VARCHAR` column raises `DataError: expected str, got UUID`. Cast with `str(...)` (bit us in `tracing.py`).
- **aframe-physics-system**: import the prebuilt bundle `'aframe-physics-system/dist/aframe-physics-system.min.js'`, NOT the package root. Vite chokes on its CJS source (`Uncaught ReferenceError: arguments is not defined`).
- A-Frame shadow type `pcfsoft` unsupported by bundled three.js — use `pcf`.
- Embeddings: Gemini `gemini-embedding-001` and fastembed `nomic-ai/nomic-embed-text-v1.5` are both 768-dim so the collection is provider-interchangeable. Bulk ingestion must use fastembed (Gemini free tier 429s under load).
- Screening severity lives in `ScreeningResult.severity_band` per row (type = "PHQ-9"/"GAD-7"); there are no `phq9_severity` attributes on the model.

## Layout map

- `backend/app/api/v1/` — FastAPI routers, registered in `router.py` under `/api/v1`. New routers must be added there.
- `backend/app/models/` + `schemas/` — SQLAlchemy models / Pydantic schemas; new models need an import in `models/__init__.py` or autogenerate misses them, plus an Alembic migration.
- `backend/app/services/` — business logic (RAG pipeline: `embeddings` → `vector_store` → `ranking` → `ai_companion` + `response_processor`; tracing in `tracing.py`).
- `frontend/src/pages/{patient,doctor,admin,auth}/` — role-scoped pages; routes wired in `App.tsx`, nav in `MainLayout.tsx`.
- Frontend API access goes through `src/api/client.ts` axios instance (`VITE_API_BASE_URL` + `/api/v1`, JWT from localStorage).

## Demo accounts

Seeded by `seed_demo.py`: admin@campus.edu/admin123, doctor1@campus.edu/doc123, alice..eve@campus.edu/pass123. VR scenarios ("Skyline Terrace", "Lecture Hall") come from `seed_vr.py`.
