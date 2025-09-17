
#!/usr/bin/env python3
"""
Debt Swap Diagnostic Tool - Debug why debt swaps aren't executing on-chain
"""

import os
import time
from datetime import datetime
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def diagnose_debt_swap_strategy():
    """Comprehensive diagnosis of debt swap strategy execution"""
    print("🔍 DEBT SWAP STRATEGY DIAGNOSTIC")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Check 1: Market Signal Strategy Status
        print("\n1️⃣ Market Signal Strategy Status:")
        print(f"   🔍 Environment Variables:")
        print(f"      MARKET_SIGNAL_ENABLED: {os.getenv('MARKET_SIGNAL_ENABLED', 'NOT SET')}")
        print(f"      BTC_DROP_THRESHOLD: {os.getenv('BTC_DROP_THRESHOLD', 'NOT SET')}")
        print(f"      DAI_TO_ARB_THRESHOLD: {os.getenv('DAI_TO_ARB_THRESHOLD', 'NOT SET')}")
        
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            mss = agent.market_signal_strategy
            print(f"   ✅ Market Signal Strategy: Initialized")
            print(f"   📊 Enabled: {mss.market_signal_enabled}")
            print(f"   🎯 BTC Drop Threshold: {mss.btc_drop_threshold*100:.1f}%")
            print(f"   📈 DAI→ARB Confidence Threshold: {mss.dai_to_arb_threshold:.0%}")
            print(f"   ⏰ Signal Cooldown: {mss.signal_cooldown}s")
            
            # Test current market conditions
            print(f"\n   📊 Current Market Analysis:")
            signal = mss.analyze_market_signals()
            if signal:
                print(f"      Signal Type: {signal.signal_type}")
                print(f"      Confidence: {signal.confidence:.2f}")
                print(f"      BTC 1h Change: {getattr(signal, 'btc_price_change', signal.get('btc_price_change', 0.0)) if hasattr(signal, 'get') else getattr(signal, 'btc_price_change', 0.0):.2f}%")
                print(f"      ARB Technical Score: {signal.arb_technical_score:.1f}")
                
                should_execute, strategy_type = mss.should_execute_market_strategy(signal)
                print(f"      Should Execute: {'YES' if should_execute else 'NO'}")
                if should_execute:
                    print(f"      Strategy Type: {strategy_type}")
            else:
                print(f"      ❌ No signal generated")
        else:
            print(f"   ❌ Market Signal Strategy: Not initialized")
        
        # Check 2: Account Status
        print(f"\n2️⃣ Account Status for Debt Swaps:")
        account_data = agent.aave.get_user_account_data()
        if account_data:
            health_factor = account_data.get('healthFactor', 0)
            available_borrows = account_data.get('availableBorrowsUSD', 0)
            total_debt = account_data.get('totalDebtUSD', 0)
            
            print(f"   💰 Available Borrows: ${available_borrows:.2f}")
            print(f"   ❤️ Health Factor: {health_factor:.4f}")
            print(f"   💸 Total Debt: ${total_debt:.2f}")
            
            # Check if account can execute debt swaps
            can_borrow = health_factor > 1.5 and available_borrows >= 1.0
            print(f"   🎯 Can Execute Debt Swap: {'YES' if can_borrow else 'NO'}")
            
            if not can_borrow:
                if health_factor <= 1.5:
                    print(f"      ⚠️ Health factor too low for borrowing")
                if available_borrows < 1.0:
                    print(f"      ⚠️ Insufficient borrowing capacity")
        
        # Check 3: Recent Transaction History
        print(f"\n3️⃣ Transaction Execution Check:")
        eth_balance = agent.get_eth_balance()
        print(f"   ⛽ ETH Balance: {eth_balance:.6f} ETH")
        
        if eth_balance < 0.001:
            print(f"   ❌ Insufficient ETH for gas fees")
        else:
            print(f"   ✅ Sufficient ETH for transactions")
        
        # Check 4: System Operation Logs
        print(f"\n4️⃣ System Operation Status:")
        if hasattr(agent, 'last_successful_operation_time'):
            last_op_time = agent.last_successful_operation_time
            if last_op_time > 0:
                time_since = time.time() - last_op_time
                print(f"   ⏰ Last Successful Operation: {time_since/60:.1f} minutes ago")
            else:
                print(f"   ⚠️ No successful operations recorded")
        
        # Check cooldown status
        is_cooldown, remaining = agent.is_operation_in_cooldown('market_signal')
        if is_cooldown:
            print(f"   ⏰ Market signal operations in cooldown: {remaining:.0f}s remaining")
        else:
            print(f"   ✅ Ready for market signal operations")
        
        # Check 5: Force Execute Test (if conditions allow)
        print(f"\n5️⃣ Debt Swap Execution Test:")
        if (hasattr(agent, 'market_signal_strategy') and 
            agent.market_signal_strategy and 
            account_data and 
            account_data.get('availableBorrowsUSD', 0) >= 1.0 and
            account_data.get('healthFactor', 0) > 1.5):
            
            print(f"   🎯 Attempting test debt swap execution...")
            test_amount = min(1.0, account_data.get('availableBorrowsUSD', 0) * 0.1)
            
            # This would execute the actual swap - uncomment to test
            # success = agent.market_signal_strategy._execute_dai_to_arb_swap(test_amount)
            # print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
            
            print(f"   💡 Test amount would be: ${test_amount:.2f}")
            print(f"   📝 Uncomment execution line in diagnostic to test")
        else:
            print(f"   ⚠️ Conditions not met for test execution")
        
        print(f"\n📊 DIAGNOSIS SUMMARY:")
        print(f"=" * 30)
        print(f"🔍 Check your Replit Secrets for:")
        print(f"   • MARKET_SIGNAL_ENABLED=true")
        print(f"   • BTC_DROP_THRESHOLD=0.003 (or lower)")
        print(f"   • DAI_TO_ARB_THRESHOLD=0.92")
        print(f"🎯 Market conditions must show:")
        print(f"   • BTC declining ≥0.3% in 1 hour")
        print(f"   • ARB oversold (RSI ≤30)")  
        print(f"   • 92% confidence threshold met")
        print(f"💰 Account must have:")
        print(f"   • Health factor >1.5")
        print(f"   • Available borrows ≥$1.00")
        print(f"   • Sufficient ETH for gas")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return False

if __name__ == "__main__":
    diagnose_debt_swap_strategy()
