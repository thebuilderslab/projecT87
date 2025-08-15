
#!/usr/bin/env python3
"""
Test Complete Autonomous System
Tests the autonomous agent, dashboard, and trigger functionality
"""

import os
import time
import subprocess
import requests
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_agent_initialization():
    """Test agent can initialize properly"""
    print("🧪 Testing Agent Initialization...")
    try:
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: {agent.network_mode}")
        print(f"⛓️ Chain ID: {agent.w3.eth.chain_id}")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

def test_dashboard_api():
    """Test dashboard API endpoints"""
    print("🧪 Testing Dashboard API...")
    try:
        # Test basic API
        response = requests.get('http://localhost:5000/api/test', timeout=10)
        if response.status_code == 200:
            print("✅ Dashboard API responding")
            
            # Test wallet status
            response = requests.get('http://localhost:5000/api/wallet_status', timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Wallet status API working")
                print(f"   Health Factor: {data.get('health_factor', 'N/A')}")
                print(f"   Collateral: ${data.get('total_collateral_usdc', 0):.2f}")
                return True
            else:
                print(f"❌ Wallet status API failed: {response.status_code}")
                return False
        else:
            print(f"❌ Dashboard API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard API test failed: {e}")
        return False

def test_trigger_logic():
    """Test the autonomous trigger logic"""
    print("🧪 Testing Trigger Logic...")
    try:
        agent = ArbitrumTestnetAgent()
        
        # Initialize integrations
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        print("✅ Integrations initialized")
        
        # Test autonomous task execution
        print("🎯 Testing autonomous task execution...")
        performance = agent.run_real_defi_task(1, 0, {
            'health_factor_target': 1.25,
            'max_iterations_per_run': 1
        })
        
        print(f"✅ Autonomous task completed with performance: {performance}")
        
        if performance > 0.5:
            print("✅ Trigger logic working correctly")
            return True
        else:
            print("⚠️ Trigger logic needs optimization")
            return False
            
    except Exception as e:
        print(f"❌ Trigger logic test failed: {e}")
        return False

def test_complete_system():
    """Run complete system test"""
    print("🚀 COMPLETE SYSTEM TEST")
    print("=" * 50)
    
    # Force mainnet mode
    os.environ['NETWORK_MODE'] = 'mainnet'
    
    results = {}
    
    # Test 1: Agent initialization
    results['agent_init'] = test_agent_initialization()
    
    # Test 2: Dashboard API (if running)
    results['dashboard_api'] = test_dashboard_api()
    
    # Test 3: Trigger logic
    results['trigger_logic'] = test_trigger_logic()
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("💡 Ready for autonomous mainnet operation")
        return True
    else:
        print("⚠️ Some systems need attention")
        return False

if __name__ == "__main__":
    test_complete_system()
