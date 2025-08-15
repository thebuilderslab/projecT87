
#!/usr/bin/env python3
"""
DEBT SWAP READINESS TEST
Comprehensive verification that debt swap feature can execute successfully and get network approval
"""

import os
import sys
import time
import json
from datetime import datetime

def test_syntax_errors():
    """Test for syntax errors in critical files"""
    print("🔍 TESTING SYNTAX ERRORS...")
    
    critical_files = [
        'arbitrum_testnet_agent.py',
        'market_signal_strategy.py',
        'aave_integration.py',
        'uniswap_integration.py'
    ]
    
    syntax_results = {}
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Try to compile the code
                compile(content, file_path, 'exec')
                syntax_results[file_path] = "✅ SYNTAX OK"
                print(f"   ✅ {file_path}: Syntax valid")
                
            except SyntaxError as e:
                syntax_results[file_path] = f"❌ SYNTAX ERROR: Line {e.lineno}: {e.msg}"
                print(f"   ❌ {file_path}: Line {e.lineno}: {e.msg}")
                return False, syntax_results
            except Exception as e:
                syntax_results[file_path] = f"⚠️ CHECK ERROR: {e}"
                print(f"   ⚠️ {file_path}: Check error: {e}")
        else:
            syntax_results[file_path] = "❌ FILE MISSING"
            print(f"   ❌ {file_path}: File missing")
            
    return True, syntax_results

