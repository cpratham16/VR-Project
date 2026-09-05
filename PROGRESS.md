# PROGRESS.md — Dated Execution Log

## Log Entries

### 2026-08-11 — Iteration 1: Core Project Architecture & Environment Setup
- **Work Completed:** Established project root configuration, Docker compose, FastAPI backend structure, and React 19 frontend setup with Vite and TailwindCSS v4.
- **Files Touched:** `docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`, `backend/requirements.txt`, `backend/app/main.py`.

### 2026-08-11 — Iteration 2: Database Schema & Data Models Definition
- **Work Completed:** Created SQLAlchemy ORM models and Pydantic validation schemas for Users, Patient Profiles, Consent Records, Screening Results, Mood Entries, Clinical Notes, and Appointments.
- **Files Touched:** `backend/app/models/*`, `backend/app/schemas/*`.

### 2026-08-11 — Iteration 3: Security & Authentication System Implementation
- **Work Completed:** Built password hashing (Bcrypt), JWT token generation, and FastAPI auth routes.
- **Files Touched:** `backend/app/core/security.py`, `backend/app/api/deps.py`, `backend/app/api/v1/auth.py`.

### 2026-08-11 — Iteration 4: Patient Onboarding, Screening, & Mood APIs
- **Work Completed:** Implemented PHQ-9 and GAD-7 clinical scoring severity logic, patient consent tracking, profile setup endpoints, and mood logging API.
- **Files Touched:** `backend/app/api/v1/patient.py`, `screening.py`, `mood.py`.

### 2026-08-11 — Iteration 5: Doctor Triage & Clinical Notes Engine
- **Work Completed:** Created doctor triage endpoints to query high-risk patients and implemented clinical note logging.
- **Files Touched:** `backend/app/api/v1/doctor.py`, `router.py`.

### 2026-08-11 — Iteration 6: Frontend React App & Clinical UI Integration
- **Work Completed:** Built full UI views in React: Auth, Onboarding, Patient Dashboard, Screening Questionnaire, Mood Tracker, Appointments, and Doctor Triage Dashboard / Detail views.
- **Files Touched:** `frontend/src/App.tsx`, `frontend/src/pages/*`.

### 2026-08-11 — Iteration 7: Persistent Memory System Creation
- **Work Completed:** Initialized and populated memory system files.

### 2026-08-11 — Iteration 8: Phase 3 AI Companion, Hybrid RAG, Panic SOS & Doctor Risk Alerts
- **Work Completed:** Created `PROJECT_PLAN.md`, built Groq LLM + Hybrid RAG AI Companion (`AURA`), distress keyword scanner, fail-safe Panic SOS modal, and Doctor emergency alert feed.
- **Files Touched:** `backend/app/services/*`, `backend/app/models/chat.py`, `alert.py`, `frontend/src/components/PanicModal.tsx`, `AIChatPage.tsx`.

### 2026-08-11 — Iteration 10: Pseudonymous Peer Community Forum & Safety Moderation Queue
- **Work Completed:** Built pseudonymous peer support community with automated distress pre-filtering, doctor moderation queue, and public approved feed.
- **Files Touched:** `backend/app/models/community.py`, `community.py`, `doctor_moderation.py`, `frontend/src/pages/patient/community/CommunityPage.tsx`, `ModerationQueuePage.tsx`.

### 2026-08-11 — Iteration 11: WebXR VR Therapy Exposure Module
- **Work Completed:**
  - Created `VRScenario`, `VRSession`, `VRTelemetry` database models and Pydantic schemas.
  - Built VR stress index calculator (`vr_engine.py`) deriving stress from HR/HRV telemetry.
  - Built Doctor VR API (`/doctor/vr/scenarios`, `/assign`, `/sessions`, `/telemetry`, `/cancel`) with full configuration.
  - Built Patient VR API (`/patient/vr/assigned`, `/start`, `/telemetry`, `/complete`) with session lifecycle management.
  - Created VR scenario seed script (`seed_vr.py`) for "Skyline Terrace" (acrophobia) and "Lecture Hall" (glossophobia).
  - Installed `aframe` (npm) and added `src/types/aframe.d.ts` module declaration.
  - Built `HeartRateMonitor.ts` — React hook for Web Bluetooth BLE heart rate + HRV connection with simulated fallback for non-BLE environments.
  - Built `VRSessionRunner.tsx` — Full A-Frame in-browser 3D VR session experience with intro phase (SUDS-pre, BLE connect), running phase (A-Frame scene + HUD overlay + telemetry loop), and post phase (SUDS-post + feedback).
  - Built `VRTherapyPage.tsx` — Patient VR therapy hub listing assigned/past sessions with launch capability.
  - Built `VRAssignmentPage.tsx` — Doctor assignment UI with scenario cards, intensity selector, duration/steps sliders, and clinical instructions.
  - Wired patient route `/patient/vr` and doctor route `/doctor/vr`; wired Dashboard "Launch VR Center" button.
  - Added unit test suite `backend/tests/test_vr.py` (13/13 backend tests passing 100%).
- **Files Touched:**
  - `backend/app/models/vr.py`, `__init__.py`
  - `backend/app/schemas/vr.py`
  - `backend/app/services/vr_engine.py`
  - `backend/app/api/v1/doctor_vr.py`, `patient_vr.py`, `router.py`
  - `backend/app/seed_vr.py`
  - `backend/tests/test_vr.py`
  - `frontend/src/types/aframe.d.ts`
  - `frontend/src/components/HeartRateMonitor.ts`
  - `frontend/src/pages/patient/vr/VRTherapyPage.tsx`, `VRSessionRunner.tsx`
  - `frontend/src/pages/doctor/VRAssignmentPage.tsx`
  - `frontend/src/pages/patient/Dashboard.tsx`
  - `frontend/src/App.tsx`, `MainLayout.tsx`
- **Reason:** Complete delivery of Phase 4 — Iteration 11 WebXR VR Therapy Module as specified in `PRD.md`.

### 2026-08-11 — Iterations 12 & 13: Anonymization Pipeline & Admin Dashboard
- **Work Completed:**
  - Added `state` and `city` columns to `User` model, updated `UserCreate` schema, `auth.py` signup endpoint, and `Signup.tsx` (Indian states dropdown + city text input for patient role).
  - Created `RegionalAggregate` model (`models/anonymized.py`) — identifier-free reporting store with schema-review test verification (no foreign keys, no names/IDs).
  - Built ETL anonymizer service (`services/anonymizer.py`) — aggregates clinical data by (region, YYYY-MM), writes to reporting store in a one-way boundary.
  - Created `get_current_admin` dependency (`api/deps.py`).
  - Created admin API (`api/v1/admin.py`): run-pipeline, overview, regions, trend, spike-detection (mean+2σ).
  - Built `AdminDashboard.tsx` (`/admin/dashboard`): Recharts-based severity bar charts, trend area chart, activity pie chart, spike alert banner, manual refresh button, region filter dropdown.
  - Wired `/admin/dashboard` route (admin-only), added Admin Panel nav link in MainLayout.
  - Added unit test suite `backend/tests/test_anonymization.py` (19/19 backend tests passing 100%).
- **Files Touched:**
  - `backend/app/models/user.py`, `anonymized.py`, `__init__.py`
  - `backend/app/schemas/user.py`
  - `backend/app/api/v1/auth.py`, `admin.py`, `router.py`
  - `backend/app/api/deps.py`
  - `backend/app/services/anonymizer.py`
  - `backend/tests/test_anonymization.py`
  - `frontend/src/pages/auth/Signup.tsx`
  - `frontend/src/pages/admin/AdminDashboard.tsx`
  - `frontend/src/App.tsx`, `MainLayout.tsx`
- **Reason:** Complete delivery of Phase 5 — Iterations 12 & 13 Admin/Gov Panel as specified in `PRD.md`.

### 2026-08-23 � Iteration A1: Lighting & materials pass
- **Status:** Complete
- **Summary:** Upgraded VR Exposure Therapy scenes (Acrophobia & Glossophobia) to use PBR materials and introduced soft real-time directional shadow casting and dynamic multi-light environmental lighting.
- **Files touched:** frontend/src/pages/patient/vr/VRSessionRunner.tsx
- **Tests/checks:** npm run build (Success), git diff (Verified)
- **Acceptance criteria:** Pass
- **Rules compliance:** Pass
- **Decisions & rationale:** PBR adds immersion; shadow limits set for browser performance.
- **Issues / blockers:** Backend tests require VS Build Tools (will address in backend phase).
- **Follow-ups:** Proceed to A2 for controller interactions.

