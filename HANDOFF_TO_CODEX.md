# Civic AI — Codex Handoff

> **Generated on:** October 2, 2026  
> **Status:** Production-ready Development Prototype (Phase 1 Complete, Transitioning to Phase 2/3)  
> **Target Engineer / Agent:** Codex  
> **Repository Path:** `C:\Users\thara\Desktop\civic_ai`  

---

## 1. Executive Summary

### What Civic AI Currently Does
**Civic AI** is a personalized civic discovery and legal rights assistance platform designed for Indian citizens. Rather than requiring users to manually search government portals, read complex criteria, and decipher bureaucratized schemes, Civic AI reverses the paradigm:
1. **Citizen Profiling:** Captures demographic, socioeconomic, and occupational attributes through a 5-step wizard.
2. **Deterministic Matching:** Evaluates structured eligibility rules in real-time across central and state-specific schemes without hallucination.
3. **Application & Readiness Tracking:** Manages milestone stages and personal document checklists without storing sensitive identity documents.
4. **Civic AI Assistant:** Provides an in-app civic advisory chat interface with structured guidance.

### Current Development Phase
- **Phase 1 (Foundation & Onboarding Core):** **COMPLETE**
- **Phase 2 (Scheme Scaling & Enhanced Logic):** **PARTIAL**
- **Phase 3 (RAG / Production AI Integration & Telephony):** **NOT STARTED / PLACEHOLDER**

### Component Status Matrix

| Component Area | Status | Description |
| :--- | :--- | :--- |
| **Project Setup & Settings** | `COMPLETE` | Modular Django configuration using `python-decouple`, SQLite dev / PostgreSQL prod ready. |
| **Authentication & OTP** | `COMPLETE` | Custom mobile-based User model, OTP hashing, rate-limiting, and pluggable Mock provider. |
| **State & Language Selection** | `COMPLETE` | Dual-state onboarding (Andhra Pradesh & Tamil Nadu), dynamic transition landmarks, language cookies. |
| **5-Step Profile Wizard** | `COMPLETE` | Personal, Location, Education/Work, Income/Family, and Specialized attributes with completion ring. |
| **Deterministic Eligibility Engine**| `COMPLETE` | 13 rule types evaluated with clear outcomes (`eligible`, `not_eligible`, `incomplete`). |
| **Scheme Explorer & Details** | `COMPLETE` | Category pills, search bar, state/central filtering, bookmarking, and sticky eligibility checklists. |
| **Application Tracker** | `COMPLETE` | Stage updating, external portal reference linking, and status badge styling. |
| **Document Checklist** | `COMPLETE` | Metadata readiness checklist for 6 core proofs and scheme-specific documents (zero file upload). |
| **Notification System** | `COMPLETE` | In-app alerts, unread badges, mark-read actions, type-to-icon mapping (no external SMS push yet). |
| **Professional PNG Icon Set** | `COMPLETE` | 10 custom 3D matte cloud-blue PNG icons migrated; **0 emojis remaining across all templates**. |
| **AI Assistant UI** | `COMPLETE` | Responsive chat drawer/page, typing indicators, suggested questions, conversation persistence. |
| **Gemini AI / RAG Pipeline** | `PLACEHOLDER` | Assistant chat returns structured rule-based responses; pgvector and vector embeddings not started. |
| **Translations Catalog (.po/.mo)** | `PARTIAL` | `i18n_patterns` and translation tags present; translation string catalogs (.po files) not yet compiled. |
| **Production SMS Gateways** | `PARTIAL` | Provider classes written for MSG91, Twilio, Fast2SMS, and Exotel; currently using Mock provider in dev. |
| **Git Version Control** | `NOT STARTED` | Git repository not yet initialized in this directory (`fatal: not a git repository`). |
| **System Stability** | `COMPLETE` | 39/39 automated tests passing; 0 system check warnings; all HTTP endpoints return 200 OK. |

---

## 2. Repository Location

- **Canonical Absolute Path:** `C:\Users\thara\Desktop\civic_ai`
- **Operating System:** Windows 11 (64-bit)
- **Active Workspace URI:** `file:///C:/Users/thara/Desktop/civic_ai`

---

## 3. Current Architecture

```
                          ┌────────────────────────┐
                          │   Public Landing &     │
                          │   State Transition     │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │    Mobile + OTP Auth   │
                          │  (Mock / Pluggable SMS)│
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │  5-Step Profile Wizard │
                          │   (Completion Engine)  │
                          └───────────┬────────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
┌────────────────────────┐ ┌────────────────────┐ ┌──────────────────────┐
│  Deterministic Engine  │ │  Scheme Explorer   │ │  In-App Assistant    │
│  (13 Rules / DB Match) │ │  & Detail Views    │ │  (Chat UI + Mock DB) │
└────────────┬───────────┘ └──────────┬─────────┘ └──────────┬───────────┘
             │                        │                      │
             ▼                        ▼                      ▼
┌────────────────────────┐ ┌────────────────────┐ ┌──────────────────────┐
│  Personal Dashboard    │ │ Application & Doc  │ │ Notifications System │
│  (Eligible Highlights) │ │ Trackers (Ready)   │ │ (Badge Alerts)       │
└────────────────────────┘ └────────────────────┘ └──────────────────────┘
```

- **Backend Framework:** Django 6.1.1 running on Python 3.14.6.
- **REST Framework:** Django REST Framework 3.18.1 for `/api/*` endpoints.
- **Storage & Static Serving:** WhiteNoise 6.12.0 (`CompressedManifestStaticFilesStorage`).
- **Database Engine:** SQLite 3 (`db.sqlite3`) for local development; configured for PostgreSQL with psycopg2-binary for staging/production.
- **Session & Caching:** In-memory `LocMemCache` (Redis cache configured in settings, toggleable via `USE_REDIS=True`).
- **Audit Logging:** Dedicated `apps.audit` tracking auth, profile updates, and scheme interactions.

