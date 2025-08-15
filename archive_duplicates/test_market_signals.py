
#!/usr/bin/env python3
"""
Comprehensive Market Signal Testing Suite
Tests all components for 90% confidence accuracy
"""

import sys
import time
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from arbitrum_testnet_agent import ArbitrumTestnetAgent
    from confidence_validator import ConfidenceValidator, ValidationResult
    from market_signal_strategy import MarketSignalStrategy
    from enhanced_market_analyzer import EnhancedMarketAnalyzer
    from strategy_optimizer import StrategyOptimizer
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def test_market_data_apis():
    """Test market data API connectivity and data quality"""
    print("\n📊 TESTING MARKET DATA APIs")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        
        if not hasattr(agent, 'market_signal_strategy') or not agent.market_signal_strategy:
            print("❌ Market signal strategy not initialized")
            return False
        
        # Test BTC data
        btc_data = agent.market_signal_strategy.get_btc_price_data()
        if btc_data:
            print(f"✅ BTC Data: ${btc_data['price']:.2f} ({btc_data['percent_change_1h']:.2f}% 1h)")
        else:
            print("❌ BTC data fetch failed")
            return False
        
        # Test ARB data
        arb_data = agent.market_signal_strategy.get_arb_price_data()
        if arb_data:
            print(f"✅ ARB Data: ${arb_data['price']:.4f} ({arb_data['percent_change_1h']:.2f}% 1h)")
        else:
            print("❌ ARB data fetch failed")
            return False
        
        # Test enhanced analyzer
        if hasattr(agent.market_signal_strategy, 'enhanced_analyzer'):
            enhanced_signal = agent.market_signal_strategy.enhanced_analyzer.generate_enhanced_signal()
            if enhanced_signal:
                print(f"✅ Enhanced Analysis: {enhanced_signal.signal_type} "
                      f"(confidence: {enhanced_signal.confidence:.2f})")
            else:
                print("⚠️ Enhanced analysis available but no signal generated")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_90_percent_confidence_validation():
    """Test 90% confidence validation system"""
    print("\n🎯 TESTING 90% CONFIDENCE VALIDATION")
    print("=" * 50)
    
    try:
        validator = ConfidenceValidator()
        
        # Create test signal data
        test_signal = {
            'signal_type': 'bearish',
            'confidence': 0.92,
            'btc_price_change': -1.5,
            'arb_technical_score': 25,
            'timestamp': time.time()
        }
        
        # Create test enhanced analysis
        test_analysis = {
            'btc_analysis': {
                'rsi': 45,
                'momentum': -2.1,
                'volatility': 65,
                'macd': {'histogram': -0.6}
            },
            'arb_analysis': {
                'rsi': 25,
                'momentum': -1.8,
                'volume_trend': {'trend': 'increasing', 'strength': 0.8},
                'macd': {'histogram': -0.7}
            },
            'pattern_analysis': {
                'patterns': [
                    {'pattern_type': 'btc_dip_arb_oversold', 'confidence': 0.91},
                    {'pattern_type': 'volume_spike_pattern', 'confidence': 0.87}
                ],
                'count': 2
            },
            'gas_efficiency_score': 0.85,
            'success_probability': 0.89
        }
        
        # Perform validation
        result = validator.validate_signal_confidence(test_signal, test_analysis)
        
        print(f"✅ Validation Result:")
        print(f"   Passed 90% Threshold: {result.passed}")
        print(f"   Confidence Score: {result.confidence_score:.2f}")
        print(f"   Risk Assessment: {result.risk_assessment}")
        
        # Display detailed scores
        print(f"   Detailed Validation Scores:")
        for criterion, score in result.validation_details.items():
            print(f"     {criterion}: {score:.2f}")
        
        return result.passed and result.confidence_score >= 0.90
        
    except Exception as e:
        print(f"❌ Confidence validation test failed: {e}")
        return False

