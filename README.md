# Dhvaani (ध्वनि / ध्वनि / தொனி)

> **Multilingual Voice-First Government Services & Civic Grievance Assistant**  
> *Bridging Indian Citizens to Verified Public Schemes and Legitimate Grievance Portals.*

---

## 1. Problem Statement

Millions of Indian citizens—especially farmers, senior citizens, rural women, and daily-wage laborers—face steep digital barriers when accessing public schemes or lodging civic grievances:
- Complex English/Hindi-heavy bureaucratic portals with dense terminology.
- Lack of keyboard literacy or familiarity with complex dropdown forms.
- Misinformation from unverified third-party blogs regarding eligibility and benefits.
- Simulated or mock civic apps that misleadingly tell users "Your complaint has been submitted to the Government" when no actual government system accepted the request.

---

## 2. The Dhvaani Solution

Dhvaani is a truthful, voice-first public service layer:
1. **Multilingual Voice Interface**: Citizens speak naturally in **Tamil (தமிழ்)**, **Hindi (हिंदी)**, or **English**.
2. **AI Understanding + Verified Data**: Gemini 1.5 Flash extracts user context (occupation, age, location, issue urgency), while **100% of scheme facts, criteria, and benefits are strictly resolved from an authoritative verified service database**.
3. **Structured Grievance Assistant**: Extracts issue category, duration, priority, and location, letting the citizen review and edit their complaint before any confirmation.
4. **Assisted Official Portal Handoff**: Because official Indian civic portals (CPGRAMS, TANGEDCO, GCC 1913, TNPDS, Police CCTNS) legally require citizen authentication (OTP / Aadhaar / CAPTCHA), Dhvaani truthfully formats the complaint, provides a one-click copy button, and opens the official government portal.
5. **Dual-ID Transparency**: Separates internal **Dhvaani Request IDs** (`DHV-YYYYMMDD-XXXXXX`) from authentic **Government Reference IDs**.
6. **SQLite Persistence**: Request records survive server restarts.

---

## 3. Architecture

```text
               ┌────────────────────────────────────────────────────────┐
               │              Citizen Speech / Text Input               │
               │            (Tamil, Hindi, or English)                  │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │           Browser Web Speech STT / Web Audio           │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │         FastAPI Backend (main.py / Python 3.13)        │
               │   • Language Detection & Rich Intent Classifier        │
               │   • Fallback Heuristics for Zero-Downtime Operation    │
               └─────────────┬───────────────────────────┬──────────────┘
                             │                           │
            Scheme Intent    │                           │  Grievance Intent
                             ▼                           ▼
        ┌───────────────────────────────┐   ┌───────────────────────────────┐
        │   Context-Aware Matcher       │   │  Civic Grievance Extractor    │
        │   • Occupation/Age/Need Match │   │  • Issue, Priority, Location  │
        │   • Multi-signal Scoring      │   │  • Guided Review & Edit       │
        └──────────────┬────────────────┘   └──────────────┬────────────────┘
                       │                                   │
                       ▼                                   ▼
        ┌───────────────────────────────┐   ┌───────────────────────────────┐
        │  Verified Service Database    │   │  Verified Service Catalog     │
        │  (schemes_db.py)              │   │  (services_catalog.py)        │
        │  12 Verified Schemes          │   │  8 Civic Departments          │
        │  (pmkisan, pmjay, pmuy, etc.) │   │  (Electricity, Roads, Water)  │
        └──────────────┬────────────────┘   └──────────────┬────────────────┘
                       │                                   │
                       ▼                                   ▼
        ┌───────────────────────────────┐   ┌───────────────────────────────┐
        │   Official Scheme Guidance    │   │  Assisted Official Handoff    │
        │   • Verified Criteria & Docs  │   │  • Clean Copyable Complaint   │
        │   • Official Portal Link ↗    │   │  • Official Portal Handoff ↗  │
        │   • Native TTS Response       │   │  • Government Reference Link  │
        └───────────────────────────────┘   └──────────────┬────────────────┘
                                                           │
                                                           ▼
                                            ┌───────────────────────────────┐
                                            │  SQLite Persistence (db.py)   │
                                            │  • dhvaani_request_id (DHV-*) │
                                            │  • government_reference_id    │
                                            │  • Survives Server Restarts   │
                                            └───────────────────────────────┘
```

---

## 4. Supported Languages

| Language | Voice Input | AI Context Understanding | Official Scheme Output | Voice Synthesis (TTS) |
| :--- | :--- | :--- | :--- | :--- |
| **English** | Native Browser SpeechRecognition | Complete context extraction | Yes (Verified records) | Native `en-IN` / `en` |
| **தமிழ் (Tamil)** | Native Browser SpeechRecognition | Complete context extraction | Yes (Tamil scheme names & details) | Native `ta-IN` |
| **हिंदी (Hindi)** | Native Browser SpeechRecognition | Complete context extraction | Yes (Hindi scheme names & details) | Native `hi-IN` |

---

## 5. Verified Service Catalog

### A. 12 Government Schemes

All 12 schemes have been checked and verified against official government portals:

