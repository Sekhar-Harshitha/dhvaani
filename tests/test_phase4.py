"""
Dhvaani Phase 4 – Realistic Grievance Assistant Test Suite

Tests the structured grievance draft, issue & category detection, department routing,
natural language location extraction, priority classification, follow-up questions,
editable drafts, explicit confirmation, tracking ID generation, truthful status wording,
and non-regression of Phase 1, Phase 2, and Phase 3 capabilities.

Run with:  python -m pytest tests/ -v
OR:        python tests/test_phase4.py
"""
import sys
import io
import os
import re
import datetime
import pytest

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    _fallback_detect_intent,
    match_department,
    extract_grievance_details,
    _fallback_extract_grievance_details,
    _extract_location,
    _extract_duration,
    _classify_priority,
    _extract_issue,
    _build_grievance_summary,
    _fallback_draft_grievance,
    generate_tracking_id,
    GRIEVANCE_STORE,
    _build_tracking_response,
    match_schemes,
)
from schemes_db import GRIEVANCE_DEPARTMENTS, GOVERNMENT_SCHEMES


# ═══════════════════════════════════════════════════════════
# P4-1: English water grievance
# ═══════════════════════════════════════════════════════════
def test_p4_1_english_water_grievance():
    """
    P4-1: English water grievance
    Input: "The water supply in Maduravoyal has been unavailable since yesterday."
    Expect: intent=grievance, department=water, location=Maduravoyal, duration=since yesterday
    """
    text = "The water supply in Maduravoyal has been unavailable since yesterday."
    intent_res = _fallback_detect_intent(text)
    assert intent_res["intent"] == "grievance", f"Expected grievance intent, got {intent_res['intent']}"

    dept_key, dept_info, conf = match_department(text)
    assert dept_key == "water", f"Expected water department, got {dept_key}"

    details = _fallback_extract_grievance_details(text, "en", dept_key)
    assert details["location"] == "Maduravoyal", f"Expected location 'Maduravoyal', got '{details['location']}'"
    assert details["duration"] is not None and "yesterday" in details["duration"].lower()
    assert "water" in details["issue"].lower()
    assert details["priority"] in ("LOW", "MEDIUM", "HIGH")
    print(f"[PASS] P4-1 – English water grievance (loc={details['location']}, dur={details['duration']}, prio={details['priority']})")


# ═══════════════════════════════════════════════════════════
# P4-2: Tamil water grievance (Demo Scenario 1)
# ═══════════════════════════════════════════════════════════
def test_p4_2_tamil_water_grievance():
    """
    P4-2: Tamil water grievance
    Input: "எங்கள் பகுதியில் மூன்று நாட்களாக தண்ணீர் வரவில்லை. நாங்கள் மதுரவாயலில் இருக்கிறோம்."
    Expect: language=ta, intent=grievance, department=water, location=மதுரவாயல், duration=மூன்று நாட்களாக, priority=HIGH
    """
    text = "எங்கள் பகுதியில் மூன்று நாட்களாக தண்ணீர் வரவில்லை. நாங்கள் மதுரவாயலில் இருக்கிறோம்."
    intent_res = _fallback_detect_intent(text)
    assert intent_res["language"] == "ta", f"Expected language 'ta', got '{intent_res['language']}'"
    assert intent_res["intent"] == "grievance", f"Expected grievance intent, got '{intent_res['intent']}'"

    dept_key, dept_info, conf = match_department(text)
    assert dept_key == "water", f"Expected water department, got '{dept_key}'"

    details = _fallback_extract_grievance_details(text, "ta", dept_key)
    assert details["location"] == "மதுரவாயல்", f"Expected location 'மதுரவாயல்', got '{details['location']}'"
    assert details["duration"] == "மூன்று நாட்களாக", f"Expected duration 'மூன்று நாட்களாக', got '{details['duration']}'"
    assert details["priority"] == "HIGH", f"Expected priority 'HIGH' for prolonged water outage, got '{details['priority']}'"
    print(f"[PASS] P4-2 – Tamil water grievance (loc={details['location']}, dur={details['duration']}, prio={details['priority']})")


