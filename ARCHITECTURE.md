# ARCHITECTURE.md — System Architecture & Data Model (Source of Truth)

## 1. Overview & Tech Stack
The VR Mental Health Platform is a web-based clinical triage, AI-supported telehealth, peer community support, and patient telemetry platform enabling VR-based or self-reported psychological screening, pseudonymous peer support, AI companion support, distress escalation, mood monitoring, and doctor triage.

### Backend
- **Framework:** FastAPI (Python 3.13)
- **Database ORM:** SQLAlchemy 2.0 (Async extension with `asyncpg`)
- **Database Engine:** PostgreSQL
- **Migrations:** Alembic
- **AI & Safety Engine:** Groq API (`llama-3.3-70b-versatile`) + Hybrid RAG retriever (`archive/conversations_training.csv`) + Distress Keyword Scanner
- **Authentication:** OAuth2 with Password Bearer & JWT tokens (Bcrypt password hashing)
- **Validation & Serialization:** Pydantic v2 Settings & Schemas

### Frontend
- **Framework:** React 19 with TypeScript 6
- **Build Tool:** Vite 8
- **Styling:** TailwindCSS v4
- **Routing:** React Router DOM v7
- **Charts:** Recharts
- **HTTP Client:** Axios (configured with auth bearer interceptor in `src/api/client.ts`)

---

## 2. Core Entities & Data Model

### `User` (`backend/app/models/user.py`)
- `id`: UUID (Primary Key)
- `email`: String (Unique, Indexed)
- `password_hash`: String
- `role`: Enum / String (`patient`, `doctor`, `admin`)
- `is_verified`: Boolean (Doctor verification flag)
- `state`: String (nullable — Indian state/UT, captured at patient signup)
- `city`: String (nullable — city/district, captured at patient signup)
- `created_at`, `updated_at`: Timestamp

### `PatientProfile` (`backend/app/models/patient.py`)
- `id`: UUID (Primary Key)
- `user_id`: Foreign Key (`User.id`)
- `pseudonym`: String
- `created_at`, `updated_at`: Timestamp

### `ConsentRecord` (`backend/app/models/patient.py`)
- `id`: UUID (Primary Key)
- `user_id`: Foreign Key (`User.id`)
- `consent_version`: String
- `agreed_to_ai_processing`: Boolean
- `agreed_to_data_usage`: Boolean
- `agreed_at`: Timestamp

### `ScreeningResult` (`backend/app/models/screening.py`)
- `id`: UUID (Primary Key)
- `user_id`: Foreign Key (`User.id`)
- `phq9_score`: Integer (0-27)
- `phq9_severity`: String (`Minimal`, `Mild`, `Moderate`, `Moderately Severe`, `Severe`)
- `gad7_score`: Integer (0-21)
- `gad7_severity`: String (`Minimal`, `Mild`, `Moderate`, `Severe`)
- `created_at`: Timestamp

### `MoodEntry` (`backend/app/models/mood.py`)
- `id`: UUID (Primary Key)
- `user_id`: Foreign Key (`User.id`)
- `score`: Integer (1-5)
- `notes`: Text
- `created_at`: Timestamp

### `CommunityPost` (`backend/app/models/community.py`)
- `id`: UUID (Primary Key)
- `user_id`: Foreign Key (`User.id`)
- `author_pseudonym`: String
- `category`: String (`Academic Stress`, `Exam Anxiety`, `Peer Support`, `General Wellness`)
- `title`: String
- `content`: Text
- `is_flagged`: Boolean
- `moderation_status`: String (`approved`, `flagged_pending`, `rejected`)
- `created_at`, `updated_at`: Timestamp

### `CommunityComment` (`backend/app/models/community.py`)
- `id`: UUID (Primary Key)
- `post_id`: Foreign Key (`CommunityPost.id`)
- `user_id`: Foreign Key (`User.id`)
- `author_pseudonym`: String
- `content`: Text
- `is_flagged`: Boolean
- `moderation_status`: String (`approved`, `flagged_pending`, `rejected`)
- `created_at`: Timestamp

### `ChatSession` (`backend/app/models/chat.py`)
- `id`: UUID (Primary Key)
- `user_id`: Foreign Key (`User.id`)
- `title`: String
- `created_at`, `updated_at`: Timestamp