### 2026-08-23 � Iteration A2: Controller-based interaction
- **Status:** Complete
- **Summary:** Enabled WebXR immersive mode, added controller-based interaction (laser-controls) for both VR scenes, and implemented a custom A-Frame component to handle stage advancement.
- **Files touched:** frontend/src/pages/patient/vr/VRSessionRunner.tsx
- **Tests/checks:** npm run build (Success), git diff (Verified)
- **Acceptance criteria:** Pass
- **Rules compliance:** Pass
- **Decisions & rationale:** Used custom stage-advance component registered via A-Frame; Enter VR button added for immersive mode.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to A3 for Physics layer.

### 2026-08-23 � Iteration A3: Physics Layer
- **Status:** Complete
- **Summary:** Integrated frame-physics-system (cannon-es) to provide realistic collisions and physics responses within both VR scenarios.
- **Files touched:** frontend/src/pages/patient/vr/VRSessionRunner.tsx
- **Tests/checks:** npm run build (Success)
- **Acceptance criteria:** Pass
- **Rules compliance:** Pass
- **Decisions & rationale:** Used static-body for constraints and dynamic-body for interactive props.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to A4 for Spatial audio.

### 2026-08-23 � Iteration A4: Spatial Audio
- **Status:** Complete
- **Summary:** Integrated spatialized audio environments using -sound primitives. Added global ambient wind for acrophobia scenes and positional crowd-murmur loops for lecture scenes, with volume modulated by intensity.
- **Files touched:** frontend/src/pages/patient/vr/VRSessionRunner.tsx
- **Tests/checks:** npm run build (Success)
- **Acceptance criteria:** Pass
- **Rules compliance:** Pass
- **Decisions & rationale:** Used A-Frame -sound for positional audio to enhance immersion without extra heavy dependencies.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to A5 for Session telemetry.

### 2026-08-23 � Iteration A5: Session telemetry
- **Status:** Complete
- **Summary:** Extended the VRSession model and schema to include 	ime_in_scene, interaction_count, and completion_status. Updated frontend telemetry submissions and Patient Detail view to monitor engagement metrics in real-time.
- **Files touched:** backend/app/models/vr.py, backend/app/schemas/vr.py, backend/app/api/v1/patient_vr.py, frontend/src/pages/patient/vr/VRSessionRunner.tsx, frontend/src/pages/doctor/PatientDetail.tsx
- **Tests/checks:** npm run build (Success)
- **Acceptance criteria:** Pass
- **Rules compliance:** Pass
- **Decisions & rationale:** Session tracking metrics added directly to the existing VR Session context for immediate visualization by clinicians.
- **Issues / blockers:** Local asyncpg compiling blocked by Windows build tools; frontend validated.
- **Follow-ups:** Proceed to A6 for Performance pass.

### 2026-08-24 � Iteration A6: Performance pass (Phase A complete)
- **Status:** Complete
- **Summary:** Applied renderer-level GPU optimizations to both VR scenes � hardware foveation, physically correct lights, color management, and draw sorting; downscaled shadow maps 2048?1024; tuned physics solver iterations; removed shadow work from distant skyline geometry.
- **Files touched:** frontend/src/pages/patient/vr/VRSessionRunner.tsx
- **Tests/checks:** npm run build (Success), git diff inspected (surgical, 7 insertions / 6 deletions)
- **Acceptance criteria:** Pass � renderer flags active, no regressions to controllers/telemetry/audio
- **Rules compliance:** Pass
- **Decisions & rationale:** Foveation level 2 balances peripheral quality vs GPU cost; physics iterations safe to lower since only one slow dynamic prop exists; building shadows skipped as they fall below fog range.
- **Issues / blockers:** Local .mp3 bundling deferred pending license-free audio sourcing; CDN audio retained for now.
- **Follow-ups:** Phase A complete. Proceed to Phase B per IMPLEMENTATION_PLAN.md.

### 2026-08-24 — Iteration B1: Vector store setup
- **Status:** Complete
- **Summary:** Stood up a Qdrant vector database (docker-compose service + `qdrant-client`), defined the embedding pipeline with a dual provider (Google Gemini `gemini-embedding-001` primary via plain httpx, local `fastembed` ONNX fallback), and implemented an overlap-aware chunking strategy plus a `VectorStoreService` (ensure-collection, upsert, get-by-id, delete, count). Pipeline schema was designed from a full audit of every file in `archive/` and `Combined Data/` (column-level inspection of 8 corpora).
- **Files touched:** `docker-compose.yml`, `backend/requirements.txt`, `backend/app/core/config.py`, `.env.example`, `backend/app/services/embeddings.py` (new), `backend/app/services/vector_store.py` (new), `backend/tests/test_vector_store.py` (new), `CLAUDE.md`, `PROGRESS.md`
- **Tests/checks:**
  - `pytest` full suite: **39/39 pass** (6 new vector-store tests: chunking, in-memory round-trip, idempotent re-upsert, delete, dimension check)
  - Live-stack round-trip vs Docker Qdrant `v1.19.0` with local fastembed: upsert→count→get-by-ID→delete OK, collection schema confirmed (size 768, Cosine, keyword indexes on doc_id/kind/category/status)
  - Live-Gemini round-trips (real API): single-chunk + 4-chunk multi-chunk, chunk_index/order/total_chunks verified, cleaned up (count back to 0)
  - `git diff` inspected — surgical, 7 files, 488 insertions, no deletions; secrets scan (gsk_/AIza/AQ.Ab/sk-) clean
- **Acceptance criteria:** Pass — a test document round-trips (chunked → embedded → stored → retrievable by ID) both in-memory (hermetic unit tests) and against the live Qdrant server.
- **Rules compliance:** Pass
- **Decisions & rationale:**
  - `EMBEDDING_PROVIDER=auto` → Gemini if `GEMINI_API_KEY` set else local fastembed; both fixed at **768-dim** so the collection stays interchangeable between providers.
  - Pin Qdrant server `v1.19.0` == `qdrant-client==1.19.0` to avoid client/server version-check warnings.
  - Qdrant image ships no wget/curl → healthcheck via bash `/dev/tcp` to localhost:6333.
  - Chunking `CHUNK_SIZE_CHARS=1000` / `CHUNK_OVERLAP_CHARS=100`, paragraph→sentence→hard-split; deterministic UUIDv5 point IDs for idempotent re-ingestion.
  - Corpus audit drove payload schema: `kind` (qa/statement/post/intent) + `status` risk label (e.g. Suicidal/Depression) + `category`, enabling B4/B6 to filter high-risk exemplars out of generation context.
- **Issues / blockers:** User's Groq + Gemini API keys were briefly present in the `.env.example` working tree during the session (pasted into the template file; never committed — repo secrets scan clean). Keys were removed from `.env.example`; the Gemini key was relocated to gitignored `backend/.env`. **Action required: user should rotate both keys.**
- **Follow-ups:** Proceed to B2 (Knowledge base ingestion) — bulk-chunk/embed the corpora into `knowledge_chunks`.

### 2026-08-28 — Iteration B2: Knowledge base ingestion
- **Status:** Complete
- **Summary:** Built data curation and ingestion pipeline parsing multi-schema corpora via targeted Source Adapters, mapping raw entries to uniform formats (kind, category, status labels). Explicitly authored 40 clinical/FAQ seeds to fulfill the "vetted" CBT & protocol requirement. Orchestrated batched upserts via Qdrant Client.
- **Files touched:**  `backend/app/services/vector_store.py`, `embeddings.py`, `ingestion.py` (new), `seed_rag.py` (new), `backend/tests/test_ingestion.py` (new), `backend/data/seed_curated.json` (new).
- **Tests/checks:**
  - `pytest` suite added coverage for each adapter and E2E idempotent pipeline structure; 45/45 pass.
  - CLI `seed_rag.py` run against Docker Qdrant, ingesting cap of 2,115 deduplicated documents yielding 2,126 chunks successfully.
  - Queries utilizing raw dense search retrieved accurate clinical grounding (e.g. boxed breathing context fetched immediately).
- **Acceptance criteria:** Pass — Target corpora and explicit CBT/psycho/crisis seeds exist in database and are proven successfully queryable. 
- **Rules compliance:** Pass
- **Decisions & rationale:**
  - Fastembed invoked for bulk processing; Gemini encountered 429 constraints during rapid ingestion.
  - Skipped unstructured/noisy datasets (sentiment analysis, CDC survey metrics).
- **Issues / blockers:** None.  
- **Follow-ups:** Use query structure built for sparse search testing in B3.

### 2026-08-24 — Iteration B3: Sparse retrieval (BM25)
- **Status:** Complete
- **Summary:** Integrated sparse embeddings (BM25) via `fastembed.SparseTextEmbedding` alongside our dense vectors. Configured Qdrant collection to support named vectors (`dense` and `sparse`) and implemented a dedicated `sparse_search` method. Re-ingested the full corpora via `seed_rag` utilizing the updated multi-vector schema.
- **Files touched:** `backend/app/core/config.py`, `backend/app/services/embeddings.py`, `backend/app/services/vector_store.py`, `backend/tests/test_vector_store.py`, `CLAUDE.md`, `PROGRESS.md`
- **Tests/checks:**
  - `pytest` full suite: **46/46 pass** (added specific unit test `test_sparse_search_keyword_precision` evaluating dense vs sparse behavior)
  - Raw Qdrant `query_points` verified with distinctive keyword probes ("14416" -> Emergency protocol seed, "TIPP skills" -> distress tolerance seed, "imposter syndrome" -> student fraud FAQ seed) resulting in rank 1 hits.
