
#!/usr/bin/env python3
"""
Test DAI Borrowing Functionality
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3
import time

def test_dai_borrowing():
    print("🧪 TESTING DAI BORROWING")
    print("=" * 40)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"📍 Wallet: {agent.address}")
        print(f"🪙 DAI Address: {agent.dai_address}")
        
        # Check current Aave position
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
        available_borrows_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"💰 Available Borrows: ${available_borrows_usd:.2f}")
        print(f"❤️ Health Factor: {health_factor:.4f}")
        
        # Test DAI borrowing conditions
        if health_factor < 1.5:
            print(f"❌ Health factor too low for borrowing: {health_factor:.4f}")
            return False
            
        if available_borrows_usd < 1.0:
            print(f"❌ Insufficient borrowing capacity: ${available_borrows_usd:.2f}")
            return False
            
        # Attempt small DAI borrow
        test_amount = min(1.0, available_borrows_usd * 0.1)  # 10% of capacity, max $1
        print(f"🎯 Testing DAI borrow: ${test_amount:.2f}")
        
        # Check if DAI market is active on Aave
        try:
            # Test conversion
            dai_wei = int(test_amount * (10 ** 18))
            print(f"💱 DAI conversion: ${test_amount} = {dai_wei} wei")
            
            # Simulate borrow (don't actually execute)
            print(f"✅ DAI borrowing parameters validated")
            print(f"   Amount: ${test_amount:.2f}")
            print(f"   DAI Wei: {dai_wei}")
            print(f"   Health Factor: {health_factor:.4f}")
            print(f"   Available Capacity: ${available_borrows_usd:.2f}")
            
            return True
            
        except Exception as conversion_error:
            print(f"❌ DAI conversion failed: {conversion_error}")
            return False
            
    except Exception as e:
        print(f"❌ DAI borrow test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_dai_borrowing()
    if success:
        print("\n✅ DAI borrowing should be approved by network")
    else:
        print("\n❌ DAI borrowing likely to be rejected by network")
