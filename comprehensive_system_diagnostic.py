
#!/usr/bin/env python3
"""
Comprehensive System Diagnostic for DeFi Agent
Provides complete system state analysis, file contents, and operational status
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any

class ComprehensiveSystemDiagnostic:
    def __init__(self):
        self.diagnostic_data = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'system_info': {},
            'environment': {},
            'file_contents': {},
            'configuration': {},
            'on_chain_state': {},
            'recent_logs': {},
            'agent_status': {},
            'network_status': {},
            'api_status': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

    def collect_system_info(self):
        """Collect basic system information"""
        print("🖥️ Collecting system information...")
        
        self.diagnostic_data['system_info'] = {
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': os.getcwd(),
            'python_path': sys.path[:5],  # First 5 entries
            'executable': sys.executable
        }

    def collect_environment_variables(self):
        """Collect environment variables (sanitized)"""
        print("🌍 Collecting environment variables...")
        
        # Critical environment variables for the system
        env_vars_to_check = [
            'NETWORK_MODE', 'PRIVATE_KEY', 'PRIVATE_KEY2', 
            'COINMARKETCAP_API_KEY', 'COIN_API', 'COIN_API_KEY',
            'MARKET_SIGNAL_ENABLED', 'ARBITRUM_RPC_URL',
            'BTC_DROP_THRESHOLD', 'ARB_RSI_OVERSOLD', 'ARB_RSI_OVERBOUGHT',
            'DAI_TO_ARB_THRESHOLD', 'ARB_TO_DAI_THRESHOLD',
            'REPLIT_DEPLOYMENT', 'REPLIT', 'HOME', 'USER'
        ]
        
        env_status = {}
        for var in env_vars_to_check:
            value = os.getenv(var)
            if value:
                # Sanitize sensitive values
                if 'KEY' in var or 'PRIVATE' in var:
                    sanitized = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "[REDACTED]"
                else:
                    sanitized = value
                
                env_status[var] = {
                    'present': True,
                    'length': len(value),
                    'value': sanitized,
                    'type': type(value).__name__
                }
            else:
                env_status[var] = {
                    'present': False,
                    'length': 0,
                    'value': None,
                    'type': 'NoneType'
                }
        
        self.diagnostic_data['environment'] = env_status

    def collect_file_contents(self):
        """Collect contents of core system files"""
        print("📁 Collecting file contents...")
        
        core_files = [
            'arbitrum_testnet_agent.py',
            'aave_integration.py', 
            'uniswap_integration.py',
            'market_signal_strategy.py',
            'enhanced_market_analyzer.py',
            'main.py',
            '.replit',
            'pyproject.toml',
            'environmental_configuration.py',
            'config_constants.py',
            'gas_fee_calculator.py',
            'aave_health_monitor.py'
        ]
        
        file_contents = {}
        for file_path in core_files:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_contents[file_path] = {
                            'exists': True,
                            'size': len(content),
                            'lines': content.count('\n') + 1,
                            'content': content,
                            'modified_time': os.path.getmtime(file_path)
                        }
                else:
                    file_contents[file_path] = {
                        'exists': False,
                        'error': 'File not found'
                    }
            except Exception as e:
                file_contents[file_path] = {
                    'exists': True,
                    'error': f"Failed to read: {str(e)}"
                }
        
        self.diagnostic_data['file_contents'] = file_contents

    def collect_configuration_files(self):
        """Collect configuration and data files"""
        print("⚙️ Collecting configuration files...")
        
        config_files = [
            'agent_config.json',
            'user_settings.json', 
            'agent_baseline.json',
            'performance_log.json',
            'emergency_stop_log.json',
            'active_swaps.json'
        ]
        
        config_data = {}
        for file_path in config_files:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        if file_path.endswith('.json'):
                            try:
                                content = json.load(f)
                                config_data[file_path] = {
                                    'exists': True,
                                    'type': 'json',
                                    'content': content,
                                    'size': os.path.getsize(file_path)
                                }
                            except json.JSONDecodeError as je:
                                config_data[file_path] = {
                                    'exists': True,
                                    'type': 'invalid_json',
                                    'error': str(je),
                                    'raw_content': f.read()[:1000]  # First 1000 chars
                                }
                        else:
                            config_data[file_path] = {
                                'exists': True,
                                'type': 'text',
                                'content': f.read(),
                                'size': os.path.getsize(file_path)
                            }
                else:
                    config_data[file_path] = {
                        'exists': False
                    }
            except Exception as e:
                config_data[file_path] = {
                    'exists': True,
                    'error': str(e)
                }
        
        self.diagnostic_data['configuration'] = config_data

    def test_agent_initialization(self):
        """Test agent initialization and collect status"""
        print("🤖 Testing agent initialization...")
        
        agent_status = {
            'initialization_attempted': False,
            'initialization_successful': False,
            'errors': [],
            'agent_data': {}
        }
        
        try:
            agent_status['initialization_attempted'] = True
            
            # Import and initialize agent
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            agent_status['initialization_successful'] = True
            agent_status['agent_data'] = {
                'address': getattr(agent, 'address', 'Unknown'),
                'network_mode': getattr(agent, 'network_mode', 'Unknown'),
                'rpc_url': getattr(agent, 'rpc_url', 'Unknown'),
                'chain_id': getattr(agent, 'chain_id', 'Unknown'),
                'has_aave': hasattr(agent, 'aave') and agent.aave is not None,
                'has_uniswap': hasattr(agent, 'uniswap') and agent.uniswap is not None,
                'has_market_strategy': hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy is not None,
                'debt_swap_active': getattr(agent, 'debt_swap_active', False)
            }
            
            # Test Web3 connection
            if hasattr(agent, 'w3') and agent.w3:
                try:
                    block_number = agent.w3.eth.block_number
                    gas_price = agent.w3.eth.gas_price
                    agent_status['agent_data']['web3_connected'] = True
                    agent_status['agent_data']['latest_block'] = block_number
                    agent_status['agent_data']['gas_price_gwei'] = agent.w3.from_wei(gas_price, 'gwei')
                except Exception as w3_error:
                    agent_status['agent_data']['web3_connected'] = False
                    agent_status['agent_data']['web3_error'] = str(w3_error)
            
            # Test market signal strategy
            if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
                try:
                    strategy_status = agent.market_signal_strategy.get_strategy_status()
                    agent_status['agent_data']['strategy_status'] = strategy_status
                except Exception as strategy_error:
                    agent_status['agent_data']['strategy_error'] = str(strategy_error)
            
            # Get on-chain state if possible
            self.collect_on_chain_state(agent)
            
        except Exception as e:
            agent_status['errors'].append({
                'type': 'initialization_error',
                'message': str(e),
                'traceback': traceback.format_exc()
            })
        
        self.diagnostic_data['agent_status'] = agent_status

    def collect_on_chain_state(self, agent):
        """Collect current on-chain state"""
        print("⛓️ Collecting on-chain state...")
        
        on_chain_data = {
            'data_collection_attempted': False,
            'data_collection_successful': False,
            'wallet_data': {},
            'aave_data': {},
            'errors': []
        }
        
        try:
            on_chain_data['data_collection_attempted'] = True
            
            # Get ETH balance
            if hasattr(agent, 'w3') and hasattr(agent, 'address'):
                eth_balance_wei = agent.w3.eth.get_balance(agent.address)
                on_chain_data['wallet_data']['eth_balance'] = float(agent.w3.from_wei(eth_balance_wei, 'ether'))
            
            # Get Aave account data
            if hasattr(agent, 'aave') and agent.aave:
                try:
                    account_data = agent.aave.get_user_account_data()
                    if account_data:
                        on_chain_data['aave_data'] = {
                            'total_collateral_usd': account_data.get('totalCollateralUSD', 0),
                            'total_debt_usd': account_data.get('totalDebtUSD', 0),
                            'available_borrows_usd': account_data.get('availableBorrowsUSD', 0),
                            'health_factor': account_data.get('healthFactor', 0),
                            'data_source': account_data.get('data_source', 'unknown')
                        }
                        
                        # Get token balances
                        token_balances = {}
                        if hasattr(agent, 'dai_address'):
                            dai_balance = agent.aave.get_token_balance(agent.dai_address)
                            token_balances['DAI'] = dai_balance
                        
                        if hasattr(agent, 'wbtc_address'):
                            wbtc_balance = agent.aave.get_token_balance(agent.wbtc_address)
                            token_balances['WBTC'] = wbtc_balance
                        
                        if hasattr(agent, 'weth_address'):
                            weth_balance = agent.aave.get_token_balance(agent.weth_address)
                            token_balances['WETH'] = weth_balance
                        
                        on_chain_data['wallet_data']['token_balances'] = token_balances
                        
                except Exception as aave_error:
                    on_chain_data['errors'].append({
                        'type': 'aave_data_error',
                        'message': str(aave_error)
                    })
            
            on_chain_data['data_collection_successful'] = True
            
        except Exception as e:
            on_chain_data['errors'].append({
                'type': 'on_chain_collection_error',
                'message': str(e),
                'traceback': traceback.format_exc()
            })
        
        self.diagnostic_data['on_chain_state'] = on_chain_data

    def collect_recent_logs(self):
        """Collect recent log files and execution data"""
        print("📋 Collecting recent logs...")
        
        log_data = {
            'log_files_found': [],
            'recent_performance': [],
            'recent_failures': [],
            'emergency_stops': []
        }
        
        # Find recent log files
        import glob
        
        # Performance logs
        if os.path.exists('performance_log.json'):
            try:
                with open('performance_log.json', 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:]  # Last 50 entries
                    for line in recent_lines:
                        try:
                            entry = json.loads(line.strip())
                            log_data['recent_performance'].append(entry)
                        except:
                            continue
            except Exception as e:
                log_data['performance_log_error'] = str(e)
        
        # Borrow failure logs
        borrow_failure_files = glob.glob('borrow_failure_*.json')
        recent_failures = sorted(borrow_failure_files)[-10:]  # Last 10 failures
        
        for failure_file in recent_failures:
            try:
                with open(failure_file, 'r') as f:
                    failure_data = json.load(f)
                    log_data['recent_failures'].append({
                        'file': failure_file,
                        'data': failure_data
                    })
            except Exception as e:
                log_data['recent_failures'].append({
                    'file': failure_file,
                    'error': str(e)
                })
        
        # Emergency stop logs
        if os.path.exists('emergency_stop_log.json'):
            try:
                with open('emergency_stop_log.json', 'r') as f:
                    emergency_data = json.load(f)
                    log_data['emergency_stops'] = emergency_data
            except Exception as e:
                log_data['emergency_stop_error'] = str(e)
        
        self.diagnostic_data['recent_logs'] = log_data

    def test_api_connectivity(self):
        """Test API connectivity for market data"""
        print("🌐 Testing API connectivity...")
        
        api_status = {
            'coinapi_status': 'not_tested',
            'coinmarketcap_status': 'not_tested',
            'rpc_status': 'not_tested',
            'errors': []
        }
        
        # Test CoinAPI
        coinapi_key = os.getenv('COIN_API')
        if coinapi_key:
            try:
                import requests
                headers = {'X-CoinAPI-Key': coinapi_key}
                response = requests.get(
                    'https://rest.coinapi.io/v1/exchangerate/BTC/USD',
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    api_status['coinapi_status'] = 'working'
                    api_status['coinapi_data'] = response.json()
                else:
                    api_status['coinapi_status'] = f'error_{response.status_code}'
                    api_status['coinapi_error'] = response.text
            except Exception as e:
                api_status['coinapi_status'] = 'failed'
                api_status['coinapi_error'] = str(e)
        else:
            api_status['coinapi_status'] = 'no_key'
        
        # Test CoinMarketCap
        cmc_key = os.getenv('COINMARKETCAP_API_KEY')
        if cmc_key:
            try:
                import requests
                headers = {'X-CMC_PRO_API_KEY': cmc_key}
                response = requests.get(
                    'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                    headers=headers,
                    params={'symbol': 'BTC', 'convert': 'USD'},
                    timeout=10
                )
                if response.status_code == 200:
                    api_status['coinmarketcap_status'] = 'working'
                    api_status['coinmarketcap_data'] = response.json()
                else:
                    api_status['coinmarketcap_status'] = f'error_{response.status_code}'
                    api_status['coinmarketcap_error'] = response.text
            except Exception as e:
                api_status['coinmarketcap_status'] = 'failed'
                api_status['coinmarketcap_error'] = str(e)
        else:
            api_status['coinmarketcap_status'] = 'no_key'
        
        # Test RPC connectivity
        try:
            from web3 import Web3
            rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if w3.is_connected():
                block_number = w3.eth.block_number
                chain_id = w3.eth.chain_id
                api_status['rpc_status'] = 'working'
                api_status['rpc_data'] = {
                    'url': rpc_url,
                    'chain_id': chain_id,
                    'latest_block': block_number
                }
            else:
                api_status['rpc_status'] = 'not_connected'
        except Exception as e:
            api_status['rpc_status'] = 'failed'
            api_status['rpc_error'] = str(e)
        
        self.diagnostic_data['api_status'] = api_status

    def analyze_system_health(self):
        """Analyze overall system health and provide recommendations"""
        print("🏥 Analyzing system health...")
        
        # Count issues
        critical_issues = 0
        warnings = 0
        recommendations = []
        
        # Check environment variables
        env_data = self.diagnostic_data.get('environment', {})
        required_vars = ['NETWORK_MODE', 'COINMARKETCAP_API_KEY']
        private_key_present = env_data.get('PRIVATE_KEY', {}).get('present') or env_data.get('PRIVATE_KEY2', {}).get('present')
        
        if not private_key_present:
            critical_issues += 1
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Environment',
                'issue': 'No private key configured',
                'solution': 'Set PRIVATE_KEY or PRIVATE_KEY2 in Replit Secrets'
            })
        
        for var in required_vars:
            if not env_data.get(var, {}).get('present'):
                critical_issues += 1
                recommendations.append({
                    'priority': 'CRITICAL',
                    'category': 'Environment', 
                    'issue': f'Missing {var}',
                    'solution': f'Set {var} in Replit Secrets'
                })
        
        # Check agent initialization
        agent_data = self.diagnostic_data.get('agent_status', {})
        if not agent_data.get('initialization_successful'):
            critical_issues += 1
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Agent',
                'issue': 'Agent initialization failed',
                'solution': 'Check environment variables and dependencies'
            })
        
        # Check API connectivity
        api_data = self.diagnostic_data.get('api_status', {})
        working_apis = 0
        if api_data.get('coinapi_status') == 'working':
            working_apis += 1
        if api_data.get('coinmarketcap_status') == 'working':
            working_apis += 1
        
        if working_apis == 0:
            warnings += 1
            recommendations.append({
                'priority': 'HIGH',
                'category': 'APIs',
                'issue': 'No working market data APIs',
                'solution': 'Check API keys and rate limits'
            })
        
        # Calculate health score
        total_checks = 10
        health_score = max(0, 100 - (critical_issues * 25) - (warnings * 10))
        
        self.diagnostic_data['system_health'] = {
            'score': health_score,
            'critical_issues': critical_issues,
            'warnings': warnings,
            'status': 'CRITICAL' if critical_issues > 0 else 'WARNING' if warnings > 0 else 'HEALTHY'
        }
        
        self.diagnostic_data['recommendations'] = recommendations

    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        print("🔍 COMPREHENSIVE SYSTEM DIAGNOSTIC")
        print("=" * 80)
        
        try:
            self.collect_system_info()
            self.collect_environment_variables()
            self.collect_file_contents()
            self.collect_configuration_files()
            self.test_agent_initialization()
            self.collect_recent_logs()
            self.test_api_connectivity()
            self.analyze_system_health()
            
            print("\n✅ Diagnostic collection complete!")
            return self.diagnostic_data
            
        except Exception as e:
            print(f"\n❌ Diagnostic failed: {e}")
            self.diagnostic_data['diagnostic_error'] = {
                'message': str(e),
                'traceback': traceback.format_exc()
            }
            return self.diagnostic_data

    def save_diagnostic_report(self):
        """Save diagnostic report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'comprehensive_diagnostic_{timestamp}.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.diagnostic_data, f, indent=2, default=str)
            print(f"📄 Diagnostic report saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to save diagnostic report: {e}")
            return None

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 80)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 80)
        
        # System Health
        health_data = self.diagnostic_data.get('system_health', {})
        health_score = health_data.get('score', 0)
        health_status = health_data.get('status', 'UNKNOWN')
        
        print(f"🏥 System Health: {health_status} (Score: {health_score}/100)")
        
        # Environment Status
        env_data = self.diagnostic_data.get('environment', {})
        env_configured = sum(1 for var_data in env_data.values() if var_data.get('present'))
        env_total = len(env_data)
        print(f"🌍 Environment: {env_configured}/{env_total} variables configured")
        
        # Agent Status
        agent_data = self.diagnostic_data.get('agent_status', {})
        agent_status = "✅ Working" if agent_data.get('initialization_successful') else "❌ Failed"
        print(f"🤖 Agent: {agent_status}")
        
        # On-chain Status
        onchain_data = self.diagnostic_data.get('on_chain_state', {})
        if onchain_data.get('data_collection_successful'):
            aave_data = onchain_data.get('aave_data', {})
            health_factor = aave_data.get('health_factor', 0)
            collateral = aave_data.get('total_collateral_usd', 0)
            debt = aave_data.get('total_debt_usd', 0)
            print(f"⛓️ On-chain: HF {health_factor:.3f}, Collateral ${collateral:.2f}, Debt ${debt:.2f}")
        else:
            print("⛓️ On-chain: Unable to fetch data")
        
        # API Status
        api_data = self.diagnostic_data.get('api_status', {})
        coinapi_status = api_data.get('coinapi_status', 'unknown')
        cmc_status = api_data.get('coinmarketcap_status', 'unknown')
        rpc_status = api_data.get('rpc_status', 'unknown')
        print(f"🌐 APIs: CoinAPI({coinapi_status}), CoinMarketCap({cmc_status}), RPC({rpc_status})")
        
        # Recommendations
        recommendations = self.diagnostic_data.get('recommendations', [])
        critical_recs = [r for r in recommendations if r.get('priority') == 'CRITICAL']
        if critical_recs:
            print(f"\n⚠️ CRITICAL ISSUES ({len(critical_recs)}):")
            for rec in critical_recs[:3]:  # Show first 3
                print(f"   • {rec.get('issue', 'Unknown')}")

def main():
    """Run comprehensive diagnostic"""
    diagnostic = ComprehensiveSystemDiagnostic()
    
    try:
        # Run full diagnostic
        report = diagnostic.run_full_diagnostic()
        
        # Save report
        filename = diagnostic.save_diagnostic_report()
        
        # Print summary
        diagnostic.print_summary()
        
        print(f"\n📄 Full diagnostic data saved to: {filename}")
        print("📋 This file contains all requested information:")
        print("   • Complete file contents")
        print("   • Environment variables (sanitized)")
        print("   • On-chain wallet state")
        print("   • Recent execution logs")
        print("   • API connectivity status")
        print("   • System health analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
