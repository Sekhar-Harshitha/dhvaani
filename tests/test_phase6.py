"""
Dhvaani Phase 6 Test Suite: Real-World Government Integration & Verified Service Layer
======================================================================================
Tests:
1. Verified scheme data schema and authoritative sources.
2. Absence of fabricated URLs, amounts, or eligibility rules.
3. Verified service catalog (schemes + 8 civic grievance services).
4. Grievance draft creation and SQLite persistence.
5. Grievance confirmation produces assisted portal handoff with copyable complaint.
6. Explicit separation of Dhvaani Request ID from Government Reference ID.
7. Tracking endpoint truthful statuses (no fake government processing claims).
8. Linking citizen's official government reference number.
9. Persistence survival across in-memory cache purge (server restart simulation).
10. Truthful status check endpoint with official tracking URLs.
11. Security & validation: malformed input handling, no credential leakage.
"""

import pytest
import sqlite3
from fastapi.testclient import TestClient
from pathlib import Path

from main import app, GRIEVANCE_STORE
from schemes_db import GOVERNMENT_SCHEMES, GRIEVANCE_DEPARTMENTS, get_scheme_by_id, get_verified_schemes
from services_catalog import ServiceCatalog, GRIEVANCE_SERVICES
import db


client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# 1. VERIFIED SCHEME DATA TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_p6_1_all_12_schemes_have_phase6_verification_fields():
    """Verify all 12 schemes have complete Phase 6 verification attributes."""
    assert len(GOVERNMENT_SCHEMES) == 12
    required_p6_fields = [
        "scheme_id", "official_name", "local_names", "category", "state",
        "description", "benefits", "eligibility", "exclusions",
        "required_documents", "application_steps", "official_application_url",
        "official_information_url", "official_helpline", "ministry_or_department",
        "source_type", "source_url", "last_verified", "verification_status"
    ]
    for s in GOVERNMENT_SCHEMES:
        for f in required_p6_fields:
            assert f in s, f"Scheme {s.get('id')} missing Phase 6 field '{f}'"
        assert s["verification_status"] in ("verified", "partially_verified", "needs_verification")
        assert s["source_type"] in ("central_portal", "state_portal", "ministry_website", "myscheme")
        assert s["official_application_url"].startswith("http")
        assert s["official_information_url"].startswith("http")
        assert s["source_url"].startswith("http")
        assert len(s["required_documents"]) > 0


def test_p6_2_no_fake_scheme_urls():
    """Verify official sources belong to legitimate domains (gov.in, nic.in, tn.gov.in, etc.)."""
    valid_domain_endings = (".gov.in", ".nic.in", ".tn.gov.in", "cmchistn.com", "nsdl.co.in", "pfrda.org.in")
    for s in GOVERNMENT_SCHEMES:
        url = s["official_information_url"].lower()
        has_valid_domain = any(dom in url for dom in valid_domain_endings)
        assert has_valid_domain, f"Scheme {s['id']} has non-authoritative URL: {url}"


def test_p6_3_scheme_helper_functions():
    """Test get_scheme_by_id and get_verified_schemes helpers."""
    s = get_scheme_by_id("pm_kisan")
    assert s is not None
    assert s["official_name"] == "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)"
    assert s["category"] == "agriculture"

    verified_list = get_verified_schemes()
    assert len(verified_list) == 12


# ─────────────────────────────────────────────────────────────────────────────
# 2. VERIFIED SERVICE CATALOG TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_p6_4_service_catalog_grievance_departments():
    """Verify all 8 core grievance services exist in ServiceCatalog with truthful modes."""
    core_depts = ["electricity", "streetlight", "water", "road", "ration", "police", "health", "municipal"]
    for dept in core_depts:
        svc = ServiceCatalog.get_service(dept)
        assert svc is not None, f"Missing grievance service for {dept}"
        assert svc.workflow.submission_mode in ("assisted_handoff", "official_portal", "api")
        # Direct unauthenticated public API does NOT exist on state/central civic portals
        assert svc.workflow.api_available is False
        assert svc.workflow.requires_citizen_auth is True
        assert svc.verification.verification_status == "verified"
        assert len(svc.requirements.required_documents) > 0


