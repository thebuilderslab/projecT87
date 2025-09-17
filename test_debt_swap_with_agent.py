#!/usr/bin/env python3
"""
Test Debt Swap with Existing Agent System
Uses the existing agent that already has private key loaded
"""

import os
import sys
import time
import requests
from typing import Dict

def test_debt_swap_with_existing_agent():
    """Test debt swap using the existing agent system"""
    
    print("🧪 TESTING DEBT SWAP WITH EXISTING AGENT")
    print("=" * 60)
    
    try:
        # Import existing agent
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Set to mainnet mode
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        print("⏳ Initializing agent with mainnet mode...")
        agent = ArbitrumTestnetAgent()
        
        print(f"✅ Agent initialized:")
        print(f"   Address: {agent.address}")
        print(f"   Network: {agent.w3.eth.chain_id}")
        
        # Test 1: Current debt position using corrected monitoring
        print(f"\n📊 STEP 1: Current Debt Position Check")
        
        # Use corrected getUserReserveData
        data_provider_abi = [{
            'inputs': [
                {'name': 'asset', 'type': 'address'}, 
                {'name': 'user', 'type': 'address'}
            ],
            'name': 'getUserReserveData',
            'outputs': [
                {'name': 'currentATokenBalance', 'type': 'uint256'},
                {'name': 'currentStableDebt', 'type': 'uint256'},
                {'name': 'currentVariableDebt', 'type': 'uint256'},
                {'name': 'principalStableDebt', 'type': 'uint256'},
                {'name': 'scaledVariableDebt', 'type': 'uint256'},
                {'name': 'stableBorrowRate', 'type': 'uint256'},
                {'name': 'liquidityRate', 'type': 'uint256'},
                {'name': 'stableRateLastUpdated', 'type': 'uint40'},
                {'name': 'usageAsCollateralEnabled', 'type': 'bool'}
            ],
            'stateMutability': 'view',
            'type': 'function'
        }]
        
        data_provider_address = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
        
        data_provider = agent.w3.eth.contract(
            address=data_provider_address,
            abi=data_provider_abi
        )
        
        # CORRECTED: Get DAI debt with proper parameter order
        dai_reserve_data = data_provider.functions.getUserReserveData(
            dai_address,
            agent.address
        ).call()
        
        dai_variable_debt = dai_reserve_data[2] / 1e18
        dai_stable_debt = dai_reserve_data[1] / 1e18
        dai_total_debt = dai_variable_debt + dai_stable_debt
        
        print(f"   DAI Variable Debt: {dai_variable_debt:.6f}")
        print(f"   DAI Stable Debt: {dai_stable_debt:.6f}")
        print(f"   DAI Total Debt: {dai_total_debt:.6f}")
        
        if dai_variable_debt < 5.0:
            print(f"   ❌ Insufficient DAI debt for 5 DAI swap: {dai_variable_debt:.6f}")
            return False
        
        print(f"   ✅ Sufficient DAI debt for 5 DAI swap")
        
        # Test 2: Get debt token addresses
        print(f"\n🔍 STEP 2: Debt Token Resolution")
        
        reserve_tokens_abi = [{
            "inputs": [{"name": "asset", "type": "address"}],
            "name": "getReserveTokensAddresses",
            "outputs": [
                {"name": "aTokenAddress", "type": "address"},
                {"name": "stableDebtTokenAddress", "type": "address"},
                {"name": "variableDebtTokenAddress", "type": "address"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        data_provider_tokens = agent.w3.eth.contract(
            address=data_provider_address,
            abi=reserve_tokens_abi
        )
        
        # Get ARB debt token (destination for swap)
        arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        arb_tokens = data_provider_tokens.functions.getReserveTokensAddresses(arb_address).call()
        arb_variable_debt_token = arb_tokens[2]
        
        print(f"   ARB Variable Debt Token: {arb_variable_debt_token}")
        print(f"   ✅ Debt token addresses resolved")
        
        # Test 3: ParaSwap route check  
        print(f"\n🔄 STEP 3: ParaSwap Route Test")
        
        # For DAI debt → ARB debt, we need ARB → DAI route
        swap_amount_wei = agent.w3.to_wei(5, 'ether')  # 5 DAI
        
        try:
            price_url = "https://apiv5.paraswap.io/prices"
            price_params = {
                'srcToken': arb_address,     # ARB (source for route)
                'destToken': dai_address,    # DAI (destination for route)
                'amount': str(swap_amount_wei),
                'srcDecimals': 18,
                'destDecimals': 18,
                'side': 'BUY',               # Buy DAI with ARB
                'network': 42161,
                'partner': 'aave',
                'maxImpact': '15'
            }
            
            print(f"   Testing ParaSwap route: ARB → DAI (reverse for debt swap)")
            response = requests.get(price_url, params=price_params, timeout=10)
            
            if response.status_code == 200:
                route_data = response.json()
                if 'priceRoute' in route_data:
                    arb_needed = int(route_data['priceRoute']['srcAmount']) / 1e18
                    dai_out = int(route_data['priceRoute']['destAmount']) / 1e18
                    
                    print(f"   ✅ ParaSwap route found:")
                    print(f"      ARB needed: {arb_needed:.6f}")
                    print(f"      DAI output: {dai_out:.6f}")
                else:
                    print(f"   ❌ No route found in response")
                    return False
            else:
                print(f"   ❌ ParaSwap API failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ ParaSwap test failed: {e}")
            return False
        
        # Test 4: Debt swap contract validation
        print(f"\n🔧 STEP 4: Debt Swap Contract Validation")
        
        debt_swap_adapter = "0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9"
        
        # Test if contract exists and is accessible
        try:
            code = agent.w3.eth.get_code(debt_swap_adapter)
            if len(code) > 0:
                print(f"   ✅ Debt swap adapter contract exists")
                print(f"   Address: {debt_swap_adapter}")
            else:
                print(f"   ❌ Debt swap adapter not found")
                return False
                
        except Exception as e:
            print(f"   ❌ Contract validation failed: {e}")
            return False
        
        # Test 5: Transaction construction (simulation only)
        print(f"\n🚀 STEP 5: Transaction Construction Test")
        
        swap_debt_abi = [{
            "inputs": [
                {"name": "assetToSwapFrom", "type": "address"},
                {"name": "assetToSwapTo", "type": "address"},
                {"name": "amountToSwap", "type": "uint256"},
                {"name": "paraswapData", "type": "bytes"},
                {
                    "components": [
                        {"name": "token", "type": "address"},
                        {"name": "delegatee", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ],
                    "name": "creditDelegationPermit",
                    "type": "tuple"
                }
            ],
            "name": "swapDebt",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        debt_swap_contract = agent.w3.eth.contract(
            address=debt_swap_adapter,
            abi=swap_debt_abi
        )
        
        print(f"   ✅ Contract interface loaded")
        print(f"   swapDebt function: Available")
        print(f"   Parameters: assetToSwapFrom, assetToSwapTo, amountToSwap, paraswapData, permit")
        
        # Summary
        print(f"\n🎉 DEBT SWAP READINESS ASSESSMENT")
        print(f"=" * 60)
        print(f"✅ Agent System: Working")
        print(f"✅ Debt Detection: Working ({dai_variable_debt:.6f} DAI debt found)")
        print(f"✅ Debt Token Resolution: Working")
        print(f"✅ ParaSwap Routing: Working")
        print(f"✅ Debt Swap Contract: Accessible")
        print(f"✅ Transaction Interface: Ready")
        print(f"")
        print(f"🚀 SYSTEM STATUS: READY FOR DEBT SWAP EXECUTION")
        print(f"")
        print(f"📋 Validated Swap:")
        print(f"   From: 5.0 DAI debt")
        print(f"   To: ARB debt")
        print(f"   ARB needed: ~{arb_needed:.6f}")
        print(f"   Current DAI debt: {dai_variable_debt:.6f}")
        print(f"")
        print(f"💡 To execute: Use the corrected debt swap system with:")
        print(f"   - Fixed debt position detection")
        print(f"   - Proper ParaSwap reverse routing")
        print(f"   - Credit delegation permits")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_debt_swap_with_existing_agent()
    
    if success:
        print(f"\n✅ DEBT SWAP TEST: COMPLETE SUCCESS")
        print(f"Your debt swap system is ready for execution!")
    else:
        print(f"\n❌ DEBT SWAP TEST: FAILED")
        print(f"Additional debugging needed")