#!/usr/bin/env python3
"""
Diagnostic script for delegated wallet 0xd60a...5cff
Reads all DelegationManager flags, 15 ERC20 allowances, and DB state.
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.dirname(__file__))
from delegation_client import (
    validate_full_automation_ready,
    get_delegation_permissions,
    get_erc20_allowance,
    REQUIRED_APPROVAL_TOKENS,
    REQUIRED_APPROVAL_CONTRACTS,
    TOKEN_NAMES,
    MIN_REQUIRED_ALLOWANCE,
)

WALLET = "0xd60acbac798f146e4b7080e9a1f93977200f5cff"
USER_ID = 22


def main():
    print(f"{'='*60}")
    print(f"  REAA Wallet Diagnostic: {WALLET[:10]}...{WALLET[-4:]}")
    print(f"{'='*60}\n")

    print("1. DelegationManager Flags")
    print("-" * 40)
    perms = get_delegation_permissions(WALLET)
    for key in ["isActive", "allowSupply", "allowBorrow", "allowRepay", "allowWithdraw"]:
        val = perms.get(key, False)
        status = "OK" if val else "MISSING"
        print(f"  {key:20s} = {val}  [{status}]")
    if perms.get("maxSupplyPerTx"):
        print(f"  {'maxSupplyPerTx':20s} = {perms['maxSupplyPerTx']}")
    if perms.get("dailySupplyLimit"):
        print(f"  {'dailySupplyLimit':20s} = {perms['dailySupplyLimit']}")

    print(f"\n2. ERC20 Approvals (5 tokens x 3 contracts = 15)")
    print("-" * 40)
    missing_approvals = []
    for token_addr in REQUIRED_APPROVAL_TOKENS:
        token_name = TOKEN_NAMES.get(token_addr, token_addr[:10])
        for spender_name, spender_addr in REQUIRED_APPROVAL_CONTRACTS.items():
            if not spender_addr:
                continue
            allowance = get_erc20_allowance(token_addr, WALLET, spender_addr)
            status = "OK" if allowance >= MIN_REQUIRED_ALLOWANCE else "MISSING"
            print(f"  {token_name:6s} -> {spender_name:20s}: {status} (raw: {allowance})")
            if allowance < MIN_REQUIRED_ALLOWANCE:
                missing_approvals.append(f"{token_name} -> {spender_name}")

    print(f"\n3. Database State")
    print("-" * 40)
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT delegation_status, strategy_status, delegation_mode, auto_supply_wbtc, last_strategy_action, last_auto_supply_at FROM managed_wallets WHERE user_id = %s AND wallet_address = %s", (USER_ID, WALLET))
        mw = cur.fetchone()
        if mw:
            for k, v in dict(mw).items():
                print(f"  {k:25s} = {v}")
        else:
            print("  No managed_wallets row found")

        cur.execute("SELECT health_factor, total_collateral_usd, total_debt_usd, has_active_position, consecutive_empty_count FROM defi_positions WHERE user_id = %s AND wallet_address = %s", (USER_ID, WALLET))
        pos = cur.fetchone()
        if pos:
            print(f"\n  DeFi Position:")
            for k, v in dict(pos).items():
                print(f"    {k:25s} = {v}")
        else:
            print("  No defi_positions row found")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"  DB error: {e}")

    print(f"\n4. Full Validation Result")
    print("-" * 40)
    result = validate_full_automation_ready(WALLET)
    print(f"  Ready: {result['ready']}")
    print(f"  Blockers: {len(result.get('blockers', []))}")
    for b in result.get("blockers", []):
        print(f"    - {b['type']}: {b.get('missing', b.get('token', ''))}")

    print(f"\n5. Summary")
    print("=" * 60)
    missing_flags = [f for f in ["allowBorrow", "allowRepay", "allowWithdraw"] if not perms.get(f, False)]
    if missing_flags:
        print(f"  CONTRACT FLAGS MISSING: {', '.join(missing_flags)}")
        print(f"  FIX: User must sign approveDelegation(maxUint, maxUint, true, true, true, true)")
        print(f"  ACTION: Click 'Re-authorize Auto-Pilot' button on dashboard")
    else:
        print(f"  All contract flags OK")

    if missing_approvals:
        print(f"  ERC20 APPROVALS MISSING: {len(missing_approvals)}")
        for ma in missing_approvals:
            print(f"    - {ma}")
        print(f"  FIX: User signs during Re-authorize flow")
    else:
        print(f"  All 15 ERC20 approvals OK")

    ready = result['ready']
    print(f"\n  Ready for next monitoring cycle: {'YES' if ready else 'NO'}")
    if not ready:
        print(f"  Required action: User must click 'Re-authorize Auto-Pilot' on dashboard")
    print()


if __name__ == "__main__":
    main()
