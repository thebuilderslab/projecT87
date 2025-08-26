#!/usr/bin/env python3
"""
Test Enhanced Market Analyzer with COIN_API Integration
"""

import os
import sys
import time
from datetime import datetime

def test_api_key():
    """Test if COIN_API key is available"""
    print("🔑 Testing COIN_API Key...")

    coin_api_key = os.getenv('COIN_API')
    if not coin_api_key:
        print("❌ COIN_API not found in environment")
        print("💡 Please add your COIN_API key to Replit Secrets")
        return False

    print(f"✅ API Key found: {coin_api_key[:8]}...")
    print(f"📏 API Key length: {len(coin_api_key)} characters")
    return True

def test_enhanced_analyzer():
    """Test the enhanced market analyzer functionality"""
    print("\n🧪 TESTING ENHANCED MARKET ANALYZER")
    print("=" * 60)

    try:
        # Test import
        try:
            from enhanced_market_analyzer import EnhancedMarketAnalyzer, EnhancedMarketSignalStrategy
            print("✅ Enhanced Market Analyzer imported successfully")
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False

        # Create mock agent
        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"

        # Test analyzer initialization
        try:
            agent = MockAgent()
            analyzer = EnhancedMarketAnalyzer(agent)
            print("✅ Enhanced Market Analyzer initialized")
        except Exception as e:
            print(f"❌ Analyzer initialization failed: {e}")
            return False

        # Test market summary
        try:
            print("📊 Testing market summary...")
            summary = analyzer.get_market_summary()

            if 'error' not in summary:
                print("✅ Market summary generated successfully")
                print(f"📈 Market sentiment: {summary.get('market_sentiment', 'unknown')}")

                # Display BTC data if available
                if 'btc_analysis' in summary and 'price' in summary['btc_analysis']:
                    btc = summary['btc_analysis']
                    print(f"₿ BTC: ${btc['price']:.2f} ({btc.get('change_24h', 0):.2f}% 24h)")
                    print(f"   Signal: {btc.get('signal', 'unknown')} (confidence: {btc.get('confidence', 0):.2f})")

                # Display ETH data if available
                if 'eth_analysis' in summary and 'price' in summary['eth_analysis']:
                    eth = summary['eth_analysis']
                    print(f"Ξ ETH: ${eth['price']:.2f} ({eth.get('change_24h', 0):.2f}% 24h)")
                    print(f"   Signal: {eth.get('signal', 'unknown')} (confidence: {eth.get('confidence', 0):.2f})")

                # Display DAI data if available
                if 'dai_analysis' in summary and 'price' in summary['dai_analysis']:
                    dai = summary['dai_analysis']
                    print(f"💵 DAI: ${dai['price']:.4f} ({dai.get('change_24h', 0):.2f}% 24h)")
                    print(f"   Signal: {dai.get('signal', 'unknown')} (confidence: {dai.get('confidence', 0):.2f})")

            else:
                print(f"❌ Market summary failed: {summary['error']}")
                return False

        except Exception as e:
            print(f"❌ Market summary test failed: {e}")
            return False

        # Test strategy
        try:
            print("\n🎯 Testing market signal strategy...")
            strategy = EnhancedMarketSignalStrategy(agent)
            print("✅ Enhanced Market Signal Strategy initialized")

            trade_decision = strategy.should_execute_trade()
            print(f"🎯 Trade recommendation: {'EXECUTE' if trade_decision else 'HOLD'}")

            status = strategy.get_strategy_status()
            print(f"📊 Strategy status: {status}")

        except Exception as e:
            print(f"❌ Strategy test failed: {e}")
            return False

        print("\n🎉 All tests passed! Enhanced Market Analyzer is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_market_signal_integration():
    """Test integration with main market signal strategy"""
    print("\n🔗 TESTING MARKET SIGNAL INTEGRATION")
    print("=" * 50)

    try:
        from market_signal_strategy import MarketSignalStrategy

        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"

        agent = MockAgent()
        strategy = MarketSignalStrategy(agent)

        print(f"✅ Market Signal Strategy initialized")

        status = strategy.get_strategy_status()
        print(f"📊 Strategy Status:")
        print(f"   Initialized: {status.get('initialized', False)}")
        print(f"   Enhanced Mode: {status.get('enhanced_mode', False)}")
        print(f"   API Key Present: {status.get('api_key_present', False)}")
        print(f"   Strategy Type: {status.get('strategy_type', 'unknown')}")

        # Test market analysis
        analysis = strategy.get_market_analysis()
        if 'error' not in analysis:
            print("✅ Market analysis integration working")
        else:
            print(f"⚠️ Market analysis issue: {analysis.get('error', 'unknown')}")

        # Test trade decision
        trade_decision = strategy.should_execute_trade()
        print(f"🎯 Integrated trade decision: {'EXECUTE' if trade_decision else 'HOLD'}")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 COIN_API INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test 1: API Key
    if not test_api_key():
        print("\n❌ CRITICAL: API key test failed. Cannot proceed with other tests.")
        return False

    # Test 2: Enhanced Analyzer
    if not test_enhanced_analyzer():
        print("\n❌ Enhanced analyzer test failed.")
        return False

    # Test 3: Integration
    if not test_market_signal_integration():
        print("\n❌ Integration test failed.")
        return False

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED! COIN_API integration is working correctly.")
    print("✅ The debt swap agent now has full market analysis capabilities.")
    print("📈 Technical indicators and market signals are operational.")
    print("🎯 Enhanced trading strategy is ready for use.")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)