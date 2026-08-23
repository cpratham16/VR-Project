# IMPLEMENTATION_PLAN.md

This file contains the complete **Systematic Implementation Plan — Upgrade Track**.

## Prerequisite

**Before implementing any iteration, the agent MUST read `RULES.md` in full and follow it.**

`RULES.md` is mandatory execution policy. No iteration may begin without it.

The plan below defines the phases, iterations, tasks, and acceptance criteria. The rules file defines the required execution, verification, acceptance, and close-out process.

## Phase A — VR Realism Upgrade (6 iterations)

**A1: Lighting & materials pass**

- Tasks: Swap primitive materials for PBR; add HDRI environment lighting to existing scenarios; add real-time shadows.
- Acceptance: Existing scenarios visually upgraded with no interaction regressions.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**A2: Controller-based interaction**

- Tasks: Add WebXR controller input alongside existing gaze-only interaction; map basic select/point actions.
- Acceptance: A user with a controller can interact with scene objects, not just look at them.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**A3: Physics layer**

- Tasks: Integrate Rapier or Cannon.js; wire interactive objects to respond realistically when touched/moved.
- Acceptance: At least one object per scenario has a physically realistic response to interaction.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**A4: Spatial audio**

- Tasks: Add positional/ambient audio (crowd noise, footsteps, environment sound) tied to scene objects.
- Acceptance: Audio cues shift correctly with head/camera movement in-scene.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**A5: Session telemetry**

- Tasks: Extend the existing `VRSession` record (no new entity) with time-in-scene, interaction count, completion vs. early-exit.
- Acceptance: Doctor panel session view shows the new engagement fields for a completed session.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**A6: Performance pass**

- Tasks: Add LOD switching, texture compression (KTX2/Basis), occlusion culling.
- Acceptance: Target scenarios run smoothly on a mid-range laptop/phone GPU, not just high-end hardware.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

---

## Phase B — Hybrid RAG Engine Upgrade (8 iterations)

**B1: Vector store setup**

- Tasks: Stand up Qdrant; define embedding pipeline (model choice, chunking strategy).
- Acceptance: A test document round-trips — chunked, embedded, stored, retrievable by ID.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**B2: Knowledge base ingestion**

- Tasks: Curate and ingest vetted content — CBT/coping techniques, psychoeducation, crisis-response protocols, FAQs.
- Acceptance: Knowledge base is queryable and covers the core support topics the chatbot needs to ground answers in.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**B3: Sparse retrieval (BM25)**

- Tasks: Implement BM25 keyword search over the ingested content.
- Acceptance: Keyword queries return relevant chunks ranked sensibly.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**B4: Dense retrieval + RRF fusion**

- Tasks: Add dense vector search; combine with BM25 results via Reciprocal Rank Fusion.
- Acceptance: Fused results outperform either method alone on a small manual test set of sample queries.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**B5: Reranking integration**

- Tasks: Add Cohere Rerank (or a local cross-encoder like `bge-reranker`) as a post-fusion step on the top-k candidates.
- Acceptance: Reranked top-3 is measurably more relevant than pre-rerank top-3 on the same test queries — this closes the gap flagged earlier.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**B6: Generation layer update**

- Tasks: Update the chatbot's generation call to inject retrieved + reranked context and session memory; keep Groq (or swap-in model) as a modular component.
- Acceptance: Chatbot answers are grounded in retrieved content, verifiable by inspecting which chunks were used per response. Escalation/risk-scoring logic remains untouched and independent of this pipeline.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**B7: Observability instrumentation**

- Tasks: Add OpenTelemetry spans for retrieval, rerank, and generation stages; log latency and token counts per stage.
- Acceptance: A single chatbot turn produces a full trace showing time spent in each pipeline stage.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**B8: Semantic caching**

- Tasks: Add Redis-backed caching for repeated/similar queries.
- Acceptance: A repeated query returns from cache with materially lower latency, verified in the trace from B7.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

---

## Phase C — RAG Testing & Evaluation (5 iterations)

**C1: Golden test set**

- Tasks: Build a curated Q&A set covering common scenarios, plus hard cases — ambiguous distress, off-topic, adversarial prompt injection, explicit crisis language.
- Acceptance: Test set reviewed and versioned; crisis-language cases clearly labeled for the safety suite in C3.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**C2: RAGAS integration in CI**

