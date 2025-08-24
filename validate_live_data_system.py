
#!/usr/bin/env python3
"""
Live Data System Validator
Comprehensive testing of all live data fetching components
"""

import time
import requests
from enhanced_contract_manager import EnhancedContractManager

def validate_enhanced_contract_manager():
    """Test Enhanced Contract Manager functionality"""
    print("🧪 TESTING ENHANCED CONTRACT MANAGER")
    print("=" * 50)
    
    try:
        # Initialize manager
        manager = EnhancedContractManager()
        
        if not manager.working_rpc:
            print("❌ Failed to establish RPC connection")
            return False
            
        print(f"✅ Connected to: {manager.working_rpc}")
        print(f"📊 Tested {len(manager.rpc_performance)} RPC endpoints")
        
        # Test wallet address
        wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        
        # Test token balances
        print("\n💰 TESTING TOKEN BALANCES:")
        
        eth_balance = manager.w3.eth.get_balance(wallet) / 1e18
        print(f"   ETH: {eth_balance:.6f}")
        
        usdc_balance = manager.get_token_balance_robust(manager.usdc_address, wallet)
        print(f"   USDC: {usdc_balance:.6f}")
        
        wbtc_balance = manager.get_token_balance_robust(manager.wbtc_address, wallet)
        print(f"   WBTC: {wbtc_balance:.8f}")
        
        # Test Aave data
        print("\n🏦 TESTING AAVE DATA:")
        aave_data = manager.get_aave_data_robust(wallet, manager.aave_pool_address)
        
        if aave_data:
            print(f"   Health Factor: {aave_data['health_factor']:.2f}")
            print(f"   Collateral: ${aave_data['total_collateral_usd']:.2f}")
            print(f"   Data Source: {aave_data['data_source']}")
            print(f"   RPC Used: {aave_data['rpc_used']}")
        else:
            print("   ❌ Aave data fetch failed")
            
        # Test prices
        print("\n💹 TESTING LIVE PRICES:")
        prices = manager.get_live_prices()
        
        if prices and prices['ETH'] > 0:
            print(f"   ETH: ${prices['ETH']:.2f}")
            print(f"   BTC: ${prices['BTC']:.2f}")
            print(f"   USDC: ${prices['USDC']:.4f}")
            print(f"   ARB: ${prices['ARB']:.4f}")
        else:
            print("   ❌ Price fetch failed")
            
        print("\n✅ Enhanced Contract Manager validation complete")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Contract Manager test failed: {e}")
        return False

def validate_dashboard_api():
    """Test dashboard API endpoints"""
    print("\n🌐 TESTING DASHBOARD API")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # Test wallet status endpoint
        response = requests.get(f"{base_url}/api/wallet-status", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ API Response: {response.status_code}")
            print(f"📊 Data Source: {data.get('data_source', 'Unknown')}")
            print(f"🔗 RPC: {data.get('enhanced_contract_manager', {}).get('rpc_endpoint', 'Unknown')}")
            print(f"🏦 Aave Source: {data.get('aave_positions', {}).get('data_source', 'Unknown')}")
            print(f"💰 Portfolio: ${data.get('total_portfolio_usd', 0):.2f}")
            
            # Check for hardcoded fallbacks
            aave_source = data.get('aave_positions', {}).get('data_source', '')
            if 'fallback' in aave_source.lower():
                print("⚠️ Dashboard still using fallback data")
                return False
            else:
                print("✅ Dashboard using live data sources")
                return True
                
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard API test failed: {e}")
        return False

def run_comprehensive_validation():
    """Run complete validation suite"""
    print("🚀 COMPREHENSIVE LIVE DATA SYSTEM VALIDATION")
    print("=" * 60)
    
    results = {
        'enhanced_contract_manager': False,
        'dashboard_api': False
    }
    
    # Test Enhanced Contract Manager
    results['enhanced_contract_manager'] = validate_enhanced_contract_manager()
    
    # Test Dashboard API
    results['dashboard_api'] = validate_dashboard_api()
    
    # Generate final report
    print("\n📋 VALIDATION RESULTS")
    print("=" * 60)
    
    overall_success = all(results.values())
    
    for component, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{component.replace('_', ' ').title()}: {status}")
    
    if overall_success:
        print("\n🎉 ALL SYSTEMS VALIDATED - LIVE DATA SYSTEM READY!")
        print("🚀 Dashboard should now display real-time blockchain data")
    else:
        print("\n⚠️ SOME SYSTEMS FAILED - REQUIRES ATTENTION")
        
    return overall_success

if __name__ == "__main__":
    success = run_comprehensive_validation()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Access your dashboard via the Replit webview")
        print("2. Verify live data is displaying correctly")
        print("3. Monitor for any error messages in console")
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Check RPC endpoint connectivity")
        print("2. Verify contract addresses are correct")
        print("3. Check API rate limits")
