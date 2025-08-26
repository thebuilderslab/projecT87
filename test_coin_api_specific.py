
#!/usr/bin/env python3
"""
Specific COIN_API Format Verification Test
Tests the exact API format and authentication method
"""

import os
import requests
import json

def test_coin_api_formats():
    """Test different COIN_API endpoint formats to find the correct one"""
    print("🔍 TESTING COIN_API ENDPOINT FORMATS")
    print("=" * 50)
    
    api_key = os.getenv('COIN_API')
    if not api_key:
        print("❌ COIN_API key not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...")
    print(f"📏 API Key length: {len(api_key)} characters")
    
    # Test different endpoint formats
    test_endpoints = [
        {
            'name': 'Assets List',
            'url': 'https://rest.coinapi.io/v1/assets',
            'params': {'filter_asset_id': 'BTC'}
        },
        {
            'name': 'Exchange Rate BTC/USD',
            'url': 'https://rest.coinapi.io/v1/exchangerate/BTC/USD',
            'params': {}
        },
        {
            'name': 'Current Price (Simple)',
            'url': 'https://rest.coinapi.io/v1/exchangerate/BTC/USD',
            'params': {}
        },
        {
            'name': 'OHLCV Data',
            'url': 'https://rest.coinapi.io/v1/ohlcv/BTC/USD/latest',
            'params': {'period_id': '1DAY', 'limit': 1}
        }
    ]
    
    headers = {
        'X-CoinAPI-Key': api_key,
        'Accept': 'application/json'
    }
    
    working_endpoints = []
    
    for test in test_endpoints:
        print(f"\n🔍 Testing: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            response = requests.get(
                test['url'], 
                headers=headers, 
                params=test['params'],
                timeout=15
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS - Response type: {type(data)}")
                
                if isinstance(data, list):
                    print(f"📊 List with {len(data)} items")
                    if len(data) > 0:
                        print(f"📋 First item keys: {list(data[0].keys())}")
                elif isinstance(data, dict):
                    print(f"📊 Dict with keys: {list(data.keys())}")
                    if 'rate' in data:
                        print(f"💰 BTC Price: ${data['rate']:,.2f}")
                
                working_endpoints.append(test['name'])
                
            elif response.status_code == 401:
                print("❌ UNAUTHORIZED - API key invalid")
            elif response.status_code == 403:
                print("❌ FORBIDDEN - API key lacks permissions")
            elif response.status_code == 429:
                print("⚠️ RATE LIMITED - Too many requests")
            else:
                print(f"❌ HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error text: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT")
        except requests.exceptions.ConnectionError:
            print("❌ CONNECTION ERROR")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n📊 SUMMARY")
    print("=" * 30)
    print(f"Working endpoints: {len(working_endpoints)}")
    for endpoint in working_endpoints:
        print(f"✅ {endpoint}")
    
    if len(working_endpoints) > 0:
        print("\n💡 RECOMMENDATION: COIN_API key is working!")
        return True
    else:
        print("\n❌ CRITICAL: No endpoints working")
        print("💡 Check API key validity at: https://www.coinapi.io/")
        return False

def test_current_integration():
    """Test the current enhanced_market_analyzer integration"""
    print("\n🔍 TESTING CURRENT INTEGRATION")
    print("=" * 40)
    
    try:
        from enhanced_market_analyzer import CoinAPIClient
        
        api_key = os.getenv('COIN_API')
        client = CoinAPIClient(api_key)
        
        print("✅ CoinAPIClient initialized")
        
        # Test getting BTC price
        btc_data = client.get_current_price('BTC')
        if btc_data:
            print(f"✅ BTC Data: ${btc_data.get('price', 'N/A')}")
            print(f"📊 24h Change: {btc_data.get('percent_change_24h', 'N/A')}%")
            return True
        else:
            print("❌ No BTC data returned")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 COIN_API SPECIFIC FORMAT VERIFICATION")
    print("=" * 60)
    
    # Test 1: Different endpoint formats
    endpoints_working = test_coin_api_formats()
    
    # Test 2: Current integration
    if endpoints_working:
        integration_working = test_current_integration()
    else:
        integration_working = False
    
    print("\n" + "=" * 60)
    if endpoints_working and integration_working:
        print("🎉 COIN_API FULLY OPERATIONAL!")
        print("✅ API key valid")
        print("✅ Endpoints accessible") 
        print("✅ Integration working")
    elif endpoints_working:
        print("⚠️ COIN_API KEY VALID BUT INTEGRATION NEEDS FIXING")
        print("✅ API key valid")
        print("✅ Endpoints accessible")
        print("❌ Integration has issues")
    else:
        print("❌ COIN_API NOT WORKING")
        print("💡 Check your API key at https://www.coinapi.io/")
    print("=" * 60)