### `ChatMessage` (`backend/app/models/chat.py`)
- `id`: UUID (Primary Key)
- `session_id`: Foreign Key (`ChatSession.id`)
- `sender`: String (`user`, `assistant`, `system`)
- `content`: Text
- `risk_flag`: Boolean
- `rag_context_used`: Boolean
- `created_at`: Timestamp

### `RiskAlert` (`backend/app/models/alert.py`)
- `id`: UUID (Primary Key)
- `user_id`: Foreign Key (`User.id`)
- `severity`: String (`CRITICAL`, `HIGH`, `MEDIUM`)
- `trigger_source`: String (`panic_sos`, `chat_distress`, `community_post_flag`, `screening_high`)
- `details`: Text
- `status`: String (`pending`, `acknowledged`, `resolved`)
- `acknowledged_by_doctor_id`: Foreign Key (`User.id`)
- `created_at`, `resolved_at`: Timestamp

### `VRScenario` (`backend/app/models/vr.py`)
- `id`: UUID (Primary Key)
- `slug`: String (Unique, `heights`, `public_speaking`)
- `name`: String
- `phobia_type`: String (`acrophobia`, `glossophobia`)
- `description`: Text
- `is_active`: Boolean
- `created_at`: Timestamp

### `VRSession` (`backend/app/models/vr.py`)
- `id`: UUID (Primary Key)
- `patient_id`: Foreign Key (`User.id`)
- `doctor_id`: Foreign Key (`User.id`)
- `scenario_id`: Foreign Key (`VRScenario.id`)
- `intensity_level`: String (`low`, `medium`, `high`)
- `duration_minutes`: Integer
- `exposure_steps`: Integer
- `instructions`: Text
- `status`: String (`assigned`, `in_progress`, `completed`, `cancelled`)
- `suds_pre`, `suds_post`: Integer (1-10)
- `patient_feedback`: Text
- `assigned_at`, `started_at`, `completed_at`: Timestamp

### `VRTelemetry` (`backend/app/models/vr.py`)
- `id`: UUID (Primary Key)
- `session_id`: Foreign Key (`VRSession.id`)
- `timestamp`: DateTime
- `heart_rate`: Float (bpm)
- `hrv_rmssd`: Float (ms)
- `stress_index`: Float (0-100)
- `scene_stage`: Integer

### `RegionalAggregate` (`backend/app/models/anonymized.py`)
- **HARD BOUNDARY:** No foreign keys, no user_id, no email, no pseudonym — only region + period + numeric aggregates.
- `id`: UUID (Primary Key)
- `region`: String (e.g. "Pune, Maharashtra")
- `period`: String (YYYY-MM)
- `total_patients`: Integer
- `screening_count`: Integer
- `phq9_minimal`, `phq9_mild`, `phq9_moderate`, `phq9_moderately_severe`, `phq9_severe`: Integer
- `gad7_minimal`, `gad7_mild`, `gad7_moderate`, `gad7_severe`: Integer
- `avg_mood_score`: Float
- `mood_entry_count`: Integer
- `risk_alert_count`: Integer
- `vr_sessions_completed`: Integer
- `created_at`: Timestamp

---

## 3. Frontend Architecture

### Routing (`frontend/src/App.tsx`)
- `/`: Public Home / Landing page (`MainLayout`)
- `/auth/login`: Authentication Login (`Login.tsx`)
- `/auth/signup`: User Registration (`Signup.tsx`)
- `/patient/onboarding/consent`: Consent screen (`ConsentScreen.tsx`)
- `/patient/onboarding/profile`: Patient profile setup (`ProfileSetup.tsx`)
- `/patient/dashboard`: Patient dashboard (`Dashboard.tsx`, protected + requires onboarding)
- `/patient/screening`: PHQ-9 & GAD-7 assessment (`ScreeningPage.tsx`, protected + requires onboarding)
- `/patient/mood`: Mood logger (`MoodTrackerPage.tsx`, protected + requires onboarding)
- `/patient/community`: Pseudonymous Peer Forum (`CommunityPage.tsx`, protected + requires onboarding)
- `/patient/chat`: Supportive AI Companion (`AIChatPage.tsx`, protected + requires onboarding)
- `/patient/vr`: VR Exposure Therapy Hub (`VRTherapyPage.tsx`, protected + requires onboarding)
- `/patient/appointments`: Patient appointment schedule (`AppointmentsPage.tsx`, protected + requires onboarding)
- `/doctor/dashboard`: Doctor Triage Overview & Alerts (`TriageDashboard.tsx`, protected for `doctor` & `admin`)
- `/doctor/moderation`: Safety Moderation Queue (`ModerationQueuePage.tsx`, protected)
- `/doctor/vr`: VR Therapy Assignment (`VRAssignmentPage.tsx`, protected for `doctor` & `admin`)
- `/doctor/patient/:patientId`: Doctor detailed patient clinical view (`PatientDetail.tsx`, protected)
- `/doctor/appointments`: Doctor appointment management (`DoctorAppointments.tsx`, protected)
- `/admin/dashboard`: Administrative Analytics Portal (`AdminDashboard.tsx`, protected for `admin` only)

