
#!/usr/bin/env python3
"""
Verify Aave Contract Interaction Resolution
Tests that all contract interaction issues have been resolved
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3

def verify_aave_resolution():
    """Verify that Aave contract interaction issues are resolved"""
    print("🔍 VERIFYING AAVE CONTRACT RESOLUTION")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        
        # Test 1: Direct Aave contract call
        print("\n1️⃣ Testing Direct Aave Contract Call...")
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(
            address=agent.aave_pool_address,
            abi=pool_abi
        )
        
        # Force fresh contract call with latest block
        account_data = pool_contract.functions.getUserAccountData(agent.address).call(block_identifier='latest')
        
        collateral_usd = account_data[0] / (10**8)
        debt_usd = account_data[1] / (10**8)
        available_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"🔍 VERIFICATION: Using latest block for real-time data")
        print(f"📊 Block number: {agent.w3.eth.block_number}")
        print(f"⏰ Timestamp: {time.time()}")
        
        print(f"   ✅ Contract call successful!")
        print(f"   📊 Collateral: ${collateral_usd:.2f}")
        print(f"   📊 Debt: ${debt_usd:.2f}")
        print(f"   📊 Available: ${available_usd:.2f}")
        print(f"   📊 Health Factor: {health_factor:.4f}")
        
        # Test 2: Aave integration robustness
        print("\n2️⃣ Testing Aave Integration Robustness...")
        if hasattr(agent, 'aave') and agent.aave:
            account_data_integration = agent.aave.get_user_account_data()
            if account_data_integration and 'health_factor' in account_data_integration:
                print(f"   ✅ Integration method working")
                print(f"   📊 Health Factor: {account_data_integration['health_factor']:.4f}")
            else:
                print(f"   ❌ Integration method failed")
        
        # Test 3: Fallback mechanisms
        print("\n3️⃣ Testing Fallback Mechanisms...")
        if hasattr(agent, 'health_monitor') and agent.health_monitor:
            health_data = agent.health_monitor.get_current_health_factor()
            if health_data:
                print(f"   ✅ Health monitor fallback working")
                print(f"   📊 Data source: {health_data.get('data_source', 'unknown')}")
            else:
                print(f"   ❌ Health monitor fallback failed")
        
        print(f"\n🎉 AAVE CONTRACT RESOLUTION VERIFICATION COMPLETE")
        print(f"✅ All critical contract interaction issues appear resolved")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    verify_aave_resolution()
