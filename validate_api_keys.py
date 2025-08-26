
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
    
    try:
        url = "https://rest.coinapi.io/v1/exchangerate/BTC/USD"
        headers = {'X-CoinAPI-Key': api_key}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, "COIN_API key valid"
        elif response.status_code == 401:
            return False, "COIN_API key invalid"
        elif response.status_code == 429:
            return False, "COIN_API rate limit exceeded"
        else:
            return False, f"COIN_API error: {response.status_code}"
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
