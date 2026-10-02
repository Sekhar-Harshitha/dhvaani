"""
Live API verification script for Dhvaani Phase 1.
Run: python tests/verify_live.py
"""
import urllib.request
import urllib.error
import json
import sys

BASE = "http://localhost:8000"

def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read())

def post(path, body):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

results = []

def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, label))
    print(f"  [{status}] {label}" + (f": {detail}" if detail else ""))
    return condition

print("\n" + "=" * 60)
print("  DHVAANI LIVE API VERIFICATION")
print("=" * 60 + "\n")

# 1. Health check
print("--- /api/health ---")
h = get("/api/health")
check("status = online", h["status"] == "online")
check("scheme_database loaded", h["scheme_database"]["count"] == 12, f"count={h['scheme_database']['count']}")
check("department_database loaded", h["department_database"]["count"] >= 9, f"count={h['department_database']['count']}")
check("gemini field present", "gemini" in h)

# 2. English scheme query
print("\n--- English scheme query (PM-KISAN) ---")
r = post("/api/process", {"text": "Am I eligible for PM-KISAN?", "language": "en"})
check("intent = scheme", r["intent"] == "scheme", f"intent={r['intent']}")
check("matched_scheme_count > 0", r.get("matched_scheme_count", 0) > 0)
check("disclaimer present", "disclaimer" in r)

# 3. Tamil scheme query
print("\n--- Tamil scheme query ---")
r = post("/api/process", {"text": "விவசாய திட்டம் பற்றி தெரிய வேண்டும்", "language": "ta"})
check("intent = scheme", r["intent"] == "scheme", f"intent={r['intent']}")
check("language = ta", r["language"] == "ta", f"lang={r['language']}")

# 4. Hindi scheme query
print("\n--- Hindi scheme query ---")
r = post("/api/process", {"text": "मुझे किसान योजना के बारे में जानकारी चाहिए", "language": "hi"})
check("intent = scheme", r["intent"] == "scheme", f"intent={r['intent']}")
check("language = hi", r["language"] == "hi", f"lang={r['language']}")

# 5. English grievance
print("\n--- English grievance (street light) ---")
r = post("/api/process", {"text": "The street light near my house has not been working for three days.", "language": "en"})
check("intent = grievance", r["intent"] == "grievance", f"intent={r['intent']}")
check("submission_status = draft", r.get("submission_status") == "draft", f"submission_status={r.get('submission_status')}")
check("note says not submitted", "not" in r.get("note", "").lower())
check("grievance_id present", bool(r.get("grievance_id")))
gid = r.get("grievance_id", "")

# 6. Confirm grievance
print("\n--- Confirm grievance ---")
if gid:
    rc = post("/api/confirm-grievance", {"grievance_id": gid, "confirmed": True})
    check("success = True", rc["success"] is True)
    check("status = request_created", rc["status"] == "request_created", f"status={rc['status']}")
    check("submission_status = ready_for_submission", rc["submission_status"] == "ready_for_submission")
    check("tracking_id starts with DHV-", rc.get("tracking_id","").startswith("DHV-"))
    check("note says NOT submitted to gov", "not" in rc.get("note","").lower())
    tid = rc.get("tracking_id", "")

    # 7. Track by DHV ID
    print("\n--- Track by DHV ID ---")
    rt = get(f"/api/track/{tid}")
    check("status = request_created", rt["status"] == "request_created")
    check("submission_status = ready_for_submission", rt["submission_status"] == "ready_for_submission")
    check("note present (truthful)", bool(rt.get("note")))
else:
    print("  [SKIP] Skipping confirm and track (no grievance_id)")

# 8. Unknown query
print("\n--- Unknown / unrelated query ---")
r = post("/api/process", {"text": "I like watching movies.", "language": "en"})
check("intent = unknown OR confidence low", r["intent"] == "unknown" or r.get("confidence", 1.0) < 0.55)
check("suggestions present", bool(r.get("suggestions")))

# 9. Invalid tracking ID
print("\n--- Invalid tracking ID ---")
try:
    get("/api/track/INVALID-9999")
    check("404 for invalid ID", False, "Should have raised 404")
except urllib.error.HTTPError as e:
    check("404 for invalid ID", e.code == 404, f"HTTP {e.code}")

# 10. /api/schemes
print("\n--- /api/schemes ---")
s = get("/api/schemes")
check("count = 12", s["count"] == 12)
check("verified field present", all("verified" in sc for sc in s["schemes"]))

# 11. Frontend loads
print("\n--- Frontend loads ---")
with urllib.request.urlopen(BASE + "/") as resp:
    html = resp.read().decode("utf-8", errors="replace")
check("Dhvaani in HTML", "Dhvaani" in html)
check("Updated confirm button text", "Create Dhvaani Request" in html)
check("Updated tracking header", "DHVAANI REQUEST CREATED" in html)

# Summary
total = len(results)
passed = sum(1 for s, _ in results if s == "PASS")
failed = total - passed

print("\n" + "=" * 60)
print(f"  LIVE RESULTS: {passed} passed / {failed} failed / {total} total")
print("=" * 60)
if failed == 0:
    print("  ALL LIVE TESTS PASSED!")
else:
    print("  Failed checks:")
    for s, label in results:
        if s == "FAIL":
            print(f"    - {label}")
print()

sys.exit(0 if failed == 0 else 1)
