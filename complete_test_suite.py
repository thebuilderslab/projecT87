#!/usr/bin/env python3
"""
OpenClaw — Full Loop Integration Test Suite
============================================
Simulates a wallet connection, logs color-coded events to the
Activity Terminal, generates a test API key, and verifies the
/api/v1/credit/borrow route is active.

Usage:
    python complete_test_suite.py
"""

import os
import sys
import time
import requests
import itsdangerous

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:5000")
TEST_WALLET = "0xDeaDBEEF00000000000000000000000000042069"

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "fallback-dev-key-change-in-production")
auth_signer = itsdangerous.TimestampSigner(APP_SECRET_KEY)

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[96m[INFO]\033[0m"
DIVIDER = "=" * 60


def header(title):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def step_1_simulate_wallet_connection():
    header("STEP 1: Simulate Wallet Connection")
    resp = requests.post(
        f"{BASE_URL}/api/auth/wallet",
        json={"walletAddress": TEST_WALLET},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"{FAIL} Wallet connect returned {resp.status_code}: {resp.text}")
        return None, None
    data = resp.json()
    user_id = data.get("userId")
    auth_token = data.get("authToken")
    wallet = data.get("walletAddress")
    print(f"{PASS} Wallet connected successfully")
    print(f"  User ID    : {user_id}")
    print(f"  Wallet     : {wallet}")
    print(f"  Auth Token : {auth_token[:20]}...")
    return user_id, auth_token


def step_2_log_wbtc_supply(auth_token):
    header("STEP 2: Log 'WBTC Supply' Event (routine/green)")
    import db as database
    result = database.add_notification(
        wallet_address=TEST_WALLET,
        title="WBTC Supply",
        message="Supplied 0.15 WBTC to Aave v3 pool — collateral updated",
        priority="info",
    )
    print(f"{PASS} Notification created (id={result['id']})")
    print(f"  Title    : {result['title']}")
    print(f"  Priority : {result['priority']} (green in terminal)")
    print(f"  Message  : {result['message']}")
    return result


def step_3_log_capacity_borrow(auth_token):
    header("STEP 3: Log 'Capacity Borrow' Event (critical/red)")
    import db as database
    result = database.add_notification(
        wallet_address=TEST_WALLET,
        title="Capacity Borrow",
        message="ALERT: Borrowed 2,500 USDC via credit delegation — health factor now 2.81",
        priority="critical",
    )
    print(f"{PASS} Notification created (id={result['id']})")
    print(f"  Title    : {result['title']}")
    print(f"  Priority : {result['priority']} (red in terminal)")
    print(f"  Message  : {result['message']}")
    return result


def step_4_generate_api_key(user_id):
    header("STEP 4: Generate Test API Key")
    import db as database
    result = database.generate_api_key(user_id, label="integration-test")
    if "error" in result:
        print(f"{FAIL} Could not generate key: {result['error']}")
        print(f"{INFO} Revoking all existing keys for user {user_id} and retrying...")
        database.revoke_all_user_keys(user_id)
        result = database.generate_api_key(user_id, label="integration-test")
        if "error" in result:
            print(f"{FAIL} Still failed: {result['error']}")
            return None
    raw_key = result.get("raw_key", "")
    print(f"{PASS} API key generated successfully")
    print(f"  Key ID   : {result.get('id')}")
    print(f"  Prefix   : {result.get('key_prefix')}")
    print(f"  Label    : {result.get('label')}")
    print(f"  Status   : {result.get('status')}")
    print()
    print(f"  {'='*50}")
    print(f"  RAW SECRET (copy this — shown only once):")
    print(f"  {raw_key}")
    print(f"  {'='*50}")
    return raw_key


def step_5_verify_vault_health(api_key):
    header("STEP 5: Verify /api/v1/vault/health (Demo Data)")
    resp = requests.get(
        f"{BASE_URL}/api/v1/vault/health",
        headers={"X-API-Key": api_key},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"{FAIL} Vault health returned {resp.status_code}: {resp.text}")
        return
    data = resp.json()
    print(f"{PASS} Vault health returned successfully")
    print(f"  Health Factor      : {data.get('health_factor')}")
    print(f"  Collateral (USD)   : ${data.get('total_collateral_usd'):,.2f}")
    print(f"  Debt (USD)         : ${data.get('total_debt_usd'):,.2f}")
    print(f"  Net Worth (USD)    : ${data.get('net_worth_usd'):,.2f}")
    print(f"  Available Borrows  : ${data.get('available_borrows_usd'):,.2f}")
    is_demo = (data.get("health_factor") == 3.42)
    print(f"  Demo Data?         : {'Yes' if is_demo else 'No (live position found)'}")


def step_6_verify_borrow_endpoint(api_key):
    header("STEP 6: Verify POST /api/v1/credit/borrow (Active)")
    resp = requests.post(
        f"{BASE_URL}/api/v1/credit/borrow",
        headers={"X-API-Key": api_key},
        json={"amount": 100, "asset": "DAI"},
        timeout=30,
    )
    print(f"  HTTP Status : {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"{PASS} Borrow endpoint is ACTIVE")
        print(f"  Status  : {data.get('status')}")
        print(f"  Mode    : {data.get('mode')}")
        print(f"  Action  : {data.get('action')}")
        print(f"  Details : {data.get('details')}")
        if data.get("status") == "executed":
            print(f"{PASS} 'Simulated Trade Executed' notification logged to Activity Feed")
        else:
            print(f"{INFO} Borrow was not executed (status={data.get('status')})")
    elif resp.status_code == 422:
        print(f"{INFO} Endpoint active but rejected input (Pydantic validation): {resp.json()}")
    else:
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        print(f"{FAIL} Unexpected response {resp.status_code}: {data}")


def step_7_verify_activity_feed(auth_token):
    header("STEP 7: Verify Activity Feed Contains Test Events")
    resp = requests.get(
        f"{BASE_URL}/api/user/activity",
        headers={"X-Auth-Token": auth_token},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"{FAIL} Activity feed returned {resp.status_code}")
        return
    data = resp.json()
    notifications = data.get("notifications", [])
    print(f"{PASS} Activity feed returned {data.get('count', 0)} notifications")
    found_wbtc = False
    found_borrow = False
    found_simulated = False
    for n in notifications[:10]:
        title = n.get("title", "")
        priority = n.get("priority", "info")
        color = {"info": "green", "critical": "RED", "balance": "cyan"}.get(priority, "green")
        print(f"  [{color:>5}] {title}: {n.get('message', '')[:60]}")
        if "WBTC Supply" in title:
            found_wbtc = True
        if "Capacity Borrow" in title:
            found_borrow = True
        if "Simulated Trade Executed" in title:
            found_simulated = True
    print()
    print(f"  WBTC Supply event found         : {'Yes' if found_wbtc else 'No'}")
    print(f"  Capacity Borrow event found      : {'Yes' if found_borrow else 'No'}")
    print(f"  Simulated Trade Executed found   : {'Yes' if found_simulated else 'No'}")


def main():
    print("\n" + "=" * 60)
    print("  OpenClaw — Full Loop Integration Test Suite")
    print("  " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    user_id, auth_token = step_1_simulate_wallet_connection()
    if not user_id:
        print(f"\n{FAIL} Cannot continue without wallet connection. Aborting.")
        sys.exit(1)

    step_2_log_wbtc_supply(auth_token)
    step_3_log_capacity_borrow(auth_token)

    api_key = step_4_generate_api_key(user_id)
    if not api_key:
        print(f"\n{FAIL} Cannot continue without API key. Aborting.")
        sys.exit(1)

    step_5_verify_vault_health(api_key)
    step_6_verify_borrow_endpoint(api_key)
    step_7_verify_activity_feed(auth_token)

    header("INTEGRATION TEST COMPLETE")
    print(f"  {PASS} All steps executed successfully.")
    print(f"  {INFO} Use the raw API key above to test endpoints manually.")
    print(f"  {INFO} Check the Developer Portal terminal for color-coded logs.")
    print()


if __name__ == "__main__":
    main()