---

## 4. Directory Structure

```
C:\Users\thara\Desktop\civic_ai\
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── README.md
├── HANDOFF_TO_CODEX.md
├── db.sqlite3
│
├── config/                          # Django project configuration
│   ├── __init__.py
│   ├── settings.py                  # Modular settings (python-decouple)
│   ├── urls.py                      # Main URL dispatcher & i18n_patterns
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                            # 10 Django Local Apps
│   ├── accounts/                    # User model, OTP generation & verification
│   ├── applications_tracker/        # Application lifecycle & user notes
│   ├── assistant/                   # AI Assistant chat views & conversation models
│   ├── audit/                       # Audit logging framework
│   ├── documents/                   # Document readiness checklist (metadata only)
│   ├── eligibility/                 # Rule-based deterministic matching engine
│   ├── notifications/               # In-app notifications and preferences
│   ├── profiles/                    # UserProfile, 5-step wizard, dashboard
│   ├── schemes/                     # Schemes, versions, rules, categories
│   └── states/                      # States, districts, languages, landmarks
│
├── templates/                       # 22 Django HTML Templates
│   ├── base/
│   │   ├── base.html                # HTML5 root shell
│   │   ├── public_base.html         # Public navbar and footer
│   │   └── app_base.html            # Authenticated sidebar & mobile dock layout
│   ├── public/
│   │   └── landing.html             # Hero page, 4-step workflow, trust metrics
│   ├── states/
│   │   ├── select_state.html        # State card grid (AP, TN)
│   │   └── state_transition.html   # Animated landmark showcase & language select
│   ├── accounts/
│   │   ├── login.html               # Split-card mobile OTP request
│   │   └── verify_otp.html          # 6-digit PIN input with cooldown timer
│   ├── profiles/
│   │   ├── profile.html             # Profile summary & privacy dashboard
│   │   ├── setup_step_1.html        # Wizard 1: Personal info & gender
│   │   ├── setup_step_2.html        # Wizard 2: Location (State, District, Area)
│   │   ├── setup_step_3.html        # Wizard 3: Education & Employment
│   │   ├── setup_step_4.html        # Wizard 4: Income, Family, Social category
│   │   └── setup_step_5.html        # Wizard 5: Specialized benefits (Farmer, etc.)
│   ├── dashboard/
│   │   └── dashboard.html           # Greeting, 4 stat cards, recommendations, chat
│   ├── schemes/
│   │   ├── scheme_list.html         # Explorer, search input, category filters
│   │   └── scheme_detail.html       # Split detail, eligibility checklist, save
│   ├── assistant/
│   │   └── assistant.html           # Full-page AI advisory chat interface
│   ├── applications/
│   │   ├── list.html                # Application milestone tracker
│   │   └── detail.html              # Stage updater and official link
│   ├── documents/
│   │   └── overview.html            # Core document readiness & privacy banner
│   └── notifications/
│       └── list.html                # Alerts list & mark-all-read action
│
├── static/                          # SOURCE static assets (Version controlled)
│   ├── css/
│   │   └── civic.css                # Master CSS (Theme variables, typography, grid)
│   ├── js/
│   │   └── civic.js                 # Helper scripts & CSRF utility
│   └── images/
│       └── civic_ai/
│           ├── brand/               # Core branding (logo, mascot, hero, clouds)
│           ├── icons/               # 10 Professional 3D matte blue PNG icons
│           └── states/              # Verified state cards & transition landmarks
│
├── staticfiles/                     # COLLECTSTATIC output (Managed by WhiteNoise)
├── tests/                           # 6 Automated Test Modules (39 Tests)
│   ├── test_eligibility_engine.py
│   ├── test_full_user_journey.py
│   ├── test_optimizations_and_resilience.py
│   ├── test_otp_and_auth.py
│   ├── test_states_and_flow.py
│   └── test_ui_assets.py
│
├── locale/                          # Translation Catalogs
│   ├── en/LC_MESSAGES/
│   ├── ta/LC_MESSAGES/
│   └── te/LC_MESSAGES/
└── media/                           # User-generated / Dynamic media
```

---

## 5. Django Apps

### 1. `apps.accounts`
- **Location:** `apps/accounts/`
- **Purpose:** Handles mobile number based identity, OTP creation, dispatch, and verification.
- **Models:**
  - `User`: Inherits `AbstractBaseUser`, `PermissionsMixin`. Primary key `UUID`. Username field is `mobile_number` (E.164 normalized). Contains `preferred_language` (`en`, `ta`, `te`) and `is_profile_complete`.
  - `OTPRequest`: Stores hashed OTP codes, expiry datetime, verification status, and retry counters.
- **Services:** `apps.accounts.otp.service.OTPService` and provider factory `get_otp_provider()`.
- **Views:** `login_view`, `send_otp_view`, `verify_otp_view`, `verify_otp_submit`, `resend_otp_view`, `logout_view`.
- **REST APIs:** `/api/auth/send-otp/`, `/api/auth/verify-otp/`, `/api/auth/me/`, `/api/auth/logout/`.
- **Status:** `COMPLETE`.

### 2. `apps.profiles`
- **Location:** `apps/profiles/`
- **Purpose:** Citizen profile collection, 5-step onboarding wizard, profile completion metric, and user dashboard.
- **Models:** `UserProfile` (OneToOne with `User`). Contains 25+ structured fields including age calculation, income values, caste category, and vulnerability flags.
- **Views:** `dashboard`, `profile_setup_step`, `profile_view`.
- **Status:** `COMPLETE`.

### 3. `apps.states`
- **Location:** `apps/states/`
- **Purpose:** State jurisdiction management, localized district mappings, transition landmarks, and language switching.
- **Models:**
  - `Language`: Code, name, native_name, script, flag_emoji, is_active.
  - `State`: Code (`AP`, `TN`), name, native_name, capital, transition landmark, theme colors, and static image paths.
  - `District`: State foreign key, name, native_name, district code.
