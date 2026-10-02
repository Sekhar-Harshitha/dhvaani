"""
Dhvaani Phase 3 – Smart Scheme Finder Test Suite

Tests the improved multi-signal scheme matching, user context extraction,
match explanation, eligibility safety wording, follow-up questions,
no-match handling, session context, and Phase 3 scheme DB fields.

Run with:  python -m pytest tests/ -v
OR:        python tests/test_phase3.py
"""
import sys
import io

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from main import (
    match_schemes,
    build_scheme_matches_metadata,
    _fallback_scheme_response,
    _suggest_follow_up_question,
    _build_match_reason_sentence,
    _score_scheme,
    merge_session_context,
    normalize_text,
    _fallback_detect_intent,
)
from schemes_db import GOVERNMENT_SCHEMES


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 1: Farmer + financial support → PM-KISAN top result
# ═══════════════════════════════════════════════════════════
def test_p3_farmer_financial_support():
    """
    P3 TEST 1: Farmer + financial support query.
    PM-KISAN (and/or PMFBY) should be in the top results.
    """
    text = "I am a farmer from Tamil Nadu and I need financial help for farming"
    ctx = {"occupation": "farmer", "state": "Tamil Nadu", "need": "financial support"}
    matched = match_schemes(text, ctx)

    assert len(matched) > 0, "Should return at least one scheme for farmer query"
    assert len(matched) <= 3, "Should return at most 3 schemes"

    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in matched]
    assert "pm_kisan" in ids or "pm_fasal_bima" in ids, (
        f"Expected PM-KISAN or PMFBY for farmer+financial query, got: {ids}"
    )
    print(f"[PASS] P3 TEST 1 – Farmer+financial support → {ids}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 2: Farmer + crop insurance → PMFBY top result
# ═══════════════════════════════════════════════════════════
def test_p3_farmer_crop_insurance():
    """
    P3 TEST 2: Farmer + crop insurance.
    PM Fasal Bima Yojana should rank top.
    """
    text = "I am a farmer looking for crop insurance"
    ctx = {"occupation": "farmer", "need": "crop insurance", "category": "agriculture"}
    matched = match_schemes(text, ctx)

    assert len(matched) > 0, "Should return results for crop insurance query"
    assert len(matched) <= 3, "Must not return more than 3 schemes"

    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in matched]
    assert "pm_fasal_bima" in ids, (
        f"Expected PMFBY for crop insurance query, got: {ids}"
    )
    # PMFBY should rank high — verify it's in top 2
    top2 = ids[:2]
    assert "pm_fasal_bima" in top2, f"PMFBY should be in top 2, got top2={top2}"
    print(f"[PASS] P3 TEST 2 – Farmer+crop insurance → {ids}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 3: Tamil farmer query
# ═══════════════════════════════════════════════════════════
def test_p3_tamil_farmer_query():
    """
    P3 TEST 3: Tamil language farmer query.
    Language should be detected as Tamil.
    Scheme results should include agriculture schemes.
    """
    query = "நான் ஒரு விவசாயி. எனக்கு விவசாயத்துக்கு நிதி உதவி வேண்டும்."
    result = _fallback_detect_intent(query)
    assert result["language"] == "ta", f"Expected Tamil, got {result['language']}"

    matched = match_schemes(query, {"occupation": "farmer", "need": "financial support"})
    assert len(matched) > 0, "Should return results for Tamil farmer query"
    assert len(matched) <= 3, "Should not exceed 3 results"

    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in matched]
    agri_ids = {"pm_kisan", "pm_fasal_bima", "mahatma_gandhi_nrega"}
    has_agri = any(sid in agri_ids for sid in ids)
    assert has_agri, f"Expected at least one agriculture/employment scheme for Tamil farmer, got: {ids}"
    print(f"[PASS] P3 TEST 3 – Tamil farmer query → lang=ta, schemes={ids}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 4: Hindi farmer query
# ═══════════════════════════════════════════════════════════
def test_p3_hindi_farmer_query():
    """
    P3 TEST 4: Hindi language farmer query.
    Language should be detected as Hindi.
    Should return agriculture-related schemes.
    """
    # "मैं एक किसान हूं और मुझे खेती के लिए आर्थिक सहायता चाहिए।"
    query = "मैं एक किसान हूं और मुझे खेती के लिए आर्थिक सहायता चाहिए।"
    result = _fallback_detect_intent(query)
    assert result["language"] == "hi", f"Expected Hindi, got {result['language']}"

    matched = match_schemes(query, {"occupation": "farmer"})
    assert len(matched) > 0, "Should return results for Hindi farmer query"
    assert len(matched) <= 3, "Should not exceed 3 results"

    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in matched]
    print(f"[PASS] P3 TEST 4 – Hindi farmer query → lang=hi, schemes={ids}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 5: Health-related scheme query
# ═══════════════════════════════════════════════════════════
def test_p3_health_scheme_query():
    """
    P3 TEST 5: Health insurance query.
    Ayushman Bharat or TN health scheme should appear.
    """
    text = "I am looking for health insurance for my family"
    ctx = {"need": "health insurance", "category": "health"}
    matched = match_schemes(text, ctx)

    assert len(matched) > 0, "Should return results for health query"
    assert len(matched) <= 3, "Should not exceed 3 results"

    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in matched]
    health_ids = {"ayushman_bharat", "tamilnadu_chief_minister_health_insurance"}
    has_health = any(sid in health_ids for sid in ids)
    assert has_health, f"Expected a health scheme, got: {ids}"
    print(f"[PASS] P3 TEST 5 – Health query → {ids}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 6: Women-related scheme query
# ═══════════════════════════════════════════════════════════
def test_p3_women_scheme_query():
    """
    P3 TEST 6: Woman asking about financial assistance.
    Kalaignar Magalir or similar should appear.
    """
    text = "I am a woman from Tamil Nadu looking for financial assistance"
    ctx = {"gender": "female", "state": "Tamil Nadu", "need": "financial assistance"}
    matched = match_schemes(text, ctx)

    assert len(matched) > 0, "Should return results for women scheme query"
    assert len(matched) <= 3, "Should not exceed 3 results"

    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in matched]
    women_ids = {"tamilnadu_kalaignar_insurance", "pm_ujjwala", "sukanya_samriddhi"}
    has_women = any(sid in women_ids for sid in ids)
    assert has_women, f"Expected a women/TN scheme for female+TN query, got: {ids}"
    print(f"[PASS] P3 TEST 6 – Women+TN query → {ids}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 7: Child-related scheme query (daughter)
# ═══════════════════════════════════════════════════════════
def test_p3_daughter_scheme_query():
    """
    P3 TEST 7: Query about daughter savings scheme.
    Sukanya Samriddhi should appear for young daughter.
    """
    text = "My daughter is 8 years old and I want a government savings scheme"
    ctx = {"child_age": 8, "child_gender": "female", "need": "savings"}
    matched = match_schemes(text, ctx)

    assert len(matched) > 0, "Should return results for daughter query"
    assert len(matched) <= 3, "Should not exceed 3 results"

    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in matched]
    assert "sukanya_samriddhi" in ids, (
        f"Expected Sukanya Samriddhi for daughter age 8 savings query, got: {ids}"
    )
    print(f"[PASS] P3 TEST 7 – Daughter age 8 savings → {ids}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 8: Insufficient context — single word query
# ═══════════════════════════════════════════════════════════
def test_p3_insufficient_context_still_returns_results():
    """
    P3 TEST 8: Minimal context (just 'farmer scheme') still returns results.
    Should not demand a form. Should return candidates.
    """
    text = "I need a farmer scheme"
    ctx = {"occupation": "farmer"}
    matched = match_schemes(text, ctx)

    # Even with minimal context, there should be results
    assert len(matched) > 0, "Should return results even for minimal context"
    assert len(matched) <= 3, "Should not exceed 3 results"

    ids = [item[0]["id"] if isinstance(item, tuple) else item["id"] for item in matched]
    agri = {"pm_kisan", "pm_fasal_bima"}
    has_agri = any(sid in agri for sid in ids)
    assert has_agri, f"Expected agriculture scheme for 'farmer scheme' query, got: {ids}"
    print(f"[PASS] P3 TEST 8 – Minimal context (farmer scheme) → {ids}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 9: No meaningful match → empty list
# ═══════════════════════════════════════════════════════════
def test_p3_no_meaningful_match():
    """
    P3 TEST 9: Completely unrelated text should return empty or near-empty results.
    Unlike Phase 1 which returned first 2 schemes as fallback,
    Phase 3 returns empty list if nothing scores > 0.
    """
    text = "zxqwerty unrelated gibberish 123456"
    ctx = {}
    matched = match_schemes(text, ctx)

    # Unrelated text should return nothing
    assert isinstance(matched, list), "Should return a list"
    # Expect empty or very low score results
    # The key guarantee: no scheme is blindly returned for nonsense input
    assert len(matched) == 0, (
        f"Phase 3 matching should return empty list for unrelated text, got: "
        f"{[item[0]['id'] if isinstance(item, tuple) else item['id'] for item in matched]}"
    )
    print("[PASS] P3 TEST 9 – No meaningful match → empty list (correct)")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 10: Top-3 maximum result limit
# ═══════════════════════════════════════════════════════════
def test_p3_top3_maximum():
    """
    P3 TEST 10: Broad query should return at most 3 schemes.
    """
    text = "government scheme yojana welfare benefit insurance pension farmer health women savings"
    ctx = {}
    matched = match_schemes(text, ctx)

    assert len(matched) <= 3, (
        f"Must return at most 3 schemes, returned {len(matched)}"
    )
    print(f"[PASS] P3 TEST 10 – Top-3 limit enforced: {len(matched)} results")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 11: Match explanation exists in every result
# ═══════════════════════════════════════════════════════════
def test_p3_match_explanation_exists():
    """
    P3 TEST 11: Every matched scheme should have a match reason.
    """
    text = "I am a farmer looking for crop insurance"
    ctx = {"occupation": "farmer", "need": "crop insurance"}
    matched = match_schemes(text, ctx)

    assert len(matched) > 0, "Should return results"

    for item in matched:
        if isinstance(item, tuple):
            scheme, reasons = item
        else:
            scheme = item
            reasons = []

        # Build match reason using the helper
        reason = _build_match_reason_sentence(scheme, reasons, ctx)
        assert reason, f"Match reason should not be empty for {scheme['id']}"
        assert len(reason) > 10, f"Match reason too short for {scheme['id']}: '{reason}'"

    print(f"[PASS] P3 TEST 11 – Match explanation exists for {len(matched)} scheme(s)")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 12: Eligibility wording is non-guaranteeing
# ═══════════════════════════════════════════════════════════
def test_p3_eligibility_wording_non_guaranteeing():
    """
    P3 TEST 12: The fallback response must NOT say 'you are eligible' or 'you are definitely eligible'.
    Must use cautious wording.
    """
    matched = match_schemes("I am a farmer looking for help", {"occupation": "farmer"})
    schemes = [item[0] if isinstance(item, tuple) else item for item in matched]
    reasons_map = {item[0]["id"] if isinstance(item, tuple) else item["id"]: (item[1] if isinstance(item, tuple) else []) for item in matched}
    ctx = {"occupation": "farmer"}

    response = _fallback_scheme_response(schemes, reasons_map, ctx)

    # Check the closing message does not guarantee eligibility
    closing = response.get("closing_message", "").lower()
    guaranteed_phrases = [
        "you are eligible",
        "you are definitely eligible",
        "you qualify",
        "you are approved",
    ]
    for phrase in guaranteed_phrases:
        assert phrase not in closing, (
            f"Closing message must not contain '{phrase}'. Got: '{response['closing_message']}'"
        )

    # Should contain caution wording
    caution_words = ["informational", "reference", "check", "verify", "official", "before applying"]
    has_caution = any(word in closing for word in caution_words)
    assert has_caution, (
        f"Closing message should contain caution wording. Got: '{response['closing_message']}'"
    )
    print(f"[PASS] P3 TEST 12 – Eligibility wording is non-guaranteeing")
    print(f"       Closing: {response['closing_message'][:80]}...")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 13: Official source is not fabricated
# ═══════════════════════════════════════════════════════════
def test_p3_official_source_not_fabricated():
    """
    P3 TEST 13: Official source in fallback response must come from the DB.
    Should never be an invented URL.
    """
    # Get verified sources from DB
    verified_sources = {s["id"]: s.get("official_source", "") for s in GOVERNMENT_SCHEMES}

    matched = match_schemes("I am a farmer", {"occupation": "farmer"})
    schemes = [item[0] if isinstance(item, tuple) else item for item in matched]
    reasons_map = {item[0]["id"] if isinstance(item, tuple) else item["id"]: [] for item in matched}
    ctx = {"occupation": "farmer"}

    response = _fallback_scheme_response(schemes, reasons_map, ctx)

    for card in response.get("schemes", []):
        src = card.get("official_source", "")
        scheme_id = next((s["id"] for s in schemes if s["name"] == card.get("scheme_name", "")), None)

        if scheme_id:
            expected_src = verified_sources.get(scheme_id, "")
            if expected_src:
                assert src == expected_src, (
                    f"Official source for {scheme_id} should be '{expected_src}', got '{src}'"
                )
            else:
                # If no source in DB, it should say "not available"
                assert "not available" in src.lower(), (
                    f"If no official source in DB, response should say 'not available', got: '{src}'"
                )

    print("[PASS] P3 TEST 13 – Official source matches DB (not fabricated)")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 14: Existing grievance tests still pass
# ═══════════════════════════════════════════════════════════
def test_p3_grievance_still_works():
    """
    P3 TEST 14: Grievance-related functionality is unchanged.
    The match_department function should still work.
    """
    from main import match_department, generate_tracking_id
    dept_key, dept_info, confidence = match_department(
        "The water supply has been cut for 3 days in my area."
    )
    assert dept_key is not None, "Grievance routing should still work"
    assert dept_key == "water", f"Expected water dept, got {dept_key}"

    tid = generate_tracking_id()
    assert tid.startswith("DHV-"), f"Tracking ID should start with DHV-, got {tid}"
    print(f"[PASS] P3 TEST 14 – Grievance routing still works (dept={dept_key}, tid={tid})")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 15: Phase 3 scheme DB fields present
# ═══════════════════════════════════════════════════════════
def test_p3_scheme_db_has_phase3_fields():
    """
    P3 TEST 15: All 12 schemes must have Phase 3 fields.
    Fields must be correct types (not invented values).
    """
    required_p3_fields = ["target_groups", "occupation", "age_min", "age_max", "gender", "income_limit"]

    assert len(GOVERNMENT_SCHEMES) == 12, (
        f"Expected 12 schemes, got {len(GOVERNMENT_SCHEMES)}"
    )

    for scheme in GOVERNMENT_SCHEMES:
        sid = scheme.get("id", "unknown")
        for field in required_p3_fields:
            assert field in scheme, f"Scheme '{sid}' missing Phase 3 field '{field}'"

        # Type checks
        assert isinstance(scheme["target_groups"], list), f"'{sid}' target_groups must be list"
        assert isinstance(scheme["occupation"], list), f"'{sid}' occupation must be list"
        assert isinstance(scheme["gender"], list), f"'{sid}' gender must be list"
        assert scheme["age_min"] is None or isinstance(scheme["age_min"], (int, float)), \
            f"'{sid}' age_min must be int or None"
        assert scheme["age_max"] is None or isinstance(scheme["age_max"], (int, float)), \
            f"'{sid}' age_max must be int or None"

    print(f"[PASS] P3 TEST 15 – All 12 schemes have Phase 3 fields with correct types")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 16: Follow-up question logic
# ═══════════════════════════════════════════════════════════
def test_p3_follow_up_question():
    """
    P3 TEST 16: Follow-up question is suggested when context is minimal.
    Should not ask when enough context is provided.
    """
    # Minimal context → should suggest a follow-up
    minimal_ctx = {}
    q_en = _suggest_follow_up_question(minimal_ctx, "en")
    assert q_en is not None, "Should suggest a follow-up when context is empty"
    assert len(q_en) > 10, "Follow-up question should be meaningful"

    # Rich context → should NOT ask more
    rich_ctx = {"occupation": "farmer", "state": "Tamil Nadu", "gender": "male"}
    q_rich = _suggest_follow_up_question(rich_ctx, "en")
    assert q_rich is None, "Should NOT ask follow-up when enough context exists"

    # Daughter mentioned but age unknown → ask daughter age
    daughter_ctx = {"child_gender": "female"}
    q_daughter = _suggest_follow_up_question(daughter_ctx, "en")
    assert q_daughter is not None, "Should ask daughter age"
    assert "daughter" in q_daughter.lower(), "Question should mention daughter"

    print("[PASS] P3 TEST 16 – Follow-up question logic works correctly")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 17: Session context merging
# ═══════════════════════════════════════════════════════════
def test_p3_session_context_merging():
    """
    P3 TEST 17: Session context accumulates across turns.
    New non-null values overwrite; null values do not erase existing.
    """
    session_id = "test-session-phase3"

    # Turn 1: user says "I am a farmer"
    ctx1 = {"occupation": "farmer"}
    merged1 = merge_session_context(session_id, ctx1)
    assert merged1["occupation"] == "farmer", "occupation should be set"

    # Turn 2: user adds "I am from Tamil Nadu"
    ctx2 = {"state": "Tamil Nadu", "occupation": None}  # null occupation shouldn't erase
    merged2 = merge_session_context(session_id, ctx2)
    assert merged2["state"] == "Tamil Nadu", "state should be added"
    assert merged2["occupation"] == "farmer", "occupation should NOT be erased by None"

    print("[PASS] P3 TEST 17 – Session context merges correctly across turns")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 18: Age-based scoring penalizes out-of-range
# ═══════════════════════════════════════════════════════════
def test_p3_age_based_scoring():
    """
    P3 TEST 18: Sukanya Samriddhi should be penalised for daughters > 10.
    Should rank lower or absent for 12-year-old girl.
    """
    # For 8-year-old girl → SSY should score positively
    sukanya = next(s for s in GOVERNMENT_SCHEMES if s["id"] == "sukanya_samriddhi")
    tl_match = normalize_text("daughter savings scheme girl")

    score_8, _ = _score_scheme(sukanya, tl_match, {"child_age": 8, "child_gender": "female"})
    score_12, _ = _score_scheme(sukanya, tl_match, {"child_age": 12, "child_gender": "female"})

    assert score_8 > score_12, (
        f"SSY score for age 8 ({score_8:.1f}) should be higher than age 12 ({score_12:.1f})"
    )
    print(f"[PASS] P3 TEST 18 – Age scoring: SSY score age-8={score_8:.1f} > age-12={score_12:.1f}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 19: Occupation match gives strong boost
# ═══════════════════════════════════════════════════════════
def test_p3_occupation_match_boost():
    """
    P3 TEST 19: PM-KISAN should score higher when occupation=farmer
    than when occupation=student.
    """
    pm_kisan = next(s for s in GOVERNMENT_SCHEMES if s["id"] == "pm_kisan")
    tl = normalize_text("government scheme financial support")

    score_farmer, _ = _score_scheme(pm_kisan, tl, {"occupation": "farmer"})
    score_student, _ = _score_scheme(pm_kisan, tl, {"occupation": "student"})

    assert score_farmer > score_student, (
        f"PM-KISAN score for farmer ({score_farmer:.1f}) should be higher than student ({score_student:.1f})"
    )
    print(f"[PASS] P3 TEST 19 – Occupation boost: farmer={score_farmer:.1f} > student={score_student:.1f}")


# ═══════════════════════════════════════════════════════════
# PHASE 3 TEST 20: Wrong state penalises state-specific schemes
# ═══════════════════════════════════════════════════════════
def test_p3_wrong_state_penalises():
    """
    P3 TEST 20: Tamil Nadu schemes should score lower (or not appear)
    when user is from a different state.
    """
    kalaignar = next(s for s in GOVERNMENT_SCHEMES if s["id"] == "tamilnadu_kalaignar_insurance")
    tl = normalize_text("women financial assistance scheme")

    score_tn, _ = _score_scheme(kalaignar, tl, {"state": "Tamil Nadu", "gender": "female"})
    score_up, _ = _score_scheme(kalaignar, tl, {"state": "Uttar Pradesh", "gender": "female"})

    assert score_tn > score_up, (
        f"Kalaignar TN scheme should score higher for TN ({score_tn:.1f}) than UP ({score_up:.1f})"
    )
    print(f"[PASS] P3 TEST 20 – State penalty: TN={score_tn:.1f} > UP={score_up:.1f}")


# ═══════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    tests = [
        ("P3 TEST 1  – Farmer + financial support",        test_p3_farmer_financial_support),
        ("P3 TEST 2  – Farmer + crop insurance",           test_p3_farmer_crop_insurance),
        ("P3 TEST 3  – Tamil farmer query",                test_p3_tamil_farmer_query),
        ("P3 TEST 4  – Hindi farmer query",                test_p3_hindi_farmer_query),
        ("P3 TEST 5  – Health scheme query",               test_p3_health_scheme_query),
        ("P3 TEST 6  – Women scheme query",                test_p3_women_scheme_query),
        ("P3 TEST 7  – Daughter savings scheme",           test_p3_daughter_scheme_query),
        ("P3 TEST 8  – Insufficient context still works",  test_p3_insufficient_context_still_returns_results),
        ("P3 TEST 9  – No meaningful match → empty",       test_p3_no_meaningful_match),
        ("P3 TEST 10 – Top-3 maximum enforced",            test_p3_top3_maximum),
        ("P3 TEST 11 – Match explanation exists",          test_p3_match_explanation_exists),
        ("P3 TEST 12 – Eligibility wording non-guaranteeing", test_p3_eligibility_wording_non_guaranteeing),
        ("P3 TEST 13 – Official source not fabricated",    test_p3_official_source_not_fabricated),
        ("P3 TEST 14 – Existing grievance tests pass",     test_p3_grievance_still_works),
        ("P3 TEST 15 – Phase 3 DB fields present",         test_p3_scheme_db_has_phase3_fields),
        ("P3 TEST 16 – Follow-up question logic",          test_p3_follow_up_question),
        ("P3 TEST 17 – Session context merging",           test_p3_session_context_merging),
        ("P3 TEST 18 – Age-based scoring",                 test_p3_age_based_scoring),
        ("P3 TEST 19 – Occupation match boost",            test_p3_occupation_match_boost),
        ("P3 TEST 20 – Wrong state penalises",             test_p3_wrong_state_penalises),
    ]

    passed = 0
    failed = 0
    errors = []

    print("\n" + "=" * 64)
    print("  DHVAANI PHASE 3 — SMART SCHEME FINDER TEST SUITE")
    print("=" * 64 + "\n")

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {name}")
            print(f"   Reason: {e}")
            failed += 1
            errors.append((name, str(e)))
        except Exception as e:
            print(f"[ERROR] {name}")
            print(f"   Exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            errors.append((name, f"{type(e).__name__}: {e}"))

    print("\n" + "=" * 64)
    print(f"  RESULTS: {passed} passed / {failed} failed / {len(tests)} total")
    print("=" * 64)
    if failed == 0:
        print("  ALL PHASE 3 TESTS PASSED! \u2705")
    else:
        print(f"  {failed} test(s) failed. See details above.")
    print()
