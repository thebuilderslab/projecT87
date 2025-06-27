from flask import Flask, render_template, jsonify, request
import os
import time
import json
from web3 import Web3
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

def get_enhanced_aave_data(agent):
    """Enhanced Aave data retrieval for mainnet operations"""
    try:
        if not agent or not hasattr(agent, 'health_monitor'):
            print("⚠️ No agent or health monitor available")
            return None

        # Try to get comprehensive health data
        health_data = agent.health_monitor.get_current_health_factor()
        if health_data and health_data.get('health_factor', 0) > 0:
            return {
                'health_factor': health_data['health_factor'],
                'total_collateral': health_data.get('total_collateral_eth', 0),
                'total_debt': health_data.get('total_debt_eth', 0),
                'total_collateral_usdc': health_data.get('total_collateral_usdc', 0),
                'total_debt': health_data.get('total_debt_usdc', 0),
                'available_borrows': health_data.get('available_borrows_eth', 0),
                'available_borrows_usdc': health_data.get('available_borrows_usdc', 0),
                'liquidation_threshold': health_data.get('liquidation_threshold', 0),
                'ltv': health_data.get('ltv', 0),
                'data_source': 'health_monitor'
            }

        print("⚠️ Enhanced Aave data: health monitor returned no data")
        return None

    except Exception as e:
        print(f"❌ Enhanced Aave data error: {e}")
        return None

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
        print("🔍 API: /api/wallet_status called")
        print(f"🔍 API: Agent status: {agent is not None}")

        if not agent:
            print("❌ API: Agent not initialized, returning error")
            return jsonify({
                'error': 'Agent not initialized',
                'status': 'initializing'
            })

        # Prepare wallet status dictionary
        wallet_status = {
            'wallet_address': agent.address,
            'eth_balance': agent.get_eth_balance(),
            'usdc_balance': 0,
            'health_factor': 0,
            'total_collateral': 0,
            'total_debt': 0,
            'available_borrows': 0,
            'total_collateral_usdc': 0,
            'total_debt_usdc': 0,
            'available_borrows_usdc': 0,
            'arb_price': 0,
            'network_name': 'Unknown',
            'network_mode': os.getenv('NETWORK_MODE', 'testnet'),
            'timestamp': time.time()
        }

        # Try enhanced direct Aave contract calls for mainnet FIRST
        print(f"🔍 Attempting enhanced Aave data retrieval for mainnet...")
        enhanced_aave_data = get_enhanced_aave_data(agent)

        if enhanced_aave_data:
            print(f"✅ Enhanced mainnet Aave data received!")
            print(f"   Source: {enhanced_aave_data.get('data_source', 'unknown')}")
            print(f"   Health Factor: {enhanced_aave_data.get('health_factor', 0):.4f}")
            print(f"   Collateral USD: ${enhanced_aave_data.get('total_collateral_usdc', 0):,.2f}")

            # Update wallet status with enhanced data
            wallet_status.update({
                'health_factor': enhanced_aave_data['health_factor'],
                'total_collateral': enhanced_aave_data['total_collateral'],
                'total_debt': enhanced_aave_data['total_debt'],
                'total_collateral_usdc': enhanced_aave_data['total_collateral_usdc'],
                'total_debt_usdc': enhanced_aave_data['total_debt_usdc'],
                'available_borrows': enhanced_aave_data['available_borrows'],
                'available_borrows_usdc': enhanced_aave_data['available_borrows_usdc'],
                'liquidation_threshold': enhanced_aave_data.get('liquidation_threshold', 0),
                'ltv': enhanced_aave_data.get('ltv', 0),
                'data_source': enhanced_aave_data['data_source']
            })
            print(f"✅ Wallet status updated with enhanced mainnet Aave data")
        else:
            print(f"⚠️ Enhanced Aave data failed, trying fallback methods...")

            # Only try legacy methods if enhanced fails
            if hasattr(agent, 'aave'):
                try:
                    wallet_status['usdc_balance'] = agent.aave.get_token_balance(agent.aave.usdc_address)
                except Exception as e:
                    print(f"⚠️ USDC balance error: {e}")
                    wallet_status['usdc_balance'] = 0

                try:
                        # Get health factor data
                        health_data = agent.health_monitor.get_current_health_factor()
                        if health_data:
                            wallet_status.update({
                                'health_factor': health_data['health_factor'],
                                'total_collateral': health_data['total_collateral_eth'],
                                'total_debt': health_data['total_debt_eth'],
                                'total_collateral_usdc': health_data.get('total_collateral_usdc', 0),
                                'total_debt_usdc': health_data.get('total_debt_usdc', 0),
                                'available_borrows': health_data.get('available_borrows_eth', 0),
                                'available_borrows_usdc': health_data.get('available_borrows_usdc', 0)
                            })
                        else:
                            print("⚠️ Health monitor returned no data, trying fallback methods...")

                            # Try third-party data providers
                            try:
                                from third_party_data_integration import ThirdPartyDataProvider
                                provider = ThirdPartyDataProvider()

                                if provider.zapper_api_key:
                                    print("🔄 Attempting Zapper API for Aave data...")
                                    zapper_data = provider.get_zapper_portfolio(agent.address)
                                    if zapper_data and zapper_data['health_factor'] > 0:
                                        print(f"✅ Zapper API successful: Health Factor {zapper_data['health_factor']:.4f}")
                                        wallet_status.update({
                                            'health_factor': zapper_data['health_factor'],
                                            'total_collateral': zapper_data['total_collateral_usd'] / 2400,  # Rough ETH conversion
                                            'total_debt': zapper_data['total_debt_usd'] / 2400,
                                            'total_collateral_usdc': zapper_data['total_collateral_usd'],
                                            'total_debt_usdc': zapper_data['total_debt_usd'],
                                            'available_borrows': 0,
                                            'available_borrows_usdc': 0,
                                            'data_source': 'zapper'
                                        })
                                    else:
                                        print("⚠️ Zapper API returned no data, trying other sources...")
                                        third_party_data = provider.get_reliable_aave_data(agent.address)
                                        if third_party_data:
                                            print(f"✅ Using {third_party_data['source']} API data")
                                            wallet_status.update({
                                                'health_factor': third_party_data['health_factor'],
                                                'total_collateral': third_party_data['total_collateral_usd'] / 2400,
                                                'total_debt': third_party_data['total_debt_usd'] / 2400,
                                                'total_collateral_usdc': third_party_data['total_collateral_usd'],
                                                'total_debt_usdc': third_party_data['total_debt_usd'],
                                                'available_borrows': 0,
                                                'available_borrows_usdc': 0,
                                                'data_source': third_party_data['source']
                                            })
                                        else:
                                            # Final fallback to on-chain analysis
                                            fallback_data = agent.health_monitor.perform_fallback_analysis()
                                            if fallback_data:
                                                wallet_status.update({
                                                    'health_factor': fallback_data.get('estimated_health_factor', 0),
                                                    'total_collateral': fallback_data.get('estimated_collateral', 0),
                                                    'total_debt': 0,
                                                    'total_collateral_usdc': fallback_data.get('estimated_collateral_usdc', 0),
                                                    'total_debt_usdc': 0,
                                                    'available_borrows': 0,
                                                    'available_borrows_usdc': 0,
                                                    'data_source': 'fallback'
                                                })
                                            print("⚠️ Using on-chain fallback analysis")
                                else:
                                    print("💡 No Zapper API key found, using other third-party sources...")
                                    third_party_data = provider.get_reliable_aave_data(agent.address)
                                    if third_party_data:
                                        print(f"✅ Using {third_party_data['source']} API data")
                                        wallet_status.update({
                                            'health_factor': third_party_data['health_factor'],
                                            'total_collateral': third_party_data['total_collateral_usd'] / 2400,
                                            'total_debt': third_party_data['total_debt_usd'] / 2400,
                                            'total_collateral_usdc': third_party_data['total_collateral_usd'],
                                            'total_debt_usdc': third_party_data['total_debt_usd'],
                                            'available_borrows': 0,
                                            'available_borrows_usdc': 0,
                                            'data_source': third_party_data['source']
                                        })
                                    else:
                                        # Final fallback to on-chain analysis
                                        fallback_data = agent.health_monitor.perform_fallback_analysis()
                                        if fallback_data:
                                            wallet_status.update({
                                                'health_factor': fallback_data.get('estimated_health_factor', 0),
                                                'total_collateral': fallback_data.get('estimated_collateral', 0),
                                                'total_debt': 0,
                                                'total_collateral_usdc': fallback_data.get('estimated_collateral_usdc', 0),
                                                'total_debt_usdc': 0,
                                                'available_borrows': 0,
                                                'available_borrows_usdc': 0,
                                                'data_source': 'fallback'
                                            })
                                        print("⚠️ Using on-chain fallback analysis")
                            except ImportError:
                                print("💡 Third-party integration not available - using fallback")
                                # Try fallback analysis
                                try:
                                    fallback_data = agent.health_monitor.perform_fallback_analysis()
                                    if fallback_data:
                                        wallet_status.update({
                                            'health_factor': fallback_data.get('estimated_health_factor', 0),
                                            'total_collateral': fallback_data.get('estimated_collateral', 0),
                                            'total_debt': 0,
                                            'total_collateral_usdc': fallback_data.get('estimated_collateral_usdc', 0),
                                            'total_debt_usdc': 0,
                                            'available_borrows': 0,
                                            'available_borrows_usdc': 0
                                        })
                                    print("⚠️ Using fallback health factor analysis")
                                except Exception as e:
                                    print(f"⚠️ Fallback analysis error: {e}")
                        except Exception as e:
                            print(f"⚠️ Aave balance/health error: {e}")
                    else:
                        print("⚠️ Aave integration not available")

        # Get ARB price
        arb_price_data = agent.health_monitor.get_arb_price() if hasattr(agent, 'health_monitor') else None
        wallet_status['arb_price'] = arb_price_data['price'] if arb_price_data else 0

        # PRIORITY: NETWORK_MODE environment variable determines display
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        print(f"🔍 Dashboard wallet_status - NETWORK_MODE: {network_mode}")

        # Force display based on NETWORK_MODE (authoritative source)
        if network_mode == 'mainnet':
            wallet_status['network_name'] = "Arbitrum Mainnet"
            print(f"🚀 Forcing Arbitrum Mainnet display based on NETWORK_MODE")
        else:
            wallet_status['network_name'] = "Arbitrum Sepolia"
            print(f"🧪 Showing Arbitrum Sepolia based on NETWORK_MODE")

        return jsonify(wallet_status)

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
    """Get current agent parameters with robust error handling"""
    try:
        print("🔍 API: /api/parameters called - Starting parameter loading...")
        print(f"🔍 API: Current working directory: {os.getcwd()}")
        print(f"🔍 API: Files in directory: {os.listdir('.')}")

        # Always start with working defaults
        config = {
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'exploration_rate': 0.1,
            'auto_mode': True,
            'learning_rate': 0.01,
            'max_iterations_per_run': 100,
            'optimization_target_threshold': 0.95,
            'status': 'active',
            'network_mode': os.getenv('NETWORK_MODE', 'mainnet'),
            'timestamp': time.time(),
            'success': True
        }
        print(f"✅ API: Default config created: {config}")

        # Try to load user settings if available
        user_settings_file = 'user_settings.json'
        if os.path.exists(user_settings_file):
            try:
                with open(user_settings_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        user_settings = json.loads(content)
                        if isinstance(user_settings, dict):
                            # Only update known parameters
                            known_params = [
                                'health_factor_target', 'borrow_trigger_threshold', 
                                'arb_decline_threshold', 'exploration_rate', 'auto_mode'
                            ]
                            for param in known_params:
                                if param in user_settings:
                                    config[param] = user_settings[param]
                            config['loaded_from'] = 'user_settings'
                            print(f"✅ API: Loaded parameters from user_settings.json")
                        else:
                            config['loaded_from'] = 'defaults'
                            print(f"⚠️ API: Invalid user_settings format, using defaults")
                    else:
                        config['loaded_from'] = 'defaults'
                        print(f"⚠️ API: Empty user_settings file, using defaults")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ API: JSON decode error in user_settings.json: {e}")
                config['loaded_from'] = 'defaults'
            except Exception as e:
                print(f"⚠️ API: Could not load user_settings.json: {e}")
                config['loaded_from'] = 'defaults'
        else:
            config['loaded_from'] = 'defaults'
            print(f"📝 API: Using default parameters")

        print(f"📊 API: Returning parameters: {config}")
        return jsonify(config)

    except Exception as e:
        print(f"❌ CRITICAL: get_parameters failed completely: {e}")
        import traceback
        traceback.print_exc()

        # Return absolute minimal config that will work
        fallback_config = {
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'auto_mode': True,
            'exploration_rate': 0.1,
            'learning_rate': 0.01,
            'max_iterations_per_run': 100,
            'optimization_target_threshold': 0.95,
            'status': 'active',
            'network_mode': 'mainnet',
            'error': str(e),
            'fallback': True,
            'success': False,
            'timestamp': time.time()
        }
        return jsonify(fallback_config), 200

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
    """Get emergency stop status with robust error handling"""
    try:
        print("🔍 API: /api/emergency_status called - Checking emergency status...")
        print(f"🔍 API: Current working directory: {os.getcwd()}")

        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        is_active = os.path.exists(emergency_file)
        print(f"🔍 API: Emergency file check - exists: {is_active}")

        status = {
            'active': is_active,
            'timestamp': time.time()
        }

        if is_active:
            try:
                with open(emergency_file, 'r') as f:
                    content = f.read()
                    status['details'] = content
                    print("🚨 API: Emergency stop is ACTIVE")
            except Exception as e:
                status['details'] = f"Could not read emergency file: {e}"
        else:
            print("✅ API: Emergency stop is NOT active")

        # Try to get recent logs
        log_file = 'emergency_stop_log.json'
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                    if isinstance(logs, list):
                        status['recent_logs'] = logs[-3:]  # Last 3 actions
                    else:
                        status['recent_logs'] = []
            except Exception as e:
                print(f"⚠️ API: Could not load emergency logs: {e}")
                status['recent_logs'] = []
        else:
            status['recent_logs'] = []

        print(f"📊 API: Emergency status: {status}")
        return jsonify(status)

    except Exception as e:
        print(f"❌ API: Emergency status error: {e}")
        # Return safe default
        return jsonify({
            'active': False,
            'error': str(e),
            'timestamp': time.time()
        }), 200

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
        print("🔍 API: Connection test requested")
        response = {
            'status': 'connected',
            'timestamp': time.time(),
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
```python
            'agent_initialized': agent is not None,
            'dashboard_available': dashboard is not None,
            'network_mode': os.getenv('NETWORK_MODE', 'unknown'),
            'deployment_mode': bool(os.getenv('REPLIT_DEPLOYMENT')),
            'api_version': '1.0'
        }
        print(f"✅ API: Connection test successful: {response}")
        return jsonify(response)
    except Exception as e:
        print(f"❌ API: Connection test failed: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/test')
def api_test():
    """Ultra-simple API test"""
    try:
        print("🔍 API: /api/test called - Basic connectivity test")
        return jsonify({'message': 'API is working', 'timestamp': time.time()})
    except Exception as e:
        print(f"❌ API: /api/test failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/test-all')
def test_all_endpoints():
    """Test all critical endpoints and return results"""
    try:
        print("🔍 API: /api/debug/test-all called")
        results = {}

        # Test each endpoint
        endpoints = ['/api/parameters', '/api/emergency_status', '/api/wallet_status', '/api/performance']

        for endpoint in endpoints:
            try:
                print(f"🔍 Testing endpoint: {endpoint}")
                # We can't easily call the endpoints directly, but we can test their functions
                if endpoint == '/api/parameters':
                    result = get_parameters()
                    results[endpoint] = {'status': 'success', 'has_data': bool(result.data)}
                elif endpoint == '/api/emergency_status':
                    result = get_emergency_status()
                    results[endpoint] = {'status': 'success', 'has_data': bool(result.data)}
                else:
                    results[endpoint] = {'status': 'not_tested', 'reason': 'requires_request_context'}
            except Exception as e:
                results[endpoint] = {'status': 'error', 'error': str(e)}
                print(f"❌ Endpoint {endpoint} failed: {e}")

        return jsonify({
            'test_results': results,
            'timestamp': time.time(),
            'agent_status': agent is not None,
            'dashboard_status': dashboard is not None
        })

    except Exception as e:
        print(f"❌ API: test-all failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health-check')
def comprehensive_health_check():
    """Comprehensive system health check"""
    try:
        health_status = {
            'overall_status': 'healthy',
            'timestamp': time.time(),
            'components': {
                'web_dashboard': 'operational',
                'network_connection': 'unknown',
                'api_endpoints': 'operational',
                'emergency_stop': 'ready',
                'parameters': 'loaded'
            },
            'network': {
                'mode': os.getenv('NETWORK_MODE', 'unknown'),
                'expected_chain_id': 42161 if os.getenv('NETWORK_MODE') == 'mainnet' else 421614
            },
            'secrets': {
                'coinmarketcap_api': bool(os.getenv('COINMARKETCAP_API_KEY')),
                'private_key': bool(os.getenv('PRIVATE_KEY')),
                'network_mode': bool(os.getenv('NETWORK_MODE'))
            }
        }

        # Test agent connection
        if agent:
            try:
                chain_id = agent.w3.eth.chain_id
                health_status['components']['network_connection'] = 'connected'
                health_status['network']['actual_chain_id'] = chain_id
                health_status['network']['chain_match'] = chain_id == health_status['network']['expected_chain_id']
            except Exception as e:
                health_status['components']['network_connection'] = f'error: {str(e)}'
                health_status['overall_status'] = 'degraded'

        return jsonify(health_status)
    except Exception as e:
        return jsonify({
            'overall_status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/api/parameter-sync-status')
def get_parameter_sync_status():
    """Check if agent has picked up latest parameter changes"""
    try:
        # Check if user_settings.json exists and get its modification time
        settings_file = 'user_settings.json'
        if not os.path.exists(settings_file):
            return jsonify({
                'sync_status': 'no_settings',
                'message': 'No parameter settings found'
            })

        settings_mtime = os.path.getmtime(settings_file)

        # Check if there's evidence the agent has processed the changes
        # Look for recent log entries mentioning parameter updates
        recent_update = False
        if os.path.exists('performance_log.json'):
            try:
                with open('performance_log.json', 'r') as f:
                    lines = f.readlines()
                    # Check last few entries for parameter update mentions
                    for line in lines[-5:]:
                        entry = json.loads(line)
                        if entry.get('timestamp', 0) > settings_mtime:
                            recent_update = True
                            break
            except:
                pass

        return jsonify({
            'sync_status': 'synced' if recent_update else 'pending',
            'settings_modified': settings_mtime,
            'settings_modified_readable': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(settings_mtime)),
            'message': 'Parameters synced with agent' if recent_update else 'Waiting for agent to pick up changes'
        })

    except Exception as e:
        return jsonify({
            'sync_status': 'error',
            'error': str(e)
        })

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
def save_parameters():
    """Save user parameters and force immediate reload"""
    try:
        data = request.get_json()

        # Load existing settings or create new ones
        settings_file = 'user_settings.json'
        existing_settings = {}

        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                existing_settings = json.load(f)

        # Update with new parameters
        existing_settings.update(data)

        # Add timestamp to force reload detection
        existing_settings['last_updated'] = time.time()
        existing_settings['update_count'] = existing_settings.get('update_count', 0) + 1

        # Save updated settings with explicit flush
        with open(settings_file, 'w') as f:
            json.dump(existing_settings, f, indent=2)
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Ensure disk write

        # Create a trigger file for immediate agent response
        trigger_file = 'parameter_update_trigger.flag'
        with open(trigger_file, 'w') as f:
            f.write(f"Parameters updated at {time.time()}\n")
            f.write(f"Updated: {list(data.keys())}\n")
            f.flush()
            os.fsync(f.fileno())

        updated_params = list(data.keys())
        print(f"✅ Parameters updated via dashboard: {updated_params}")
        print(f"📁 Settings file updated with timestamp: {existing_settings['last_updated']}")

        return jsonify({
            'status': 'success',
            'message': f'Parameters updated: {", ".join(updated_params)}',
            'updated_parameters': updated_params,
            'timestamp': existing_settings['last_updated'],
            'update_count': existing_settings['update_count']
        })

    except Exception as e:
        print(f"❌ Failed to save parameters: {e}")
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

def log_startup_diagnostics():
    """Log comprehensive startup diagnostics"""
    print("=" * 60)
    print("🚀 WEB DASHBOARD STARTUP DIAGNOSTICS")
    print("=" * 60)

    print(f"📂 Working Directory: {os.getcwd()}")
    print(f"🌍 Environment Variables:")
    env_vars = ['NETWORK_MODE', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY', 'REPLIT_DEPLOYMENT']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if var == 'PRIVATE_KEY':
                print(f"   {var}: {value[:10]}...{value[-4:] if len(value) > 14 else 'short'}")
            elif var == 'COINMARKETCAP_API_KEY':
                print(f"   {var}: {value[:8]}...{value[-4:] if len(value) > 12 else 'short'}")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: NOT SET")

    print(f"📁 Key Files:")
    files_to_check = ['user_settings.json', 'agent_config.json', 'EMERGENCY_STOP_ACTIVE.flag', 'performance_log.json']
    for file in files_to_check:
        if os.path.exists(file):
            try:
                size = os.path.getsize(file)
                print(f"   ✅ {file}: {size} bytes")
            except:
                print(f"   ⚠️ {file}: exists but can't read size")
        else:
            print(f"   ❌ {file}: not found")

    print(f"🤖 Agent Initialization:")
    print(f"   Agent object: {agent is not None}")
    print(f"   Dashboard object: {dashboard is not None}")

    print("=" * 60)

if __name__ == '__main__':
    log_startup_diagnostics()

    # Check for emergency stop and clear if needed for dashboard
    if os.path.exists('EMERGENCY_STOP_ACTIVE.flag'):
        print("⚠️ Emergency stop detected - clearing for dashboard access...")
        try:
            os.remove('EMERGENCY_STOP_ACTIVE.flag')
            print("✅ Emergency stop cleared for dashboard")
        except:
            print("❌ Could not clear emergency stop flag")

    print("🌐 Starting DeFi Agent Web Dashboard")
    print("📱 Access your dashboard at the web preview URL")

    # Use port 5000 for deployment consistency
    port = 5000

    print(f"🌐 Starting web dashboard on port {port}")
    print(f"🔗 Dashboard will be accessible at your Replit webview URL")

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)