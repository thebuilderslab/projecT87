#!/usr/bin/env python3
"""
Streamlined test for automated swap with HF monitoring
"""

import os
from web3 import Web3
from decimal import Decimal
from smart_delegation_manager import SmartDelegationManager
from debt_swap_bidirectional import BidirectionalDebtSwapper

def main():
    # Setup Web3
    RPC_URL = os.getenv('ALCHEMY_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    private_key = os.getenv('PRIVATE_KEY') or os.getenv('WALLET_PRIVATE_KEY')
    if not private_key:
        raise ValueError("PRIVATE_KEY or WALLET_PRIVATE_KEY not found")
    
    if not private_key.startswith('0x'):
        private_key = '0x' + private_key
    
    account = w3.eth.account.from_key(private_key)
    wallet_address = account.address
    
    print("="*80)
    print("AUTOMATED SWAP TEST - 5 DAI → WETH")
    print("="*80)
    print(f"Wallet: {wallet_address}")
    print(f"RPC: {RPC_URL[:50]}...")
    
    # Initialize managers
    delegation_mgr = SmartDelegationManager(w3, private_key)
    swapper = BidirectionalDebtSwapper(w3, private_key)
    
    # STEP 1: Health check
    print(f"\n{'='*80}")
    print("STEP 1: PRE-SWAP HEALTH CHECK")
    print(f"{'='*80}")
    
    is_safe, hf, status = delegation_mgr.check_health_factor_safe()
    print(f"Health Factor: {hf:.4f}")
    print(f"Status: {status}")
    
    if not is_safe:
        print(f"\n🚫 ABORT: Health factor {hf:.4f} below 1.05 minimum")
        return
    
    if hf < Decimal('1.10'):
        print(f"⚠️ WARNING: HF in danger zone (1.05-1.10)")
    else:
        print(f"✅ HF is safe (above 1.10)")
    
    # STEP 2: Check delegation
    print(f"\n{'='*80}")
    print("STEP 2: CREDIT DELEGATION")
    print(f"{'='*80}")
    
    current_delegation = delegation_mgr.get_current_delegation()
    print(f"Current WETH delegation: {current_delegation:.6f} WETH")
    
    # Estimate WETH needed for 5 DAI (roughly 5 / 3100 = 0.00161 WETH)
    dai_amount = Decimal('5')
    estimated_weth = dai_amount / Decimal('3100')
    
    print(f"Estimated WETH needed: ~{estimated_weth:.6f} WETH")
    
    if current_delegation < estimated_weth * Decimal('1.2'):
        print(f"\nApproving exact delegation amount...")
        tx_hash = delegation_mgr.approve_exact_delegation(estimated_weth)
        
        if tx_hash is None:
            print(f"\n🚫 ABORT: Delegation approval failed")
            return
        
        print(f"✅ Delegation approved: {tx_hash}")
    else:
        print(f"✅ Sufficient delegation exists")
    
    # STEP 3: Execute swap
    print(f"\n{'='*80}")
    print("STEP 3: EXECUTING SWAP (5 DAI → WETH)")
    print(f"{'='*80}")
    
    swap_tx = swapper.swap_debt(
        from_asset='DAI',
        to_asset='WETH',
        amount=dai_amount,
        slippage_bps=100
    )
    
    if not swap_tx:
        print(f"\n❌ SWAP FAILED")
        return
    
    print(f"\n✅ SWAP EXECUTED: {swap_tx}")
    
    # STEP 4: Post-swap health check
    print(f"\n{'='*80}")
    print("STEP 4: POST-SWAP HEALTH CHECK")
    print(f"{'='*80}")
    
    import time
    time.sleep(5)
    
    is_safe_after, final_hf, final_status = delegation_mgr.check_health_factor_safe()
    print(f"Health Factor: {final_hf:.4f}")
    print(f"Status: {final_status}")
    print(f"Change: {hf:.4f} → {final_hf:.4f} ({(final_hf - hf):+.4f})")
    
    if not is_safe_after:
        print(f"\n🚨 CRITICAL: HF dropped below 1.05!")
    elif final_hf < Decimal('1.10'):
        print(f"\n⚠️ WARNING: HF in danger zone")
    else:
        print(f"\n✅ HF still safe")
    
    print(f"\n{'='*80}")
    print("✅ TEST COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
