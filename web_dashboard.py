
from flask import Flask, render_template, jsonify, request
import json
import os
import time
from datetime import datetime
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from dashboard import AgentDashboard
import threading

app = Flask(__name__)
agent = None
dashboard = None

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
        
        return jsonify({
            'wallet_address': agent.address,
            'eth_balance': eth_balance,
            'usdc_balance': usdc_balance,
            'health_factor': health_data['health_factor'],
            'total_collateral': health_data['total_collateral_eth'],
            'total_debt': health_data['total_debt_eth'],
            'available_borrows': health_data['available_borrows_eth'],
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
    """Get current adjustable parameters"""
    try:
        if dashboard:
            return jsonify(dashboard.adjustable_params)
        else:
            return jsonify({
                'health_factor_target': 1.19,
                'borrow_trigger_threshold': 0.02,
                'arb_decline_threshold': 0.05,
                'auto_mode': True
            })
    except Exception as e:
        return jsonify({'error': str(e)})

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

if __name__ == '__main__':
    print("🌐 Starting DeFi Agent Web Dashboard")
    print("📱 Access your dashboard at the web preview URL")
    app.run(host='0.0.0.0', port=5000, debug=True)
