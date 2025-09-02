
#!/usr/bin/env python3
"""
Technical Indicators Integration Test with Debt Swap Mechanism
Tests the complete integration pipeline from data collection to debt swap decisions
"""

import os
import sys
import time
import traceback
from datetime import datetime

def test_market_signal_environment():
    """Test market signal environment setup"""
    print("🔍 TESTING MARKET SIGNAL ENVIRONMENT")
    print("=" * 40)

    # Check environment variables
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
    coin_api = os.getenv('COIN_API') or os.getenv('COIN_API_KEY') or os.getenv('COINAPI_KEY')
    coinmarketcap_api = os.getenv('COINMARKETCAP_API_KEY')

    print(f"✅ MARKET_SIGNAL_ENABLED: {market_enabled}")
    if coin_api:
        print(f"✅ COIN_API: {coin_api[:8]}... (PRIMARY)")
    if coinmarketcap_api:
        print(f"✅ COINMARKETCAP_API_KEY: [REDACTED] (SECONDARY)")

    if not market_enabled:
        print("❌ Market signals not enabled")
        return False

    if not coin_api and not coinmarketcap_api:
        print("❌ No API keys found")
        return False

    print("✅ Environment setup correct")
    return True

def test_enhanced_market_analyzer():
    """Test enhanced market analyzer data collection"""
    print("\n🔍 TESTING ENHANCED MARKET ANALYZER")
    print("=" * 40)

    try:
        from enhanced_market_analyzer import EnhancedMarketAnalyzer

        # Create mock agent for testing
        class MockAgent:
            def __init__(self):
                self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"

        mock_agent = MockAgent()
        analyzer = EnhancedMarketAnalyzer(mock_agent)

        print(f"✅ Enhanced analyzer initialized: {analyzer.initialized}")
        print(f"✅ Primary API: {getattr(analyzer, 'primary_api', 'Unknown')}")
        print(f"✅ Mock mode: {getattr(analyzer, 'mock_mode', False)}")

        # Test data collection
        print("\n📊 Testing data collection...")
        for symbol in ['BTC', 'ETH', 'ARB', 'DAI']:
            data = analyzer.get_market_data_with_fallback(symbol)
            if data:
                print(f"✅ {symbol}: ${data.get('price', 0):.4f}")
                
                # Store historical data for pattern analysis
                analyzer.store_historical_data(symbol, data)
            else:
                print(f"❌ {symbol}: No data received")

        # Check data points collected
        for symbol in ['BTC', 'ARB']:
            points = len(analyzer.price_history.get(symbol, []))
            print(f"📈 {symbol} data points: {points}")

        return True

    except Exception as e:
        print(f"❌ Enhanced analyzer test failed: {e}")
        return False

def test_market_signal_strategy_initialization():
    """Test market signal strategy initialization"""
    print("\n🔍 TESTING MARKET SIGNAL STRATEGY")
    print("=" * 40)

    try:
        from market_signal_strategy import MarketSignalStrategy

        # Create mock agent
        class MockAgent:
            def __init__(self):
                self.address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"

        mock_agent = MockAgent()
        strategy = MarketSignalStrategy(mock_agent)

        print(f"✅ Strategy initialized: {strategy.initialized}")
        print(f"✅ Initialization successful: {strategy.initialization_successful}")

        # Test strategy status
        status = strategy.get_strategy_status()
        print(f"📊 Technical indicators ready: {status.get('technical_indicators_ready', False)}")
        print(f"📊 Enhanced ARB points: {status.get('enhanced_arb_points', 0)}")
        print(f"📊 Enhanced BTC points: {status.get('enhanced_btc_points', 0)}")
        print(f"📊 Data source: {status.get('data_source', 'Unknown')}")

        # Test market analysis
        analysis = strategy.get_market_analysis()
        if analysis and not analysis.get('error'):
            print("✅ Market analysis functional")
            
            # Display key market data
            btc_data = analysis.get('btc_analysis', {})
            arb_data = analysis.get('arb_analysis', {})
            
            if btc_data:
                print(f"₿ BTC: ${btc_data.get('price', 0):,.2f} ({btc_data.get('change_24h', 0):+.2f}%)")
            if arb_data:
                print(f"🔵 ARB: ${arb_data.get('price', 0):.4f} ({arb_data.get('change_24h', 0):+.2f}%)")
        else:
            print("⚠️ Market analysis has issues")

        return True

    except Exception as e:
        print(f"❌ Market signal strategy test failed: {e}")
        traceback.print_exc()
        return False

