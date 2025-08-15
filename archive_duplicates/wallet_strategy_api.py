
from flask import Flask, request, jsonify
from multi_wallet_agent import MultiWalletAgent, create_multi_wallet_prompt
import threading
import time

app = Flask(__name__)
agent = MultiWalletAgent()

# Store active monitoring sessions
monitoring_sessions = {}

@app.route('/execute_strategy', methods=['POST'])
def execute_strategy():
    """API endpoint to execute strategy for a wallet"""
    try:
        data = request.json
        
        wallet_address = data.get('wallet_address')
        network = data.get('network', 'arbitrum_mainnet')
        strategy_type = data.get('strategy_type', 'monitor_only')
        
        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400
        
        # Validate wallet address format
        from web3 import Web3
        if not Web3.is_address(wallet_address):
            return jsonify({'error': 'Invalid wallet address format'}), 400
        
        strategy_config = {
            'type': strategy_type,
            'health_factor_target': data.get('health_factor_target', 1.19),
            'borrow_trigger_threshold': data.get('borrow_trigger_threshold', 0.02),
            'risk_mitigation_enabled': data.get('risk_mitigation_enabled', True)
        }
        
        # Execute strategy
        result = agent.execute_strategy_for_wallet(wallet_address, network, strategy_config)
        
        return jsonify({
            'success': True,
            'wallet_address': wallet_address,
            'network': network,
            'strategy_type': strategy_type,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/monitor_wallet', methods=['POST'])
def monitor_wallet():
    """Start continuous monitoring for a wallet"""
    try:
        data = request.json
        
        wallet_address = data.get('wallet_address')
        network = data.get('network', 'arbitrum_mainnet')
        
        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400
        
        session_id = f"{network}_{wallet_address}"
        
        # Start monitoring thread
        if session_id not in monitoring_sessions:
            monitoring_thread = threading.Thread(
                target=continuous_monitoring,
                args=(wallet_address, network, session_id)
            )
            monitoring_thread.daemon = True
            monitoring_thread.start()
            
            monitoring_sessions[session_id] = {
                'wallet_address': wallet_address,
                'network': network,
                'status': 'active',
                'started_at': time.time()
            }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': 'monitoring_started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    """Stop monitoring for a wallet"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id in monitoring_sessions:
            monitoring_sessions[session_id]['status'] = 'stopped'
            return jsonify({'success': True, 'status': 'monitoring_stopped'})
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/wallet_status/<wallet_address>')
def wallet_status(wallet_address):
    """Get current status of a wallet"""
    try:
        network = request.args.get('network', 'arbitrum_mainnet')
        
        strategy_config = {'type': 'monitor_only'}
        result = agent.execute_strategy_for_wallet(wallet_address, network, strategy_config)
        
        # Get session info
        session_id = f"{network}_{wallet_address}"
        session_info = monitoring_sessions.get(session_id, {})
        
        return jsonify({
            'wallet_address': wallet_address,
            'network': network,
            'monitoring_active': session_info.get('status') == 'active',
            'last_check': time.time(),
            'strategy_result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_prompt', methods=['POST'])
def generate_prompt():
    """Generate strategy prompt for a wallet"""
    try:
        data = request.json
        
        wallet_address = data.get('wallet_address')
        network = data.get('network', 'arbitrum_mainnet')
        strategy_type = data.get('strategy_type', 'dynamic_health')
        
        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400
        
        prompt = create_multi_wallet_prompt(wallet_address, network)
        
        return jsonify({
            'wallet_address': wallet_address,
            'network': network,
            'strategy_prompt': prompt
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def continuous_monitoring(wallet_address, network, session_id):
    """Continuous monitoring function"""
    print(f"🔄 Starting continuous monitoring for {wallet_address} on {network}")
    
    while True:
        try:
            session = monitoring_sessions.get(session_id)
            if not session or session.get('status') != 'active':
                break
            
            # Execute monitoring
            strategy_config = {'type': 'monitor_only'}
            agent.execute_strategy_for_wallet(wallet_address, network, strategy_config)
            
            # Wait before next check
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"❌ Monitoring error for {session_id}: {e}")
            time.sleep(30)  # Wait before retrying
    
    print(f"🛑 Stopped monitoring for {session_id}")

if __name__ == '__main__':
    print("🌐 Multi-Wallet DeFi Strategy API")
    print("=" * 50)
    print("📍 Available endpoints:")
    print("   POST /execute_strategy - Execute strategy for wallet")
    print("   POST /monitor_wallet - Start continuous monitoring")
    print("   POST /stop_monitoring - Stop monitoring")
    print("   GET /wallet_status/<address> - Get wallet status")
    print("   POST /generate_prompt - Generate strategy prompt")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
