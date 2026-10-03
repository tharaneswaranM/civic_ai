# Civic AI: Government Scheme & Legal Rights Discovery Platform

**Civic AI** is an AI-powered intelligent civic assistance web platform that flips the traditional government portal paradigm:
> **Citizen Profile → Eligibility Analysis → Recommended Schemes & Rights → Guided Application**

---

## 🏛️ Key Architectural Highlights

1. **Deterministic Eligibility Engine** (`apps/eligibility/engine.py`):
   - Rule evaluation is 100% deterministic (never delegated to non-deterministic LLMs).
   - Structured rules (age, state, income, education hierarchy, occupation, farmer, disability, widow, category).
   - The AI Assistant only translates and explains results computed by the engine.

2. **Data-Driven Multi-State System** (`apps/states/`):
   - Adding new states (beyond AP and TN) requires zero code changes — simply insert rows into `State` and `Language`.
   - Dynamic state transitions, landmarks, hero imagery, and brand colors live in the database.

3. **Pluggable SMS/OTP Abstraction** (`apps/accounts/otp/`):
   - Pluggable provider architecture (`BaseOTPProvider`).
   - Built-in providers: `MockOTPProvider`, `MSG91OTPProvider`, `TwilioOTPProvider`, `Fast2SMSOTPProvider`, `ExotelOTPProvider`.
   - Security: SHA-256 hashed OTPs with expiry, rate limiting, and maximum attempt controls.
   - Fixed dev test OTP `123456` enabled in mock mode.

4. **Matte Cloud UI Design System** (`static/css/civic.css`):
   - Clean Indian government aesthetic (Deep Blue `#1a56a4`, Soft Cloud `#f4f7fd`, Forest Green `#1a9b52`).
   - Accessible touch targets (minimum 44px), high-contrast readability, responsive sidebar + mobile bottom nav.

---

## 🚀 Quick Setup & Run Instructions

### 1. Environment Requirements
- **Python**: 3.14+ (Executable: `C:\Users\thara\AppData\Local\Python\pythoncore-3.14-64\python.exe`)
- **Database**: SQLite (default for development: `USE_SQLITE=True`)

### 2. Apply Migrations
```powershell
$python = "C:\Users\thara\AppData\Local\Python\pythoncore-3.14-64\python.exe"
& $python manage.py migrate
```

### 3. Seed Initial Master Data
Loads AP & TN master records, English/Telugu/Tamil language packs, districts, categories, and 7 verified initial schemes with complete eligibility rules:
```powershell
& $python manage.py seed_data
```

### 4. Default Credentials & Testing Codes
- **Superuser Admin**:
  - URL: `http://localhost:8000/admin/`
  - Mobile: `+919999999999`
  - Password: `admin123`
- **Mobile OTP Login**:
  - Any 10-digit number (e.g. `9876543210`)
  - Fixed Dev OTP: `123456` (or read generated OTP from terminal output)

### 5. Start Development Server
```powershell
& $python manage.py runserver 8000
```
Visit: [http://localhost:8000/](http://localhost:8000/)

---

## 🧪 Automated Test Suite

Civic AI includes automated unit and end-to-end integration tests:
```powershell
& $python manage.py test tests
```
Tested capabilities:
- OTP generation, rate limiting, hashing & validation
- Deterministic eligibility evaluation (age limits, income thresholds, education rank, boolean attributes)
- State and language selection flows
- Complete 5-step citizen profile wizard
- Scheme bookmarking, application milestone tracking, and AI Assistant queries

---

## 📂 Core Apps Directory Structure
```
civic_ai/
├── apps/
│   ├── accounts/             # Custom UUID User model, OTPRequest, pluggable OTP providers
│   ├── states/               # State, District, Language, transition metadata & views
│   ├── profiles/             # UserProfile (comprehensive eligibility attributes & wizard)
│   ├── schemes/              # Scheme, SchemeVersion, EligibilityRule, RequiredDocument, UserSchemeMatch
│   ├── eligibility/          # Deterministic EligibilityEngine and batch re-evaluation
│   ├── assistant/            # Civic AI Assistant chat views & conversation models
│   ├── notifications/        # User notifications & alert preferences
│   ├── applications_tracker/ # Citizen personal application status tracker
│   ├── documents/            # Privacy-first document readiness checklist
│   └── audit/                # Security and access audit logging
├── static/
│   ├── css/civic.css         # Matte cloud design system stylesheet
│   └── images/               # Logos and icons
├── templates/
│   ├── base/                 # App shell, top navigation, sidebar, mobile nav
│   ├── public/               # Public landing page
│   ├── states/               # State selection & transition animation
│   ├── accounts/             # Mobile login & OTP verification
│   ├── profiles/             # 5-step profile wizard & citizen profile view
│   ├── dashboard/            # Citizen dashboard with personalized recommendations
│   ├── schemes/              # Scheme explorer & detailed rule match breakdown
│   ├── assistant/            # Interactive AI Assistant interface
│   ├── notifications/        # Notifications list
│   ├── applications/         # Personal application tracker
│   └── documents/            # Document readiness overview
└── tests/                    # Comprehensive unit and integration test suite
```
