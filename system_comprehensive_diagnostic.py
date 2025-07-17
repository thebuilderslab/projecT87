
#!/usr/bin/env python3
"""
Comprehensive System Diagnostic for Complete Autonomous DeFi System
Checks all components, functions, and integrations for proper operation
"""

import os
import sys
import time
import json
import traceback
import subprocess
import requests
from datetime import datetime

class ComprehensiveSystemDiagnostic:
    def __init__(self):
        self.report = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'overall_status': 'CHECKING',
            'critical_issues': [],
            'warnings': [],
            'component_status': {},
            'function_tests': {},
            'recommendations': []
        }
        
    def run_full_diagnostic(self):
        """Run complete system diagnostic"""
        print("🔍 COMPREHENSIVE AUTONOMOUS SYSTEM DIAGNOSTIC")
        print("=" * 80)
        
        try:
            # Component checks
            self.check_environment_variables()
            self.check_file_integrity()
            self.check_agent_initialization()
            self.check_dashboard_functionality()
            self.check_defi_integrations()
            self.check_autonomous_functions()
            self.check_trigger_system()
            self.check_emergency_systems()
            self.check_network_connectivity()
            
            # Generate final assessment
            self.generate_final_assessment()
            
        except Exception as e:
            self.report['critical_issues'].append(f"Diagnostic failed: {e}")
            self.report['overall_status'] = 'FAILED'
            
        return self.report
        
    def check_environment_variables(self):
        """Check all required environment variables"""
        print("\n🔍 CHECKING ENVIRONMENT VARIABLES...")
        
        required_vars = {
            'PRIVATE_KEY': 'Wallet private key for mainnet operations',
            'COINMARKETCAP_API_KEY': 'Price data API key',
            'NETWORK_MODE': 'Network mode (should be mainnet)'
        }
        
        env_status = {}
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                if var == 'PRIVATE_KEY':
                    env_status[var] = f"✅ Set (length: {len(value)})"
                    if len(value) != 66 or not value.startswith('0x'):
                        self.report['warnings'].append(f"{var} may have incorrect format")
                elif var == 'NETWORK_MODE':
                    env_status[var] = f"✅ Set: {value}"
                    if value != 'mainnet':
                        self.report['warnings'].append(f"Network mode is {value}, expected 'mainnet'")
                else:
                    env_status[var] = f"✅ Set (length: {len(value)})"
            else:
                env_status[var] = "❌ Not set"
                self.report['critical_issues'].append(f"Missing {var}: {description}")
                
        self.report['component_status']['environment'] = env_status
        print(f"   Environment variables: {len([v for v in env_status.values() if '✅' in v])}/{len(required_vars)} configured")
        
    def check_file_integrity(self):
        """Check critical files exist and are valid"""
        print("\n🔍 CHECKING FILE INTEGRITY...")
        
        critical_files = {
            'arbitrum_testnet_agent.py': 'Main agent implementation',
            'web_dashboard.py': 'Dashboard interface',
            'complete_autonomous_launcher.py': 'System launcher',
            'aave_integration.py': 'Aave DeFi integration',
            'uniswap_integration.py': 'Uniswap integration',
            'aave_health_monitor.py': 'Health monitoring',
            'gas_fee_calculator.py': 'Gas optimization'
        }
        
        file_status = {}
        for file, description in critical_files.items():
            if os.path.exists(file):
                try:
                    # Check for syntax errors
                    with open(file, 'r') as f:
                        content = f.read()
                        compile(content, file, 'exec')
                    file_status[file] = "✅ Valid syntax"
                except SyntaxError as e:
                    file_status[file] = f"❌ Syntax error: {e}"
                    self.report['critical_issues'].append(f"Syntax error in {file}: {e}")
                except Exception as e:
                    file_status[file] = f"⚠️ Issue: {e}"
                    self.report['warnings'].append(f"File issue in {file}: {e}")
            else:
                file_status[file] = "❌ Missing"
                self.report['critical_issues'].append(f"Missing critical file: {file}")
                
        self.report['component_status']['files'] = file_status
        print(f"   File integrity: {len([v for v in file_status.values() if '✅' in v])}/{len(critical_files)} files valid")
        
    def check_agent_initialization(self):
        """Test agent initialization"""
        print("\n🔍 CHECKING AGENT INITIALIZATION...")
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            agent_tests = {
                'initialization': '✅ Agent created successfully',
                'wallet_address': f"✅ Wallet: {agent.address}",
                'network_connection': f"✅ Connected to chain {agent.w3.eth.chain_id}",
                'eth_balance': f"✅ ETH Balance: {agent.get_eth_balance():.6f} ETH"
            }
            
            # Test DeFi integrations
            try:
                integration_success = agent.initialize_integrations()
                if integration_success:
                    agent_tests['integrations'] = '✅ DeFi integrations initialized'
                    
                    # Test individual components
                    if hasattr(agent, 'aave') and agent.aave:
                        agent_tests['aave'] = '✅ Aave integration ready'
                    else:
                        agent_tests['aave'] = '❌ Aave integration failed'
                        self.report['critical_issues'].append("Aave integration not working")
                        
                    if hasattr(agent, 'uniswap') and agent.uniswap:
                        agent_tests['uniswap'] = '✅ Uniswap integration ready'
                    else:
                        agent_tests['uniswap'] = '❌ Uniswap integration failed'
                        self.report['critical_issues'].append("Uniswap integration not working")
                        
                    if hasattr(agent, 'health_monitor') and agent.health_monitor:
                        agent_tests['health_monitor'] = '✅ Health monitor ready'
                    else:
                        agent_tests['health_monitor'] = '❌ Health monitor failed'
                        self.report['critical_issues'].append("Health monitor not working")
                else:
                    agent_tests['integrations'] = '❌ DeFi integrations failed'
                    self.report['critical_issues'].append("DeFi integrations failed to initialize")
                    
            except Exception as e:
                agent_tests['integrations'] = f'❌ Integration error: {e}'
                self.report['critical_issues'].append(f"Integration initialization error: {e}")
                
            self.report['component_status']['agent'] = agent_tests
            
        except Exception as e:
            self.report['critical_issues'].append(f"Agent initialization failed: {e}")
            self.report['component_status']['agent'] = {'error': f"❌ Failed to initialize: {e}"}
            
        print(f"   Agent initialization: {'✅ Success' if 'error' not in self.report['component_status']['agent'] else '❌ Failed'}")
        
    def check_dashboard_functionality(self):
        """Test dashboard functionality"""
        print("\n🔍 CHECKING DASHBOARD FUNCTIONALITY...")
        
        dashboard_tests = {}
        
        # Check if dashboard can start
        try:
            # Test import
            import web_dashboard
            dashboard_tests['import'] = '✅ Dashboard imports successfully'
            
            # Test critical functions
            try:
                # Test get_live_agent_data function
                live_data = web_dashboard.get_live_agent_data()
                if live_data:
                    dashboard_tests['live_data'] = '✅ Live data function working'
                else:
                    dashboard_tests['live_data'] = '⚠️ Live data returns None'
                    self.report['warnings'].append("Dashboard live data function returns None")
            except Exception as e:
                dashboard_tests['live_data'] = f'❌ Live data error: {e}'
                self.report['critical_issues'].append(f"Dashboard live data error: {e}")
                
        except Exception as e:
            dashboard_tests['import'] = f'❌ Import error: {e}'
            self.report['critical_issues'].append(f"Dashboard import error: {e}")
            
        self.report['component_status']['dashboard'] = dashboard_tests
        print(f"   Dashboard functionality: {'✅ Working' if all('✅' in v for v in dashboard_tests.values()) else '⚠️ Issues detected'}")
        
    def check_defi_integrations(self):
        """Test DeFi protocol integrations"""
        print("\n🔍 CHECKING DEFI INTEGRATIONS...")
        
        defi_tests = {}
        
        # Test Aave integration
        try:
            from aave_integration import AaveArbitrumIntegration
            defi_tests['aave_import'] = '✅ Aave integration imports'
        except Exception as e:
            defi_tests['aave_import'] = f'❌ Aave import error: {e}'
            self.report['critical_issues'].append(f"Aave integration import error: {e}")
            
        # Test Uniswap integration
        try:
            from uniswap_integration import UniswapArbitrumIntegration
            defi_tests['uniswap_import'] = '✅ Uniswap integration imports'
        except Exception as e:
            defi_tests['uniswap_import'] = f'❌ Uniswap import error: {e}'
            self.report['critical_issues'].append(f"Uniswap integration import error: {e}")
            
        # Test Health Monitor
        try:
            from aave_health_monitor import AaveHealthMonitor
            defi_tests['health_monitor_import'] = '✅ Health monitor imports'
        except Exception as e:
            defi_tests['health_monitor_import'] = f'❌ Health monitor import error: {e}'
            self.report['critical_issues'].append(f"Health monitor import error: {e}")
            
        # Test Gas Calculator
        try:
            from gas_fee_calculator import ArbitrumGasCalculator
            defi_tests['gas_calculator_import'] = '✅ Gas calculator imports'
        except Exception as e:
            defi_tests['gas_calculator_import'] = f'❌ Gas calculator import error: {e}'
            self.report['critical_issues'].append(f"Gas calculator import error: {e}")
            
        self.report['component_status']['defi_integrations'] = defi_tests
        print(f"   DeFi integrations: {len([v for v in defi_tests.values() if '✅' in v])}/{len(defi_tests)} working")
        
    def check_autonomous_functions(self):
        """Test autonomous system functions"""
        print("\n🔍 CHECKING AUTONOMOUS FUNCTIONS...")
        
        function_tests = {}
        
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            # Test critical autonomous functions
            critical_functions = [
                'run_real_defi_task',
                'execute_autonomous_sequence_enhanced',
                'check_wallet_readiness_for_defi',
                'get_arb_price',
                'get_optimized_gas_params',
                'update_baseline_after_success',
                'is_operation_on_cooldown'
            ]
            
            for func_name in critical_functions:
                if hasattr(agent, func_name):
                    function_tests[func_name] = '✅ Function exists'
                else:
                    function_tests[func_name] = '❌ Function missing'
                    self.report['critical_issues'].append(f"Missing critical function: {func_name}")
                    
        except Exception as e:
            function_tests['agent_creation'] = f'❌ Cannot create agent: {e}'
            self.report['critical_issues'].append(f"Cannot test autonomous functions: {e}")
            
        self.report['function_tests']['autonomous_functions'] = function_tests
        print(f"   Autonomous functions: {len([v for v in function_tests.values() if '✅' in v])}/{len(function_tests)} available")
        
    def check_trigger_system(self):
        """Test trigger and monitoring system"""
        print("\n🔍 CHECKING TRIGGER SYSTEM...")
        
        trigger_tests = {}
        
        # Check baseline file
        if os.path.exists('agent_baseline.json'):
            try:
                with open('agent_baseline.json', 'r') as f:
                    baseline_data = json.load(f)
                if 'last_collateral_value_usd' in baseline_data:
                    trigger_tests['baseline_file'] = f"✅ Baseline: ${baseline_data['last_collateral_value_usd']:.2f}"
                else:
                    trigger_tests['baseline_file'] = '⚠️ Baseline file missing data'
                    self.report['warnings'].append("Baseline file exists but missing collateral data")
            except Exception as e:
                trigger_tests['baseline_file'] = f'❌ Baseline file error: {e}'
                self.report['warnings'].append(f"Baseline file error: {e}")
        else:
            trigger_tests['baseline_file'] = '⚠️ No baseline file found'
            self.report['warnings'].append("No baseline file found - will be created on first run")
            
        # Check performance log
        if os.path.exists('performance_log.json'):
            trigger_tests['performance_log'] = '✅ Performance log exists'
        else:
            trigger_tests['performance_log'] = '⚠️ No performance log'
            self.report['warnings'].append("No performance log found")
            
        self.report['component_status']['trigger_system'] = trigger_tests
        print(f"   Trigger system: {'✅ Ready' if all('❌' not in v for v in trigger_tests.values()) else '⚠️ Needs setup'}")
        
    def check_emergency_systems(self):
        """Test emergency stop and safety systems"""
        print("\n🔍 CHECKING EMERGENCY SYSTEMS...")
        
        emergency_tests = {}
        
        # Check emergency stop functionality
        try:
            import emergency_stop
            emergency_tests['emergency_stop_module'] = '✅ Emergency stop module available'
        except Exception as e:
            emergency_tests['emergency_stop_module'] = f'❌ Emergency stop error: {e}'
            self.report['warnings'].append(f"Emergency stop module error: {e}")
            
        # Check emergency flag
        emergency_active = os.path.exists('EMERGENCY_STOP_ACTIVE.flag')
        if emergency_active:
            emergency_tests['emergency_flag'] = '⚠️ Emergency stop is ACTIVE'
            self.report['warnings'].append("Emergency stop is currently active")
        else:
            emergency_tests['emergency_flag'] = '✅ Emergency stop not active'
            
        self.report['component_status']['emergency_systems'] = emergency_tests
        print(f"   Emergency systems: {'✅ Ready' if not emergency_active else '⚠️ Emergency stop active'}")
        
    def check_network_connectivity(self):
        """Test network connectivity and RPC endpoints"""
        print("\n🔍 CHECKING NETWORK CONNECTIVITY...")
        
        network_tests = {}
        
        # Test Arbitrum mainnet RPC
        test_rpcs = [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.publicnode.com",
            "https://arbitrum.llamarpc.com"
        ]
        
        working_rpcs = 0
        for rpc in test_rpcs:
            try:
                from web3 import Web3
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
                if w3.is_connected():
                    chain_id = w3.eth.chain_id
                    if chain_id == 42161:  # Arbitrum mainnet
                        working_rpcs += 1
                        network_tests[f'rpc_{working_rpcs}'] = f'✅ {rpc[:30]}... working'
                    else:
                        network_tests[f'rpc_error'] = f'❌ Wrong chain ID: {chain_id}'
                else:
                    network_tests[f'rpc_error'] = f'❌ Cannot connect to {rpc[:30]}...'
            except Exception as e:
                network_tests[f'rpc_error'] = f'❌ RPC error: {e}'
                
        if working_rpcs == 0:
            self.report['critical_issues'].append("No working Arbitrum mainnet RPC endpoints")
        elif working_rpcs < 2:
            self.report['warnings'].append("Limited RPC endpoint availability")
            
        # Test CoinMarketCap API
        try:
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            if api_key:
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
                headers = {'X-CMC_PRO_API_KEY': api_key}
                params = {'symbol': 'ARB', 'convert': 'USD'}
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    network_tests['coinmarketcap_api'] = '✅ CoinMarketCap API working'
                else:
                    network_tests['coinmarketcap_api'] = f'❌ API error: {response.status_code}'
                    self.report['warnings'].append("CoinMarketCap API not responding properly")
            else:
                network_tests['coinmarketcap_api'] = '❌ No API key found'
        except Exception as e:
            network_tests['coinmarketcap_api'] = f'❌ API test error: {e}'
            self.report['warnings'].append(f"CoinMarketCap API test error: {e}")
            
        self.report['component_status']['network'] = network_tests
        print(f"   Network connectivity: {working_rpcs} RPC endpoints working")
        
    def generate_final_assessment(self):
        """Generate final system assessment"""
        print("\n" + "=" * 80)
        print("🎯 FINAL SYSTEM ASSESSMENT")
        print("=" * 80)
        
        critical_count = len(self.report['critical_issues'])
        warning_count = len(self.report['warnings'])
        
        if critical_count == 0:
            if warning_count == 0:
                self.report['overall_status'] = 'EXCELLENT'
                print("🎉 SYSTEM STATUS: EXCELLENT")
                print("✅ All systems operational and ready for autonomous operation")
                print("✅ No critical issues or warnings detected")
            else:
                self.report['overall_status'] = 'GOOD'
                print("✅ SYSTEM STATUS: GOOD")
                print("✅ All critical systems operational")
                print(f"⚠️ {warning_count} minor warning(s) detected")
        else:
            if critical_count <= 2:
                self.report['overall_status'] = 'NEEDS_ATTENTION'
                print("⚠️ SYSTEM STATUS: NEEDS ATTENTION")
                print(f"❌ {critical_count} critical issue(s) need fixing")
            else:
                self.report['overall_status'] = 'CRITICAL'
                print("❌ SYSTEM STATUS: CRITICAL")
                print(f"❌ {critical_count} critical issues prevent operation")
                
        # Display issues
        if self.report['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES TO FIX ({critical_count}):")
            for i, issue in enumerate(self.report['critical_issues'], 1):
                print(f"   {i}. {issue}")
                
        if self.report['warnings']:
            print(f"\n⚠️ WARNINGS ({warning_count}):")
            for i, warning in enumerate(self.report['warnings'], 1):
                print(f"   {i}. {warning}")
                
        # Generate recommendations
        self.generate_recommendations()
        
        print("=" * 80)
        
    def generate_recommendations(self):
        """Generate specific recommendations"""
        if self.report['critical_issues']:
            print(f"\n💡 IMMEDIATE ACTIONS REQUIRED:")
            
            for issue in self.report['critical_issues']:
                if 'PRIVATE_KEY' in issue:
                    print("   • Add your mainnet private key to Replit Secrets")
                elif 'COINMARKETCAP_API_KEY' in issue:
                    print("   • Add your CoinMarketCap API key to Replit Secrets")
                elif 'Syntax error' in issue:
                    print("   • Fix syntax errors in code files")
                elif 'integration' in issue.lower():
                    print("   • Check DeFi integration dependencies")
                elif 'RPC' in issue:
                    print("   • Check network connectivity and RPC endpoints")
                    
        if self.report['warnings']:
            print(f"\n🔧 RECOMMENDED IMPROVEMENTS:")
            for warning in self.report['warnings']:
                if 'baseline' in warning.lower():
                    print("   • Baseline will be auto-created on first autonomous run")
                elif 'emergency' in warning.lower():
                    print("   • Clear emergency stop if not needed")
                elif 'API' in warning:
                    print("   • Verify API credentials and connectivity")
                    
        # Always provide system readiness guidance
        if self.report['overall_status'] in ['EXCELLENT', 'GOOD']:
            print(f"\n🚀 SYSTEM READY FOR OPERATION:")
            print("   • Run: python complete_autonomous_launcher.py")
            print("   • Monitor dashboard at: http://localhost:5000")
            print("   • Emergency stop available if needed")
            
    def save_report(self):
        """Save diagnostic report to file"""
        try:
            with open('system_diagnostic_report.json', 'w') as f:
                json.dump(self.report, f, indent=2)
            print(f"\n📄 Diagnostic report saved to: system_diagnostic_report.json")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

def main():
    """Run comprehensive system diagnostic"""
    diagnostic = ComprehensiveSystemDiagnostic()
    
    try:
        report = diagnostic.run_full_diagnostic()
        diagnostic.save_report()
        
        # Return appropriate exit code
        if report['overall_status'] in ['EXCELLENT', 'GOOD']:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