- **Management Command:** `seed_data` (populates AP and TN, 28 districts, 15 categories, 7 schemes).
- **Views:** `landing_page`, `select_state`, `set_state`, `state_transition`, `select_language`, `set_language`.
- **REST APIs:** `/api/states/`, `/api/states/languages/`.
- **Status:** `COMPLETE`.

### 4. `apps.schemes`
- **Location:** `apps/schemes/`
- **Purpose:** Government schemes registry, version tracking, eligibility rules definition, required documents, and user bookmarks.
- **Models:**
  - `SchemeCategory`: Categorization (Agriculture, Scholarships, etc.).
  - `Department`: Sponsoring state or central department.
  - `Scheme`: Parent record with government level (`central`, `state`), status (`active`), and slug.
  - `SchemeVersion`: Active scheme parameters, benefit amounts, application URLs.
  - `EligibilityRule`: Structured criteria (rule type, operator, target value, mandatory flag).
  - `RequiredDocument`: Documents checklist per scheme version.
  - `SchemeTranslation`: Localized scheme name, description, and benefits in Tamil and Telugu.
  - `UserSchemeMatch`: Persisted eligibility outcome for a user (`eligible`, `not_eligible`, `incomplete`).
  - `SavedScheme`: Bookmark model for user favorites.
- **Views:** `scheme_list`, `scheme_detail`, `save_scheme`.
- **REST APIs:** `/api/schemes/`, `/api/schemes/recommended/`, `/api/schemes/<pk>/`, `/api/schemes/<pk>/eligibility/`.
- **Status:** `COMPLETE`.

### 5. `apps.eligibility`
- **Location:** `apps/eligibility/`
- **Purpose:** Deterministic, non-LLM rule matching engine.
- **Engine File:** `apps/eligibility/engine.py`.
- **Classes:** `EligibilityEngine`, `RuleResult`, `EligibilityResult`.
- **Functions:** `evaluate(profile, scheme)`, `evaluate_and_save(user, profile, scheme)`, `run_eligibility_for_user(user)`.
- **Status:** `COMPLETE`.

### 6. `apps.assistant`
- **Location:** `apps/assistant/`
- **Purpose:** Conversational civic advisor interface.
- **Models:**
  - `AssistantConversation`: Linked to user and language.
  - `AssistantMessage`: Role (`user`, `assistant`), message text, sources.
- **Views:** `assistant_home`, `chat_view`.
- **REST APIs:** `/api/assistant/chat/` (accepts user message, returns response and sources list).
- **Status:** `PARTIAL` (UI and conversation storage complete; real Gemini LLM and RAG retrieval not connected).

### 7. `apps.notifications`
- **Location:** `apps/notifications/`
- **Purpose:** In-app notification center for scheme alerts and deadlines.
- **Models:** `Notification`, `NotificationPreference`.
- **Views:** `notifications_list`, `mark_read`, `mark_all_read`.
- **REST APIs:** `/api/notifications/`, `/api/notifications/unread-count/`.
- **Status:** `COMPLETE`.

### 8. `apps.applications_tracker`
- **Location:** `apps/applications_tracker/`
- **Purpose:** Personal application milestones and status tracking.
- **Models:** `ApplicationTracker`, `ApplicationNote`.
- **Views:** `applications_list`, `application_detail`, `add_application`, `update_status`.
- **Status:** `COMPLETE`.

### 9. `apps.documents`
- **Location:** `apps/documents/`
- **Purpose:** Privacy-preserving document readiness tracking (no file uploads).
- **Models:** `DocumentChecklist`.
- **Views:** `documents_overview`.
- **Status:** `COMPLETE`.

### 10. `apps.audit`
- **Location:** `apps/audit/`
- **Purpose:** Security and audit event logging.
- **Models:** `AuditLog`.
- **Services:** `apps.audit.services.log_audit_event`.
- **Status:** `COMPLETE`.

---

## 6. Frontend and Templates

All 22 templates reside under `templates/` and inherit from `base/base.html`, `base/public_base.html`, or `base/app_base.html`.

