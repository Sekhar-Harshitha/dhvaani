import requests
import io
import sys
import time

BASE = 'https://dhvaani.vercel.app'
print('=== DHVAANI PRODUCTION VERIFICATION ===')
print(f'Target: {BASE}\n')

failures = []

def check(name, fn):
    try:
        fn()
        print(f'[OK] {name}')
    except AssertionError as e:
        print(f'[FAIL] {name}: Assertion failed - {e}')
        failures.append(name)
    except Exception as e:
        print(f'[FAIL] {name}: {type(e).__name__} - {e}')
        failures.append(name)

# 1. Health
def test_health():
    r = requests.get(f'{BASE}/api/health', timeout=15)
    data = r.json()
    print(f'   Status: {data.get("status")}, DB: {data.get("database_type")}, Gemini: {data.get("gemini")}, OpenRouter: {data.get("openrouter")}')
    assert r.status_code == 200 and data.get('status') == 'online'
check('Health check (/api/health)', test_health)

# 2. Frontend
def test_frontend():
    r = requests.get(f'{BASE}/', timeout=15)
    print(f'   HTTP {r.status_code}, Length: {len(r.text)} bytes, "Dhvaani" in title: {"Dhvaani" in r.text}')
    assert r.status_code == 200 and 'Dhvaani' in r.text
check('Frontend load (/)', test_frontend)

# 3. Services Catalog
def test_services():
    r = requests.get(f'{BASE}/api/services', timeout=15)
    count = r.json().get('count')
    print(f'   Count: {count}')
    assert r.status_code == 200 and count == 20
check('Services catalog (/api/services)', test_services)

# 4. Schemes List
def test_schemes():
    r = requests.get(f'{BASE}/api/schemes', timeout=15)
    schemes = r.json().get('schemes', [])
    print(f'   Count: {len(schemes)}')
    assert r.status_code == 200 and len(schemes) == 12
check('Schemes list (/api/schemes)', test_schemes)

# 5. Scheme Discovery (AI)
def test_scheme_query():
    r = requests.post(
        f'{BASE}/api/process',
        json={'text': 'I am a small farmer needing financial support', 'language': 'en'},
        timeout=60
    )
    data = r.json()
    print(f'   HTTP {r.status_code}, Intent: {data.get("intent")}, Matched: {data.get("matched_scheme_count")}')
    assert r.status_code == 200 and data.get('intent') == 'scheme'
check('Scheme discovery AI (/api/process)', test_scheme_query)

# 6. Grievance Query (AI)
gid = None
def test_grievance_query():
    global gid
    r = requests.post(
        f'{BASE}/api/process',
        json={'text': 'Streetlight not working in Gandhi Nagar Madurai for 5 days', 'language': 'en'},
        timeout=60
    )
    data = r.json()
    gid = data.get('grievance_id')
    print(f'   HTTP {r.status_code}, Intent: {data.get("intent")}, Draft GID: {gid}')
    assert r.status_code == 200 and data.get('intent') == 'grievance' and gid
check('Grievance intake AI (/api/process)', test_grievance_query)

# 7. Grievance Confirmation
tid = None
def test_grievance_confirm():
    global tid
    if not gid:
        raise AssertionError('No grievance_id from step 6')
    r = requests.post(
        f'{BASE}/api/confirm-grievance',
        json={'grievance_id': gid, 'confirmed': True, 'user_name': 'Ravi Kumar', 'contact': '9876543210'},
        timeout=30
    )
    data = r.json()
    tid = data.get('tracking_id')
    print(f'   HTTP {r.status_code}, Tracking ID: {tid}, Mode: {data.get("submission_mode")}')
    assert r.status_code == 200 and tid and tid.startswith('DHV-')
check('Grievance confirm (/api/confirm-grievance)', test_grievance_confirm)

# 8. Tracking Lookup
def test_tracking():
    if not tid:
        raise AssertionError('No tracking_id from step 7')
    r = requests.get(f'{BASE}/api/track/{tid}', timeout=15)
    data = r.json()
    print(f'   HTTP {r.status_code}, Status: {data.get("status")}, Dept: {data.get("department")}')
    assert r.status_code == 200 and data.get('success') is True
check('Tracking lookup (/api/track/:id)', test_tracking)

# 9. Link Government Reference
def test_link_govt_ref():
    if not tid:
        raise AssertionError('No tracking_id from step 7')
    r = requests.post(
        f'{BASE}/api/link-government-ref',
        json={'tracking_id': tid, 'government_reference_id': 'GOV-TN-2026-9812'},
        timeout=15
    )
    data = r.json()
    print(f'   HTTP {r.status_code}, Linked: {data.get("government_reference_id")}')
    assert r.status_code == 200 and data.get('success') is True
check('Link govt ref (/api/link-government-ref)', test_link_govt_ref)

# 10. Attachment Upload & Delete
def test_attachment():
    attach_rid = tid or 'DEMO-TEST-001'
    img_bytes = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00' + b'dummy test photo evidence content'
    files = [('files', ('evidence.jpg', io.BytesIO(img_bytes), 'image/jpeg'))]
    r = requests.post(
        f'{BASE}/api/attachments',
        files=files,
        data={'dhvaani_request_id': attach_rid},
        timeout=30
    )
    data = r.json()
    saved = data.get('saved_count', 0)
    print(f'   HTTP {r.status_code}, Saved count: {saved}')
    assert r.status_code == 200 and saved >= 1
    aid = data['saved'][0]['attachment_id']

    # Cleanup
    del_r = requests.delete(f'{BASE}/api/attachments/{aid}', timeout=15)
    print(f'   Delete: HTTP {del_r.status_code}, {del_r.json().get("message")}')
    assert del_r.status_code == 200
check('Attachment upload & delete (/api/attachments)', test_attachment)

# Summary
print(f'\n{"=" * 50}')
if failures:
    print(f'RESULT: {10 - len(failures)}/10 tests passed')
    print(f'FAILED: {", ".join(failures)}')
    sys.exit(1)
else:
    print('RESULT: 10/10 tests passed — ALL PRODUCTION ENDPOINTS VERIFIED ✓')
    sys.exit(0)
