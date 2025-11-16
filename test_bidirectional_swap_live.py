#!/usr/bin/env python3
"""
Live Bidirectional Debt Swap Test
Swaps 10 DAI → WETH, waits 5 minutes, then swaps WETH → DAI
"""

import os
import time
from web3 import Web3
from decimal import Decimal
from debt_swap_bidirectional import BidirectionalDebtSwapper
from datetime import datetime

def main():
    print("=" * 80)
    print("LIVE BIDIRECTIONAL DEBT SWAP TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get credentials
    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        print("❌ PRIVATE_KEY not set")
        return
    
    # Connect to Arbitrum
    rpc = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return
    
    print("✅ Connected to Arbitrum mainnet")
    print(f"   Block: {w3.eth.block_number:,}")
    
    # Initialize swapper
    swapper = BidirectionalDebtSwapper(w3, private_key)
    
    # Get initial position
    print("\n" + "=" * 80)
    print("INITIAL POSITION")
    print("=" * 80)
    initial_summary = swapper.get_account_summary()
    print(f"DAI Debt: {initial_summary['dai_debt']:.6f} DAI")
    print(f"WETH Debt: {initial_summary['weth_debt']:.6f} WETH")
    print(f"Health Factor: {initial_summary['health_factor']:.4f}")
    print(f"Total Debt: ${initial_summary['total_debt_usd']:.2f}")
    
    # Verify we have enough DAI debt
    if initial_summary['dai_debt'] < 10:
        print(f"\n❌ Insufficient DAI debt ({initial_summary['dai_debt']:.2f} DAI)")
        print("   Need at least 10 DAI debt to perform this test")
        return
    
    # ========================================================================
    # STEP 1: Swap 10 DAI → WETH
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 1: SWAP 10 DAI → WETH")
    print("=" * 80)
    print("📊 Action: Repay 10 DAI debt, borrow WETH")
    
    step1_start_block = w3.eth.block_number
    step1_start_time = datetime.now()
    
    tx_hash1 = swapper.swap_debt(
        from_asset='DAI',
        to_asset='WETH',
        amount=Decimal('10'),
        slippage_bps=100,  # 1%
        dry_run=False
    )
    
    if not tx_hash1:
        print("❌ First swap failed")
        return
    
    print(f"\n✅ Transaction confirmed!")
    print(f"   TX Hash: {tx_hash1}")
    print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash1}")
    print(f"   Block: {w3.eth.block_number:,}")
    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Get receipt to extract actual amounts
    receipt1 = w3.eth.get_transaction_receipt(tx_hash1)
    print(f"   Gas Used: {receipt1['gasUsed']:,}")
    print(f"   Status: {'Success ✅' if receipt1['status'] == 1 else 'Failed ❌'}")
    
    # Get position after first swap
    after_swap1 = swapper.get_account_summary()
    weth_borrowed = after_swap1['weth_debt'] - initial_summary['weth_debt']
    dai_repaid = initial_summary['dai_debt'] - after_swap1['dai_debt']
    
    print(f"\n📈 Swap 1 Results:")
    print(f"   DAI Repaid: {dai_repaid:.6f} DAI")
    print(f"   WETH Borrowed: {weth_borrowed:.6f} WETH")
    print(f"   New DAI Debt: {initial_summary['dai_debt']:.6f} → {after_swap1['dai_debt']:.6f}")
    print(f"   New WETH Debt: {initial_summary['weth_debt']:.6f} → {after_swap1['weth_debt']:.6f}")
    print(f"   Health Factor: {initial_summary['health_factor']:.4f} → {after_swap1['health_factor']:.4f}")
    
    # ========================================================================
    # STEP 2: Wait 5 minutes
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 2: WAIT 5 MINUTES")
    print("=" * 80)
    
    wait_seconds = 5 * 60  # 5 minutes
    average_block_time = 0.25  # Arbitrum average block time
    estimated_blocks = int(wait_seconds / average_block_time)
    
    print(f"⏱️  Waiting {wait_seconds} seconds (~{estimated_blocks} blocks)")
    print(f"   Start Block: {step1_start_block:,}")
    print(f"   Current Block: {w3.eth.block_number:,}")
    print(f"   Start Time: {step1_start_time.strftime('%H:%M:%S')}")
    
    # Wait with progress updates
    for i in range(5):
        time.sleep(60)  # Wait 1 minute
        current_block = w3.eth.block_number
        blocks_passed = current_block - step1_start_block
        print(f"   {i+1} min elapsed - Block: {current_block:,} (+{blocks_passed} blocks)")
    
    step2_end_block = w3.eth.block_number
    step2_end_time = datetime.now()
    total_blocks = step2_end_block - step1_start_block
    elapsed_time = (step2_end_time - step1_start_time).total_seconds()
    
    print(f"\n✅ Wait complete!")
    print(f"   End Block: {step2_end_block:,}")
    print(f"   Blocks Passed: {total_blocks:,}")
    print(f"   Actual Time: {elapsed_time:.1f} seconds")
    print(f"   Avg Block Time: {elapsed_time/total_blocks:.3f} seconds")
    
    # ========================================================================
    # STEP 3: Swap WETH → DAI (reverse)
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 3: SWAP WETH → DAI (REVERSE)")
    print("=" * 80)
    
    # Use the WETH amount we borrowed in step 1
    weth_to_swap = weth_borrowed
    print(f"📊 Action: Repay {weth_to_swap:.6f} WETH debt, borrow DAI")
    
    tx_hash2 = swapper.swap_debt(
        from_asset='WETH',
        to_asset='DAI',
        amount=Decimal(str(weth_to_swap)),
        slippage_bps=100,  # 1%
        dry_run=False
    )
    
    if not tx_hash2:
        print("❌ Second swap failed")
        return
    
    print(f"\n✅ Transaction confirmed!")
    print(f"   TX Hash: {tx_hash2}")
    print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash2}")
    print(f"   Block: {w3.eth.block_number:,}")
    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Get receipt
    receipt2 = w3.eth.get_transaction_receipt(tx_hash2)
    print(f"   Gas Used: {receipt2['gasUsed']:,}")
    print(f"   Status: {'Success ✅' if receipt2['status'] == 1 else 'Failed ❌'}")
    
    # Get final position
    final_summary = swapper.get_account_summary()
    weth_repaid = after_swap1['weth_debt'] - final_summary['weth_debt']
    dai_borrowed = final_summary['dai_debt'] - after_swap1['dai_debt']
    
    print(f"\n📈 Swap 2 Results:")
    print(f"   WETH Repaid: {weth_repaid:.6f} WETH")
    print(f"   DAI Borrowed: {dai_borrowed:.6f} DAI")
    print(f"   New DAI Debt: {after_swap1['dai_debt']:.6f} → {final_summary['dai_debt']:.6f}")
    print(f"   New WETH Debt: {after_swap1['weth_debt']:.6f} → {final_summary['weth_debt']:.6f}")
    print(f"   Health Factor: {after_swap1['health_factor']:.4f} → {final_summary['health_factor']:.4f}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("🎉 BIDIRECTIONAL SWAP TEST COMPLETE")
    print("=" * 80)
    
    print(f"\n📊 Overall Changes:")
    print(f"   DAI Debt: {initial_summary['dai_debt']:.6f} → {final_summary['dai_debt']:.6f} ({final_summary['dai_debt'] - initial_summary['dai_debt']:+.6f})")
    print(f"   WETH Debt: {initial_summary['weth_debt']:.6f} → {final_summary['weth_debt']:.6f} ({final_summary['weth_debt'] - initial_summary['weth_debt']:+.6f})")
    print(f"   Health Factor: {initial_summary['health_factor']:.4f} → {final_summary['health_factor']:.4f} ({final_summary['health_factor'] - initial_summary['health_factor']:+.4f})")
    
    print(f"\n💰 Cost Analysis:")
    gas_eth_1 = receipt1['gasUsed'] * receipt1['effectiveGasPrice'] / 1e18
    gas_eth_2 = receipt2['gasUsed'] * receipt2['effectiveGasPrice'] / 1e18
    total_gas_eth = gas_eth_1 + gas_eth_2
    eth_price = 3000  # Approximate ETH price
    print(f"   Swap 1 Gas: {gas_eth_1:.6f} ETH (${gas_eth_1 * eth_price:.2f})")
    print(f"   Swap 2 Gas: {gas_eth_2:.6f} ETH (${gas_eth_2 * eth_price:.2f})")
    print(f"   Total Gas: {total_gas_eth:.6f} ETH (${total_gas_eth * eth_price:.2f})")
    
    print(f"\n📋 Transaction Links:")
    print(f"   Swap 1 (DAI→WETH): https://arbiscan.io/tx/{tx_hash1}")
    print(f"   Swap 2 (WETH→DAI): https://arbiscan.io/tx/{tx_hash2}")
    
    print(f"\n✅ All swaps executed successfully!")
    print(f"   Test Duration: {(datetime.now() - step1_start_time).total_seconds():.0f} seconds")
    print(f"   Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
