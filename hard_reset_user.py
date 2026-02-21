#!/usr/bin/env python3
"""
Hard Reset Script for a single user.
Cleans all DB state, verifies no on-chain funds stuck in DM or BOT,
and leaves the user ready for a clean re-onboard.

Usage:
    python hard_reset_user.py --user-id 22
    python hard_reset_user.py --user-id 22 --dry-run   # preview only
"""

import argparse
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal

DATABASE_URL = os.environ.get("DATABASE_URL")

TOKENS = {
    "WBTC": {"address": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f", "decimals": 8},
    "WETH": {"address": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", "decimals": 18},
    "DAI":  {"address": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1", "decimals": 18},
    "USDC": {"address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", "decimals": 6},
    "USDT": {"address": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", "decimals": 6},
}

ERC20_BALANCE_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def db_reset(user_id, dry_run=False):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print_section(f"DB RESET for user_id={user_id}")

    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    if not user:
        print(f"[ERROR] User {user_id} not found in users table.")
        conn.close()
        return None
    wallet = user["wallet_address"]
    print(f"  User: id={user_id}, wallet={wallet}")
    print(f"  bot_enabled={user['bot_enabled']}, last_seen={user['last_seen']}")

    cur.execute("SELECT COUNT(*) as cnt FROM managed_wallets WHERE user_id=%s", (user_id,))
    mw_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM defi_positions WHERE user_id=%s", (user_id,))
    dp_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM wallet_actions WHERE user_id=%s", (user_id,))
    wa_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM income_events WHERE user_id=%s", (user_id,))
    ie_count = cur.fetchone()["cnt"]

    print(f"\n  Current row counts:")
    print(f"    managed_wallets:  {mw_count}")
    print(f"    defi_positions:   {dp_count}")
    print(f"    wallet_actions:   {wa_count}")
    print(f"    income_events:    {ie_count}")

    if dry_run:
        print("\n  [DRY RUN] No changes will be made.")
        conn.close()
        return wallet

    print("\n  Executing reset...")

    cur.execute("""
        UPDATE managed_wallets
        SET delegation_status = 'inactive',
            strategy_status = 'disabled',
            auto_supply_wbtc = FALSE,
            supplied_wbtc_amount = 0,
            last_auto_supply_at = NULL,
            last_strategy_action = NULL,
            last_strategy_at = NULL,
            last_collateral_baseline = NULL,
            delegation_mode = NULL,
            updated_at = NOW()
        WHERE user_id = %s
    """, (user_id,))
    print(f"    [OK] managed_wallets: reset {cur.rowcount} row(s)")

    cur.execute("DELETE FROM defi_positions WHERE user_id = %s", (user_id,))
    print(f"    [OK] defi_positions: deleted {cur.rowcount} row(s)")

    cur.execute("DELETE FROM wallet_actions WHERE user_id = %s", (user_id,))
    print(f"    [OK] wallet_actions: deleted {cur.rowcount} row(s)")

    cur.execute("DELETE FROM income_events WHERE user_id = %s", (user_id,))
    print(f"    [OK] income_events: deleted {cur.rowcount} row(s)")

    cur.execute("""
        UPDATE users
        SET bot_enabled = FALSE,
            last_seen = NOW()
        WHERE id = %s
    """, (user_id,))
    print(f"    [OK] users: set bot_enabled=false for {cur.rowcount} row(s)")

    conn.commit()
    print("\n  [COMMITTED] All DB changes applied.")

    cur.execute("SELECT * FROM managed_wallets WHERE user_id=%s", (user_id,))
    mw = cur.fetchone()
    if mw:
        print(f"\n  Verification — managed_wallets after reset:")
        for k in ["delegation_status", "strategy_status", "auto_supply_wbtc",
                   "supplied_wbtc_amount", "last_auto_supply_at", "delegation_mode",
                   "last_strategy_action", "last_collateral_baseline"]:
            print(f"    {k}: {mw.get(k)}")

    cur.execute("SELECT COUNT(*) as cnt FROM defi_positions WHERE user_id=%s", (user_id,))
    print(f"  defi_positions remaining: {cur.fetchone()['cnt']}")
    cur.execute("SELECT COUNT(*) as cnt FROM wallet_actions WHERE user_id=%s", (user_id,))
    print(f"  wallet_actions remaining: {cur.fetchone()['cnt']}")

    conn.close()
    return wallet


def onchain_audit(wallet_address):
    print_section("ON-CHAIN BALANCE AUDIT")

    try:
        from web3 import Web3
    except ImportError:
        print("  [ERROR] web3 not installed. Skipping on-chain audit.")
        return

    rpcs = [
        os.getenv("ALCHEMY_RPC_URL", ""),
        os.getenv("ARBITRUM_RPC_URL", ""),
        "https://arb1.arbitrum.io/rpc",
        "https://arbitrum.llamarpc.com",
    ]
    w3 = None
    for url in rpcs:
        if not url:
            continue
        try:
            _w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))
            if _w3.is_connected() and _w3.eth.chain_id == 42161:
                w3 = _w3
                break
        except Exception:
            continue

    if not w3:
        print("  [ERROR] Could not connect to Arbitrum RPC. Skipping on-chain audit.")
        return

    dm_address = os.environ.get("DELEGATION_MANAGER_ADDRESS", "")
    bot_account = None
    pk = os.getenv("BOT_PRIVATE_KEY") or os.getenv("PRIVATE_KEY") or os.getenv("Wallet_PRIVATE_KEY")
    if pk:
        try:
            bot_account = w3.eth.account.from_key(pk)
        except Exception:
            pass

    addresses_to_check = {}
    if dm_address and dm_address.startswith("0x") and len(dm_address) == 42:
        addresses_to_check["DelegationManager"] = Web3.to_checksum_address(dm_address)
    if bot_account:
        addresses_to_check["Bot Wallet"] = bot_account.address

    if not addresses_to_check:
        print("  [WARN] No DM or Bot wallet address available. Cannot audit.")
        return

    print(f"  Checking balances for:")
    for name, addr in addresses_to_check.items():
        print(f"    {name}: {addr}")
    print()

    stuck_funds = []

    for token_symbol, token_info in TOKENS.items():
        token_addr = Web3.to_checksum_address(token_info["address"])
        decimals = token_info["decimals"]
        contract = w3.eth.contract(address=token_addr, abi=ERC20_BALANCE_ABI)

        for holder_name, holder_addr in addresses_to_check.items():
            try:
                raw_balance = contract.functions.balanceOf(holder_addr).call()
                human_balance = Decimal(raw_balance) / Decimal(10 ** decimals)

                status = "CLEAN" if raw_balance == 0 else "HAS BALANCE"
                marker = "  " if raw_balance == 0 else ">>"

                print(f"  {marker} {token_symbol:5s} in {holder_name:20s}: {human_balance:>20.8f}  [{status}]")

                if raw_balance > 0:
                    stuck_funds.append({
                        "token": token_symbol,
                        "holder": holder_name,
                        "holder_address": holder_addr,
                        "raw_balance": raw_balance,
                        "human_balance": float(human_balance),
                    })
            except Exception as e:
                print(f"  ?? {token_symbol:5s} in {holder_name:20s}: ERROR — {e}")

    print()
    if stuck_funds:
        print_section("STUCK FUNDS DETECTED")
        for sf in stuck_funds:
            print(f"  {sf['token']} in {sf['holder']} ({sf['holder_address']}):")
            print(f"    Balance: {sf['human_balance']:.8f} ({sf['raw_balance']} raw)")
            if sf["holder"] == "DelegationManager":
                print(f"    RESCUE: Call emergencyWithdrawToken({sf['token']}) on DM contract")
                print(f"             or transfer via DM owner to user wallet")
            elif sf["holder"] == "Bot Wallet":
                print(f"    RESCUE: Bot can transfer these tokens directly to user wallet")
            print()
    else:
        print("  [ALL CLEAN] No user-relevant tokens found in DM or Bot Wallet.")

    eth_balance_dm = None
    eth_balance_bot = None
    if "DelegationManager" in addresses_to_check:
        eth_balance_dm = w3.eth.get_balance(addresses_to_check["DelegationManager"])
        eth_dm = Decimal(eth_balance_dm) / Decimal(10**18)
        print(f"\n  ETH in DelegationManager: {eth_dm:.6f} ETH")
    if "Bot Wallet" in addresses_to_check:
        eth_balance_bot = w3.eth.get_balance(addresses_to_check["Bot Wallet"])
        eth_bot = Decimal(eth_balance_bot) / Decimal(10**18)
        print(f"  ETH in Bot Wallet:        {eth_bot:.6f} ETH (gas funds)")


def main():
    parser = argparse.ArgumentParser(description="Hard reset a user for clean re-onboard testing")
    parser.add_argument("--user-id", type=int, required=True, help="User ID to reset")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    if not DATABASE_URL:
        print("[FATAL] DATABASE_URL not set.")
        sys.exit(1)

    print(f"\n{'#'*60}")
    print(f"  HARD RESET — User {args.user_id}")
    print(f"  Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE (will modify DB)'}")
    print(f"{'#'*60}")

    wallet = db_reset(args.user_id, dry_run=args.dry_run)

    if wallet:
        onchain_audit(wallet)

    print_section("NEXT STEPS")
    print("""
  1. Clear browser localStorage:
     - User should open DevTools > Application > localStorage
     - Delete the 'reaa_wallet' key, or use a fresh/incognito browser

  2. Reconnect wallet on the dashboard

  3. Enable Auto-Pilot — the frontend will walk through:
     a) Step 1: approveDelegation() on DM contract (sets all flags)
     b) Step 2: 15 ERC20 approve() calls (5 tokens x 3 spenders)
     c) Step 3: Aave credit delegation (DAI + WETH debt tokens)
     d) Step 4: Activate on backend — triggers immediate auto-supply

  4. Monitor bot logs for clean auto-supply cycle
""")


if __name__ == "__main__":
    main()
