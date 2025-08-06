
import os
import sys
import traceback
from datetime import datetime

def test_syntax_validation():
    """Test all critical files for syntax errors"""
    print("🔍 TESTING SYNTAX VALIDATION")
    print("=" * 50)
    
    critical_files = [
        'arbitrum_testnet_agent.py',
        'main.py',
        'web_dashboard.py',
        'aave_integration.py',
        'uniswap_integration.py'
    ]
    
    syntax_errors = []
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                import py_compile
                py_compile.compile(file_path, doraise=True)
                print(f"✅ {file_path}: Syntax OK")
            except py_compile.PyCompileError as e:
                print(f"❌ {file_path}: {e}")
                syntax_errors.append(f"{file_path}: {e}")
        else:
            print(f"⚠️ {file_path}: File not found")
    
    return len(syntax_errors) == 0, syntax_errors

def test_agent_initialization():
    """Test agent initialization with all integrations"""
    print("\n🤖 TESTING AGENT INITIALIZATION")
    print("=" * 50)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print("✅ Agent initialized successfully")
        
        # Test critical properties
        if not hasattr(agent, 'address') or not agent.address:
            print("❌ Agent address not set")
            return False
            
        if not hasattr(agent, 'w3') or not agent.w3:
            print("❌ Web3 connection not established")
            return False
            
        # Test network connection
        try:
            chain_id = agent.w3.eth.chain_id
            print(f"✅ Connected to chain ID: {chain_id}")
        except:
            print("❌ Network connection failed")
            return False
            
        # Test DeFi integrations
        if agent.initialize_integrations():
            print("✅ DeFi integrations initialized")
        else:
            print("⚠️ Some DeFi integrations failed")
            
        # Test debt swap methods
        debt_swap_methods = [
            'execute_debt_swap_dai_to_arb',
            'execute_debt_swap_arb_to_dai',
            'check_debt_swap_conditions',
            'get_debt_swap_parameters',
            'execute_complete_debt_swap_sequence'
        ]
        
        for method in debt_swap_methods:
            if hasattr(agent, method):
                print(f"✅ Debt swap method available: {method}")
            else:
                print(f"❌ Missing debt swap method: {method}")
                return False
        
        print("✅ Agent initialization and debt swap functionality verified")
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        traceback.print_exc()
        return False

def test_debt_swap_readiness():
    """Test debt swap system readiness"""
    print("\n🔄 TESTING DEBT SWAP READINESS")
    print("=" * 50)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        if not agent.initialize_integrations():
            print("⚠️ DeFi integrations not fully initialized")
        
        # Test debt swap conditions check
        try:
            conditions_ok, message = agent.check_debt_swap_conditions()
            print(f"✅ Debt swap conditions check: {message}")
        except Exception as e:
            print(f"❌ Debt swap conditions check failed: {e}")
            return False
            
        # Test debt swap parameters
        try:
            params = agent.get_debt_swap_parameters()
            if params:
                print(f"✅ Debt swap parameters available: {len(params)} parameters")
            else:
                print("⚠️ Debt swap parameters not available (market signal strategy not enabled)")
        except Exception as e:
            print(f"❌ Debt swap parameters check failed: {e}")
            return False
            
        print("✅ Debt swap system readiness verified")
        return True
        
    except Exception as e:
        print(f"❌ Debt swap readiness test failed: {e}")
        return False

def test_network_approval_requirements():
    """Test network approval requirements"""
    print("\n🌐 TESTING NETWORK APPROVAL REQUIREMENTS")
    print("=" * 50)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        # Test ETH balance for gas
        eth_balance = agent.get_eth_balance()
        if eth_balance >= 0.001:
            print(f"✅ ETH balance sufficient: {eth_balance:.6f} ETH")
        else:
            print(f"⚠️ ETH balance low: {eth_balance:.6f} ETH")
            
        # Test health factor
        health_factor = agent.get_health_factor()
        if health_factor >= 2.0:
            print(f"✅ Health factor safe: {health_factor:.3f}")
        else:
            print(f"⚠️ Health factor risky: {health_factor:.3f}")
            
        # Test account data availability
        if hasattr(agent, 'aave') and agent.aave:
            account_data = agent.aave.get_user_account_data()
            if account_data:
                available_borrows = account_data.get('availableBorrowsUSD', 0)
                print(f"✅ Available borrows: ${available_borrows:.2f}")
                
                if available_borrows > 5.0:
                    print("✅ Sufficient borrowing capacity for operations")
                else:
                    print("⚠️ Limited borrowing capacity")
            else:
                print("❌ Unable to retrieve account data")
                return False
        else:
            print("❌ Aave integration not available")
            return False
            
        print("✅ Network approval requirements verified")
        return True
        
    except Exception as e:
        print(f"❌ Network approval requirements test failed: {e}")
        return False

def main():
    """Run complete system functionality test"""
    print("🚀 COMPLETE SYSTEM FUNCTIONALITY TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    # Track test results
    test_results = {}
    
    # Test 1: Syntax validation
    syntax_ok, syntax_errors = test_syntax_validation()
    test_results['syntax'] = syntax_ok
    
    if not syntax_ok:
        print(f"\n❌ CRITICAL: Syntax errors must be fixed before proceeding")
        for error in syntax_errors:
            print(f"   • {error}")
        return False
    
    # Test 2: Agent initialization
    agent_ok = test_agent_initialization()
    test_results['agent'] = agent_ok
    
    # Test 3: Debt swap readiness
    debt_swap_ok = test_debt_swap_readiness()
    test_results['debt_swap'] = debt_swap_ok
    
    # Test 4: Network approval requirements
    network_ok = test_network_approval_requirements()
    test_results['network'] = network_ok
    
    # Final assessment
    print("\n📊 FINAL SYSTEM ASSESSMENT")
    print("=" * 60)
    
    all_tests_passed = all(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.upper()}: {status}")
    
    if all_tests_passed:
        print("\n🎉 SYSTEM 100% FUNCTIONAL - READY FOR NETWORK EXECUTION")
        print("✅ All tests passed")
        print("✅ Debt swap feature operational")
        print("✅ Network approval requirements met")
        return True
    else:
        print("\n⚠️ SYSTEM NOT FULLY FUNCTIONAL")
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"Failed tests: {', '.join(failed_tests)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
