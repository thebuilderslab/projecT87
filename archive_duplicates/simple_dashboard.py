#!/usr/bin/env python3
"""
Simple Emergency Dashboard
Works even when agent initialization fails
"""

from flask import Flask, render_template_string, jsonify, request
import os
import time
import json
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from gas_fee_calculator import ArbitrumGasCalculator

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emergency DeFi Dashboard</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
        }
        .status-card {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }
        .error-card {
            border-left-color: #f44336;
        }
        .warning-card {
            border-left-color: #ff9800;
        }
        .refresh-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 5px;
        }
        .refresh-btn:hover { background: #45a049; }
        .emergency-btn { background: #f44336; }
        .emergency-btn:hover { background: #da190b; }
        pre { 
            background: rgba(0,0,0,0.3); 
            padding: 10px; 
            border-radius: 5px; 
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚨 Emergency DeFi Dashboard</h1>

        <div class="status-card">
            <h3>📊 Dashboard Status</h3>
            <p>✅ Emergency Dashboard Active</p>
            <p>🕐 Last Update: <span id="lastUpdate">Loading...</span></p>
        </div>

        <div id="networkStatus" class="status-card">
            <h3>🌐 Network Status</h3>
            <p id="networkInfo">Loading...</p>
        </div>

        <div id="agentStatus" class="status-card">
            <h3>🤖 Agent Status</h3>
            <p id="agentInfo">Loading...</p>
        </div>

        <div id="secretsStatus" class="status-card">
            <h3>🔐 Secrets Status</h3>
            <p id="secretsInfo">Loading...</p>
        </div>

        <div class="status-card">
            <h3>🛠️ Emergency Actions</h3>
            <button class="refresh-btn" onclick="checkSecrets()">🔍 Check Secrets</button>
            <button class="refresh-btn" onclick="testAgent()">🤖 Test Agent</button>
            <button class="refresh-btn emergency-btn" onclick="emergencyStop()">🛑 Emergency Stop</button>
        </div>

        <div id="logs" class="status-card">
            <h3>📝 System Logs</h3>
            <pre id="logContent">Loading system status...</pre>
        </div>
    </div>

    <script>
        function updateTime() {
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
        }

        function checkSecrets() {
            fetch('/api/check-secrets')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('secretsInfo').innerHTML = 
                        `PRIVATE_KEY: ${data.private_key ? '✅ SET' : '❌ NOT SET'}<br>
                         NETWORK_MODE: ${data.network_mode || 'NOT SET'}<br>
                         COINMARKETCAP_API_KEY: ${data.coinmarketcap ? '✅ SET' : '❌ NOT SET'}`;
                });
        }

        function testAgent() {
            fetch('/api/test-agent')
                .then(r => r.json())
                .then(data => {
                    const statusDiv = document.getElementById('agentStatus');
                    if (data.success) {
                        statusDiv.className = 'status-card';
                        document.getElementById('agentInfo').innerHTML = 
                            `✅ Agent Working<br>
                             Address: ${data.address}<br>
                             Network: ${data.network}`;
                    } else {
                        statusDiv.className = 'status-card error-card';
                        document.getElementById('agentInfo').innerHTML = 
                            `❌ Agent Failed<br>
                             Error: ${data.error}`;
                    }
                });
        }

        function emergencyStop() {
            if (confirm('Activate emergency stop?')) {
                fetch('/api/emergency-stop', {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        alert(data.message);
                    });
            }
        }

        function loadStatus() {
            updateTime();
            checkSecrets();
            testAgent();

            // Update logs
            fetch('/api/system-status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('logContent').textContent = JSON.stringify(data, null, 2);
                });
             // Fetch wallet status
            fetch('/api/wallet_status')
                .then(r => r.json())
                .then(data => {
                    const networkInfoDiv = document.getElementById('networkStatus');
                    if (data.connected) {
                        networkInfoDiv.className = 'status-card';
                        document.getElementById('networkInfo').innerHTML =
                            `✅ Connected to ${data.network}<br>
                             Address: ${data.address}<br>
                             ETH Balance: ${data.eth_balance} ETH<br>
                             Gas Prices: ${data.current_gas_gwei} gwei<br>
                             Private Key Source: ${data.private_key_source}`;
                    } else {
                        networkInfoDiv.className = 'status-card error-card';
                        document.getElementById('networkInfo').innerHTML =
                            `❌ Not Connected<br>
                             Error: ${data.error}`;
                    }
                });
        }

        // Auto refresh
        setInterval(updateTime, 1000);
        setInterval(loadStatus, 30000);

        // Initial load
        loadStatus();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/check-secrets')
def check_secrets():
    return jsonify({
        'private_key': bool(os.getenv('PRIVATE_KEY') or os.getenv('PRIVATE_KEY2')),
        'network_mode': os.getenv('NETWORK_MODE', 'NOT SET'),
        'coinmarketcap': bool(os.getenv('COINMARKETCAP_API_KEY')),
        'prompt_key': bool(os.getenv('PROMPT_KEY')),
        'timestamp': time.time()
    })

@app.route('/api/test-agent')
def test_agent():
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        return jsonify({
            'success': True,
            'address': agent.address,
            'network': agent.w3.eth.chain_id,
            'balance': agent.get_eth_balance()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    try:
        with open('EMERGENCY_STOP_ACTIVE.flag', 'w') as f:
            f.write(f"Emergency stop activated at {time.time()}")
        return jsonify({'success': True, 'message': 'Emergency stop activated'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed: {e}'})

@app.route('/api/system-status')
def system_status():
    return jsonify({
        'timestamp': time.time(),
        'python_version': os.sys.version,
        'environment_vars': {
            k: 'SET' if v else 'NOT SET' 
            for k, v in {
                'NETWORK_MODE': os.getenv('NETWORK_MODE'),
                'PRIVATE_KEY': os.getenv('PRIVATE_KEY'),
                'PRIVATE_KEY2': os.getenv('PRIVATE_KEY2'),
                'COINMARKETCAP_API_KEY': os.getenv('COINMARKETCAP_API_KEY')
            }.items()
        },
        'emergency_stop_active': os.path.exists('EMERGENCY_STOP_ACTIVE.flag')
    })

@app.route('/api/wallet_status')
def wallet_status():
    """Get current wallet status with gas prices"""
    try:
        agent = ArbitrumTestnetAgent()

        # Get real-time gas prices
        gas_calc = ArbitrumGasCalculator()
        gas_prices = gas_calc.get_current_gas_prices()
        current_gas_gwei = agent.w3.from_wei(gas_prices['market'], 'gwei') if gas_prices else 0

        return jsonify({
            'address': agent.address,
            'eth_balance': f"{agent.get_eth_balance():.6f}",
            'network': 'Arbitrum Mainnet' if agent.w3.eth.chain_id == 42161 else 'Arbitrum Sepolia',
            'chain_id': agent.w3.eth.chain_id,
            'current_gas_gwei': f"{current_gas_gwei:.2f}",
            'private_key_source': 'PRIVATE_KEY' if os.getenv('PRIVATE_KEY') else 'PRIVATE_KEY2',
            'connected': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'connected': False})

if __name__ == '__main__':
    print("🚨 Starting Emergency Dashboard...")
    print("🌐 Available at: http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)