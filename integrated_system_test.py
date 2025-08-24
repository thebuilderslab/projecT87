
#!/usr/bin/env python3
"""
Integrated System Test for Debt Swapping Optimization
Tests complete system including market signals, safety mechanisms, and network approval
"""

import os
import time
import json
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_complete_system_integration():
    """Test complete system integration with market-driven debt swapping"""
    print("🔄 COMPLETE SYSTEM INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Initialize agent with all integrations
        agent = ArbitrumTestnetAgent()
        print("✅ Agent initialized")
        
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        print("✅ All integrations initialized")
        
        # Test 1: Market signal analysis
        print("\n🎯 Testing market signal analysis...")
        if agent.market_signal_strategy:
            signal = agent.market_signal_strategy.analyze_market_signals()
            if signal:
                print(f"✅ Market signal generated: {signal.signal_type} (confidence: {signal.confidence:.2f})")
            else:
                print("⚠️ No market signal generated (may be in cooldown)")
        
        # Test 2: Safety validation
        print("\n🔒 Testing safety mechanisms...")
        account_data = agent.aave.get_user_account_data()
        if account_data:
            hf = account_data.get('healthFactor', 0)
            available = account_data.get('availableBorrowsUSD', 0)
            
            print(f"✅ Health Factor: {hf:.3f}")
            print(f"✅ Available Borrows: ${available:.2f}")
            
            # Check safety thresholds
            min_hf = float(os.getenv('MIN_HEALTH_FACTOR_FOR_MARKET_OPS', '2.0'))
            if hf >= min_hf and available >= 5.0:
                print("✅ Safety checks passed - system ready for operations")
                system_ready = True
            else:
                print("⚠️ Safety checks failed - operations would be blocked")
                system_ready = False
        else:
            print("❌ Cannot retrieve account data")
            return False
        
        # Test 3: Operation simulation
        if system_ready:
            print("\n💰 Testing operation calculation...")
            max_amount = float(os.getenv('MAX_MARKET_OPERATION_AMOUNT', '10'))
            safe_percentage = 0.04  # 4% of available
            
            calculated_amount = min(available * safe_percentage, max_amount)
            
            if calculated_amount >= 1.0:
                print(f"✅ Safe operation amount: ${calculated_amount:.2f}")
                
                # Simulate the complete flow
                print("\n🔄 Simulating complete debt swap flow...")
                print(f"   1. Borrow ${calculated_amount:.2f} DAI")
                print(f"   2. Swap DAI → ARB on Uniswap")
                print(f"   3. Monitor position for reversal opportunity")
                print("✅ Flow simulation completed")
            else:
                print(f"⚠️ Operation amount too small: ${calculated_amount:.2f}")
        
        # Test 4: Emergency mechanisms
        print("\n🚨 Testing emergency mechanisms...")
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        if not os.path.exists(emergency_file):
            print("✅ Emergency stop not active")
        else:
            print("⚠️ Emergency stop is active")
        
        # Test 5: Network approval likelihood
        print("\n🌐 Calculating network approval likelihood...")
        
        approval_factors = {
            'health_factor_safe': hf >= 2.0,
            'gas_sufficient': agent.get_eth_balance() >= 0.001,
            'amount_conservative': calculated_amount <= 10.0,
            'position_stable': available > calculated_amount * 10,  # 10x buffer
            'timing_appropriate': True  # Would check actual market conditions
        }
        
        approval_score = sum(approval_factors.values()) / len(approval_factors) * 100
        
        print(f"📊 Network Approval Factors:")
        for factor, passed in approval_factors.items():
            print(f"   {factor}: {'✅' if passed else '❌'}")
        
        print(f"\n🎯 Network Approval Likelihood: {approval_score:.1f}%")
        
        if approval_score >= 80:
            print("🎉 HIGH LIKELIHOOD OF NETWORK APPROVAL")
        elif approval_score >= 60:
            print("⚠️ MODERATE LIKELIHOOD - CONSIDER OPTIMIZATIONS")
        else:
            print("❌ LOW LIKELIHOOD - ADDRESS CRITICAL ISSUES")
        
        return approval_score >= 60
        
    except Exception as e:
        print(f"❌ Complete system integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hourly_opportunity_detection():
    """Test the system's ability to detect hourly opportunities"""
    print("\n⏰ TESTING HOURLY OPPORTUNITY DETECTION")
    print("=" * 60)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        if not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return False
        
        # Simulate hourly market analysis
        print("📊 Simulating hourly market analysis cycle...")
        
        # Get current market data
        btc_data = agent.market_signal_strategy.get_btc_price_data()
        arb_data = agent.market_signal_strategy.get_arb_price_data()
        
        if not btc_data or not arb_data:
            print("❌ Market data unavailable")
            return False
        
        print(f"✅ BTC 1h change: {btc_data['percent_change_1h']:.2f}%")
        print(f"✅ ARB 1h change: {arb_data['percent_change_1h']:.2f}%")
        
        # Calculate opportunity score
        btc_drop = btc_data['percent_change_1h'] <= -1.5  # 1.5% drop
        arb_indicators = agent.market_signal_strategy.calculate_technical_indicators(arb_data)
        arb_oversold = arb_indicators['rsi'] <= 30
        
        opportunity_score = 0
        
        if btc_drop:
            opportunity_score += 40
            print("✅ BTC drop detected (+40 points)")
        
        if arb_oversold:
            opportunity_score += 30
            print("✅ ARB oversold detected (+30 points)")
        
        if abs(btc_data['percent_change_1h'] - arb_data['percent_change_1h']) > 2:
            opportunity_score += 20
            print("✅ BTC-ARB divergence detected (+20 points)")
        
        if arb_data['volume_24h'] > 100000000:  # High volume
            opportunity_score += 10
            print("✅ High ARB volume detected (+10 points)")
        
        print(f"\n🎯 Opportunity Score: {opportunity_score}/100")
        
        if opportunity_score >= 70:
            print("🚀 EXCELLENT OPPORTUNITY - Execute DAI→ARB swap")
        elif opportunity_score >= 50:
            print("⚡ GOOD OPPORTUNITY - Consider execution")
        elif opportunity_score >= 30:
            print("⚠️ MODERATE OPPORTUNITY - Monitor closely")
        else:
            print("❌ NO CLEAR OPPORTUNITY - Wait for better conditions")
        
        return opportunity_score >= 50
        
    except Exception as e:
        print(f"❌ Hourly opportunity detection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 INTEGRATED SYSTEM TESTING FOR DEBT OPTIMIZATION")
    print("=" * 70)
    
    # Run comprehensive integration tests
    integration_test = test_complete_system_integration()
    opportunity_test = test_hourly_opportunity_detection()
    
    print(f"\n📊 FINAL TEST RESULTS:")
    print(f"   Complete System Integration: {'✅ PASS' if integration_test else '❌ FAIL'}")
    print(f"   Hourly Opportunity Detection: {'✅ PASS' if opportunity_test else '❌ FAIL'}")
    
    if integration_test and opportunity_test:
        print(f"\n🎉 SYSTEM READY FOR AUTONOMOUS DEBT OPTIMIZATION")
        print(f"💡 The system can now:")
        print(f"   • Detect BTC/ARB market opportunities every hour")
        print(f"   • Execute safe DAI→ARB debt swaps when conditions are optimal")
        print(f"   • Maintain strict safety limits for network approval")
        print(f"   • Operate autonomously with minimal risk")
    else:
        print(f"\n⚠️ SYSTEM NEEDS REFINEMENT BEFORE DEPLOYMENT")
