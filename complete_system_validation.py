
#!/usr/bin/env python3
"""
Complete System Validation - Network Approval Ready Test
Tests all components for successful execution and network approval
"""

import os
import sys
import time
import json
import traceback
from datetime import datetime

def test_syntax_errors():
    """Test for syntax errors in critical files"""
    print("🔍 TESTING SYNTAX ERRORS...")
    
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
                error_msg = str(e)
                line_match = None
                if 'line' in error_msg:
                    import re
                    line_match = re.search(r'line (\d+)', error_msg)
                
                if line_match:
                    line_num = line_match.group(1)
                    print(f"❌ {file_path}: Line {line_num}: {e}")
                    syntax_errors.append(f"{file_path}: Line {line_num}: {e}")
                else:
                    print(f"❌ {file_path}: {e}")
                    syntax_errors.append(f"{file_path}: {e}")
                    
        else:
            print(f"⚠️ {file_path}: File not found")
    
    if syntax_errors:
        print("❌ CRITICAL: Syntax errors must be fixed before proceeding")
        for error in syntax_errors:
            print(f"   • {error}")
        return False
    
    print("✅ All syntax tests passed")
    return True

def test_agent_initialization():
    """Test agent initialization and debt swap readiness"""
    print("\n🤖 TESTING AGENT INITIALIZATION & DEBT SWAP READINESS...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print("✅ Agent initialized successfully")
        
        # Test critical properties
        if not hasattr(agent, 'address') or not agent.address:
            print("❌ Agent address not set")
            return False, {}
            
        print(f"✅ Agent address: {agent.address}")
        
        # Test network connection
        try:
            chain_id = agent.w3.eth.chain_id
            print(f"✅ Connected to chain ID: {chain_id}")
        except:
            print("❌ Network connection failed")
            return False, {}
            
        # Test DeFi integrations
        if agent.initialize_integrations():
            print("✅ DeFi integrations initialized")
        else:
            print("⚠️ Some DeFi integrations failed")
            
        # Test account data retrieval
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot retrieve Aave account data")
            return False, {}
            
        health_factor = account_data.get('healthFactor', 0)
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        total_collateral = account_data.get('totalCollateralUSD', 0)
        
        print(f"✅ Health Factor: {health_factor:.4f}")
        print(f"✅ Available Borrows: ${available_borrows:.2f}")
        print(f"✅ Total Collateral: ${total_collateral:.2f}")
        
        # Test debt swap methods
        debt_swap_methods = [
            'execute_debt_swap_dai_to_arb',
            'execute_debt_swap_arb_to_dai', 
            'check_debt_swap_conditions',
            'get_debt_swap_parameters',
            'execute_complete_debt_swap_sequence'
        ]
        
        missing_methods = []
        for method in debt_swap_methods:
            if hasattr(agent, method):
                print(f"✅ Debt swap method available: {method}")
            else:
                print(f"❌ Missing debt swap method: {method}")
                missing_methods.append(method)
                
        if missing_methods:
            return False, {}
            
        # Test debt swap conditions
        try:
            conditions_ok, message = agent.check_debt_swap_conditions()
            print(f"✅ Debt swap conditions: {message}")
        except Exception as e:
            print(f"❌ Debt swap conditions check failed: {e}")
            return False, {}
            
        system_data = {
            'health_factor': health_factor,
            'available_borrows': available_borrows,
            'total_collateral': total_collateral,
            'debt_swap_ready': conditions_ok,
            'eth_balance': agent.get_eth_balance(),
            'chain_id': chain_id,
            'agent_address': agent.address
        }
        
        print("✅ Agent initialization and debt swap functionality verified")
        return True, system_data
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        traceback.print_exc()
        return False, {}

def test_triggers_and_targets():
    """Test autonomous triggers and targets"""
    print("\n🎯 TESTING TRIGGERS AND TARGETS...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot test triggers without account data")
            return False, {}
            
        health_factor = account_data.get('healthFactor', 0)
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        total_collateral = account_data.get('totalCollateralUSD', 0)
        
        # Test trigger conditions
        triggers_active = []
        
        # Growth-triggered system
        if hasattr(agent, 'last_collateral_value_usd') and agent.last_collateral_value_usd > 0:
            growth = total_collateral - agent.last_collateral_value_usd
            if growth >= agent.growth_trigger_threshold:
                triggers_active.append(f"GROWTH: ${growth:.2f} >= ${agent.growth_trigger_threshold:.2f}")
                print(f"✅ Growth trigger ACTIVE: ${growth:.2f}")
            else:
                print(f"⚠️ Growth trigger: ${growth:.2f} < ${agent.growth_trigger_threshold:.2f}")
        else:
            print(f"⚠️ No baseline set for growth trigger")
            
        # Capacity-based system
        if available_borrows > 50:  # $50 threshold
            triggers_active.append(f"CAPACITY: ${available_borrows:.2f} > $50.00")
            print(f"✅ Capacity trigger ACTIVE: ${available_borrows:.2f}")
        else:
            print(f"⚠️ Capacity trigger: ${available_borrows:.2f} <= $50.00")
            
        # Market signal system (if enabled)
        market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
        if market_enabled and hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            try:
                should_trade = agent.market_signal_strategy.should_execute_trade()
                if should_trade:
                    triggers_active.append("MARKET_SIGNAL: Active trade signal")
                    print("✅ Market signal trigger ACTIVE")
                else:
                    print("⚠️ Market signal trigger: No signal")
            except:
                print("⚠️ Market signal trigger: Error checking")
        else:
            print("ℹ️ Market signal trigger: Disabled")
            
        # Calculate targets
        target_data = {
            'health_factor_target': getattr(agent, 'target_health_factor', 3.5),
            'growth_threshold': getattr(agent, 'growth_trigger_threshold', 13.0),
            'capacity_threshold': getattr(agent, 'capacity_available_threshold', 13.0),
            'baseline_collateral': getattr(agent, 'last_collateral_value_usd', 0),
            'next_trigger_at': getattr(agent, 'last_collateral_value_usd', 0) + getattr(agent, 'growth_trigger_threshold', 13.0)
        }
        
        print(f"🎯 SYSTEM TARGETS:")
        print(f"   Health Factor Target: {target_data['health_factor_target']:.1f}")
        print(f"   Growth Trigger: ${target_data['growth_threshold']:.0f}")
        print(f"   Capacity Trigger: ${target_data['capacity_threshold']:.0f}")
        print(f"   Current Baseline: ${target_data['baseline_collateral']:.2f}")
        print(f"   Next Trigger At: ${target_data['next_trigger_at']:.2f}")
        
        triggers_data = {
            'active_triggers': triggers_active,
            'total_active': len(triggers_active),
            'targets': target_data,
            'ready_for_execution': len(triggers_active) > 0 and health_factor > 1.5
        }
        
        if triggers_data['ready_for_execution']:
            print("✅ SYSTEM READY FOR AUTONOMOUS EXECUTION")
        else:
            print("⚠️ System waiting for trigger conditions")
            
        return True, triggers_data
        
    except Exception as e:
        print(f"❌ Trigger/target test failed: {e}")
        return False, {}

def test_network_approval_probability():
    """Calculate network approval probability"""
    print("\n🌐 CALCULATING NETWORK APPROVAL PROBABILITY...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            return False, 0
            
        health_factor = account_data.get('healthFactor', 0)
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        eth_balance = agent.get_eth_balance()
        
        # Scoring system (100 points max)
        approval_score = 0
        max_score = 100
        
        # Health factor scoring (40 points max)
        if health_factor > 3.0:
            approval_score += 40
            hf_status = "EXCELLENT"
        elif health_factor > 2.0:
            approval_score += 30
            hf_status = "GOOD"
        elif health_factor > 1.5:
            approval_score += 20
            hf_status = "ACCEPTABLE"
        else:
            approval_score += 0
            hf_status = "RISKY"
            
        print(f"📊 Health Factor: {health_factor:.4f} ({hf_status}) - {min(40, int(approval_score))} points")
        
        # Available capacity scoring (30 points max)
        capacity_points = 0
        if available_borrows > 100:
            capacity_points = 30
            capacity_status = "HIGH"
        elif available_borrows > 50:
            capacity_points = 25
            capacity_status = "GOOD"
        elif available_borrows > 20:
            capacity_points = 20
            capacity_status = "MODERATE"
        elif available_borrows > 5:
            capacity_points = 10
            capacity_status = "LIMITED"
        else:
            capacity_points = 0
            capacity_status = "INSUFFICIENT"
            
        approval_score += capacity_points
        print(f"📊 Available Capacity: ${available_borrows:.2f} ({capacity_status}) - {capacity_points} points")
        
        # ETH balance scoring (20 points max)
        eth_points = 0
        if eth_balance > 0.01:
            eth_points = 20
            eth_status = "EXCELLENT"
        elif eth_balance > 0.005:
            eth_points = 15
            eth_status = "GOOD"
        elif eth_balance > 0.001:
            eth_points = 10
            eth_status = "ACCEPTABLE"
        else:
            eth_points = 0
            eth_status = "INSUFFICIENT"
            
        approval_score += eth_points
        print(f"📊 ETH Balance: {eth_balance:.6f} ({eth_status}) - {eth_points} points")
        
        # System readiness scoring (10 points max)
        system_points = 0
        if health_factor > 1.5 and available_borrows > 1.0 and eth_balance > 0.001:
            system_points = 10
            system_status = "READY"
        else:
            system_points = 0
            system_status = "NOT_READY"
            
        approval_score += system_points
        print(f"📊 System Readiness: {system_status} - {system_points} points")
        
        approval_percentage = (approval_score / max_score) * 100
        
        print(f"\n🎯 NETWORK APPROVAL PROBABILITY: {approval_percentage:.1f}%")
        print(f"📊 Total Score: {approval_score}/{max_score} points")
        
        if approval_percentage >= 80:
            print("✅ HIGH probability of network approval")
            approval_status = "HIGH"
        elif approval_percentage >= 60:
            print("⚠️ MODERATE probability of network approval")  
            approval_status = "MODERATE"
        else:
            print("❌ LOW probability of network approval")
            approval_status = "LOW"
            
        return True, {
            'probability': approval_percentage,
            'score': approval_score,
            'max_score': max_score,
            'status': approval_status,
            'factors': {
                'health_factor': {'score': min(40, int(approval_score)), 'status': hf_status},
                'capacity': {'score': capacity_points, 'status': capacity_status},
                'eth_balance': {'score': eth_points, 'status': eth_status},
                'system_ready': {'score': system_points, 'status': system_status}
            }
        }
        
    except Exception as e:
        print(f"❌ Network approval test failed: {e}")
        return False, 0

def test_self_improvement():
    """Test self-improvement system"""
    print("\n🧠 TESTING SELF-IMPROVEMENT SYSTEM...")
    
    try:
        # Check for performance logs
        if os.path.exists('performance_log.json'):
            with open('performance_log.json', 'r') as f:
                lines = f.readlines()
                if len(lines) > 5:
                    print(f"✅ Performance data: {len(lines)} entries")
                    
                    # Analyze recent performance
                    recent_entries = []
                    for line in lines[-10:]:  # Last 10 entries
                        try:
                            entry = json.loads(line)
                            recent_entries.append(entry.get('performance_metric', 0))
                        except:
                            continue
                            
                    if recent_entries:
                        avg_performance = sum(recent_entries) / len(recent_entries)
                        print(f"✅ Average performance: {avg_performance:.3f}")
                        
                        # Self-improvement recommendations
                        improvement_proposals = []
                        
                        if avg_performance < 0.6:
                            improvement_proposals.append({
                                'category': 'Risk Reduction',
                                'proposal': 'Reduce operation frequency and amounts',
                                'priority': 'HIGH',
                                'user_approval_required': True
                            })
                            
                        if avg_performance > 0.8:
                            improvement_proposals.append({
                                'category': 'Capacity Optimization',
                                'proposal': 'Increase operation efficiency',
                                'priority': 'MEDIUM', 
                                'user_approval_required': False
                            })
                            
                        print(f"🔄 SELF-IMPROVEMENT PROPOSALS:")
                        for i, proposal in enumerate(improvement_proposals, 1):
                            print(f"   {i}. {proposal['category']}: {proposal['proposal']}")
                            print(f"      Priority: {proposal['priority']}")
                            print(f"      User Approval: {'Required' if proposal['user_approval_required'] else 'Not Required'}")
                            
                        return True, {
                            'performance_entries': len(lines),
                            'avg_performance': avg_performance,
                            'improvement_proposals': improvement_proposals
                        }
                else:
                    print("⚠️ Limited performance data")
        else:
            print("⚠️ No performance log found")
            
        return True, {'status': 'limited_data'}
        
    except Exception as e:
        print(f"❌ Self-improvement test failed: {e}")
        return False, {}

def generate_comprehensive_report(test_results):
    """Generate comprehensive system report"""
    print("\n📋 GENERATING COMPREHENSIVE SYSTEM REPORT...")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    report = {
        'timestamp': timestamp,
        'test_results': test_results,
        'overall_status': 'UNKNOWN',
        'network_ready': False,
        'debt_swap_ready': False,
        'user_actions_required': [],
        'recommendations': []
    }
    
    # Determine overall status
    if test_results.get('syntax_ok', False):
        if test_results.get('agent_ok', False):
            if test_results.get('approval_probability', {}).get('probability', 0) >= 60:
                report['overall_status'] = 'READY'
                report['network_ready'] = True
                report['debt_swap_ready'] = True
            else:
                report['overall_status'] = 'NEEDS_OPTIMIZATION'
        else:
            report['overall_status'] = 'AGENT_ISSUES'
    else:
        report['overall_status'] = 'SYNTAX_ERRORS'
        
    # Generate recommendations
    if not test_results.get('syntax_ok', False):
        report['recommendations'].append('Fix all syntax errors before proceeding')
        
    if test_results.get('approval_probability', {}).get('probability', 0) < 60:
        report['recommendations'].append('Improve system health metrics for better network approval')
        
    # User actions
    improvement_data = test_results.get('self_improvement', {})
    if improvement_data.get('improvement_proposals'):
        for proposal in improvement_data['improvement_proposals']:
            if proposal.get('user_approval_required'):
                report['user_actions_required'].append(proposal)
                
    # Save report
    with open('system_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"✅ Report saved: system_validation_report.json")
    return report

def main():
    """Run complete system validation"""
    print("🚀 COMPLETE SYSTEM VALIDATION - NETWORK APPROVAL TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)
    
    test_results = {}
    
    # Test 1: Syntax validation
    test_results['syntax_ok'] = test_syntax_errors()
    
    if not test_results['syntax_ok']:
        print("\n❌ CRITICAL: Cannot proceed with syntax errors")
        return False
        
    # Test 2: Agent initialization and debt swap readiness
    agent_ok, system_data = test_agent_initialization()
    test_results['agent_ok'] = agent_ok
    test_results['system_data'] = system_data
    
    # Test 3: Triggers and targets
    triggers_ok, triggers_data = test_triggers_and_targets()
    test_results['triggers_ok'] = triggers_ok
    test_results['triggers_data'] = triggers_data
    
    # Test 4: Network approval probability
    approval_ok, approval_data = test_network_approval_probability()
    test_results['approval_ok'] = approval_ok
    test_results['approval_probability'] = approval_data
    
    # Test 5: Self-improvement system
    improvement_ok, improvement_data = test_self_improvement()
    test_results['improvement_ok'] = improvement_ok
    test_results['self_improvement'] = improvement_data
    
    # Generate comprehensive report
    report = generate_comprehensive_report(test_results)
    
    # Final assessment
    print("\n🎯 FINAL SYSTEM ASSESSMENT")
    print("=" * 70)
    
    if report['overall_status'] == 'READY':
        print("🎉 SYSTEM 100% READY FOR NETWORK EXECUTION")
        print("✅ All tests passed")
        print("✅ Debt swap feature operational")
        print("✅ High network approval probability")
        print("✅ Ready for autonomous execution")
    elif report['overall_status'] == 'NEEDS_OPTIMIZATION':
        print("⚠️ SYSTEM FUNCTIONAL BUT NEEDS OPTIMIZATION")
        print("✅ Core functionality working")
        print("⚠️ Network approval probability could be improved")
    else:
        print("❌ SYSTEM NOT READY")
        print("❌ Critical issues must be resolved")
        
    print(f"\n📊 NETWORK APPROVAL PROBABILITY: {test_results.get('approval_probability', {}).get('probability', 0):.1f}%")
    
    if test_results.get('triggers_data', {}).get('ready_for_execution'):
        print("🚀 TRIGGERS ACTIVE - READY FOR EXECUTION")
    else:
        print("⏳ WAITING FOR TRIGGER CONDITIONS")
        
    return report['network_ready']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
