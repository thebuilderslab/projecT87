
#!/usr/bin/env python3
"""
Comprehensive Autonomous System Diagnostic
Checks all components needed for full autonomous operation
"""

import os
import sys
import time
from web3 import Web3
from datetime import datetime

def check_environment_variables():
    """Check critical environment variables"""
    print("🔍 Checking Environment Variables...")
    
    required_vars = {
        'PRIVATE_KEY': 'Wallet private key',
        'COINMARKETCAP_API_KEY': 'Price data API key',
        'NETWORK_MODE': 'Network mode (should be mainnet)'
    }
    
    results = {}
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == 'PRIVATE_KEY':
                results[var] = f"✅ Set (length: {len(value)})"
            elif var == 'COINMARKETCAP_API_KEY':
                results[var] = f"✅ Set (length: {len(value)})"
            else:
                results[var] = f"✅ Set: {value}"
        else:
            results[var] = "❌ Not set"
    
    return results

def check_agent_initialization():
    """Check if agent can initialize properly"""
    print("🔍 Checking Agent Initialization...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        results = {
            'agent_created': '✅ Agent created successfully',
            'wallet_address': f"✅ Wallet: {agent.address}",
            'network_connected': f"✅ Connected to chain {agent.w3.eth.chain_id}",
            'eth_balance': f"✅ ETH Balance: {agent.get_eth_balance():.6f} ETH"
        }
        
        # Test integration initialization
        integration_success = agent.initialize_integrations()
        if integration_success:
            results['integrations'] = '✅ DeFi integrations initialized'
            
            # Check individual integrations
            if agent.aave:
                results['aave'] = '✅ Aave integration ready'
            else:
                results['aave'] = '❌ Aave integration failed'
                
            if agent.uniswap:
                results['uniswap'] = '✅ Uniswap integration ready'
            else:
                results['uniswap'] = '❌ Uniswap integration failed'
                
            if agent.health_monitor:
                results['health_monitor'] = '✅ Health monitor ready'
            else:
                results['health_monitor'] = '❌ Health monitor failed'
        else:
            results['integrations'] = '❌ DeFi integrations failed'
            
        return results, agent
        
    except Exception as e:
        return {'error': f"❌ Agent initialization failed: {e}"}, None

def check_aave_position(agent):
    """Check current Aave position"""
    print("🔍 Checking Aave Position...")
    
    try:
        # Get fresh Aave data
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(
            address=agent.aave_pool_address,
            abi=pool_abi
        )
        
        account_data = pool_contract.functions.getUserAccountData(agent.address).call()
        
        collateral_usd = account_data[0] / (10**8)
        debt_usd = account_data[1] / (10**8)
        available_borrows_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        return {
            'collateral': f"✅ Collateral: ${collateral_usd:,.2f}",
            'debt': f"✅ Debt: ${debt_usd:,.2f}",
            'available_borrows': f"✅ Available Borrows: ${available_borrows_usd:,.2f}",
            'health_factor': f"✅ Health Factor: {health_factor:.4f}",
            'position_ready': '✅ Position suitable for autonomous operations' if collateral_usd > 100 else '⚠️ Position too small for operations'
        }
        
    except Exception as e:
        return {'error': f"❌ Aave position check failed: {e}"}

def check_autonomous_readiness():
    """Check if system is ready for autonomous operation"""
    print("🔍 Checking Autonomous Readiness...")
    
    readiness_checks = {
        'baseline_file': os.path.exists('agent_baseline.json'),
        'emergency_stop': not os.path.exists('EMERGENCY_STOP_ACTIVE.flag'),
        'performance_log': os.path.exists('performance_log.json')
    }
    
    results = {}
    for check, status in readiness_checks.items():
        results[check] = "✅ Ready" if status else "❌ Not ready"
    
    return results

def main():
    """Run comprehensive diagnostic"""
    print("🏥 AUTONOMOUS SYSTEM DIAGNOSTIC")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    # Check environment
    print("\n1. ENVIRONMENT VARIABLES:")
    env_results = check_environment_variables()
    for var, result in env_results.items():
        print(f"   {var}: {result}")
    
    # Check agent
    print("\n2. AGENT INITIALIZATION:")
    agent_results, agent = check_agent_initialization()
    for check, result in agent_results.items():
        print(f"   {check}: {result}")
    
    # Check Aave position if agent is available
    if agent:
        print("\n3. AAVE POSITION:")
        aave_results = check_aave_position(agent)
        for check, result in aave_results.items():
            print(f"   {check}: {result}")
    
    # Check autonomous readiness
    print("\n4. AUTONOMOUS READINESS:")
    readiness_results = check_autonomous_readiness()
    for check, result in readiness_results.items():
        print(f"   {check}: {result}")
    
    # Final assessment
    print("\n" + "=" * 60)
    print("🎯 FINAL ASSESSMENT:")
    
    critical_issues = []
    
    # Check for critical environment issues
    if '❌' in str(env_results.values()):
        critical_issues.append("Missing environment variables")
    
    # Check for agent issues
    if '❌' in str(agent_results.values()):
        critical_issues.append("Agent initialization problems")
    
    # Check for Aave issues
    if agent and '❌' in str(aave_results.values()):
        critical_issues.append("Aave position issues")
    
    if critical_issues:
        print("❌ SYSTEM NOT READY FOR AUTONOMOUS OPERATION")
        print("🔧 Issues to fix:")
        for issue in critical_issues:
            print(f"   • {issue}")
    else:
        print("✅ SYSTEM READY FOR AUTONOMOUS OPERATION")
        print("🚀 All critical components are functional")
        print("💡 You can start autonomous mode with confidence")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
