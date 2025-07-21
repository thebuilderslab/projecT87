
#!/usr/bin/env python3
"""
Direct USDC Borrow Test
Test USDC borrowing without complex strategy layers
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3

def test_direct_usdc_borrow():
    print("🧪 DIRECT USDC BORROW TEST")
    print("=" * 40)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"✅ Agent initialized")
        print(f"📍 Wallet: {agent.address}")
        
        # Get current position
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
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"💰 Available Borrows: ${available_borrows_usd:.2f}")
        print(f"❤️ Health Factor: {health_factor:.4f}")
        
        if available_borrows_usd < 1.0:
            print("❌ Insufficient borrowing capacity for test")
            return False
            
        # Test small USDC borrow (1 USD)
        test_amount = 1.0
        print(f"\n🏦 Testing ${test_amount} USDC borrow...")
        
        # Convert to USDC wei (6 decimals)
        usdc_amount_wei = int(test_amount * (10 ** 6))
        print(f"💱 Amount: {usdc_amount_wei} USDC wei")
        
        # Try direct borrow
        result = agent.aave.borrow(
            test_amount,  # Use USD amount, not wei
            agent.usdc_address
        )
        
        if result:
            print(f"✅ USDC borrow successful: {result}")
            return True
        else:
            print(f"❌ USDC borrow failed")
            agent.analyze_borrow_failure()
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_usdc_borrow()
    print(f"\n🎯 DIRECT USDC BORROW TEST: {'✅ PASSED' if success else '❌ FAILED'}")
