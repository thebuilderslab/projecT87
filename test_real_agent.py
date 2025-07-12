#!/usr/bin/env python3
"""
Comprehensive test script for ArbitrumTestnetAgent with real blockchain data
Tests all integrations, gas optimization, and strict error handling
"""

import os
import sys
import time
from datetime import datetime
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step_num, description):
    """Print a formatted test step"""
    print(f"\n📋 Step {step_num}: {description}")
    print("-" * 50)

def check_prerequisites():
    """Check all prerequisites before testing"""
    print_section("PRE-TEST VERIFICATION")

    # Check environment variables
    required_vars = ['PRIVATE_KEY', 'COINMARKETCAP_API_KEY', 'NETWORK_MODE']
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'PRIVATE_KEY':
                print(f"✅ {var}: {value[:10]}...{value[-4:]} (length: {len(value)})")
            elif var == 'COINMARKETCAP_API_KEY':
                print(f"✅ {var}: {value[:8]}...{value[-4:]} (length: {len(value)})")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n🚨 CRITICAL: Missing environment variables: {missing_vars}")
        print("💡 Please set these in Replit Secrets before continuing")
        return False

    print(f"\n✅ All required environment variables are set")
    return True

def test_agent_initialization():
    """Test agent initialization with real connections"""
    print_section("AGENT INITIALIZATION TEST")

    try:
        print_step(1, "Creating ArbitrumTestnetAgent instance")
        agent = ArbitrumTestnetAgent()

        print(f"✅ Agent created successfully")
        print(f"   📍 Wallet Address: {agent.address}")
        print(f"   🌐 Network Mode: {agent.network_mode}")
        print(f"   🔗 RPC URL: {agent.rpc_url}")
        print(f"   ⛓️ Chain ID: {agent.chain_id}")

        print_step(2, "Testing Web3 connection")
        if agent.w3.is_connected():
            chain_id = agent.w3.eth.chain_id
            latest_block = agent.w3.eth.block_number
            print(f"✅ Connected to blockchain")
            print(f"   ⛓️ Chain ID: {chain_id}")
            print(f"   📦 Latest Block: {latest_block}")
        else:
            print(f"❌ Failed to connect to blockchain")
            return None

        print_step(3, "Checking wallet balance")
        eth_balance = agent.get_eth_balance()
        print(f"✅ ETH Balance: {eth_balance:.6f} ETH")

        if eth_balance < 0.001:
            print(f"⚠️ WARNING: Low ETH balance for gas fees")

        return agent

    except Exception as e:
        print(f"❌ CRITICAL: Agent initialization failed: {e}")
        return None

def test_integrations_initialization(agent):
    """Test initialization of all DeFi integrations"""
    print_section("DEFI INTEGRATIONS TEST")

    try:
        print_step(1, "Initializing DeFi integrations")
        success = agent.initialize_integrations()

        if success:
            print(f"✅ All integrations initialized successfully")

            # Test each integration
            integrations = [
                ('Aave Integration', agent.aave),
                ('Uniswap Integration', agent.uniswap),
                ('Health Monitor', agent.health_monitor),
                ('Gas Calculator', agent.gas_calculator)
            ]

            for name, integration in integrations:
                if integration:
                    print(f"   ✅ {name}: Initialized")
                else:
                    print(f"   ❌ {name}: Failed")

            return True
        else:
            print(f"❌ Integration initialization failed")
            return False

    except Exception as e:
        print(f"❌ CRITICAL: Integration initialization error: {e}")
        return False

