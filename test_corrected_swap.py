#!/usr/bin/env python3
"""
Test the corrected debt swap implementation
Performs dry run first, then small live test
"""

import os
from web3 import Web3
from decimal import Decimal
from debt_swap_bidirectional import BidirectionalDebtSwapper

def main():
    print("=" * 80)
    print("CORRECTED DEBT SWAP TEST")
    print("=" * 80)
    
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
    
    # Get current position
    print("\n" + "=" * 80)
    print("CURRENT POSITION")
    print("=" * 80)
    summary = swapper.get_account_summary()
    print(f"DAI Debt: {summary['dai_debt']:.6f} DAI")
    print(f"WETH Debt: {summary['weth_debt']:.6f} WETH")
    print(f"Health Factor: {summary['health_factor']:.4f}")
    print(f"Total Debt: ${summary['total_debt_usd']:.2f}")
    
    # Determine swap direction based on current debt
    if summary['dai_debt'] > 0:
        print("\n📊 You have DAI debt. Testing DAI → WETH swap...")
        from_asset = 'DAI'
        to_asset = 'WETH'
        amount = min(Decimal('5'), summary['dai_debt'])  # Max $5 or available debt
    elif summary['weth_debt'] > 0:
        print("\n📊 You have WETH debt. Testing WETH → DAI swap...")
        from_asset = 'WETH'
        to_asset = 'DAI'
        amount = min(Decimal('0.002'), summary['weth_debt'])  # Max ~$6 or available debt
    else:
        print("\n⚠️  No debt found. Cannot test debt swap.")
        return
    
    print(f"\n💱 Test Parameters:")
    print(f"   Direction: {from_asset} → {to_asset}")
    print(f"   Amount: {amount} {from_asset}")
    print(f"   Slippage: 1%")
    
    # First: Dry run
    print("\n" + "=" * 80)
    print("DRY RUN TEST")
    print("=" * 80)
    result = swapper.swap_debt(
        from_asset=from_asset,
        to_asset=to_asset,
        amount=amount,
        slippage_bps=100,
        dry_run=True
    )
    
    if result != "DRY_RUN":
        print("❌ Dry run failed")
        return
    
    print("\n✅ Dry run successful!")
    
    # Ask user if they want to proceed with live test
    print("\n" + "=" * 80)
    print("READY FOR LIVE TEST")
    print("=" * 80)
    print(f"This will execute a REAL debt swap on Arbitrum mainnet:")
    print(f"  • Repay {amount} {from_asset}")
    print(f"  • Borrow {to_asset} (amount determined by market)")
    print(f"  • Gas cost: ~0.04 ETH (~$120 at current prices)")
    print()
    
    response = input("Proceed with live transaction? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n🛑 Live test cancelled by user")
        return
    
    # Execute live swap
    print("\n" + "=" * 80)
    print("EXECUTING LIVE SWAP")
    print("=" * 80)
    
    tx_hash = swapper.swap_debt(
        from_asset=from_asset,
        to_asset=to_asset,
        amount=amount,
        slippage_bps=100,
        dry_run=False
    )
    
    if tx_hash:
        print("\n" + "=" * 80)
        print("🎉 SUCCESS!")
        print("=" * 80)
        print(f"Transaction: {tx_hash}")
        print(f"Arbiscan: https://arbiscan.io/tx/{tx_hash}")
        
        # Show final position
        final_summary = swapper.get_account_summary()
        print(f"\n📊 Final Position:")
        print(f"   DAI Debt: {summary['dai_debt']:.6f} → {final_summary['dai_debt']:.6f}")
        print(f"   WETH Debt: {summary['weth_debt']:.6f} → {final_summary['weth_debt']:.6f}")
        print(f"   Health Factor: {summary['health_factor']:.4f} → {final_summary['health_factor']:.4f}")
    else:
        print("\n❌ Transaction failed. Check logs above for details.")

if __name__ == "__main__":
    main()