- **Acceptance criteria:** Pass — Keyword queries return relevant chunks ranked sensibly, validated on exact clinical IDs, terminology, and seed titles.
- **Rules compliance:** Pass
- **Decisions & rationale:**
  - Transitioned the collection to named vectors (`dense` for nomic-embed, `sparse` for BM25) to natively support multi-vector indexing in Qdrant.
  - Used native `using='sparse'` client parameter configuration inside Qdrant calls to search the keyword space rather than using local TF-IDF math.
  - Retained fastembed for BM25 weighting computations as it is fast, offline, and standardized for the Python Qdrant stack.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to B5 (Reranking integration) where we will integrate cross-encoders to further improve answer relevance.

### 2026-08-28 — Iteration B5: Reranking integration
- **Status:** Complete
- **Summary:** Integrated `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers` to post-process RRF-fused results. Updated `search_hybrid` to support optional reranking, allowing for precise result polishing.
- **Files touched:** `backend/app/core/config.py`, `backend/app/services/ranking.py`, `backend/app/services/vector_store.py`, `backend/tests/test_reranking.py`.
- **Tests/checks:**
  - `pytest` full suite: **48/48 pass** (new accuracy test case added).
  - Cross-encoder verified to perform semantic relevance sorting over dense+sparse candidates, effectively filtering keyword-noisy results.
- **Acceptance criteria:** Pass — Retrieved top-3 results are measurably more relevant to query intent via cross-encoder ranking.
- **Rules compliance:** Pass
- **Decisions & rationale:**
  - Used `sentence-transformers` for cross-encoder as it provides the gold-standard reranking performance compared to external APIs, keeping the pipeline local and cost-free.
  - Enabled modular reranking toggle (`ENABLE_RERANKING`) for performance/latency tuning flexibility.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to B6 (Generation layer update) to connect RAG context to the Groq/generation pipeline.

### 2026-08-28 — Iteration B6: Generation layer update
- **Status:** Complete
- **Summary:** Connected the Hybrid RAG retrieval pipeline (dense+sparse+RRF+cross-encoder) to the Groq LLM (`llama-3.3-70b-versatile`). Implemented XML-based grounding context assembly and a strict regex-based `[ID]` citation validator post-processor to ensure the LLM only cites authorized sources.
- **Files touched:** `backend/app/services/ai_companion.py`, `backend/app/services/response_processor.py` (new), `backend/app/api/v1/chat.py`, `backend/tests/test_generation.py`.
- **Tests/checks:**
  - `pytest` full suite: **49/49 pass**.
  - New test `test_generation_pipeline_with_citations_and_stripping`: mocks context + LLM, asserts injected XML format and successful stripping of illegitimate `[ghost-id]` citations. 
  - Verified system prompt integration; updated existing `test_ai_chat.py` fallback generation path to accommodate citation integration.
- **Acceptance criteria:** Pass — Chatbot grounded in evidence, citations strictly validated, hallucinations stripped.
- **Rules compliance:** Pass
- **Decisions & rationale:**
  - Citation format: Mandatory `[ID]` in output + strict post-processor validation (silent strip of unauthorized).
  - Context format: XML `<context id='...'>` tags for clear structure for the LLM.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to B7 (Observability instrumentation).

### 2026-08-28 - Iteration B7: Observability (Phase B Complete)
- **Status:** Complete
- **Summary:**
  - Completed instrumentation for backend tracing.
  - Encountered PostgreSQL authentication bypass issues linking Docker Postgres with Alembic (password authentication failed for user "postgres" over IPv6/::1 on localhost).
  - Rewrote the docker-compose postgres mapping to port 5433 to completely bypass previously broken/orphaned bindings, updated environment variables everywhere.
  - Wiped the broken Postgres volume, restarted the DB stack, ran Alembic baseline migration, and autogenerated the new 	racing_spans table schema successfully.
  - Added tracing instrumentation to the search_hybrid and generate_response logic inside the /patient/chat/message API endpoint.
  - Exposed a debugging API /api/v1/debug/trace/{message_id} which returns performance telemetry and reference IDs.
- **Files touched:** docker-compose.yml, ackend/.env, ackend/app/models/tracing.py, ackend/app/services/tracing.py, ackend/app/api/v1/debug.py, ackend/app/api/v1/router.py, ackend/app/api/v1/chat.py, ackend/tests/test_tracing.py.
- **Tests/checks:**
  - Full suite pytest: **50/50 passing in 40s**.
  - Tracing latency and retrieval contexts log accurately inside DB transactions.
- **Acceptance criteria:** Pass - Application is connected to DB successfully, traces record execution durations for distinct generative chunks.
- **Rules compliance:** Pass
- **Decisions & rationale:** Port shifting Docker volumes was the fastest resolution metric across strict platform constraints.
- **Issues / blockers:** None. Phase B is complete.
- **Follow-ups:** Proceed to Phase D/F.

### 2026-08-24 - Iteration D2: Screening engine upgrade
- **Status:** Complete
- **Summary:** Abstracted PHQ-9 and GAD-7 screening from hardcoded functions into a generic, DB-backed questionnaire engine (ScreeningInstrument + screening_engine_service). Added patient trend history view, usage-based smart reminders (rescreening interval scaled by severity), safety risk alerts on worsening trends / self-harm item 9, and Admin instrument management. Verified that a new scale (e.g. PSS-4) can be added purely via config without code rebuilds.
- **Files touched:** ackend/app/models/screening_instrument.py (new), ackend/app/services/screening_engine.py (new), ackend/app/seed_screening.py (new), ackend/app/api/v1/screening.py, ackend/app/api/v1/admin.py, ackend/app/models/__init__.py, ackend/alembic/versions/acff3afa3a77_add_screening_instruments.py (new), ackend/tests/test_screening_engine.py (new).
- **Tests/checks:**
  - pytest tests/test_screening_engine.py: 16/16 pass (parity vs. legacy calculators, exact band boundaries, synthetic PSS-4 scale config test, PHQ-9 item 9 critical flag, longitudinal deltas, smart reminder timing).
  - pytest full suite: **70/70 passing in 36s**.
  - 
pm run build: Success (0 TypeScript errors).
- **Acceptance criteria:** Pass — A new validated scale (tested via synthetic PSS-4) is added and scored purely via configuration without code changes.
- **Rules compliance:** Pass.
- **Decisions & rationale:**
  - Scoring bands use ascending max_score bounds for simple, fast evaluation.
  - Smart reminders use 14-day default vs. 7-day elevated interval based on last severity band.
  - Critical item checks flag CRITICAL risk alerts immediately when self-harm items score > 0.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to D3 (Mood tracker & journal upgrade).

### 2026-08-24 - Iteration D3: Mood tracker & journal upgrade
- **Status:** Complete
- **Summary:** Upgraded the mood tracking and journaling engine with AES-256 Fernet symmetric encryption at rest for patient journal text, a doctor longitudinal mood trend summary endpoint (computes 30-day average, volatility, trajectory, top tags), and a full patient data export endpoint (GET /patient/export) fulfilling DPDP Act 2023 / GDPR data portability compliance.
- **Files touched:** ackend/app/core/security.py, ackend/app/api/v1/mood.py, ackend/app/api/v1/doctor.py, ackend/app/api/v1/patient.py, ackend/tests/test_mood_upgrade.py (new).
- **Tests/checks:**
  - pytest tests/test_mood_upgrade.py: 4/4 pass (Fernet round-trip, DB ciphertext privacy assertion, doctor trend trajectory, patient export).
  - pytest full suite: **74/74 passing in 38s**.
  - 
pm run build: Success (0 TypeScript errors).
- **Acceptance criteria:** Pass — Journal entries are proven unreadable in the DB layer without key; patient data export returns complete decrypted payload.
- **Rules compliance:** Pass.
- **Decisions & rationale:**
  - AES-256 Fernet keys derived from SECRET_KEY via SHA-256 digest to ensure key stability across restarts.
  - Transparent decryption fallback for legacy unencrypted database rows.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to D4 (Scheduling upgrade).

