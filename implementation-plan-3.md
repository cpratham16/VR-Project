# Implementation Plan 3
## Student Panel Polish, Diary, Scheduling UI, Community & Chat, Doctor Panel Fix, Admin Resource System

Continues from Phases A-G. New work organized as Phases H through N, same tracking discipline as before, plus a git workflow added to the close-out protocol.

---

## Status Summary

| Phase | Scope | Status |
|---|---|---|
| A, B, D | VR, RAG engine, feature upgrades | ✅ Complete |
| F, G | Frontend overhaul, registration & access control | 🔵 Active (see `presentation-ready-plan.md`) |
| C, E | RAG testing, production hardening | ⏭️ Deferred |
| **H** | Student panel navigation, bugs & UI polish | 🔵 New — this plan |
| **I** | PHQ-9/GAD-7 assessment UX overhaul | 🔵 New — this plan |
| **J** | Diary (new private feature) | 🔵 New — this plan |
| **K** | Scheduling UI overhaul | 🔵 New — this plan |
| **L** | Community UI & chat rooms | 🔵 New — this plan |
| **M** | Doctor panel SOS alert display fix | 🔵 New — this plan |
| **N** | Admin resource, newsletter & communication system | 🔵 New — this plan |
| **O** | Full API contract test sweep + E2E + report | 🔵 New — this plan |

---

## 0. Iteration Close-Out Protocol

Unchanged from before, every iteration ends with:
1. Verify acceptance criteria are actually met
2. Inspect the final diff before considering it done
3. Update `CLAUDE.md` (overwrite current-state snapshot)
4. Append an entry to `progress.md`
5. Record any blockers/follow-ups
6. Stop — no auto-continuing to the next iteration without explicit go-ahead

## 0b. Git Workflow (new — applies to every iteration below)

- **Never commit directly to `main`.**
- Each iteration gets its own feature branch off your integration branch (`develop`/`staging`), named `feature/<iteration-id>-<short-slug>` — e.g. `feature/j2-diary-calendar-view`.
- Commit messages are prefixed with the iteration ID — e.g. `[J2] Add calendar dashboard view with diary markers`.
- Once Section 0's close-out is complete, push the branch and open a PR into `develop`/`staging` (not `main`). PR description includes: iteration ID, summary, acceptance criteria checklist, and screenshots for any UI change.
- Merging to `main` happens as a separate, deliberate release step covering a batch of completed iterations (e.g., right before your presentation) — never automatically per-iteration.
- Close-out line for every iteration below reads "Full Section 0 + 0b protocol" — that means both the verification/logging steps *and* the branch/PR step, every time.

---

## Phase H — Student Panel: Navigation, Bugs & UI Polish (6 iterations)

**H1: Remove SOS from landing page; fold "Get Help" into SOS**
- Tasks: Remove the SOS button from the public landing page (it belongs in the authenticated student panel only, per H3). Remove the separate "Get Help" button anywhere it appears in the student panel and merge its functionality (helpline links, resources) into the floating SOS button's expanded view.
- Acceptance: Landing page has no SOS element; there is exactly one help/crisis entry point in the student panel, not two competing ones.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/h1-sos-consolidation`.

**H2: Global navigation — collapsible left panel + back/profile/update-info**
- Tasks: Move features currently in the top navbar into a collapsible left side panel (expand/collapse toggle). Add a reusable header component with a back-to-dashboard button and a profile button; build an "update my info" screen for both doctor and patient roles using this same component.
- Acceptance: Left panel opens/closes without layout shift; back and profile buttons appear consistently across every authenticated screen in both patient and doctor panels; a user can edit and save their own profile info.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/h2-nav-overhaul`.

**H3: Floating panic/SOS button — student panel only**
- Tasks: Add a floating SOS button, bottom-left, visible only in the student/patient panel. Confirm it does not render in doctor or admin panels.
- Acceptance: Button is present and functional on every student screen; absent from doctor and admin views.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/h3-floating-sos`.

**H4: Mood tracker visual redesign**
- Tasks: Rebuild the mood tracker page using the Phase F design system (cards, typography, color tokens) instead of the current plain/pale layout.
- Acceptance: Mood tracker visually matches the rest of the redesigned app; no functional regression to existing mood-logging behavior.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/h4-mood-tracker-redesign`.

