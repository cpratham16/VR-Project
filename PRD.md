# Product Requirements Document
## VR-Based Digital Mental Health Platform for Campus Use

| | |
|---|---|
| **Status** | Draft v1.0 |
| **Author** | Pratham (Product/Engineering Lead), KIET Group of Institutions |
| **Date** | August 2026 |
| **Related work** | Springer LNCS conference paper — three-panel architecture with AI-assisted risk detection |

---

## 1. Executive Summary

A three-panel platform that lets students screen themselves for common mental health concerns (anxiety, stress, phobias), get matched to appropriate treatment including VR-based exposure therapy, stay connected with a treating doctor, and gives institutional/government stakeholders anonymized visibility into population-level trends — without ever exposing an individual's identity outside the clinical relationship.

The three panels:
- **Patient panel** — self-screening, mood tracking, AI companion support, VR therapy, doctor access
- **Doctor panel** — clinical dashboard, notes, treatment planning, VR session assignment, scheduling
- **Admin/government panel** — aggregated, anonymized statistics only, for regional monitoring and resource planning

This PRD scopes the build as a final-year academic project: a working prototype demonstrating the full architecture, not a production clinical system. Where clinical/legal rigor would normally be required for real deployment, this is called out explicitly rather than assumed away.

---

## 2. Background & Problem Statement

Campus mental health support is typically under-resourced relative to demand: long wait times for counseling, stigma around walk-in visits, and no structured way to triage who needs urgent attention versus lower-acuity support. Students often first notice something is wrong through mood changes or stress spikes that go unrecorded and unnoticed until a crisis point.

This platform aims to:
- Lower the barrier to a first mental-health touchpoint (self-screening, anonymous community, AI companion)
- Give clinicians a structured, triaged view of who needs attention and when
- Offer accessible exposure-based therapy (phobias, social anxiety) via VR without needing a specialist clinic visit
- Give institutions/regional health bodies visibility into trends to allocate counseling resources — without compromising individual privacy

## 3. Goals

- Ship a working, demoable prototype covering all three panels
- Demonstrate the AI-assisted risk detection and escalation pipeline described in the accompanying paper
- Keep individual patient data fully separated from the admin/government panel
- Build on a stack the team already has working knowledge of, to keep velocity high within an academic timeline

## Non-Goals (for this phase)

- Regulatory certification as a medical device or clinical software
- Real-time multi-region deployment or high-availability infrastructure
- Native mobile apps (a responsive web app / PWA covers the demo needs)
- Full native VR builds (WebXR covers the prototype; native Unity is a stretch goal, not required scope)

## 4. Assumptions

- Team size: ~4 (matching co-authorship of the related paper); adjust iteration pacing if team size differs
- Timeline: sized for a typical single-semester academic build (~14-16 weeks of active development)
- Hosting: student/free-tier cloud services (Render/Railway/Vercel + a managed Postgres tier) are acceptable for the prototype
- No real patient data is used during development — synthetic/seed data only

---

## 5. Personas

| Persona | Description | Primary needs |
|---|---|---|
| **Student patient** | Undergrad/postgrad experiencing stress, anxiety, or a specific phobia | Fast, low-friction screening; privacy; a way to reach a real doctor when needed |
| **Treating doctor / counselor** | Licensed campus counselor or affiliated psychiatrist | Triaged patient list; full clinical context; ability to assign therapy and intervene quickly |
| **Government/institutional admin** | State health department or college wellness office staff | Regional trend visibility to plan resources; zero exposure to individual identities |

---

## 6. Scope by Panel

### 6.1 Patient Panel

| Feature | Description | Priority |
|---|---|---|
| Auth & profile | Signup/login, profile setup, informed consent capture | P0 |
| PHQ-9 / GAD-7 screening | Standard validated questionnaires, auto-scored, versioned over time | P0 |
| Mood tracker & journal | Daily mood log + free-text journal entries, private by default | P0 |
| Panic button | One-tap SOS: shows crisis helpline immediately + notifies assigned doctor in parallel | P0 |
| AI companion chatbot | Supportive conversational agent; discloses it is not a therapist; feeds risk signals to the triage engine | P0 |
| Schedule call with doctor | Request/view appointment slots | P1 |
| Anonymous community & chat | Pseudonymous posting; auto-flagging of self-harm language for moderation | P1 |
| VR therapy sessions | Doctor-assigned WebXR exposure scenarios (heights, public speaking, social situations, etc.) | P1 |
| Treatment recommendation view | Shows suggested next step based on screening score, pending doctor confirmation | P2 |

