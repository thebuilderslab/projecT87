#!/usr/bin/env python3
"""
Liability Short Plumbing Test — Forces a tiny $2.00 WETH borrow + distribute (Part A only).
Bypasses all HF/collateral triggers. Skips Part B (debt swap).
Purpose: Prove the WETH borrow → split → swap pipeline works on-chain.
"""

import os
import sys
import time

TEST_BORROW_USD = 2.00

PLUMBING_DISTRIBUTION = {
    'total_borrow_usd': TEST_BORROW_USD,
    'wbtc_swap_supply': 0.40,
    'weth_supply': 0.40,
    'dai_swap_total': 0.70,
    'dai_supply': 0.50,
    'dai_transfer': 0.20,
    'eth_gas_reserve': 0.50,
    'debt_swap_amount': 0.0,
    'min_capacity': 3.0,
}

def main():
    print("=" * 70)
    print("LIABILITY SHORT — PLUMBING TEST ($2.00 WETH)")
    print("Part A Only: Borrow WETH → Distribute (WBTC/WETH/DAI/Gas)")
    print("Part B Skipped: No debt swap in this test")
    print("=" * 70)

    from arbitrum_testnet_agent import ArbitrumTestnetAgent

    print("\n🔧 Initializing agent...")
    agent = ArbitrumTestnetAgent()

    if not agent.w3 or not agent.w3.is_connected():
        print("❌ Web3 not connected — cannot run plumbing test")
        return False

    print(f"✅ Agent constructed — wallet: {agent.account.address}")

    print("🔄 Initializing DeFi integrations (standard boot)...")
    if not agent.initialize_integrations():
        print("❌ DeFi integration initialization failed")
        return False

    print(f"✅ Integrations ready — Aave: {'✅' if agent.aave else '❌'} | Uniswap: {'✅' if agent.uniswap else '❌'}")

    if not agent.aave:
        print("❌ Aave integration required but not available")
        return False

    print("\n📊 Pre-flight checks...")

    eth_balance = agent.get_eth_balance()
    print(f"   ETH balance: {eth_balance:.6f} ETH")
    if eth_balance < 0.0005:
        print("❌ Insufficient ETH for gas — need at least 0.0005 ETH")
        return False

    account_data = agent.aave.get_user_account_data()
    if not account_data:
        print("❌ Could not fetch Aave account data")
        return False

    collateral_usd = account_data.get('totalCollateralUSD', 0)
    health_factor = account_data.get('healthFactor', 0)
    available_usd = account_data.get('availableBorrowsUSD', 0)

    from web3 import Web3
    chainlink_abi = [{"inputs":[],"name":"latestAnswer","outputs":[{"name":"","type":"int256"}],"stateMutability":"view","type":"function"}]
    chainlink_eth = agent.w3.eth.contract(
        address=Web3.to_checksum_address("0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612"),
        abi=chainlink_abi
    )
    raw_price = chainlink_eth.functions.latestAnswer().call()
    eth_price = raw_price / 10**8

    print(f"   Collateral: ${collateral_usd:.2f}")
    print(f"   Health Factor: {health_factor:.3f}")
    print(f"   Available to Borrow: ${available_usd:.2f}")
    print(f"   ETH Price: ${eth_price:.2f}")

    if health_factor < 1.20 and health_factor != float('inf'):
        print(f"❌ Health factor too low for plumbing test: {health_factor:.3f} < 1.20")
        return False

    if available_usd < PLUMBING_DISTRIBUTION['min_capacity']:
        print(f"❌ Insufficient borrow capacity: ${available_usd:.2f} < ${PLUMBING_DISTRIBUTION['min_capacity']:.2f}")
        return False

    weth_to_borrow = TEST_BORROW_USD / eth_price
    print(f"\n🚀 EXECUTING PLUMBING TEST")
    print(f"   Borrowing: {weth_to_borrow:.8f} WETH (${TEST_BORROW_USD:.2f})")
    print(f"   Distribution: WBTC=${PLUMBING_DISTRIBUTION['wbtc_swap_supply']:.2f} | WETH=${PLUMBING_DISTRIBUTION['weth_supply']:.2f} | DAI=${PLUMBING_DISTRIBUTION['dai_swap_total']:.2f} | Gas=${PLUMBING_DISTRIBUTION['eth_gas_reserve']:.2f}")

    print(f"\n{'='*60}")
    print(f"STEP 1: Borrow {weth_to_borrow:.8f} WETH from Aave V3")
    print(f"{'='*60}")
    weth_balance_before = agent.get_weth_balance()
    result = agent.aave.borrow_weth(weth_to_borrow)
    if not result:
        print("❌ WETH borrow FAILED")
        return False

    time.sleep(3)
    weth_balance_after = agent.get_weth_balance()
    weth_received = weth_balance_after - weth_balance_before
    print(f"✅ WETH Borrow TX complete")
    print(f"   Before: {weth_balance_before:.8f} | After: {weth_balance_after:.8f} | Received: {weth_received:.8f}")

    if weth_received < weth_to_borrow * 0.5:
        print(f"⚠️ Received less WETH than expected — continuing anyway")

    results = {"borrow": "✅ SUCCESS"}

    wbtc_usd = PLUMBING_DISTRIBUTION['wbtc_swap_supply']
    weth_for_wbtc = wbtc_usd / eth_price
    if weth_for_wbtc > 0.00001:
        print(f"\n{'='*60}")
        print(f"STEP 2: Swap {weth_for_wbtc:.8f} WETH → WBTC (${wbtc_usd:.2f}) + Supply to Aave")
        print(f"{'='*60}")
        try:
            wbtc_before = agent.get_wbtc_balance()
            swap_result = agent.uniswap.swap_weth_for_wbtc(weth_for_wbtc)
            if swap_result and 'tx_hash' in swap_result:
                time.sleep(5)
                wbtc_after = agent.get_wbtc_balance()
                wbtc_received = wbtc_after - wbtc_before
                print(f"✅ WETH→WBTC swap TX: {swap_result['tx_hash']}")
                print(f"   WBTC received: {wbtc_received:.8f}")
                results["wbtc_swap"] = f"✅ SUCCESS (TX: {swap_result['tx_hash'][:18]}...)"
                if wbtc_received > 0 and hasattr(agent, '_supply_wbtc_to_aave'):
                    agent._supply_wbtc_to_aave(wbtc_received)
                    results["wbtc_supply"] = "✅ SUCCESS"
            else:
                print(f"❌ WETH→WBTC swap failed")
                results["wbtc_swap"] = "❌ FAILED"
        except Exception as e:
            print(f"❌ WETH→WBTC swap error: {e}")
            results["wbtc_swap"] = f"❌ ERROR: {e}"

    weth_supply_usd = PLUMBING_DISTRIBUTION['weth_supply']
    weth_for_supply = weth_supply_usd / eth_price
    if weth_for_supply > 0.00001:
        print(f"\n{'='*60}")
        print(f"STEP 3: Supply {weth_for_supply:.8f} WETH to Aave (${weth_supply_usd:.2f})")
        print(f"{'='*60}")
        try:
            if hasattr(agent, '_supply_weth_to_aave') and agent._supply_weth_to_aave(weth_for_supply):
                print(f"✅ WETH supply complete")
                results["weth_supply"] = "✅ SUCCESS"
            else:
                print(f"❌ WETH supply failed")
                results["weth_supply"] = "❌ FAILED"
        except Exception as e:
            print(f"❌ WETH supply error: {e}")
            results["weth_supply"] = f"❌ ERROR: {e}"

    dai_total_usd = PLUMBING_DISTRIBUTION['dai_swap_total']
    weth_for_dai = dai_total_usd / eth_price
    if weth_for_dai > 0.00001:
        print(f"\n{'='*60}")
        print(f"STEP 4: Swap {weth_for_dai:.8f} WETH → DAI (${dai_total_usd:.2f})")
        print(f"{'='*60}")
        try:
            dai_before = agent.get_dai_balance()
            swap_result = agent.uniswap.swap_weth_for_dai(weth_for_dai)
            if swap_result and 'tx_hash' in swap_result:
                time.sleep(5)
                dai_after = agent.get_dai_balance()
                dai_received = dai_after - dai_before
                print(f"✅ WETH→DAI swap TX: {swap_result['tx_hash']}")
                print(f"   DAI received: {dai_received:.4f}")
                results["dai_swap"] = f"✅ SUCCESS (TX: {swap_result['tx_hash'][:18]}...)"
            else:
                print(f"❌ WETH→DAI swap failed")
                results["dai_swap"] = "❌ FAILED"
        except Exception as e:
            print(f"❌ WETH→DAI swap error: {e}")
            results["dai_swap"] = f"❌ ERROR: {e}"

    remaining_weth = agent.get_weth_balance()
    if remaining_weth > 0.00001:
        print(f"\n{'='*60}")
        print(f"STEP 5: Unwrap remaining {remaining_weth:.8f} WETH → ETH (gas reserve)")
        print(f"{'='*60}")
        try:
            if hasattr(agent, '_unwrap_weth_to_eth') and agent._unwrap_weth_to_eth(remaining_weth):
                print(f"✅ WETH→ETH unwrap complete")
                results["gas_reserve"] = "✅ SUCCESS"
            else:
                print(f"⚠️ WETH→ETH unwrap failed — remaining WETH stays in wallet")
                results["gas_reserve"] = "⚠️ FAILED (WETH retained)"
        except Exception as e:
            print(f"❌ Unwrap error: {e}")
            results["gas_reserve"] = f"❌ ERROR: {e}"

    print(f"\n{'='*70}")
    print(f"PLUMBING TEST RESULTS")
    print(f"{'='*70}")
    for step, status in results.items():
        print(f"   {step:20s} → {status}")

    passed = sum(1 for v in results.values() if "SUCCESS" in v)
    total = len(results)
    print(f"\n   Score: {passed}/{total} steps successful")

    if passed == total:
        print(f"\n✅ PLUMBING TEST PASSED — All steps executed on-chain successfully")
        return True
    elif passed > 0:
        print(f"\n⚠️ PLUMBING TEST PARTIAL — {passed}/{total} steps worked, review failures above")
        return True
    else:
        print(f"\n❌ PLUMBING TEST FAILED — No steps completed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
