
#!/usr/bin/env python3
"""
System Validator - Comprehensive Testing
Validates all components work correctly with real data
"""

import os
import time
import sys
import traceback

def test_accurate_fetcher():
    """Test the accurate data fetcher"""
    print("🧪 Testing Accurate Data Fetcher")
    print("-" * 40)
    
    try:
        from accurate_debank_fetcher import AccurateWalletDataFetcher
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Initialize with mainnet
        os.environ['NETWORK_MODE'] = 'mainnet'
        agent = ArbitrumTestnetAgent('mainnet')
        
        fetcher = AccurateWalletDataFetcher(agent.w3, agent.address)
        data = fetcher.get_comprehensive_wallet_data()
        
        # Validate data
        required_fields = [
            'wallet_address', 'eth_balance', 'wbtc_balance', 'health_factor',
            'total_collateral_usdc', 'total_debt_usdc', 'success'
        ]
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing field: {field}")
                return False
        
        print(f"✅ Wallet: {data['wallet_address']}")
        print(f"✅ ETH Balance: {data['eth_balance']:.6f}")
        print(f"✅ WBTC Balance: {data['wbtc_balance']:.8f}")
        print(f"✅ Health Factor: {data['health_factor']:.2f}")
        print(f"✅ Aave Collateral: ${data['total_collateral_usdc']:.2f}")
        print(f"✅ Data Source: {data.get('data_source', 'unknown')}")
        
        if data['health_factor'] > 0 and data['total_collateral_usdc'] > 0:
            print("✅ Accurate fetcher test PASSED")
            return True
        else:
            print("❌ Data validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Accurate fetcher test FAILED: {e}")
        traceback.print_exc()
        return False

def test_dashboard_components():
    """Test dashboard components"""
    print("\n🧪 Testing Dashboard Components")
    print("-" * 40)
    
    try:
        from improved_web_dashboard import initialize_system, update_wallet_data
        
        # Test initialization
        initialize_system()
        print("✅ Dashboard initialization successful")
        
        # Test data update
        update_wallet_data()
        print("✅ Data update successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard component test FAILED: {e}")
        traceback.print_exc()
        return False

def test_web3_connectivity():
    """Test Web3 connectivity"""
    print("\n🧪 Testing Web3 Connectivity")
    print("-" * 40)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        agent = ArbitrumTestnetAgent('mainnet')
        
        # Test connection
        chain_id = agent.w3.eth.chain_id
        print(f"✅ Connected to chain ID: {chain_id}")
        
        if chain_id != 42161:
            print(f"❌ Wrong chain ID. Expected 42161, got {chain_id}")
            return False
        
        # Test wallet access
        eth_balance = agent.get_eth_balance()
        print(f"✅ ETH balance accessible: {eth_balance:.6f}")
        
        print(f"✅ Wallet address: {agent.address}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web3 connectivity test FAILED: {e}")
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints (requires dashboard to be running)"""
    print("\n🧪 Testing API Endpoints")
    print("-" * 40)
    
    try:
        import requests
        import time
        
        base_url = "http://localhost:5000"
        
        # Wait a moment for server startup
        time.sleep(2)
        
        # Test system status
        response = requests.get(f"{base_url}/api/system-status", timeout=10)
        if response.status_code == 200:
            print("✅ System status endpoint working")
            data = response.json()
            print(f"   Fetcher initialized: {data.get('fetcher_initialized')}")
            print(f"   Last update: {data.get('data_age_seconds', -1):.0f}s ago")
        else:
            print(f"❌ System status failed: {response.status_code}")
            return False
        
        # Test wallet status
        response = requests.get(f"{base_url}/api/wallet-status", timeout=10)
        if response.status_code == 200:
            print("✅ Wallet status endpoint working")
            data = response.json()
            if data.get('success'):
                print(f"   Health Factor: {data.get('health_factor', 0):.2f}")
                print(f"   ETH Balance: {data.get('eth_balance', 0):.6f}")
            else:
                print(f"   ⚠️ API returned error: {data.get('error', 'Unknown')}")
        else:
            print(f"❌ Wallet status failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test FAILED: {e}")
        return False

def run_comprehensive_validation():
    """Run all validation tests"""
    print("🔍 COMPREHENSIVE SYSTEM VALIDATION")
    print("=" * 50)
    
    tests = [
        ("Web3 Connectivity", test_web3_connectivity),
        ("Accurate Data Fetcher", test_accurate_fetcher),
        ("Dashboard Components", test_dashboard_components),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n▶️ Running {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 VALIDATION SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - System ready for deployment!")
        return True
    else:
        print("⚠️ Some tests failed - Check logs above")
        return False

if __name__ == "__main__":
    success = run_comprehensive_validation()
    
    if success:
        print("\n✅ System validation completed successfully")
        print("🚀 Ready to launch improved dashboard")
    else:
        print("\n❌ System validation failed")
        print("🔧 Please fix issues before launching")
        sys.exit(1)
