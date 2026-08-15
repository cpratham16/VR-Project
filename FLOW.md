# FLOW.md — Control Flow & Execution Chains (Source of Truth)

## 1. Authentication & Session Flow
```
User (Login/Signup Page)
  └── POST /api/v1/auth/login OR /auth/signup
        ├── Hash password using Bcrypt (`backend/app/core/security.py`)
        ├── Generate JWT Access Token with user `sub` ID & expiry
        └── Client stores token in localStorage ('token')
              └── `apiClient` Axios interceptor attaches `Authorization: Bearer <token>` to all HTTP requests
                    └── `get_current_user` dependency verifies JWT signature and resolves DB User model
```

---

## 2. Patient Onboarding Flow
```
Patient logs in -> Accesses `/patient/dashboard`
  └── Enters `RequireOnboarding` wrapper in `App.tsx`
        └── GET `/api/v1/patient/status`
              ├── IF `has_consent` is false:
              │     └── Redirect to `/patient/onboarding/consent`
              │           └── POST `/api/v1/patient/consent` -> set consent = true
              ├── IF `has_profile` is false:
              │     └── Redirect to `/patient/onboarding/profile`
              │           └── POST `/api/v1/patient/profile` -> save demographics & medical history
              └── IF both true:
                    └── Render requested page (Dashboard / Screening / Mood / Community / Chat / Appointments)
```

---

## 3. Psychological Screening Flow (PHQ-9 & GAD-7)
```
Patient opens `/patient/screening`
  ├── Fills out 9-item PHQ-9 (Depression) & 7-item GAD-7 (Anxiety) questionnaire
  └── Submits form -> POST `/api/v1/patient/screening`
        ├── Backend calculates `phq9_score` (sum of answers 0-3)
        ├── Backend calculates `gad7_score` (sum of answers 0-3)
        ├── Runs `calculate_phq9_severity` (Minimal, Mild, Moderate, Moderately Severe, Severe)
        ├── Runs `calculate_gad7_severity` (Minimal, Mild, Moderate, Severe)
        └── Stores `ScreeningResult` record in DB
              └── Returns calculated scores and severity classifications to Frontend UI
```

---

## 4. Pseudonymous Community & Safety Moderation Flow
```
Student creates Post/Comment -> POST /api/v1/community/posts
  ├── Fetches student's assigned `author_pseudonym` (hides real identity)
  ├── Distress Scanner (`risk_engine.py`): Scans text for self-harm / panic keywords
  │     ├── IF keywords detected:
  │     │     ├── Sets `moderation_status = "flagged_pending"` (hidden from public feed)
  │     │     └── Creates `RiskAlert` for doctor triage (`trigger_source="community_post_flag"`)
  │     └── IF clean:
  │           └── Sets `moderation_status = "approved"` (visible instantly in public feed)
  └── Doctor reviews queue -> GET /api/v1/doctor/moderation/queue
        └── Doctor clicks Approve/Reject -> POST /api/v1/doctor/moderation/posts/{post_id}/action
```

---

## 5. Doctor Triage & Alert Management Flow
```
Doctor accesses `/doctor/dashboard`
  ├── GET `/api/v1/doctor/alerts` -> Renders sticky emergency alert banner for unhandled CRITICAL flags
  └── GET `/api/v1/doctor/triage`
        ├── Fetches all patient profiles with latest `ScreeningResult` & `MoodEntry`
        ├── Sorts / flags patients with Severe / Moderately Severe scores for high priority triage
        └── Doctor clicks on patient -> Navigate to `/doctor/patient/:patientId`
              ├── GET `/api/v1/doctor/patient/:patientId` (loads screening history, mood charts, clinical notes)
              └── POST `/api/v1/doctor/patient/:patientId/notes` (appends clinical evaluation note)
```

---

## 6. AI Companion Chat & Hybrid RAG Flow
```
Patient opens `/patient/chat`
  ├── Submits text query to AURA AI -> POST `/api/v1/patient/chat`
        ├── Distress Scanner (`risk_engine.py`): Scans input for self-harm / panic keywords
        │     └── IF flagged: Creates `RiskAlert` in DB (`severity="CRITICAL"` or `"HIGH"`)
        ├── RAG Retriever (`rag_engine.py`): Vector matches query against `archive/conversations_training.csv`
        │     └── Returns top 2 doctor-patient clinical response exemplars
        ├── Prompt Synthesizer (`ai_companion.py`): Combines System Rules + PHQ-9/GAD-7 band + RAG Exemplars
        │     ├── IF `GROQ_API_KEY` present: Calls Groq LLM (`llama-3.3-70b-versatile`)
        │     └── IF offline / API error: Executes Local Fallback Engine using RAG exemplar
        └── Stores `ChatMessage` in DB and returns response to frontend UI with RAG badge indicator
```

