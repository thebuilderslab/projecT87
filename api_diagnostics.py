
#!/usr/bin/env python3
"""
API DIAGNOSTICS SYSTEM
Comprehensive diagnostic endpoint for UI-backend communication debugging
"""

import os
import sys
import time
import json
import traceback
from datetime import datetime
from flask import Flask, jsonify, request
import subprocess

app = Flask(__name__)

@app.route('/api/diagnostics/full-report')
def full_diagnostic_report():
    """Comprehensive diagnostic report for UI-backend communication"""
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'system_info': {},
        'environment_status': {},
        'api_endpoints': {},
        'agent_status': {},
        'file_system': {},
        'network_connectivity': {},
        'errors': []
    }
    
    try:
        # System Information
        report['system_info'] = {
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'pid': os.getpid(),
            'deployment_mode': bool(os.getenv('REPLIT_DEPLOYMENT')),
            'replit_env': bool(os.getenv('REPLIT'))
        }
        
        # Environment Variables Status
        critical_env_vars = [
            'NETWORK_MODE', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY', 
            'PROMPT_KEY', 'ARBITRUM_RPC_URL', 'REPLIT_DEPLOYMENT'
        ]
        
        env_status = {}
        for var in critical_env_vars:
            value = os.getenv(var)
            env_status[var] = {
                'exists': bool(value),
                'length': len(value) if value else 0,
                'type': type(value).__name__,
                'first_chars': value[:10] if value and len(value) > 10 else value
            }
        
        report['environment_status'] = env_status
        
        # Test API Endpoints
        api_tests = {}
        
        # Test 1: Wallet Status Endpoint
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            eth_balance = agent.get_eth_balance()
            api_tests['wallet_status'] = {
                'status': 'success',
                'agent_initialized': True,
                'wallet_address': agent.address,
                'eth_balance': eth_balance,
                'network_connected': True
            }
            
            # Test Aave integration
            if hasattr(agent, 'aave'):
                try:
                    usdc_balance = agent.aave.get_token_balance(agent.aave.usdc_address)
                    health_data = agent.health_monitor.get_current_health_factor()
                    api_tests['aave_integration'] = {
                        'status': 'success',
                        'usdc_balance': usdc_balance,
                        'health_factor': health_data.get('health_factor', 'N/A')
                    }
                except Exception as e:
                    api_tests['aave_integration'] = {
                        'status': 'error',
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
            else:
                api_tests['aave_integration'] = {
                    'status': 'not_available',
                    'reason': 'agent.aave not found'
                }
                
        except Exception as e:
            api_tests['wallet_status'] = {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Test 2: Parameters Endpoint
        try:
            # Test parameter loading
            config = {
                'learning_rate': 0.01,
                'exploration_rate': 0.1,
                'max_iterations_per_run': 100,
                'optimization_target_threshold': 0.95,
                'health_factor_target': 1.19,
                'borrow_trigger_threshold': 0.02,
                'arb_decline_threshold': 0.05,
                'auto_mode': True
            }
            
            # Try to load from agent_config.json
            if os.path.exists('agent_config.json'):
                with open('agent_config.json', 'r') as f:
                    saved_config = json.load(f)
                    config.update(saved_config)
            
            api_tests['parameters'] = {
                'status': 'success',
                'config_file_exists': os.path.exists('agent_config.json'),
                'config': config
            }
            
        except Exception as e:
            api_tests['parameters'] = {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Test 3: Performance Data
        try:
            performance_data = []
            if os.path.exists('performance_log.json'):
                with open('performance_log.json', 'r') as f:
                    for line in f:
                        performance_data.append(json.loads(line))
            
            api_tests['performance'] = {
                'status': 'success',
                'log_file_exists': os.path.exists('performance_log.json'),
                'total_entries': len(performance_data),
                'recent_entries': len(performance_data[-10:]) if performance_data else 0
            }
            
        except Exception as e:
            api_tests['performance'] = {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Test 4: Emergency Stop Status
        try:
            emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
            is_active = os.path.exists(emergency_file)
            
            api_tests['emergency_stop'] = {
                'status': 'success',
                'emergency_active': is_active,
                'file_exists': is_active
            }
            
        except Exception as e:
            api_tests['emergency_stop'] = {
                'status': 'error',
                'error': str(e)
            }
        
        report['api_endpoints'] = api_tests
        
        # File System Status
        important_files = [
            'web_dashboard.py', 'arbitrum_testnet_agent.py', 'dashboard.py',
            'agent_config.json', 'performance_log.json', 'emergency_stop.py',
            'templates/dashboard.html', '.env'
        ]
        
        file_status = {}
        for file_path in important_files:
            file_status[file_path] = {
                'exists': os.path.exists(file_path),
                'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'readable': os.access(file_path, os.R_OK) if os.path.exists(file_path) else False
            }
        
        report['file_system'] = file_status
        
        # Network Connectivity Tests
        network_tests = {}
        
        # Test Arbitrum RPC
        try:
            from web3 import Web3
            rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://sepolia-rollup.arbitrum.io/rpc')
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            network_tests['arbitrum_rpc'] = {
                'status': 'success' if w3.is_connected() else 'failed',
                'url': rpc_url,
                'connected': w3.is_connected(),
                'chain_id': w3.eth.chain_id if w3.is_connected() else None
            }
            
        except Exception as e:
            network_tests['arbitrum_rpc'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test CoinMarketCap API
        try:
            import requests
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            if api_key:
                response = requests.get(
                    'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                    params={'symbol': 'ARB'},
                    headers={'X-CMC_PRO_API_KEY': api_key},
                    timeout=10
                )
                
                network_tests['coinmarketcap'] = {
                    'status': 'success' if response.status_code == 200 else 'failed',
                    'status_code': response.status_code,
                    'api_key_length': len(api_key)
                }
            else:
                network_tests['coinmarketcap'] = {
                    'status': 'no_api_key',
                    'message': 'COINMARKETCAP_API_KEY not found'
                }
                
        except Exception as e:
            network_tests['coinmarketcap'] = {
                'status': 'error',
                'error': str(e)
            }
        
        report['network_connectivity'] = network_tests
        
        # Overall Status Summary
        report['summary'] = {
            'overall_status': 'healthy' if all(
                test.get('status') == 'success' 
                for test in api_tests.values() 
                if test.get('status') in ['success', 'error']
            ) else 'issues_detected',
            'critical_issues': [
                key for key, test in api_tests.items() 
                if test.get('status') == 'error'
            ],
            'deployment_ready': env_status['NETWORK_MODE']['exists'] and 
                              env_status['PRIVATE_KEY']['exists'] and
                              env_status['COINMARKETCAP_API_KEY']['exists']
        }
        
    except Exception as e:
        report['errors'].append({
            'error': str(e),
            'traceback': traceback.format_exc()
        })
    
    return jsonify(report)

@app.route('/api/diagnostics/quick-check')
def quick_diagnostic_check():
    """Quick diagnostic check for immediate issues"""
    
    issues = []
    
    # Check environment variables
    if not os.getenv('NETWORK_MODE'):
        issues.append("NETWORK_MODE not set")
    
    if not os.getenv('PRIVATE_KEY'):
        issues.append("PRIVATE_KEY not set")
    
    if not os.getenv('COINMARKETCAP_API_KEY'):
        issues.append("COINMARKETCAP_API_KEY not set")
    
    # Check file existence
    if not os.path.exists('web_dashboard.py'):
        issues.append("web_dashboard.py missing")
    
    if not os.path.exists('templates/dashboard.html'):
        issues.append("dashboard.html missing")
    
    # Test agent initialization
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        agent_status = "initialized"
    except Exception as e:
        issues.append(f"Agent initialization failed: {str(e)}")
        agent_status = "failed"
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy' if not issues else 'issues_detected',
        'issues': issues,
        'agent_status': agent_status,
        'issues_count': len(issues)
    })

@app.route('/api/diagnostics/test-endpoints')
def test_all_endpoints():
    """Test all dashboard API endpoints"""
    
    endpoints_to_test = [
        '/api/wallet_status',
        '/api/performance',
        '/api/parameters',
        '/api/emergency_status',
        '/api/network-info'
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        try:
            # Import Flask app
            from web_dashboard import app as dashboard_app
            
            with dashboard_app.test_client() as client:
                response = client.get(endpoint)
                results[endpoint] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'content_type': response.content_type,
                    'data_size': len(response.data) if response.data else 0
                }
                
                if response.status_code == 200:
                    try:
                        data = response.get_json()
                        results[endpoint]['has_data'] = bool(data)
                        results[endpoint]['error_in_data'] = 'error' in data if data else False
                    except:
                        results[endpoint]['json_parseable'] = False
                        
        except Exception as e:
            results[endpoint] = {
                'status': 'test_failed',
                'error': str(e)
            }
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'endpoint_tests': results,
        'total_endpoints': len(endpoints_to_test),
        'successful_endpoints': sum(1 for r in results.values() if r.get('success')),
        'failed_endpoints': sum(1 for r in results.values() if not r.get('success'))
    })

if __name__ == '__main__':
    print("🔍 Starting API Diagnostics Server")
    print("Available endpoints:")
    print("  /api/diagnostics/full-report - Comprehensive diagnostic report")
    print("  /api/diagnostics/quick-check - Quick issue detection")
    print("  /api/diagnostics/test-endpoints - Test all dashboard endpoints")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
