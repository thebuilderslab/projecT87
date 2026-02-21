import requests
import json
import os

API_URL = os.getenv("OPENCLAW_API_URL", "http://localhost:5000")
API_KEY = os.getenv("OPENCLAW_API_KEY", "your_generated_raw_api_key_here")

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def run_agent_test():
    print("=" * 60)
    print("OpenClaw Agent Simulation")
    print("=" * 60)

    print("\n[TEST 0] API Health Check...")
    try:
        resp = requests.get(f"{API_URL}/api/v1/health", timeout=10)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"  FAILED: {e}")
        print("  Server may not be running. Aborting.")
        return

    print("\n[TEST 1] Vault Health (authenticated)...")
    try:
        resp = requests.get(f"{API_URL}/api/v1/vault/health", headers=headers, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {json.dumps(resp.json(), indent=2)}")
        if resp.status_code == 401:
            print("  Authentication failed. Check your API key.")
            return
    except Exception as e:
        print(f"  FAILED: {e}")
        return

    print("\n[TEST 2] Notifications (authenticated)...")
    try:
        resp = requests.get(f"{API_URL}/api/v1/notifications", headers=headers, timeout=10)
        print(f"  Status: {resp.status_code}")
        data = resp.json()
        print(f"  Notification count: {len(data)}")
        for n in data[:3]:
            print(f"    [{n.get('priority','')}] {n.get('title','')}: {n.get('message','')[:80]}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[TEST 3] Credit Borrow (authenticated)...")
    payload = {
        "amount": 100.0,
        "asset": "USDC"
    }
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/credit/borrow",
            headers=headers,
            json=payload,
            timeout=60
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[TEST 4] Reject invalid asset...")
    bad_payload = {"amount": 50.0, "asset": "INVALID_TOKEN"}
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/credit/borrow",
            headers=headers,
            json=bad_payload,
            timeout=10
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[TEST 5] Reject risk parameter injection...")
    risky_payload = {
        "amount": 100.0,
        "asset": "USDC",
        "health_factor_min": 1.0,
        "collateral_threshold": 0.5
    }
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/credit/borrow",
            headers=headers,
            json=risky_payload,
            timeout=10
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {json.dumps(resp.json(), indent=2)}")
        if resp.status_code == 200:
            print("  (Extra fields silently ignored by Pydantic - Black Box enforced)")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n" + "=" * 60)
    print("OpenClaw Simulation Complete")
    print("=" * 60)

if __name__ == "__main__":
    run_agent_test()