**H5: Fix admin login**
- Tasks: Diagnose and fix the admin login failure (check auth flow, role assignment, session handling for the admin role specifically).
- Acceptance: An admin account can log in reliably and lands on the admin dashboard.
- Close-out: Full Section 0 + 0b protocol. Branch: `fix/h5-admin-login`.

**H6: Student panel bug sweep**
- Tasks: Triage the reported "student panel bugs" against your actual bug list/tracker and fix each. (This plan can't scope specific fixes without a bug list — attach or link one when you start this iteration so it has real acceptance criteria instead of "fix bugs.")
- Acceptance: Every tracked bug in the list is resolved and verified; no new regressions introduced.
- Close-out: Full Section 0 + 0b protocol. Branch: `fix/h6-student-panel-bugs`.

---

## Phase I — PHQ-9 / GAD-7 Assessment UX Overhaul (2 iterations)

**I1: Daily popup reminder, skippable**
- Tasks: Trigger a daily popup prompting the user to take the PHQ-9/GAD-7 if not already completed that day; include "Skip" and "Take later" options that don't block the rest of the app.
- Acceptance: Popup appears once per day per unfinished assessment; skipping doesn't reappear again until the next day; "take later" leaves it accessible from the dashboard.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/i1-assessment-daily-popup`.

**I2: One-question-at-a-time flow**
- Tasks: Replace the current all-at-once questionnaire layout with a single-question view plus a "Next" button, for both PHQ-9 and GAD-7.
- Acceptance: Only one question is visible at a time; progress is preserved if the user navigates away mid-assessment; scoring logic (already built) is unaffected by the layout change.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/i2-assessment-one-at-a-time`.

---

## Phase J — Diary (New Private Feature) (7 iterations)

**J1: Diary data model + entry CRUD**
- Tasks: Build the diary entry model (optional title, date/time, free-text content) and create/edit/delete operations; support multiple entries per day.
- Acceptance: A user can create, edit, and delete diary entries; multiple entries on the same day are all stored and retrievable independently.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/j1-diary-crud`.

**J2: Calendar dashboard view**
- Tasks: Build the diary's main dashboard as a calendar, marking any day with ≥1 entry using a 📖 indicator; support month navigation (previous/next); clicking a marked date shows all entries for that day.
- Acceptance: Calendar correctly reflects entry data; navigating months works; clicking a marked date lists every entry from that day.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/j2-diary-calendar-view`.

**J3: Search & filter**
- Tasks: Add keyword search and filters (date range, emotion tag if set) across diary entries.
- Acceptance: A keyword search returns matching entries; filters narrow results correctly.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/j3-diary-search`.

**J4: Optional emotion tagging**
- Tasks: Allow a user to optionally tag an entry with an emotion (happy, calm, sad, anxious, stressed, etc.) at write-time. Keep this fully separate from the main Mood Tracker's data model — it's descriptive metadata on a diary entry, not a mood-tracker log.
- Acceptance: An entry can be saved with or without an emotion tag; diary emotion tags do not write to or read from Mood Tracker data.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/j4-diary-emotion-tags`.

**J5: PIN/biometric privacy lock**
- Tasks: Add an additional authentication layer (PIN, password, or device biometric) gating access to the Diary section specifically, separate from the app's main login.
- Acceptance: Diary content is inaccessible without passing this second check, even within an already-logged-in session.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/j5-diary-privacy-lock`.

**J6: Optional AI reflection**
- Tasks: Add an explicit, per-entry "reflect with AI" action. Only when a user actively triggers it for a specific entry does that entry's content get sent for AI analysis (general themes, supportive reflection, relevant coping resource suggestions). No entry is analyzed or transmitted anywhere without that specific, per-entry action.
- Acceptance: No diary content reaches the AI pipeline unless the user explicitly requests it for that exact entry; there is no global "auto-analyze my diary" setting.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/j6-diary-ai-reflection`.
- Note: this is a hard requirement, not a default-on convenience feature — keep the opt-in explicit and per-entry, exactly as specified.

**J7: Journaling streak tracker**
- Tasks: Track consecutive days with at least one diary entry and display a streak count.
- Acceptance: Streak increments correctly with consecutive-day entries and resets appropriately on a missed day.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/j7-diary-streak`.

---

## Phase K — Scheduling UI Overhaul (1 iteration)

**K1: Redesign scheduling layout**
- Tasks: Rebuild the scheduling screen with doctor info on the left, the session-booking module on the right, and a "My Appointments" list at the bottom.
- Acceptance: Layout matches this structure on desktop and adapts sensibly on mobile (e.g., stacked sections); existing booking functionality is unaffected.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/k1-scheduling-layout`.

---

## Phase L — Community UI & Chat Rooms (4 iterations)

**L1: Community UI improvement**
- Tasks: Redesign the community/forum screens using the Phase F design system for visual consistency.
- Acceptance: Community screens match the app's current design language; no loss of existing posting/commenting functionality.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/l1-community-ui`.

**L2: Real-time chat infrastructure**
- Tasks: Build the core chat backend — rooms, sending messages, receiving messages in real time (WebSockets), and persisting messages to the database.
- Acceptance: Two users in the same room see each other's messages appear live without a page refresh; message history persists and reloads correctly.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/l2-chat-realtime-core`.

**L3: Predefined chat rooms & role hierarchy**
- Tasks: Create the fixed room set — General Support, Academic Stress, Anxiety & Stress, Wellness Discussion — with Moderator and Doctor/Counselor roles having elevated visibility/permissions across rooms.
- Acceptance: All four rooms exist and are joinable by students; moderator and doctor/counselor accounts have the appropriate elevated access in each room.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/l3-chat-rooms-roles`.

**L4: Admin moderation tools for chat**
- Tasks: Give moderators/admins the ability to view, remove messages, and mute/restrict a user within the chat context.
- Acceptance: A moderator can remove a message and it disappears for all participants; a muted user cannot send further messages in that room.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/l4-chat-moderation`.

---

## Phase M — Doctor Panel: SOS Alert Display Fix (1 iteration)

**M1: Collapse SOS alerts on doctor dashboard**
- Tasks: Replace the current full-dashboard-taking-over SOS alert display with a collapsible/compact widget that doesn't obstruct the rest of the doctor's view.
- Acceptance: A high-risk alert is still clearly visible and actionable, but doesn't take over the whole screen; doctor can expand/collapse it and continue using the rest of the dashboard.
- Close-out: Full Section 0 + 0b protocol. Branch: `fix/m1-doctor-sos-collapse`.
- Note: this is a display fix only — the underlying escalation/notification logic from Phase D6/G6 is unaffected.

---

## Phase N — Admin Resource, Newsletter & Communication System (8 iterations)

**N1: Resource data model + upload/management**
- Tasks: Build the `resources` table and admin-facing upload/manage flow — title, description, resource type, category, file (PDF/book), thumbnail, publication status; support draft, publish, unpublish, edit, delete.
- Acceptance: An admin can upload a resource, save it as a draft, publish it, edit it later, and delete it.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/n1-resource-management`.

**N2: Wellness Library (student-facing)**
- Tasks: Build the student-facing library — browse, search, filter by category, open/read PDFs, save for later, track reading progress, mark as completed.
- Acceptance: A published resource appears in the library and is fully browsable/readable by students; save-for-later and progress tracking persist per user.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/n2-wellness-library`.

**N3: Newsletter creation & management**
- Tasks: Build the `newsletters` table and admin flow — create, save draft, preview, edit, publish.
- Acceptance: An admin can draft, preview, and publish a newsletter end-to-end.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/n3-newsletter-management`.

**N4: Newsletter display in-app**
- Tasks: Surface published newsletters to students under the Wellness Library or a dedicated Newsletter section.
- Acceptance: A published newsletter is visible and readable to students immediately after publishing.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/n4-newsletter-display`.

**N5: Communication campaign engine**
- Tasks: Build the `email_campaigns` and `email_recipients` tables and the campaign creation flow — audience selection (all/selected/group), delivery channel selection (in-app publish, notification, email, or combination), draft/preview/send-now/schedule, status tracking (pending/sent/failed), and history view.
- Acceptance: An admin can create a campaign, select an audience and channels, schedule or send it, and see accurate status in the history view.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/n5-communication-campaigns`.

**N6: Email delivery integration**
- Tasks: Integrate an actual email delivery service (e.g., SendGrid/SES) and wire it to the campaign engine from N5; track per-recipient delivery status.
- Acceptance: A sent campaign actually delivers email to real addresses in a test run, with delivery status correctly recorded per recipient.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/n6-email-delivery`.

**N7: In-app notification triggers**
- Tasks: Wire automatic in-app notifications for new resources, new newsletters, and announcements, linking directly to the relevant content.
- Acceptance: Publishing a resource or newsletter generates a notification that, when tapped, opens the correct item.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/n7-notification-triggers`.

**N8: Privacy & responsible communication safeguards**
- Tasks: Enforce that campaign audience selection can only use non-clinical criteria (e.g., "all students," a class/group) — never assessment scores, diary content, or other clinical/private data. Add email preference/unsubscribe controls for non-essential communications.
- Acceptance: The audience-selection UI has no option to target by assessment result, diary content, or any clinical field; a student can opt out of non-essential email and it's respected on the next send.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/n8-communication-privacy-safeguards`.
- Note: this extends the privacy principles from the original PRD (Section 7) and the admin-panel isolation work from Phase E/G3 — this system must never become a channel for using clinical data to target individual students.

---

## Phase O — Full API Contract Test Sweep + Frontend E2E + Report (1 iteration)

**O1: Comprehensive API contract testing & full-stack verification**
- Tasks: Build a complete backend contract test suite (`backend/tests/test_api_contract.py`) covering all 57 endpoints across 14 routers with full auth matrix (public/patient/doctor/admin), validation, edge cases, and RBAC boundaries. Add Playwright E2E tests (`frontend/e2e/`) for 18 critical user journeys across all three roles. Generate a Markdown report (`TEST_REPORT.md`) with endpoint×role matrix, pass/fail status, response samples, coverage gaps, and regression flags.
- Acceptance: Every endpoint tested against OpenAPI contract; all auth/role combinations verified; 18 critical frontend journeys passing; report documents current state with zero undocumented failures.
- Close-out: Full Section 0 + 0b protocol. Branch: `feature/o1-api-contract-sweep`.

---

## Sequencing Notes

- **H1-H3** (SOS/help consolidation) should land before **M1** (doctor-side SOS display fix) since they touch the same underlying alert/help concept from two different panels — do the student-facing side first so the doctor-facing fix reflects the final shape.
- **H2**'s reusable header/profile component should exist before **K1** (scheduling redesign) and **N2** (Wellness Library), since both are new/reworked screens that should use it from the start rather than being retrofitted later.
- **J1 → J2 → (J3, J4 in either order) → J5 → J6 → J7** — J5's privacy lock should go in before J6's AI reflection ships, since AI reflection is the most sensitive diary action and shouldn't be exposed before the section itself is properly gated.
- **L2 (chat infrastructure)** must exist before **L3 (rooms/roles)** and **L4 (moderation)** — L3 and L4 are configuration and permissions on top of L2's real-time core.
- **N1 → N2**, **N3 → N4**, and **N5 → N6 → N7** are each pairs/chains where the second item is meaningless without the first. **N8 should be built alongside N5**, not after — bolting privacy constraints onto an already-built audience-selection UI is more rework than building them in from the start.
- None of Phases H-N depend on the deferred C/E phases.