### 6.2 Doctor Panel

| Feature | Description | Priority |
|---|---|---|
| Auth & role access | Verified doctor accounts, role-scoped data access | P0 |
| Triage patient list | Patients sorted/filterable by risk score and recency | P0 |
| Patient detail view | Full history: scores, mood trends, journal (if not marked anonymous), chat flags | P0 |
| Clinical notes | Doctor-authored notes per patient, private to clinical staff | P0 |
| Anonymity handling | If a patient marks a submission anonymous, doctor sees the clinical content without the identity attached to that specific item | P1 |
| VR therapy assignment | Doctor selects/assigns a VR module and tracks completion | P1 |
| Scheduling | Doctor-side calendar, accept/propose call times | P1 |
| Treatment recommendation override | Doctor confirms, edits, or overrides system-suggested treatment path | P2 |

### 6.3 Admin / Government Panel

| Feature | Description | Priority |
|---|---|---|
| Aggregated dashboard | Case volume, severity distribution, trend lines — state/district level only | P0 |
| Regional heatmap | Visual density of flagged cases by area, anonymized | P1 |
| Trend alerts | Spike detection when a region's flagged-case rate rises sharply | P2 |
| Resource view | Doctor/counselor availability vs. regional demand | P2 |

**Hard constraint across this entire panel:** no name, contact detail, journal text, or any single-patient-identifiable record is ever queryable from this panel. All data enters through the anonymization layer described in Section 8, Iteration 12.

---

## 7. Non-Functional Requirements

- **Privacy & compliance:** Design with India's DPDP Act 2023 and the Mental Healthcare Act 2017 confidentiality principles in mind — encrypt data at rest and in transit, role-based access control, audit logging on all clinical data access, explicit informed consent before any AI processing of patient input.
- **Safety:** Any AI-detected high-risk signal must trigger a deterministic, rule-based escalation — never rely solely on the LLM's judgment for crisis detection.
- **Accessibility:** WCAG 2.1 AA target for the patient and doctor web panels.
- **Performance:** Screening flows and chatbot responses should feel responsive (sub-2s for standard API calls; chatbot streaming for perceived latency).
- **Portability:** VR content must run in-browser (WebXR) so the demo doesn't depend on headset availability.

---

## 8. Development Plan — Iterative Roadmap

Each iteration is scoped to be independently demoable. Durations are relative sprint units (~1-2 weeks each for a ~4-person team); adjust to your actual team size and course calendar.

### Phase 0 — Foundations

**Iteration 0: Project setup**
- Goal: A working skeleton every later iteration builds on.
- Deliverables: Monorepo or multi-repo structure, FastAPI backend skeleton, React frontend skeleton, Postgres instance, CI pipeline (lint + test on push), shared design tokens (colors, typography) applied across patient/doctor/admin frontends.
- Acceptance criteria: A "hello world" request round-trips from React → FastAPI → Postgres → back, deployed to a staging URL.
- Tech: FastAPI, React, PostgreSQL, GitHub Actions.

### Phase 1 — Patient Panel Core

**Iteration 1: Patient auth & login page**
- Goal: A student can create an account and log in securely.
- Deliverables: Signup/login UI, JWT-based auth, password hashing, session handling, role field (`patient`) on the user model.
- Acceptance criteria: A new user can sign up, log out, log back in; invalid credentials are rejected with a clear error; passwords are never stored in plaintext.
- Tech: FastAPI + `passlib`/`bcrypt`, JWT, React form with client-side validation.

**Iteration 2: Onboarding, consent & profile**
- Goal: Capture informed consent and basic profile before any clinical data is collected.
- Deliverables: Consent screen (data usage, AI processing disclosure, right to withdraw), profile form (name or pseudonym, optional demographic fields for later aggregate stats), consent timestamp stored against the user record.
- Acceptance criteria: A user cannot reach the questionnaire or chatbot without having accepted consent; consent version is recorded so future policy changes can be tracked.

