
#!/usr/bin/env python3
"""
API Key Validation Script
Validates all market data API keys before system startup
"""

import os
import requests
import time

def validate_coin_api():
    """Validate COIN_API key"""
    api_key = os.getenv('COIN_API')
    if not api_key:
        return False, "COIN_API key not found"
    
    # Check key format - should be UUID format (36+ chars)
    if len(api_key) < 30:
        return False, f"COIN_API key too short ({len(api_key)} chars) - should be 36+ characters UUID format"
    
    try:
        # Use simple exchange rate endpoint for validation
        url = "https://rest.coinapi.io/v1/exchangerate/BTC/USD"
        headers = {
            'X-CoinAPI-Key': api_key,
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if 'rate' in data and data['rate'] > 0:
                return True, f"COIN_API key valid (BTC price: ${data['rate']:,.2f})"
            else:
                return False, "COIN_API returned invalid data format"
        elif response.status_code == 401:
            return False, "COIN_API key unauthorized - check your API key"
        elif response.status_code == 403:
            return False, "COIN_API key forbidden - check permissions or upgrade plan"
        elif response.status_code == 429:
            return False, "COIN_API rate limit exceeded - try again later"
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                return False, f"COIN_API error {response.status_code}: {error_msg}"
            except:
                return False, f"COIN_API HTTP error: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "COIN_API validation timeout"
    except Exception as e:
        return False, f"COIN_API validation error: {e}"
    except requests.exceptions.ConnectionError:
        return False, "COIN_API connection failed"
    except Exception as e:
        return False, f"COIN_API validation error: {e}"

def validate_coinmarketcap_api():
    """Validate CoinMarketCap API key"""
    api_key = os.getenv('COINMARKETCAP_API_KEY')
    if not api_key:
        return False, "COINMARKETCAP_API_KEY not found"
    
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {'X-CMC_PRO_API_KEY': api_key}
        params = {'symbol': 'BTC', 'convert': 'USD'}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return True, "CoinMarketCap API key valid"
        elif response.status_code == 401:
            return False, "CoinMarketCap API key invalid"
        elif response.status_code == 429:
            return False, "CoinMarketCap rate limit exceeded"
        else:
            return False, f"CoinMarketCap error: {response.status_code}"
    except Exception as e:
        return False, f"CoinMarketCap validation error: {e}"

def validate_coingecko_api():
    """Validate CoinGecko API (free tier)"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': 'bitcoin', 'vs_currencies': 'usd'}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return True, "CoinGecko API accessible"
        elif response.status_code == 429:
            return False, "CoinGecko rate limit exceeded"
        else:
            return False, f"CoinGecko error: {response.status_code}"
    except Exception as e:
        return False, f"CoinGecko validation error: {e}"

def main():
    """Validate all API keys and provide recommendations"""
    print("🔍 VALIDATING MARKET DATA API KEYS")
    print("=" * 40)
    
    valid_apis = 0
    total_apis = 3
    
    # Test COIN_API
    coin_valid, coin_msg = validate_coin_api()
    print(f"{'✅' if coin_valid else '❌'} COIN_API: {coin_msg}")
    if coin_valid:
        valid_apis += 1
    
    # Small delay between API calls
    time.sleep(1)
    
    # Test CoinMarketCap
    cmc_valid, cmc_msg = validate_coinmarketcap_api()
    print(f"{'✅' if cmc_valid else '❌'} CoinMarketCap: {cmc_msg}")
    if cmc_valid:
        valid_apis += 1
    
    time.sleep(1)
    
    # Test CoinGecko
    gecko_valid, gecko_msg = validate_coingecko_api()
    print(f"{'✅' if gecko_valid else '❌'} CoinGecko: {gecko_msg}")
    if gecko_valid:
        valid_apis += 1
    
    print(f"\n📊 API Status: {valid_apis}/{total_apis} working")
    
    if valid_apis == 0:
        print("🚨 CRITICAL: No market data APIs available!")
        print("💡 SOLUTION: Update your Replit secrets with valid API keys")
        return False
    elif valid_apis < 2:
        print("⚠️ WARNING: Limited market data sources available")
        print("💡 RECOMMENDATION: Add more API keys for reliability")
        return True
    else:
        print("✅ GOOD: Multiple market data sources available")
        return True

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Validate API keys and market signal configuration
"""

import os
import requests

def main():
    print("🔍 API KEY VALIDATION")
    print("=" * 30)
    
    # Check environment variables
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
    coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
    coinapi_key = os.getenv('COIN_API_KEY') or os.getenv('COINAPI_KEY')
    
    print(f"MARKET_SIGNAL_ENABLED: {'✅' if market_enabled else '❌'} {market_enabled}")
    print(f"COINMARKETCAP_API_KEY: {'✅' if coinmarketcap_key else '❌'} {'Present' if coinmarketcap_key else 'Missing'}")
    print(f"COIN_API_KEY: {'✅' if coinapi_key else '❌'} {'Present' if coinapi_key else 'Missing'}")
    
    # Test CoinMarketCap API if key present
    if coinmarketcap_key:
        print(f"\n🧪 Testing CoinMarketCap API...")
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': coinmarketcap_key,
            }
            params = {'symbol': 'BTC', 'convert': 'USD'}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'BTC' in data['data']:
                    btc_price = data['data']['BTC']['quote']['USD']['price']
                    print(f"✅ CoinMarketCap API working - BTC: ${btc_price:.2f}")
                else:
                    print("⚠️ CoinMarketCap API returned unexpected format")
            else:
                print(f"❌ CoinMarketCap API failed: HTTP {response.status_code}")
                if response.status_code == 401:
                    print("   Invalid API key")
                elif response.status_code == 429:
                    print("   Rate limited - too many requests")
                    
        except Exception as e:
            print(f"❌ CoinMarketCap API test failed: {e}")
    
    # Test CoinAPI if key present
    if coinapi_key:
        print(f"\n🧪 Testing CoinAPI...")
        try:
            url = "https://rest.coinapi.io/v1/exchangerate/BTC/USD"
            headers = {'X-CoinAPI-Key': coinapi_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'rate' in data:
                    btc_price = data['rate']
                    print(f"✅ CoinAPI working - BTC: ${btc_price:.2f}")
                else:
                    print("⚠️ CoinAPI returned unexpected format")
            else:
                print(f"❌ CoinAPI failed: HTTP {response.status_code}")
                if response.status_code == 401:
                    print("   Invalid API key")
                elif response.status_code == 429:
                    print("   Rate limited")
                    
        except Exception as e:
            print(f"❌ CoinAPI test failed: {e}")
    
    # Overall status
    working_apis = 0
    if coinmarketcap_key:
        working_apis += 1
    if coinapi_key:
        working_apis += 1
    
    print(f"\n📊 SUMMARY")
    print(f"Market Signals Enabled: {'✅' if market_enabled else '❌'}")
    print(f"Working APIs: {working_apis}")
    print(f"Status: {'✅ READY' if market_enabled and working_apis > 0 else '❌ NOT READY'}")
    
    return market_enabled and working_apis > 0

if __name__ == "__main__":
    main()
