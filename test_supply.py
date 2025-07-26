
#!/usr/bin/env python3

import os
import sys
from arbitrum_testnet_agent import ArbitrumTestnetAgent
import time

def test_dai_supply():
    """Test DAI supply to Aave with proper error handling"""
    print("🧪 TESTING DAI SUPPLY TO AAVE")
    print("=" * 40)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print(f"🤖 Agent initialized")
        print(f"📍 Wallet: {agent.address}")
        print(f"⛓️ Chain ID: {agent.w3.eth.chain_id}")
        
        # Initialize integrations
        agent.initialize_integrations()
        
        # Check DAI balance
        dai_balance = agent.aave.get_dai_balance()
        print(f"💰 DAI Balance: {dai_balance:.6f} DAI")
        
        if dai_balance < 0.1:
            print("❌ Insufficient DAI balance for test")
            return False
        
        # Test supply amount (small amount for testing)
        supply_amount = min(0.1, dai_balance * 0.1)  # 10% of balance or 0.1 DAI max
        
        print(f"🏦 Testing supply of {supply_amount:.6f} DAI")
        
        # Execute supply
        result = agent.aave.supply_dai_to_aave(supply_amount)
        
        if result:
            print(f"✅ Supply successful!")
            print(f"🔗 Transaction: {result}")
            
            # Wait and check updated position
            print("⏳ Waiting for confirmation...")
            time.sleep(10)
            
            # Check updated DAI balance
            new_dai_balance = agent.aave.get_dai_balance()
            print(f"📊 Updated DAI Balance: {new_dai_balance:.6f} DAI")
            print(f"📊 DAI Supplied: {dai_balance - new_dai_balance:.6f} DAI")
            
            return True
        else:
            print("❌ Supply failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_dai_supply()