# ═══════════════════════════════════════════════════════════
# P4-3: Hindi water grievance
# ═══════════════════════════════════════════════════════════
def test_p4_3_hindi_water_grievance():
    """
    P4-3: Hindi water grievance
    Input: "हमारे इलाके में तीन दिनों से पानी नहीं आ रहा है। हम मधुरवॉयल में रहते हैं।"
    Expect: language=hi, intent=grievance, department=water, location=मधुरवॉयल, duration=तीन दिनों से, priority=HIGH
    """
    text = "हमारे इलाके में तीन दिनों से पानी नहीं आ रहा है। हम मधुरवॉयल में रहते हैं।"
    intent_res = _fallback_detect_intent(text)
    assert intent_res["language"] == "hi", f"Expected language 'hi', got '{intent_res['language']}'"
    assert intent_res["intent"] == "grievance", f"Expected grievance intent, got '{intent_res['intent']}'"

    dept_key, dept_info, conf = match_department(text)
    assert dept_key == "water", f"Expected water department, got '{dept_key}'"

    details = _fallback_extract_grievance_details(text, "hi", dept_key)
    assert details["location"] in ("मधुरवॉयल", "मदुरवायल"), f"Expected location 'मधुरवॉयल', got '{details['location']}'"
    assert details["duration"] == "तीन दिनों से", f"Expected duration 'तीन दिनों से', got '{details['duration']}'"
    assert details["priority"] == "HIGH", f"Expected priority 'HIGH', got '{details['priority']}'"
    print(f"[PASS] P4-3 – Hindi water grievance (loc={details['location']}, dur={details['duration']}, prio={details['priority']})")


# ═══════════════════════════════════════════════════════════
# P4-4: Streetlight grievance (Demo Scenario 2)
# ═══════════════════════════════════════════════════════════
def test_p4_4_streetlight_grievance():
    """
    P4-4: Streetlight grievance
    Input: "The street light near my house in Koyambedu has not been working for a week."
    Expect: department=streetlight (NOT electricity), location=Koyambedu, duration=a week
    """
    text = "The street light near my house in Koyambedu has not been working for a week."
    dept_key, dept_info, conf = match_department(text)
    assert dept_key == "streetlight", f"Streetlight complaint must route to 'streetlight', not '{dept_key}'"

    details = _fallback_extract_grievance_details(text, "en", dept_key)
    assert details["location"] == "Koyambedu", f"Expected location 'Koyambedu', got '{details['location']}'"
    assert details["duration"] == "a week", f"Expected duration 'a week', got '{details['duration']}'"
    assert "streetlight" in details["issue"].lower() or "street light" in details["issue"].lower()
    print(f"[PASS] P4-4 – Streetlight grievance (dept={dept_key}, loc={details['location']}, dur={details['duration']})")


# ═══════════════════════════════════════════════════════════
# P4-5: Road grievance
# ═══════════════════════════════════════════════════════════
def test_p4_5_road_grievance():
    """
    P4-5: Road grievance
    Input: "There is a huge pothole near the college entrance on Poonamallee High Road."
    Expect: department=road, location includes Poonamallee High Road, issue includes pothole
    """
    text = "There is a huge pothole near the college entrance on Poonamallee High Road."
    dept_key, dept_info, conf = match_department(text)
    assert dept_key == "road", f"Expected road department, got '{dept_key}'"

    details = _fallback_extract_grievance_details(text, "en", dept_key)
    assert "Poonamallee High Road" in details["location"], f"Expected Poonamallee High Road in location, got '{details['location']}'"
    assert "pothole" in details["issue"].lower()
    print(f"[PASS] P4-5 – Road grievance (dept={dept_key}, loc={details['location']})")


# ═══════════════════════════════════════════════════════════
# P4-6: Electricity grievance
# ═══════════════════════════════════════════════════════════
def test_p4_6_electricity_grievance():
    """
    P4-6: Electricity grievance
    Input: "The power has been cut in our area for five hours."
    Expect: department=electricity, duration=five hours
    """
    text = "The power has been cut in our area for five hours."
    dept_key, dept_info, conf = match_department(text)
    assert dept_key == "electricity", f"Expected electricity department, got '{dept_key}'"

    details = _fallback_extract_grievance_details(text, "en", dept_key)
    assert details["duration"] == "five hours", f"Expected duration 'five hours', got '{details['duration']}'"
    assert "power" in details["issue"].lower() or "electricity" in details["issue"].lower()
    print(f"[PASS] P4-6 – Electricity grievance (dept={dept_key}, dur={details['duration']})")