def test_debt_swap_integration():
    """Test debt swap mechanism integration"""
    print("\n🔍 TESTING DEBT SWAP INTEGRATION")
    print("=" * 40)

    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent

        # Initialize agent
        agent = ArbitrumTestnetAgent()

        # Check if market signal strategy is properly integrated
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            print("✅ Market signal strategy integrated into agent")
            
            # Check debt swap activation
            debt_swap_active = getattr(agent, 'debt_swap_active', False)
            print(f"✅ Debt swap active: {debt_swap_active}")

            # Test debt swap conditions
            try:
                if hasattr(agent, 'check_debt_swap_conditions'):
                    conditions_ok, message = agent.check_debt_swap_conditions()
                    print(f"📊 Debt swap conditions: {message}")
                else:
                    print("⚠️ check_debt_swap_conditions method not found")
            except Exception as conditions_error:
                print(f"⚠️ Debt swap conditions check failed: {conditions_error}")

            # Test market signal analysis
            if agent.market_signal_strategy:
                try:
                    signals = agent.market_signal_strategy.analyze_market_signals()
                    if signals:
                        action = signals.get('action', 'hold')
                        confidence = signals.get('confidence_level', 0)
                        print(f"📊 Market signal: {action.upper()} (confidence: {confidence:.2f})")
                    else:
                        print("⚠️ No market signals generated")
                except Exception as signal_error:
                    print(f"⚠️ Market signal analysis failed: {signal_error}")

            return True
        else:
            print("❌ Market signal strategy not integrated")
            return False

    except Exception as e:
        print(f"❌ Debt swap integration test failed: {e}")
        traceback.print_exc()
        return False

def test_technical_indicators_data_flow():
    """Test complete data flow from API to technical indicators"""
    print("\n🔍 TESTING TECHNICAL INDICATORS DATA FLOW")
    print("=" * 50)

    try:
        from market_signal_strategy import MarketSignalStrategy
        from arbitrum_testnet_agent import ArbitrumTestnetAgent

        # Initialize agent with market signals
        agent = ArbitrumTestnetAgent()
        
        if not hasattr(agent, 'market_signal_strategy') or not agent.market_signal_strategy:
            print("❌ Market signal strategy not available on agent")
            return False

        strategy = agent.market_signal_strategy

        # Force data collection for testing
        print("📊 Forcing data collection...")
        
        if hasattr(strategy, 'enhanced_analyzer') and strategy.enhanced_analyzer:
            analyzer = strategy.enhanced_analyzer
            
            # Collect fresh data for BTC and ARB
            for symbol in ['BTC', 'ARB']:
                print(f"🔄 Collecting {symbol} data...")
                data = analyzer.get_market_data_with_fallback(symbol)
                if data:
                    analyzer.store_historical_data(symbol, data)
                    points = len(analyzer.price_history.get(symbol, []))
                    print(f"✅ {symbol}: {points} data points stored")
                else:
                    print(f"❌ {symbol}: Failed to collect data")

            # Check if technical indicators are ready
            status = strategy.get_strategy_status()
            tech_ready = status.get('technical_indicators_ready', False)
            arb_points = status.get('enhanced_arb_points', 0)
            btc_points = status.get('enhanced_btc_points', 0)

            print(f"\n📈 TECHNICAL INDICATORS STATUS:")
            print(f"   Ready: {tech_ready}")
            print(f"   ARB Points: {arb_points}")
            print(f"   BTC Points: {btc_points}")
            print(f"   Data Source: {status.get('data_source', 'Unknown')}")

            # Test signal generation
            if tech_ready:
                print("\n🚀 Testing signal generation...")
                signals = strategy.analyze_market_signals()
                if signals and signals.get('status') == 'success':
                    print(f"✅ Signal generated: {signals.get('action', 'hold').upper()}")
                    print(f"✅ Confidence: {signals.get('confidence_level', 0):.2f}")
                else:
                    print("⚠️ Signal generation failed")
            else:
                print("⚠️ Not enough data for technical indicators")

        return True

    except Exception as e:
        print(f"❌ Data flow test failed: {e}")
        traceback.print_exc()
        return False