| Template Path | Page Description | Supplying Route | Key UI Components | Tested? |
| :--- | :--- | :--- | :--- | :--- |
| `base/base.html` | HTML5 Shell | Core layout | CSS/JS includes, flash messages, accessibility root | Yes |
| `base/public_base.html` | Public Shell | Public pages | Responsive topnav, Civic AI logo (contain), language pill, footer | Yes |
| `base/app_base.html` | App Shell | Authenticated | 260px Sidebar with 9 PNG icons, mobile bottom bar (5 PNG icons), user badge | Yes |
| `public/landing.html` | Landing Page | `/` (`home`) | Hero visual, trust badge, 4 step progression, state cards, disclaimer | Yes |
| `states/select_state.html` | State Selector | `/select-state/` | Andhra Pradesh and Tamil Nadu card grid with landmark previews | Yes |
| `states/state_transition.html` | Transition Page | `/transition/<slug>/` | Circular landmark animation, language selector button group | Yes |
| `accounts/login.html` | Login Screen | `/auth/login/` | Split 2-column card, state hero banner, phone prefix input, OTP trigger | Yes |
| `accounts/verify_otp.html` | OTP Screen | `/auth/verify/` | 6 auto-advancing digit inputs, countdown clock, resend timer | Yes |
| `profiles/setup_step_1.html` | Wizard: Personal | `/dashboard/setup/1/` | Progress bar (20%), clean SVG gender selector cards, DOB picker | Yes |
| `profiles/setup_step_2.html` | Wizard: Location | `/dashboard/setup/2/` | Progress bar (40%), dynamic state/district select, rural/urban pills | Yes |
| `profiles/setup_step_3.html` | Wizard: Education | `/dashboard/setup/3/` | Progress bar (60%), education & employment dropdowns, student toggle | Yes |
| `profiles/setup_step_4.html` | Wizard: Income | `/dashboard/setup/4/` | Progress bar (80%), income brackets, marital status, social category | Yes |
| `profiles/setup_step_5.html` | Wizard: Special | `/dashboard/setup/5/` | Progress bar (100%), 8 attribute cards with PNG icons, landholding toggle | Yes |
| `dashboard/dashboard.html` | User Dashboard | `/dashboard/` | Greeting, 4 stat cards with PNG icons, recommended scheme cards, AI chat | Yes |
| `schemes/scheme_list.html` | Scheme Explorer | `/schemes/` | Search bar with PNG icon, text category pills, scheme cards with badges | Yes |
| `schemes/scheme_detail.html` | Scheme Detail | `/schemes/<slug>/` | 2:1 Split, eligibility checklist (green/red), required documents, bookmark | Yes |
| `assistant/assistant.html` | Full Assistant | `/assistant/` | Clean suggested question pills, chat bubbles with mascot/user avatar | Yes |
| `applications/list.html` | Tracker List | `/applications/` | Application cards, status badges, official portal notice, empty state | Yes |
| `applications/detail.html` | Tracker Detail | `/applications/<pk>/` | Stage dropdown updater, official portal external button, metadata | Yes |
| `documents/overview.html` | Documents List | `/documents/` | Privacy notice banner, 6 essential document cards, scheme requirements | Yes |
| `notifications/list.html` | Notifications | `/notifications/` | Filtered notification items with semantic icons, mark-as-read buttons | Yes |
| `profiles/profile.html` | Profile View | `/dashboard/profile/` | Completion ring, 4 category cards with PNG icons, vulnerability tags | Yes |

---

## 7. UI / Design State

### Approved Visual Direction
- **Palette:** Deep civic navy (`#002060`, `#003580`), vibrant primary blue (`#1a56a4`, `#1a56db`), sky tint (`#ebf3ff`, `#f4f7fd`), crisp white (`#ffffff`).
- **Texture:** Matte/cloud finish. No harsh glassmorphism, no glossy skeuomorphism.
- **Typography:** System font stack (`system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif`) with strict hierarchy (`2.25rem` titles down to `0.85rem` hints).
- **Accessibility:** Touch target minimum `44px` on all interactives; high-contrast borders (`#e2e8f0`); visible `:focus` rings.
- **Cards & Containers:** `border-radius: 12px` to `16px`; soft diffused shadows (`0 2px 8px rgba(0,0,0,0.06)`).

### Logo Display Standards
The brand logo (`static/images/civic_ai/brand/logo.png`) is a 3:1 horizontal emblem (2172x724 px) containing both the emblem and the "Civic AI" wordmark:
- **Rule:** Always rendered with `height: 34px-38px; width: auto; max-width: 180px; object-fit: contain; display: block;`.
- **Rule:** Never pair with separate duplicate `Civic AI` HTML text in the same header element, which previously caused text clipping or duplicate branding.

---

## 8. Images and Static Assets

All canonical source image assets reside in `static/images/civic_ai/`:

| File Name | Exact Disk Path | Purpose / Aspect Ratio | Currently Used? | Referenced In Template / CSS |
| :--- | :--- | :--- | :--- | :--- |
| `logo.png` | `static/images/civic_ai/brand/logo.png` | Master 3:1 horizontal brandmark | **YES** | `app_base.html`, `public_base.html`, `login.html`, `setup_step_*.html` |
| `mascot.png` | `static/images/civic_ai/brand/mascot.png` | Friendly 3D cloud-blue robot mascot | **YES** | `dashboard.html`, `assistant.html`, `scheme_detail.html` |
| `hero_family.png` | `static/images/civic_ai/brand/hero_family.png` | Indian multi-gen family at civic center | **YES** | `landing.html`, `login.html` (fallback) |
| `cloud_bg.png` | `static/images/civic_ai/brand/cloud_bg.png` | Subtle matte cloud background texture | **YES** | `civic.css`, `landing.html`, `select_state.html`, `login.html` |
| `ap_state.png` | `static/images/civic_ai/states/ap_state.png` | Amaravati capital & temple panorama | **YES** | `landing.html`, `select_state.html` |
| `tn_state.png` | `static/images/civic_ai/states/tn_state.png` | Meenakshi / Shore temple heritage card | **YES** | `landing.html`, `select_state.html` |
| `ap_transition.png`| `static/images/civic_ai/states/ap_transition.png`| Tirumala hillscape panorama | **YES** | `state_transition.html` (Andhra Pradesh) |
| `tn_transition.png`| `static/images/civic_ai/states/tn_transition.png`| Thanjavur Brihadisvara landmark | **YES** | `state_transition.html` (Tamil Nadu) |
| `ap_login.png` | `static/images/civic_ai/states/ap_login.png` | AP citizen family beneath temple sky | **YES** | `login.html` (When AP selected) |
| `tn_login.png` | `static/images/civic_ai/states/tn_login.png` | TN citizen family beside temple pond | **YES** | `login.html` (When TN selected) |

*Note:* Identical mirror copies are maintained in `staticfiles/` as generated by `manage.py collectstatic`.

---

## 9. Professional Icon Migration

### Semantic Mapping & File Verification
The 10 icons in `static/images/civic_ai/icons/` have been verified on disk:

```
C:\Users\thara\Desktop\civic_ai\static\images\civic_ai\icons\
├── icon_dashboard.png         # 739 KB - Dashboard & System Overview
├── icon_my_schemes.png        # 615 KB - Matched Eligibility & Trust Badges
├── icon_explore_schemes.png   # 605 KB - Browse Schemes & Discovery
├── icon_ai_assistant.png      # 826 KB - Civic AI Assistant Mascot / Dialog
├── icon_applications.png      # 814 KB - Application Tracker & Procedures
├── icon_documents.png         # 675 KB - Document Checklist & Identity Cards
├── icon_notifications.png     # 763 KB - Alerts, Badges & Updates
├── icon_profile.png           # 693 KB - Citizen Profile & Account Details
├── icon_help_support.png      # 593 KB - Help Center & Guidance
└── icon_information.png       # 866 KB - Legal Disclaimers & Notices
```