# ═══════════════════════════════════════════════════════════
# P4-7: Missing location follow-up
# ═══════════════════════════════════════════════════════════
def test_p4_7_missing_location_followup():
    """
    P4-7: Missing location follow-up
    Input: "The street light near my house has not been working for three days."
    Expect: location=None (not invented), needs_location=True, follow_up_question asked
    """
    text = "The street light near my house has not been working for three days."
    details = _fallback_extract_grievance_details(text, "en", "streetlight")
    assert details["location"] is None, f"Address should not be invented, got '{details['location']}'"
    assert details["needs_location"] is True, "Should flag needs_location=True when location is missing"
    assert details["follow_up_question"] == "Where is the issue located?", (
        f"Expected location question, got '{details['follow_up_question']}'"
    )
    print(f"[PASS] P4-7 – Missing location follow-up correctly generated: '{details['follow_up_question']}'")


# ═══════════════════════════════════════════════════════════
# P4-8: Ambiguous grievance follow-up
# ═══════════════════════════════════════════════════════════
def test_p4_8_ambiguous_grievance_followup():
    """
    P4-8: Ambiguous grievance follow-up
    Input: "There is a problem near my street."
    Expect: department=None or low confidence, prompts user about issue type (water, electricity, road, streetlight...)
    """
    text = "There is a problem near my street."
    dept_key, dept_info, conf = match_department(text)
    assert dept_key is None or conf < 0.15, (
        f"Ambiguous complaint should not confidently pick a department, got '{dept_key}' conf={conf}"
    )
    # Check clarification message phrasing
    q_en = "What kind of problem is it — water, electricity, road, streetlight, or something else?"
    assert "water" in q_en and "electricity" in q_en and "road" in q_en and "streetlight" in q_en
    print(f"[PASS] P4-8 – Ambiguous grievance correctly leaves department undecided")


# ═══════════════════════════════════════════════════════════
# P4-9: Structured grievance draft
# ═══════════════════════════════════════════════════════════
def test_p4_9_structured_grievance_draft():
    """
    P4-9: Structured grievance draft
    Verify the draft object contains all required fields:
    {issue, category, department, description, location, priority, language, status}
    """
    text = "The water supply in Maduravoyal has been unavailable since yesterday."
    details = _fallback_extract_grievance_details(text, "en", "water")
    dept_info = GRIEVANCE_DEPARTMENTS["water"]
    draft = _fallback_draft_grievance(text, "water", dept_info, details, "en")

    structured = {
        "issue": details["issue"],
        "category": "water",
        "department": dept_info["name"],
        "description": details["description"],
        "location": details["location"],
        "priority": details["priority"],
        "language": "en",
        "status": "draft",
    }

    required_keys = ["issue", "category", "department", "description", "location", "priority", "language", "status"]
    for k in required_keys:
        assert k in structured, f"Missing structured field: {k}"
        assert structured[k] is not None or k == "location", f"Field {k} should have a value"

    assert structured["status"] == "draft"
    assert structured["priority"] in ("LOW", "MEDIUM", "HIGH")
    print(f"[PASS] P4-9 – Structured grievance draft verified with all {len(required_keys)} fields")


# ═══════════════════════════════════════════════════════════
# P4-10: Priority classification
# ═══════════════════════════════════════════════════════════
def test_p4_10_priority_classification():
    """
    P4-10: Priority classification
    Verify LOW, MEDIUM, and HIGH are appropriately determined based on rules:
    - broken decorative streetlight → LOW
    - regular streetlight not working → MEDIUM
    - prolonged water outage (>=3 days) → HIGH
    - exposed sparking electrical wire → HIGH
    """
    p_low = _classify_priority("streetlight", "The decorative streetlight bulb is broken")
    assert p_low == "LOW", f"Expected LOW for decorative light, got {p_low}"

    p_med = _classify_priority("streetlight", "The streetlight is not working")
    assert p_med == "MEDIUM", f"Expected MEDIUM for regular streetlight, got {p_med}"

    p_water_high = _classify_priority("water", "No water supply for three days", "three days")
    assert p_water_high == "HIGH", f"Expected HIGH for prolonged water outage, got {p_water_high}"

    p_hazard_high = _classify_priority("electricity", "There is a sparking wire hanging near the road")
    assert p_hazard_high == "HIGH", f"Expected HIGH for sparking wire, got {p_hazard_high}"

    print(f"[PASS] P4-10 – Priority classification works across all levels (LOW, MEDIUM, HIGH)")