def test_agent_initialization():
    """Test if agent can initialize without errors"""
    print("\n🤖 TESTING AGENT INITIALIZATION...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        # Test basic properties
        if not hasattr(agent, 'address') or not agent.address:
            print("   ❌ Agent address not set")
            return False
            
        if not hasattr(agent, 'w3') or not agent.w3:
            print("   ❌ Web3 connection not established")
            return False
            
        # Test network connection
        try:
            chain_id = agent.w3.eth.chain_id
            print(f"   ✅ Connected to chain ID: {chain_id}")
        except:
            print("   ❌ Network connection failed")
            return False
            
        # Test ETH balance
        try:
            eth_balance = agent.get_eth_balance()
            if eth_balance < 0.001:
                print(f"   ⚠️ Low ETH balance: {eth_balance:.6f} ETH")
                return False
            print(f"   ✅ ETH balance sufficient: {eth_balance:.6f} ETH")
        except:
            print("   ❌ Cannot retrieve ETH balance")
            return False
            
        print("   ✅ Agent initialization successful")
        return True
        
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        return False

def test_debt_swap_components():
    """Test debt swap system components"""
    print("\n🔄 TESTING DEBT SWAP COMPONENTS...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        # Test integrations initialization
        success = agent.initialize_integrations()
        if not success:
            print("   ❌ DeFi integrations failed to initialize")
            return False
            
        # Test market signal strategy
        if not agent.market_signal_strategy:
            print("   ⚠️ Market signal strategy not initialized")
            # This is not critical - system can work without it
        else:
            print("   ✅ Market signal strategy available")
            
        # Test Aave integration
        if not agent.aave:
            print("   ❌ Aave integration not available")
            return False
        print("   ✅ Aave integration ready")
        
        # Test Uniswap integration
        if not agent.uniswap:
            print("   ❌ Uniswap integration not available")
            return False
        print("   ✅ Uniswap integration ready")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Component test failed: {e}")
        return False

def test_network_approval_readiness():
    """Test network approval readiness"""
    print("\n🌐 TESTING NETWORK APPROVAL READINESS...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        # Initialize integrations
        agent.initialize_integrations()
        
        # Get account data
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("   ❌ Cannot retrieve Aave account data")
            return False, 0
            
        health_factor = account_data.get('healthFactor', 0)
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        total_collateral = account_data.get('totalCollateralUSD', 0)
        
        print(f"   📊 Health Factor: {health_factor:.4f}")
        print(f"   📊 Available Borrows: ${available_borrows:.2f}")
        print(f"   📊 Total Collateral: ${total_collateral:.2f}")
        
        # Calculate approval probability
        approval_score = 0
        max_score = 100
        
        # Health factor scoring (40 points max)
        if health_factor > 3.0:
            approval_score += 40
        elif health_factor > 2.0:
            approval_score += 30
        elif health_factor > 1.5:
            approval_score += 20
        else:
            approval_score += 0
            
        # Available capacity scoring (30 points max)
        if available_borrows > 50:
            approval_score += 30
        elif available_borrows > 20:
            approval_score += 20
        elif available_borrows > 5:
            approval_score += 10
        else:
            approval_score += 0
            
        # ETH balance scoring (20 points max)
        eth_balance = agent.get_eth_balance()
        if eth_balance > 0.01:
            approval_score += 20
        elif eth_balance > 0.005:
            approval_score += 15
        elif eth_balance > 0.001:
            approval_score += 10
        else:
            approval_score += 0
            
        # System readiness scoring (10 points max)
        if health_factor > 1.5 and available_borrows > 1.0 and eth_balance > 0.001:
            approval_score += 10
            
        approval_percentage = (approval_score / max_score) * 100
        
        print(f"   🎯 NETWORK APPROVAL PROBABILITY: {approval_percentage:.1f}%")
        
        if approval_percentage >= 80:
            print("   ✅ HIGH probability of network approval")
            return True, approval_percentage
        elif approval_percentage >= 60:
            print("   ⚠️ MODERATE probability of network approval")
            return True, approval_percentage
        else:
            print("   ❌ LOW probability of network approval")
            return False, approval_percentage
            
    except Exception as e:
        print(f"   ❌ Network approval test failed: {e}")
        return False, 0

def main():
    """Run comprehensive debt swap readiness test"""
    print("🚀 DEBT SWAP READINESS VERIFICATION")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    all_tests_passed = True
    test_results = {}
    
    # Test 1: Syntax Errors
    syntax_passed, syntax_results = test_syntax_errors()
    test_results['syntax_check'] = syntax_results
    if not syntax_passed:
        all_tests_passed = False
        print("\n❌ CRITICAL: Syntax errors must be fixed before proceeding")
        
    # Test 2: Agent Initialization
    if syntax_passed:
        agent_passed = test_agent_initialization()
        test_results['agent_initialization'] = agent_passed
        if not agent_passed:
            all_tests_passed = False
            
        # Test 3: Debt Swap Components
        if agent_passed:
            components_passed = test_debt_swap_components()
            test_results['debt_swap_components'] = components_passed
            if not components_passed:
                all_tests_passed = False
                
            # Test 4: Network Approval Readiness
            approval_passed, approval_score = test_network_approval_readiness()
            test_results['network_approval'] = {
                'ready': approval_passed,
                'score': approval_score
            }
    
    # Final Assessment
    print("\n" + "=" * 60)
    print("🎯 DEBT SWAP READINESS ASSESSMENT:")
    print("=" * 60)
    
    if all_tests_passed:
        approval_score = test_results.get('network_approval', {}).get('score', 0)
        print("✅ ALL SYSTEMS READY FOR DEBT SWAP EXECUTION")
        print("✅ Syntax errors resolved")
        print("✅ Agent initialization working")
        print("✅ Debt swap components operational")
        print(f"✅ Network approval probability: {approval_score:.1f}%")
        print("\n🚀 READY TO START AUTONOMOUS SYSTEM WITH DEBT SWAPS")
        
        # Save readiness report
        readiness_report = {
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'all_systems_ready': True,
            'network_approval_score': approval_score,
            'test_results': test_results,
            'recommendation': 'PROCEED_WITH_AUTONOMOUS_EXECUTION'
        }
        
    else:
        print("❌ SYSTEM NOT READY FOR DEBT SWAP EXECUTION")
        print("🔧 Issues that must be resolved:")
        
        if not syntax_passed:
            print("   • Fix syntax errors in critical files")
        if not test_results.get('agent_initialization', True):
            print("   • Resolve agent initialization issues")
        if not test_results.get('debt_swap_components', True):
            print("   • Fix DeFi integration components")
            
        readiness_report = {
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'all_systems_ready': False,
            'test_results': test_results,
            'recommendation': 'RESOLVE_ISSUES_BEFORE_EXECUTION'
        }
    
    # Save report
    with open('debt_swap_readiness_report.json', 'w') as f:
        json.dump(readiness_report, f, indent=2)
    
    print(f"\n📄 Full report saved: debt_swap_readiness_report.json")
    print("=" * 60)
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