**Iteration 3: PHQ-9 / GAD-7 screening**
- Goal: Validated self-screening with automatic scoring.
- Deliverables: Questionnaire UI (one question at a time or single-page form), scoring logic per standard PHQ-9/GAD-7 bands, score history stored per user, results screen showing band (minimal/mild/moderate/severe) — not a diagnosis label.
- Acceptance criteria: Score calculation matches the standard published scoring bands; results are versioned by submission date so trends can be tracked later.
- Note: verify current licensing terms for PHQ-9/GAD-7 use before publishing — they're widely used in academic/clinical tools but confirm current terms directly rather than relying on this document.

**Iteration 4: Mood tracker & journal**
- Goal: Lightweight daily check-in that feeds the risk engine later.
- Deliverables: Mood entry (scale + optional tags), free-text journal entry, private-by-default storage, simple trend chart over time.
- Acceptance criteria: Entries are timestamped, editable within a short window, and visible only to the patient and their assigned doctor (not admin).

### Phase 2 — Doctor Panel Core

**Iteration 5: Doctor auth & triage list**
- Goal: A doctor logs in and sees a prioritized patient list.
- Deliverables: Doctor role + verification flag on signup, patient list view sortable by latest risk score and last activity, basic filters (severity band, unread flags).
- Acceptance criteria: Doctor accounts cannot self-register as verified without an admin approval step; patient list correctly reflects latest scores.

**Iteration 6: Patient detail view & clinical notes**
- Goal: Doctor can review full context and record notes.
- Deliverables: Patient detail page (score history, mood trend, journal if not anonymized, flagged chat/community content), free-text clinical notes field per visit, anonymity handling so patient-marked-anonymous content shows content without linking to other identifiable records in that view.
- Acceptance criteria: Notes persist and are timestamped/attributed to the authoring doctor; anonymized submissions never expose the patient's other identifiable data alongside them.

**Iteration 7: Scheduling**
- Goal: Patient and doctor can agree on a call time.
- Deliverables: Patient-side "request a call" flow, doctor-side calendar/availability view, confirmation + basic reminder (email or in-app).
- Acceptance criteria: A requested slot appears on the doctor's calendar and a confirmed slot appears on the patient's dashboard.

### Phase 3 — AI & Safety Layer

**Iteration 8: AI companion chatbot**
- Goal: A scoped conversational support agent, clearly bounded.
- Deliverables: Chat UI, backend call to an LLM API with a system prompt that (a) discloses it isn't a therapist, (b) stays within supportive/psychoeducational bounds, (c) never gives clinical diagnoses, conversation history stored per user.
- Acceptance criteria: The bot consistently declines to diagnose or give medication advice and redirects to a doctor or crisis line when the conversation indicates distress.

**Iteration 9: Risk scoring & escalation**
- Goal: Deterministic escalation path independent of chatbot "judgment."
- Deliverables: Rule-based risk scoring combining questionnaire bands + chat/journal sentiment signals, panic button wired to immediately surface a crisis helpline number and notify the assigned doctor (SMS/push via Twilio or FCM), doctor-side real-time alert on high-risk flags.
- Acceptance criteria: A simulated high-risk input triggers a doctor notification within seconds in staging; the panic button always shows the helpline number even if the notification service is down (fail-safe, not fail-silent).

### Phase 4 — Community & VR

**Iteration 10: Anonymous community & chat**
- Goal: Peer support space with safety moderation.
- Deliverables: Pseudonymous posting, basic thread/comment structure, automated keyword/sentiment flagging of self-harm-adjacent language routed to a moderation queue (not public auto-removal, human review).
- Acceptance criteria: Posts display under pseudonyms only; flagged posts appear in a moderator queue within the doctor/admin-moderator view, not visible publicly as "flagged."

**Iteration 11: WebXR VR therapy module**
- Goal: Doctor-assigned browser-based exposure therapy sessions.
- Deliverables: 2-3 initial WebXR scenarios (e.g., height exposure, public speaking simulation, crowded space), doctor assignment flow, patient session launch + completion tracking.
- Acceptance criteria: A patient can launch an assigned scenario from a standard browser (headset optional) and completion is logged back to the doctor's view.
- Tech: Three.js or A-Frame.