### Migration Status
- **Emoji Replacement Completion:** **100% COMPLETE**.
- **Remaining Emojis in Templates:** **0**. An automated recursive Unicode scan confirms zero emoji characters in all 22 templates.
- **Render Specifications:**
  - Sidebar icons: `.nav-icon` = `26px × 26px` with `object-fit: contain;`.
  - Mobile bottom navigation: `.icon` = `22px × 22px`.
  - Page header banners: `40px × 40px`.
  - Dashboard stat cards: `28px × 28px` centered in `52px` rounded tinted containers.
  - Empty states: `56px × 56px`.
  - Badges & pills: Text-only (all emoji prefixes removed).
  - Gender options: Accessible vector SVGs.

---

## 10. URL Routing

### Configuration Details
- `ROOT_URLCONF`: `config.urls`
- `i18n_patterns` with `prefix_default_language=False`:
  - English (`en`) routes have **no prefix** (e.g. `/`, `/select-state/`, `/schemes/`, `/dashboard/`).
  - Tamil (`ta`) routes are accessed at `/ta/...`.
  - Telugu (`te`) routes are accessed at `/te/...`.
- `path('', landing_page, name='root_landing')` guarantees that `/` always returns `200 OK` regardless of browser locale negotiation.

### Master Route Table

| URL Pattern | View Function | Namespace / Name | Auth Required? | Verified HTTP Status |
| :--- | :--- | :--- | :--- | :--- |
| `/` | `apps.states.views.landing_page` | `root_landing` / `home` | Public | **200 OK** |
| `/select-state/` | `apps.states.views.select_state` | `states:select_state` | Public | **200 OK** |
| `/set-state/` | `apps.states.views.set_state` | `states:set_state` | Public (POST) | **302 Redirect** |
| `/transition/<slug>/` | `apps.states.views.state_transition` | `states:state_transition` | Public | **200 OK** |
| `/select-language/` | `apps.states.views.select_language` | `states:select_language` | Public | **200 OK** |
| `/set-language/` | `apps.states.views.set_language` | `states:set_language` | Public (POST) | **302 Redirect** |
| `/auth/login/` | `apps.accounts.views.login_view` | `accounts:login` | Public | **200 OK** |
| `/auth/send-otp/` | `apps.accounts.views.send_otp_view` | `accounts:send_otp` | Public (POST) | **302 / 200** |
| `/auth/verify/` | `apps.accounts.views.verify_otp_view`| `accounts:verify_otp` | Session OTP | **200 OK** |
| `/auth/verify/submit/` | `apps.accounts.views.verify_otp_submit` | `accounts:verify_otp_submit` | Public (POST) | **302 / 200** |
| `/auth/resend-otp/` | `apps.accounts.views.resend_otp_view` | `accounts:resend_otp` | Public (POST) | **200 JSON** |
| `/auth/logout/` | `apps.accounts.views.logout_view` | `accounts:logout` | Public | **302 Redirect** |
| `/dashboard/` | `apps.profiles.views.dashboard` | `dashboard:home` | **Login Required** | **200 OK** |
| `/dashboard/profile/` | `apps.profiles.views.profile_view` | `dashboard:profile` | **Login Required** | **200 OK** |
| `/dashboard/setup/<step>/`| `apps.profiles.views.profile_setup_step`| `dashboard:profile_setup_step`| **Login Required** | **200 OK** |
| `/schemes/` | `apps.schemes.views.scheme_list` | `schemes:list` | Public/Auth | **200 OK** |
| `/schemes/<slug>/` | `apps.schemes.views.scheme_detail` | `schemes:detail` | Public/Auth | **200 OK** |
| `/schemes/<slug>/save/` | `apps.schemes.views.save_scheme` | `schemes:save` | **Login Required** | **302 Redirect** |
| `/assistant/` | `apps.assistant.views.assistant_home` | `assistant:home` | **Login Required** | **200 OK** |
| `/applications/` | `apps.applications_tracker.views.applications_list`| `applications:list` | **Login Required** | **200 OK** |
| `/applications/<pk>/` | `apps.applications_tracker.views.application_detail`| `applications:detail` | **Login Required** | **200 OK** |
| `/applications/<pk>/update/`| `apps.applications_tracker.views.update_status`| `applications:update_status`| **Login Required** | **302 Redirect** |
| `/documents/` | `apps.documents.views.documents_overview` | `documents:overview` | **Login Required** | **200 OK** |
| `/notifications/` | `apps.notifications.views.notifications_list` | `notifications:list` | **Login Required** | **200 OK** |
| `/api/auth/send-otp/` | `apps.accounts.api_views.SendOTPView` | `api_auth:send_otp` | API | **200 JSON** |
| `/api/auth/verify-otp/`| `apps.accounts.api_views.VerifyOTPView`| `api_auth:verify_otp` | API | **200 JSON** |
| `/api/states/` | `apps.states.views.states_api` | `api_states:list` | API | **200 JSON** |
| `/api/schemes/` | `apps.schemes.api_views.SchemeListView`| `api_schemes:list` | API | **200 JSON** |
| `/api/assistant/chat/` | `apps.assistant.api_views.ChatAPIView` | `api_assistant:chat` | Auth API | **200 JSON** |

---

## 11. i18n and Languages

- **Supported Languages:** English (`en`), Tamil (`ta`), Telugu (`te`).
- **Middleware Chain:**
  - `django.middleware.locale.LocaleMiddleware` (handles standard session/cookie language resolution).
  - `apps.accounts.middleware.UserLanguageMiddleware` (synchronizes authenticated user's `preferred_language` with Django's active translation context).
