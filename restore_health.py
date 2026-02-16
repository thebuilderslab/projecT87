#!/usr/bin/env python3
"""
Restore Health — Supply all idle WETH and DAI from wallet back to Aave.
One-time script to recover HF after the Growth ghost trigger incident.
"""

import os
import sys
import time

def main():
    print("=" * 60)
    print("RESTORE HEALTH — Supply idle WETH + DAI to Aave")
    print("=" * 60)

    from arbitrum_testnet_agent import ArbitrumTestnetAgent

    print("\n🔧 Initializing agent...")
    agent = ArbitrumTestnetAgent()

    if not agent.w3 or not agent.w3.is_connected():
        print("❌ Web3 not connected")
        return False

    print(f"✅ Agent ready — wallet: {agent.account.address}")

    print("🔄 Initializing DeFi integrations...")
    if not agent.initialize_integrations():
        print("❌ Integration init failed")
        return False

    if not agent.aave:
        print("❌ Aave not available")
        return False

    print("✅ Aave ready\n")

    account_data = agent.aave.get_user_account_data()
    if account_data:
        hf_before = account_data.get('healthFactor', 0)
        print(f"📊 BEFORE — HF: {hf_before:.4f}")
    else:
        print("⚠️ Could not read account data, continuing anyway")
        hf_before = 0

    weth_address = agent.weth_address
    dai_address = agent.dai_address

    weth_balance = agent.aave.get_token_balance(weth_address)
    dai_balance = agent.aave.get_token_balance(dai_address)

    usdc_balance = 0.0
    if hasattr(agent, 'usdc_address') and agent.usdc_address:
        try:
            usdc_balance = agent._get_usdc_balance()
        except Exception:
            usdc_balance = 0.0

    print(f"\n💰 Wallet balances:")
    print(f"   WETH: {weth_balance:.8f}")
    print(f"   DAI:  {dai_balance:.6f}")
    if usdc_balance > 0:
        print(f"   🛡️ USDC:  {usdc_balance:.6f} — WHITELISTED (will send to WALLET_B, NOT sweep)")

    supplied_any = False

    if weth_balance > 0.0001:
        print(f"\n🏦 Supplying {weth_balance:.8f} WETH to Aave...")
        result = agent.aave.supply_weth_to_aave(weth_balance)
        if result:
            print(f"✅ WETH supply confirmed: {result}")
            supplied_any = True
            time.sleep(3)
        else:
            print(f"❌ WETH supply failed")
    else:
        print(f"\n⏭️ WETH balance too small to supply ({weth_balance:.8f})")

    if dai_balance > 0.1:
        supply_amount = dai_balance * 0.99
        print(f"\n🏦 Converting {supply_amount:.6f} DAI → USDT → Aave...")
        result = agent._resupply_dai_to_aave(supply_amount)
        if result:
            print(f"✅ DAI→USDT→Aave supply confirmed")
            supplied_any = True
            time.sleep(3)
        else:
            print(f"❌ DAI→USDT conversion/supply failed")
    else:
        print(f"\n⏭️ DAI balance too small to supply ({dai_balance:.6f})")

    if supplied_any:
        account_data = agent.aave.get_user_account_data()
        if account_data:
            hf_after = account_data.get('healthFactor', 0)
            print(f"\n📊 AFTER — HF: {hf_after:.4f} (was {hf_before:.4f})")
            print(f"   HF change: +{hf_after - hf_before:.4f}")
        print("\n✅ RESTORE HEALTH COMPLETE")
    else:
        print("\n⚠️ No assets were supplied — wallet may already be clean")

    return True

if __name__ == "__main__":
    main()
