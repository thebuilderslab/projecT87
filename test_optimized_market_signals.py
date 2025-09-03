
#!/usr/bin/env python3
"""
Test Optimized Market Signal Parameters
Verify that new less conservative parameters enable successful DAI→ARB swaps
"""

import os
import time
import json
from datetime import datetime

def test_optimized_parameters():
    """Test new optimized market signal parameters for improved opportunity capture"""
    print("🚀 TESTING OPTIMIZED MARKET SIGNAL PARAMETERS")
    print("=" * 60)
    
    # Set optimized environment variables for testing
    os.environ['MARKET_SIGNAL_ENABLED'] = 'true'
    os.environ['BTC_DROP_THRESHOLD'] = '0.005'  # 0.5%
    os.environ['ARB_RSI_OVERSOLD'] = '40'
    os.environ['DAI_TO_ARB_THRESHOLD'] = '0.5'  # 50%
    
    print("✅ Environment configured with optimized parameters")
    
    try:
        # Test 1: Verify optimized configuration loading
        print("\n1️⃣ Testing Optimized Configuration Loading...")
        from environmental_configuration import (
            BTC_DROP_THRESHOLD, ARB_RSI_OVERSOLD, DAI_TO_ARB_THRESHOLD
        )
        
        print(f"   BTC Drop Threshold: {BTC_DROP_THRESHOLD*100:.1f}% (optimized from 1.0%)")
        print(f"   ARB RSI Oversold: {ARB_RSI_OVERSOLD} (optimized from 35)")
        print(f"   DAI→ARB Confidence: {DAI_TO_ARB_THRESHOLD*100:.0f}% (optimized from 70%)")
        
        assert BTC_DROP_THRESHOLD == 0.005, f"BTC threshold not optimized: {BTC_DROP_THRESHOLD}"
        assert ARB_RSI_OVERSOLD == 40.0, f"ARB RSI not optimized: {ARB_RSI_OVERSOLD}"
        assert DAI_TO_ARB_THRESHOLD == 0.5, f"DAI threshold not optimized: {DAI_TO_ARB_THRESHOLD}"
        
        print("✅ Optimized parameters loaded successfully")
        
        # Test 2: Initialize Market Signal Strategy
        print("\n2️⃣ Testing Market Signal Strategy with Optimized Parameters...")
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        agent = ArbitrumTestnetAgent()
        
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            strategy = agent.market_signal_strategy
            print("✅ Market Signal Strategy initialized")
            
            # Test 3: MACD Bullish Crossover Detection
            print("\n3️⃣ Testing MACD Bullish Crossover Detection...")
            
            # Simulate MACD bullish crossover scenario
            mock_arb_analysis = {
                'price': 0.68,
                'change_24h': 1.2,
                'signal': 'bullish',
                'rsi': 38,  # Below new 40 threshold
                'pattern': 'bullish_momentum',
                'confidence': 0.7,
                'price_change_5min': 0.4,
                'macd_line': 0.002,
                'macd_signal': 0.001,
                'macd_histogram': 0.001
            }
            
            # Test MACD crossover detection
            if hasattr(strategy, '_detect_macd_bullish_crossover'):
                crossover_detected = strategy._detect_macd_bullish_crossover(mock_arb_analysis)
                print(f"   MACD Bullish Crossover: {'✅ DETECTED' if crossover_detected else '❌ NOT DETECTED'}")
            else:
                print("   ⚠️ MACD crossover method not available")
            
            # Test 4: Overall Signal Analysis with Optimized Parameters
            print("\n4️⃣ Testing Overall Signal Analysis...")
            
            signals = strategy.analyze_market_signals()
            if signals:
                action = signals.get('action', 'hold')
                confidence = signals.get('confidence_level', 0)
                recommendation = signals.get('recommendation', 'HOLD')
                signals_detected = signals.get('signals_detected', [])
                
                print(f"   Action: {action.upper()}")
                print(f"   Confidence: {confidence:.2f} (threshold: {DAI_TO_ARB_THRESHOLD:.2f})")
                print(f"   Recommendation: {recommendation}")
                print(f"   Signals Detected: {len(signals_detected)}")
                
                for signal in signals_detected:
                    print(f"      • {signal}")
                
                # Check if optimized parameters would trigger DAI→ARB
                if action == 'dai_to_arb' and confidence >= DAI_TO_ARB_THRESHOLD:
                    print("🚀 SUCCESS: Optimized parameters would trigger DAI→ARB swap!")
                    
                    # Test 5: Simulate DAI→ARB Swap Execution
                    print("\n5️⃣ Simulating DAI→ARB Swap Execution...")
                    
                    swap_result = simulate_dai_arb_swap(agent, confidence, signals_detected)
                    return swap_result
                    
                else:
                    print(f"⚠️ Optimized parameters not sufficient for swap trigger")
                    print(f"   Action: {action}, Confidence: {confidence:.2f}")
                    return False
            else:
                print("❌ No market signals generated")
                return False
                
        else:
            print("❌ Market Signal Strategy not available")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_dai_arb_swap(agent, confidence, signals_detected):
    """Simulate a DAI→ARB swap with optimized parameters"""
    try:
        print("💱 SIMULATING DAI→ARB SWAP WITH OPTIMIZED PARAMETERS")
        print("=" * 50)
        
        # Get current balances
        if hasattr(agent, 'aave') and agent.aave:
            account_data = agent.aave.get_user_account_data()
            if account_data:
                available_borrows = account_data.get('availableBorrowsUSD', 0)
                health_factor = account_data.get('healthFactor', 0)
                
                print(f"💰 Available to borrow: ${available_borrows:.2f}")
                print(f"🏥 Health Factor: {health_factor:.3f}")
                
                # Check if conditions are met for actual swap
                if health_factor > 1.8 and available_borrows > 1.0:
                    # Calculate swap amount (conservative for test)
                    swap_amount = min(available_borrows * 0.1, 5.0)  # 10% or $5 max
                    
                    print(f"🎯 Calculated swap amount: ${swap_amount:.2f}")
                    print(f"📊 Triggered by signals: {', '.join(signals_detected)}")
                    print(f"📈 Confidence level: {confidence:.2f}")
                    
                    # Log successful trigger
                    success_log = {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'dai_to_arb',
                        'amount_usd': swap_amount,
                        'confidence': confidence,
                        'triggers': signals_detected,
                        'health_factor': health_factor,
                        'available_borrows': available_borrows,
                        'trigger_reason': 'Bullish signal from optimized parameters'
                    }
                    
                    # Save to swap log
                    try:
                        with open('optimized_swap_test_log.json', 'w') as f:
                            json.dump(success_log, f, indent=2)
                        print("✅ Swap simulation logged to optimized_swap_test_log.json")
                    except Exception as log_error:
                        print(f"⚠️ Logging error: {log_error}")
                    
                    print("\n🎉 SUCCESS: DAI→ARB swap would be triggered by optimized parameters!")
                    print(f"✅ SWAP TRIGGERED BY: Bullish signal from optimized parameters")
                    print(f"💡 Amount: ${swap_amount:.2f} DAI → ARB")
                    print(f"📊 Confidence: {confidence:.2f} (meets {0.5:.1f} threshold)")
                    
                    return True
                else:
                    print(f"❌ Account conditions not suitable for swap")
                    print(f"   Health Factor: {health_factor:.3f} (need >1.8)")
                    print(f"   Available Borrows: ${available_borrows:.2f} (need >1.0)")
                    return False
            else:
                print("❌ Cannot retrieve account data")
                return False
        else:
            print("❌ Aave integration not available")
            return False
            
    except Exception as e:
        print(f"❌ Swap simulation failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive test with actual swap execution simulation"""
    print("🚀 TESTING OPTIMIZED MARKET LOGIC WITH SWAP EXECUTION")
    print("=" * 60)
    
    # Test optimized parameters first
    params_success = test_optimized_parameters()
    
    if params_success:
        print("\n✅ OPTIMIZED PARAMETERS VALIDATED")
        print("🔄 Testing actual swap execution logic...")
        
        # Test actual swap execution with optimized agent
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            
            # Initialize agent with optimized settings
            agent = ArbitrumTestnetAgent()
            agent.debt_swap_active = True
            
            # Force mock data for testing
            if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
                # Simulate optimized market conditions
                test_result = agent.run_real_defi_task(1, 1, {'optimization_test': True})
                
                print(f"🎯 Agent execution result: {test_result:.3f}")
                
                if test_result > 0:
                    print("✅ SWAP EXECUTION LOGIC OPERATIONAL")
                    return True
                else:
                    print("⚠️ Swap execution needs further optimization")
                    return False
            else:
                print("❌ Market signal strategy not available for testing")
                return False
                
        except Exception as e:
            print(f"❌ Swap execution test failed: {e}")
            return False
    else:
        return False

if __name__ == "__main__":
    print("🔍 COMPREHENSIVE OPTIMIZED MARKET SIGNAL TEST")
    print("🎯 Objective: Verify optimized parameters and swap execution")
    print()
    
    success = run_comprehensive_test()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ OPTIMIZATION AND EXECUTION TEST PASSED")
        print("🚀 System ready to execute swaps with optimized parameters")
        print("💡 Next: Monitor live execution in autonomous mode")
    else:
        print("❌ OPTIMIZATION TEST INCOMPLETE")
        print("🔧 Review system logs and continue debugging")
    print("=" * 60)
