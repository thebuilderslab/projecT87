
#!/usr/bin/env python3
"""
Market Signal Environment Verification Script
Checks if MARKET_SIGNAL_ENABLED and COINMARKETCAP_API_KEY are properly configured
"""

import os
import sys

def verify_market_signal_config():
    """Verify market signal environment variables are properly set"""
    print("🔍 VERIFYING MARKET SIGNAL CONFIGURATION")
    print("=" * 50)
    
    # Check MARKET_SIGNAL_ENABLED
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED')
    print(f"\n📊 MARKET_SIGNAL_ENABLED:")
    if market_enabled is None:
        print(f"   ❌ NOT SET - Add to Replit Secrets")
        print(f"   💡 Required value: true")
        return False
    elif market_enabled.lower() == 'true':
        print(f"   ✅ CORRECTLY SET: {market_enabled}")
    else:
        print(f"   ⚠️  SET BUT INCORRECT: {market_enabled}")
        print(f"   💡 Should be: true")
        return False
    
    # Check COINMARKETCAP_API_KEY
    api_key = os.getenv('COINMARKETCAP_API_KEY')
    print(f"\n🔑 COINMARKETCAP_API_KEY:")
    if api_key is None:
        print(f"   ❌ NOT SET - Add to Replit Secrets")
        print(f"   💡 Get free API key from: https://coinmarketcap.com/api/")
        return False
    elif len(api_key) < 10:
        print(f"   ⚠️  SET BUT TOO SHORT: {len(api_key)} characters")
        print(f"   💡 API keys are typically 32+ characters")
        return False
    else:
        print(f"   ✅ CORRECTLY SET: {api_key[:8]}...{api_key[-4:]} ({len(api_key)} chars)")
    
    # Test API connectivity if possible
    print(f"\n🌐 API CONNECTIVITY TEST:")
    try:
        import requests
        headers = {
            'X-CMC_PRO_API_KEY': api_key,
            'Accept': 'application/json'
        }
        
        # Test with a simple API call
        response = requests.get(
            'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
            headers=headers,
            params={'symbol': 'BTC'},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ API KEY VALID - Connection successful")
            data = response.json()
            btc_price = data['data']['BTC']['quote']['USD']['price']
            print(f"   💰 BTC Price: ${btc_price:,.2f}")
        elif response.status_code == 401:
            print(f"   ❌ API KEY INVALID - Authentication failed")
            return False
        elif response.status_code == 429:
            print(f"   ⚠️  API RATE LIMITED - Key valid but quota exceeded")
        else:
            print(f"   ⚠️  API ERROR - Status: {response.status_code}")
            
    except ImportError:
        print(f"   ⚠️  Cannot test - requests module not available")
    except Exception as e:
        print(f"   ⚠️  Cannot test API - {str(e)[:50]}")
    
    print(f"\n" + "=" * 50)
    print(f"✅ MARKET SIGNAL CONFIGURATION: VALID")
    print(f"🚀 Ready for market signal operations")
    
    return True

def show_setup_instructions():
    """Show setup instructions if configuration is invalid"""
    print(f"\n🔧 SETUP INSTRUCTIONS:")
    print(f"=" * 50)
    print(f"1. Go to Replit Secrets tab")
    print(f"2. Add these environment variables:")
    print(f"")
    print(f"   Key: MARKET_SIGNAL_ENABLED")
    print(f"   Value: true")
    print(f"")
    print(f"   Key: COINMARKETCAP_API_KEY") 
    print(f"   Value: your_api_key_here")
    print(f"")
    print(f"3. Get free API key from:")
    print(f"   https://coinmarketcap.com/api/")
    print(f"")
    print(f"4. Run this script again to verify")

if __name__ == "__main__":
    if verify_market_signal_config():
        print(f"\n🎉 Configuration is valid!")
        sys.exit(0)
    else:
        show_setup_instructions()
        sys.exit(1)