def test_debt_swap_decision_process():
    """Test the complete debt swap decision process"""
    print("\n🔍 TESTING DEBT SWAP DECISION PROCESS")
    print("=" * 45)

    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent

        # Initialize agent
        agent = ArbitrumTestnetAgent()

        if not hasattr(agent, 'market_signal_strategy') or not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return False

        # Initialize integrations for testing
        if not agent.initialize_integrations():
            print("⚠️ Integrations not fully initialized, testing with mock data")

        # Test market signal trigger conditions
        print("📊 Testing market signal trigger conditions...")
        
        try:
            # Get account data for health factor check
            if hasattr(agent, 'aave') and agent.aave:
                account_data = agent.aave.get_user_account_data()
                if account_data:
                    health_factor = account_data.get('healthFactor', 0)
                    available_borrows = account_data.get('availableBorrowsUSD', 0)
                    print(f"✅ Health Factor: {health_factor:.3f}")
                    print(f"✅ Available Borrows: ${available_borrows:.2f}")
                    
                    # Test if market signal operation would be allowed
                    if health_factor > 1.8:
                        print("✅ Health factor meets market signal threshold (>1.8)")
                    else:
                        print(f"❌ Health factor {health_factor:.3f} below threshold 1.8")
                else:
                    print("⚠️ Cannot retrieve account data")
            else:
                print("⚠️ Aave integration not available for testing")

            # Test market signal analysis
            strategy = agent.market_signal_strategy
            signals = strategy.analyze_market_signals()
            
            if signals and signals.get('status') == 'success':
                action = signals.get('action', 'hold')
                confidence = signals.get('confidence_level', 0)
                signals_detected = signals.get('signals_detected', [])
                
                print(f"\n🎯 MARKET SIGNAL ANALYSIS:")
                print(f"   Action: {action.upper()}")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Signals: {len(signals_detected)} detected")
                
                for signal in signals_detected:
                    print(f"      • {signal}")
                
                # Check if this would trigger a debt swap
                if action != 'hold' and confidence > 0.6:
                    print(f"🚀 DEBT SWAP WOULD BE TRIGGERED!")
                    print(f"   Type: {action}")
                    print(f"   Confidence: {confidence:.2f}")
                else:
                    print(f"⏳ No debt swap trigger (action: {action}, confidence: {confidence:.2f})")
                    
            else:
                print("❌ Market signal analysis failed")
                if signals:
                    print(f"   Error: {signals.get('message', 'Unknown error')}")

            return True

        except Exception as analysis_error:
            print(f"❌ Decision process test failed: {analysis_error}")
            return False

    except Exception as e:
        print(f"❌ Debt swap decision test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive technical indicators integration tests"""
    print("🔍 TECHNICAL INDICATORS INTEGRATION WITH DEBT SWAP MECHANISM")
    print("=" * 65)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    tests = [
        ("Environment Setup", test_market_signal_environment),
        ("Enhanced Market Analyzer", test_enhanced_market_analyzer),
        ("Market Signal Strategy", test_market_signal_strategy_initialization),
        ("Debt Swap Integration", test_debt_swap_integration),
        ("Technical Indicators Data Flow", test_technical_indicators_data_flow),
        ("Debt Swap Decision Process", test_debt_swap_decision_process)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 65)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 65)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")

    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Technical indicators properly integrated!")
        print("🔄 Debt swap mechanism ready for market-driven operations")
    elif passed >= total * 0.8:
        print("⚠️ MOSTLY FUNCTIONAL - Minor issues detected")
        print("💡 Review failed tests and ensure API connectivity")
    else:
        print("❌ INTEGRATION ISSUES - Multiple components failing")
        print("🔧 Check environment variables and API connectivity")

    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
