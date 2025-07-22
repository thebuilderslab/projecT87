"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""


#!/usr/bin/env python3
"""
Test readiness for DAI → WBTC swap
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from config_constants import MIN_ETH_FOR_OPERATIONS

def test_swap_readiness():
    """Test all components needed for successful swap"""
    print("🔄 TESTING SWAP READINESS")
    print("=" * 50)
    
    issues_found = []
    
    try:
        # Test 1: Agent initialization
        print("1️⃣ Testing agent initialization...")
        agent = ArbitrumTestnetAgent()
        print(f"   ✅ Agent initialized: {agent.address}")
        print(f"   ✅ Network: {agent.w3.eth.chain_id}")
        
        # Test 2: Integration initialization
        print("\n2️⃣ Testing integrations...")
        if agent.initialize_integrations():
            print("   ✅ Integrations initialized")
            
            # Test Aave
            if agent.aave and not hasattr(agent.aave, '__class__') or 'Mock' not in agent.aave.__class__.__name__:
                print("   ✅ Real Aave integration loaded")
            else:
                print("   ⚠️ Mock Aave integration (limited functionality)")
                issues_found.append("Mock Aave integration")
            
            # Test Uniswap
            if agent.uniswap and not hasattr(agent.uniswap, '__class__') or 'Mock' not in agent.uniswap.__class__.__name__:
                print("   ✅ Real Uniswap integration loaded")
            else:
                print("   ⚠️ Mock Uniswap integration (limited functionality)")
                issues_found.append("Mock Uniswap integration")
        else:
            print("   ❌ Integration initialization failed")
            issues_found.append("Integration initialization failed")
        
        # Test 3: ETH balance
        print("\n3️⃣ Testing ETH balance...")
        eth_balance = agent.get_eth_balance()
        print(f"   ETH Balance: {eth_balance:.6f} ETH")
        if eth_balance < MIN_ETH_FOR_OPERATIONS:
            print("   ❌ Insufficient ETH for gas fees")
            issues_found.append("Insufficient ETH balance")
        else:
            print("   ✅ Sufficient ETH for gas fees")
        
        # Test 4: DAI balance
        print("\n4️⃣ Testing DAI balance...")
        try:
            DAI_balance = agent.aave.get_token_balance(agent.dai_address)
            print(f"   DAI Balance: {DAI_balance:.6f} DAI")
            required = 40.6293
            if DAI_balance < required:
                print(f"   ❌ Insufficient DAI (need {required:.4f})")
                issues_found.append(f"Insufficient DAI (need {required:.4f}, have {DAI_balance:.4f})")
            else:
                print("   ✅ Sufficient DAI for swap")
        except Exception as e:
            print(f"   ❌ Failed to check DAI balance: {e}")
            issues_found.append("DAI balance check failed")
        
        # Test 5: Contract connectivity
        print("\n5️⃣ Testing contract connectivity...")
        try:
            # Test DAI contract
            from web3 import Web3
            DAI_contract = agent.w3.eth.contract(
                address=agent.dai_address,
                abi=[{
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                }]
            )
            symbol = DAI_contract.functions.symbol().call()
            print(f"   ✅ DAI contract responsive: {symbol}")
        except Exception as e:
            print(f"   ❌ DAI contract issue: {e}")
            issues_found.append("DAI contract connectivity")
        
        # Test 6: Network status
        print("\n6️⃣ Testing network status...")
        network_ok, status = agent.check_network_status()
        if network_ok:
            print(f"   ✅ Network status: {status}")
        else:
            print(f"   ❌ Network issue: {status}")
            issues_found.append(f"Network issue: {status}")
        
    except Exception as e:
        print(f"❌ Critical test failure: {e}")
        issues_found.append(f"Critical test failure: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    if not issues_found:
        print("🎉 ALL TESTS PASSED - READY FOR SWAP!")
        print("✅ You can now run: python swap_DAI_for_wbtc.py")
    else:
        print("❌ ISSUES FOUND - NEEDS FIXING:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
        
        print("\n💡 RECOMMENDED ACTIONS:")
        if any("ETH" in issue for issue in issues_found):
            print(f"   • Send ETH to: {agent.address if 'agent' in locals() else 'your wallet'}")
        if any("DAI" in issue for issue in issues_found):
            print(f"   • Send DAI to: {agent.address if 'agent' in locals() else 'your wallet'}")
        if any("Mock" in issue for issue in issues_found):
            print("   • Check integration imports and contract addresses")
        if any("contract" in issue for issue in issues_found):
            print("   • Verify token contract addresses are correct")

if __name__ == "__main__":
    test_swap_readiness()
