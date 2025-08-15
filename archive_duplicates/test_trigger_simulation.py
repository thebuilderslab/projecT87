
#!/usr/bin/env python3
"""
Test script to simulate the autonomous trigger
"""

import os
import sys
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_trigger_simulation():
    """Test the trigger logic with simulated collateral growth"""
    
    # Set mainnet mode
    os.environ['NETWORK_MODE'] = 'mainnet'
    
    print("🧪 TRIGGER SIMULATION TEST")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        print(f"📍 Wallet: {agent.address}")
        
        # Initialize integrations
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return
        
        # Get current collateral value
        try:
            # Direct Aave query
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

            account_data = pool_contract.functions.getUserAccountData(agent.address).call()
            current_collateral_usd = account_data[0] / (10**8)  # Aave V3 uses 8 decimals
            
            print(f"💰 Current Collateral: ${current_collateral_usd:.2f}")
            print(f"📊 Agent Baseline: ${agent.last_collateral_value_usd:.2f}")
            print(f"🎯 Growth Needed: ${agent.last_collateral_value_usd + 12:.2f}")
            
            growth = current_collateral_usd - agent.last_collateral_value_usd
            print(f"📈 Current Growth: ${growth:.2f}")
            
            if current_collateral_usd >= (agent.last_collateral_value_usd + 12):
                print("🚀 TRIGGER WOULD ACTIVATE!")
                print("   Collateral growth meets $12+ threshold")
            else:
                needed = (agent.last_collateral_value_usd + 12) - current_collateral_usd
                print(f"⏸️ Trigger not active")
                print(f"💡 Need ${needed:.2f} more collateral to trigger")
                print(f"💡 Add USDC/WETH to your Aave position to test")
            
        except Exception as e:
            print(f"❌ Error getting collateral data: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_trigger_simulation()