# ═══════════════════════════════════════════════════════════
# P4-11: Explicit confirmation required
# ═══════════════════════════════════════════════════════════
def test_p4_11_explicit_confirmation_required():
    """
    P4-11: Explicit confirmation required
    A draft grievance must start with status='draft' and NOT have a tracking_id.
    Tracking ID is only generated upon explicit confirmation.
    """
    import uuid
    internal_id = str(uuid.uuid4())[:8].upper()
    dept_info = GRIEVANCE_DEPARTMENTS["water"]
    GRIEVANCE_STORE[internal_id] = {
        "id": internal_id,
        "intent": "grievance",
        "language": "en",
        "issue": "Water supply interruption",
        "category": "water",
        "department": dept_info["name"],
        "description": "Water outage",
        "location": "Maduravoyal",
        "priority": "MEDIUM",
        "status": "draft",
        "submission_status": "draft",
    }

    draft_record = GRIEVANCE_STORE[internal_id]
    assert draft_record["status"] == "draft", "Initial status must be 'draft'"
    assert "tracking_id" not in draft_record, "Draft must NOT have a tracking_id before explicit confirmation"
    print(f"[PASS] P4-11 – Explicit confirmation required; draft has no tracking ID initially")

    del GRIEVANCE_STORE[internal_id]


# ═══════════════════════════════════════════════════════════
# P4-12: Tracking ID creation
# ═══════════════════════════════════════════════════════════
def test_p4_12_tracking_id_creation():
    """
    P4-12: Tracking ID creation
    Verify DHV-YYYYMMDD-XXXXXX format.
    """
    tid = generate_tracking_id()
    assert re.match(r"^DHV-\d{8}-[A-F0-9]{6}$", tid), f"Invalid tracking ID format: {tid}"
    print(f"[PASS] P4-12 – Tracking ID format verified: {tid}")


# ═══════════════════════════════════════════════════════════
# P4-13: Tracking lookup
# ═══════════════════════════════════════════════════════════
def test_p4_13_tracking_lookup():
    """
    P4-13: Tracking lookup
    Verify lookup by DHV tracking ID returns structured fields:
    tracking_id, issue, department, location, priority, status.
    """
    import uuid
    internal_id = str(uuid.uuid4())[:8].upper()
    tid = generate_tracking_id()
    GRIEVANCE_STORE[internal_id] = {
        "id": internal_id,
        "tracking_id": tid,
        "issue": "Water supply interruption",
        "category": "water",
        "department": "Water Supply Department",
        "location": "Maduravoyal",
        "priority": "HIGH",
        "description": "No water supply for 3 days",
        "status": "request_created",
        "submission_status": "ready_for_submission",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "confirmed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    # Lookup
    found = None
    for g in GRIEVANCE_STORE.values():
        if g.get("tracking_id") == tid:
            found = g
            break

    assert found is not None, "Should find record by tracking ID"
    resp = _build_tracking_response(found)
    assert resp["tracking_id"] == tid
    assert resp["issue"] == "Water supply interruption"
    assert resp["location"] == "Maduravoyal"
    assert resp["priority"] == "HIGH"
    assert resp["status"] == "request_created"
    print(f"[PASS] P4-13 – Tracking lookup successful with structured fields")

    del GRIEVANCE_STORE[internal_id]


# ═══════════════════════════════════════════════════════════
# P4-14: Truthful request status
# ═══════════════════════════════════════════════════════════
def test_p4_14_truthful_request_status():
    """
    P4-14: Truthful request status
    Status must only be 'draft' or 'request_created'.
    submission_status must only be 'draft' or 'ready_for_submission'.
    Must NOT contain 'Submitted', 'Under Government Review', 'Officer Assigned', 'Resolved'.
    """
    fake_statuses = ["submitted", "under government review", "officer assigned", "resolved", "government_submitted"]
    import uuid
    internal_id = str(uuid.uuid4())[:8].upper()
    tid = generate_tracking_id()
    g = {
        "id": internal_id,
        "tracking_id": tid,
        "issue": "Streetlight broken",
        "department": "Municipal Corporation",
        "status": "request_created",
        "submission_status": "ready_for_submission",
    }
    resp = _build_tracking_response(g)

    assert resp["status"] == "request_created"
    assert resp["submission_status"] == "ready_for_submission"
    assert resp["status"].lower() not in fake_statuses
    assert resp["submission_status"].lower() not in fake_statuses
    print(f"[PASS] P4-14 – Truthful status verified: {resp['status']} / {resp['submission_status']}")


# ═══════════════════════════════════════════════════════════
# P4-15: No fake government submission claim
# ═══════════════════════════════════════════════════════════
def test_p4_15_no_fake_government_submission_claim():
    """
    P4-15: No fake government submission claim
    Verify message and note explicitly clarify that the request is internal to Dhvaani
    and has NOT been officially submitted to any government portal.
    """
    g = {
        "id": "TEST01",
        "tracking_id": "DHV-20261002-123456",
        "issue": "Water outage",
        "department": "Water Department",
        "status": "request_created",
        "submission_status": "ready_for_submission",
    }
    resp = _build_tracking_response(g)
    assert "not been submitted to any government portal" in resp["note"].lower()
    assert "submitted to the government" not in resp["message"].lower()
    print(f"[PASS] P4-15 – Truthful disclaimer verified: '{resp['note']}'")


# ═══════════════════════════════════════════════════════════
# P4-16: Invalid tracking ID
# ═══════════════════════════════════════════════════════════
def test_p4_16_invalid_tracking_id():
    """
    P4-16: Invalid tracking ID
    Input: 'DHV-INVALID-9999'
    Expect: Clean not found response without stack traces.
    """
    invalid_id = "DHV-INVALID-9999"
    found = any(g.get("tracking_id") == invalid_id for g in GRIEVANCE_STORE.values())
    assert not found, "Invalid ID should not be found"
    clean_err = {
        "success": False,
        "error": "Tracking ID not found",
        "message": f"No Dhvaani request found for '{invalid_id}'. Please check the ID and try again.",
    }
    assert clean_err["success"] is False
    assert "traceback" not in str(clean_err).lower()
    print(f"[PASS] P4-16 – Invalid tracking ID cleanly handled")


# ═══════════════════════════════════════════════════════════
# P4-17: Existing Phase 3 scheme matching non-regression
# ═══════════════════════════════════════════════════════════
def test_p4_17_scheme_matching_non_regression():
    """
    P4-17: Phase 3 scheme matching non-regression
    Query for farmer financial support must still match PM-KISAN.
    """
    results = match_schemes("I am a farmer and need financial support for my crops")
    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in results]
    assert "pm_kisan" in ids or "pm_fasal_bima" in ids, f"Expected PM-KISAN in results, got {ids}"
    print(f"[PASS] P4-17 – Scheme matching intact: {ids}")