- **Template Status:** All user-facing strings are wrapped with `{% trans "..." %}` or `{% blocktrans %}`.
- **Catalog Status:** Directory structures exist (`locale/en/LC_MESSAGES/`, `locale/ta/LC_MESSAGES/`, `locale/te/LC_MESSAGES/`). Compiled `.po` and `.mo` message files have not been generated yet. Running `makemessages` and translating strings remains a Phase 2 task.

---

## 12. Authentication and OTP

### Architecture
- **Model:** `apps.accounts.models.User` (mobile number based authentication, no passwords).
- **Format:** E.164 phone numbers (Indian mobile numbers normalized to `+91XXXXXXXXXX`).
- **Storage:** `OTPRequest` stores a SHA-256 hash salted with `settings.SECRET_KEY[:16]`. Plaintext OTPs are never stored in the database.
- **Expiry:** Configured via `OTP_EXPIRY_SECONDS` (default: 300 seconds / 5 minutes).
- **Security Limits:** `OTP_MAX_ATTEMPTS = 5`, `OTP_RESEND_COOLDOWN_SECONDS = 60`.

### Provider Implementation Status
- **Active Dev Provider:** `MockOTPProvider` (`apps/accounts/otp/providers.py`).
  - Dispatches mock OTP to logger and stdout.
  - Accepts fixed test OTP `123456` in development mode for seamless test automation.
- **Production Provider Stubs (Code Implemented, Requires API Keys):**
  - `MSG91OTPProvider` (uses `httpx` against `https://api.msg91.com/api/v5/otp`).
  - `TwilioOTPProvider` (uses `httpx` against Twilio Messages API).
  - `Fast2SMSOTPProvider` (uses `httpx` against Fast2SMS Bulk V2).
  - `ExotelOTPProvider` (uses `httpx` against Exotel SMS API).

---

## 13. User Profile

### Fields in `UserProfile` (`apps/profiles/models.py`)
1. **Identity & Age:** `date_of_birth` (Date), `age` (PositiveSmallInteger, auto-calculated), `gender` (`male`, `female`, `other`, `prefer_not_to_say`).
2. **Location:** `state` (FK `State`), `district` (FK `District`), `city_village` (Char), `pin_code` (Char), `is_rural` (Boolean).
3. **Education:** `education_level` (9 choices: `no_formal` to `doctorate`), `is_student` (Boolean), `student_course` (Char), `institution_type` (Char).
4. **Employment:** `employment_status` (8 choices: `employed`, `self_employed`, `unemployed`, `student`, `homemaker`, `retired`, `farmer`, `daily_wage`), `occupation` (Char), `sector` (Char).
5. **Financial & Family:** `individual_income_range` (6 ranges), `family_income_range` (6 ranges), `marital_status` (5 choices), `number_of_dependents` (Integer).
6. **Social Category:** `category` (`general`, `obc`, `sc`, `st`, `ews`).
7. **Special Eligibility Attributes:** `is_farmer` (Boolean), `land_holding` (`landless`, `marginal`, `small`, `medium`, `large`), `has_disability` (Boolean), `disability_type` (Char), `is_senior_citizen` (Boolean), `is_widow` (Boolean), `is_shg_member` (Boolean), `is_ration_card_holder` (Boolean), `ration_card_type` (Char), `is_entrepreneur` (Boolean), `is_job_seeker` (Boolean).

### 5-Step Setup Wizard
- **Step 1 (`/dashboard/setup/1/`):** Full name, DOB, gender cards, language preference.
- **Step 2 (`/dashboard/setup/2/`):** State, District, City/Village, PIN code, Rural/Urban.
- **Step 3 (`/dashboard/setup/3/`):** Education level, employment status, occupation, student toggle.
- **Step 4 (`/dashboard/setup/4/`):** Annual income, family income, marital status, dependents, social category.
- **Step 5 (`/dashboard/setup/5/`):** 8 Special scheme toggle cards (Farmer, Disability, Senior, Widow, SHG, Job Seeker, Entrepreneur, Ration Card) and landholding selector.
- **Completion Formula:** Evaluates 11 key fields; triggers synchronous/asynchronous eligibility engine evaluation on completion.

---

## 14. Scheme System

### Data Structure
- `Scheme` acts as the persistent entity (`level`, `status`, `slug`, `state`, `department`).
- `SchemeVersion` acts as the point-in-time configuration holding the benefit description, application URL, and eligibility criteria rules.
- `EligibilityRule` holds discrete conditions.

### Seeded Sample Schemes
7 verified schemes are seeded in `db.sqlite3`:
1. **PM Employment Generation Programme (PMEGP):** Central | Employment & Skills.
2. **PM Scholarship Scheme for Ex-Servicemen:** Central | Scholarships.
3. **Tamil Nadu Chief Minister's Kisan Scheme:** State (Tamil Nadu) | Agriculture & Farmers.
4. **Kalaignar Magalir Urimai Scheme (TN):** State (Tamil Nadu) | Women Welfare & Basic Income.
5. **YSR Pension Kanuka:** State (Andhra Pradesh) | Social Security & Pensions.
6. **Amma Vodi Scheme (AP):** State (Andhra Pradesh) | Education & Schooling Assistance.
7. **Dr. YSR Rythu Bharosa PM-KISAN:** State (Andhra Pradesh) | Agriculture & Farmer Subsidy.

---

## 15. Eligibility Engine

### Core Principles
- **Location:** `apps/eligibility/engine.py`.
- **Absolute Rule:** The engine is **100% deterministic code**. LLMs / Generative AI are **forbidden** from making eligibility determinations to prevent hallucinations.
- **Outcome States:**
  - `eligible`: All mandatory rules passed.
  - `not_eligible`: One or more mandatory rules failed.
  - `incomplete`: Missing mandatory user profile fields prevent conclusive determination.

