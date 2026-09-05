# Presentation-Ready Plan
## Active: Frontend Overhaul (Stitch MCP) + Registration & Access Control

Both F and G are being presented — this plan sequences them as one build so nothing gets built twice. Two changes from the earlier draft:
- **G8 (landing page positioning) is removed as a standalone step and merged into F2** — F2 already builds the hero section, so it now owns getting the positioning/copy right the first time instead of F building it once and G8 redoing it later.
- **G1 (registration wizard) now builds directly on F1's design system**, instead of being built first and re-skinned later.

---

## Status Summary

| Phase | Status |
|---|---|
| A — VR Realism Upgrade | ✅ Complete |
| B — Hybrid RAG Engine Upgrade | ✅ Complete |
| D — Feature-Level Upgrades | ✅ Complete |
| C — RAG Testing & Evaluation | ⏭️ Deferred — not required for a presentation; revisit before any real/production use |
| E — Production Hardening | ⏭️ Deferred — same reasoning |
| **F — Frontend Overhaul (Stitch MCP)** | 🔵 **Active — this plan** |
| **G — Registration & Access Control Overhaul** | 🔵 **Active — this plan** |

---

## 0. Iteration Close-Out Protocol

Every iteration below ends the same way, in this order:
1. Verify acceptance criteria are actually met
2. Inspect the final diff before considering it done
3. Update `CLAUDE.md` (current-state snapshot — overwrite, not append)
4. Append an entry to `progress.md` (permanent chronological log)
5. Record any blockers/follow-ups
6. Stop — don't auto-continue into the next iteration without an explicit go-ahead

---

## Unified Build Order

Build in this exact order — it's not F-then-G or G-then-F, it's interleaved so each step only ever gets built once.

| # | Iteration | Why it goes here |
|---|---|---|
| 1 | F1 — Design system & skeleton | Foundation every later screen builds on |
| 2 | G1 — Multi-step registration | Built using F1's components from the start, not restyled later |
| 3 | G2 — Doctor profile: state, city, credentials | Extends the registration wizard from G1 immediately |
| 4 | G3 — Location-based doctor matching | Depends on G2's data existing |
| 5 | G4 — Doctor approval workflow | Depends on G2's credential submission existing |
| 6 | G5 — Language preference & matching | Depends on G2's doctor profile existing |
| 7 | G6 — Secondary emergency contact + crisis escalation | Depends on G1's registration + Phase B/D1's classifier (already complete) |
| 8 | G7 — VR access model change | Depends on Phase A's VR module + A5 telemetry (already complete) |
| 9 | F2 — Hero section, feature highlights & positioning | Built *after* G1-G7 exist, so the hero can accurately showcase real features and the positioning copy (formerly G8) is right the first time |
| 10 | F3 — Compliance, privacy & crisis helpline panel | Built *after* G6, so the crisis panel accurately reflects the real escalation feature instead of promising something not yet built |
| 11 | F4 — Full panel visual overhaul | Last, so it applies final styling once across every screen — including the new registration, doctor-approval, and location/language screens from G — instead of styling twice |

---

## Iteration Detail

### 1. F1: Design System & Skeleton Setup
- Tasks: Establish Stitch MCP design tokens, glassmorphism UI card components, typography scale, micro-animations, and responsive layout grid; update `frontend/src/pages/Home.tsx` to replace the prototype gateway buttons.
- Acceptance: Landing page skeleton renders with clean responsive layouts, consistent styling primitives, and fast load times. Components are structured for reuse by G1's registration wizard next.
- Close-out: Full Section 0 protocol.

### 2. G1: Multi-Step Registration Flow
- Tasks: Build the multi-step wizard for both patient and doctor roles using F1's component library: Step 1 — account basics (name, email, password); Step 2 — contact details + secondary emergency contact; Step 3 — role-specific profile (patient: state/city, demographics; doctor: state/city, license/credentials, languages spoken); Step 4 — consent & disclosures; Step 5 — confirmation.
- Acceptance: A user completes registration across discrete steps with progress preserved between them (no data loss on back/refresh); no single screen asks for more than one related group of fields; visually consistent with F1's design system from the start.
- Close-out: Full Section 0 protocol.

### 3. G2: Doctor Profile — State, City & Credentials
- Tasks: Add state, city, and license/credential upload to the doctor's profile step (built in G1); store credential documents for admin review.
- Acceptance: A doctor cannot complete registration without state, city, and a credential submission.
- Close-out: Full Section 0 protocol.

### 4. G3: Location-Based Doctor Matching
- Tasks: Build a filter/matching layer so patients see doctors from their own state and city by default, with an explicit option to broaden the search; display each doctor's location in results.
- Acceptance: A patient in a given state/city sees local doctors first; broadening the filter reveals others.
- Close-out: Full Section 0 protocol.
- Note: supersedes the "any doctor, any location" assumption implicit in the original Doctor Panel scope (PRD Section 6.2).