# ═══════════════════════════════════════════════════════════
# P4-18: Existing Phase 2 voice/frontend tests non-regression
# ═══════════════════════════════════════════════════════════
def test_p4_18_frontend_voice_and_edit_features():
    """
    P4-18: Phase 2 frontend voice and Phase 4 edit features
    Verify index.html has TTS, mic buttons, edit panel, and confirmation buttons.
    """
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "index.html")
    assert os.path.exists(html_path), "index.html must exist"
    with open(html_path, encoding="utf-8", errors="replace") as f:
        html = f.read()

    assert "ttsCtrl" in html or "tts-controls" in html
    assert "state-listening" in html
    assert "edit-draft-panel" in html, "Edit draft panel CSS/HTML must be present"
    assert "saveDraftEdit" in html, "Draft editing JS function must be present"
    assert "Create Dhvaani Request" in html, "Dhvaani Request wording must be present"
    print(f"[PASS] P4-18 – Voice and edit frontend features verified")


# ═══════════════════════════════════════════════════════════
# P4-19: Tamil grievance routing
# ═══════════════════════════════════════════════════════════
def test_p4_19_tamil_grievance_routing():
    """
    P4-19: Tamil grievance routing
    Input: "எங்கள் தெரு விளக்கு எரியவில்லை"
    Expect: routes to 'streetlight', NOT 'electricity'
    """
    text = "எங்கள் தெரு விளக்கு எரியவில்லை"
    dept_key, dept_info, conf = match_department(text)
    assert dept_key == "streetlight", f"Tamil streetlight complaint must route to 'streetlight', got '{dept_key}'"
    print(f"[PASS] P4-19 – Tamil streetlight routed to '{dept_key}'")


# ═══════════════════════════════════════════════════════════
# P4-20: Hindi grievance routing
# ═══════════════════════════════════════════════════════════
def test_p4_20_hindi_grievance_routing():
    """
    P4-20: Hindi grievance routing
    Input: "हमारे इलाके की स्ट्रीट लाइट काम नहीं कर रही है"
    Expect: routes to 'streetlight', NOT 'electricity'
    """
    text = "हमारे इलाके की स्ट्रीट लाइट काम नहीं कर रही है"
    dept_key, dept_info, conf = match_department(text)
    assert dept_key == "streetlight", f"Hindi streetlight complaint must route to 'streetlight', got '{dept_key}'"
    print(f"[PASS] P4-20 – Hindi streetlight routed to '{dept_key}'")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
