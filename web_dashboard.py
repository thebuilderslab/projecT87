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

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

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
    """Get current agent parameters"""
    try:
        if os.path.exists('agent_config.json'):
            with open('agent_config.json', 'r') as f:
                config = json.load(f)
        else:
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

        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/parameters', methods=['POST'])
def update_parameters():
    """Update adjustable parameters"""
    try:
        if not dashboard:
            return jsonify({'error': 'Dashboard not initialized'})

        data = request.json

        # Validate and update parameters
        if 'health_factor_target' in data:
            value = float(data['health_factor_target'])
            if 1.05 <= value <= 3.0:
                dashboard.adjustable_params['health_factor_target'] = value

        if 'borrow_trigger_threshold' in data:
            value = float(data['borrow_trigger_threshold'])
            if 0.001 <= value <= 0.5:
                dashboard.adjustable_params['borrow_trigger_threshold'] = value

        if 'arb_decline_threshold' in data:
            value = float(data['arb_decline_threshold'])
            if 0.01 <= value <= 0.5:
                dashboard.adjustable_params['arb_decline_threshold'] = value

        if 'auto_mode' in data:
            dashboard.adjustable_params['auto_mode'] = bool(data['auto_mode'])

        # Save settings
        dashboard.save_user_settings()

        return jsonify({'success': True, 'parameters': dashboard.adjustable_params})

    except Exception as e:
        return jsonify({'error': str(e)})

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
    
    # Find available port with detailed logging
    port = get_available_port(5000)
    print(f"🌐 Starting web dashboard on port {port}")
    print(f"🔗 Dashboard will be accessible at your Replit webview URL")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)