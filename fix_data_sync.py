
#!/usr/bin/env python3
"""
Emergency Data Sync Fix
Resolves stale/cached data vs live data mismatches
"""

import json
import time
from web3 import Web3
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def fix_data_sync():
    """Fix data synchronization issues"""
    print("🔧 EMERGENCY DATA SYNC FIX")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"🔍 Checking live Aave data vs cached data...")
        
        # Get fresh live data directly from Aave contract
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
        
        live_collateral = account_data[0] / (10**8)
        live_debt = account_data[1] / (10**8)
        live_available = account_data[2] / (10**8)
        live_hf = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"✅ LIVE AAVE DATA:")
        print(f"   Collateral: ${live_collateral:.2f}")
        print(f"   Debt: ${live_debt:.2f}")
        print(f"   Available Borrows: ${live_available:.2f}")
        print(f"   Health Factor: {live_hf:.3f}")
        
        # Force update baseline if we have good data
        if live_collateral > 50:
            agent.last_collateral_value_usd = live_collateral
            agent.baseline_initialized = True
            
            # Save to baseline file
            baseline_data = {
                'last_collateral_value_usd': live_collateral,
                'baseline_initialized': True,
                'timestamp': time.time(),
                'wallet_address': agent.address,
                'sync_method': 'emergency_data_sync_fix'
            }
            
            with open('agent_baseline.json', 'w') as f:
                json.dump(baseline_data, f, indent=2)
            
            print(f"✅ BASELINE SYNCHRONIZED: ${live_collateral:.2f}")
            print(f"🎯 Next trigger at: ${live_collateral + 12:.2f}")
            
            return True
        else:
            print(f"❌ Live data still shows insufficient collateral")
            return False
            
    except Exception as e:
        print(f"❌ Data sync fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_data_sync()
    if success:
        print(f"\n✅ DATA SYNC FIXED!")
        print(f"System should now see live position correctly")
    else:
        print(f"\n❌ DATA SYNC FIX FAILED!")
