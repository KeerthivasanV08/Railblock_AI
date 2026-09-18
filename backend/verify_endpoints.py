"""
Verification script for RailBlock AI backend deployment readiness.
Tests:
1. GET /
2. GET /health
3. GET /api/tasks (verifying priority distribution and non-99 values)
4. GET /api/blocks
5. GET /api/trains
6. GET /api/resources
"""

import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_endpoints():
    print("--- 1. Testing GET / ---")
    r = client.get("/")
    assert r.status_code == 200, f"GET / failed: {r.status_code} {r.text}"
    print("GET / passed:", r.json())

    print("\n--- 2. Testing GET /health ---")
    r = client.get("/health")
    assert r.status_code == 200, f"GET /health failed: {r.status_code} {r.text}"
    print("GET /health passed:", r.json())

    print("\n--- 3. Testing GET /api/tasks ---")
    r = client.get("/api/tasks?page=1&page_size=20")
    assert r.status_code == 200, f"GET /api/tasks failed: {r.status_code} {r.text}"
    tasks_data = r.json()
    items = tasks_data.get("items") or tasks_data.get("data") or tasks_data.get("records") or []
    print(f"Total tasks: {tasks_data.get('total')}, Returned: {len(items)}")
    assert len(items) > 0, "No tasks returned!"
    scores = [item.get("criticality_score") or item.get("priority_score") for item in items]
    print(f"Sample task priorities: {scores[:10]}")
    non_99 = [s for s in scores if s != 99 and s != 99.0]
    print(f"Non-99 tasks in first 20: {len(non_99)}/{len(scores)}")
    assert len(non_99) > 0, "All tasks still showing 99!"

    print("\n--- 4. Testing GET /api/blocks ---")
    r = client.get("/api/blocks?page=1&page_size=10")
    assert r.status_code == 200, f"GET /api/blocks failed: {r.status_code} {r.text}"
    blocks_data = r.json()
    b_items = blocks_data.get("items") or blocks_data.get("data") or []
    print(f"Total blocks: {blocks_data.get('total')}, Returned: {len(b_items)}")

    print("\n--- 5. Testing GET /api/trains ---")
    r = client.get("/api/trains?page=1&page_size=10")
    assert r.status_code == 200, f"GET /api/trains failed: {r.status_code} {r.text}"
    trains_data = r.json()
    t_items = trains_data.get("items") or trains_data.get("data") or []
    print(f"Total trains: {trains_data.get('total')}, Returned: {len(t_items)}")

    print("\n--- 6. Testing GET /api/resources ---")
    r = client.get("/api/resources?page=1&page_size=10")
    assert r.status_code == 200, f"GET /api/resources failed: {r.status_code} {r.text}"
    res_data = r.json()
    r_items = res_data.get("items") or res_data.get("data") or []
    print(f"Total resources: {res_data.get('total')}, Returned: {len(r_items)}")

    print("\n--- 7. Testing OpenAPI Docs schema generation ---")
    r = client.get("/openapi.json")
    assert r.status_code == 200, f"OpenAPI schema failed: {r.status_code}"
    print(f"OpenAPI schema passed: {r.json()['info']['title']}")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()
