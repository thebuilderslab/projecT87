
#!/usr/bin/env python3
"""
Comprehensive Debt Swap System Test
Tests market signal detection, environment setup, and network execution
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_complete_debt_swap_system():
    """Test the complete debt swap system"""
    print("🧪 COMPREHENSIVE DEBT SWAP SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: Environment Variables
    print("\n1️⃣ Testing Environment Variables...")
    from environment_validator import validate_market_signal_environment
    env_ok = validate_market_signal_environment()
    
    if not env_ok:
        print("❌ Environment validation failed - please fix environment variables first")
        return False
    
    # Test 2: Agent Initialization
    print("\n2️⃣ Testing Agent Initialization...")
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        print(f"✅ Agent initialized: {agent.address}")
        print(f"✅ Chain ID: {agent.w3.eth.chain_id}")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test 3: Market Signal Strategy
    print("\n3️⃣ Testing Market Signal Strategy...")
    if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
        mss = agent.market_signal_strategy
        print(f"✅ Market Signal Strategy initialized")
        print(f"   Enabled: {mss.market_signal_enabled}")
        print(f"   BTC Threshold: {mss.btc_drop_threshold}")
        print(f"   DAI→ARB Threshold: {mss.dai_to_arb_threshold}")
        
        # Test signal generation
        signal = mss.analyze_market_signals()
        if signal:
            print(f"✅ Market signal generated: {signal.signal_type} (confidence: {signal.confidence:.2f})")
        else:
            print(f"⚠️ No market signal generated (normal if conditions not met)")
    else:
        print(f"❌ Market Signal Strategy not initialized")
        return False
    
    # Test 4: Account Status
    print("\n4️⃣ Testing Account Status...")
    try:
        account_data = agent.aave.get_user_account_data()
        if account_data:
            health_factor = account_data.get('healthFactor', 0)
            available_borrows = account_data.get('availableBorrowsUSD', 0)
            
            print(f"✅ Health Factor: {health_factor:.4f}")
            print(f"✅ Available Borrows: ${available_borrows:.2f}")
            
            can_execute = health_factor > 1.5 and available_borrows >= 1.0
            print(f"✅ Can Execute Debt Swaps: {'YES' if can_execute else 'NO'}")
            
            if not can_execute:
                print(f"⚠️ Account not ready for debt swaps")
                if health_factor <= 1.5:
                    print(f"   - Health factor too low")
                if available_borrows < 1.0:
                    print(f"   - Insufficient borrowing capacity")
        else:
            print(f"❌ Could not retrieve account data")
            return False
    except Exception as e:
        print(f"❌ Account status check failed: {e}")
        return False
    
    # Test 5: Network Connectivity
    print("\n5️⃣ Testing Network Connectivity...")
    try:
        eth_balance = agent.get_eth_balance()
        print(f"✅ ETH Balance: {eth_balance:.6f} ETH")
        
        if eth_balance < 0.001:
            print(f"⚠️ Low ETH balance for gas fees")
        
        # Test RPC connectivity
        latest_block = agent.w3.eth.block_number
        print(f"✅ Latest Block: {latest_block}")
        
        # Test contract connectivity
        dai_balance = agent.aave.get_token_balance(agent.dai_address)
        print(f"✅ DAI Balance: {dai_balance:.6f}")
        
    except Exception as e:
        print(f"❌ Network connectivity test failed: {e}")
        return False
    
    # Test 6: Trading Readiness
    print("\n6️⃣ Testing Trading Readiness...")
    try:
        trade_ready = agent.market_signal_strategy.should_execute_trade()
        print(f"✅ Trade Execution Ready: {'YES' if trade_ready else 'NO'}")
        
        if trade_ready:
            print(f"🎯 SYSTEM READY FOR DEBT SWAP EXECUTION")
        else:
            print(f"⏰ System ready, waiting for market conditions")
            
    except Exception as e:
        print(f"❌ Trading readiness test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ COMPREHENSIVE SYSTEM TEST COMPLETED")
    print("🚀 Debt swap system is properly configured and operational")
    
    return True

if __name__ == "__main__":
    test_complete_debt_swap_system()
