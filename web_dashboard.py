# Applying the provided changes to update the network display logic in the Flask app.
from flask import Flask, render_template, jsonify, request
import json
import os
import time
from datetime import datetime
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from dashboard import AgentDashboard
import threading
import subprocess

app = Flask(__name__)
agent = None
dashboard = None

# CRITICAL: Force load environment variables for deployment
def force_load_deployment_env():
    """Force load environment variables in deployment mode"""
    if os.getenv('REPLIT_DEPLOYMENT'):
        print("🔄 WEB DASHBOARD: Loading deployment environment")
        try:
            result = subprocess.run(['printenv'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '=' in line and line.strip():
                        key, value = line.split('=', 1)
                        if key in ['NETWORK_MODE', 'PROMPT_KEY', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY']:
                            os.environ[key] = value
                            print(f"🔄 Dashboard env loaded: {key}")
        except Exception as e:
            print(f"⚠️ Dashboard env loading warning: {e}")

# Load environment immediately
force_load_deployment_env()

def initialize_agent():
    """Initialize the agent in a separate thread"""
    global agent, dashboard
    try:
        agent = ArbitrumTestnetAgent()
        dashboard = AgentDashboard(agent)
        print("✅ Agent initialized for web dashboard")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        agent = None
        dashboard = None

# Initialize agent in background
threading.Thread(target=initialize_agent, daemon=True).start()

def get_network_info():
    """Get current network information with proper mainnet detection"""
    try:
        # PRIORITY 1: NETWORK_MODE environment variable (most authoritative)
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        print(f"🔍 Dashboard network detection - NETWORK_MODE: {network_mode}")

        # Force display based on NETWORK_MODE setting
        if network_mode == 'mainnet':
            print(f"🚀 NETWORK_MODE=mainnet detected - forcing Arbitrum Mainnet display")
            return {
                'network_mode': 'mainnet',
                'chain_id': 42161,
                'network_name': 'Arbitrum Mainnet',
                'rpc_url': 'https://arb1.arbitrum.io/rpc'
            }
        
        # Initialize agent to verify actual connection for testnet
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        chain_id = agent.w3.eth.chain_id
        
        print(f"🔍 Dashboard network detection - Chain ID: {chain_id}")

        # For testnet, verify chain ID matches
        if chain_id == 421614:
            network_name = "Arbitrum Sepolia"
            rpc_url = "https://sepolia-rollup.arbitrum.io/rpc"
        elif chain_id == 42161:
            # If connected to mainnet but NETWORK_MODE is testnet, show warning
            print(f"⚠️ WARNING: Connected to mainnet (42161) but NETWORK_MODE is testnet")
            network_name = "Arbitrum Mainnet (via testnet mode)"
            rpc_url = "https://arb1.arbitrum.io/rpc"
        else:
            network_name = f"Unknown Network (Chain ID: {chain_id})"
            rpc_url = agent.w3.provider.endpoint_uri if hasattr(agent.w3.provider, 'endpoint_uri') else 'Unknown'

        result = {
            'network_mode': network_mode,
            'chain_id': chain_id,
            'network_name': network_name,
            'rpc_url': rpc_url
        }

        print(f"🔍 Dashboard network result: {result}")
        return result

    except Exception as e:
        print(f"⚠️ Network info fallback due to error: {e}")
        # Fallback based on NETWORK_MODE environment variable
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        if network_mode == 'mainnet':
            return {
                'network_mode': 'mainnet',
                'chain_id': 42161,
                'network_name': 'Arbitrum Mainnet',
                'rpc_url': 'https://arb1.arbitrum.io/rpc'
            }
        else:
            return {
                'network_mode': 'testnet',
                'chain_id': 421614,
                'network_name': 'Arbitrum Sepolia',
                'rpc_url': 'https://sepolia-rollup.arbitrum.io/rpc'
            }

@app.route('/')
def dashboard():
    """Main dashboard page with accurate network detection"""
    try:
        # Get system status
        emergency_active = check_emergency_status()

        # Get comprehensive network info using our improved function
        network_info = get_network_info()

        # Try to get agent status
        agent_status = "Initializing..."
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            agent_status = "Connected"

            # Verify network info matches actual connection
            actual_chain_id = agent.w3.eth.chain_id
            if actual_chain_id != network_info['chain_id']:
                print(f"⚠️ Chain ID mismatch: Expected {network_info['chain_id']}, got {actual_chain_id}")
                # Update network info with actual connection
                network_info['chain_id'] = actual_chain_id
                if actual_chain_id == 42161:
                    network_info['network_name'] = 'Arbitrum Mainnet'
                elif actual_chain_id == 421614:
                    network_info['network_name'] = 'Arbitrum Sepolia'

        except Exception as e:
            agent_status = f"Error: {str(e)}"
            print(f"⚠️ Agent connection error in dashboard: {e}")

        return render_template('dashboard.html',
                               emergency_active=emergency_active,
                               agent_status=agent_status,
                               network_info=network_info)  # Pass to template

    except Exception as e:
        return render_template('dashboard.html',
                               emergency_active=False,
                               agent_status=f"Dashboard Error: {str(e)}",
                               network_info={})

def check_emergency_status():
    """Check if emergency stop is active"""
    emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
    return os.path.exists(emergency_file)

@app.route('/api/wallet_status')
def wallet_status():
    """Get current wallet status"""
    try:
        if not agent:
            return jsonify({
                'error': 'Agent not initialized',
                'status': 'initializing'
            })

        # Get balances
        eth_balance = agent.get_eth_balance()

        if hasattr(agent, 'aave'):
            usdc_balance = agent.aave.get_token_balance(agent.aave.usdc_address)
            health_data = agent.health_monitor.get_current_health_factor()
        else:
            usdc_balance = 0
            health_data = {'health_factor': 0, 'total_collateral_eth': 0, 'total_debt_eth': 0, 'available_borrows_eth': 0}

        # Get ARB price
        arb_price_data = agent.health_monitor.get_arb_price() if hasattr(agent, 'health_monitor') else None
        arb_price = arb_price_data['price'] if arb_price_data else 0

        # Convert ETH values to USDC (assuming 1 ETH = $2500 for mainnet)
        eth_to_usd_rate = 2500.0  # Conservative estimate for mainnet

        total_collateral_usdc = health_data['total_collateral_eth'] * eth_to_usd_rate
        total_debt_usdc = health_data['total_debt_eth'] * eth_to_usd_rate
        available_borrows_usdc = health_data['available_borrows_eth'] * eth_to_usd_rate

        # PRIORITY: NETWORK_MODE environment variable determines display
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        print(f"🔍 Dashboard wallet_status - NETWORK_MODE: {network_mode}")
        
        # Force display based on NETWORK_MODE (authoritative source)
        if network_mode == 'mainnet':
            network_name = "Arbitrum Mainnet"
            print(f"🚀 Forcing Arbitrum Mainnet display based on NETWORK_MODE")
        else:
            network_name = "Arbitrum Sepolia"
            print(f"🧪 Showing Arbitrum Sepolia based on NETWORK_MODE")

        return jsonify({
            'wallet_address': agent.address,
            'eth_balance': eth_balance,
            'usdc_balance': usdc_balance,
            'health_factor': health_data['health_factor'],
            'total_collateral': health_data['total_collateral_eth'],
            'total_debt': health_data['total_debt_eth'],
            'available_borrows': health_data['available_borrows_eth'],
            'total_collateral_usdc': total_collateral_usdc,
            'total_debt_usdc': total_debt_usdc,
            'available_borrows_usdc': available_borrows_usdc,
            'arb_price': arb_price,
            'network_name': network_name,
            'network_mode': network_mode,
            'timestamp': time.time()
        })

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/performance')
def performance_data():
    """Get 24h performance metrics"""
    try:
        performance_data = []
        if os.path.exists('performance_log.json'):
            with open('performance_log.json', 'r') as f:
                for line in f:
                    performance_data.append(json.loads(line))

        if len(performance_data) >= 2:
            recent = performance_data[-50:]
            avg_performance = sum(p['performance_metric'] for p in recent) / len(recent)

            if len(recent) > 1:
                start_perf = recent[0]['performance_metric']
                end_perf = recent[-1]['performance_metric']
                pnl_pct = ((end_perf - start_perf) / start_perf) * 100
            else:
                pnl_pct = 0

            error_count = sum(1 for p in recent if p['performance_metric'] < 0.5)
            error_rate = (error_count / len(recent)) * 100

            return jsonify({
                'pnl_24h': pnl_pct,
                'avg_performance': avg_performance,
                'error_rate': error_rate,
                'total_operations': len(recent),
                'timestamp': time.time()
            })
        else:
            return jsonify({
                'pnl_24h': 0,
                'avg_performance': 0,
                'error_rate': 0,
                'total_operations': 0,
                'timestamp': time.time()
            })

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/parameters')
def get_parameters():
    """Get current agent parameters with enhanced error handling"""
    try:
        # Default configuration
        config = {
            'learning_rate': 0.01,
            'exploration_rate': 0.1,
            'max_iterations_per_run': 100,
            'optimization_target_threshold': 0.95,
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'auto_mode': True,
            'debug_info': {
                'config_sources': [],
                'load_time': time.time()
            }
        }

        # Try multiple parameter sources
        sources_tried = []

        # Source 1: agent_config.json
        if os.path.exists('agent_config.json'):
            try:
                with open('agent_config.json', 'r') as f:
                    saved_config = json.load(f)
                    if isinstance(saved_config, dict):
                        config.update(saved_config)
                        sources_tried.append('agent_config.json')
                        config['debug_info']['config_sources'].append('agent_config.json')
            except Exception as e:
                sources_tried.append(f'agent_config.json (failed: {e})')

        # Source 2: user_settings.json
        if os.path.exists('user_settings.json'):
            try:
                with open('user_settings.json', 'r') as f:
                    user_config = json.load(f)
                    if isinstance(user_config, dict):
                        config.update(user_config)
                        sources_tried.append('user_settings.json')
                        config['debug_info']['config_sources'].append('user_settings.json')
            except Exception as e:
                sources_tried.append(f'user_settings.json (failed: {e})')

        # Source 3: dashboard parameters
        if dashboard and hasattr(dashboard, 'adjustable_params'):
            try:
                if isinstance(dashboard.adjustable_params, dict):
                    config.update(dashboard.adjustable_params)
                    sources_tried.append('dashboard')
                    config['debug_info']['config_sources'].append('dashboard')
            except Exception as e:
                sources_tried.append(f'dashboard (failed: {e})')

        # Add debug information
        config['debug_info']['sources_tried'] = sources_tried
        config['debug_info']['total_sources'] = len([s for s in sources_tried if 'failed' not in s])

        return jsonify(config)

    except Exception as e:
        print(f"CRITICAL: get_parameters failed completely: {e}")
        # Return minimal working config
        return jsonify({
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'auto_mode': True,
            'error': str(e),
            'fallback': True,
            'timestamp': time.time()
        })

@app.route('/api/emergency_stop', methods=['POST'])
def activate_emergency_stop():
    """Activate emergency stop"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Emergency stop via dashboard')

        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        with open(emergency_file, 'w') as f:
            f.write(f"EMERGENCY STOP ACTIVE\n")
            f.write(f"Reason: {reason}\n")
            f.write(f"Timestamp: {time.time()}\n")
            f.write(f"DateTime: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")

        # Log the action
        import json
        log_file = 'emergency_stop_log.json'
        log_entry = {
            'timestamp': time.time(),
            'action': 'EMERGENCY_STOP_ACTIVATED',
            'reason': reason,
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'source': 'dashboard'
        }

        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(log_entry)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

        return jsonify({'success': True, 'message': 'Emergency stop activated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency_stop', methods=['DELETE'])
def clear_emergency_stop():
    """Clear emergency stop"""
    try:
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        if os.path.exists(emergency_file):
            os.remove(emergency_file)

            # Log the action
            import json
            log_file = 'emergency_stop_log.json'
            log_entry = {
                'timestamp': time.time(),
                'action': 'EMERGENCY_STOP_CLEARED',
                'reason': 'Cleared via dashboard',
                'datetime': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                'source': 'dashboard'
            }

            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append(log_entry)
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)

            return jsonify({'success': True, 'message': 'Emergency stop cleared'})
        else:
            return jsonify({'success': False, 'message': 'No emergency stop active'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network-info')
def get_network_info_api():
    """Get current network information"""
    try:
        network_info = get_network_info()
        return jsonify(network_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency_status')
def get_emergency_status():
    """Get emergency stop status"""
    try:
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        is_active = os.path.exists(emergency_file)

        status = {'active': is_active}

        if is_active:
            with open(emergency_file, 'r') as f:
                content = f.read()
                status['details'] = content

        # Get recent logs
        log_file = 'emergency_stop_log.json'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
                status['recent_logs'] = logs[-3:]  # Last 3 actions

        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/switch-network', methods=['POST'])
def switch_network():
    """Switch between mainnet and testnet"""
    try:
        data = request.get_json()
        target_network = data.get('network', 'testnet').lower()
        
        if target_network not in ['mainnet', 'testnet']:
            return jsonify({'error': 'Invalid network. Use "mainnet" or "testnet"'}), 400
        
        # Update environment variable
        os.environ['NETWORK_MODE'] = target_network
        
        # Save to .env file if it exists
        env_file = '.env'
        if os.path.exists(env_file):
            lines = []
            network_mode_found = False
            
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('NETWORK_MODE='):
                        lines.append(f'NETWORK_MODE={target_network}\n')
                        network_mode_found = True
                    else:
                        lines.append(line)
            
            if not network_mode_found:
                lines.append(f'NETWORK_MODE={target_network}\n')
            
            with open(env_file, 'w') as f:
                f.writelines(lines)
        
        # Log the network switch
        log_entry = {
            'timestamp': time.time(),
            'action': 'NETWORK_SWITCH',
            'from_network': 'unknown',  # Could be enhanced to track previous
            'to_network': target_network,
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'source': 'dashboard'
        }
        
        # Create network switch log
        switch_log_file = 'network_switch_log.json'
        if os.path.exists(switch_log_file):
            with open(switch_log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        with open(switch_log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        return jsonify({
            'success': True,
            'network': target_network,
            'message': f'Network switched to {target_network}',
            'restart_required': True,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diagnostics/connection-test')
def connection_test():
    """Simple connection test for UI debugging"""
    try:
        return jsonify({
            'status': 'connected',
            'timestamp': time.time(),
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'agent_initialized': agent is not None,
            'dashboard_available': dashboard is not None,
            'network_mode': os.getenv('NETWORK_MODE', 'unknown'),
            'deployment_mode': bool(os.getenv('REPLIT_DEPLOYMENT'))
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/diagnostics/debug-parameters')
def debug_parameters():
    """Debug parameter loading issues"""
    try:
        debug_info = {
            'config_file_exists': os.path.exists('agent_config.json'),
            'user_settings_exists': os.path.exists('user_settings.json'),
            'dashboard_available': dashboard is not None,
            'dashboard_has_params': hasattr(dashboard, 'adjustable_params') if dashboard else False
        }
        
        # Try different parameter loading methods
        methods = {}
        
        # Method 1: Default config
        methods['default_config'] = {
            'learning_rate': 0.01,
            'exploration_rate': 0.1,
            'max_iterations_per_run': 100,
            'optimization_target_threshold': 0.95,
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'auto_mode': True
        }
        
        # Method 2: From agent_config.json
        if os.path.exists('agent_config.json'):
            try:
                with open('agent_config.json', 'r') as f:
                    methods['agent_config_file'] = json.load(f)
            except Exception as e:
                methods['agent_config_file'] = {'error': str(e)}
        
        # Method 3: From user_settings.json
        if os.path.exists('user_settings.json'):
            try:
                with open('user_settings.json', 'r') as f:
                    methods['user_settings_file'] = json.load(f)
            except Exception as e:
                methods['user_settings_file'] = {'error': str(e)}
        
        # Method 4: From dashboard
        if dashboard and hasattr(dashboard, 'adjustable_params'):
            try:
                methods['dashboard_params'] = dashboard.adjustable_params
            except Exception as e:
                methods['dashboard_params'] = {'error': str(e)}
        
        return jsonify({
            'debug_info': debug_info,
            'parameter_methods': methods,
            'recommendation': 'Check which method is causing the issue'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parameters', methods=['POST'])
def update_parameters():
    """Update adjustable parameters"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        # Use a local config if dashboard is not available
        if dashboard and hasattr(dashboard, 'adjustable_params'):
            params = dashboard.adjustable_params
        else:
            # Load from file or use defaults
            if os.path.exists('user_settings.json'):
                try:
                    with open('user_settings.json', 'r') as f:
                        params = json.load(f)
                except:
                    params = {}
            else:
                params = {}

        # Default values
        default_params = {
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'auto_mode': True
        }
        
        # Ensure all default params exist
        for key, default_value in default_params.items():
            if key not in params:
                params[key] = default_value

        # Validate and update parameters
        updated = False
        
        if 'health_factor_target' in data:
            try:
                value = float(data['health_factor_target'])
                if 1.05 <= value <= 3.0:
                    params['health_factor_target'] = value
                    updated = True
            except (ValueError, TypeError):
                pass

        if 'borrow_trigger_threshold' in data:
            try:
                value = float(data['borrow_trigger_threshold'])
                if 0.001 <= value <= 0.5:
                    params['borrow_trigger_threshold'] = value
                    updated = True
            except (ValueError, TypeError):
                pass

        if 'arb_decline_threshold' in data:
            try:
                value = float(data['arb_decline_threshold'])
                if 0.01 <= value <= 0.5:
                    params['arb_decline_threshold'] = value
                    updated = True
            except (ValueError, TypeError):
                pass

        if 'auto_mode' in data:
            try:
                params['auto_mode'] = bool(data['auto_mode'])
                updated = True
            except (ValueError, TypeError):
                pass

        # Save settings
        if updated:
            try:
                with open('user_settings.json', 'w') as f:
                    json.dump(params, f, indent=2)
                
                # Update dashboard if available
                if dashboard and hasattr(dashboard, 'adjustable_params'):
                    dashboard.adjustable_params.update(params)
                    
            except Exception as e:
                print(f"Warning: Could not save settings: {e}")

        return jsonify({'success': True, 'parameters': params})

    except Exception as e:
        print(f"Error in update_parameters: {e}")
        return jsonify({'error': str(e)}), 500

def get_available_port(start_port=5000):
    """Find an available port starting from start_port"""
    import socket
    for port in range(start_port, start_port + 20):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            print(f"✅ Port {port} is available")
            return port
        except OSError:
            print(f"❌ Port {port} is in use, trying next...")
            continue
    return 8080  # Fallback port

if __name__ == '__main__':
    print("🌐 Starting DeFi Agent Web Dashboard")
    print("📱 Access your dashboard at the web preview URL")

    # Use port 5000 for deployment consistency
    port = 5000
    print(f"🌐 Starting web dashboard on port {port}")
    print(f"🔗 Dashboard will be accessible at your Replit webview URL")

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)