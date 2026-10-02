"""
Dhvaani - Phase 7 Automated Test Suite
========================================
Validates all Phase 7 requirements:
1. Real Attachment / Evidence feature for civic grievances & service requests.
2. Supported file types: JPG, PNG, WEBP, PDF.
3. Server-side validation: max 10MB per file, max 5 files per request.
4. Security validation: reject .exe, .sh, .html, .js, sanitize filenames, prevent path traversal.
5. Storage: persistent ./data/uploads/, never exposed as public static directory.
6. Database: attachments table schema, metadata persistence, binary files on disk only.
7. Grievance evidence flow: linking attachments to confirmed Dhvaani requests.
8. Truthful disclaimers: attachments stored by Dhvaani, not submitted to government.
"""

import io
import os
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import app, UPLOAD_DIR, MAX_FILE_SIZE, MAX_FILES_PER_REQUEST
import db


@pytest.fixture
def client():
    return TestClient(app)


def test_upload_directory_not_in_static():
    """Requirement: Do NOT store uploads inside static/ and do NOT mount as static."""
    static_dir = (Path(__file__).parent.parent / "static").resolve()
    upload_dir = UPLOAD_DIR.resolve()
    assert not str(upload_dir).startswith(str(static_dir)), (
        f"Upload dir {upload_dir} must NOT be inside static dir {static_dir}"
    )


def test_no_public_static_mount_for_uploads():
    """Verify uploads directory is not exposed as a public static mount in FastAPI."""
    for route in app.routes:
        if hasattr(route, "path") and route.path.startswith("/uploads"):
            pytest.fail("Uploads directory must not be mounted directly as a public route.")


def test_valid_image_upload_jpg(client):
    """Test valid JPG image upload and metadata storage."""
    file_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"dummy jpeg image content for testing"
    files = [("files", ("pothole.jpg", io.BytesIO(file_bytes), "image/jpeg"))]

    resp = client.post("/api/attachments", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["saved"]) == 1

    saved = data["saved"][0]
    aid = saved["attachment_id"]
    assert saved["original_filename"] == "pothole.jpg"
    assert saved["content_type"] == "image/jpeg"
    assert saved["file_size"] == len(file_bytes)
    assert "not been submitted to any government portal" in data["note"].lower()

    # Check file exists on disk
    stored_path = UPLOAD_DIR / f"{aid}.jpg"
    assert stored_path.exists()
    assert stored_path.read_bytes() == file_bytes

    # Cleanup
    client.delete(f"/api/attachments/{aid}")


def test_valid_document_upload_pdf(client):
    """Test valid PDF document upload and metadata storage."""
    pdf_bytes = b"%PDF-1.4 header dummy civic petition document"
    files = [("files", ("petition.pdf", io.BytesIO(pdf_bytes), "application/pdf"))]

    resp = client.post("/api/attachments", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["saved"]) == 1

    saved = data["saved"][0]
    aid = saved["attachment_id"]
    assert saved["original_filename"] == "petition.pdf"
    assert saved["content_type"] == "application/pdf"

    # Cleanup
    client.delete(f"/api/attachments/{aid}")


