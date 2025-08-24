
#!/usr/bin/env python3
"""
Manual Trigger Override - Forces the autonomous sequence to execute
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def activate_manual_trigger():
    """Activate manual trigger override to test the system"""
    
    # Create manual override flag
    with open('trigger_test.flag', 'w') as f:
        f.write('manual_trigger_activated')
    
    print("🔧 Manual trigger override activated!")
    print("⚡ This will force the autonomous sequence to execute on next cycle")
    print("🎯 The system will execute: Borrow → Swap → Supply sequence")
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        
        # Initialize integrations
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        # Get current position
        from web3 import Web3
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
        
        pool_contract = agent.w3.eth.contract(address=agent.aave_pool_address, abi=pool_abi)
        account_data = pool_contract.functions.getUserAccountData(agent.address).call()
        
        available_borrows_usd = account_data[2] / (10**8)
        current_health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"📊 Current Position:")
        print(f"   Health Factor: {current_health_factor:.4f}")
        print(f"   Available Borrows: ${available_borrows_usd:.2f}")
        
        if current_health_factor < 2.0:
            print("⚠️ WARNING: Health factor is low for borrowing")
            return False
        
        if available_borrows_usd < 0.5:
            print("⚠️ WARNING: Very low borrowing capacity")
            return False
        
        print("✅ Manual trigger is ready - system will activate on next monitoring cycle")
        print("🔄 The autonomous agent will detect the override and execute the sequence")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up manual trigger: {e}")
        return False

if __name__ == "__main__":
    activate_manual_trigger()