| Scheme ID | Official Name | Category | Jurisdiction | Official Source | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `pm_kisan` | Pradhan Mantri Kisan Samman Nidhi | Agriculture | India | `https://pmkisan.gov.in` | **Verified** |
| `ayushman_bharat` | Ayushman Bharat – PMJAY | Health | India | `https://pmjay.gov.in` | **Verified** |
| `pm_awas_yojana_rural`| Pradhan Mantri Awaas Yojana - Gramin | Housing | India | `https://pmayg.nic.in` | **Verified** |
| `pm_ujjwala` | Pradhan Mantri Ujjwala Yojana 2.0 | Energy | India | `https://pmuy.gov.in` | **Verified** |
| `mahatma_gandhi_nrega`| Mahatma Gandhi NREGA | Employment | India | `https://nrega.nic.in` | **Verified** |
| `pm_jan_dhan` | Pradhan Mantri Jan Dhan Yojana | Banking | India | `https://pmjdy.gov.in` | **Verified** |
| `tamilnadu_kalaignar_insurance`| Kalaignar Magalir Urimai Thittam | Welfare | Tamil Nadu | `https://kmut.tn.gov.in` | **Verified** |
| `atal_pension_yojana`| Atal Pension Yojana (APY) | Pension | India | `https://www.pfrda.org.in` | **Verified** |
| `pm_fasal_bima` | Pradhan Mantri Fasal Bima Yojana | Agriculture | India | `https://pmfby.gov.in` | **Verified** |
| `pm_scholarship` | PMSS / National Scholarship Portal | Education | India | `https://scholarships.gov.in`| **Verified** |
| `sukanya_samriddhi` | Sukanya Samriddhi Yojana | Welfare | India | `https://www.indiapost.gov.in`| **Verified** |
| `tamilnadu_chief_minister_health_insurance`| Chief Minister's Comprehensive Health Insurance (CMCHIS) | Health | Tamil Nadu | `https://www.cmchistn.com` | **Verified** |

### B. 8 Civic Grievance Departments

| Department | Authority | Official Portal | Helpline | Submission Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Electricity** | TANGEDCO / State Power Board | `https://grievances.tneb.in` | `1912` / `94987-94987` | Assisted Handoff (Requires Consumer No + OTP) |
| **Streetlight** | Greater Chennai Corporation / Urban Local Bodies | `https://www.chennaicorporation.gov.in` | `1913` / `1800-425-4788` | Assisted Handoff (Requires Ward / Landmark) |
| **Water Supply** | TWAD Board / MetroWater | `https://grievances.tn.gov.in` | `1800-425-1530` | Assisted Handoff (Requires Location / Consumer No) |
| **Roads & PWD** | Public Works Department / MoRTH | `https://pgportal.gov.in` | `1800-11-4000` | Assisted Handoff (Requires CPGRAMS login/OTP) |
| **Ration / PDS** | Food and Civil Supplies Department | `https://www.tnpds.gov.in` | `1967` / `1800-425-5901` | Assisted Handoff (Requires Smart Card + OTP) |
| **Police** | State Police Citizen Portal | `https://www.tamilnadupolice.gov.in` | `100` / `1091` / `1098` | Assisted Handoff (Requires Citizen CCTNS Login) |
| **Public Health**| Health and Family Welfare Department | `https://www.tnhealth.tn.gov.in` | `104` / `108` | Assisted Handoff (Requires PHC / Hospital info) |
| **Municipal** | Municipal Corporation / Local Body | `https://www.chennaicorporation.gov.in` | `1913` | Assisted Handoff (Requires Ward & Citizen Auth) |

---

## 6. Real Integrations vs. Portal Handoffs

### What Is Genuinely Real:
1. **Authoritative Government Verification**: Every URL, eligibility clause, helpline number, and document requirement is grounded in official government sources (`.gov.in`, `.nic.in`, `.tn.gov.in`).
2. **Real SQLite Persistence**: Grievances, drafts, and tracking numbers are stored in `dhvaani.db`. Data survives server restarts.
3. **Structured Complaint Builder**: Raw conversational voice inputs are transformed into formal complaints ready for official submission.
4. **Dual-ID Reference Separation**: Dhvaani cleanly distinguishes between:
   - `dhvaani_request_id`: Internal tracking token (`DHV-YYYYMMDD-XXXXXX`).
   - `government_reference_id`: Actual reference number returned by the government system upon citizen submission.
5. **Government Reference Linking**: Citizens can link their genuine SMS reference number back to Dhvaani for unified status tracking.
6. **Status Check & Handoff**: `GET /api/services/{service_id}/status/{government_reference_id}` routes users directly to the official government status tracking portal.

### What Remains Unavailable (Honest Limitations):
- **Direct Unauthenticated Machine Submission**: Indian government grievance portals (CPGRAMS, TANGEDCO, GCC, TNPDS) deliberately do not expose public unauthenticated REST APIs for automated complaint submission. This prevents bot spam and guarantees accountability through citizen OTP/Aadhaar authentication.
- **Private Automated Status Scraping**: We do not scrape behind CAPTCHAs or bypass citizen authentication, as doing so would violate security guidelines and terms of service.
- **Dhvaani Does Not Issue Government Approvals**: Approval, sanction, and disbursal remain the exclusive legal prerogative of the respective government authorities.