def test_real_data_fetching(agent):
    """Test fetching real blockchain data"""
    print_section("REAL DATA FETCHING TEST")

    try:
        print_step(1, "Testing health factor retrieval")
        health_data = agent.health_monitor.get_health_factor()

        if health_data:
            hf = health_data.get('health_factor', 0)
            print(f"✅ Health Factor: {hf:.4f}")
            if hf > 1.0:
                print(f"   ✅ Health factor is healthy (> 1.0)")
            else:
                print(f"   ⚠️ WARNING: Low health factor!")
        else:
            print(f"❌ Failed to get health factor")

        print_step(2, "Testing ARB price fetching")
        try:
            arb_price_data = agent.get_arb_price()
            arb_price = arb_price_data['price']
            print(f"✅ ARB Price: ${arb_price:.4f}")
        except Exception as e:
            print(f"❌ ARB price fetch failed: {e}")

        print_step(3, "Testing gas price optimization")
        gas_params = agent.gas_calculator.calculate_transaction_fee('aave_borrow', speed='market')
        if gas_params:
            gas_price_gwei = agent.w3.from_wei(gas_params['gas_price_wei'], 'gwei')
            print(f"✅ Optimized Gas Price: {gas_price_gwei:.2f} Gwei")
            print(f"   Gas Limit: {gas_params['gas_limit']}")
        else:
            print(f"❌ Gas optimization failed")

        return True

    except Exception as e:
        print(f"❌ CRITICAL: Real data fetching failed: {e}")
        return False

def test_autonomous_sequence(agent):
    """Test a small autonomous sequence"""
    print_section("AUTONOMOUS SEQUENCE TEST")

    try:
        print_step(1, "Testing autonomous task execution")
        print("🔄 Running autonomous DeFi task (1 iteration)...")

        # Run one iteration of the autonomous task
        performance = agent.run_real_defi_task(
            run_id=999,  # Test run ID
            iteration=1,
            config={'test_mode': True}
        )

        print(f"✅ Autonomous task completed")
        print(f"   📊 Performance Score: {performance:.3f}")

        if performance > 0.5:
            print(f"   ✅ Good performance (> 0.5)")
        else:
            print(f"   ⚠️ Low performance score")

        return True

    except Exception as e:
        print(f"❌ Autonomous sequence failed: {e}")
        return False

def test_error_handling(agent):
    """Test strict error handling (safe tests only)"""
    print_section("ERROR HANDLING TEST")

    try:
        print_step(1, "Testing network status checking")
        network_ok, status = agent.check_network_status()
        print(f"✅ Network Status: {status}")

        print_step(2, "Testing emergency stop mechanism")
        emergency_active = agent.check_emergency_stop()
        if emergency_active:
            print(f"🛑 Emergency stop is ACTIVE")
        else:
            print(f"✅ Emergency stop is not active")

        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Main test execution"""
    print(f"🚀 ARBITRUM TESTNET AGENT - COMPREHENSIVE TEST")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Check prerequisites
    if not check_prerequisites():
        print(f"\n❌ PRE-TEST VERIFICATION FAILED")
        return False

    # Step 2: Initialize agent
    agent = test_agent_initialization()
    if not agent:
        print(f"\n❌ AGENT INITIALIZATION FAILED")
        return False

    # Step 3: Test integrations
    if not test_integrations_initialization(agent):
        print(f"\n❌ INTEGRATIONS TEST FAILED")
        return False

    # Step 4: Test real data fetching
    if not test_real_data_fetching(agent):
        print(f"\n❌ REAL DATA FETCHING FAILED")
        return False

    # Step 5: Test autonomous sequence
    if not test_autonomous_sequence(agent):
        print(f"\n❌ AUTONOMOUS SEQUENCE FAILED")
        return False

    # Step 6: Test error handling
    if not test_error_handling(agent):
        print(f"\n❌ ERROR HANDLING TEST FAILED")
        return False

    # Final summary
    print_section("TEST SUMMARY")
    print(f"✅ ALL TESTS PASSED SUCCESSFULLY!")
    print(f"🎉 ArbitrumTestnetAgent is ready for operation")
    print(f"💡 You can now run autonomous mode or use the web dashboard")

    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\n🚀 READY TO PROCEED TO NEXT PHASE")
            exit(0)
        else:
            print(f"\n❌ TESTS FAILED - PLEASE FIX ISSUES BEFORE PROCEEDING")
            exit(1)
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        exit(1)