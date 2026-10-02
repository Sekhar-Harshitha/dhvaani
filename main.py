"""
Dhvaani - Multilingual Government Services Voice Assistant
FastAPI Backend — Phase 1 (Reliable Core)

IMPORTANT DESIGN RULES:
- Gemini is used ONLY for language understanding and intent detection.
- ALL scheme facts (eligibility, benefits, steps, helplines) come from
  the verified schemes_db.py database — never from Gemini free-form.
- Grievances are tracked internally as Dhvaani requests only.
  We NEVER claim to have submitted anything to a government department.
"""

import os
import json
import uuid
import datetime
import re
import string
from typing import Optional, List, Dict, Any

import google.generativeai as genai
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

from schemes_db import GOVERNMENT_SCHEMES, GRIEVANCE_DEPARTMENTS
import db
from services_catalog import ServiceCatalog, GRIEVANCE_SERVICES
import storage

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_ready = True
    except Exception:
        _gemini_ready = False
else:
    _gemini_ready = False

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

def is_openrouter_ready() -> bool:
    """Return True if a valid OpenRouter API key has been configured."""
    return bool(OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here" and OPENROUTER_API_KEY.startswith("sk-or-"))

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
_sarvam_ready = bool(SARVAM_API_KEY and SARVAM_API_KEY != "your_sarvam_api_key_here")

def is_sarvam_ready() -> bool:
    """Return True if a valid Sarvam API key has been configured."""
    return _sarvam_ready

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and load stored requests on startup."""
    db.init_db()
    db.load_all_requests_to_memory(GRIEVANCE_STORE)
    yield

app = FastAPI(title="Dhvaani API", version="1.8.0", lifespan=lifespan)

# Dynamic CORS configuration: Production Vercel domain, local development, or configured origins
_allowed_env = os.getenv("ALLOWED_ORIGINS", "").strip()
if _allowed_env:
    _origins = [o.strip() for o in _allowed_env.split(",") if o.strip()]
else:
    _origins = [
        "https://dhvaani.vercel.app",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"^https://[a-zA-Z0-9_-]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ──────────────────────────────────────────────
# UPLOAD DIRECTORY CONFIGURATION (Phase 7 + Vercel)
# ──────────────────────────────────────────────
# NEVER expose the upload directory as a public static folder.
# All uploads are served only through the explicit /api/attachments endpoint.
_default_upload_dir = Path(__file__).parent / "data" / "uploads"
_env_upload_dir = os.getenv("DHVAANI_UPLOAD_DIR")
if _env_upload_dir:
    UPLOAD_DIR = Path(_env_upload_dir)
elif os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    UPLOAD_DIR = Path("/tmp/uploads")
else:
    UPLOAD_DIR = _default_upload_dir

try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    UPLOAD_DIR = Path("/tmp/uploads")
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

MAX_FILE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_FILES_PER_REQUEST = 5

# Allowed MIME types and their canonical extensions
ALLOWED_MIME_TYPES: dict = {
    "image/jpeg":       [".jpg", ".jpeg"],
    "image/png":        [".png"],
    "image/webp":       [".webp"],
    "application/pdf":  [".pdf"],
}
# Allowed extensions (derived from above map)
ALLOWED_EXTENSIONS: set = {
    ext for exts in ALLOWED_MIME_TYPES.values() for ext in exts
}

# In-memory grievance store (DHV tracking IDs) synchronized with SQLite
GRIEVANCE_STORE: dict = {}

# ──────────────────────────────────────────────
# Phase 3: In-session context store
# Lightweight dict keyed by a browser-supplied session token.
# NEVER persists sensitive data to a database.
# ──────────────────────────────────────────────
SESSION_CONTEXT_STORE: dict = {}


# ──────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────

class TextQueryRequest(BaseModel):
    text: str
    language: str = "en"
    session_id: Optional[str] = None   # Phase 3: lightweight session context


class GrievanceConfirmRequest(BaseModel):
    grievance_id: str
    confirmed: bool
    user_name: Optional[str] = None
    contact: Optional[str] = None
    attachment_ids: Optional[List[str]] = None


class GrievanceEditRequest(BaseModel):
    grievance_id: str
    issue: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    department: Optional[str] = None


class SetKeyRequest(BaseModel):
    key: str


class SessionContextUpdate(BaseModel):
    session_id: str
    context: dict


class LinkGovernmentRefRequest(BaseModel):
    tracking_id: str
    government_reference_id: str


class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    speaker: Optional[str] = None



# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def is_gemini_ready() -> bool:
    """Return True if OpenRouter or direct Gemini API key has been configured."""
    return is_openrouter_ready() or _gemini_ready


class OpenRouterGeminiResponse:
    """Simple wrapper exposing .text property matching Google GenerativeAI response."""
    def __init__(self, text: str):
        self.text = text


class GeminiModelWrapper:
    """Resilient Gemini model wrapper routing through OpenRouter with fallback to Google SDK."""
    _model_order: List[str] = [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-flash-latest",
    ]

    def __init__(self, model_names: Optional[List[str]] = None):
        self.model_names = model_names or list(GeminiModelWrapper._model_order)

    def generate_content(self, *args, **kwargs):
        # 1. Prefer OpenRouter for Gemini reasoning when configured
        if is_openrouter_ready():
            prompt_text = ""
            if args:
                first = args[0]
                if isinstance(first, str):
                    prompt_text = first
                elif isinstance(first, list) and len(first) > 0 and isinstance(first[0], str):
                    prompt_text = first[0]
            elif "contents" in kwargs:
                c = kwargs["contents"]
                if isinstance(c, str):
                    prompt_text = c

            if prompt_text:
                try:
                    headers = {
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://dhvaani.vercel.app",
                        "X-Title": "Dhvaani",
                    }
                    payload = {
                        "model": OPENROUTER_MODEL,
                        "messages": [{"role": "user", "content": prompt_text}],
                        "temperature": 0.1,
                        "max_tokens": 200,
                    }
                    resp = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=12
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0] and "content" in choices[0]["message"]:
                            return OpenRouterGeminiResponse(choices[0]["message"]["content"])
                    elif resp.status_code == 402:
                        # Out of credits — skip directly to Gemini SDK fallback
                        print(f"[Dhvaani] OpenRouter 402 (credit limit) — using Gemini SDK directly")
                    else:
                        print(f"[Dhvaani] OpenRouter error {resp.status_code}: {resp.text[:120]}")
                except Exception as e:
                    print(f"[Dhvaani] OpenRouter exception: {e}")

        # 2. Fallback to direct Gemini SDK if configured
        last_exc = None
        current_list = list(GeminiModelWrapper._model_order) if not self.model_names else list(self.model_names)
        for m_name in current_list:
            try:
                m = genai.GenerativeModel(m_name)
                res = m.generate_content(*args, **kwargs)
                # Keep successful model at front
                if m_name in GeminiModelWrapper._model_order and GeminiModelWrapper._model_order[0] != m_name:
                    GeminiModelWrapper._model_order.remove(m_name)
                    GeminiModelWrapper._model_order.insert(0, m_name)
                return res
            except Exception as e:
                last_exc = e
                err_type = type(e).__name__
                if "ResourceExhausted" in err_type or "NotFound" in err_type or "429" in str(e) or "404" in str(e):
                    # Move exhausted model to back
                    if m_name in GeminiModelWrapper._model_order:
                        GeminiModelWrapper._model_order.remove(m_name)
                        GeminiModelWrapper._model_order.append(m_name)
                    continue
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError("No AI reasoning model available.")


def get_model():
    """Return a configured Gemini model instance with resilient fallback across flash models."""
    return GeminiModelWrapper()


def parse_json_from_ai(text: str) -> dict:
    """
    Strip markdown code fences that Gemini sometimes wraps around JSON,
    then parse. Raises json.JSONDecodeError on failure.
    """
    text = text.strip()
    # Strip markdown code fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    # Try to parse directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to extract JSON object from mixed text
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return json.loads(match.group(0))
    raise json.JSONDecodeError("No JSON object found", text, 0)


def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace. Keeps Unicode chars intact."""
    return re.sub(r"\s+", " ", text.lower().strip())


def clean_error_response(message: str, detail: str = "Please try again.") -> dict:
    """
    Return a clean JSON-safe error dict.
    Never expose Python stack traces or internal errors.
    """
    return {"success": False, "error": message, "message": detail}


# ──────────────────────────────────────────────
# INTENT DETECTION
# ──────────────────────────────────────────────

def detect_intent(text: str) -> dict:
    """
    Detect language, intent (scheme/grievance/unknown), and confidence.
    Uses Gemini if available; falls back to keyword heuristics.

    Returns:
        {
          "language": "en" | "hi" | "ta",
          "language_name": "English" | "Hindi" | "Tamil",
          "intent": "scheme" | "grievance" | "unknown",
          "confidence": float,
          "query": str,
          "user_context": { ... }
        }
    """
    if is_gemini_ready():
        return _gemini_detect_intent(text)
    return _fallback_detect_intent(text)


def _gemini_detect_intent(text: str) -> dict:
    """
    Phase 3: Extended prompt extracts richer user context for scheme matching.
    """
    prompt = (
        'You are a language and intent classifier for Dhvaani, an Indian government services assistant.\n'
        'Analyze the message below and respond ONLY with valid JSON. No extra text.\n\n'
        f'Message: "{text}"\n\n'
        'JSON schema to return:\n'
        '{\n'
        '  "language": "en" or "hi" or "ta",\n'
        '  "language_name": "English" or "Hindi" or "Tamil",\n'
        '  "intent": "scheme" or "grievance" or "unknown",\n'
        '  "confidence": <number 0.0-1.0>,\n'
        '  "query": "<normalized query in English>",\n'
        '  "user_context": {\n'
        '    "occupation": "<farmer/student/worker/daily wage/self-employed/etc or null>",\n'
        '    "age": <number or null>,\n'
        '    "child_age": <number or null — age of child if user is asking for a child>,\n'
        '    "gender": "<male/female/null>",\n'
        '    "child_gender": "<male/female/null — gender of child if relevant>",\n'
        '    "state": "<Indian state name or null>",\n'
        '    "income": "<low/medium/high or null>",\n'
        '    "need": "<brief need: financial support/health insurance/crop insurance/savings/employment/housing/etc or null>",\n'
        '    "category": "<agriculture/health/housing/energy/employment/banking/women/pension/education or null>"\n'
        '  }\n'
        '}\n\n'
        'Rules:\n'
        '- intent=scheme: user asking about government benefits, eligibility, welfare, pension, insurance, scheme, yojana, allowance\n'
        '- intent=grievance: user reporting a civic problem, complaint, broken infrastructure, public service failure\n'
        '- intent=unknown: greetings, small talk, unrelated topics, or genuinely ambiguous\n'
        '- If unsure between scheme and grievance, set intent=unknown with confidence < 0.6\n'
        '- Extract what is clearly stated — do not invent context that the user did not mention\n'
    )
    try:
        r = get_model().generate_content(prompt)
        result = parse_json_from_ai(r.text)
        # Validate required fields
        result.setdefault("confidence", 0.7)
        result.setdefault("user_context", {})
        result.setdefault("query", text[:200])
        return result
    except Exception as e:
        print(f"[Dhvaani] Gemini intent error: {type(e).__name__}")
        return _fallback_detect_intent(text)


def _fallback_detect_intent(text: str) -> dict:
    """Heuristic fallback when Gemini is unavailable."""
    # Language detection by Unicode range
    if any('\u0B80' <= c <= '\u0BFF' for c in text):
        lang, lang_name = "ta", "Tamil"
    elif any('\u0900' <= c <= '\u097F' for c in text):
        lang, lang_name = "hi", "Hindi"
    else:
        lang, lang_name = "en", "English"

    tl = normalize_text(text)
    scheme_kw = [
        "scheme", "yojana", "eligib", "benefit", "welfare", "pension", "insurance",
        "kisan", "scholarship", "subsidy", "ration", "job card", "nrega", "ayushman",
        "ujjwala", "जानकारी", "योजना", "पात्रता",
        "திட்டம்", "தகுதி", "உதவி",
    ]
    grievance_kw = [
        "problem", "complaint", "not working", "broken", "repair", "issue", "shikayat",
        "light", "road", "water", "garbage", "pothole", "drainage", "no supply",
        "power cut", "power failure", "no power", "blackout", "outage", "leak",
        "बिजली नहीं", "पानी नहीं", "सड़क", "शिकायत", "बिजली",
        "புகார்", "சிக்கல்", "தெரு விளக்கு", "தண்ணீர்", "மின்வெட்டு", "மின்சாரம்",
    ]
    is_scheme = any(k in tl for k in scheme_kw)
    is_grievance = any(k in tl for k in grievance_kw)

    if is_scheme and not is_grievance:
        intent, confidence = "scheme", 0.70
    elif is_grievance and not is_scheme:
        intent, confidence = "grievance", 0.70
    elif is_scheme and is_grievance:
        intent, confidence = "unknown", 0.50
    else:
        intent, confidence = "unknown", 0.40

    return {
        "language": lang,
        "language_name": lang_name,
        "intent": intent,
        "confidence": confidence,
        "query": text[:200],
        "user_context": {},
    }


# ──────────────────────────────────────────────
# SCHEME MATCHING
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
# Phase 3: SESSION CONTEXT HELPERS
# ──────────────────────────────────────────────

def get_session_context(session_id: Optional[str]) -> dict:
    """Retrieve existing session context, or return empty dict."""
    if not session_id:
        return {}
    return SESSION_CONTEXT_STORE.get(session_id, {})


def merge_session_context(session_id: Optional[str], new_context: dict) -> dict:
    """
    Merge newly detected user context into the session context.
    Only non-None values overwrite existing ones.
    Returns the merged context.
    """
    if not session_id:
        return new_context
    existing = SESSION_CONTEXT_STORE.get(session_id, {})
    merged = dict(existing)
    for k, v in new_context.items():
        if v is not None and v != "" and v != []:
            merged[k] = v
    SESSION_CONTEXT_STORE[session_id] = merged
    return merged


# ──────────────────────────────────────────────
# Phase 3: MULTI-SIGNAL SCHEME MATCHING
# ──────────────────────────────────────────────

def _score_scheme(scheme: dict, tl: str, ctx: dict) -> tuple:
    """
    Score a single scheme against the normalised query text and user context.
    Returns (score: float, reasons: list[str])

    Signal weights:
      keyword match        = 2.0 per keyword hit
      occupation match     = 4.0 (strong)
      category match       = 3.0
      state match          = 2.5
      need/keyword match   = 2.0 per hit
      gender match         = 1.5
      age fit              = 1.5
      target group match   = 2.0
    """
    score = 0.0
    reasons = []

    # ── Keyword hits ──
    kw_hits = [kw for kw in scheme.get("keywords", []) if normalize_text(kw) in tl]
    if kw_hits:
        score += len(kw_hits) * 2.0
        reasons.append(f"keyword match: {', '.join(kw_hits[:3])}")

    # ── Scheme name words ──
    name_words = [w for w in scheme["name"].lower().split() if len(w) > 3 and w in tl]
    score += len(name_words) * 1.0

    # ── Occupation match (strong signal) ──
    user_occ = (ctx.get("occupation") or "").lower()
    if user_occ:
        for occ in scheme.get("occupation", []):
            if occ.lower() in user_occ or user_occ in occ.lower():
                score += 4.0
                reasons.append(f"you mentioned occupation: {user_occ}")
                break
        # Also check if occupation word appears in text
        for occ in scheme.get("occupation", []):
            if occ.lower() in tl and occ.lower() not in user_occ:
                score += 2.0
                break

    # ── Category match ──
    user_cat = (ctx.get("category") or "").lower()
    user_need = (ctx.get("need") or "").lower()
    scheme_cat = scheme.get("category", "").lower()
    if user_cat and user_cat in scheme_cat:
        score += 3.0
        reasons.append(f"category match: {scheme_cat}")
    elif user_need:
        # Check if need words align with scheme category or keywords
        need_words = user_need.split()
        cat_hit = any(w in scheme_cat for w in need_words)
        kw_need_hit = any(w in normalize_text(" ".join(scheme.get("keywords", []))) for w in need_words if len(w) > 3)
        if cat_hit or kw_need_hit:
            score += 2.0
            reasons.append(f"need match: {user_need}")

    # ── State match ──
    user_state = (ctx.get("state") or "").lower()
    scheme_state = scheme.get("state", "India").lower()
    if user_state:
        if user_state in scheme_state or scheme_state == "india":
            if scheme_state != "india":
                score += 2.5  # Exact state match is better
                reasons.append(f"state match: {scheme.get('state')}")
            else:
                score += 0.5  # National schemes are less specific
        else:
            # State scheme but wrong state → penalise
            if scheme_state != "india":
                score -= 3.0

    # ── Gender match ──
    user_gender = (ctx.get("gender") or ctx.get("child_gender") or "").lower()
    scheme_genders = [g.lower() for g in scheme.get("gender", ["male", "female"])]
    if user_gender and scheme_genders:
        if user_gender in scheme_genders:
            score += 1.5
            reasons.append(f"gender match: {user_gender}")
        elif "all" not in scheme_genders and user_gender not in scheme_genders:
            score -= 2.0  # Wrong gender → penalise

    # ── Target group match ──
    target_groups_text = normalize_text(" ".join(scheme.get("target_groups", [])))
    if user_occ and user_occ in target_groups_text:
        score += 2.0
        reasons.append(f"target group match: {user_occ}")

    # ── Age fit (for child_age / user_age) ──
    child_age = ctx.get("child_age")
    user_age = ctx.get("age")
    age_to_check = child_age if child_age is not None else user_age
    age_min = scheme.get("age_min")
    age_max = scheme.get("age_max")
    if age_to_check is not None and (age_min is not None or age_max is not None):
        in_range = True
        if age_min is not None and age_to_check < age_min:
            in_range = False
        if age_max is not None and age_to_check > age_max:
            in_range = False
        if in_range:
            score += 1.5
            reasons.append(f"age fits: {age_to_check}")
        else:
            score -= 2.5  # Age explicitly out of range → penalise significantly

    return (score, reasons)


def match_schemes(text: str, user_context: dict = None) -> List[dict]:
    """
    Phase 3: Multi-signal scheme matching.
    Returns up to 3 schemes with scores > 0, or empty list if no match.
    """
    if user_context is None:
        user_context = {}
    tl = normalize_text(text)
    scored = []

    for scheme in GOVERNMENT_SCHEMES:
        score, reasons = _score_scheme(scheme, tl, user_context)
        if score > 0:
            scored.append((score, reasons, scheme))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [(scheme, reasons) for _, reasons, scheme in scored[:3]]


def build_scheme_matches_metadata(text: str, matched: List) -> List[dict]:
    """
    Phase 3: Build structured match metadata including match reason.
    matched is a list of (scheme, reasons) tuples.
    """
    result = []
    for item in matched:
        if isinstance(item, tuple):
            scheme, reasons = item
        else:
            # Backward compat: plain scheme dict
            scheme = item
            reasons = []
        result.append({
            "scheme_id": scheme["id"],
            "name": scheme["name"],
            "match_reasons": reasons,
        })
    return result


# ──────────────────────────────────────────────
# SCHEME RESPONSE GENERATION
# ──────────────────────────────────────────────

def _enrich_cards_with_db_data(cards: List[dict], schemes: List[dict]) -> List[dict]:
    for card in cards:
        s = next(
            (x for x in schemes if x.get("id") == card.get("id")
             or x.get("scheme_id") == card.get("scheme_id")
             or x.get("name") == card.get("scheme_name")
             or x.get("official_name") == card.get("scheme_name")),
            None
        )
        if not s and schemes:
            s = schemes[0]
        if s:
            card["id"] = s.get("id", "")
            card["scheme_id"] = s.get("scheme_id", s.get("id", ""))
            card["official_name"] = s.get("official_name", s.get("name", ""))
            card["official_source"] = s.get("official_source", "")
            card["official_source_url"] = s.get("official_source_url", s.get("official_source", ""))
            card["application_url"] = s.get("application_url", "")
            card["status_url"] = s.get("status_url", "")
            card["official_application_url"] = s.get("official_application_url", s.get("official_source", ""))
            card["official_information_url"] = s.get("official_information_url", s.get("official_source", ""))
            card["source_url"] = s.get("source_url", s.get("official_source", ""))
            card["official_helpline"] = s.get("official_helpline", s.get("helpline", ""))
            card["helpline"] = s.get("helpline", "")
            card["last_verified"] = s.get("last_verified", "2024-11-15")
            card["verification_status"] = s.get("verification_status", "verified")
            card["ministry_or_department"] = s.get("ministry_or_department", s.get("ministry", ""))
            if not card.get("required_documents") and s.get("required_documents"):
                card["required_documents"] = s["required_documents"]
            if not card.get("documents") and s.get("documents"):
                card["documents"] = s["documents"]
            if not card.get("benefit") and s.get("benefit"):
                card["benefit"] = s["benefit"]
    return cards


def build_scheme_response(text: str, matched: List, language: str, user_context: dict = None) -> dict:
    """
    Phase 3: Use verified scheme data from DB.
    matched is a list of (scheme, reasons) tuples.
    Gemini writes language-appropriate explanation; it does NOT invent facts.
    """
    if user_context is None:
        user_context = {}
    # Extract just the schemes for the response builder
    schemes = [item[0] if isinstance(item, tuple) else item for item in matched]
    reasons_map = {}
    for item in matched:
        if isinstance(item, tuple):
            reasons_map[item[0]["id"]] = item[1]

    if is_gemini_ready():
        res = _gemini_scheme_response(text, schemes, language, reasons_map, user_context)
    else:
        res = _fallback_scheme_response(schemes, reasons_map, user_context)

    if res and "schemes" in res and isinstance(res["schemes"], list):
        res["schemes"] = _enrich_cards_with_db_data(res["schemes"], schemes)
    return res


def _build_match_reason_sentence(scheme: dict, reasons: list, user_context: dict) -> str:
    """
    Phase 3: Build a human-readable 'why this may be relevant' sentence
    from matching signals. Uses only what the user actually stated.
    """
    parts = []
    occ = user_context.get("occupation")
    state = user_context.get("state")
    need = user_context.get("need")
    gender = user_context.get("gender")
    child_age = user_context.get("child_age")
    child_gender = user_context.get("child_gender")

    if occ:
        parts.append(f"you mentioned you are a {occ}")
    if state:
        parts.append(f"you are from {state}")
    if need:
        parts.append(f"you are looking for {need}")
    if gender == "female":
        parts.append("you are a woman")
    if child_age is not None:
        parts.append(f"your child is {child_age} years old")
    if child_gender == "female":
        parts.append("your child is a girl")

    if parts:
        reason = "Based on what you told me — " + ", ".join(parts) + " — this scheme may be relevant."
    elif reasons:
        # Fall back to keyword-based reasons
        clean = [r for r in reasons if not r.startswith("keyword match")]
        if clean:
            reason = f"This scheme may be relevant: {'; '.join(clean[:2])}."
        else:
            reason = "This scheme may be relevant based on your query."
    else:
        reason = "This scheme may be relevant based on your query."

    return reason


def _gemini_scheme_response(
    text: str, schemes: List[dict], language: str,
    reasons_map: dict, user_context: dict
) -> dict:
    lang_name = {"en": "English", "hi": "Hindi", "ta": "Tamil"}.get(language, "English")

    # Build verified data payload — Gemini must use this, not invent alternatives
    scheme_payloads = []
    for s in schemes:
        reasons = reasons_map.get(s["id"], [])
        match_reason = _build_match_reason_sentence(s, reasons, user_context)
        scheme_payloads.append({
            "name": s["name"],
            "category": s.get("category", ""),
            "state": s.get("state", "India"),
            "description": s["description"],
            "benefit": s["benefit"],
            "eligibility": s["eligibility"],
            "documents": s.get("documents", []),
            "application_steps": s["application_steps"],
            "helpline": s.get("helpline", ""),
            "official_source": s.get("official_source", ""),
            "match_reason": match_reason,
        })

    verified_data = json.dumps(scheme_payloads, ensure_ascii=False)

    prompt = (
        f'You are Dhvaani, a helpful Indian government services assistant.\n'
        f'User query (in {lang_name}): "{text}"\n\n'
        f'VERIFIED SCHEME DATA (use ONLY this — do NOT add or invent any facts, eligibility, URLs, or amounts):\n{verified_data}\n\n'
        f'Respond in {lang_name}. Return ONLY valid JSON with this exact structure:\n'
        f'{{\n'
        f'  "greeting": "warm 1-sentence greeting in {lang_name}",\n'
        f'  "schemes": [\n'
        f'    {{\n'
        f'      "scheme_name": "exact name from data",\n'
        f'      "category": "category from data",\n'
        f'      "match_reason": "use the match_reason field from the data exactly — do not rewrite it",\n'
        f'      "description": "2-3 sentence explanation in {lang_name} using the description field from data only",\n'
        f'      "benefit": "exact benefit text from data",\n'
        f'      "key_eligibility": ["up to 3 items from eligibility field in data"],\n'
        f'      "documents": ["up to 3 items from documents field in data"],\n'
        f'      "quick_steps": ["up to 3 items from application_steps field in data"],\n'
        f'      "official_source": "exact official_source from data (or empty string if not in data)",\n'
        f'      "helpline": "exact helpline from data"\n'
        f'    }}\n'
        f'  ],\n'
        f'  "closing_message": "1-2 sentence closing in {lang_name}. Must include: eligibility shown is informational — verify with the official portal.",\n'
        f'  "spoken_summary": "2-3 natural spoken sentences in {lang_name} summarising the top scheme. Do NOT read all fields — keep it brief and conversational."\n'
        f'}}\n\n'
        f'CRITICAL RULES:\n'
        f'- Do NOT say the user is definitely eligible.\n'
        f'- Use phrases like "may be relevant", "based on what you told me", "check official eligibility".\n'
        f'- Do NOT invent URLs, amounts, or eligibility criteria not present in the data.\n'
        f'- match_reason must come from the data — do not rewrite or embellish it.\n'
    )
    try:
        r = get_model().generate_content(prompt)
        return parse_json_from_ai(r.text)
    except Exception as e:
        print(f"[Dhvaani] Gemini scheme response error: {type(e).__name__}")
        return _fallback_scheme_response(schemes, reasons_map, user_context)


def _fallback_scheme_response(schemes: List[dict], reasons_map: dict = None, user_context: dict = None) -> dict:
    """
    Phase 3: Fallback when Gemini is unavailable.
    Uses verified DB data only. Includes match_reason and official_source.
    """
    if reasons_map is None:
        reasons_map = {}
    if user_context is None:
        user_context = {}

    if not schemes:
        return {
            "greeting": "I searched Dhvaani's scheme database.",
            "schemes": [],
            "closing_message": (
                "I couldn't find a closely matching scheme in Dhvaani's current scheme database. "
                "You can try describing your need differently."
            ),
            "spoken_summary": (
                "I couldn't find a closely matching scheme. Please try describing your need differently."
            ),
        }

    scheme_cards = []
    for s in schemes:
        reasons = reasons_map.get(s["id"], [])
        match_reason = _build_match_reason_sentence(s, reasons, user_context)
        official_source = s.get("official_source") or "Official source not available in Dhvaani's current database."
        scheme_cards.append({
            "scheme_name": s["name"],
            "category": s.get("category", ""),
            "match_reason": match_reason,
            "description": s["description"],
            "benefit": s.get("benefit", ""),
            "key_eligibility": s.get("eligibility", [])[:3],
            "documents": s.get("documents", [])[:3],
            "quick_steps": s.get("application_steps", [])[:3],
            "official_source": official_source,
            "helpline": s.get("helpline", ""),
        })

    s0 = schemes[0]
    spoken = (
        f"{s0['name']} may be relevant. "
        f"{s0['description'][:100]}. "
        "Please check the official eligibility requirements before applying."
    )
    return {
        "greeting": f"I found {len(schemes)} potentially relevant scheme(s) in Dhvaani's database.",
        "schemes": scheme_cards,
        "closing_message": (
            "The information shown is from Dhvaani's verified scheme database and is for reference only. "
            "Please check official eligibility requirements before applying."
        ),
        "spoken_summary": spoken,
    }


# ──────────────────────────────────────────────
# Phase 3: FOLLOW-UP QUESTION GENERATOR
# ──────────────────────────────────────────────

def _suggest_follow_up_question(user_context: dict, language: str) -> Optional[str]:
    """
    Phase 3: Suggest ONE useful follow-up question if a single missing piece
    of information would significantly improve scheme matching.
    Returns None if no follow-up is needed.
    Only asks if context is sparse.
    """
    occ = user_context.get("occupation")
    state = user_context.get("state")
    gender = user_context.get("gender")
    child_age = user_context.get("child_age")
    need = user_context.get("need")
    age = user_context.get("age")

    # Don't pepper the user with questions — only ask if context is very sparse
    known_fields = sum(1 for f in [occ, state, gender, child_age, need, age] if f)
    if known_fields >= 2:
        return None  # Enough context

    questions = {
        "en": {
            "state": "Could you tell me which state you are from? This will help me find state-specific schemes.",
            "occupation": "What is your occupation? (e.g., farmer, daily wage worker, student) This helps me find the most relevant scheme.",
            "age": "How old are you? This will help me narrow down the applicable schemes.",
            "daughter_age": "How old is your daughter? This will help me find the right savings or education scheme for her.",
        },
        "hi": {
            "state": "क्या आप बता सकते हैं कि आप किस राज्य से हैं? इससे मुझे राज्य-विशेष योजनाएं खोजने में मदद मिलेगी।",
            "occupation": "आपका व्यवसाय क्या है? (जैसे किसान, मजदूर, छात्र) इससे मुझे सबसे उपयुक्त योजना मिलेगी।",
            "age": "आपकी उम्र क्या है? इससे मुझे लागू योजनाओं को संकुचित करने में मदद मिलेगी।",
            "daughter_age": "आपकी बेटी की उम्र क्या है? इससे मुझे उसके लिए सही योजना मिलेगी।",
        },
        "ta": {
            "state": "நீங்கள் எந்த மாநிலத்தில் இருந்து வருகிறீர்கள்? இது மாநில திட்டங்களை கண்டறிய உதவும்.",
            "occupation": "உங்கள் தொழில் என்ன? (எ.கா. விவசாயி, தொழிலாளர், மாணவர்) இது பொருத்தமான திட்டம் கண்டறிய உதவும்.",
            "age": "உங்கள் வயது என்ன? இது பொருந்தும் திட்டங்களை குறைக்க உதவும்.",
            "daughter_age": "உங்கள் மகளுக்கு எத்தனை வயது? சரியான திட்டம் கண்டறிய இது உதவும்.",
        },
    }
    lang_q = questions.get(language, questions["en"])

    # If daughter / girl child mentioned but age unknown
    child_gender = user_context.get("child_gender")
    if child_gender == "female" and child_age is None:
        return lang_q.get("daughter_age")

    # If no state and no occupation → ask occupation (more discriminating)
    if not occ and not state:
        return lang_q.get("occupation")

    # If occupation known but no state → ask state
    if occ and not state:
        return lang_q.get("state")

    # If state known but no occupation → ask occupation
    if state and not occ:
        return lang_q.get("occupation")

    return None


# ──────────────────────────────────────────────
# GRIEVANCE DEPARTMENT MATCHING
# ──────────────────────────────────────────────

def match_department(text: str) -> tuple[Optional[str], Optional[dict], float]:
    """
    Score all departments against user text.
    Returns (dept_key, dept_info, confidence_score).
    Returns (None, None, 0.0) if nothing matches with confidence.
    """
    tl = normalize_text(text)
    best_key, best_dept, best_score = None, None, 0

    # Prioritize streetlight explicitly if streetlight terms appear
    streetlight_terms = [
        "street light", "streetlight", "road light", "lamp post", "no light on road",
        "தெரு விளக்கு", "தெருவிளக்கு", "விளக்கு எரியவில்லை", "தெரு லைட்", "தெரு விளக்குகள்",
        "सड़क की लाइट", "स्ट्रीट लाइट", "स्ट्रीटलाइट", "गली की लाइट", "खंभे की लाइट",
    ]
    if any(st in tl for st in streetlight_terms) and "streetlight" in GRIEVANCE_DEPARTMENTS:
        return "streetlight", GRIEVANCE_DEPARTMENTS["streetlight"], 0.85

    for dept_key, dept_info in GRIEVANCE_DEPARTMENTS.items():
        kw_hits = sum(1 for kw in dept_info.get("keywords", []) if normalize_text(kw) in tl)
        if kw_hits > best_score:
            best_score = kw_hits
            best_key = dept_key
            best_dept = dept_info

    if best_score == 0:
        return None, None, 0.0

    # Rough confidence: more keyword hits → higher confidence
    max_possible = max(len(d.get("keywords", [1])) for d in GRIEVANCE_DEPARTMENTS.values())
    confidence = min(best_score / max(max_possible * 0.15, 1), 0.95)
    return best_key, best_dept, confidence


# ──────────────────────────────────────────────
# PHASE 4: GRIEVANCE DETAIL EXTRACTION & PRIORITY
# ──────────────────────────────────────────────

def _extract_location(text: str, language: str = "en") -> Optional[str]:
    """
    Extract natural language locality / landmark if provided in text.
    Never invents addresses. Returns None if unknown.
    """
    known_localities = [
        "Poonamallee High Road", "Poonamallee", "Maduravoyal", "Koyambedu", "Anna Nagar",
        "T Nagar", "Velachery", "Guindy", "Tambaram", "Adyar", "Mylapore", "Porur",
        "Chromepet", "Perambur", "Saidapet", "Egmore", "Mount Road", "OMR", "ECR",
        "மதுரவாயல்", "கோயம்பேடு", "பூந்தமல்லி", "அண்ணா நகர்", "வேளச்சேரி", "கிண்டி", "தாம்பரம்",
        "மயிலாப்பூர்", "போரூர்", "பூந்தமல்லி நெடுஞ்சாலை",
        "मधुरवॉयल", "मदुरवायल", "कोयम्बेडु", "पूनमल्ली", "अन्ना नगर", "पूनमल्ली हाई रोड"
    ]
    text_clean = text.strip()
    
    # 1. Known locality check
    for loc in known_localities:
        if loc.lower() in text_clean.lower():
            m = re.search(rf"{re.escape(loc)}(?:\s+(?:High Road|bus stand|bus stop|college entrance|railway station))?", text_clean, re.I)
            matched_loc = m.group(0) if m else loc
            if "college entrance" in text_clean.lower() and "college entrance" not in matched_loc.lower():
                return f"{matched_loc} / college entrance"
            return matched_loc

    # 2. Generic landmark with prepositions (English)
    m = re.search(r"(?:near|behind|outside|at|opposite)\s+(?:the\s+)?([a-zA-Z0-9\s]+?(?:bus stand|bus stop|college|hospital|school|railway station|market|entrance|depot|junction|flyover))", text_clean, re.I)
    if m:
        val = m.group(1).strip()
        if not re.search(r"^(my house|our house|my home|our area|my area|here)$", val, re.I):
            return m.group(0).strip()

    # In/at locality pattern
    m_in = re.search(r"\b(?:in|at)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b", text_clean)
    if m_in:
        cand = m_in.group(1).strip()
        if cand.lower() not in ("my house", "our house", "the area", "my area", "this area"):
            return cand

    # 3. Tamil morphology check
    m_ta = re.search(r"நாங்கள்\s+([^\s]+?)(?:லில்|ல்|இல்)\s+இருக்கிறோம்", text_clean)
    if m_ta:
        raw_loc = m_ta.group(1).strip()
        if raw_loc.endswith("லி"):
            raw_loc = raw_loc[:-1] + "ல்"
        elif not raw_loc.endswith("ல்"):
            raw_loc = raw_loc + "ல்"
        return raw_loc

    # 4. Hindi pattern check
    m_hi = re.search(r"(?:हम\s+)?([^\s]+?)\s+में\s+(?:रहते हैं|हैं)", text_clean)
    if m_hi:
        cand_hi = m_hi.group(1).strip()
        if cand_hi not in ("इलाके", "घर"):
            return cand_hi

    m_hi_pass = re.search(r"([^\s]+?\s+(?:बस स्टैंड|कॉलेज|स्कूल|अस्पताल))\s+के\s+पास", text_clean)
    if m_hi_pass:
        return m_hi_pass.group(0).strip()

    return None


def _extract_duration(text: str, language: str = "en") -> Optional[str]:
    """Extract natural language duration if mentioned in text."""
    patterns = [
        r"(?:since\s+)?yesterday",
        r"(?:for\s+(?:the\s+past\s+)?)?((?:\d+|one|two|three|four|five|six|seven)\s+(?:days|hours|weeks|months))",
        r"(?:for\s+)?((?:a|1|one)\s+week)",
        r"மூன்று\s+நாட்களாக|\d+\s+நாட்களாக|நேற்றிலிருந்து|ஒரு\s+வாரமாக|\d+\s+மணி\s+நேரமாக|இரண்டு\s+நாட்களாக",
        r"तीन\s+दिनों\s+से|\d+\s+दिनों\s+से|कल\s+से|एक\s+हफ्ते\s+से|\d+\s+घंटे\s+से|दो\s+दिनों\s+से"
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            val = m.group(1) if (m.groups() and m.group(1)) else m.group(0)
            return val.strip()
    return None


def _classify_priority(dept_key: Optional[str], text: str, duration: Optional[str] = None) -> str:
    """
    Classify grievance priority as LOW, MEDIUM, or HIGH.
    Based only on user's stated issue and existing rule logic.
    """
    tl = text.lower()

    # Immediate danger / hazard keywords → HIGH
    high_kw = [
        "sparking", "shock", "electric shock", "exposed wire", "fire", "danger", "hazard", "burst",
        "cave in", "collapse", "accident", "open manhole", "emergency", "flood", "threat", "violence",
        "திறந்த மேன்ஹோல்", "மின் அதிர்ச்சி", "ஆபத்து", "அவசரம்", "தீ", "வெடிப்பு",
        "खतरा", "बिजली का झटका", "खुला मैनहोल", "आग", "हादसा"
    ]
    if any(k in tl for k in high_kw):
        return "HIGH"

    # Prolonged outages in essential utilities (water, electricity, ration) → HIGH
    if dept_key in ("water", "electricity", "ration"):
        if duration and any(w in duration.lower() for w in ["three days", "3 days", "week", "days", "மூன்று", "நேற்றிலிருந்து", "तीन"]):
            return "HIGH"
        if any(w in tl for w in ["three days", "3 days", "week", "மூன்று நாட்களாக", "तीन दिनों से"]):
            return "HIGH"

    # Contaminated water / sewage mix → HIGH
    if dept_key == "water" and any(k in tl for k in ["contaminated", "dirty", "drainage mix", "sewage"]):
        return "HIGH"

    # Low priority triggers (minor / decorative) → LOW
    low_kw = ["decorative", "minor", "single bulb", "cleaning", "footpath crack", "small", "லேசான", "சிறிய", "छोटा"]
    if any(k in tl for k in low_kw):
        return "LOW"

    # Defaults by department
    if dept_key in ("police", "health"):
        return "HIGH"
    if dept_key in ("water", "electricity"):
        return "HIGH" if duration else "MEDIUM"
    return "MEDIUM"


def _extract_issue(text: str, dept_key: Optional[str], language: str = "en") -> str:
    """Derive a clear, concise issue title based on complaint context and language."""
    tl = text.lower()
    if any(k in tl for k in ["pothole", "குழி", "गड्ढा"]):
        return {"ta": "சாலையில் குழி", "hi": "सड़क पर गड्ढा", "en": "Pothole on road"}.get(language, "Pothole on road")
    if any(k in tl for k in ["sparking", "shock", "மின் அதிர்ச்சி", "चिंगारी"]):
        return {"ta": "மின் கம்பி அபாயம்", "hi": "बिजली का खतरा", "en": "Electrical hazard / Sparking wire"}.get(language, "Electrical hazard / Sparking wire")

    issue_map = {
        "water": {"ta": "குடிநீர் விநியோகத் தடை", "hi": "जल आपूर्ति में रुकावट", "en": "Water supply interruption"},
        "streetlight": {"ta": "தெரு விளக்கு எரியவில்லை", "hi": "स्ट्रीट लाइट खराब है", "en": "Streetlight not working"},
        "road": {"ta": "சாலை சேதம் / குழி", "hi": "सड़क क्षति / गड्ढा", "en": "Road damage / pothole"},
        "electricity": {"ta": "மின்வெட்டு பிரச்சனை", "hi": "बिजली कटौती", "en": "Power outage"},
        "ration": {"ta": "ரேஷன் பொருள் விநியோகப் பிரச்சனை", "hi": "राशन समस्या", "en": "Ration supply issue"},
        "municipal": {"ta": "குப்பை / துப்புரவுப் பிரச்சனை", "hi": "सफाई / कचरा समस्या", "en": "Sanitation / Garbage issue"},
        "police": {"ta": "காவல்துறை உதவி கோரிக்கை", "hi": "पुलिस सहायता अनुरोध", "en": "Police assistance request"},
        "health": {"ta": "சுகாதார புகார்", "hi": "स्वास्थ्य शिकायत", "en": "Healthcare issue"},
        "education": {"ta": "பள்ளிக் கல்வி புகார்", "hi": "विद्यालय शिकायत", "en": "School education grievance"},
        "revenue": {"ta": "வருவாய்த் துறை புகார்", "hi": "राजस्व शिकायत", "en": "Revenue department grievance"},
    }
    lang_issues = issue_map.get(dept_key, {"ta": "பொது மக்கள் குறைதீர்ப்பு", "hi": "सार्वजनिक जन शिकायत", "en": "Civic Grievance"})
    return lang_issues.get(language, lang_issues["en"])


def _build_grievance_summary(details: dict, dept_name: str, language: str = "en") -> str:
    """Generate concise human-readable summary before confirmation (Requirement 19)."""
    issue = details.get("issue", "Civic grievance")
    loc = details.get("location")
    prio = details.get("priority", "MEDIUM")

    if language == "ta":
        loc_str = loc if loc else "குறிப்பிடப்படவில்லை"
        return f"நான் புரிந்துகொண்டது:\n{issue}.\nஇடம்: {loc_str}.\nமுன்னுரிமை: {prio}.\nஇந்தத் த்வானி கோரிக்கையை உருவாக்க விரும்புகிறீர்களா?"
    elif language == "hi":
        loc_str = loc if loc else "निर्दिष्ट नहीं"
        return f"मैंने समझा:\n{issue}।\nस्थान: {loc_str}।\nप्राथमिकता: {prio}।\nक्या आप यह ध्वा Project/Dhvaani अनुरोध बनाना चाहते हैं?"
    else:
        loc_str = loc if loc else "Not specified"
        return f"I understood:\n{issue}.\nLocation: {loc_str}.\nPriority: {prio.capitalize()}.\nWould you like to create this Dhvaani request?"


def extract_grievance_details(text: str, language: str = "en", dept_key: Optional[str] = None) -> dict:
    """
    Extract structured grievance details from text.
    Uses Gemini if available, otherwise heuristic fallback.
    """
    if is_gemini_ready():
        return _gemini_extract_grievance_details(text, language, dept_key)
    return _fallback_extract_grievance_details(text, language, dept_key)


def _gemini_extract_grievance_details(text: str, language: str, dept_key: Optional[str]) -> dict:
    prompt = (
        f'Extract structured grievance details from the user complaint below.\n'
        f'Complaint: "{text}"\n\n'
        f'Return ONLY valid JSON with this schema:\n'
        f'{{\n'
        f'  "issue": "short title of issue (max 6 words)",\n'
        f'  "location": "locality or landmark if explicitly stated, else null. Do NOT invent an address.",\n'
        f'  "duration": "duration mentioned in text or null",\n'
        f'  "priority": "LOW" or "MEDIUM" or "HIGH"\n'
        f'}}\n'
    )
    try:
        r = get_model().generate_content(prompt)
        res = parse_json_from_ai(r.text)
        issue = res.get("issue") or _extract_issue(text, dept_key, language)
        location = res.get("location") or _extract_location(text, language)
        duration = res.get("duration") or _extract_duration(text, language)
        priority = (res.get("priority") or _classify_priority(dept_key, text, duration)).upper()
        if priority not in ("LOW", "MEDIUM", "HIGH"):
            priority = _classify_priority(dept_key, text, duration)

        needs_loc = bool(not location and dept_key in ("water", "streetlight", "road", "electricity", "municipal"))
        q_map = {
            "ta": "இந்த பிரச்சனை எந்த பகுதியில் உள்ளது?",
            "hi": "यह समस्या किस क्षेत्र या स्थान पर है?",
            "en": "Where is the issue located?"
        }
        follow_up = q_map.get(language, q_map["en"]) if needs_loc else None

        return {
            "issue": issue,
            "description": text.strip(),
            "location": location,
            "duration": duration,
            "priority": priority,
            "needs_location": needs_loc,
            "follow_up_question": follow_up,
        }
    except Exception as e:
        print(f"[Dhvaani] Gemini extract grievance error: {type(e).__name__}")
        return _fallback_extract_grievance_details(text, language, dept_key)


def _fallback_extract_grievance_details(text: str, language: str = "en", dept_key: Optional[str] = None) -> dict:
    location = _extract_location(text, language)
    duration = _extract_duration(text, language)
    priority = _classify_priority(dept_key, text, duration)
    issue = _extract_issue(text, dept_key, language)

    needs_loc = bool(not location and dept_key in ("water", "streetlight", "road", "electricity", "municipal"))
    q_map = {
        "ta": "இந்த பிரச்சனை எந்த பகுதியில் உள்ளது?",
        "hi": "यह समस्या किस क्षेत्र या स्थान पर है?",
        "en": "Where is the issue located?"
    }
    follow_up = q_map.get(language, q_map["en"]) if needs_loc else None

    return {
        "issue": issue,
        "description": text.strip(),
        "location": location,
        "duration": duration,
        "priority": priority,
        "needs_location": needs_loc,
        "follow_up_question": follow_up,
    }


# ──────────────────────────────────────────────
# GRIEVANCE DRAFT CREATION
# ──────────────────────────────────────────────

def draft_grievance_text(text: str, dept_key: str, dept_info: dict, language: str, details: Optional[dict] = None) -> dict:
    """
    Create a formal grievance draft.
    Gemini is used only for translation/formalization — NOT to invent dept details.
    """
    if details is None:
        details = extract_grievance_details(text, language, dept_key)
    if is_gemini_ready():
        return _gemini_draft_grievance(text, dept_key, dept_info, language, details)
    return _fallback_draft_grievance(text, dept_key, dept_info, details, language)


def _gemini_draft_grievance(text: str, dept_key: str, dept_info: dict, language: str, details: Optional[dict] = None) -> dict:
    lang_name = {"en": "English", "hi": "Hindi", "ta": "Tamil"}.get(language, "English")
    if details is None:
        details = _fallback_extract_grievance_details(text, language, dept_key)
    prompt = (
        f'You are Dhvaani, a grievance drafting assistant for Indian citizens.\n'
        f'User complaint ({lang_name}): "{text}"\n'
        f'Issue Title: {details["issue"]}\n'
        f'Location: {details["location"] or "Not specified"}\n'
        f'Duration: {details["duration"] or "Not specified"}\n'
        f'Routed to: {dept_info["name"]}\n'
        f'Priority: {details["priority"]}\n\n'
        f'Return ONLY valid JSON:\n'
        f'{{\n'
        f'  "complaint_title": "{details["issue"]}",\n'
        f'  "formal_complaint": "formal English complaint text (3-4 sentences). Do NOT claim government response times or invent details.",\n'
        f'  "complaint_tamil": "Tamil translation of formal_complaint",\n'
        f'  "complaint_hindi": "Hindi translation of formal_complaint",\n'
        f'  "department": "{dept_info["name"]}",\n'
        f'  "priority": "{details["priority"].lower()}",\n'
        f'  "priority_level": "{details["priority"]}",\n'
        f'  "location": "{details["location"] or ""}",\n'
        f'  "estimated_resolution": "{dept_info.get("avg_resolution_days", 7)} working days (estimate only)",\n'
        f'  "confirmation_prompt": "2 sentences in {lang_name} asking user to review and confirm the draft",\n'
        f'  "spoken_draft": "3-4 natural spoken sentences in {lang_name} summarizing the grievance draft"\n'
        f'}}'
    )
    try:
        r = get_model().generate_content(prompt)
        return parse_json_from_ai(r.text)
    except Exception as e:
        print(f"[Dhvaani] Gemini draft error: {type(e).__name__}")
        return _fallback_draft_grievance(text, dept_key, dept_info, details, language)


def _fallback_draft_grievance(text: str, dept_key: str, dept_info: dict, details: Optional[dict] = None, language: str = "en") -> dict:
    if details is None:
        details = _fallback_extract_grievance_details(text, language, dept_key)

    issue = details.get("issue", f"Grievance — {dept_info['name']}")
    loc_str = f" Location: {details['location']}." if details.get("location") else ""
    dur_str = f" Duration: {details['duration']}." if details.get("duration") else ""
    priority = details.get("priority", dept_info.get("priority", "medium").upper())
    summary_text = _build_grievance_summary(details, dept_info["name"], language)

    return {
        "complaint_title": issue,
        "formal_complaint": (
            f"I wish to bring the following issue to your attention: {text}.{loc_str}{dur_str} "
            f"This issue is affecting daily life and requires prompt attention. "
            f"I request that the concerned authority investigate and take appropriate action."
        ),
        "complaint_tamil": f"புகார்: {issue}. {text}.{loc_str}{dur_str}",
        "complaint_hindi": f"शिकायत: {issue}। {text}।{loc_str}{dur_str}",
        "department": dept_info["name"],
        "priority": priority.lower(),
        "priority_level": priority,
        "location": details.get("location"),
        "estimated_resolution": f"{dept_info.get('avg_resolution_days', 7)} working days (estimate only)",
        "confirmation_prompt": "Please review the grievance draft above. Is the information correct? Confirm to create the Dhvaani request.",
        "spoken_draft": summary_text,
    }


# ──────────────────────────────────────────────
# AUDIO TRANSCRIPTION
# ──────────────────────────────────────────────

def _sarvam_transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm", language_code: Optional[str] = None) -> str:
    """Transcribe speech using Sarvam AI (saaras:v3)."""
    if not is_sarvam_ready():
        return ""
    try:
        ext = ".webm" if "webm" in mime_type else ".wav" if "wav" in mime_type else ".mp3"
        files = {
            "file": (f"audio{ext}", audio_bytes, mime_type),
        }
        data = {
            "model": "saaras:v3",
        }
        if language_code and language_code != "auto":
            lang_map = {"ta": "ta-IN", "hi": "hi-IN", "en": "en-IN"}
            data["language_code"] = lang_map.get(language_code, language_code)
        
        headers = {
            "api-subscription-key": SARVAM_API_KEY
        }
        resp = requests.post("https://api.sarvam.ai/speech-to-text", headers=headers, files=files, data=data, timeout=20)
        if resp.status_code == 200:
            res_json = resp.json()
            return res_json.get("transcript", "").strip()
        else:
            print(f"[Dhvaani] Sarvam STT error {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"[Dhvaani] Sarvam STT exception: {e}")
    return ""


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm", language: str = "auto") -> str:
    """
    Transcribe audio using Sarvam STT (if available) or Gemini multimodal.
    Returns empty string on failure.
    """
    if is_sarvam_ready():
        sarvam_text = _sarvam_transcribe_audio(audio_bytes, mime_type, language)
        if sarvam_text:
            return sarvam_text

    if not is_gemini_ready():
        return ""
    try:
        model = get_model()
        r = model.generate_content([
            "Transcribe this audio exactly. The speaker may use Tamil, Hindi, or English. Return ONLY the transcribed text — no comments.",
            {"mime_type": mime_type, "data": audio_bytes},
        ])
        return r.text.strip()
    except Exception as e:
        print(f"[Dhvaani] Transcription error: {type(e).__name__}")
        return ""


def synthesize_speech(text: str, language: str = "en", speaker: Optional[str] = None) -> Optional[str]:
    """Generate audio using Sarvam Bulbul TTS (bulbul:v3). Returns base64 wav string."""
    if not is_sarvam_ready():
        return None
    try:
        lang_map = {"ta": "ta-IN", "hi": "hi-IN", "en": "en-IN"}
        target_lang = lang_map.get(language, "en-IN")
        if not speaker:
            speaker = "kavya" if target_lang in ("ta-IN", "hi-IN") else "priya"
        
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": [text[:500]],
            "target_language_code": target_lang,
            "speaker": speaker,
            "model": "bulbul:v3",
            "enable_preprocessing": True
        }
        resp = requests.post("https://api.sarvam.ai/text-to-speech", headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            res_json = resp.json()
            audios = res_json.get("audios", [])
            if audios:
                return audios[0]
        else:
            print(f"[Dhvaani] Sarvam TTS error {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"[Dhvaani] Sarvam TTS exception: {e}")
    return None


# ──────────────────────────────────────────────
# TRACKING ID GENERATOR
# ──────────────────────────────────────────────

def generate_tracking_id() -> str:
    """Generate a DHV-YYYYMMDD-XXXXXX tracking ID."""
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"DHV-{date_str}-{suffix}"


# ──────────────────────────────────────────────
# API ROUTES
# ──────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(str(static_path / "index.html"))


@app.get("/api/health")
async def health():
    """
    Health check endpoint.
    Reports backend status, database connectivity, storage availability, Gemini configuration, and Sarvam configuration.
    Does NOT expose any secrets, credentials, or private URLs.
    """
    gemini_status = "configured" if is_gemini_ready() else "not_configured"
    sarvam_status = "configured" if is_sarvam_ready() else "not_configured"
    openrouter_status = "configured" if is_openrouter_ready() else "not_configured"
    db_health = db.check_db_health()
    storage_configured = storage.is_blob_configured()

    return {
        "status": "online",
        "database": db_health.get("status", "unknown"),
        "database_type": db_health.get("type", "sqlite"),
        "storage": "configured" if storage_configured else "local_ready",
        "storage_type": "vercel_blob" if storage_configured else "local_disk",
        "gemini": gemini_status,
        "gemini_configured": is_gemini_ready(),
        "openrouter": openrouter_status,
        "openrouter_configured": is_openrouter_ready(),
        "openrouter_model": OPENROUTER_MODEL if is_openrouter_ready() else None,
        "sarvam": sarvam_status,
        "sarvam_configured": is_sarvam_ready(),
        "scheme_database": {
            "loaded": True,
            "count": len(GOVERNMENT_SCHEMES),
        },
        "department_database": {
            "loaded": True,
            "count": len(GRIEVANCE_DEPARTMENTS),
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "version": "1.8.0",
    }


@app.post("/api/tts")
async def text_to_speech_endpoint(req: TTSRequest):
    """Synthesize speech using Sarvam AI Bulbul TTS."""
    if not is_sarvam_ready():
        return JSONResponse(
            {"success": False, "message": "Sarvam AI TTS is not configured on this server."},
            status_code=503
        )
    text = req.text.strip()
    if not text:
        return JSONResponse(
            {"success": False, "message": "Text cannot be empty."},
            status_code=400
        )
    audio_b64 = synthesize_speech(text, req.language, req.speaker)
    if not audio_b64:
        return JSONResponse(
            {"success": False, "message": "Speech synthesis failed."},
            status_code=500
        )
    return {
        "success": True,
        "audio_base64": audio_b64,
        "content_type": "audio/wav",
        "language": req.language
    }


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = Form(default="auto")):
    """Transcribe voice input using Sarvam AI or Gemini multimodal."""
    try:
        data = await audio.read()
    except Exception:
        return JSONResponse(clean_error_response("Failed to read audio file", "Please try again."), status_code=400)

    if not data or len(data) < 100:
        return JSONResponse(
            {"success": False, "transcript": "", "message": "Audio too short. Please speak clearly and try again."},
            status_code=400,
        )

    if not is_gemini_ready() and not is_sarvam_ready():
        return JSONResponse(
            {"success": False, "transcript": "", "message": "AI transcription requires an API key. Please type your message instead."},
        )

    fn = audio.filename or ""
    if fn.endswith(".webm"):
        mime = "audio/webm"
    elif fn.endswith(".wav"):
        mime = "audio/wav"
    elif fn.endswith(".mp3"):
        mime = "audio/mp3"
    else:
        mime = audio.content_type or "audio/webm"

    transcript = transcribe_audio(data, mime, language=language)
    if not transcript:
        return JSONResponse({
            "success": False,
            "transcript": "",
            "message": "Could not transcribe your speech. Please speak clearly or type your message.",
        })

    return {"success": True, "transcript": transcript}


@app.post("/api/process")
async def process(request: TextQueryRequest):
    """
    Main query processing endpoint.
    Phase 3: Detects intent, uses session context, multi-signal scheme matching,
    returns match explanation, official source, and optional follow-up question.
    """
    text = request.text.strip()
    if not text:
        return JSONResponse(
            clean_error_response("Empty query", "Please type or speak your question."),
            status_code=400,
        )
    if len(text) > 1000:
        return JSONResponse(
            clean_error_response("Query too long", "Please keep your message under 1000 characters."),
            status_code=400,
        )

    # Step 1: Detect intent + extract user context
    try:
        detection = detect_intent(text)
    except Exception:
        detection = _fallback_detect_intent(text)

    lang = detection.get("language", request.language or "en")
    lang_name = detection.get("language_name", "English")
    intent = detection.get("intent", "unknown")
    confidence = detection.get("confidence", 0.5)
    detected_context = detection.get("user_context", {})

    # Phase 3: Merge with session context
    session_id = request.session_id
    user_context = merge_session_context(session_id, detected_context)
    # Store detected language in session too
    if session_id and lang:
        merged = SESSION_CONTEXT_STORE.get(session_id, {})
        merged["language"] = lang
        SESSION_CONTEXT_STORE[session_id] = merged

    # Step 2: Handle active draft awaiting location or low-confidence intent
    if session_id and session_id in SESSION_CONTEXT_STORE:
        sess_ctx = SESSION_CONTEXT_STORE[session_id]
        pending_gid = sess_ctx.get("pending_grievance_id")
        if pending_gid and pending_gid in GRIEVANCE_STORE and GRIEVANCE_STORE[pending_gid].get("status") == "draft":
            existing_g = GRIEVANCE_STORE[pending_gid]
            if not existing_g.get("location"):
                loc_cand = _extract_location(text, lang) or text.strip()
                # Check if this looks like a location response
                if loc_cand and len(loc_cand) < 100 and not any(k in normalize_text(text) for k in ["scheme", "yojana", "திட்டம்", "योजना"]):
                    existing_g["location"] = loc_cand
                    dept_name = existing_g.get("department", "Public Department")
                    details_upd = {
                        "issue": existing_g.get("issue", "Civic Grievance"),
                        "location": loc_cand,
                        "priority": existing_g.get("priority", "MEDIUM"),
                    }
                    summary_text = _build_grievance_summary(details_upd, dept_name, lang)
                    if "draft" in existing_g and isinstance(existing_g["draft"], dict):
                        existing_g["draft"]["spoken_draft"] = summary_text
                        existing_g["draft"]["location"] = loc_cand

                    return {
                        "intent": "grievance",
                        "language": lang,
                        "language_name": lang_name,
                        "confidence": 0.9,
                        "grievance_id": pending_gid,
                        "grievance": {
                            "issue": existing_g.get("issue"),
                            "category": existing_g.get("category"),
                            "department": existing_g.get("department"),
                            "description": existing_g.get("description"),
                            "location": loc_cand,
                            "priority": existing_g.get("priority"),
                            "language": existing_g.get("language"),
                            "status": "draft",
                        },
                        "issue": existing_g.get("issue"),
                        "category": existing_g.get("category"),
                        "department": existing_g.get("department"),
                        "description": existing_g.get("description"),
                        "location": loc_cand,
                        "priority": existing_g.get("priority"),
                        "draft": existing_g.get("draft", {}),
                        "status": "draft",
                        "submission_status": "draft",
                        "needs_location": False,
                        "follow_up_question": None,
                        "summary": summary_text,
                        "message": f"Updated location to '{loc_cand}'. Please review and confirm your Dhvaani request.",
                        "note": "This is a Dhvaani draft. No complaint has been submitted to the government yet.",
                    }

    # Step 2b: Handle low-confidence intent — ask for clarification
    if intent == "unknown" or confidence < 0.55:
        return {
            "intent": "unknown",
            "language": lang,
            "language_name": lang_name,
            "confidence": confidence,
            "detection": detection,
            "message": (
                "Dhvaani is not sure whether you are asking about a government scheme "
                "or reporting a problem. Could you please clarify?"
            ),
            "suggestions": [
                "Am I eligible for PM-KISAN?",
                "The street light near my house is not working",
                "How do I apply for Ayushman Bharat?",
                "The road has many potholes near my home",
            ],
        }

    # Step 3a: Scheme flow
    if intent == "scheme":
        matched = match_schemes(text, user_context)
        scheme_meta = build_scheme_matches_metadata(text, matched)
        response = build_scheme_response(text, matched, lang, user_context)

        # Phase 3: No-match handling
        if not matched:
            follow_up = _suggest_follow_up_question(user_context, lang)
            return {
                "intent": "scheme",
                "language": lang,
                "language_name": lang_name,
                "confidence": confidence,
                "detection": detection,
                "scheme_matches": [],
                "matched_scheme_count": 0,
                "response": response,
                "no_match": True,
                "follow_up_question": follow_up,
                "disclaimer": (
                    "I couldn't find a closely matching scheme. "
                    "Try describing your need differently, e.g. 'I am a farmer looking for crop insurance'."
                ),
            }

        # Phase 3: Follow-up question if useful context is missing
        follow_up = _suggest_follow_up_question(user_context, lang)

        return {
            "intent": "scheme",
            "language": lang,
            "language_name": lang_name,
            "confidence": confidence,
            "detection": detection,
            "scheme_matches": scheme_meta,
            "matched_scheme_count": len(matched),
            "response": response,
            "follow_up_question": follow_up,
            "session_id": session_id,
            "disclaimer": (
                "Information shown is from the Dhvaani verified scheme database. "
                "Eligibility shown here is informational — please verify with the official portal."
            ),
        }

    # Step 3b: Grievance flow
    if intent == "grievance":
        dept_key, dept_info, dept_confidence = match_department(text)

        # If department cannot be determined confidently, ask for clarification (Requirement 18)
        if dept_key is None or dept_confidence < 0.1:
            q_map = {
                "ta": "இது எந்த வகையான பிரச்சனை — தண்ணீர், மின்சாரம், சாலை, தெரு விளக்கு அல்லது வேறொன்றா?",
                "hi": "यह किस प्रकार की समस्या है — पानी, बिजली, सड़क, स्ट्रीट लाइट या कुछ और?",
                "en": "What kind of problem is it — water, electricity, road, streetlight, or something else?",
            }
            clarify_msg = q_map.get(lang, q_map["en"])
            return {
                "intent": "grievance",
                "language": lang,
                "language_name": lang_name,
                "confidence": confidence,
                "detection": detection,
                "clarification_needed": True,
                "message": clarify_msg,
                "follow_up_question": clarify_msg,
                "suggestions": [
                    "The street light near my house has not been working for 3 days",
                    "There is a pothole on the main road",
                    "No water supply since yesterday",
                    "The power has been cut for five hours",
                ],
            }

        # Extract structured details
        details = extract_grievance_details(text, lang, dept_key)

        # Create grievance draft
        draft = draft_grievance_text(text, dept_key, dept_info, lang, details)

        # Create an internal draft record (NOT submitted to government)
        internal_id = str(uuid.uuid4())[:8].upper()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        GRIEVANCE_STORE[internal_id] = {
            "id": internal_id,
            "intent": "grievance",
            "language": lang,
            "issue": details["issue"],
            "category": dept_key or "general",
            "department_key": dept_key,
            "department": dept_info["name"],
            "priority": details["priority"],
            "description": details["description"],
            "location": details["location"],
            "duration": details.get("duration"),
            "status": "draft",
            "submission_status": "draft",
            "original_text": text,
            "draft": draft,
            "created_at": now_iso,
            "portal": dept_info.get("portal", ""),
            "helpline": dept_info.get("helpline", ""),
        }
        db.save_or_update_request(GRIEVANCE_STORE[internal_id])

        # Store pending draft in session context
        if session_id:
            sess_dict = SESSION_CONTEXT_STORE.get(session_id, {})
            sess_dict["pending_grievance_id"] = internal_id
            SESSION_CONTEXT_STORE[session_id] = sess_dict

        structured_grievance = {
            "issue": details["issue"],
            "category": dept_key or "general",
            "department": dept_info["name"],
            "description": details["description"],
            "location": details["location"],
            "priority": details["priority"],
            "language": lang,
            "status": "draft",
        }

        return {
            "intent": "grievance",
            "language": lang,
            "language_name": lang_name,
            "confidence": confidence,
            "detection": detection,
            "grievance_id": internal_id,
            "grievance": structured_grievance,
            "issue": details["issue"],
            "department": dept_info["name"],
            "category": dept_key or "general",
            "priority": details["priority"],
            "description": details["description"],
            "location": details["location"],
            "duration": details.get("duration"),
            "department_confidence": round(dept_confidence, 2),
            "draft": draft,
            "portal": dept_info.get("portal", ""),
            "helpline": dept_info.get("helpline", ""),
            "status": "draft",
            "submission_status": "draft",
            "needs_location": details.get("needs_location", False),
            "follow_up_question": details.get("follow_up_question"),
            "summary": draft.get("spoken_draft"),
            "note": "This is a Dhvaani draft. No complaint has been submitted to the government yet.",
        }

    # Should not reach here, but handle gracefully
    return {
        "intent": "unknown",
        "language": lang,
        "language_name": lang_name,
        "message": "Dhvaani could not process your request. Please try again.",
        "suggestions": [
            "Am I eligible for PM-KISAN?",
            "The street light near my house is not working",
        ],
    }


@app.post("/api/edit-grievance")
@app.patch("/api/edit-grievance")
async def edit_grievance(request: GrievanceEditRequest):
    """
    Phase 4: Edit a grievance draft before confirmation.
    Allows user to modify issue, description, location, category, department, or priority.
    Does NOT regenerate the entire grievance unnecessarily.
    """
    gid = request.grievance_id
    if gid not in GRIEVANCE_STORE:
        raise HTTPException(
            status_code=404,
            detail={"error": "Grievance not found", "message": f"No draft found for ID '{gid}'."},
        )

    g = GRIEVANCE_STORE[gid]
    if g.get("status") != "draft":
        raise HTTPException(
            status_code=400,
            detail={"error": "Cannot edit", "message": "Only draft requests can be edited."},
        )

    if request.issue is not None:
        g["issue"] = request.issue.strip()
        if "draft" in g and isinstance(g["draft"], dict):
            g["draft"]["complaint_title"] = request.issue.strip()

    if request.description is not None:
        g["description"] = request.description.strip()
        if "draft" in g and isinstance(g["draft"], dict):
            g["draft"]["formal_complaint"] = request.description.strip()

    if request.location is not None:
        g["location"] = request.location.strip() if request.location.strip() else None
        if "draft" in g and isinstance(g["draft"], dict):
            g["draft"]["location"] = g["location"]

    if request.category is not None:
        g["category"] = request.category.strip()

    if request.department is not None:
        g["department"] = request.department.strip()

    if request.priority is not None:
        p = request.priority.strip().upper()
        if p in ("LOW", "MEDIUM", "HIGH"):
            g["priority"] = p
            if "draft" in g and isinstance(g["draft"], dict):
                g["draft"]["priority"] = p.lower()
                g["draft"]["priority_level"] = p

    # Rebuild summary
    dept_name = g.get("department", "Public Department")
    details = {
        "issue": g.get("issue", "Civic Grievance"),
        "location": g.get("location"),
        "priority": g.get("priority", "MEDIUM"),
    }
    lang = g.get("language", "en")
    summary = _build_grievance_summary(details, dept_name, lang)
    if "draft" in g and isinstance(g["draft"], dict):
        g["draft"]["spoken_draft"] = summary

    structured_grievance = {
        "issue": g.get("issue"),
        "category": g.get("category"),
        "department": g.get("department"),
        "description": g.get("description"),
        "location": g.get("location"),
        "priority": g.get("priority"),
        "language": g.get("language"),
        "status": g.get("status"),
    }
    db.save_or_update_request(g)

    return {
        "success": True,
        "grievance_id": gid,
        "grievance": structured_grievance,
        "issue": g.get("issue"),
        "category": g.get("category"),
        "department": g.get("department"),
        "description": g.get("description"),
        "location": g.get("location"),
        "priority": g.get("priority"),
        "draft": g.get("draft", {}),
        "summary": summary,
        "message": "Grievance draft updated successfully.",
        "note": "This is a Dhvaani draft. No complaint has been submitted to the government yet.",
    }


@app.post("/api/confirm-grievance")
async def confirm_grievance(request: GrievanceConfirmRequest):
    """
    Confirm or cancel a grievance draft.

    On confirmation:
    - status = "request_created"
    - submission_status = "ready_for_submission"
    - A Dhvaani Tracking ID is assigned (DHV-YYYYMMDD-XXXXXX).
    - An assisted official portal handoff payload is generated with pre-formatted complaint text.
    - Synchronized with SQLite database.

    IMPORTANT: This does NOT submit anything to any government portal.
    """
    gid = request.grievance_id
    if gid not in GRIEVANCE_STORE:
        # Check SQLite
        db_rec = db.get_request(gid)
        if db_rec:
            GRIEVANCE_STORE[gid] = db_rec
        else:
            raise HTTPException(
                status_code=404,
                detail={"error": "Grievance not found", "message": f"No draft found for ID '{gid}'. It may have expired."},
            )

    g = GRIEVANCE_STORE[gid]

    if not request.confirmed:
        g["status"] = "cancelled"
        g["submission_status"] = "cancelled"
        db.save_or_update_request(g)
        return {
            "success": True,
            "status": "cancelled",
            "message": "Your grievance draft has been cancelled. No request was created.",
        }

    # Generate Dhvaani tracking ID
    tracking_id = generate_tracking_id()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    dept_key = g.get("department_key", "municipal")
    dept_info = GRIEVANCE_DEPARTMENTS.get(dept_key, {})
    pathway = ServiceCatalog.get_submission_pathway(dept_key)

    formatted_complaint = (
        f"GRIEVANCE COMPLAINT DETAILS\n"
        f"Department: {g.get('department')}\n"
        f"Issue: {g.get('issue')}\n"
        f"Category: {g.get('category')}\n"
        f"Location: {g.get('location') or 'Not specified'}\n"
        f"Priority: {g.get('priority', 'MEDIUM')}\n"
        f"Details: {g.get('description')}\n"
        f"Prepared via Dhvaani Civic Assistant for official portal submission."
    )

    g.update({
        "status": "request_created",
        "submission_status": "ready_for_submission",
        "tracking_id": tracking_id,
        "dhvaani_request_id": tracking_id,
        "government_reference_id": None,
        "government_status": "Awaiting citizen submission on official portal",
        "submission_mode": "assisted_handoff",
        "official_portal": pathway["official_portal"],
        "portal_name": pathway["portal_name"],
        "official_application_url": pathway["application_url"],
        "status_tracking_url": pathway["status_tracking_url"],
        "official_helpline": pathway["helpline"],
        "copyable_complaint": formatted_complaint,
        "required_documents": pathway["required_documents"],
        "confirmed_at": now_iso,
    })
    if request.user_name:
        g["user_name"] = request.user_name
    if request.contact:
        g["contact"] = request.contact

    # Phase 7: Link any attachments uploaded during draft or session
    if request.attachment_ids:
        db.link_attachments_to_request(request.attachment_ids, tracking_id)
    # Migrate any attachments saved with dhvaani_request_id == gid
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE attachments SET dhvaani_request_id = ? WHERE dhvaani_request_id = ?", (tracking_id, gid))
    conn.commit()
    conn.close()

    attachments_meta = db.get_attachments_for_request(tracking_id)
    g["attachments"] = attachments_meta

    db.save_or_update_request(g)

    return {
        "success": True,
        "status": "request_created",
        "submission_status": "ready_for_submission",
        "tracking_id": tracking_id,
        "dhvaani_request_id": tracking_id,
        "government_reference_id": None,
        "government_status": "Awaiting citizen submission on official portal",
        "submission_mode": "assisted_handoff",
        "issue": g.get("issue", ""),
        "department": g.get("department", ""),
        "category": g.get("category", ""),
        "priority": g.get("priority", "MEDIUM"),
        "location": g.get("location", None),
        "description": g.get("description", ""),
        "portal": pathway["official_portal"],
        "portal_name": pathway["portal_name"],
        "official_portal": pathway["official_portal"],
        "official_application_url": pathway["application_url"],
        "status_tracking_url": pathway["status_tracking_url"],
        "helpline": pathway["helpline"],
        "estimated_resolution": f"{dept_info.get('avg_resolution_days', 7)} working days (estimate only)",
        "created_at": g.get("created_at", ""),
        "confirmed_at": g["confirmed_at"],
        "copyable_complaint": formatted_complaint,
        "required_documents": pathway["required_documents"],
        "attachments": attachments_meta,
        "attachment_count": len(attachments_meta),
        "message": (
            f"Your Dhvaani request has been created. Tracking ID: {tracking_id}. "
            "Use this ID to track your request in Dhvaani."
        ),
        "next_steps": [
            f"Dhvaani Tracking ID: {tracking_id}",
            f"Issue: {g.get('issue', 'Civic Grievance')}",
            f"Department: {g.get('department', '')}",
            f"Location: {g.get('location') or 'Not specified'}",
            f"Priority: {g.get('priority', 'MEDIUM')}",
            f"Estimated resolution: {dept_info.get('avg_resolution_days', 7)} working days (estimate only)",
            f"Helpline: {pathway['helpline']}",
            f"Official Portal: {pathway['portal_name']} ({pathway['official_portal']})",
            "Action: Copy your complaint summary and continue to the official portal to complete citizen submission.",
            "Note: This is a Dhvaani request. Official government submission will be supported in a future update.",
        ],
        "note": "This Dhvaani request has NOT been submitted to any government portal. Official submission will be available in a future update.",
    }


@app.get("/api/track/{gid}")
async def track_grievance(gid: str):
    """
    Track a Dhvaani request by its internal ID or Dhvaani Tracking ID.
    Looks up in memory and SQLite.
    Returns structured status — does NOT claim government processing.
    """
    # 1. Look up by internal ID in memory
    if gid in GRIEVANCE_STORE:
        return _build_tracking_response(GRIEVANCE_STORE[gid])

    # 2. Look up by DHV tracking ID in memory
    for g_id, g_data in GRIEVANCE_STORE.items():
        if g_data.get("tracking_id", "") == gid or g_data.get("dhvaani_request_id", "") == gid:
            return _build_tracking_response(g_data)

    # 3. Look up in SQLite
    db_rec = db.get_request(gid)
    if db_rec:
        GRIEVANCE_STORE[db_rec.get("grievance_id", gid)] = db_rec
        return _build_tracking_response(db_rec)

    return JSONResponse(
        {
            "success": False,
            "error": "Tracking ID not found",
            "message": f"No Dhvaani request found for '{gid}'. Please check the ID and try again.",
        },
        status_code=404,
    )


def _build_tracking_response(g: dict) -> dict:
    status_messages = {
        "draft": "Your grievance draft is awaiting confirmation.",
        "request_created": "Your Dhvaani request has been created. Use this ID to track your request in Dhvaani.",
        "cancelled": "This grievance draft was cancelled.",
    }
    gov_ref = g.get("government_reference_id")
    gov_status = g.get("government_status")

    if gov_ref:
        msg = f"Dhvaani Request: {g.get('tracking_id')}. Linked Government Reference: {gov_ref}. Official status is tracked directly on the official portal."
    else:
        msg = status_messages.get(g.get("status", ""), "Status unknown.")

    req_id = g.get("tracking_id") or g.get("grievance_id") or str(g.get("id", ""))
    attachments_meta = db.get_attachments_for_request(req_id)

    return {
        "tracking_id": g.get("tracking_id", g.get("id", "")),
        "dhvaani_request_id": g.get("tracking_id", g.get("id", "")),
        "government_reference_id": gov_ref,
        "government_status": gov_status,
        "submission_mode": g.get("submission_mode", "assisted_handoff"),
        "status": g.get("status", "unknown"),
        "submission_status": g.get("submission_status", "draft"),
        "issue": g.get("issue", ""),
        "department": g.get("department", ""),
        "category": g.get("category", ""),
        "priority": g.get("priority", "MEDIUM"),
        "location": g.get("location", None),
        "description": g.get("description", ""),
        "portal": g.get("official_portal") or g.get("portal", ""),
        "official_portal": g.get("official_portal") or g.get("portal", ""),
        "helpline": g.get("official_helpline") or g.get("helpline", ""),
        "created_at": g.get("created_at", ""),
        "confirmed_at": g.get("confirmed_at", None),
        "attachments": attachments_meta,
        "attachment_count": len(attachments_meta),
        "message": msg,
        "note": "This is a Dhvaani internal request. It has not been submitted to any government portal. Dhvaani request ID is separate from official government reference numbers.",
    }


@app.get("/api/schemes")
async def list_schemes():
    """Return a summary list of all verified schemes in the database. Phase 6: verified service metadata."""
    return {
        "count": len(GOVERNMENT_SCHEMES),
        "schemes": [
            {
                "id": s["id"],
                "scheme_id": s.get("scheme_id", s["id"]),
                "name": s["name"],
                "official_name": s.get("official_name", s["name"]),
                "local_names": s.get("local_names", {"hi": s.get("name_hindi", ""), "ta": s.get("name_tamil", "")}),
                "category": s["category"],
                "state": s.get("state", "India"),
                "benefit": s.get("benefit", ""),
                "benefits": s.get("benefits", s.get("benefit", "")),
                "helpline": s.get("helpline", ""),
                "official_helpline": s.get("official_helpline", s.get("helpline", "")),
                "official_source": s.get("official_source", ""),
                "official_source_url": s.get("official_source_url", s.get("official_source", "")),
                "application_url": s.get("application_url", ""),
                "status_url": s.get("status_url", ""),
                "official_application_url": s.get("official_application_url", s.get("official_source", "")),
                "official_information_url": s.get("official_information_url", s.get("official_source", "")),
                "ministry_or_department": s.get("ministry_or_department", s.get("ministry", "")),
                "source_type": s.get("source_type", "central_portal"),
                "source_url": s.get("source_url", s.get("official_source", "")),
                "last_verified": s.get("last_verified", "2024-11-15"),
                "verification_status": s.get("verification_status", "verified"),
                "verified": s.get("verified", True),
                # Phase 3 fields
                "target_groups": s.get("target_groups", []),
                "occupation": s.get("occupation", []),
                "age_min": s.get("age_min"),
                "age_max": s.get("age_max"),
                "gender": s.get("gender", []),
                "income_limit": s.get("income_limit"),
                "required_documents": s.get("required_documents", s.get("documents", [])),
                "application_steps": s.get("application_steps", []),
            }
            for s in GOVERNMENT_SCHEMES
        ],
    }


@app.post("/api/link-government-ref")
async def link_government_ref(payload: LinkGovernmentRefRequest):
    """
    Link a genuine government reference ID (from SMS or official portal confirmation)
    to an existing Dhvaani request.
    """
    tid = payload.tracking_id.strip()
    gov_ref = payload.government_reference_id.strip()
    if not gov_ref:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid reference ID", "message": "Government reference ID cannot be empty."}
        )

    # Check memory first
    target_g = None
    for g in GRIEVANCE_STORE.values():
        if g.get("tracking_id") == tid or g.get("id") == tid:
            target_g = g
            break

    if not target_g:
        db_rec = db.get_request(tid)
        if db_rec:
            target_g = db_rec
            GRIEVANCE_STORE[db_rec.get("grievance_id", tid)] = target_g

    if not target_g:
        raise HTTPException(
            status_code=404,
            detail={"error": "Request not found", "message": f"No Dhvaani request found for tracking ID '{tid}'."}
        )

    target_g["government_reference_id"] = gov_ref
    target_g["government_status"] = "Reference linked by citizen"
    db.save_or_update_request(target_g)

    return {
        "success": True,
        "tracking_id": tid,
        "dhvaani_request_id": target_g.get("tracking_id"),
        "government_reference_id": gov_ref,
        "government_status": "Reference linked by citizen",
        "message": f"Official government reference '{gov_ref}' linked successfully to request '{tid}'.",
        "official_tracking_url": target_g.get("official_portal") or "https://pgportal.gov.in/Status",
        "note": "Dhvaani stores your government reference ID for your convenience. Official status updates are maintained on the government portal."
    }


@app.get("/api/services")
async def list_services():
    """
    Return the verified service catalog containing all verified schemes
    and civic grievance pathways with authoritative sources.
    """
    schemes = [
        {
            "id": s["id"],
            "scheme_id": s.get("scheme_id", s["id"]),
            "official_name": s.get("official_name", s["name"]),
            "local_names": s.get("local_names", {"hi": s.get("name_hindi", ""), "ta": s.get("name_tamil", "")}),
            "service_type": "scheme",
            "category": s["category"],
            "state": s.get("state", "India"),
            "benefits": s.get("benefits", s.get("benefit", "")),
            "eligibility": s.get("eligibility", []),
            "exclusions": s.get("exclusions", s.get("not_eligible", [])),
            "required_documents": s.get("required_documents", s.get("documents", [])),
            "official_source": s.get("official_source", ""),
            "official_source_url": s.get("official_source_url", s.get("official_source", "")),
            "application_url": s.get("application_url", ""),
            "status_url": s.get("status_url", ""),
            "official_application_url": s.get("official_application_url", s.get("official_source", "")),
            "official_information_url": s.get("official_information_url", s.get("official_source", "")),
            "official_helpline": s.get("official_helpline", s.get("helpline", "")),
            "ministry_or_department": s.get("ministry_or_department", s.get("ministry", "")),
            "submission_mode": "official_portal",
            "source_type": s.get("source_type", "central_portal"),
            "source_url": s.get("source_url", s.get("official_source", "")),
            "last_verified": s.get("last_verified", "2024-11-15"),
            "verification_status": s.get("verification_status", "verified"),
        }
        for s in GOVERNMENT_SCHEMES
    ]

    grievance_services = ServiceCatalog.list_grievance_services()

    return {
        "count": len(schemes) + len(grievance_services),
        "schemes_count": len(schemes),
        "grievance_services_count": len(grievance_services),
        "schemes": schemes,
        "grievance_services": grievance_services,
        "verification_standards": {
            "source_authority": "Official gov.in and nic.in domains",
            "no_invented_data": True,
            "submission_modes": ["assisted_handoff", "official_portal", "api", "information_only"],
        }
    }


@app.get("/api/services/{service_id}")
async def get_service_details(service_id: str):
    """Get authoritative metadata for a single service or scheme."""
    # Check schemes first
    for s in GOVERNMENT_SCHEMES:
        if s["id"] == service_id or s.get("scheme_id") == service_id:
            return {
                "success": True,
                "service_type": "scheme",
                "service": s,
            }

    # Check grievance services
    svc = ServiceCatalog.get_service(service_id)
    if svc:
        return {
            "success": True,
            "service_type": "grievance",
            "service": svc.to_dict(),
        }

    raise HTTPException(
        status_code=404,
        detail={"error": "Service not found", "message": f"No verified service found for ID '{service_id}'."}
    )


@app.get("/api/services/{service_id}/status/{government_reference_id}")
async def get_government_service_status(service_id: str, government_reference_id: str):
    """
    Truthful government service status lookup.
    Checks whether an unauthenticated public API exists for this service.
    If no unauthenticated status API exists (due to citizen privacy and OTP/CAPTCHA requirements),
    truthfully provides the official tracking URL and steps without fabricating statuses.
    """
    svc = ServiceCatalog.get_service(service_id)
    tracking_url = "https://pgportal.gov.in/Status"
    portal_name = "Central Public Grievance Portal"
    authority = "Competent Government Authority"
    truthful_notes = "Official government portals mandate citizen authentication (OTP / CAPTCHA) to view complaint remarks."

    if svc:
        tracking_url = svc.official_info.status_tracking_url or svc.official_info.portal_url
        portal_name = svc.official_info.portal_name
        authority = svc.identity.department
        truthful_notes = svc.verification.truthful_notes

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return {
        "success": True,
        "service_id": service_id,
        "government_reference_id": government_reference_id,
        "authority": authority,
        "status_check_mode": "official_portal_lookup",
        "current_status": "Government status is available on the official portal.",
        "official_tracking_url": tracking_url,
        "portal_name": portal_name,
        "source": tracking_url,
        "last_updated": now_iso,
        "timestamp": now_iso,
        "instructions": (
            f"Visit {portal_name} ({tracking_url}) and enter your reference ID '{government_reference_id}' "
            "to view the live remarks and officer action history."
        ),
        "truthful_notes": truthful_notes,
    }


@app.post("/api/session-context")
async def update_session_context(request: SessionContextUpdate):
    """
    Phase 3: Update the session context for a given session ID.
    Used by the frontend to accumulate user context across turns.
    Does NOT store personal identifiers or sensitive data.
    """
    allowed_keys = {"occupation", "state", "age", "gender", "need",
                    "category", "child_age", "child_gender", "language"}
    filtered = {k: v for k, v in request.context.items() if k in allowed_keys}
    session_id = request.session_id
    existing = SESSION_CONTEXT_STORE.get(session_id, {})
    merged = {**existing, **{k: v for k, v in filtered.items() if v is not None}}
    SESSION_CONTEXT_STORE[session_id] = merged
    return {
        "success": True,
        "session_id": session_id,
        "context_keys": list(merged.keys()),
        "note": "Context stored for this browser session only. No personal data is persisted.",
    }


@app.get("/api/session-context/{session_id}")
async def get_session_context_api(session_id: str):
    """Phase 3: Get the accumulated context for a session (for debugging)."""
    ctx = SESSION_CONTEXT_STORE.get(session_id, {})
    return {
        "session_id": session_id,
        "context_keys": list(ctx.keys()),
        "context": ctx,
    }


@app.post("/api/set-key")
async def set_api_key(request: SetKeyRequest):
    """
    Set or update the Gemini or Sarvam API key at runtime.
    The key is validated for format only — not exposed in logs.
    """
    global _gemini_ready, _sarvam_ready, GEMINI_API_KEY, SARVAM_API_KEY, OPENROUTER_API_KEY
    key = request.key.strip()
    if key.startswith("sk-or-"):
        OPENROUTER_API_KEY = key
        return {"success": True, "message": "OpenRouter API key configured. Gemini reasoning enabled via OpenRouter."}

    if key.startswith("sk_"):
        SARVAM_API_KEY = key
        _sarvam_ready = True
        return {"success": True, "message": "Sarvam API key configured. Indian speech (STT/TTS) features enabled."}

    if not (key.startswith("AIza") or key.startswith("AQ.") or len(key) >= 30):
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid API key format", "message": "Gemini keys start with 'AIza' or 'AQ.', OpenRouter keys start with 'sk-or-', and Sarvam keys start with 'sk_'."},
        )
    GEMINI_API_KEY = key
    genai.configure(api_key=GEMINI_API_KEY)
    _gemini_ready = True
    return {"success": True, "message": "Gemini API key configured. AI features enabled."}



# ──────────────────────────────────────────────
# ATTACHMENT ENDPOINTS (Phase 7)
# ──────────────────────────────────────────────

def _sanitize_original_filename(name: str) -> str:
    """Sanitize user-supplied filename for safe metadata storage only."""
    # Keep only basename, remove path components
    name = os.path.basename(name.strip())
    # Strip dangerous characters, keep alphanumeric, dash, underscore, dot
    name = re.sub(r"[^\w.\-]", "_", name)
    # Limit length
    return name[:120] if name else "upload"


def _get_file_extension(filename: str) -> str:
    """Return lowercase extension including leading dot."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def _validate_upload(file: UploadFile, data: bytes) -> Optional[str]:
    """
    Validate a single uploaded file.
    Returns an error string if invalid, or None if valid.
    - NEVER executes uploaded files.
    - Validates MIME type against allowed list.
    - Validates extension against allowed list.
    - Validates file size.
    - Prevents path traversal.
    """
    if not file.filename:
        return "Filename is required."

    # Block path traversal attempts in filename metadata
    if ".." in file.filename or file.filename.startswith("/") or file.filename.startswith("\\"):
        return "Invalid filename."

    ext = _get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        return (
            f"File type '{ext or 'unknown'}' is not allowed. "
            "Allowed: JPG, PNG, WEBP, PDF."
        )

    declared_mime = (file.content_type or "").split(";")[0].strip().lower()
    if declared_mime not in ALLOWED_MIME_TYPES:
        return (
            f"MIME type '{declared_mime}' is not allowed. "
            "Allowed: image/jpeg, image/png, image/webp, application/pdf."
        )

    # Verify declared extension matches declared MIME type
    if ext not in ALLOWED_MIME_TYPES.get(declared_mime, []):
        return "File extension and MIME type do not match."

    if len(data) > MAX_FILE_SIZE:
        size_mb = len(data) / (1024 * 1024)
        return f"File is too large ({size_mb:.1f} MB). Maximum allowed is 10 MB."

    if len(data) == 0:
        return "Uploaded file is empty."

    return None


@app.post("/api/attachments")
async def upload_attachments(
    files: List[UploadFile] = File(...),
    dhvaani_request_id: Optional[str] = Form(default=None),
):
    """
    Phase 7: Upload evidence files (photos / PDFs) for a Dhvaani grievance.

    Security:
    - Only JPG, PNG, WEBP, PDF allowed (by MIME + extension).
    - Maximum 10 MB per file, maximum 5 files per request.
    - Stored with a cryptographically random UUID filename — never the user-supplied name.
    - Original filename stored in metadata only (sanitized).
    - Upload directory is NEVER served as a public static folder.
    - No file is ever executed.
    - No path traversal possible (all paths resolved via UPLOAD_DIR).

    Returns attachment metadata. Does NOT claim files were submitted to government.
    """
    if not files or len(files) == 0:
        return JSONResponse(
            {"success": False, "error": "No files provided."},
            status_code=400,
        )
    if len(files) > MAX_FILES_PER_REQUEST:
        return JSONResponse(
            {"success": False, "error": f"Maximum {MAX_FILES_PER_REQUEST} files per upload."},
            status_code=400,
        )

    saved = []
    errors = []

    for f in files:
        try:
            data = await f.read()
        except Exception:
            errors.append({"filename": f.filename, "error": "Could not read file."})
            continue

        validation_error = _validate_upload(f, data)
        if validation_error:
            errors.append({"filename": _sanitize_original_filename(f.filename or ""), "error": validation_error})
            continue

        # Generate secure stored filename — NEVER use user-supplied name as storage path
        attachment_id = str(uuid.uuid4())
        ext = _get_file_extension(f.filename)
        stored_filename = f"{attachment_id}{ext}"

        # Resolve absolute path and verify it stays within UPLOAD_DIR
        dest_path = (UPLOAD_DIR / stored_filename).resolve()
        if not str(dest_path).startswith(str(UPLOAD_DIR.resolve())):
            errors.append({"filename": _sanitize_original_filename(f.filename), "error": "Path traversal blocked."})
            continue

        local_saved = False
        try:
            dest_path.write_bytes(data)
            local_saved = True
        except Exception:
            # Serverless fallback to /tmp
            try:
                tmp_path = Path("/tmp/uploads") / stored_filename
                tmp_path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path.write_bytes(data)
                local_saved = True
            except Exception:
                pass

        # Vercel Blob cloud upload when token is configured
        blob_url = None
        if storage.is_blob_configured():
            blob_url = storage.upload_to_blob(
                stored_filename, data, (f.content_type or "").split(";")[0].strip()
            )

        if not local_saved and not blob_url:
            errors.append({"filename": _sanitize_original_filename(f.filename), "error": "Could not save file to storage."})
            continue

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        meta = {
            "attachment_id": attachment_id,
            "dhvaani_request_id": dhvaani_request_id or None,
            "original_filename": _sanitize_original_filename(f.filename),
            "stored_filename": stored_filename,
            "content_type": (f.content_type or "").split(";")[0].strip(),
            "file_size": len(data),
            "created_at": now_iso,
            "blob_url": blob_url,
        }
        try:
            db.save_attachment(meta)
        except Exception as e:
            print(f"[Dhvaani] Attachment DB error: {e}")
            if blob_url:
                storage.delete_from_blob(blob_url)
            try:
                dest_path.unlink(missing_ok=True)
            except Exception:
                pass
            errors.append({"filename": meta["original_filename"], "error": "Database error saving attachment."})
            continue

        saved.append({
            "attachment_id": attachment_id,
            "original_filename": meta["original_filename"],
            "content_type": meta["content_type"],
            "file_size": len(data),
            "created_at": now_iso,
            "dhvaani_request_id": dhvaani_request_id,
            "blob_url": blob_url,
        })

    if not saved and errors:
        return JSONResponse(
            {"success": False, "error": "All uploads failed.", "details": errors},
            status_code=422,
        )

    return {
        "success": True,
        "saved": saved,
        "saved_count": len(saved),
        "errors": errors,
        "note": "Attachments are stored by Dhvaani only. They have NOT been submitted to any government portal.",
    }


@app.delete("/api/attachments/{attachment_id}")
async def delete_attachment_endpoint(attachment_id: str):
    """
    Phase 7: Remove an uploaded attachment by its attachment_id.
    Deletes both the on-disk/blob file and the database record.
    """
    # Validate attachment_id is a UUID to prevent path traversal
    try:
        uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid attachment ID format."},
        )

    success, row = db.delete_attachment(attachment_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail={"error": "Attachment not found.", "attachment_id": attachment_id},
        )

    # Remove from Vercel Blob if stored in cloud
    if row and row.get("blob_url"):
        storage.delete_from_blob(row["blob_url"])

    # Remove the physical file
    if row and row.get("stored_filename"):
        stored = row["stored_filename"]
        # Safety: ensure stored_filename is just a basename
        stored_safe = os.path.basename(stored)
        dest_path = (UPLOAD_DIR / stored_safe).resolve()
        if str(dest_path).startswith(str(UPLOAD_DIR.resolve())):
            try:
                dest_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"[Dhvaani] Attachment file delete error: {e}")


    return {
        "success": True,
        "attachment_id": attachment_id,
        "message": "Attachment removed.",
    }


@app.get("/api/attachments")
async def list_attachments(dhvaani_request_id: str):
    """Phase 7: List all attachment metadata for a given Dhvaani request."""
    records = db.get_attachments_for_request(dhvaani_request_id)
    return {
        "success": True,
        "dhvaani_request_id": dhvaani_request_id,
        "attachments": records,
        "count": len(records),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
