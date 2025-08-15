
#!/usr/bin/env python3
"""
Test API endpoints directly to diagnose dashboard issues
"""

import requests
import json
import time

def test_endpoint(url, name):
    """Test a single API endpoint"""
    print(f"\n🔍 Testing {name}: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                data = response.json()
                print(f"   JSON Response: {json.dumps(data, indent=2)}")
                return True, data
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Decode Error: {e}")
                print(f"   Raw Response: {response.text[:500]}")
                return False, response.text
        else:
            print(f"   Raw Response: {response.text[:500]}")
            return False, response.text
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request Error: {e}")
        return False, str(e)

def main():
    """Test all critical API endpoints"""
    print("🚀 API ENDPOINT DIAGNOSTICS")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    endpoints = [
        ("/api/test", "Basic API Test"),
        ("/api/parameters", "Parameters API"),
        ("/api/emergency_status", "Emergency Status API"),
        ("/api/wallet_status", "Wallet Status API"),
        ("/api/performance", "Performance API"),
        ("/api/network-info", "Network Info API"),
        ("/api/debug/test-all", "Debug Test All")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        success, data = test_endpoint(f"{base_url}{endpoint}", name)
        results[endpoint] = {'success': success, 'data': data}
        time.sleep(1)  # Small delay between requests
    
    print("\n📊 SUMMARY")
    print("=" * 50)
    for endpoint, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {endpoint}")
    
    print(f"\n🕒 Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