---

## 4. API Endpoints Reference (`backend/app/api/v1/`)
- `POST /api/v1/auth/signup`: Register user
- `POST /api/v1/auth/login`: Authenticate and receive JWT access token
- `GET /api/v1/auth/me`: Fetch authenticated user profile
- `GET /api/v1/patient/status`: Check onboarding status (`has_consent`, `has_profile`)
- `POST /api/v1/patient/consent`: Submit patient consent record
- `POST /api/v1/patient/profile`: Create/Update patient profile
- `POST /api/v1/patient/screening`: Submit PHQ-9 & GAD-7 responses
- `GET /api/v1/patient/screening/history`: Retrieve patient screening history
- `POST /api/v1/patient/mood`: Submit daily mood entry
- `GET /api/v1/patient/mood/history`: Retrieve patient mood logs
- `GET /api/v1/community/posts`: List public approved community posts
- `POST /api/v1/community/posts`: Create new community discussion post
- `GET /api/v1/community/posts/{post_id}`: Retrieve post details and approved comments
- `POST /api/v1/community/posts/{post_id}/comments`: Add comment to post
- `GET /api/v1/doctor/moderation/queue`: Fetch flagged community posts pending review
- `POST /api/v1/doctor/moderation/posts/{post_id}/action`: Doctor approve/reject moderation action
- `POST /api/v1/patient/chat`: Send message to AI Companion (`AURA`)
- `GET /api/v1/patient/chat/history`: Retrieve active AI companion conversation
- `POST /api/v1/patient/panic`: Trigger Panic SOS emergency alert
- `GET /api/v1/patient/vr/assigned`: List patient's assigned VR sessions
- `POST /api/v1/patient/vr/sessions/{session_id}/start`: Start a VR session
- `POST /api/v1/patient/vr/sessions/{session_id}/telemetry`: Upload HR/HRV telemetry (every ~5s)
- `POST /api/v1/patient/vr/sessions/{session_id}/complete`: Submit SUDS pre/post & feedback, mark session complete
- `GET /api/v1/doctor/triage`: Doctor triage view of patient risk scores
- `GET /api/v1/doctor/alerts`: Fetch pending emergency alerts for doctor feed
- `POST /api/v1/doctor/alerts/{alert_id}/acknowledge`: Acknowledge/resolve emergency alert
- `GET /api/v1/doctor/vr/scenarios`: List active VR exposure scenarios
- `POST /api/v1/doctor/vr/assign`: Assign VR session with full config
- `GET /api/v1/doctor/vr/sessions?patient_id=`: List VR sessions (optionally filtered by patient)
- `GET /api/v1/doctor/vr/sessions/{session_id}/telemetry`: View telemetry series for a session
- `POST /api/v1/doctor/vr/sessions/{session_id}/cancel`: Cancel a VR session
- `POST /api/v1/admin/analytics/run-pipeline`: Trigger anonymization ETL (admin only, manual demo trigger)
- `GET /api/v1/admin/analytics/overview`: Aggregated totals + severity band distribution
- `GET /api/v1/admin/analytics/regions`: List of available regions in reporting store
- `GET /api/v1/admin/analytics/trend?region=&months=12`: Monthly trend time series (optionally filtered by region)
- `GET /api/v1/admin/analytics/spikes`: Spike/anomaly detection — flag regions with alert-rate exceeding mean+2σ