### Phase 5 — Admin/Gov Panel

**Iteration 12: Anonymization pipeline**
- Goal: A hard boundary between clinical data and aggregate reporting.
- Deliverables: A scheduled/triggered job that aggregates counts and score bands by region and time period, strips all identifiers before writing to a separate reporting store the admin panel reads from.
- Acceptance criteria: The admin-facing database/schema contains no columns capable of identifying an individual, verified by a schema review, not just application-layer filtering.

**Iteration 13: Admin dashboard**
- Goal: Regional visibility for planning, nothing else.
- Deliverables: Aggregated charts (volume, severity distribution, trend over time) filterable by region, basic spike/anomaly indicator.
- Acceptance criteria: Every chart on this panel is backed only by the anonymized reporting store from Iteration 12.

### Phase 6 — Hardening & Launch

**Iteration 14: Security, accessibility, testing, deployment**
- Goal: Demo-ready, defensible build.
- Deliverables: Auth/access-control test pass, dependency and basic security audit, WCAG spot-check on key patient/doctor flows, seeded demo data, deployment to a stable staging URL, README + architecture write-up tying back to the paper.
- Acceptance criteria: A cold demo run-through (signup → screening → chatbot → panic button → doctor view → admin view) works end-to-end without manual intervention.

---

## 9. Recommended Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python, FastAPI | Matches existing RAG pipeline experience; fast to prototype AI-integrated endpoints |
| Frontend (doctor/admin) | React | Standard, component reuse across dashboards |
| Frontend (patient) | React PWA | Single codebase, installable, avoids native app store overhead for a student project |
| Database | PostgreSQL | Relational integrity for patient/doctor/appointment/score data |
| AI/chat | Claude or GPT-4o-mini via API | Cost-effective, quality sufficient for a supportive/psychoeducational chatbot |
| VR | Three.js / A-Frame (WebXR) | Headset-optional, browser-based, faster to build than native Unity |
| Notifications | Twilio (SMS) or Firebase Cloud Messaging | For doctor escalation alerts and appointment reminders |
| Auth | JWT + bcrypt, role-based access control | Straightforward, well-understood, sufficient for prototype scope |
| Hosting (prototype) | Vercel/Render/Railway + managed Postgres | Free/low-cost tiers suitable for an academic build |

Spring Boot remains a reasonable alternative for the backend if the team wants to reuse the Spring AI agent experience — FastAPI is recommended primarily for speed of iteration on the AI-heavy pieces (Iterations 8-9).

---

## 10. Data Model Overview (high level)

Core entities: `User` (role: patient/doctor/admin), `PatientProfile`, `ConsentRecord`, `ScreeningResult` (PHQ-9/GAD-7), `MoodEntry`, `JournalEntry`, `ChatSession` + `ChatMessage`, `CommunityPost` + `Flag`, `Appointment`, `ClinicalNote`, `VRSession`, `RiskFlag`, `AggregatedStat` (admin-facing, no FK to any identifiable table).

A full normalized schema with field-level detail can be produced as a follow-up if useful.

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| VR scope overruns the timeline | WebXR-first, 2-3 scenarios only, native Unity deferred |
| Chatbot gives inappropriate clinical advice | Hard system-prompt boundaries + human escalation path, tested with adversarial prompts before demo |
| Admin panel accidentally exposes identifiable data | Separate reporting database/schema, not just filtered queries; schema-level review in Iteration 12 |
| Team bandwidth vs. coursework load | Iterations sized to ~1-2 weeks each so scope can flex without breaking the whole plan |
| PHQ-9/GAD-7 licensing/use terms | Verify current terms before any public-facing or published use |

---

## 12. Success Metrics (for this academic build)

- All 15 iterations demoable end-to-end by submission date
- Zero identifiable data reachable from the admin panel (verified, not assumed)
- Chatbot correctly escalates in 100% of adversarial "high risk" test prompts
- Screening-to-recommendation flow completes in under 5 minutes for a test user

---

## 13. Open Questions

- Confirmed team size and available weekly hours per member
- Target submission/demo date to size the phase timeline precisely
- Whether a real (verified, non-production) doctor account will be used for demo or a seeded persona is sufficient
- Hosting budget, if any, beyond free tiers