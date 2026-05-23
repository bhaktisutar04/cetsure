"""
test_api.py — In-memory integration tests for FastAPI backend (F3)

Usage:
  python backend/test_api.py
"""

import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from fastapi.testclient import TestClient
    from backend.main import app
except ImportError as e:
    print(f"Missing dependencies to run this test script in-memory: {e}")
    print("Please install requirements first: pip install -r backend/requirements.txt")
    sys.exit(0)


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ")
    print("=" * 80)


def main():
    client = TestClient(app)
    
    # 1. Health Check (unprotected)
    print_section("Testing GET /health (Public)")
    resp = client.get("/health")
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.json()}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    print("SUCCESS: /health endpoint working publicly.")

    # 2. Verify Authentication Protection (Expecting 401 Unauthorized)
    print_section("Testing Authentication Protection (Expecting 401)")
    
    # Predict without token
    resp = client.post("/predict", json={
        "percentile": 87.0,
        "category": "GOPENS",
        "branch": "Computer Engineering"
    })
    print(f"POST /predict (No token) Status Code: {resp.status_code}")
    assert resp.status_code == 401
    
    # College details without token
    resp = client.get("/college/6271")
    print(f"GET /college/6271 (No token) Status Code: {resp.status_code}")
    assert resp.status_code == 401

    # Search without token
    resp = client.get("/search?q=COEP")
    print(f"GET /search?q=COEP (No token) Status Code: {resp.status_code}")
    assert resp.status_code == 401
    print("SUCCESS: Authenticator correctly blocks requests without tokens with 401.")

    # 3. Setup Dependency Override for Successful Flows
    print_section("Configuring Mock Firebase User Dependency Override")
    from backend.auth.firebase_auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"uid": "test_user_id", "email": "test@cetsure.com"}

    # 4. Predict Endpoint (Authenticated)
    print_section("Testing POST /predict (percentile=87, category=GOPENS, CS - Authenticated)")
    payload = {
        "percentile": 87.0,
        "category": "GOPENS",
        "branch": "Computer Engineering",
        "district": "Pune",
        "quota": "MH"
    }
    resp = client.post("/predict", json=payload)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        res_data = resp.json()
        print(f"Total Colleges Found: {res_data['meta']['total_colleges']}")
        print(f"  - SAFE:     {len(res_data['safe'])}")
        print(f"  - MODERATE: {len(res_data['moderate'])}")
        print(f"  - REACH:    {len(res_data['reach'])}")
        assert "safe" in res_data
        assert "moderate" in res_data
        assert "reach" in res_data
        print("SUCCESS: /predict endpoint working when authenticated.")
    else:
        print(f"FAILURE: Status {resp.status_code}, detail: {resp.text}")
        assert False

    # 5. College Detail Endpoint (Authenticated)
    print_section("Testing GET /college/6271 (PICT Pune - Authenticated)")
    resp = client.get("/college/6271")
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        res_data = resp.json()
        print(f"College: {res_data['college_name']}")
        print(f"Total Cutoff Records: {len(res_data['cutoffs'])}")
        print(f"Sample Cutoff: {res_data['cutoffs'][0]}")
        assert res_data["college_code"] == "6271"
        assert len(res_data["cutoffs"]) > 0
        print("SUCCESS: /college/{college_code} endpoint working when authenticated.")
    else:
        print(f"FAILURE: Status {resp.status_code}, detail: {resp.text}")
        assert False

    # 6. College Search Endpoint (Authenticated)
    print_section("Testing GET /search?q=COEP (Authenticated)")
    resp = client.get("/search?q=COEP")
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        res_data = resp.json()
        print(f"Total Results: {len(res_data['results'])}")
        for r in res_data['results'][:3]:
            print(f"  [{r['college_code']}] {r['college_name']}")
        assert len(res_data["results"]) > 0
        print("SUCCESS: /search endpoint working when authenticated.")
    else:
        print(f"FAILURE: Status {resp.status_code}, detail: {resp.text}")
        assert False

    # 7. Invalid Percentile Range Validation (Authenticated)
    print_section("Testing POST /predict with invalid percentile (200 - Authenticated)")
    payload = {
        "percentile": 200.0,
        "category": "GOPENS",
        "branch": "Computer Engineering",
    }
    resp = client.post("/predict", json=payload)
    print(f"Status Code: {resp.status_code} (Expected: 422)")
    assert resp.status_code == 422
    print("SUCCESS: Invalid percentile correctly triggered validation error (422).")

    print_section("ALL IN-MEMORY INTEGRATION TESTS COMPLETED")


if __name__ == "__main__":
    main()
