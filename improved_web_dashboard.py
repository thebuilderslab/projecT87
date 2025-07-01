
#!/usr/bin/env python3
"""
Improved Web Dashboard - DeBank Style Interface
Uses accurate data fetching and displays real wallet information
"""

from flask import Flask, render_template, jsonify, request
import os
import time
import json
import threading
from accurate_debank_fetcher import AccurateWalletDataFetcher

app = Flask(__name__)

# Global state
wallet_data = {}
fetcher = None
last_update = 0

def initialize_system():
    """Initialize the wallet data fetcher"""
    global fetcher, wallet_data
    
    try:
        print("🚀 Initializing improved dashboard system...")
        
        # Force mainnet mode
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent('mainnet')
        
        # Initialize accurate fetcher
        fetcher = AccurateWalletDataFetcher(agent.w3, agent.address)
        
        # Initial data fetch
        update_wallet_data()
        
        print("✅ Dashboard system initialized successfully")
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        
        # Create minimal fallback data
        wallet_data = {
            'wallet_address': '0x5B823270e3719CDe8669e5e5326B455EaA8a350b',
            'network_name': 'Arbitrum Mainnet',
            'eth_balance': 0.001935,
            'wbtc_balance': 0.0002,
            'health_factor': 6.20,
            'total_collateral_usdc': 157.05,
            'total_debt_usdc': 20.00,
            'success': False,
            'error': str(e)
        }

def update_wallet_data():
    """Update wallet data from fetcher"""
    global wallet_data, last_update
    
    try:
        if fetcher:
            wallet_data = fetcher.get_comprehensive_wallet_data()
            last_update = time.time()
            print(f"✅ Wallet data updated at {time.strftime('%H:%M:%S')}")
        else:
            print("⚠️ No fetcher available for data update")
            
    except Exception as e:
        print(f"❌ Data update failed: {e}")
        wallet_data['last_error'] = str(e)
        wallet_data['last_error_time'] = time.time()

def background_data_updater():
    """Background thread to update data every 30 seconds"""
    while True:
        try:
            time.sleep(30)  # Update every 30 seconds
            update_wallet_data()
        except Exception as e:
            print(f"❌ Background update error: {e}")
            time.sleep(60)  # Wait longer on error

# Start background updater
def start_background_updater():
    """Start the background data update thread"""
    updater_thread = threading.Thread(target=background_data_updater, daemon=True)
    updater_thread.start()
    print("✅ Background data updater started")

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('improved_dashboard.html')

@app.route('/api/wallet-status')
def api_wallet_status():
    """API endpoint for wallet status"""
    try:
        # Ensure we have recent data
        if time.time() - last_update > 60:  # If data is older than 1 minute
            update_wallet_data()
        
        return jsonify(wallet_data)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False,
            'timestamp': time.time()
        }), 200

@app.route('/api/refresh-data', methods=['POST'])
def api_refresh_data():
    """Manually refresh wallet data"""
    try:
        update_wallet_data()
        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully',
            'timestamp': last_update
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/api/system-status')
def api_system_status():
    """Get system status information"""
    return jsonify({
        'fetcher_initialized': fetcher is not None,
        'last_update': last_update,
        'data_age_seconds': time.time() - last_update if last_update > 0 else -1,
        'wallet_address': wallet_data.get('wallet_address', 'Unknown'),
        'network': wallet_data.get('network_name', 'Unknown'),
        'success': wallet_data.get('success', False),
        'timestamp': time.time()
    })

@app.route('/api/emergency-stop', methods=['POST'])
def api_emergency_stop():
    """Emergency stop endpoint"""
    try:
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        with open(emergency_file, 'w') as f:
            f.write(f"Emergency stop activated at {time.time()}\n")
            f.write("Source: Improved Dashboard\n")
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop activated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/emergency-stop', methods=['DELETE'])
def api_clear_emergency_stop():
    """Clear emergency stop"""
    try:
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        if os.path.exists(emergency_file):
            os.remove(emergency_file)
            return jsonify({
                'success': True,
                'message': 'Emergency stop cleared'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No emergency stop active'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def setup_app():
    """Set up the Flask app"""
    print("🔧 Setting up improved dashboard...")
    
    # Initialize system
    initialize_system()
    
    # Start background updater
    start_background_updater()
    
    print("✅ Dashboard setup complete")

if __name__ == '__main__':
    setup_app()
    
    print("🌐 Starting Improved DeFi Dashboard")
    print("📊 DeBank-style interface with accurate data")
    print("🔗 Access via your Replit webview URL")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