### Supported Rule Criteria
- `age`: Min/Max age limits (with DOB auto-fallback calculation).
- `state`: State jurisdiction match (central schemes match all states).
- `district`: Localized district restriction.
- `income`: Individual and family income range ceiling comparisons.
- `education`: Ordered comparisons (`EDUCATION_ORDER` numeric hierarchy).
- `employment`: Employment status matching.
- `student`: Student status verification.
- `farmer`: Agricultural worker check and landholding category.
- `gender`: Gender-specific programs.
- `category`: Social category reservations (SC, ST, OBC, EWS).
- `disability`: Recognized disability status.
- `senior_citizen`: Age 60+ benefits.
- `widow`: Widow status.
- `shg_member`: Self-Help Group membership.

---

## 16. Applications

- **Model:** `apps.applications_tracker.models.ApplicationTracker`.
- **Status Choices:** `draft`, `submitted`, `under_verification`, `action_required`, `approved`, `rejected`, `completed`.
- **Functionality:** Allows citizens to bookmark schemes they intend to apply for, record application submission dates and reference numbers, and link directly to official state portals.

---

## 17. Documents

- **Model:** `apps.documents.models.DocumentChecklist`.
- **Privacy Architecture:** **Zero File Uploads.** In accordance with privacy-by-design standards, Civic AI stores only metadata flags (`available`, `missing`, `expired`) and notes. Physical certificates and Aadhaar numbers are never uploaded to the server.

---

## 18. Notifications

- **Model:** `apps.notifications.models.Notification`.
- **Notification Types:** `new_scheme`, `eligibility_changed`, `deadline`, `document_required`, `application_update`, `system`.
- **UI:** Dropdown counter badge on sidebar, dedicated notification page with mark-all-read and individual read states, semantic icon mapping.

---

## 19. AI Assistant

- **Status:** **Frontend Complete, Backend Mocked**.
- **Model:** `apps.assistant.models.AssistantConversation`, `AssistantMessage`.
- **Endpoint:** `POST /api/assistant/chat/`.
- **Current Behavior:** Stores conversation history in the database; returns structured rule-based responses for eligibility, document, and application queries; includes latency spinner and speech-bubble UI.
- **Target:** Connect to Google Gemini API via `google-generativeai` in Phase 3.

---

## 20. RAG Status

- **Status:** **NOT STARTED**.
- **pgvector:** Listed in `requirements.txt` (`pgvector==0.3.6`), but vector tables, chunking pipelines, and vector embeddings have not been created.
- **Current Retrieval:** Database queries (`UserSchemeMatch`, `SchemeVersion`, `RequiredDocument`) provide all structured context.

---

## 21. Database

- **Current Engine:** SQLite 3 (`db.sqlite3`, 585 KB).
- **PostgreSQL Readiness:** Toggleable via `USE_SQLITE=False` in `.env`.
- **Applied Migrations:** All 10 apps have active initial migrations cleanly executed.

---

## 22. Seed Data

- **Command:** `python manage.py seed_data`.
- **Location:** `apps/states/management/commands/seed_data.py`.
- **Seeded Entities:**
  - 3 Languages: English (`en`), Tamil (`ta`), Telugu (`te`).
  - 2 States: Andhra Pradesh (`AP`), Tamil Nadu (`TN`).
  - 28 Districts: 13 for AP, 15 for TN.
  - 15 Scheme Categories.
  - 7 Schemes with active versions, required documents, and eligibility rules.

---

## 23. Tests

The automated test suite contains **39 tests across 6 modules**:

```powershell
& "C:\Users\thara\AppData\Local\Python\pythoncore-3.14-64\python.exe" manage.py test tests
```

### Execution Log:
```
Creating test database for alias 'default'...
.......................................
----------------------------------------------------------------------
Ran 39 tests in 0.568s

OK
Destroying test database for alias 'default'...
Found 39 test(s).
System check identified no issues (0 silenced).
```

### Module Breakdown:
1. `tests/test_eligibility_engine.py` (9 tests): Evaluates mandatory rules, missing fields, age calculation, education ranking, and batch runs.
2. `tests/test_full_user_journey.py` (1 test): Complete end-to-end integration test from public landing, OTP auth, wizard steps 1–5, to dashboard recommendations.
3. `tests/test_optimizations_and_resilience.py` (9 tests): Rate limiting, HTTP method restrictions, audit logging, invalid UUID exception safety.
4. `tests/test_otp_and_auth.py` (7 tests): Mock OTP verification, attempt limits, cooldown headers, session establishment.
5. `tests/test_states_and_flow.py` (5 tests): State selection, landmark transitions, language context switching, REST APIs.
6. `tests/test_ui_assets.py` (8 tests): File presence on disk, image paths in models, template rendering without missing assets.

---

## 24. Static Files

- `STATIC_URL = '/static/'`
- `STATICFILES_DIRS = [BASE_DIR / 'static']` (Source assets)
- `STATIC_ROOT = BASE_DIR / 'staticfiles'` (Collectstatic target)
- `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`
- `manage.py collectstatic --noinput` copies 199 files with manifest hashing cleanly.

---

## 25. Environment

- **Python Version:** 3.14.6 (64-bit)
- **Python Binary:** `C:\Users\thara\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- **Django Version:** 6.1.1
- **Installed Packages:** `django`, `djangorestframework`, `whitenoise`, `pillow`, `psycopg2-binary`, `google-generativeai`, `httpx`, `python-decouple`, `celery`, `redis`.

### Environment Variable Names (`.env`):
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `USE_SQLITE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `USE_REDIS`, `REDIS_URL`, `CELERY_BROKER_URL`
- `OTP_PROVIDER`, `OTP_EXPIRY_SECONDS`, `OTP_MAX_ATTEMPTS`, `OTP_RESEND_COOLDOWN_SECONDS`
- `MSG91_AUTH_KEY`, `MSG91_SENDER_ID`, `MSG91_TEMPLATE_ID`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
- `FAST2SMS_API_KEY`, `EXOTEL_ACCOUNT_SID`, `EXOTEL_API_KEY`, `EXOTEL_API_TOKEN`
- `GOOGLE_API_KEY`, `GOOGLE_AI_MODEL`, `AI_PROVIDER`

