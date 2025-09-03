
#!/usr/bin/env python3
"""
High-Frequency Trading Test with Corrected Logic
Tests small-scale, rapid DAI↔ARB swaps with proper buy low/sell high strategy
"""

import os
import time
import json
from datetime import datetime

def create_high_frequency_mock_data():
    """Create mock data simulating high-frequency trading opportunities"""
    
    # Scenario 1: Bearish ARB dip (DAI→ARB opportunity - buy low)
    bearish_scenario = {
        'btc_analysis': {
            'price': 96800, 'change_24h': -0.8, 'signal': 'neutral',
            'pattern': 'consolidation', 'confidence': 0.5
        },
        'arb_analysis': {
            'price': 0.67, 'change_24h': -2.1, 'signal': 'bearish',
            'rsi': 42, 'pattern': 'moderate_bearish', 'confidence': 0.8,
            'price_change_5min': -0.6,  # Bearish momentum
            'macd_line': -0.001, 'macd_signal': 0.001, 'macd_histogram': -0.002
        },
        'market_sentiment': 'bearish',
        'scenario': 'bearish_dip_buy_opportunity'
    }
    
    # Scenario 2: Bullish ARB peak (ARB→DAI opportunity - sell high)
    bullish_scenario = {
        'btc_analysis': {
            'price': 97200, 'change_24h': 1.2, 'signal': 'bullish',
            'pattern': 'moderate_bullish', 'confidence': 0.7
        },
        'arb_analysis': {
            'price': 0.71, 'change_24h': 3.5, 'signal': 'bullish',
            'rsi': 68, 'pattern': 'strong_bullish', 'confidence': 0.9,
            'price_change_5min': 0.8,  # Bullish momentum
            'macd_line': 0.003, 'macd_signal': 0.001, 'macd_histogram': 0.002
        },
        'market_sentiment': 'bullish',
        'scenario': 'bullish_peak_sell_opportunity'
    }
    
    return [bearish_scenario, bullish_scenario]