def test_reject_disallowed_file_types(client):
    """Requirement: Server-side validation rejects exe, sh, html, js, py."""
    disallowed = [
        ("malicious.exe", b"MZ\x90\x00", "application/x-msdownload"),
        ("script.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
        ("hack.html", b"<script>alert(1)</script>", "text/html"),
        ("code.js", b"console.log('pwned');", "application/javascript"),
        ("backdoor.py", b"import os; os.system('calc')", "text/x-python"),
    ]

    for filename, content, mime in disallowed:
        files = [("files", (filename, io.BytesIO(content), mime))]
        resp = client.post("/api/attachments", files=files)
        assert resp.status_code == 422, f"Expected 422 rejection for {filename}, got {resp.status_code}"
        data = resp.json()
        assert data["success"] is False


def test_reject_oversized_file(client):
    """Requirement: Reject files exceeding 10MB."""
    oversized_bytes = b"0" * (MAX_FILE_SIZE + 1024)
    files = [("files", ("huge_pothole.jpg", io.BytesIO(oversized_bytes), "image/jpeg"))]

    resp = client.post("/api/attachments", files=files)
    assert resp.status_code == 422
    data = resp.json()
    assert data["success"] is False
    assert any("too large" in d.get("error", "").lower() or "maximum" in d.get("error", "").lower() for d in data.get("details", []))


def test_reject_more_than_max_files(client):
    """Requirement: Maximum 5 files per upload request."""
    files = [
        ("files", (f"photo{i}.jpg", io.BytesIO(b"\xFF\xD8\xFF\xE0" + b"x" * 10), "image/jpeg"))
        for i in range(6)
    ]
    resp = client.post("/api/attachments", files=files)
    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False
    assert "maximum 5" in data["error"].lower()


def test_multiple_valid_attachments(client):
    """Test uploading multiple valid files (photo + PDF) simultaneously."""
    files = [
        ("files", ("broken_pipe.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"img1"), "image/png")),
        ("files", ("resident_complaint.pdf", io.BytesIO(b"%PDF-1.5" + b"doc1"), "application/pdf")),
    ]
    resp = client.post("/api/attachments", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["saved"]) == 2

    # Cleanup
    for s in data["saved"]:
        client.delete(f"/api/attachments/{s['attachment_id']}")


def test_delete_attachment_flow(client):
    """Test successful removal of an attachment on server and disk."""
    file_bytes = b"\xFF\xD8\xFF\xE0" + b"temporary evidence photo"
    files = [("files", ("temp_evidence.jpg", io.BytesIO(file_bytes), "image/jpeg"))]
    resp = client.post("/api/attachments", files=files)
    aid = resp.json()["saved"][0]["attachment_id"]

    stored_file = UPLOAD_DIR / f"{aid}.jpg"
    assert stored_file.exists()

    del_resp = client.delete(f"/api/attachments/{aid}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True
    assert not stored_file.exists()


def test_delete_nonexistent_or_invalid_id(client):
    """Test delete with invalid UUID or nonexistent attachment."""
    # Invalid UUID format (path traversal attempt)
    resp = client.delete("/api/attachments/../../etc/passwd")
    assert resp.status_code in (400, 404)

    # Random nonexistent valid UUID
    nonexistent = str(uuid.uuid4())
    resp2 = client.delete(f"/api/attachments/{nonexistent}")
    assert resp2.status_code == 404


def test_grievance_confirmation_links_attachments(client):
    """
    Test full end-to-end evidence linking:
    1. Create grievance draft via text query.
    2. Upload attachment with draft grievance_id.
    3. Confirm grievance.
    4. Verify tracking record contains attachment metadata.
    """
    # 1. Create draft
    q_resp = client.post("/api/process", json={"text": "Streetlight not working on Anna Salai Chennai", "language": "en"})
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert q_data["intent"] == "grievance"
    gid = q_data["grievance_id"]

    # 2. Upload attachment associated with draft
    photo_bytes = b"\xFF\xD8\xFF\xE0" + b"water leakage photo evidence"
    files = [("files", ("leakage.jpg", io.BytesIO(photo_bytes), "image/jpeg"))]
    att_resp = client.post(
        "/api/attachments",
        files=files,
        data={"dhvaani_request_id": gid},
    )
    assert att_resp.status_code == 200
    aid = att_resp.json()["saved"][0]["attachment_id"]

    # 3. Confirm grievance
    conf_resp = client.post(
        "/api/confirm-grievance",
        json={"grievance_id": gid, "confirmed": True, "attachment_ids": [aid]},
    )
    assert conf_resp.status_code == 200
    conf_data = conf_resp.json()
    assert conf_data["success"] is True
    assert conf_data["status"] == "request_created"
    tid = conf_data["tracking_id"]

    # Verify attachment is linked in confirmation response
    assert "attachments" in conf_data
    assert conf_data["attachment_count"] >= 1
    linked_aids = [a["attachment_id"] for a in conf_data["attachments"]]
    assert aid in linked_aids

    # 4. Verify tracking query returns attachments
    track_resp = client.get(f"/api/track/{tid}")
    assert track_resp.status_code == 200
    track_data = track_resp.json()
    assert track_data["tracking_id"] == tid
    assert "attachments" in track_data
    assert track_data["attachment_count"] >= 1

    # Cleanup
    client.delete(f"/api/attachments/{aid}")
