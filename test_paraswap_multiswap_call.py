#!/usr/bin/env python3
"""
Test ParaSwap multiSwap calldata with eth_call simulation
"""

import os
from web3 import Web3
from augustus_v5_multiswap_builder import AugustusV5MultiSwapBuilder

# Configuration
ARBITRUM_RPC = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
ARB_ADDRESS = "0x912CE59144191C1204E64559FE8253a0e49E6548"
DAI_ADDRESS = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
AUGUSTUS_V5 = "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57"
DEBT_SWITCH_V3 = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"

def main():
    print("=" * 80)
    print("🧪 TESTING PARASWAP MULTISWAP CALLDATA")
    print("=" * 80)
    
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return
    
    print(f"✅ Connected to Arbitrum (Chain ID: {w3.eth.chain_id})")
    
    # Build multiSwap calldata (BUY mode for exact 20 DAI output)
    builder = AugustusV5MultiSwapBuilder(w3)
    dai_amount = 20 * 10**18
    
    import time
    multiswap_data = builder.build_multiswap_calldata(
        from_token="ARB",
        to_token="DAI",
        from_amount=dai_amount,  # In BUY mode: exact DAI we want
        min_to_amount=dai_amount,  # Must receive exact amount
        beneficiary=DEBT_SWITCH_V3,  # Debt Switch receives the DAI
        deadline=int(time.time()) + 1800,
        slippage_bps=0,
        use_buy_mode=True
    )
    
    if not multiswap_data:
        print("❌ Failed to build multiSwap calldata")
        return
    
    calldata = multiswap_data['calldata']
    print(f"\n✅ MultiSwap calldata built: {len(calldata)} bytes")
    
    # Simulate the call from Debt Switch's perspective
    # (as if Debt Switch has ARB and is calling Augustus V5)
    print(f"\n🧪 SIMULATING MULTISWAP CALL...")
    print(f"   Simulating from: {DEBT_SWITCH_V3} (Debt Switch)")
    print(f"   Calling: {AUGUSTUS_V5} (Augustus V5)")
    
    try:
        # Simulate call (eth_call doesn't actually execute, just simulates)
        result = w3.eth.call({
            'from': w3.to_checksum_address(DEBT_SWITCH_V3),
            'to': w3.to_checksum_address(AUGUSTUS_V5),
            'data': calldata
        })
        
        print(f"✅ SIMULATION SUCCESSFUL!")
        print(f"   Result: {result.hex()}")
        print(f"   The multiSwap calldata appears valid")
        
    except Exception as e:
        print(f"❌ SIMULATION FAILED!")
        print(f"   Error: {e}")
        print(f"   The multiSwap calldata may be invalid or the swap cannot execute")
        
        # Try to extract error message
        error_str = str(e)
        if "execution reverted" in error_str.lower():
            print(f"\n⚠️  Execution reverted - this could be:")
            print(f"   - Insufficient ARB balance (Debt Switch doesn't have ARB yet)")
            print(f"   - Missing ARB approval to Augustus V5")
            print(f"   - Invalid swap route or slippage")

if __name__ == "__main__":
    main()