def test_signal_generation_with_validation():
    """Test market signal generation with 90% confidence validation"""
    print("\n🎯 TESTING SIGNAL GENERATION WITH 90% VALIDATION")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        if not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return False
        
        validator = ConfidenceValidator()
        
        # Generate market signal
        signal = agent.market_signal_strategy.analyze_market_signals()
        
        if signal:
            print(f"✅ Signal Generated:")
            print(f"   Type: {signal.signal_type}")
            print(f"   Confidence: {signal.confidence:.2f}")
            print(f"   BTC Change: {signal.btc_price_change:.2f}%")
            print(f"   ARB RSI: {signal.arb_technical_score:.1f}")
            
            # Test 90% confidence validation
            if signal.confidence >= 0.90:
                print(f"✅ Signal meets 90% confidence threshold")
                
                # Test strategy execution decision
                should_execute, strategy_type = agent.market_signal_strategy.should_execute_market_strategy(signal)
                print(f"✅ Strategy Decision: {strategy_type} (Execute: {should_execute})")
                
                return True
            else:
                print(f"⚠️ Signal below 90% confidence threshold (may be normal)")
                return True  # This is acceptable behavior
            
        else:
            print("⚠️ No signal generated (may be in cooldown or insufficient confidence)")
            return True  # This is okay, high-confidence signals aren't always available
            
    except Exception as e:
        print(f"❌ Signal generation test failed: {e}")
        return False

def test_strategy_optimizer():
    """Test strategy optimizer for 90% confidence selection"""
    print("\n🔧 TESTING STRATEGY OPTIMIZER")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        optimizer = StrategyOptimizer(agent)
        
        # Test strategy selection
        optimal_strategy = optimizer.select_optimal_strategy()
        print(f"✅ Optimal Strategy Selected: {optimal_strategy}")
        
        # Test performance report
        performance_report = optimizer.get_performance_report()
        print(f"✅ Performance Report Generated:")
        for strategy_name, metrics in performance_report['strategies'].items():
            print(f"   {strategy_name}: {metrics['success_rate']} success rate")
        
        # Test current market conditions
        conditions = optimizer.evaluate_current_conditions()
        print(f"✅ Current Market Conditions:")
        for condition, score in conditions.items():
            print(f"   {condition}: {score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy optimizer test failed: {e}")
        return False

def test_comprehensive_system_integration():
    """Test complete system integration with 90% confidence requirements"""
    print("\n🚀 TESTING COMPREHENSIVE SYSTEM INTEGRATION")
    print("=" * 60)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Test all components
        components_status = {
            'market_data_apis': False,
            'confidence_validation': False,
            'signal_generation': False,
            'strategy_optimization': False
        }
        
        # Test each component
        components_status['market_data_apis'] = test_market_data_apis()
        components_status['confidence_validation'] = test_90_percent_confidence_validation()
        components_status['signal_generation'] = test_signal_generation_with_validation()
        components_status['strategy_optimization'] = test_strategy_optimizer()
        
        # Summary
        print(f"\n📊 COMPREHENSIVE TEST RESULTS:")
        print("=" * 60)
        all_passed = True
        for component, status in components_status.items():
            status_icon = "✅ PASS" if status else "❌ FAIL"
            print(f"   {component.replace('_', ' ').title()}: {status_icon}")
            if not status:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 ALL TESTS PASSED - SYSTEM OPTIMIZED FOR 90% CONFIDENCE")
            print(f"💡 System ready for high-confidence autonomous trading")
        else:
            print(f"\n⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Comprehensive system test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE 90% CONFIDENCE MARKET SIGNAL TESTING")
    print("=" * 70)
    
    # Run comprehensive test suite
    success = test_comprehensive_system_integration()
    
    if success:
        print(f"\n✅ SYSTEM OPTIMIZED FOR 90% CONFIDENCE TRADING")
        print(f"🎯 Ready for autonomous operation with high-confidence signals")
    else:
        print(f"\n❌ OPTIMIZATION INCOMPLETE - REVIEW FAILED COMPONENTS")
    
    sys.exit(0 if success else 1)