### 5. G4: Doctor Approval Workflow
- Tasks: Build an admin-side review queue for pending doctor registrations (credentials from G2) with approve/reject + reason, and a doctor-side pending/approved/rejected status view.
- Acceptance: A newly registered doctor cannot appear in patient-facing search or accept appointments until explicitly approved by an admin.
- Close-out: Full Section 0 protocol.
- Note: formalizes the rule stated informally in the original roadmap's Iteration 5 into a full, auditable workflow.

### 6. G5: Language Preference & Matching
- Tasks: Add "languages spoken" to the doctor profile (G2); add a language filter/selector to the appointment booking flow so patients can filter by, or see tags for, which languages a doctor is available in.
- Acceptance: A patient filtering by a specific language sees only doctors who list that language.
- Close-out: Full Section 0 protocol.

### 7. G6: Secondary Emergency Contact + Crisis Escalation
- Tasks: Add a secondary emergency contact number to patient registration (G1), with clear consent language at signup explaining it will only be contacted if a high-risk situation is detected. Extend the existing semantic risk-detection/classifier layer so a detected suicide/self-harm risk signal triggers a parallel notification to the secondary contact and to the on-call doctor pool in the patient's state, alongside the assigned-doctor alert.
- Acceptance: A simulated high-risk input triggers notifications to both the secondary contact and the state's on-call doctors within the existing SLA window; detection remains a deterministic/classifier layer, independent of chatbot generation quality.
- Close-out: Full Section 0 protocol.
- Note: extends the multi-tier escalation from the earlier Panic Button/Escalation work (Phase D6) with a new notification channel — adds to, rather than replaces, the assigned-doctor and crisis-line paths already defined there.

### 8. G7: VR Access Model Change
- Tasks: Remove "VR appointment" as a doctor-scheduled slot type. Doctor panel keeps: recommending/assigning specific VR modules as part of a treatment plan, and viewing VR usage/progress reports (reusing the session telemetry from Phase A5). Patient panel gets full self-service access — any patient can browse and try any VR module in demo mode directly, independent of doctor assignment; doctor-recommended modules are shown but not gating.
- Acceptance: A patient with no doctor-assigned module can still launch and complete any available VR scenario; a doctor can still view a usage report for that session afterward.
- Close-out: Full Section 0 protocol.
- Note: changes the access-control layer on top of the VR realism work in Phase A — the scenarios themselves are unaffected.

### 9. F2: Hero Section, Feature Highlights & Positioning
- Tasks: Build the Stitch MCP hero section and feature showcase cards — now for the real, completed feature set: WebXR exposure therapy, the AURA AI companion, location/language-matched doctor consultation (G3/G5), and secondary-contact crisis support (G6). Headline positioning is "AI chatbot + mental health and psychological support system" with VR as one feature among several, not the primary framing. Remove campus/institution-specific language from all landing and auth copy in favor of general-audience messaging. Wire CTA buttons for Patient and Doctor portals.
- Acceptance: Hero and feature grid render cleanly across mobile, tablet, and desktop; CTAs navigate correctly; a first-time visitor's first impression communicates "mental health support platform," not "VR therapy app"; no copy is scoped to a specific school or institution.
- Close-out: Full Section 0 protocol.
- Note: this step absorbs what was previously a separate G8 iteration — positioning is handled once, here, instead of twice.

### 10. F3: Compliance, Privacy & Crisis Helpline Panel
- Tasks: Add a Tele-MANAS helpline banner, a DPDP Act 2023 compliance badge, an anonymized-data explainer panel, and persistent crisis helpline shortcuts — now accurately describing the real secondary-contact escalation feature built in G6, not a placeholder promise.
- Acceptance: Helpline info and compliance badges are visually prominent and meet WCAG 2.1 AA accessibility standards; any claim made about what happens in a crisis matches what G6 actually does.
- Close-out: Full Section 0 protocol.
- **Before presenting:** confirm the Tele-MANAS number and any other helpline shown is current — this is the one part of the demo where "looks right" isn't good enough, since it's a real safety resource even in a demo.

### 11. F4: Full Panel Visual Overhaul
- Tasks: Apply the Stitch MCP system across every screen that now exists — Patient Dashboard, Doctor Triage Dashboard, AI Companion chat interface, Admin Analytics view, the registration wizard (G1), doctor approval queue (G4), and location/language-filtered doctor search (G3/G5) — consistent dark/light contrast cards, standardized status tags, polished Recharts visualizations.
- Acceptance: All screens work with the upgraded design system without breaking existing backend integration or the test suite you do have.
- Close-out: Full Section 0 protocol.

---

## Sequencing Notes

- Follow the Unified Build Order table exactly — it exists specifically so nothing in F or G gets touched twice.
- Nothing here depends on the deferred C/E phases; this whole sequence is safe to build and demo independently of them.
- Once step 11 is done, that's your full presentation-ready state: A + B + D (functional) + F + G (complete, polished, and consistent). 