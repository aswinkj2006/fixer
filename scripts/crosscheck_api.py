import httpx, json, sys

BASE = "http://127.0.0.1:8765/api"
passed = []
failed = []

def check(name, ok, detail=""):
    if ok:
        passed.append(name)
        print(f"  PASS  {name}")
    else:
        failed.append(name)
        print(f"  FAIL  {name}: {detail}")

# 1. Health
try:
    r = httpx.get(f"{BASE}/health", timeout=5)
    check("GET /api/health", r.status_code == 200 and r.json().get("status") == "ok", r.text[:80])
except Exception as e:
    check("GET /api/health", False, str(e))

# 2. Machines list
try:
    r = httpx.get(f"{BASE}/machines", timeout=5)
    data = r.json()
    check("GET /api/machines (4 machines)", r.status_code == 200 and len(data) == 4, f"got {len(data)}")
    for m in data:
        has_fields = "machine_id" in m and "name" in m and "model" in m
        check(f"  Machine {m['machine_id']} has required fields", has_fields, str(list(m.keys())))
except Exception as e:
    check("GET /api/machines", False, str(e))

# 3. Individual machine
try:
    r = httpx.get(f"{BASE}/machines/M-01", timeout=5)
    data = r.json()
    check("GET /api/machines/M-01", r.status_code == 200 and data.get("machine_id") == "M-01", r.text[:80])
except Exception as e:
    check("GET /api/machines/M-01", False, str(e))

# 4. Machine tickets
try:
    r = httpx.get(f"{BASE}/machines/M-01/tickets", timeout=5)
    data = r.json()
    check("GET /api/machines/M-01/tickets (>=1 ticket)", r.status_code == 200 and len(data) >= 1, f"got {len(data)}")
except Exception as e:
    check("GET /api/machines/M-01/tickets", False, str(e))

# 5. Sensor history
try:
    r = httpx.get(f"{BASE}/sensors/M-01/history?limit=5", timeout=5)
    data = r.json()
    check("GET /api/sensors/M-01/history", r.status_code == 200, f"got {len(data)} readings")
except Exception as e:
    check("GET /api/sensors/M-01/history", False, str(e))

# 6. Admin triggers
try:
    r = httpx.get(f"{BASE}/admin/triggers", timeout=5)
    data = r.json()
    check("GET /api/admin/triggers (>=3)", r.status_code == 200 and len(data) >= 3, f"got {len(data)}")
except Exception as e:
    check("GET /api/admin/triggers", False, str(e))

# 7. Chat M-01
try:
    r = httpx.post(f"{BASE}/chat/M-01", data={"symptom_text": "Grinding noise near J2 bearing, running hot"}, timeout=20)
    data = r.json()
    has_ticket = "ticket_id" in data
    has_diag = isinstance(data.get("diagnosis"), dict) and "ranked_diagnoses" in data["diagnosis"]
    has_decision = "decision" in data
    rag_chunks = data.get("diagnosis", {}).get("rag_context_used", {}).get("manual_chunks_retrieved", 0)
    has_rag = rag_chunks > 0
    action = data.get("decision", {}).get("action", "")
    decision_valid = action in ("self_resolve", "escalate")
    check("POST /api/chat/M-01 returns ticket", r.status_code == 200 and has_ticket, f"status={r.status_code}")
    check("POST /api/chat/M-01 has ranked_diagnoses", has_diag)
    check("POST /api/chat/M-01 decision has action", has_decision and decision_valid, f"action={action}")
    check("POST /api/chat/M-01 real RAG used", has_rag, f"manual_chunks={rag_chunks}")
    if has_ticket:
        print(f"         ticket_id={data['ticket_id'][:8]}... severity={data['diagnosis'].get('severity')} action={action}")
except Exception as e:
    check("POST /api/chat/M-01", False, str(e))

# 8. Chat M-03 (critical severity should escalate)
try:
    r = httpx.post(f"{BASE}/chat/M-03", data={"symptom_text": "Motor bearing very hot, belt slipping"}, timeout=20)
    data = r.json()
    severity = data.get("diagnosis", {}).get("severity", "")
    action = data.get("decision", {}).get("action", "")
    check("POST /api/chat/M-03 severity=critical", severity == "critical", f"got severity={severity}")
    check("POST /api/chat/M-03 decision=escalate", action == "escalate", f"got action={action}")
except Exception as e:
    check("POST /api/chat/M-03", False, str(e))

# 9. Chat M-04 (calibration specialist)
try:
    r = httpx.post(f"{BASE}/chat/M-04", data={"symptom_text": "Calibration drift above threshold"}, timeout=20)
    data = r.json()
    specialist = data.get("diagnosis", {}).get("specialist_required", "")
    check("POST /api/chat/M-04 specialist=calibration", specialist == "calibration", f"got specialist={specialist}")
except Exception as e:
    check("POST /api/chat/M-04", False, str(e))

# 10. Invalid machine 404
try:
    r = httpx.post(f"{BASE}/chat/X-99", data={"symptom_text": "test"}, timeout=5)
    check("POST /api/chat/X-99 returns 404", r.status_code == 404, f"got {r.status_code}")
except Exception as e:
    check("POST /api/chat/X-99", False, str(e))

# 11. WebSocket endpoint present in openapi
try:
    r = httpx.get("http://127.0.0.1:8765/openapi.json", timeout=5)
    paths = r.json().get("paths", {})
    chat_path = "/api/chat/{machine_id}" in paths
    machines_path = "/api/machines" in paths
    check("OpenAPI has /api/chat route", chat_path, str(list(paths.keys())[:8]))
    check("OpenAPI has /api/machines route", machines_path)
except Exception as e:
    check("GET /openapi.json", False, str(e))

print()
print(f"Results: {len(passed)}/{len(passed)+len(failed)} PASSED")
if failed:
    print(f"FAILED checks: {failed}")
    sys.exit(1)
else:
    print("All API endpoint checks PASSED")