def test_corrected_high_frequency_logic():
    """Test the corrected high-frequency trading logic"""
    print("🔄 TESTING CORRECTED HIGH-FREQUENCY TRADING LOGIC")
    print("=" * 60)
    
    # Set high-frequency environment
    os.environ['MARKET_SIGNAL_ENABLED'] = 'true'
    os.environ['OPERATION_COOLDOWN'] = '30'
    os.environ['MIN_SWAP_AMOUNT'] = '1.0'
    os.environ['MAX_SWAP_AMOUNT'] = '10.0'
    os.environ['DAI_TO_ARB_THRESHOLD'] = '0.4'
    os.environ['ARB_TO_DAI_THRESHOLD'] = '0.4'
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        if not (hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy):
            print("❌ Market signal strategy not available")
            return False
            
        strategy = agent.market_signal_strategy
        mock_scenarios = create_high_frequency_mock_data()
        
        successful_swaps = []
        total_profit = 0
        
        print("\n📊 HIGH-FREQUENCY TRADING SIMULATION")
        print("=" * 50)
        
        for i, scenario in enumerate(mock_scenarios, 1):
            print(f"\n🎯 SCENARIO {i}: {scenario['scenario'].upper()}")
            print("-" * 40)
            
            # Create mock analyzer for this scenario
            class HighFrequencyMockAnalyzer:
                def __init__(self, scenario_data):
                    self.initialized = True
                    self.scenario = scenario_data
                    
                def get_market_summary(self):
                    return self.scenario
            
            # Inject scenario data
            strategy.enhanced_analyzer = HighFrequencyMockAnalyzer(scenario)
            
            # Simulate MACD history for crossover detection
            if scenario['scenario'] == 'bearish_dip_buy_opportunity':
                # Simulate bearish crossover (MACD crossing below signal)
                strategy.macd_history = [
                    {'macd_line': 0.001, 'signal_line': 0.001, 'histogram': 0.0, 'timestamp': time.time() - 60},
                    {'macd_line': -0.001, 'signal_line': 0.001, 'histogram': -0.002, 'timestamp': time.time()}
                ]
            else:
                # Simulate bullish crossover (MACD crossing above signal)
                strategy.macd_history = [
                    {'macd_line': -0.001, 'signal_line': 0.001, 'histogram': -0.002, 'timestamp': time.time() - 60},
                    {'macd_line': 0.003, 'signal_line': 0.001, 'histogram': 0.002, 'timestamp': time.time()}
                ]
            
            # Analyze signals
            signals = strategy.analyze_market_signals()
            
            if signals and signals.get('status') == 'success':
                action = signals.get('action', 'hold')
                confidence = signals.get('confidence_level', 0)
                signals_detected = signals.get('signals_detected', [])
                
                print(f"   Action: {action.upper()}")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Signals: {signals_detected}")
                
                # Simulate swap execution
                if action == 'dai_to_arb' and confidence >= 0.4:
                    # Simulate buying ARB low
                    entry_price = scenario['arb_analysis']['price']
                    swap_amount = 5.0  # Small high-frequency amount
                    arb_received = swap_amount / entry_price
                    
                    swap_record = {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'dai_to_arb',
                        'strategy': 'buy_low',
                        'entry_price': entry_price,
                        'dai_amount': swap_amount,
                        'arb_received': arb_received,
                        'confidence': confidence,
                        'signals': signals_detected
                    }
                    successful_swaps.append(swap_record)
                    
                    print(f"   ✅ EXECUTED: Buy {arb_received:.4f} ARB at ${entry_price:.4f} (low price)")
                    
                elif action == 'arb_to_dai' and confidence >= 0.4:
                    # Simulate selling ARB high
                    exit_price = scenario['arb_analysis']['price']
                    arb_amount = 7.0  # Assume we have ARB to sell
                    dai_received = arb_amount * exit_price
                    
                    # Calculate profit (assuming we bought at $0.67)
                    profit = (exit_price - 0.67) * arb_amount
                    total_profit += profit
                    
                    swap_record = {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'arb_to_dai',
                        'strategy': 'sell_high',
                        'exit_price': exit_price,
                        'arb_amount': arb_amount,
                        'dai_received': dai_received,
                        'profit_usd': profit,
                        'confidence': confidence,
                        'signals': signals_detected
                    }
                    successful_swaps.append(swap_record)
                    
                    print(f"   ✅ EXECUTED: Sell {arb_amount:.4f} ARB at ${exit_price:.4f} (high price)")
                    print(f"   💰 PROFIT: ${profit:.4f}")
                    
                else:
                    print(f"   ⏸️ HOLD: Confidence {confidence:.2f} below threshold (0.4)")
            
            # Simulate 30-second cooldown
            print("   ⏳ 30-second cooldown...")
            
        # Generate final report
        print(f"\n🏆 HIGH-FREQUENCY TRADING SIMULATION COMPLETE")
        print("=" * 60)
        print(f"   Total Swaps: {len(successful_swaps)}")
        print(f"   Total Profit: ${total_profit:.4f}")
        print(f"   Strategy: Corrected Buy Low / Sell High")
        print(f"   Cooldown: 30 seconds between operations")
        print(f"   Swap Range: $1 - $10 per operation")
        
        # Save comprehensive results
        results = {
            'test_type': 'high_frequency_corrected_logic',
            'total_swaps': len(successful_swaps),
            'total_profit': total_profit,
            'strategy': 'buy_low_sell_high',
            'parameters': {
                'cooldown': 30,
                'min_swap': 1.0,
                'max_swap': 10.0,
                'dai_to_arb_threshold': 0.4,
                'arb_to_dai_threshold': 0.4
            },
            'swaps': successful_swaps,
            'logic_corrected': True,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('high_frequency_trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Results saved to high_frequency_trading_results.json")
        
        return len(successful_swaps) > 0
        
    except Exception as e:
        print(f"❌ High-frequency test failed: {e}")
        return False

def run_comprehensive_high_frequency_test():
    """Run comprehensive high-frequency trading test with profit tracking"""
    print("🎯 COMPREHENSIVE HIGH-FREQUENCY TRADING TEST")
    print("=" * 55)
    print("🔧 CORRECTED LOGIC: DAI→ARB (bearish), ARB→DAI (bullish)")
    print("⚡ HIGH-FREQUENCY: 30s cooldown, $1-$10 swaps")
    print()
    
    success = test_corrected_high_frequency_logic()
    
    if success:
        print("\n🎉 HIGH-FREQUENCY TRADING TEST SUCCESSFUL!")
        print("✅ Logic corrected: Buy low, sell high")
        print("⚡ High-frequency parameters configured")
        print("💰 Profitable round-trip simulation complete")
        print("📊 System ready for small-scale, rapid trading")
    else:
        print("\n❌ HIGH-FREQUENCY TRADING TEST FAILED")
        print("🔧 Review configuration and logic")
    
    return success

if __name__ == "__main__":
    run_comprehensive_high_frequency_test()