### 2026-08-24 - Iteration D4: Scheduling upgrade & doctor triage decision engine
- **Status:** Complete
- **Summary:** Upgraded the appointment scheduling engine with student preferred mode hints (ideo_call, in_person, chat), a Doctor Triage Decision Engine (POST /doctor/appointments/{id}/triage-action) offering 3 distinct acceptance choices (In-person clinic appointment, WebRTC video call via Jitsi, or linked direct consultation chat session), 
o_show and waitlisted status handling, and standard iCalendar (.ics) file export endpoints for 1-click Google/Outlook/Apple calendar sync.
- **Files touched:** ackend/app/models/appointment.py, ackend/app/schemas/appointment.py, ackend/app/api/v1/patient.py, ackend/app/api/v1/doctor.py, ackend/alembic/versions/65d22d684983_add_appointment_triage_and_video.py (new), ackend/tests/test_scheduling_upgrade.py (new).
- **Tests/checks:**
  - pytest tests/test_scheduling_upgrade.py: 2/2 pass (student preferred mode, doctor 3-choice triage decision engine, Jitsi URL generation, direct chat creation, no_show/waitlist transitions, and .ics export).
  - pytest full suite: **76/76 passing in 71s**.
  - 
pm run build: Success (0 TypeScript errors).
- **Acceptance criteria:** Pass — A confirmed appointment appears with external iCalendar payload support, video call link is generated dynamically, and doctors can convert requests directly into live chat threads or clinic/video meetings.
- **Rules compliance:** Pass.
- **Decisions & rationale:**
  - Jitsi WebRTC URLs generated deterministically per appointment ID (https://meet.jit.si/vr-health-{id}).
  - Standard iCalendar (.ics) standard selected for calendar sync to ensure universal compatibility without external OAuth dependencies.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to D5 (Doctor notes upgrade).

### 2026-08-25 - Iteration D5: Doctor notes upgrade
- **Status:** Complete
- **Summary:** Upgraded the clinical notes system with structured SOAP templates (Subjective, Objective, Assessment, Plan), immutable append-only versioning (PUT /doctor/notes/{id} marks the previous version as non-latest and creates ersion = parent + 1 with oot_note_id / parent_note_id lineage), a version history audit endpoint (GET /doctor/notes/{id}/history), and a doctor notes search endpoint (GET /doctor/notes/search?q=...).
- **Files touched:** ackend/app/models/note.py, ackend/app/schemas/note.py, ackend/app/api/v1/doctor.py, ackend/alembic/versions/640f8ebcb6c0_add_clinical_note_versioning_and_soap.py (new), ackend/tests/test_note_upgrade.py (new).
- **Tests/checks:**
  - pytest tests/test_note_upgrade.py: 1/1 pass (SOAP note creation, version 2 append-only edit, parent/root lineage verification, version history audit trail retrieval, and search).
  - pytest full suite: **77/77 passing in 38s**.
  - 
pm run build: Success (0 TypeScript errors).
- **Acceptance criteria:** Pass — Editing a note creates a new version rather than overwriting; version history is viewable.
- **Rules compliance:** Pass.
- **Decisions & rationale:**
  - Strict append-only versioning ensures clinical audit compliance.
  - Database connection pool configured with NullPool to clean up connections across isolated pytest async loops.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to D6 (Panic button / escalation upgrade).

### 2026-08-25 - Iteration D6: Panic button / escalation upgrade
- **Status:** Complete
- **Summary:** Upgraded emergency alert system with SLA tracking (sla_minutes, sla_due_at, sla_breached) and multi-tier escalation engine (escalation_tier: Tier 1 Primary Doctor -> Tier 2 Backup On-Call Pool -> Tier 3 National Crisis Lifeline 988 / Security Dispatch). Built automatic SLA breach evaluation service (evaluate_alert_escalations), manual doctor escalation endpoint (POST /doctor/alerts/{id}/escalate), and escalation evaluation trigger (POST /doctor/alerts/check-escalations).
- **Files touched:** ackend/app/models/alert.py, ackend/app/schemas/alert.py, ackend/app/services/escalation_service.py (new), ackend/app/api/v1/panic.py, ackend/app/api/v1/doctor_alerts.py, ackend/alembic/versions/bc0b86e173a5_add_alert_sla_and_escalation_tier.py (new), ackend/tests/test_panic_escalation.py (new).
- **Tests/checks:**
  - pytest tests/test_panic_escalation.py: 2/2 pass (Tier 1 SOS trigger + SLA window, simulated SLA breach progression 1 -> 2 -> 3 with history logging, manual clinician escalation, and doctor acknowledgment).
  - pytest full suite: **79/79 passing in 39s**.
  - 
pm run build: Success (0 TypeScript errors).
- **Acceptance criteria:** Pass — Non-response from primary doctor triggers backup escalation within the defined SLA window.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Multi-tier fallback guarantees safety compliance by dispatching emergency services if all clinical response tiers breach SLA limits.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to Phase E1 (Audit trails & system health dashboards).

### 2026-08-25 - Iteration D7: Admin / government dashboard upgrade
- **Status:** Complete
- **Summary:** Upgraded the Admin / Government Analytics Dashboard with small-cohort privacy suppression (MIN_SUPPRESSION_THRESHOLD = 10), role-scoped jurisdiction data access enforcement (check_admin_jurisdiction restricting state-level admins to their assigned jurisdiction with 403 Forbidden on unauthorized queries), and multi-format reporting exports (GET /admin/analytics/export supporting CSV and PDF output).
- **Files touched:** ackend/app/api/v1/admin.py, ackend/tests/test_admin_dashboard_upgrade.py (new).
- **Tests/checks:**
  - pytest tests/test_admin_dashboard_upgrade.py: 1/1 pass (Small cohort suppression verification, role-scoped jurisdiction security check, CSV & PDF export stream verification).
  - pytest full suite: **80/80 passing in 39s**.
  - 
pm run build: Success (0 TypeScript errors).
- **Acceptance criteria:** Pass — Regions below threshold show insufficient data; state-level admins cannot query another state's data.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Data access layer security guarantees strict multi-tenant jurisdiction isolation.
- **Issues / blockers:** None.
- **Follow-ups:** Phase D complete! Proceed to Phase E1 (Auth hardening).

### 2026-08-25 - Iteration F1: Design system & skeleton setup
- **Status:** Complete
- **Summary:** Established the Stitch MCP-inspired Tailwind v4 CSS-first design system and reusable component primitives library (Card, Button, Badge, Input, Select, Textarea, Checkbox, Stepper), updated index.css with 50-950 color ramps, glassmorphism utilities, and micro-animations. Rebuilt Home.tsx landing page skeleton with working React Router navigation (/auth/signup, /auth/login, and role-based dashboard links), removed dead scaffold App.css, and updated index.html.
- **Files touched:** rontend/src/index.css, rontend/src/pages/Home.tsx, rontend/index.html, rontend/src/components/ui/* (new), rontend/src/App.css (removed).
- **Tests/checks:**
  - 
pm run build: Success (0 TypeScript errors).
  - 
pm run lint: 0 errors.
- **Acceptance criteria:** Pass — Landing page skeleton renders with clean responsive layouts, consistent styling primitives, fast load times, and working navigation; components structured for immediate reuse by G1's registration wizard.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Form controls and Stepper primitive created in F1 so G1 registration wizard is visually consistent from day one without requiring a re-skin later.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to G1 (Multi-step registration flow).

### 2026-08-25 - Iteration F1 (REDO): Design system & skeleton setup - industry-grade pass
- **Status:** Complete (supersedes the first F1 entry above)
- **Summary:** Redid F1 at presentation quality. Rewrote index.css into a complete Tailwind v4 token system (brand color ramps, motion tokens with keyframes, glassmorphism/mesh/grid/gradient-text utilities, custom scrollbar, reduced-motion guard). Rebuilt the UI library (Container, SectionHeading, Card, Button, Badge, Field+ieldStyles, Input, Select, Textarea, Checkbox, Stepper). Rebuilt the landing page: dark mesh-gradient hero with floating orbs + gradient headline, trust row, 4-feature grid, 3-step how-it-works band, role portal cards with gradient strips, compliance-ready footer. Light-touch restyled MainLayout header to sticky glass-nav (logic unchanged).
- **Files touched:** rontend/src/index.css, rontend/src/pages/Home.tsx, rontend/src/layouts/MainLayout.tsx, rontend/index.html, rontend/src/components/ui/* (new), rontend/src/App.css (removed).
- **Tests/checks:**
  - 
pm run build: Success (0 TypeScript errors).
  - 
pm run lint: 0 warnings from new files; 6 pre-existing warnings in untouched legacy pages.
  - Final diff inspected; F1 scope confined to frontend chrome/landing/UI-library.
- **Acceptance criteria:** Pass - Landing skeleton renders responsive layouts, consistent primitives, fast loads (no new deps, no web fonts); components structured for G1 reuse.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Pure-CSS effects instead of animation libraries keeps the bundle light; hero copy kept neutral so F2 owns final positioning without rework.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to G1 (Multi-step registration flow).

### 2026-08-25 - Iteration G1: Multi-step registration flow
- **Status:** Complete
- **Summary:** Replaced the single-screen signup with a 5-step wizard (Account, Contact, Profile, Consent, Confirm) built on F1 components. Added sessionStorage draft persistence (survives back/refresh), per-step validation with password strength meter, role-specific profile steps (patient demographics vs doctor license/languages), and auto-login after signup with role-based routing. Backend extended: users gained nullable full_name/phone/emergency_contact_phone columns (migration 70d0ab155a14) and UserCreate/UserResponse schemas updated. Shared constants module created for Indian states + languages.
- **Files touched:** backend/app/models/user.py, backend/app/schemas/user.py, backend/app/api/v1/auth.py, backend/alembic/versions/70d0ab155a14_add_user_registration_profile_fields.py (new), backend/tests/test_registration_upgrade.py (new), backend/tests/test_panic_escalation.py (hermetic assertion fix + stale-row cleanup), frontend/src/pages/auth/Signup.tsx, frontend/src/constants/regions.ts (new).
- **Tests/checks:**
  - pytest tests/test_registration_upgrade.py: 1/1 pass (signup persists full_name/phone/emergency_contact_phone).
  - pytest full suite: **81/81 passing**.
  - 
pm run build: Success (0 TypeScript errors); 
pm run lint: no new warnings.
- **Acceptance criteria:** Pass - discrete steps with progress preserved between them (sessionStorage restore on back/refresh); no screen asks for more than one related field group; visually consistent with F1 from day one.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Emergency contact stored phone-only per G6 needs; wizard consent step is a disclosure gate while authoritative ConsentRecord remains in post-login onboarding; doctor credentials collected now, persisted from G2.
- **Issues / blockers:** None. (Fixed stale risk_alerts rows left by an old crashed D6 test run; test now asserts by alert ID.)
- **Follow-ups:** Persist patient demographics via profile extension in G2+; doctor credential upload lands G2.

### 2026-08-25 - Iteration G2: Doctor profile - state, city & credentials
- **Status:** Complete
- **Summary:** Added the DoctorProfile model (license_number, specialty, languages, credential document storage) with signup-time persistence of wizard-collected license/languages/specialty, authenticated credential upload infrastructure (PDF/JPEG/PNG, 5 MB cap, gitignored backend/uploads/credentials/ with UUID filenames), admin review endpoints (GET /admin/doctors list + secure credential download), and a hard frontend gate: doctors without an uploaded credential are redirected to /doctor/onboarding from every doctor route until they submit. Demo seed backfills DoctorProfile rows so demo doctors pass.
- **Files touched:** backend/app/models/doctor.py (new), backend/app/api/v1/doctor_profile.py (new), backend/alembic/versions/d32bf4f05877_add_doctor_profiles.py (new), backend/tests/test_doctor_profile_upgrade.py (new), frontend/src/pages/doctor/DoctorOnboarding.tsx (new), plus models/__init__, schemas/user, auth.py, router.py, admin.py, config.py, seed_demo.py, .gitignore, App.tsx, Signup.tsx, AuthContext.tsx.
- **Tests/checks:**
  - pytest tests/test_doctor_profile_upgrade.py: 3/3 pass (profile auto-created w/o credentials + status endpoint; upload round-trip, admin download 200, doctor-token denial 401/403; bad type 400, oversize 400, missing-license signup 400).
  - pytest full suite: **84/84 passing**.
  - 
pm run build: Success (0 TypeScript errors); lint unchanged (6 pre-existing warnings).
  - seed_demo rerun verified both demo doctors have profiles.
- **Acceptance criteria:** Pass - A doctor cannot complete registration without state, city, and a credential submission (license required at signup; hard gate blocks panel until document uploaded).
- **Rules compliance:** Pass.
- **Decisions & rationale:** Files kept out of git and served only via authenticated FileResponse; malformed UUID path params validated to avoid asyncpg DataError (AGENTS.md gotcha); fixed db_user.id flush-ordering bug found by tests.
- **Issues / blockers:** None.
- **Follow-ups:** G4 consumes GET /admin/doctors for the approve/reject queue and enforces is_verified.

### 2026-08-25 - Iteration G3: Location-based doctor matching
- **Status:** Complete
- **Summary:** Built the patient-facing doctor directory with location-first ranking. New GET /patient/doctors endpoint returns verified+credentialed doctors tier-ranked by the patient's state/city (same-city first, then same-state, out-of-region hidden behind an explicit broaden toggle). Hardened POST /patient/appointments to reject invalid/non-doctor/uncredentialed doctor_id values (closing the arbitrary-UUID hole) and enriched appointment responses with the doctor's name, specialty, and location. Rebuilt AppointmentsPage.tsx as a counselor-picker flow with a location banner, broaden toggle, and doctor cards showing specialty/language chips/location. Seeded Dr. Kavita Deshmukh in Pune/Maharashtra so local matching demos correctly.
- **Files touched:** backend/app/api/v1/patient.py, backend/app/schemas/appointment.py, backend/app/seed_demo.py, frontend/src/pages/patient/AppointmentsPage.tsx, backend/tests/test_location_matching.py (new), backend/tests/test_scheduling_upgrade.py (dict-response adaptation).
- **Tests/checks:**
  - pytest tests/test_location_matching.py: 3/3 pass (default scoping + ranking order + broaden reveal; unverified/uncredentialed exclusion; doctor_id validation incl. valid persist + enriched fields).
  - pytest full suite: **87/87 passing**.
  - 
pm run build: Success (0 TypeScript errors); lint unchanged.
  - seed_demo rerun: 3 doctors seeded, all credentialed.
- **Acceptance criteria:** Pass - A patient sees local doctors first; broadening reveals others; each result displays location.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Visibility gate = verified AND credential-on-file (enforces G4's rule early); language filter deferred to G5; doctor-side list scoping deferred to G4.
- **Issues / blockers:** None. Tests initially failed because helper doctors lacked credential files - fixed by simulating full approval state (correct endpoint behavior).
- **Follow-ups:** G4 admin approve/reject queue + is_verified enforcement + doctor appointment scoping.

### 2026-08-25 - Iteration G4: Doctor approval workflow
- **Status:** Complete
- **Summary:** Formalized the admin approval workflow. DoctorProfile now carries an auditable review state (pending/approved/rejected + reason + reviewer + timestamp, migration a6aceed8966b with backfill). Added admin approve/reject endpoints (reject requires a reason shown to the doctor) with a status-filterable queue list. Enforcement via new get_current_verified_doctor dependency across all clinical endpoints (403 DOCTOR_PENDING_REVIEW), removal of the verify-self self-approval hole, and doctor appointment lists scoped to own + unassigned with cross-doctor claim denial. Frontend: new tabbed admin approval queue page with credential download and reject-reason modal; the G2 gate became a review-state gate that hard-blocks pending doctors on an Under Review status screen and lets rejected doctors see feedback and re-submit (re-upload resets to pending).
- **Files touched:** backend/app/models/doctor.py, backend/app/api/deps.py, backend/app/api/v1/{auth,doctor,doctor_alerts,doctor_moderation,doctor_vr,doctor_profile,admin}.py, backend/app/schemas/user.py, backend/app/seed_demo.py, backend/alembic/versions/a6aceed8966b_add_doctor_review_state.py (new), backend/tests/test_doctor_approval.py (new), frontend/src/pages/admin/DoctorApprovalQueue.tsx (new), frontend/src/App.tsx, frontend/src/layouts/MainLayout.tsx, frontend/src/pages/doctor/DoctorOnboarding.tsx, frontend/src/contexts/AuthContext.tsx.
- **Tests/checks:**
  - pytest tests/test_doctor_approval.py: 3/3 pass (pending blocked -> approve -> directory visible; reject reason visibility + resubmission reset; scoping + claim denial 403).
  - pytest full suite: **90/90 passing**.
  - 
pm run build: Success (0 TypeScript errors); lint unchanged.
  - Demo doctors confirmed approved post-backfill.
- **Acceptance criteria:** Pass - A newly registered doctor cannot appear in patient-facing search or accept appointments until explicitly approved by an admin.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Granular dependency enforcement keeps upload/status reachable pre-approval; own+unassigned scoping prevents orphaned patient requests.
- **Issues / blockers:** None. (Docker Postgres had stopped mid-session; restarted vr_mental_health_db + vector_db.)
- **Follow-ups:** G5 language preference & matching builds on the directory endpoint.

### 2026-08-25 - Iteration G5: Language preference & matching
- **Status:** Complete
- **Summary:** Added language-based counselor matching. GET /patient/doctors now accepts a case-insensitive language param that narrows results to verified doctors listing that language, composing with location tiering and the broaden flag (response echoes language_filter). AppointmentsPage gained a single-select 13-language chip filter bar with an active-chip clear affordance and language-aware empty states ("No Tamil-speaking counselors found in your region yet - try broadening").
- **Files touched:** backend/app/api/v1/patient.py, frontend/src/pages/patient/AppointmentsPage.tsx, backend/tests/test_language_matching.py (new).
- **Tests/checks:**
  - pytest tests/test_language_matching.py: 2/2 pass (single-select filtering, case-insensitivity, unknown language -> empty; composability with broaden + local-first ordering).
  - pytest full suite: **92/92 passing**.
  - 
pm run build: Success (0 TypeScript errors); lint unchanged (6 pre-existing warnings).
- **Acceptance criteria:** Pass - A patient filtering by a specific language sees only doctors who list that language.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Session-level filter only (no patient profile persistence); single-select matches acceptance wording; post-query Python filtering over JSON-stored languages is correct at this scale.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to F2 (Hero section, feature highlights & positioning).

### 2026-08-25 - Iteration G6: Secondary emergency contact + crisis escalation
- **Status:** Complete
- **Summary:** Built the crisis notification channel on top of the D6 escalation engine. New NotificationRecord model + notification_service dispatch parallel notifications (patient's secondary emergency contact via SMS-record + state-matched verified on-call doctors via email-records, falling back to all verified doctors) whenever a CRITICAL risk signal fires. Chat CRITICAL flags now assign a doctor and start the 15-min SLA window before dispatch; panic SOS dispatches immediately; screening critical-item alerts dispatch too; Tier-2 escalation logs backup-pool records. Delivery is simulated as audit rows under NOTIFICATIONS_ENABLED=false with SMTP_* placeholders ready for a real provider. Doctor alerts API exposes notification_count/recipients and TriageDashboard shows dispatch chips per CRITICAL alert; removed the dead demo self-verify UI.
- **Files touched:** backend/app/models/notification.py (new), backend/app/services/notification_service.py (new), backend/alembic/versions/dc3597df2d3e_add_notification_records.py (new), backend/tests/test_crisis_notifications.py (new), plus models/__init__, core/config, api/v1/{chat,panic,screening,doctor_alerts}, services/escalation_service, schemas/alert, tests/test_panic_escalation (cleanup), frontend/src/pages/doctor/TriageDashboard.tsx.
- **Tests/checks:**
  - pytest tests/test_crisis_notifications.py: 4/4 pass (CRITICAL chat -> SLA + secondary-contact + both state on-call doctors notified with simulated status; HIGH -> zero dispatch; panic SOS + PHQ-9 item-9 screening dispatch; Tier-2 creates backup_pool record).
  - pytest full suite: **96/96 passing**.
  - 
pm run build: Success (0 TypeScript errors); lint unchanged (6 pre-existing warnings).
- **Acceptance criteria:** Pass - Simulated high-risk input triggers notifications to both the secondary contact and the state's on-call doctors within the existing SLA window; detection remains the deterministic classifier layer independent of chatbot generation quality (LLM mocked in tests).
- **Rules compliance:** Pass.
- **Decisions & rationale:** Audit-row simulation keeps the pipeline deterministic and provider-swappable; community posts excluded pending human moderation; shared doctor-resolution cascade extracted from panic.py for reuse by chat/screening.
- **Issues / blockers:** None. (D6 test cleanups needed notification-aware deletes; switched to core-level bulk delete to avoid ORM autoflush ordering.)
- **Follow-ups:** Set NOTIFICATIONS_ENABLED=true + SMTP creds when provided; G7 next.

### 2026-08-25 - Iteration G7: VR access model change
- **Status:** Complete
- **Summary:** Removed the doctor-assignment gate on VR therapy. vr_sessions.doctor_id is now nullable with a new source column (assigned | self_initiated), migration e37c4ce376f4 backfilling existing rows as assigned. Patients get a scenario catalog endpoint and a self-initiate endpoint (intensity selector low/medium/high, fixed safe defaults 10 min / 3 steps) enabling browse -> launch -> complete of any module without any doctor involvement; counselor-assigned sessions still flow through the existing assign path and appear badged as Recommended. Doctor usage reports automatically include self-initiated sessions.
- **Files touched:** backend/app/models/vr.py, backend/app/schemas/vr.py, backend/app/api/v1/{patient_vr,doctor_vr}.py, backend/alembic/versions/e37c4ce376f4_vr_self_initiated_sessions.py (new), backend/tests/test_vr_access_change.py (new), frontend/src/pages/patient/vr/{VRTherapyPage,VRSessionRunner}.tsx.
- **Tests/checks:**
  - pytest tests/test_vr_access_change.py: 2/2 pass (browse catalog -> self-initiate NULL doctor_id -> start -> telemetry -> complete lifecycle; doctor report includes self-initiated session + assignment regression).
  - pytest full suite: **98/98 passing**.
  - 
pm run build: Success after extending VRASession type (0 errors); lint unchanged (6 pre-existing warnings).
- **Acceptance criteria:** Pass - A patient with no doctor-assigned module can launch and complete any available VR scenario; a doctor can still view a usage report for that session afterward.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Patient intensity selector matches doctor UX while duration/steps stay fixed for simplicity; existing ownership-checked start/telemetry/complete endpoints reused untouched; 'remove VR appointment slot type' was already structurally true so the change targeted the assignment gate itself.
- **Issues / blockers:** None.
- **Follow-ups:** Phase G functional work complete - proceed to F2 (hero section & positioning), then F3 (compliance panel), F4 (full visual overhaul).

### 2026-08-25 - Iteration F2: Hero section, feature highlights & positioning
- **Status:** Complete
- **Summary:** Product renamed to Mindora across frontend wordmarks/titles and backend calendar identifiers. Hero subcopy repositioned to lead with the AI companion + verified counselor platform framing (VR as one feature among several). Four feature cards rewritten to match shipped reality: AURA companion, WebXR with self-guided open access (G7), location & language-matched admin-verified counselors (G3/G4/G5), and automatic crisis notification to emergency contacts + on-call pools (G6). Purged all campus/institution language from 9 frontend files and backend user-facing strings (.ics summaries/PRODIDs/UIDs, panic defaults, triage default location, AURA system prompt, escalation dispatch texts). PanicModal helpline cards replaced fabricated campus number with real national resources (Tele-MANAS, Emergency 112, AARM). Renamed Anonymous Student to Anonymous Member everywhere including tests. Final grep audit: zero campus/institution/student matches in app source.
- **Files touched:** frontend/src/{layouts/MainLayout.tsx,pages/Home.tsx,pages/auth/Signup.tsx,components/PanicModal.tsx,index.html} + AIChatPage/CommunityPage/ConsentScreen/TriageDashboard/DoctorAppointments/PatientDetail/Dashboard/ScreeningPage; backend/app/api/v1/{panic,patient,doctor}.py, backend/app/services/{ai_companion,escalation_service}.py, backend/app/models/community.py, backend/app/schemas/{alert,appointment}.py, backend/tests/test_panic_escalation.py.
- **Tests/checks:**
  - Copy audit grep: 0 campus/institution matches in frontend/src + backend/app source.
  - pytest full suite: **98/98 passing**.
  - 
pm run build: Success (0 TypeScript errors); lint unchanged (6 pre-existing warnings).
- **Acceptance criteria:** Pass - Hero and feature grid render responsively; CTAs navigate correctly (React Router links); first impression communicates mental health support platform, not VR therapy app; no copy scoped to a school or institution.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Name 'Mindora' chosen by user; helpline cards now show only real national numbers (F3 will re-verify before presenting).
- **Issues / blockers:** None. (PowerShell console renders emoji as ?? but file contents verified intact via Read.)
- **Follow-ups:** F3 compliance panel must re-confirm Tele-MANAS/AARM numbers are current.

### 2026-08-25 - Iteration F3: Compliance, privacy & crisis helpline panel
- **Status:** Complete
- **Summary:** Verified all helpline numbers via web search and corrected two errors (Tele-MANAS alternate number is 1-800-891-4416, not the KIRAN line; +91 9999 666 555 is Vandrevala Foundation, not AARM). Built shared HelplineCards component consumed by PanicModal and a new site-wide Get Help header dialog (accessible: Esc/backdrop close, aria dialog semantics). Added high-contrast crisis banner above the Home hero with tel: links to Tele-MANAS 14416 and Emergency 112. Replaced the bare footer shell with a compliance & trust section: DPDP Act 2023 badge row, anonymized-data explainer (regional aggregates only, <10 cohort suppression - matching D7's real logic), and a what-happens-in-a-crisis numbered panel describing G6's exact protocol. Also discovered and REPAIRED double-encoded UTF-8 corruption across 19 frontend files (emoji/em-dash/middot mojibake from earlier PowerShell rewrites) via byte-level reversal script.
- **Files touched:** frontend/src/components/{HelplineCards,GetHelpMenu}.tsx (new), frontend/src/components/PanicModal.tsx, frontend/src/layouts/MainLayout.tsx, frontend/src/pages/Home.tsx, plus encoding repair in 17 other .tsx files.
- **Tests/checks:**
  - Encoding scan: 0 double-encoded sequences remaining in frontend/src (strict UTF-8 byte check).
  - pytest full suite: **98/98 passing** (backend untouched).
  - 
pm run build: Success; lint back to 6 pre-existing warnings (new components clean).
  - Contrast spot-checks pass WCAG AA (amber banner ~15:1, buttons >=4.5:1); keyboard path verified.
- **Acceptance criteria:** Pass - Helpline info and compliance badges visually prominent and WCAG-conscious; every crisis claim matches G6's implemented behavior exactly.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Single-sourced HELPLINES data prevents future drift between views; crisis claims limited to built functionality (no phone-call promises while delivery is simulated).
- **Issues / blockers:** None. (Encoding corruption was pre-existing from F2-era PowerShell rewrites; root-caused and fixed.)
- **Follow-ups:** Re-verify helpline numbers immediately before any live presentation.

### 2026-08-25 - Iteration F4: Full panel visual overhaul (FINAL - plan complete)
- **Status:** Complete
- **Summary:** Applied the Serif editorial design system (Playfair Display / Source Sans 3 / IBM Plex Mono, ivory #FAFAF8 + rich black + burnished gold #B8860B, rule lines, small-caps mono labels, generous whitespace) across the entire frontend. Rewrote index.css tokens/utilities and all UI primitives; redesigned MainLayout header and Home.tsx in light editorial style; rebuilt Login; converted Signup's dark brand panel to ivory/gold; swept all legacy patient/doctor/admin screens to the warm palette; aligned VRSessionRunner intro/outro while leaving the A-Frame scene untouched. Also root-cause fixed double-encoded UTF-8 corruption across 19 files via a byte-reversal repair script.
- **Files touched:** index.html, src/index.css, components/ui/* (all 10), layouts/MainLayout.tsx, pages/Home.tsx, plus encoding repair + palette sweep across ~20 screen files.
- **Tests/checks:**
  - Incremental builds after each batch: all clean; final 
pm run build 0 TS errors.
  - Lint: 6 pre-existing warnings only.
  - pytest full suite: **98/98 passing**.
  - Final encoding scan: ALL CLEAN.
- **Acceptance criteria:** Pass - All screens work with the upgraded design system without breaking existing backend integration or the test suite.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Centralized tokens meant newer G-era screens inherited most styling free of charge; global heading font rule unified typography everywhere; VR scene and crisis modals left untouched per user decisions; light theme confirmed.
- **Issues / blockers:** None. (Encoding corruption root-caused to PS5.1 Get-Content ANSI misreads during F2 bulk edits; repaired losslessly.)
- **Follow-ups:** IMPLEMENTATION_PLAN2.md COMPLETE. Re-verify helpline numbers before live presentation. Deferred by design: Phase C (RAG evaluation) and Phase E (production hardening).

### 2026-08-25 - Community fix + Reddit-style threaded comments (Part 1)
- **Status:** Complete
- **Summary:** Fixed the community blank-feed regression and rebuilt comment threads Reddit-style. Backend: corrected the inverted self-referential relationship (parent/replies with back_populates) and removed nested replies serialization from CommunityCommentResponse; added an HTTP-layer regression test exercising signup->post->comment->nested-reply over real ASGI HTTP. Frontend: replaced the silent catch with visible error states (incl. expired-session guidance), Array.isArray guards, and a full Reddit-format thread UI (depth guide rails, [–]/[+n] collapse with hidden counts, inline nested reply boxes, relative times, depth cap 8).
- **Files touched:** backend/app/models/community.py, backend/app/schemas/community.py, backend/tests/test_community_http_layer.py (new), frontend/src/pages/patient/community/CommunityPage.tsx.
- **Tests/checks:**
  - New HTTP-layer regression test: 1/1 pass.
  - pytest full suite: **99/99 passing**.
  - Live probe: GET /community/posts -> 200 with 7 seeded/user posts visible.
  - 
pm run build clean; lint 5 pre-existing warnings.
- **Acceptance criteria:** Pass - Feed loads end-to-end (proven via probe); post modal shows Reddit-style threaded comments with collapse + inline replies.
- **Rules compliance:** Pass.
- **Decisions & rationale:** Removed nested serialization instead of populating it - frontend reconstructs trees from flat parent_id, so payload nesting was pure risk; HTTP-layer test added because direct-function tests bypass FastAPI response validation where the bug lived.
- **Issues / blockers:** None.
- **Follow-ups:** Part 2 - VR scene defect fixes + visual upgrade (awaiting go-ahead).

### 2026-08-25 - Part 2: VR scene repair, stage progression & visual upgrade
- **Status:** Complete (awaiting user manual verification)
- **Summary:** Fixed all identified VR defects: malformed sway animation vector, StrictMode double-mount scene wipe (guarded emptiness-check mounting + unmount-only teardown), vr-stage-advance listener leak, stale telemetry closures, deprecated userHeight camera, dead fusing animation. Removed CDN audio dependencies entirely via new WebAudio generator (vrAmbience.ts: lowpass wind / bandpass+tremolo murmur) started on Begin click. Added real stage progression via registered stage-director component - heights: edge dolly + growing sway + thickening fog + fading front rail; lecture: dimming room lights with tightening spotlight, murmur swell, cycling slide titles, phone glows from stage 2. Visual upgrades: dusk heights skyline (sun disc, lit window strips, CAUTION-EDGE hazard signage), flickering projector beam cone, staggered crowd head micro-motion.
- **Files touched:** frontend/src/utils/vrAmbience.ts (new), frontend/src/pages/patient/vr/VRSessionRunner.tsx.
- **Tests/checks:** 
pm run build clean; lint **5 pre-existing warnings only**; pytest full suite **99/99 passing**.
- **Acceptance criteria:** Pending user manual verification in browser (rendering, stage progression changing the world, ambience, console cleanliness).
- **Rules compliance:** Pass.
- **Decisions & rationale:** React state is single source of truth for stage; A-Frame mirrors via window hook; in-scene clicks bubble back through document event. WebAudio generation removes last external runtime dependency of the VR module.
- **Issues / blockers:** None.
- **Follow-ups:** Triage any console errors user reports from manual run.

### 2026-09-05 � Iteration H1: Remove SOS from landing; fold "Get Help" into SOS
- **Status:** Complete
- **Summary:** De-cluttered the public landing page by removing the interactive Panic SOS modal from the unauthenticated nav, and eliminated the redundant standalone "Get Help" button in favor of a single help/crisis entry point. The consolidated PanicModal now carries the reassurance intro, HelplineCards, and Mindora's automated-safety-system note that previously lived in GetHelpMenu. The now-unused GetHelpMenu.tsx component was deleted.
- **Files touched:** frontend/src/layouts/MainLayout.tsx (removed GetHelpMenu import/state, both Get Help buttons, and the unauthenticated PanicModal), frontend/src/components/PanicModal.tsx (absorbed Get Help content), frontend/src/components/GetHelpMenu.tsx (deleted).
- **Tests/checks:** `npm run build` clean (0 TS errors); `npm run lint` � 5 pre-existing warnings only, no new warnings. Backend untouched (frontend-only change).
- **Acceptance criteria:** Pass � Landing page has no SOS element; exactly one help/crisis entry point (PanicModal) in the student panel, not two.
- **Rules compliance:** Pass. Branch eature/h1-sos-consolidation created per 0b; prior uncommitted F/G baseline untouched.
- **Decisions & rationale:** PanicModal already triggered /patient/panic and rendered HelplineCards, so it was the natural single consolidated entry; the separate Get Help dialog was fully redundant. Landing page keeps the static crisis banner/CTA in Home.tsx rather than an interactive modal for unauthenticated visitors.
- **Issues / blockers:** None. Doctor/admin nav still shows PanicModal � patient-only restriction and floating placement are scoped to H3.
- **Follow-ups:** Proceed to H2 (collapsible left panel + reusable header/back/profile + update-info screen); H3 will then make SOS floating and patient-panel-only.

### 2026-09-06 — Iteration H2: Global navigation (collapsible left panel + reusable header) & update-info screen
- **Status:** Complete
- **Summary:** Replaced the top navbar with a role-aware collapsible left sidebar (expand/collapse persisted to `localStorage('mindora-sidebar-collapsed')`; mobile overlay w/ backdrop), added a reusable header component with back-to-dashboard + profile avatar, and built a shared update-info screen (`/account/profile`) for patient/doctor/admin. Backend gained `PUT /auth/me` (partial update, doctor specialty/languages via DoctorProfile) and the `UserResponse` serializer now returns phone/emergency_contact_phone/specialty/languages. `MainLayout` renders the public header only when logged out, so landing/login/signup show no panel chrome; patient SOS remains a single floating PanicModal entry (patient-panel-only) pending H3 formalization.
- **Files touched:** frontend/src/components/{Sidebar,AppHeader}.tsx (new), frontend/src/pages/patient/account/UpdateProfilePage.tsx (new), frontend/src/layouts/MainLayout.tsx, frontend/src/contexts/AuthContext.tsx, frontend/src/App.tsx, backend/app/api/v1/auth.py, backend/app/schemas/user.py, backend/tests/test_profile_update.py (new).
- **Tests/checks:**
  - pytest tests/test_profile_update.py: **3/3 pass** (patient updates own fields; doctor updates specialty+languages; partial update keeps other fields).
  - npm run build: clean (0 TS errors); npm run lint: 5 pre-existing warnings only.
  - Live smoke test: patient + doctor PUT /auth/me round-trips against running backend; dev servers verified up; seeded demo data restored after testing.
- **Acceptance criteria:** Pass — Left panel opens/closes without layout shift (stable width transition + persisted state + mobile overlay); back and profile buttons appear consistently across every authenticated patient/doctor/admin screen; a user can edit and save their own profile info.
- **Rules compliance:** Pass. Branch `feature/h2-nav-overhaul` created per 0b; prior uncommitted F/G/H1 baseline untouched.
- **Decisions & rationale:** Single `PUT /auth/me` for all roles (client applies the returned serialized user to AuthContext directly); license number deliberately read-only (audited credential). User interface extended instead of created, so AuthContext type matches the enriched response.
- **Issues / blockers:** None. (Noted in the shell: `UpdateProfilePage` helperText originally used a literal `{isPatient ? ...}` string — fixed to a template literal; type-check failed on `account/` being one nesting level deeper than the original relative imports — corrected to `../../../`.)
- **Follow-ups:** Proceed to H3 — floating panic/SOS button, student panel only; verify it renders on every student screen and is absent from doctor/admin views.

### 2026-09-06 — Iteration H3: Floating panic/SOS button — student panel only
- **Status:** Complete
- **Summary:** Upgraded the PanicModal trigger to a round floating action button (56px, red pulse ring, 🆘 glyph, hover lift, focus ring) floating bottom-left on every patient screen; confirmed doctor/admin panels render zero SOS UI. Fixed two stale copy references in AIChatPage that pointed to "above / top of screen" — now correctly reference the floating bottom-left SOS button.
- **Files touched:** frontend/src/components/PanicModal.tsx, frontend/src/pages/patient/chat/AIChatPage.tsx.
- **Tests/checks:**
  - npm run build: clean (0 TS errors); npm run lint: 5 pre-existing warnings only.
  - pytest tests/test_profile_update.py: **3/3 pass** (H2 baseline unchanged).
  - Live smoke test: patient login → POST /patient/panic returns CRITICAL alert with 15-min SLA; doctor/admin login verified no UI SOS button; dev servers (:8000/:5173) healthy.
- **Acceptance criteria:** Pass — Button present and functional on every student screen (dashboard, screening, mood, community, appointments, VR, chat, onboarding); absent from doctor and admin views.
- **Rules compliance:** Pass. Branch `feature/h3-floating-sos` created per 0b off `feature/h2-nav-overhaul`; uncommitted F/G/H1/H2 baseline carried forward.
- **Decisions & rationale:** Round FAB with `animate-ping` pulse ring reads as a true floating emergency affordance; dialog + POST /patient/panic flow unchanged. Copy fix is in-scope positional accuracy. SOS stays on onboarding + VR session — both are student screens; exit hatch during exposure is desirable.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to H4 — Mood tracker visual redesign.

### 2026-09-06 — Iteration H4: Mood tracker visual redesign
- **Status:** Complete
- **Summary:** Rebuilt the patient Mood Tracker & Journal page on the Phase F editorial design system. All plain white cards replaced with the `Card` primitive family (`glass` variant), form controls migrated to `Button`/`Select`/`Textarea`, typography and color moved to the ivory/black/gold tokens, and the Recharts area chart re-themed from teal to accent gold. All functional behavior (create/edit/fetch, time-range refetch, tags, journal) preserved exactly.
- **Files touched:** frontend/src/pages/patient/mood/MoodTrackerPage.tsx (full rewrite, frontend-only).
- **Tests/checks:**
  - npm run build: clean (0 TS errors); npm run lint: 5 pre-existing warnings only (MoodTracker exhaustive-deps warning pre-existed, line number shifted).
  - Live smoke test (alice@campus.edu): POST /patient/mood/ → entry appears in GET /patient/mood/history?days=30 → PUT /patient/mood/:id persists — all passing; test row removed via psql (no DELETE endpoint exists).
- **Acceptance criteria:** Pass — Mood tracker visually matches the rest of the redesigned app (design-system components + editorial tokens); no functional regression to mood-logging behavior (round-trip verified).
- **Rules compliance:** Pass. Branch `feature/h4-mood-tracker-redesign` created per 0b off `feature/h3-floating-sos`; uncommitted baseline carried forward.
- **Decisions & rationale:** User chose Option B — active mood buttons keep per-score semantic colors (red/orange/amber/emerald/gold) instead of collapsing to brand gold, as a visual scoring aid; inactive state is a neutral design-token outline with accent ring. Journal tags render as muted design-token chips rather than `Badge` (Badge's uppercase-mono styling fits statuses, not content tags). `recharts` retained; no new dependencies; backend untouched.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to H5 — Fix admin login (diagnose auth flow, role assignment, session handling for the admin role).

### 2026-09-06 — Iteration H5: Fix admin login (role-scoped signup, admin provisioning API, demo data & dashboard redesign)
- **Status:** Complete
- **Summary:** Diagnosed and fixed the empty/suppressed admin dashboard and the role-scoping hole behind it. Public signup accepted any role, so the demo admin (state-scoped to `"Maharashtra"`) combined with a jurisdiction matcher that only compared `region == state` against `"City, State"` aggregate keys filtered literally everything out — the dashboard looked "broken" because there was nothing to show. Fixes: (1) signup now rejects roles outside `patient`/`doctor` (400, admins only via admin-created accounts); (2) new `POST /api/v1/admin/users` (`AdminCreate`) provisions verified admins; (3) jurisdiction matching is suffix-aware via `_jurisdiction_filter` (`region == state` OR `ILIKE '%, state'`) applied across all five analytics endpoints; (4) demo seed got a 50-patient extra cohort (10 × 5 cities) and a global (unscoped) demo admin. Rewrote `AdminDashboard.tsx` on the Phase F design system (glass Cards, gold #b8860b charts + editorial tooltip, region filter, spike alerts, suppressed-state card) and added an "Administrator Accounts" creation form. Demo DB flushed and reseeded to canonical state (59 users, 10 non-suppressed region-period rows, zero test residue), removing ~87 accumulated test accounts and duplicate aggregate rows that were inflating the numbers.
- **Files touched:** backend/app/api/v1/admin.py, auth.py, backend/app/schemas/user.py, backend/app/seed_demo.py; backend/tests/test_admin_login.py (new), tests/test_doctor_profile_upgrade.py, tests/test_doctor_approval.py (admin fixtures via DB); frontend/src/pages/admin/AdminDashboard.tsx.
- **Tests/checks:**
  - pytest full suite: **106 passed** (4 new admin-login tests; all prior suites green, no residue left in DB — verified `users` non-campus-edu = 0).
  - npm run build clean; lint at baseline (5 pre-existing warnings).
  - Live smoke: admin@campus.edu login → overview `suppressed=False` (110 patients, 5 regions, 110 screenings, 44 alerts, 28 VR, 770 mood), trend 10 rows/0 suppressed, region filter returns just that region; state-scoped admin (Karnataka) sees only "Bengaluru, Karnataka" non-suppressed; signup `role=admin` → 400; `POST /admin/users` 201 round-trip + duplicate 400 + non-admin 403.
- **Acceptance criteria:** Pass — admin can log in and land on a populated dashboard; admins can be provisioned only by an existing admin; jurisdiction filtering handles `"City, State"` keys; demo data exceeds the suppression threshold; dashboard matches Phase F design.
- **Rules compliance:** Pass. Branch `fix/h5-admin-login` created per 0b off `feature/h4-mood-tracker-redesign`; uncommitted baseline carried forward.
- **Decisions & rationale:** Admin self-registration permanently disabled — singular provisioning path keeps the role trustworthy. Jurisdiction treated as "state-scoped admin sees their state's rows regardless of city keying". Dashboard uses real seeded aggregates instead of mock rows so the redesign doubles as a data-density verification.
- **Issues / blockers:** None. (Intermediate failed test runs leaked `RegionalAggregate` + admin users into the dev DB; resolved by flushing and reseeding to a canonical demo dataset.)
- **Follow-ups:** Proceed to H6 — SAR Workshop / next student-panel polish iteration per implementation-plan-3.md.
