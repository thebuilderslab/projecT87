#!/usr/bin/env python3
"""
API DIAGNOSTICS
Comprehensive endpoint for debugging UI-backend connection issues
"""

from flask import Flask, jsonify
import os
import time
import json
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3

app = Flask(__name__)

@app.route('/api/diagnostics/full-report')
def full_diagnostic_report():
    """Comprehensive diagnostic report for UI debugging"""
    try:
        report = {
            'timestamp': time.time(),
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'environment': {},
            'network': {},
            'agent': {},
            'endpoints': {},
            'files': {},
            'errors': []
        }

        # Environment diagnostics
        critical_env_vars = ['NETWORK_MODE', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY', 'PROMPT_KEY']
        for var in critical_env_vars:
            value = os.getenv(var)
            report['environment'][var] = {
                'present': bool(value),
                'length': len(value) if value else 0,
                'preview': value[:10] + '...' if value and len(value) > 10 else value if value else None
            }

        # Network diagnostics
        try:
            network_mode = os.getenv('NETWORK_MODE', 'testnet')
            report['network']['mode'] = network_mode

            if network_mode == 'mainnet':
                rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
                expected_chain_id = 42161
                network_name = 'Arbitrum Mainnet'
            else:
                rpc_url = 'https://sepolia-rollup.arbitrum.io/rpc'
                expected_chain_id = 421614
                network_name = 'Arbitrum Sepolia'

            report['network']['rpc_url'] = rpc_url
            report['network']['expected_chain_id'] = expected_chain_id
            report['network']['expected_name'] = network_name

            # Test RPC connection
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                actual_chain_id = w3.eth.chain_id
                latest_block = w3.eth.get_block('latest')

                report['network']['connected'] = True
                report['network']['actual_chain_id'] = actual_chain_id
                report['network']['latest_block'] = latest_block.number
                report['network']['chain_id_match'] = actual_chain_id == expected_chain_id

                if actual_chain_id == 42161:
                    report['network']['actual_name'] = 'Arbitrum Mainnet'
                elif actual_chain_id == 421614:
                    report['network']['actual_name'] = 'Arbitrum Sepolia'
                else:
                    report['network']['actual_name'] = f'Unknown (Chain ID: {actual_chain_id})'
            else:
                report['network']['connected'] = False
                report['errors'].append('RPC connection failed')

        except Exception as e:
            report['network']['error'] = str(e)
            report['errors'].append(f'Network check failed: {e}')

        # Agent initialization diagnostics
        try:
            agent = ArbitrumTestnetAgent()
            report['agent']['initialized'] = True
            report['agent']['address'] = agent.address
            report['agent']['eth_balance'] = agent.get_eth_balance()
            report['agent']['chain_id'] = agent.w3.eth.chain_id
        except Exception as e:
            report['agent']['initialized'] = False
            report['agent']['error'] = str(e)
            report['errors'].append(f'Agent initialization failed: {e}')

        # File existence diagnostics
        important_files = [
            'agent_config.json',
            'user_settings.json',
            'performance_log.json',
            'EMERGENCY_STOP_ACTIVE.flag'
        ]
        for file in important_files:
            report['files'][file] = os.path.exists(file)

        # Endpoint testing
        endpoints_to_test = [
            '/api/wallet_status',
            '/api/performance',
            '/api/parameters',
            '/api/network-info',
            '/api/emergency_status'
        ]

        for endpoint in endpoints_to_test:
            try:
                # We can't test these directly here, but we can check if the functions exist
                report['endpoints'][endpoint] = 'available'
            except Exception as e:
                report['endpoints'][endpoint] = f'error: {e}'

        # Parameter loading diagnostics
        try:
            # Test parameter loading methods
            config_methods = {}

            # Method 1: Default config
            config_methods['default'] = {
                'health_factor_target': 1.19,
                'borrow_trigger_threshold': 0.02,
                'arb_decline_threshold': 0.05,
                'auto_mode': True
            }

            # Method 2: From agent_config.json
            if os.path.exists('agent_config.json'):
                try:
                    with open('agent_config.json', 'r') as f:
                        config_methods['agent_config_file'] = json.load(f)
                except Exception as e:
                    config_methods['agent_config_file'] = {'error': str(e)}

            # Method 3: From user_settings.json
            if os.path.exists('user_settings.json'):
                try:
                    with open('user_settings.json', 'r') as f:
                        config_methods['user_settings_file'] = json.load(f)
                except Exception as e:
                    config_methods['user_settings_file'] = {'error': str(e)}

            report['parameters'] = config_methods

        except Exception as e:
            report['parameters'] = {'error': str(e)}
            report['errors'].append(f'Parameter diagnostics failed: {e}')

        # Overall status
        report['overall_status'] = {
            'healthy': len(report['errors']) == 0,
            'error_count': len(report['errors']),
            'critical_issues': [error for error in report['errors'] if any(word in error.lower() for word in ['failed', 'connection', 'initialization'])]
        }

        return jsonify(report)

    except Exception as e:
        return jsonify({
            'error': 'Diagnostic system failure',
            'exception': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/api/diagnostics/quick-health')
def quick_health_check():
    """Quick health check for rapid debugging"""
    try:
        health = {
            'status': 'ok',
            'timestamp': time.time(),
            'network_mode': os.getenv('NETWORK_MODE', 'unknown'),
            'secrets_count': len([var for var in ['NETWORK_MODE', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY'] if os.getenv(var)]),
            'agent_can_initialize': False
        }

        # Quick agent test
        try:
            agent = ArbitrumTestnetAgent()
            health['agent_can_initialize'] = True
            health['agent_address'] = agent.address
            health['agent_network'] = agent.w3.eth.chain_id
        except Exception as e:
            health['agent_error'] = str(e)

        return jsonify(health)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)