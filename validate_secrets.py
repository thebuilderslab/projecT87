
#!/usr/bin/env python3
"""
Comprehensive Secrets Validation Script
Validates all environment variables and provides detailed diagnostics
"""

import os
import sys

def validate_all_secrets():
    """Validate all secrets configuration"""
    print("🔍 COMPREHENSIVE SECRETS VALIDATION")
    print("=" * 50)
    
    # Check market signal secrets
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED')
    print(f"MARKET_SIGNAL_ENABLED: {market_enabled}")
    
    # Check all possible CoinAPI key variations
    coin_api_variations = [
        'COIN_API_KEY', 'COINAPI_KEY', 'COIN_API', 'COINAPI'
    ]
    
    print(f"\nCoinAPI Key Variations:")
    coinapi_found = False
    for var in coin_api_variations:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: FOUND (length: {len(value)})")
            coinapi_found = True
        else:
            print(f"❌ {var}: NOT_SET")
    
    # Check CoinMarketCap
    cmc_key = os.getenv('COINMARKETCAP_API_KEY')
    print(f"\nCOINMARKETCAP_API_KEY: {'✅ FOUND' if cmc_key else '❌ NOT_SET'}")
    if cmc_key:
        print(f"   Length: {len(cmc_key)} characters")
    
    # Check wallet keys
    private_key = os.getenv('PRIVATE_KEY')
    private_key2 = os.getenv('PRIVATE_KEY2')
    wallet_private_key = os.getenv('WALLET_PRIVATE_KEY')
    
    print(f"\nWallet Keys:")
    print(f"PRIVATE_KEY: {'✅ FOUND' if private_key else '❌ NOT_SET'}")
    print(f"PRIVATE_KEY2: {'✅ FOUND' if private_key2 else '❌ NOT_SET'}")
    print(f"WALLET_PRIVATE_KEY: {'✅ FOUND' if wallet_private_key else '❌ NOT_SET'}")
    
    # Check other important secrets
    other_secrets = [
        'NETWORK_MODE', 'ALCHEMY_RPC_URL', 'ARBITRUM_RPC_URL'
    ]
    
    print(f"\nOther Configuration:")
    for secret in other_secrets:
        value = os.getenv(secret)
        print(f"{secret}: {value if value else 'NOT_SET'}")
    
    # Show all environment variables containing key market terms
    print(f"\nAll Market-Related Environment Variables:")
    all_env = dict(os.environ)
    market_terms = ['COIN', 'MARKET', 'API', 'SIGNAL']
    
    for key, value in all_env.items():
        if any(term in key.upper() for term in market_terms):
            display_value = '[REDACTED]' if 'KEY' in key else value
            print(f"   {key}: {display_value}")
    
    # Test market signal strategy initialization
    print(f"\n🧪 TESTING MARKET SIGNAL INITIALIZATION:")
    try:
        from market_signal_strategy import MarketSignalStrategy
        
        # Create mock agent for testing
        class MockAgent:
            def __init__(self):
                self.address = "0x1234567890123456789012345678901234567890"
        
        mock_agent = MockAgent()
        strategy = MarketSignalStrategy(mock_agent)
        
        print(f"Strategy initialized: {getattr(strategy, 'initialized', False)}")
        print(f"Initialization successful: {getattr(strategy, 'initialization_successful', False)}")
        
        if hasattr(strategy, 'enhanced_analyzer'):
            analyzer = strategy.enhanced_analyzer
            print(f"Enhanced analyzer available: {analyzer is not None}")
            if analyzer:
                print(f"Analyzer initialized: {getattr(analyzer, 'initialized', False)}")
                print(f"Mock mode: {getattr(analyzer, 'mock_mode', False)}")
                print(f"Primary API: {getattr(analyzer, 'primary_api', 'None')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_all_secrets()
    if success:
        print(f"\n✅ Secrets validation completed")
    else:
        print(f"\n❌ Secrets validation failed")
        sys.exit(1)
