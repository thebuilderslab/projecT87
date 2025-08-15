
#!/usr/bin/env python3
"""
Comprehensive API diagnostic test to identify dashboard issues
"""

import requests
import json
import time
import subprocess
import threading
import sys
import os

def start_dashboard_process():
    """Start the web dashboard in background"""
    try:
        print("🚀 Starting web dashboard process...")
        process = subprocess.Popen(['python', 'web_dashboard.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT, 
                                 universal_newlines=True,
                                 bufsize=1)
        
        # Give it time to start
        time.sleep(5)
        return process
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return None

def test_endpoint_detailed(url, name):
    """Test endpoint with detailed debugging"""
    print(f"\n{'='*60}")
    print(f"🔍 TESTING: {name}")
    print(f"📍 URL: {url}")
    print(f"{'='*60}")
    
    try:
        print("⏱️ Making request...")
        response = requests.get(url, timeout=15)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print(f"⏱️ Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                data = response.json()
                print(f"✅ JSON Response (first 1000 chars):")
                json_str = json.dumps(data, indent=2)
                if len(json_str) > 1000:
                    print(json_str[:1000] + "... (truncated)")
                else:
                    print(json_str)
                
                # Check for specific error patterns
                if isinstance(data, dict):
                    if 'error' in data:
                        print(f"🚨 ERROR DETECTED: {data['error']}")
                    if 'success' in data and not data['success']:
                        print(f"🚨 SUCCESS=FALSE: {data}")
                        
                return True, data
            except json.JSONDecodeError as e:
                print(f"❌ JSON Decode Error: {e}")
                print(f"📝 Raw Response: {response.text[:500]}")
                return False, response.text
        else:
            print(f"📝 Non-JSON Response: {response.text[:500]}")
            return False, response.text
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Dashboard may not be running on port 5000")
        return False, str(e)
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: {e}")
        return False, str(e)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False, str(e)

def monitor_dashboard_logs(process, duration=30):
    """Monitor dashboard logs for specified duration"""
    print(f"\n📊 MONITORING DASHBOARD LOGS FOR {duration} SECONDS...")
    print("="*60)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        if process and process.poll() is None:
            try:
                line = process.stdout.readline()
                if line:
                    print(f"🖥️ DASHBOARD: {line.strip()}")
            except:
                break
        time.sleep(0.1)

def main():
    """Main diagnostic function"""
    print("🚀 COMPREHENSIVE API DIAGNOSTICS")
    print("="*80)
    
    # Check if dashboard is already running
    try:
        response = requests.get("http://127.0.0.1:5000/api/test", timeout=3)
        print("✅ Dashboard appears to be already running")
        dashboard_process = None
    except:
        print("🔄 Starting new dashboard process...")
        dashboard_process = start_dashboard_process()
        if not dashboard_process:
            print("❌ Could not start dashboard, testing anyway...")
    
    # Wait for startup
    print("⏱️ Waiting for dashboard startup...")
    time.sleep(8)
    
    base_url = "http://127.0.0.1:5000"
    
    # Test endpoints in order of importance
    critical_endpoints = [
        ("/api/test", "Basic API Test"),
        ("/api/parameters", "Parameters API (CRITICAL)"),
        ("/api/emergency_status", "Emergency Status API (CRITICAL)"),
        ("/api/wallet_status", "Wallet Status API"),
        ("/api/performance", "Performance API"),
        ("/api/network-info", "Network Info API"),
        ("/api/health-check", "Health Check API")
    ]
    
    results = {}
    failed_endpoints = []
    
    for endpoint, name in critical_endpoints:
        success, data = test_endpoint_detailed(f"{base_url}{endpoint}", name)
        results[endpoint] = {'success': success, 'data': data}
        
        if not success:
            failed_endpoints.append(endpoint)
        
        # Small delay between tests
        time.sleep(2)
    
    # Monitor logs if we started the process
    if dashboard_process:
        monitor_dashboard_logs(dashboard_process, 15)
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL DIAGNOSTIC SUMMARY")
    print(f"{'='*80}")
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print(f"✅ Successful endpoints: {success_count}/{total_count}")
    print(f"❌ Failed endpoints: {len(failed_endpoints)}")
    
    if failed_endpoints:
        print(f"\n🚨 FAILED ENDPOINTS:")
        for endpoint in failed_endpoints:
            print(f"   - {endpoint}")
            error_data = results[endpoint]['data']
            if isinstance(error_data, str) and len(error_data) < 200:
                print(f"     Error: {error_data}")
    
    # Check for specific dashboard error patterns
    params_result = results.get('/api/parameters', {})
    emergency_result = results.get('/api/emergency_status', {})
    
    print(f"\n🔍 SPECIFIC ISSUE ANALYSIS:")
    
    if not params_result.get('success'):
        print(f"❌ Parameters API failing - this causes 'undefined' errors")
        print(f"   Likely cause: {params_result.get('data', 'Unknown')}")
    
    if not emergency_result.get('success'):
        print(f"❌ Emergency Status API failing")
        print(f"   Likely cause: {emergency_result.get('data', 'Unknown')}")
    
    # Check if it's a specific data format issue
    if params_result.get('success') and emergency_result.get('success'):
        print(f"✅ Both critical APIs working - issue may be frontend JavaScript")
        
        params_data = params_result.get('data', {})
        if isinstance(params_data, dict) and 'error' in params_data:
            print(f"🚨 Parameters API returning error: {params_data['error']}")
    
    print(f"\n⏰ Diagnostic completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Clean up
    if dashboard_process:
        try:
            dashboard_process.terminate()
            dashboard_process.wait(timeout=5)
        except:
            pass

if __name__ == "__main__":
    main()