- Tasks: Wire up RAGAS metrics (faithfulness, answer relevancy, context precision/recall) to run automatically on retrieval/embedding/reranker changes.
- Acceptance: A deliberate retrieval regression (e.g. reverting B5) causes a CI failure.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**C3: Safety escalation test suite**

- Tasks: Build a separate, deterministic test suite covering the crisis-language cases from C1 against the risk-scoring/escalation layer (not RAGAS — this tests the rule layer).
- Acceptance: 100% pass rate required to merge; suite blocks deployment on any failure.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**C4: Load & latency testing**

- Tasks: k6 or Locust load tests against the full hybrid pipeline (retrieval + rerank + generation).
- Acceptance: Response time stays under the \~2s target at expected concurrent load.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**C5: Human-in-the-loop review process**

- Tasks: Define a lightweight monthly sampling process for a supervising reviewer to spot-check real/synthetic conversations.
- Acceptance: Review process documented and a first sample round completed.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

---

## Phase D — Feature-Level Upgrades to Industry Standard (7 iterations)

**D1: Anonymous community upgrade**

- Tasks: Replace keyword flagging with a severity-tiered classifier (reuse Phase B's embeddings infra); move to real-time updates (WebSockets); add rate limiting/abuse prevention; add semantic tagging/search; add a visible report-abuse flow; define retention/auto-purge policy.
- Acceptance: A test post with self-harm-adjacent language is classified with a severity tier and routed to the moderation queue in real time.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**D2: Screening engine upgrade**

- Tasks: Abstract the questionnaire engine beyond hardcoded PHQ-9/GAD-7; add patient-facing trend view; add usage-based smart reminders.
- Acceptance: A new validated scale could be added via config, not a code rebuild (even if not actually added yet).
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**D3: Mood tracker & journal upgrade**

- Tasks: Add client-side/end-to-end encryption for journal text; add longitudinal trend summaries for doctors (reuse embeddings pipeline); add patient data export.
- Acceptance: Journal entries are unreadable at the DB layer without the encryption key; a patient can export their own data.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**D4: Scheduling upgrade**

- Tasks: Add Google/Outlook calendar sync; add embedded video calling (Daily.co/Twilio Video); add no-show handling and waitlist.
- Acceptance: A confirmed appointment appears on both the doctor's and patient's external calendar, and a video call can be launched directly from the appointment.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**D5: Doctor notes upgrade**

- Tasks: Add structured SOAP-format templates alongside free text; make notes immutable/versioned (edits create new versions with attribution); add semantic search across a doctor's own notes.
- Acceptance: Editing a note creates a new version rather than overwriting; version history is viewable.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**D6: Panic button / escalation upgrade**

- Tasks: Add time-to-response SLA tracking with breach alerts; add multi-tier escalation (assigned doctor → backup/on-call → crisis line) if the first tier doesn't respond in time.
- Acceptance: A simulated non-response from the assigned doctor triggers backup escalation within the defined SLA window.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**D7: Admin/government dashboard upgrade**

- Tasks: Add small-cohort suppression (no stats shown below a minimum case count, e.g. 10); enforce role-scoped drill-down at the data-access layer; add PDF/CSV export.
- Acceptance: A region below the minimum threshold shows "insufficient data" instead of a number; a state-level admin account cannot query another state's data even via direct API call.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

---

## Phase E — Production Hardening (9 iterations)

**E1: Auth hardening**

- Tasks: Add refresh tokens, session revocation, login rate-limiting.
- Acceptance: A revoked session is rejected immediately on the next request.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**E2: Secrets management**

- Tasks: Migrate from `.env` files to a secrets manager (Vault or cloud provider's secrets service).
- Acceptance: No secret values remain in source control or plain environment files in the deployed environment.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**E3: Data protection**

- Tasks: Enable encryption at rest; set up automated backups with point-in-time recovery.
- Acceptance: A test restore from backup succeeds without data loss.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**E4: Observability & error tracking (platform-wide)**

- Tasks: Extend OpenTelemetry tracing beyond the RAG pipeline (B7) to the full request path; add structured logging, error tracking (Sentry), uptime alerting.
- Acceptance: A deliberately triggered error surfaces in the error tracker with full trace context within seconds.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**E5: Full testing pyramid**

- Tasks: Unit tests for core business logic, integration tests across services, e2e tests (Playwright) for critical user flows, load testing for non-RAG endpoints.
- Acceptance: CI blocks merge on failing unit/integration/e2e tests for the core flows (signup, screening, scheduling, escalation).
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**E6: Deployment pipeline**

- Tasks: Containerize with Docker; set up staged/canary deploys; automate DB migrations.
- Acceptance: A deploy to staging happens automatically on merge to main, with a manual promotion step to production.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**E7: AI input safety**

- Tasks: Add PII redaction before any external LLM API call; add prompt-injection defenses; log an audit trail of AI-influenced decisions (e.g. risk flags raised).
- Acceptance: A test input containing PII is redacted before leaving the system; a known prompt-injection pattern fails to override system instructions.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**E8: Compliance documentation**

- Tasks: Complete a Data Protection Impact Assessment; implement immutable audit logging for clinical data access; define retention and right-to-erasure procedures.
- Acceptance: DPIA document exists and reflects the actual system; an erasure request can be fulfilled end-to-end in a test run.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**E9: Admin panel physical isolation**

- Tasks: Move the admin-facing reporting store to a physically separate schema/database fed only by the anonymization pipeline; verify no identifiable columns exist there at the schema level.
- Acceptance: A schema audit confirms zero columns capable of identifying an individual in the admin-facing store.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

---

## Phase F — Industry-Grade Landing Page & Frontend Upgrade with Stitch MCP (4 iterations)

**F1: Stitch MCP Landing Page Design System & Skeleton Setup**

- Tasks: Establish Stitch MCP design tokens, glassmorphism UI card components, typography scale, micro-animations, and responsive layout grid; update `frontend/src/pages/Home.tsx` to replace prototype gateway buttons.
- Acceptance: Modern landing page skeleton renders with clean responsive layouts, basic styling primitives, and high-performance load times.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**F2: Hero Section & Immersive Clinical Feature Highlights**

- Tasks: Build dynamic Stitch MCP hero section with medical-tech visuals, interactive feature showcase cards for WebXR exposure therapy, 24/7 AI Companion (AURA), and real-time biometric telemetry tracking; wire high-conversion call-to-action (CTA) buttons for Patient and Doctor Portals.
- Acceptance: Hero header and feature grid render cleanly across mobile, tablet, and desktop viewports; CTA buttons navigate correctly without visual artifacts.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**F3: Clinical Compliance, Privacy Badges & Emergency Helplines**

- Tasks: Add Tele-MANAS national guidelines banner, DPDP Act 2023 compliance badge, anonymized telemetry security panel, and persistent Crisis Panic Helpline shortcuts to the landing page.
- Acceptance: Crisis helplines and compliance standards are visually highlighted and meet WCAG 2.1 AA accessibility standards.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

**F4: Full Frontend Panel Overhaul with Stitch MCP Components**

- Tasks: Apply Stitch MCP UI system across Patient Dashboard, Doctor Triage Dashboard, AI Companion Chat interface, and Admin Analytics view; implement cohesive dark/light contrast cards, standardized status tags, and polished Recharts charts.
- Acceptance: All patient, doctor, and admin portal screens function seamlessly with the upgraded industry-grade design system without breaking any backend integration or test suite.
**Final step:** Complete the mandatory Section 0 close-out protocol — verify acceptance criteria, inspect the final diff, update `CLAUDE.md`, append to `progress.md`, record any blockers/follow-ups, then stop the iteration.

---

## Sequencing Notes

- Phases are ordered A → F to match your stated priority (VR first, then RAG, testing, feature upgrades, hardening, and final Stitch MCP landing page/frontend overhaul).
- **D1 and D5** (community moderation, doctor notes semantic search) depend on Phase B's embeddings infrastructure being in place — sequence them after B2 at minimum.
- **C3 (safety escalation tests)** should exist before B6 ships to production, even in draft form — you want the safety net defined before the RAG-powered chatbot goes live, not after.
- 35 iterations total. At roughly 1-2 weeks each for a \~4-person team working part-time alongside coursework, that's a multi-semester scope — treat this as the full production roadmap, and pull the highest-priority subset (Phase A + B + C3 at minimum) as your actual final-year deliverable.