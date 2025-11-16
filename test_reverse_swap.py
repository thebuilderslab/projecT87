#!/usr/bin/env python3
"""
Test reverse debt swap: WETH → DAI
This should INCREASE health factor since we're repaying expensive WETH debt
and borrowing cheap DAI debt.
"""

from web3 import Web3
from decimal import Decimal
from debt_swap_bidirectional import BidirectionalDebtSwapper
import os

def main():
    # Connect to Arbitrum mainnet
    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    print("=" * 80)
    print("REVERSE DEBT SWAP TEST (WETH → DAI)")
    print("=" * 80)
    print(f"✅ Connected to Arbitrum mainnet")
    print(f"   Block: {w3.eth.block_number:,}")
    
    # Initialize swapper
    swapper = BidirectionalDebtSwapper(w3, os.environ['PRIVATE_KEY'])
    
    # Check initial position
    print("\n" + "=" * 80)
    print("INITIAL POSITION")
    print("=" * 80)
    summary = swapper.get_account_summary()
    print(f"DAI Debt: {summary['dai_debt']:.6f} DAI")
    print(f"WETH Debt: {summary['weth_debt']:.6f} WETH")
    print(f"Health Factor: {summary['health_factor']:.4f}")
    print(f"Total Debt: ${summary['total_debt_usd']:.2f}")
    
    # Try reverse swap - should INCREASE health factor!
    print("\n" + "=" * 80)
    print("SWAP TEST: 0.005 WETH → DAI (REVERSE DIRECTION)")
    print("=" * 80)
    print("📊 Action: Repay 0.005 WETH debt, borrow DAI")
    print("💡 This should INCREASE health factor (repaying expensive debt)\n")
    
    try:
        tx_hash = swapper.swap_debt('WETH', 'DAI', Decimal('0.005'), slippage_bps=100)
        
        if tx_hash and tx_hash != "DRY_RUN":
            print(f"\n✅ SUCCESS!")
            print(f"   TX: {tx_hash}")
            print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash}")
            
            # Check new position
            print("\n" + "=" * 80)
            print("NEW POSITION")
            print("=" * 80)
            summary = swapper.get_account_summary()
            print(f"DAI Debt: {summary['dai_debt']:.6f} DAI")
            print(f"WETH Debt: {summary['weth_debt']:.6f} WETH")
            print(f"Health Factor: {summary['health_factor']:.4f}")
            print(f"Total Debt: ${summary['total_debt_usd']:.2f}")
        else:
            print(f"\n❌ Swap failed")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
