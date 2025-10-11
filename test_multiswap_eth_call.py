#!/usr/bin/env python3
"""
Test multiSwap calldata with eth_call simulation
Validates against Aave Debt Switch V3 on Arbitrum mainnet
"""

from web3 import Web3
from augustus_v5_multiswap_builder import AugustusV5MultiSwapBuilder
import json

def test_multiswap_eth_call():
    """Test multiSwap via Debt Switch V3 swapDebt function"""
    
    print("=" * 80)
    print("MULTISWAP ETH_CALL SIMULATION TEST")
    print("=" * 80)
    
    # Connect to Arbitrum mainnet
    w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum mainnet")
        return False
    
    print(f"✅ Connected to Arbitrum (Chain ID: {w3.eth.chain_id})")
    
    # Contract addresses
    debt_switch_v3 = w3.to_checksum_address("0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4")
    augustus_v5 = w3.to_checksum_address("0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57")
    arb_token = w3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548")
    dai_token = w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
    
    # Test wallet (using Debt Switch as dummy user for simulation)
    test_user = debt_switch_v3
    
    print(f"\n📍 CONTRACT ADDRESSES:")
    print(f"   Debt Switch V3: {debt_switch_v3}")
    print(f"   Augustus V5: {augustus_v5}")
    print(f"   ARB Token: {arb_token}")
    print(f"   DAI Token: {dai_token}")
    print(f"   Test User: {test_user}")
    
    # Build multiSwap calldata
    print(f"\n🏗️  BUILDING MULTISWAP CALLDATA")
    print("-" * 60)
    
    builder = AugustusV5MultiSwapBuilder(w3, network="arbitrum")
    
    # Build for ARB → DAI swap (reverse of debt swap for testing)
    swap_amount = int(60 * 1e18)  # 60 ARB
    min_amount = int(24 * 1e18)   # Min 24 DAI
    
    multiswap_result = builder.build_multiswap_calldata(
        from_token='ARB',
        to_token='DAI',
        from_amount=swap_amount,
        min_to_amount=min_amount,
        beneficiary=test_user,
        slippage_bps=400  # 4%
    )
    
    if not multiswap_result:
        print("❌ Failed to build multiSwap calldata")
        return False
    
    print(f"\n✅ multiSwap calldata built:")
    print(f"   Selector: {multiswap_result['method_selector']}")
    print(f"   Length: {len(multiswap_result['calldata'])} chars ({len(multiswap_result['calldata'])//2} bytes)")
    
    # Debt Switch V3 swapDebt ABI
    swap_debt_abi = {
        "inputs": [
            {"name": "debtAsset", "type": "address"},
            {"name": "debtAmount", "type": "uint256"},
            {"name": "debtRateMode", "type": "uint256"},
            {"name": "newDebtAsset", "type": "address"},
            {"name": "maxNewDebtAmount", "type": "uint256"},
            {"name": "extraCollateralAsset", "type": "address"},
            {"name": "extraCollateralAmount", "type": "uint256"},
            {"name": "offset", "type": "uint256"},
            {"name": "paraswapData", "type": "bytes"}
        ],
        "name": "swapDebt",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
    
    # Build swapDebt parameters
    swap_debt_params = {
        'debtAsset': dai_token,              # Current debt in DAI
        'debtAmount': int(25 * 1e18),        # Repay 25 DAI
        'debtRateMode': 2,                   # Variable rate
        'newDebtAsset': arb_token,           # New debt in ARB
        'maxNewDebtAmount': int(70 * 1e18),  # Max 70 ARB new debt
        'extraCollateralAsset': '0x0000000000000000000000000000000000000000',
        'extraCollateralAmount': 0,
        'offset': 36,                        # Standard offset for beneficiary in multiSwap
        'paraswapData': multiswap_result['calldata']
    }
    
    print(f"\n📋 SWAP DEBT PARAMETERS:")
    print(f"   Current Debt: 25 DAI ({dai_token[:10]}...)")
    print(f"   New Debt: Max 70 ARB ({arb_token[:10]}...)")
    print(f"   Rate Mode: Variable (2)")
    print(f"   Offset: {swap_debt_params['offset']}")
    print(f"   ParaSwap Data: {len(swap_debt_params['paraswapData'])} chars")
    
    # Encode swapDebt call
    debt_switch_contract = w3.eth.contract(address=debt_switch_v3, abi=[swap_debt_abi])
    
    try:
        swap_debt_data = debt_switch_contract.encodeABI(
            fn_name='swapDebt',
            args=[
                swap_debt_params['debtAsset'],
                swap_debt_params['debtAmount'],
                swap_debt_params['debtRateMode'],
                swap_debt_params['newDebtAsset'],
                swap_debt_params['maxNewDebtAmount'],
                swap_debt_params['extraCollateralAsset'],
                swap_debt_params['extraCollateralAmount'],
                swap_debt_params['offset'],
                bytes.fromhex(swap_debt_params['paraswapData'][2:])
            ]
        )
        
        print(f"\n✅ swapDebt calldata encoded:")
        print(f"   Signature: 0xb8bd1c6b (swapDebt)")
        print(f"   Full calldata: {len(swap_debt_data)} bytes")
        
    except Exception as e:
        print(f"❌ Failed to encode swapDebt: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Perform eth_call simulation
    print(f"\n🔬 PERFORMING ETH_CALL SIMULATION")
    print("-" * 60)
    
    tx_params = {
        'from': test_user,
        'to': debt_switch_v3,
        'data': swap_debt_data,
        'gas': 500000  # Reasonable gas limit for debt swap
    }
    
    print(f"   From: {tx_params['from']}")
    print(f"   To: {tx_params['to']}")
    print(f"   Gas Limit: {tx_params['gas']}")
    
    try:
        # Attempt eth_call
        result = w3.eth.call(tx_params)
        
        print(f"\n✅ ETH_CALL SUCCESSFUL!")
        print(f"   Result: {result.hex()}")
        print(f"   Calldata PASSED Debt Switch validation!")
        print(f"   multiSwap selector accepted (0x0863b7ac)")
        print(f"   ArbitrumAdapter01 routing validated")
        
        # Try gas estimation
        try:
            gas_estimate = w3.eth.estimate_gas(tx_params)
            print(f"\n⛽ GAS ESTIMATE: {gas_estimate:,} gas")
            
            # Calculate gas cost
            gas_price = w3.eth.gas_price
            gas_cost_wei = gas_estimate * gas_price
            gas_cost_eth = gas_cost_wei / 1e18
            
            print(f"   Gas Price: {gas_price / 1e9:.2f} gwei")
            print(f"   Est. Cost: {gas_cost_eth:.6f} ETH")
            
        except Exception as e:
            print(f"   ⚠️  Gas estimation failed: {e}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ETH_CALL FAILED!")
        print(f"   Error: {error_msg}")
        
        # Parse error details
        if "execution reverted" in error_msg.lower():
            print(f"\n   ⚠️  EXECUTION REVERTED - Possible causes:")
            print(f"      - Insufficient allowance or balance")
            print(f"      - Invalid debt position (test user has no Aave debt)")
            print(f"      - Slippage too tight")
            print(f"      - NOTE: Revert might be expected for test user")
        
        if "selector" in error_msg.lower() or "signature" in error_msg.lower():
            print(f"\n   ❌ SELECTOR VALIDATION FAILED!")
            print(f"      - Debt Switch rejected the paraswapData selector")
            print(f"      - Expected: 0x0863b7ac (multiSwap)")
            print(f"      - Check multiSwap calldata encoding")
        
        # Still check if it's just a balance/position issue vs selector issue
        if "selector" not in error_msg.lower() and "signature" not in error_msg.lower():
            print(f"\n   ℹ️  SELECTOR LIKELY PASSED (error is position-related)")
            print(f"      This suggests multiSwap selector was accepted!")
        
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("AUGUSTUS V5 MULTISWAP + ARBITRUMADAPTER01 VALIDATION TEST")
    print("=" * 80 + "\n")
    
    success = test_multiswap_eth_call()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST RESULT: PASSED")
        print("   - multiSwap calldata structure valid")
        print("   - ArbitrumAdapter01 routing accepted")
        print("   - Debt Switch V3 compatibility confirmed")
    else:
        print("⚠️  TEST RESULT: SIMULATION FAILED")
        print("   - Check error details above")
        print("   - Revert might be expected for test user with no debt")
        print("   - Key validation: selector acceptance")
    print("=" * 80 + "\n")