---

## 7. Technology Stack

- **Backend**: Python 3.13 + FastAPI + Uvicorn + Pydantic v2
- **Persistence**: SQLite 3 (`dhvaani.db`) with zero external service dependencies
- **Language Intelligence**: Google Gemini 1.5 Flash (via `google.generativeai`) with resilient rule-based fallbacks
- **Frontend**: Vanilla HTML5, CSS3 (Glassmorphic dark civic UI), Vanilla JavaScript (no framework overhead)
- **Speech**: Web Speech API (`SpeechRecognition` + `SpeechSynthesisUtterance`) with automatic voice matching

---

## 8. Local Setup & Running

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Modern web browser (Chrome, Edge, Safari, or Firefox)

### Installation
```bash
# 1. Clone repository or open project directory
cd "build fast"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and insert your Gemini API Key (optional for testing, rule-based fallbacks work out of the box)
```

### Running Locally
```bash
# Run FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to: `http://localhost:8000`

---

## 9. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/process` | Processes voice transcript or text query; identifies language & intent. |
| `POST` | `/api/confirm-grievance` | Confirms draft, assigns `DHV-...` ID, prepares official portal handoff. |
| `POST` | `/api/edit-grievance` | Edits issue, category, location, priority, or description before confirmation. |
| `GET` | `/api/track/{gid}` | Tracks request status by Dhvaani Tracking ID or internal ID. |
| `POST` | `/api/link-government-ref` | Links citizen's official government reference number to their Dhvaani request. |
| `GET` | `/api/schemes` | Returns all 12 verified schemes with Phase 6 verification metadata. |
| `GET` | `/api/services` | Returns the complete service catalog (schemes + grievance services). |
| `GET` | `/api/services/{id}` | Returns authoritative details for a specific scheme or service. |
| `GET` | `/api/services/{id}/status/{ref}` | Truthfully routes to official status portal for the specified government reference. |
| `POST` | `/api/attachments` | Secure multi-file attachment/evidence upload (JPG, PNG, WEBP, PDF up to 10MB). |
| `DELETE`| `/api/attachments/{id}` | Deletes uploaded attachment record and physical file. |
| `GET` | `/api/attachments` | Lists attachments associated with a given Dhvaani Request ID. |
| `GET` | `/api/health` | Healthcheck endpoint reporting service status. |

---

## 10. Automated Testing

The project contains **87 automated tests** covering Phases 1 through 7:
```bash
python -m pytest tests/ -v
```

Expected test result:
```text
======================= 87 passed, 3 warnings in ~40s =======================
```

---

## 11. Production Deployment (Vercel + GitHub)

Dhvaani is production-ready for deployment on **Vercel**:
- **Python Runtime**: `@vercel/python` runs FastAPI serverless functions via `main.py` and `vercel.json`.
- **Dual-Mode Persistence**:
  - *Local Development*: SQLite (`dhvaani.db`) with zero setup.
  - *Vercel Production*: PostgreSQL connection via `DATABASE_URL` (compatible with Neon, Supabase, Vercel Postgres).
- **Evidence Storage**:
  - *Local*: Secure `./data/uploads/` directory with path traversal protection.
  - *Vercel*: Vercel Blob cloud storage integration via `BLOB_READ_WRITE_TOKEN`.
- **Static Assets**: Complete responsive frontend, Google fonts, SVG vector icons, and Unsplash-licensed photography served directly.

To deploy via Vercel CLI:
```bash
vercel deploy --prod
```

---

## 12. Security & Compliance

- **No Hardcoded API Keys**: All secrets are loaded strictly from `.env`.
- **Git Ignored**: `.env`, `*.db`, `data/uploads/`, and cache files are strictly ignored via `.gitignore`.
- **No Private Data Storage**: Audio streams are processed locally in the browser; raw audio is never stored on the server.
- **Truthful Communication**: No artificial delays, fake officer names, or simulated approvals are ever returned.

---

## 12. Photography & Civic Visual Assets

Dhvaani uses curated high-resolution photography representing real Indian citizens, rural communities, and public infrastructure to deliver a human-centered civic interface. All photographs are stored locally under `static/assets/images/` and are licensed for free commercial and editorial use under the Unsplash License:

| Asset | Subject | Source & License |
| :--- | :--- | :--- |
| `farmer-community.webp` | Indian farmer in agricultural field receiving scheme guidance | Unsplash Community (Unsplash Free License) |
| `citizen-support.webp` | Indian woman and family accessing public welfare services | Unsplash Community (Unsplash Free License) |
| `community-health.webp` | Community healthcare professional providing clinical support | Unsplash Community (Unsplash Free License) |
| `civic-infrastructure.webp` | Clean urban streets, public lighting, and municipal infrastructure | Unsplash Community (Unsplash Free License) |
| `public-service.webp` | Young students and citizens exploring scholarship opportunities | Unsplash Community (Unsplash Free License) |
