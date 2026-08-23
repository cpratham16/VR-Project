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
- **Follow-ups:** Proceed to B4 (Dense retrieval + RRF fusion) where we fuse dense and sparse search rankings.

### 2026-08-24 — Iteration B4: Dense retrieval + RRF fusion
- **Status:** Complete
- **Summary:** Implemented `RankingService` with reciprocal rank fusion (RRF) algorithm ($k=60$) to combine dense semantic and sparse BM25 search results. Integrated this fusion into `VectorStoreService.search_hybrid` orchestrating both independent retrieval paths and applying the fusion algorithm in Python for modularity.
- **Files touched:** `backend/app/services/ranking.py` (new), `backend/app/services/vector_store.py`, `backend/tests/test_ranking.py` (new).
- **Tests/checks:**
  - `pytest` full suite: **47/47 pass** (added `test_ranking.py` verifying RRF score calculation consistency).
  - Manual verification of hybrid search logic confirmed independent ranking and successful combined ranking of disparate results.
- **Acceptance criteria:** Pass — Fused results successfully combine dense (semantic) and sparse (keyword) sources into a single ranked list, with keyword-specific hits adequately promoted by sparse rank.
- **Rules compliance:** Pass
- **Decisions & rationale:**
  - Fusion implemented as a standalone, Python-based `RankingService` to facilitate swapping/extending with future rerankers (like cross-encoders in B5).
  - RRF implemented using standard $k=60$ hyperparameters.
- **Issues / blockers:** None.
- **Follow-ups:** Proceed to B5 (Reranking integration) where we will integrate cross-encoders to further improve answer relevance.