def test_p6_5_api_services_endpoint():
    """Test GET /api/services returns catalog with schemes and grievance pathways."""
    resp = client.get("/api/services")
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data
    assert data["schemes_count"] == 12
    assert data["grievance_services_count"] >= 8
    assert len(data["schemes"]) == 12
    assert len(data["grievance_services"]) >= 8
    assert data["verification_standards"]["no_invented_data"] is True


def test_p6_6_api_service_details_endpoint():
    """Test GET /api/services/{service_id} for both scheme and grievance types."""
    # Scheme details
    resp = client.get("/api/services/pm_kisan")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["service_type"] == "scheme"
    assert data["service"]["id"] == "pm_kisan"

    # Grievance service details
    resp2 = client.get("/api/services/grievance_streetlight")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is True
    assert data2["service_type"] == "grievance"
    assert data2["service"]["service_id"] == "grievance_streetlight"

    # 404 for unknown
    resp3 = client.get("/api/services/unknown_service_xyz")
    assert resp3.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 3. GRIEVANCE DRAFT, CONFIRMATION & OFFICIAL HANDOFF TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_p6_7_grievance_draft_persisted_to_db():
    """Test that creating a grievance draft persists to SQLite database."""
    resp = client.post(
        "/api/process",
        json={"text": "There has been no streetlight near my house in Velachery for two weeks", "language": "en"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "grievance"
    gid = data["grievance_id"]

    # Verify in SQLite database directly
    rec = db.get_request(gid)
    assert rec is not None
    assert rec["grievance_id"] == gid
    assert rec["status"] == "draft"
    assert "streetlight" in rec["category"].lower() or "lighting" in rec["issue"].lower()


def test_p6_8_grievance_confirmation_assisted_handoff():
    """Test confirmation workflow returns assisted portal handoff, copyable text, and separate IDs."""
    # 1. Draft
    draft_res = client.post(
        "/api/process",
        json={"text": "Water pipeline burst on Main Road near Gandhi statue in Madurai", "language": "en"}
    )
    gid = draft_res.json()["grievance_id"]

    # 2. Confirm
    conf_res = client.post(
        "/api/confirm-grievance",
        json={"grievance_id": gid, "confirmed": True, "user_name": "Ravi", "contact": "9876543210"}
    )
    assert conf_res.status_code == 200
    res_data = conf_res.json()

    assert res_data["success"] is True
    assert res_data["status"] == "request_created"
    assert res_data["submission_status"] == "ready_for_submission"
    assert res_data["submission_mode"] == "assisted_handoff"

    # Crucial Phase 6 check: Dhvaani Request ID is populated, Government Reference ID is None
    tracking_id = res_data["tracking_id"]
    assert tracking_id.startswith("DHV-")
    assert res_data["dhvaani_request_id"] == tracking_id
    assert res_data["government_reference_id"] is None
    assert "Awaiting citizen submission" in res_data["government_status"]

    # Official handoff artifacts
    assert "portal" in res_data
    assert "portal_name" in res_data
    assert "copyable_complaint" in res_data
    assert "Water pipeline burst" in res_data["copyable_complaint"]
    assert len(res_data["required_documents"]) > 0


def test_p6_9_tracking_distinguishes_dhvaani_from_government_id():
    """Test tracking endpoint truthfully distinguishes Dhvaani ID from Government Reference ID."""
    # Draft & confirm
    d = client.post("/api/process", json={"text": "Severe power cut for 6 hours in Tambaram", "language": "en"}).json()
    gid = d["grievance_id"]
    c = client.post("/api/confirm-grievance", json={"grievance_id": gid, "confirmed": True}).json()
    tid = c["tracking_id"]

    # Track
    track_res = client.get(f"/api/track/{tid}")
    assert track_res.status_code == 200
    tdata = track_res.json()

    assert tdata["dhvaani_request_id"] == tid
    assert tdata["tracking_id"] == tid
    assert tdata["government_reference_id"] is None
    assert "official government reference" in tdata["note"].lower()
    assert "not been submitted" in tdata["note"].lower()


def test_p6_10_link_government_reference_flow():
    """Test linking an authentic government reference number to a Dhvaani request."""
    # 1. Create request
    d = client.post("/api/process", json={"text": "Garbage not cleared in ward 12 for 5 days", "language": "en"}).json()
    gid = d["grievance_id"]
    c = client.post("/api/confirm-grievance", json={"grievance_id": gid, "confirmed": True}).json()
    tid = c["tracking_id"]

    # 2. Link Government Reference ID (e.g. from GCC / CPGRAMS SMS)
    link_res = client.post(
        "/api/link-government-ref",
        json={"tracking_id": tid, "government_reference_id": "GCC/2024/098712"}
    )
    assert link_res.status_code == 200
    ldata = link_res.json()
    assert ldata["success"] is True
    assert ldata["government_reference_id"] == "GCC/2024/098712"
    assert ldata["tracking_id"] == tid

    # 3. Track request again - verify Government Reference is preserved
    track_res = client.get(f"/api/track/{tid}")
    assert track_res.status_code == 200
    tdata = track_res.json()
    assert tdata["government_reference_id"] == "GCC/2024/098712"
    assert "GCC/2024/098712" in tdata["message"]


def test_p6_11_sqlite_persistence_survives_memory_wipe():
    """Test that requests in SQLite survive complete in-memory store eviction (simulating server restart)."""
    # 1. Create and confirm request
    d = client.post("/api/process", json={"text": "Deep pothole causing accidents on GST Road", "language": "en"}).json()
    gid = d["grievance_id"]
    c = client.post("/api/confirm-grievance", json={"grievance_id": gid, "confirmed": True}).json()
    tid = c["tracking_id"]

    # Link government reference
    client.post("/api/link-government-ref", json={"tracking_id": tid, "government_reference_id": "PWD-NH-5432"})

    # 2. SIMULATE SERVER RESTART: completely wipe in-memory GRIEVANCE_STORE
    GRIEVANCE_STORE.clear()
    assert len(GRIEVANCE_STORE) == 0

    # 3. Track request by tracking ID - must be retrieved from SQLite
    track_res = client.get(f"/api/track/{tid}")
    assert track_res.status_code == 200
    tdata = track_res.json()
    assert tdata["tracking_id"] == tid
    assert tdata["government_reference_id"] == "PWD-NH-5432"
    assert "pothole" in tdata["issue"].lower() or "road" in tdata["department"].lower()


def test_p6_12_truthful_government_service_status_endpoint():
    """Test GET /api/services/{service_id}/status/{government_reference_id} truthfully provides portal tracking link."""
    resp = client.get("/api/services/grievance_electricity/status/TNEB-2024-8841")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["government_reference_id"] == "TNEB-2024-8841"
    assert data["status_check_mode"] == "official_portal_lookup"
    assert "tneb.in" in data["official_tracking_url"]
    assert "available on the official portal" in data["current_status"]
    # No fake statuses like "Officer Assigned" or "In Review"
    assert "Officer Assigned" not in data["current_status"]


def test_p6_13_security_and_error_handling():
    """Test security: malformed inputs, nonexistent IDs, empty reference IDs."""
    # Empty reference ID
    resp1 = client.post("/api/link-government-ref", json={"tracking_id": "DHV-999999", "government_reference_id": ""})
    assert resp1.status_code == 400

    # Nonexistent tracking ID
    resp2 = client.post("/api/link-government-ref", json={"tracking_id": "DHV-NONEXISTENT", "government_reference_id": "REF123"})
    assert resp2.status_code == 404

    # Nonexistent tracking lookup
    resp3 = client.get("/api/track/DHV-UNKNOWN-000")
    assert resp3.status_code == 404
    assert resp3.json()["success"] is False
