"""
Quick verification of all Day 4 API endpoints
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

print("Testing Day 4 Endpoints...")

# 1. Fleet overview
res = client.get("/api/machines")
assert res.status_code == 200, f"Machines failed: {res.status_code}"
machines = res.json()
print(f"Fleet machines count: {len(machines)}")
for m in machines:
    mid = m["machine_id"]
    hs = m["health_score"]
    st = m["health_status"]
    oee = m["oee_pct"]
    win = m["predicted_service_window"]
    print(f"  {mid}: Health={hs} ({st}) | OEE={oee}% | Window={win}")

# 2. Machine health
h_res = client.get("/api/machines/M-01/health")
assert h_res.status_code == 200
print(f"M-01 Health check: status={h_res.json()['status']}, score={h_res.json()['health_score']}")

# 3. Machine RUL
rul_res = client.get("/api/machines/M-01/rul")
assert rul_res.status_code == 200
print(f"M-01 RUL: window={rul_res.json()['service_window']}, is_heuristic={rul_res.json()['is_heuristic']}")

# 4. Recurring faults
rf_res = client.get("/api/machines/M-01/recurring-faults")
assert rf_res.status_code == 200
print(f"M-01 Recurring clusters: count={rf_res.json()['cluster_count']}")

# 5. Fleet leaderboard
fl_res = client.get("/api/fleet/recurring-faults")
assert fl_res.status_code == 200
print(f"Fleet leaderboard count: {fl_res.json()['count']}")
if fl_res.json()["leaderboard"]:
    top = fl_res.json()["leaderboard"][0]
    print(f"  Top recurring: #{top['rank']} {top['machine_id']} {top['pattern_name']} (occurred {top['occurrence_count']}x)")

print("\n[OK] ALL DAY 4 API ENDPOINTS WORKING PERFECTLY!")
