
#!/usr/bin/env python3
"""
COMPREHENSIVE API DIAGNOSTICS SYSTEM
Full diagnostic endpoint for UI-backend communication debugging
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
        'ui_backend_communication': {},
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
        
        # UI-Backend Communication Tests
        ui_tests = {}
        
        # Test 1: Basic Connection Test
        try:
            ui_tests['basic_connection'] = {
                'status': 'success',
                'server_time': datetime.now().isoformat(),
                'response_time': time.time()
            }
        except Exception as e:
            ui_tests['basic_connection'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test 2: Parameters Endpoint Deep Dive
        try:
            # Test parameter loading mechanisms
            param_sources = {}
            
            # Source 1: Default config
            default_config = {
                'health_factor_target': 1.19,
                'borrow_trigger_threshold': 0.02,
                'arb_decline_threshold': 0.05,
                'auto_mode': True
            }
            param_sources['default_config'] = {
                'status': 'success',
                'data': default_config
            }
            
            # Source 2: agent_config.json
            if os.path.exists('agent_config.json'):
                try:
                    with open('agent_config.json', 'r') as f:
                        config_data = json.load(f)
                    param_sources['agent_config_file'] = {
                        'status': 'success',
                        'file_exists': True,
                        'data': config_data
                    }
                except Exception as e:
                    param_sources['agent_config_file'] = {
                        'status': 'error',
                        'file_exists': True,
                        'error': str(e)
                    }
            else:
                param_sources['agent_config_file'] = {
                    'status': 'missing',
                    'file_exists': False
                }
            
            # Source 3: user_settings.json
            if os.path.exists('user_settings.json'):
                try:
                    with open('user_settings.json', 'r') as f:
                        user_data = json.load(f)
                    param_sources['user_settings_file'] = {
                        'status': 'success',
                        'file_exists': True,
                        'data': user_data
                    }
                except Exception as e:
                    param_sources['user_settings_file'] = {
                        'status': 'error',
                        'file_exists': True,
                        'error': str(e)
                    }
            else:
                param_sources['user_settings_file'] = {
                    'status': 'missing',
                    'file_exists': False
                }
            
            ui_tests['parameters_deep_dive'] = param_sources
            
        except Exception as e:
            ui_tests['parameters_deep_dive'] = {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Test 3: Agent Initialization Test
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            ui_tests['agent_initialization'] = {
                'status': 'success',
                'agent_address': agent.address,
                'network_connected': True,
                'chain_id': agent.w3.eth.chain_id if hasattr(agent, 'w3') else 'unknown'
            }
            
            # Test wallet status
            try:
                eth_balance = agent.get_eth_balance()
                ui_tests['wallet_status_test'] = {
                    'status': 'success',
                    'eth_balance': eth_balance,
                    'balance_type': type(eth_balance).__name__
                }
            except Exception as e:
                ui_tests['wallet_status_test'] = {
                    'status': 'error',
                    'error': str(e)
                }
                
        except Exception as e:
            ui_tests['agent_initialization'] = {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Test 4: Web Dashboard Import Test
        try:
            from web_dashboard import app as dashboard_app
            ui_tests['dashboard_import'] = {
                'status': 'success',
                'app_available': True
            }
            
            # Test individual endpoints
            endpoints_to_test = [
                '/api/wallet_status',
                '/api/performance', 
                '/api/parameters',
                '/api/emergency_status'
            ]
            
            endpoint_results = {}
            for endpoint in endpoints_to_test:
                try:
                    with dashboard_app.test_client() as client:
                        response = client.get(endpoint)
                        endpoint_results[endpoint] = {
                            'status_code': response.status_code,
                            'success': response.status_code == 200,
                            'content_type': response.content_type,
                            'has_data': bool(response.data)
                        }
                        
                        if response.status_code == 200:
                            try:
                                data = response.get_json()
                                endpoint_results[endpoint]['json_valid'] = True
                                endpoint_results[endpoint]['has_error'] = 'error' in data if data else False
                            except:
                                endpoint_results[endpoint]['json_valid'] = False
                                
                except Exception as e:
                    endpoint_results[endpoint] = {
                        'status': 'test_failed',
                        'error': str(e)
                    }
            
            ui_tests['endpoint_tests'] = endpoint_results
            
        except Exception as e:
            ui_tests['dashboard_import'] = {
                'status': 'error',
                'error': str(e)
            }
        
        report['ui_backend_communication'] = ui_tests
        
        # Test API Endpoints
        api_tests = {}
        
        # Test 1: Emergency Stop Status
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
        
        # Test 2: Performance Data
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
            rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
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
        ui_issues = [
            key for key, test in ui_tests.items() 
            if test.get('status') == 'error'
        ]
        
        api_issues = [
            key for key, test in api_tests.items() 
            if test.get('status') == 'error'
        ]
        
        report['summary'] = {
            'overall_status': 'healthy' if not ui_issues and not api_issues else 'issues_detected',
            'ui_issues': ui_issues,
            'api_issues': api_issues,
            'critical_issues': ui_issues + api_issues,
            'deployment_ready': env_status['NETWORK_MODE']['exists'] and 
                              env_status['PRIVATE_KEY']['exists'] and
                              env_status['COINMARKETCAP_API_KEY']['exists'],
            'recommendations': []
        }
        
        # Add specific recommendations
        if ui_issues:
            report['summary']['recommendations'].append("Fix UI-backend communication issues")
        if 'parameters_deep_dive' in ui_issues:
            report['summary']['recommendations'].append("Check parameter file permissions and JSON format")
        if not env_status['NETWORK_MODE']['exists']:
            report['summary']['recommendations'].append("Set NETWORK_MODE environment variable")
        
    except Exception as e:
        report['errors'].append({
            'error': str(e),
            'traceback': traceback.format_exc()
        })
    
    return jsonify(report)

@app.route('/api/diagnostics/ui-fix')
def ui_communication_fix():
    """Provide specific fixes for UI communication issues"""
    
    fixes = {
        'timestamp': datetime.now().isoformat(),
        'detected_issues': [],
        'fixes_applied': [],
        'manual_fixes_needed': []
    }
    
    try:
        # Issue 1: Check if parameters endpoint is working
        try:
            # Test parameter loading
            config = {
                'health_factor_target': 1.19,
                'borrow_trigger_threshold': 0.02,
                'arb_decline_threshold': 0.05,
                'auto_mode': True
            }
            
            # Create user_settings.json if missing
            if not os.path.exists('user_settings.json'):
                with open('user_settings.json', 'w') as f:
                    json.dump(config, f, indent=2)
                fixes['fixes_applied'].append("Created user_settings.json with default parameters")
            
            # Create agent_config.json if missing
            if not os.path.exists('agent_config.json'):
                with open('agent_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                fixes['fixes_applied'].append("Created agent_config.json with default parameters")
                
        except Exception as e:
            fixes['detected_issues'].append(f"Parameter file issue: {str(e)}")
        
        # Issue 2: Check performance log
        try:
            if not os.path.exists('performance_log.json'):
                # Create empty performance log
                with open('performance_log.json', 'w') as f:
                    pass  # Create empty file
                fixes['fixes_applied'].append("Created empty performance_log.json")
        except Exception as e:
            fixes['detected_issues'].append(f"Performance log issue: {str(e)}")
        
        # Issue 3: Check emergency stop log
        try:
            if not os.path.exists('emergency_stop_log.json'):
                with open('emergency_stop_log.json', 'w') as f:
                    json.dump([], f)
                fixes['fixes_applied'].append("Created emergency_stop_log.json")
        except Exception as e:
            fixes['detected_issues'].append(f"Emergency log issue: {str(e)}")
        
        # Manual fixes needed
        if not os.getenv('NETWORK_MODE'):
            fixes['manual_fixes_needed'].append("Set NETWORK_MODE in Replit Secrets")
        
        if not os.getenv('PRIVATE_KEY'):
            fixes['manual_fixes_needed'].append("Set PRIVATE_KEY in Replit Secrets")
            
        if not os.getenv('COINMARKETCAP_API_KEY'):
            fixes['manual_fixes_needed'].append("Set COINMARKETCAP_API_KEY in Replit Secrets")
    
    except Exception as e:
        fixes['detected_issues'].append(f"Fix application error: {str(e)}")
    
    return jsonify(fixes)

@app.route('/api/diagnostics/parameters-test')
def test_parameters_endpoint():
    """Test parameters endpoint specifically"""
    
    test_result = {
        'timestamp': datetime.now().isoformat(),
        'test_methods': {},
        'final_result': {}
    }
    
    # Method 1: Default parameters
    test_result['test_methods']['default'] = {
        'health_factor_target': 1.19,
        'borrow_trigger_threshold': 0.02,
        'arb_decline_threshold': 0.05,
        'auto_mode': True
    }
    
    # Method 2: From agent_config.json
    try:
        if os.path.exists('agent_config.json'):
            with open('agent_config.json', 'r') as f:
                config = json.load(f)
            test_result['test_methods']['agent_config'] = config
        else:
            test_result['test_methods']['agent_config'] = {'status': 'file_not_found'}
    except Exception as e:
        test_result['test_methods']['agent_config'] = {'error': str(e)}
    
    # Method 3: From user_settings.json
    try:
        if os.path.exists('user_settings.json'):
            with open('user_settings.json', 'r') as f:
                config = json.load(f)
            test_result['test_methods']['user_settings'] = config
        else:
            test_result['test_methods']['user_settings'] = {'status': 'file_not_found'}
    except Exception as e:
        test_result['test_methods']['user_settings'] = {'error': str(e)}
    
    # Final merged result
    final_config = test_result['test_methods']['default'].copy()
    
    if 'agent_config' in test_result['test_methods'] and isinstance(test_result['test_methods']['agent_config'], dict):
        if 'error' not in test_result['test_methods']['agent_config']:
            final_config.update(test_result['test_methods']['agent_config'])
    
    if 'user_settings' in test_result['test_methods'] and isinstance(test_result['test_methods']['user_settings'], dict):
        if 'error' not in test_result['test_methods']['user_settings']:
            final_config.update(test_result['test_methods']['user_settings'])
    
    test_result['final_result'] = final_config
    
    return jsonify(test_result)

if __name__ == '__main__':
    print("🔍 Starting Enhanced API Diagnostics Server")
    print("Available endpoints:")
    print("  /api/diagnostics/full-report - Comprehensive diagnostic report")
    print("  /api/diagnostics/ui-fix - Apply automatic fixes for UI issues")
    print("  /api/diagnostics/parameters-test - Test parameters endpoint specifically")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