---

## 7. Fail-Safe Panic SOS & Crisis Escalation Flow
```
User clicks "Panic SOS" button (Navbar or Modal)
  ├── Frontend immediately opens `PanicModal.tsx` displaying zero-network crisis numbers:
  │     ├── Campus Emergency Desk: 1800-999-0000
  │     ├── Tele-MANAS National Helpline: 14416 / 1800-599-0019
  │     └── Student Crisis Line: +91 98765 43210
  └── Simultaneously sends asynchronous call -> POST `/api/v1/patient/panic`
        └── Backend creates `RiskAlert` (`severity="CRITICAL"`, `trigger_source="panic_sos"`)
              └── Surfaced instantly on Doctor Triage Banner (`/doctor/dashboard`) for doctor acknowledgment
```

---

## 8. VR Exposure Therapy Assignment & Session Flow
```
DOCTOR ASSIGNS VR SESSION:
  Doctor opens `/doctor/vr` -> Selects Scenario + Patient + Intensity + Duration + Steps + Instructions
    └── POST `/api/v1/doctor/vr/assign`
          ├── Validates patient exists and scenario is active
          └── Creates `VRSession` record (status = "assigned")
                └── Appears on patient's `/patient/vr` hub

PATIENT LAUNCHES SESSION:
  Patient opens `/patient/vr` -> Views assigned sessions
    └── Clicks "Launch Session" -> POST `/api/v1/patient/vr/sessions/{id}/start`
          ├── Sets `status = "in_progress"`, `started_at = now()`
          └── Launches A-Frame 3D scene + HUD overlay
                ├── Intro phase: SUDS-pre slider, optional BLE heart rate monitor connection
                ├── Running phase: A-Frame scene + timer + telemetry POST every 5s
                │     ├── Heart rate & HRV from Web Bluetooth (or simulated fallback)
                │     ├── Backend calculates `stress_index` from HR/HRV via `vr_engine.py`
                │     └── Patient advances through exposure stages via on-screen prompts
                └── Post phase: SUDS-post slider, feedback textarea
                      └── POST `/api/v1/patient/vr/sessions/{id}/complete`
                            └── Stores SUDS pre/post, feedback, completion timestamp
```

---

## 9. Heart Rate / HRV Telemetry Pipeline
```
Patient's Browser (VRSessionRunner.tsx)
  ├── Web Bluetooth: navigator.bluetooth.requestDevice({ filters: [{ services: ['heart_rate'] }] })
  │     └── Subscribes to Heart Rate Measurement characteristic (0x180D service, 0x2A37 characteristic)
  │           ├── Parses instant BPM from byte payload
  │           └── Computes RMSSD HRV from RR-interval samples (60s rolling window)
  ├── Simulated fallback (when no device/Bluetooth unavailable):
  │     └── Generates resting HR ~72bpm with periodic stress spikes correlated to exposure stages
  └── Every ~5 seconds -> POST `/api/v1/patient/vr/sessions/{id}/telemetry`
        ├── Backend receives heart_rate, hrv_rmssd, scene_stage
        ├── Calculates stress_index = hrComponent * 0.55 + hrvComponent * 0.45
        └── Stores in `VRTelemetry` table for doctor analytics
```

---

## 10. Anonymization Pipeline & Admin Dashboard Flow
```
ADMIN TRIGGERS PIPELINE (manual button in AdminDashboard):
  POST `/api/v1/admin/analytics/run-pipeline` (admin-only JWT required)
    └── `anonymizer.py` ETL service executes one-way write:
          ├── Reads `users` (state, city) -> resolves region = "City, State"
          ├── Reads `screening_results` (user_id, severity_band, created_at)
          ├── Reads `mood_entries` (user_id, mood_score, created_at)
          ├── Reads `risk_alerts` (user_id, severity, created_at) [CRITICAL+HIGH only]
          ├── Reads `vr_sessions` (patient_id, status, completed_at) [completed only]
          ├── Groups by (region, YYYY-MM)
          ├── Computes tallies: distinct patients, severity band counts, avg mood, alert counts
          └── UPSERTS into `regional_aggregates` (delete month -> insert fresh)

ADMIN DASHBOARD READS (GET /admin/analytics/*):
  ├── overview   -> totals + severity band distribution from `regional_aggregates`
  ├── regions    -> distinct regions available
  ├── trend      -> time series for the last N months, filtered by region
  └── spikes     -> flags any (region, month) where alert_rate > mean + 2σ of that region's history

HARD BOUNDARY: `regional_aggregates` contains NO foreign keys, NO user IDs,
NO email, NO pseudonym — only region string + period string + numeric aggregates.
```
