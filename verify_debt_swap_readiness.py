
#!/usr/bin/env python3
"""
Debt Swap Readiness Verification Script
Verifies all components are ready for debt swap execution and network approval
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def check_environment_variables():
    """Check all required environment variables for debt swap"""
    print("🔍 CHECKING ENVIRONMENT VARIABLES")
    print("-" * 40)
    
    required_vars = {
        'MARKET_SIGNAL_ENABLED': 'true',
        'BTC_DROP_THRESHOLD': '0.002',
        'DAI_TO_ARB_THRESHOLD': '0.92',
        'ARB_TO_DAI_THRESHOLD': '0.88',
        'ARB_RSI_OVERSOLD': '30',
        'ARB_RSI_OVERBOUGHT': '70'
    }
    
    all_set = True
    for var, expected in required_vars.items():
        actual = os.getenv(var, 'NOT_SET')
        status = "✅" if actual != 'NOT_SET' else "❌"
        print(f"{status} {var}: {actual}")
        if actual == 'NOT_SET':
            all_set = False
    
    return all_set

def check_agent_initialization():
    """Check if agent can initialize successfully"""
    print("\n🤖 CHECKING AGENT INITIALIZATION")
    print("-" * 40)
    
    try:
        agent = ArbitrumTestnetAgent()
        print("✅ Agent created successfully")
        
        if agent.initialize_integrations():
            print("✅ Integrations initialized successfully")
            
            # Check specific integrations
            if hasattr(agent, 'aave') and agent.aave:
                print("✅ Aave integration ready")
            else:
                print("❌ Aave integration failed")
                return False
                
            if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
                print("✅ Market Signal Strategy initialized")
                if agent.market_signal_strategy.market_signal_enabled:
                    print("✅ Debt swap system enabled")
                else:
                    print("❌ Debt swap system disabled")
                    return False
            else:
                print("❌ Market Signal Strategy not available")
                return False
                
            return True
        else:
            print("❌ Integration initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

def check_account_status():
    """Check current account status for debt swap readiness"""
    print("\n💰 CHECKING ACCOUNT STATUS")
    print("-" * 40)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot retrieve account data")
            return False
        
        health_factor = account_data.get('healthFactor', 0)
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        total_collateral = account_data.get('totalCollateralUSD', 0)
        total_debt = account_data.get('totalDebtUSD', 0)
        eth_balance = agent.get_eth_balance()
        
        print(f"📊 Health Factor: {health_factor:.4f}")
        print(f"💰 Total Collateral: ${total_collateral:.2f}")
        print(f"💳 Total Debt: ${total_debt:.2f}")
        print(f"💵 Available Borrows: ${available_borrows:.2f}")
        print(f"⛽ ETH Balance: {eth_balance:.6f}")
        
        # Check readiness criteria
        ready = True
        
        if health_factor < 2.0:
            print("❌ Health factor too low for safe operations")
            ready = False
        else:
            print("✅ Health factor adequate")
        
        if available_borrows < 2.0:
            print("❌ Insufficient borrowing capacity")
            ready = False
        else:
            print("✅ Sufficient borrowing capacity")
        
        if eth_balance < 0.001:
            print("❌ Insufficient ETH for gas")
            ready = False
        else:
            print("✅ Sufficient ETH for gas")
            
        return ready
        
    except Exception as e:
        print(f"❌ Account status check failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🔍 DEBT SWAP READINESS VERIFICATION")
    print("=" * 50)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Agent Initialization", check_agent_initialization),
        ("Account Status", check_account_status)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        result = check_func()
        if not result:
            all_passed = False
    
    print(f"\n📋 VERIFICATION SUMMARY")
    print("=" * 30)
    
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("🚀 System ready for debt swap execution")
        print("🎯 Network approval likelihood: HIGH")
    else:
        print("❌ SOME CHECKS FAILED")
        print("⚠️ System not ready for debt swap execution")
        print("🔧 Fix issues above before proceeding")
    
    return all_passed

if __name__ == "__main__":
    main()
