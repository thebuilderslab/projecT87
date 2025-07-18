
#!/usr/bin/env python3
"""
Immediate Borrow Fix Script
Fixes gas pricing issues causing borrow failures
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
import time

def fix_borrow_immediately():
    """Test and fix borrowing with proper gas handling"""
    try:
        print("🔧 IMMEDIATE BORROW FIX")
        print("=" * 40)
        
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"✅ Agent initialized: {agent.address}")
        print(f"💰 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Get current network conditions
        current_block = agent.w3.eth.get_block('latest')
        base_fee = current_block['baseFeePerGas']
        gas_price = agent.w3.eth.gas_price
        
        print(f"🔧 Network conditions:")
        print(f"   Base fee: {base_fee:,} wei ({agent.w3.from_wei(base_fee, 'gwei'):.2f} gwei)")
        print(f"   Gas price: {gas_price:,} wei ({agent.w3.from_wei(gas_price, 'gwei'):.2f} gwei)")
        
        # Test small borrow with fixed gas pricing
        test_amount = 1.0  # $1 USDC
        print(f"\n🧪 Testing ${test_amount} USDC borrow with fixed gas...")
        
        # Use enhanced borrow manager
        if hasattr(agent, 'enhanced_borrow_manager'):
            result = agent.enhanced_borrow_manager.safe_borrow_with_fallbacks(
                test_amount,
                agent.usdc_address
            )
            
            if result:
                print(f"✅ BORROW FIX SUCCESSFUL!")
                print(f"🔗 Transaction: {result}")
                return True
            else:
                print(f"❌ Borrow still failing")
                return False
        else:
            print("❌ Enhanced borrow manager not available")
            return False
            
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_borrow_immediately()
    print(f"\n🎯 BORROW FIX: {'✅ SUCCESS' if success else '❌ FAILED'}")