---

## 26. Git / Changed Files

- **Git Repository Status:** Git is **not currently initialized** in `C:\Users\thara\Desktop\civic_ai`.
- **Recommendation for Codex:** Initialize Git repository and create initial baseline commit before proceeding:
  ```powershell
  git init
  git add .
  git commit -m "feat: complete Phase 1 Civic AI prototype with professional icon set"
  ```

---

## 27. Known Issues & Technical Limitations

1. **Translation Catalogs Uncompiled:** `locale/ta/` and `locale/te/` folders exist, but `.po` and `.mo` files are not generated. UI displays English fallbacks for translated strings.
2. **AI Assistant is Mocked:** `/api/assistant/chat/` generates hardcoded rule-based advice instead of invoking Google Gemini.
3. **RAG Pipeline Not Started:** Vector search, embeddings, and scheme PDF ingestion are not yet implemented.
4. **Dev OTP In Use:** Currently running `MockOTPProvider` (fixed code `123456`). Real SMS gateway credentials need to be configured for live SMS dispatch.
5. **No File Uploads in Documents:** By design, but citizens cannot attach PDF receipts to their application milestones.

---

## 28. Remaining Work

1. **Phase 2 — Scheme Content & Language Expansion:**
   - Ingest 50+ real schemes for Andhra Pradesh and Tamil Nadu.
   - Run `python manage.py makemessages -l ta` and `-l te`, populate translations, and compile.
   - Expand to Telangana, Karnataka, and Kerala.
2. **Phase 3 — Gemini AI & RAG Engine:**
   - Configure `google-generativeai` with `GOOGLE_API_KEY`.
   - Setup pgvector / vector store with government scheme guidelines.
   - Implement source-attributed Q&A grounded in official scheme rules.
3. **Phase 4 — Production Hardening:**
   - Activate live SMS provider (MSG91 or Exotel).
   - Switch from SQLite to PostgreSQL with connection pooling.
   - Enable Redis for Celery and session caching.

---

## 29. Priority Backlog

- **P0 (Critical / Next Immediate Step):**
  - Initialize Git repo and commit baseline.
  - Compile Tamil (`ta`) and Telugu (`te`) `.po` catalogs for onboarding pages.
- **P1 (Important / Core Value):**
  - Connect Gemini 1.5 Flash in `apps/assistant/api_views.py` using `GOOGLE_API_KEY`.
  - Add more real government schemes to `apps/states/management/commands/seed_data.py`.
- **P2 (Enhancement):**
  - Implement PDF export of matched eligibility summary for citizens.
  - Setup Celery background task for nightly eligibility re-evaluations.
- **P3 (Future Expansion):**
  - Add WhatsApp Bot integration using the same `/api/*` endpoints.
  - Add DigiLocker integration for automated document verification.

---

## 30. Codex — Start Here

Welcome Codex! Here is your exact checklist to resume development seamlessly:

1. **Verify Environment:**
   ```powershell
   $python = "C:\Users\thara\AppData\Local\Python\pythoncore-3.14-64\python.exe"
   Set-Location "C:\Users\thara\Desktop\civic_ai"
   & $python manage.py check
   & $python manage.py test tests
   ```
2. **Initialize Git (if you want version tracking):**
   ```powershell
   git init
   git add .
   git commit -m "feat: Civic AI verified baseline with professional icons"
   ```
3. **First Files to Inspect:**
   - `apps/assistant/api_views.py`: Where Gemini integration should replace the mock generator.
   - `apps/eligibility/engine.py`: Where deterministic matching rules are maintained.
   - `apps/states/management/commands/seed_data.py`: Where schemes and criteria are seeded.
4. **Login Dev Credentials:**
   - Navigate to `/auth/login/`.
   - Enter any 10-digit mobile number (e.g. `9876543210`).
   - On the OTP screen, enter fixed test code: `123456`.

---

## 31. Useful Commands

```powershell
# Define python path shortcut
$python = "C:\Users\thara\AppData\Local\Python\pythoncore-3.14-64\python.exe"

# Navigate to project
Set-Location "C:\Users\thara\Desktop\civic_ai"

# Run system check
& $python manage.py check

# Run full test suite (39 tests)
& $python manage.py test tests

# Check migration status
& $python manage.py showmigrations

# Apply new migrations if models change
& $python manage.py makemigrations
& $python manage.py migrate

# Re-seed database
& $python manage.py seed_data

# Collect static files
& $python manage.py collectstatic --noinput

# Start development server
& $python manage.py runserver 127.0.0.1:8000
```

---

## 32. Verification Results

All tests and endpoints were verified live during this handoff generation:
- **System Check:** `0 issues identified (0 silenced)`.
- **Test Suite:** `Ran 39 tests in 0.568s, OK`.
- **Static Assets:** `199 static files copied/unmodified in staticfiles/`.
- **HTTP Smoke Tests (200 OK):**
  - `GET /` -> `200`
  - `GET /select-state/` -> `200`
  - `GET /auth/login/` -> `200`
  - `GET /schemes/` -> `200`
  - `GET /dashboard/` -> `200`
  - `GET /dashboard/profile/` -> `200`
  - `GET /assistant/` -> `200`
  - `GET /applications/` -> `200`
  - `GET /documents/` -> `200`
  - `GET /notifications/` -> `200`
  - `GET /dashboard/setup/1/` through `5/` -> `200`
  - `GET /ta/` & `GET /te/` -> `200`
