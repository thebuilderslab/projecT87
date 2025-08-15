
#!/usr/bin/env python3
"""
Working Dashboard - Based on old dashboard.py with fixes
"""

from flask import Flask, render_template_string, jsonify, request
import os
import time
import json
import threading
from datetime import datetime

app = Flask(__name__)

# Global agent instance
agent = None
dashboard_instance = None

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏦 DeFi Agent Dashboard</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255,255,255,0.15);
            padding: 20px;
            border-radius: 15px;
            border-left: 5px solid #4CAF50;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .status-card.error {
            border-left-color: #f44336;
        }
        .status-card.warning {
            border-left-color: #ff9800;
        }
        .status-card h3 {
            margin: 0 0 15px 0;
            font-size: 1.2em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-value {
            font-weight: bold;
        }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        .btn:hover { 
            background: #45a049; 
            transform: translateY(-2px);
        }
        .btn.emergency { 
            background: #f44336; 
        }
        .btn.emergency:hover { 
            background: #da190b; 
        }
        .btn.warning { 
            background: #ff9800; 
        }
        .btn.warning:hover { 
            background: #e68900; 
        }
        .controls {
            text-align: center;
            margin: 20px 0;
        }
        .last-update {
            text-align: center;
            opacity: 0.8;
            font-size: 0.9em;
        }
        .health-indicator {
            font-size: 2em;
            text-align: center;
            margin: 10px 0;
        }
        .health-safe { color: #4CAF50; }
        .health-warning { color: #ff9800; }
        .health-danger { color: #f44336; }
        
        .parameter-controls {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
        }
        .parameter-row {
            display: flex;
            align-items: center;
            margin: 10px 0;
            gap: 15px;
        }
        .parameter-row label {
            min-width: 200px;
            font-weight: bold;
        }
        .parameter-row input {
            flex: 1;
            padding: 8px;
            border: none;
            border-radius: 5px;
            background: rgba(255,255,255,0.2);
            color: white;
        }
        .parameter-row input::placeholder {
            color: rgba(255,255,255,0.7);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏦 DeFi Agent Dashboard</h1>
            <p class="last-update">Last Update: <span id="lastUpdate">Loading...</span></p>
        </div>

        <div class="status-grid">
            <!-- Wallet Status -->
            <div class="status-card" id="walletCard">
                <h3>💰 Wallet Status</h3>
                <div class="metric">
                    <span>Address:</span>
                    <span class="metric-value" id="walletAddress">Loading...</span>
                </div>
                <div class="metric">
                    <span>ETH Balance:</span>
                    <span class="metric-value" id="ethBalance">0 ETH</span>
                </div>
                <div class="metric">
                    <span>USDC Balance:</span>
                    <span class="metric-value" id="usdcBalance">0 USDC</span>
                </div>
                <div class="metric">
                    <span>Network:</span>
                    <span class="metric-value" id="networkName">Loading...</span>
                </div>
            </div>

            <!-- Aave Status -->
            <div class="status-card" id="aaveCard">
                <h3>🏥 Aave Protocol Status</h3>
                <div class="health-indicator" id="healthIndicator">
                    <span id="healthFactor">0.00</span>
                </div>
                <div class="metric">
                    <span>Total Collateral:</span>
                    <span class="metric-value" id="totalCollateral">$0.00</span>
                </div>
                <div class="metric">
                    <span>Total Debt:</span>
                    <span class="metric-value" id="totalDebt">$0.00</span>
                </div>
                <div class="metric">
                    <span>Available Borrows:</span>
                    <span class="metric-value" id="availableBorrows">$0.00</span>
                </div>
            </div>

            <!-- Performance -->
            <div class="status-card" id="performanceCard">
                <h3>📊 24h Performance</h3>
                <div class="metric">
                    <span>P/L:</span>
                    <span class="metric-value" id="pnl24h">+0.00%</span>
                </div>
                <div class="metric">
                    <span>Operations:</span>
                    <span class="metric-value" id="operations">0</span>
                </div>
                <div class="metric">
                    <span>Error Rate:</span>
                    <span class="metric-value" id="errorRate">0%</span>
                </div>
                <div class="metric">
                    <span>Status:</span>
                    <span class="metric-value" id="agentStatus">Loading...</span>
                </div>
            </div>

            <!-- Emergency Controls -->
            <div class="status-card" id="emergencyCard">
                <h3>🚨 Emergency Controls</h3>
                <div style="text-align: center;">
                    <button class="btn emergency" onclick="emergencyStop()">🛑 Emergency Stop</button>
                    <button class="btn warning" onclick="clearEmergencyStop()">✅ Clear Emergency</button>
                    <button class="btn" onclick="refreshData()">🔄 Refresh Data</button>
                </div>
                <div class="metric">
                    <span>Emergency Status:</span>
                    <span class="metric-value" id="emergencyStatus">Checking...</span>
                </div>
            </div>
        </div>

        <!-- Parameter Controls -->
        <div class="parameter-controls">
            <h3>⚙️ Agent Parameters</h3>
            <div class="parameter-row">
                <label>Health Factor Target:</label>
                <input type="number" id="healthFactorTarget" step="0.01" min="1.05" max="3.0" value="1.19">
            </div>
            <div class="parameter-row">
                <label>Borrow Trigger Threshold:</label>
                <input type="number" id="borrowTrigger" step="0.001" min="0.001" max="0.5" value="0.02">
            </div>
            <div class="parameter-row">
                <label>ARB Decline Threshold (%):</label>
                <input type="number" id="arbDecline" step="0.1" min="1" max="50" value="5">
            </div>
            <div class="parameter-row">
                <label>Auto Mode:</label>
                <input type="checkbox" id="autoMode" checked>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <button class="btn" onclick="saveParameters()">💾 Save Parameters</button>
                <button class="btn warning" onclick="resetParameters()">🔄 Reset to Defaults</button>
            </div>
        </div>
    </div>

    <script>
        let lastUpdateTime = 0;

        function updateTime() {
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
        }

        function updateHealthIndicator(healthFactor) {
            const indicator = document.getElementById('healthIndicator');
            const factorSpan = document.getElementById('healthFactor');
            factorSpan.textContent = healthFactor.toFixed(4);

            if (healthFactor > 2.0) {
                indicator.className = 'health-indicator health-safe';
            } else if (healthFactor > 1.5) {
                indicator.className = 'health-indicator health-warning';
            } else {
                indicator.className = 'health-indicator health-danger';
            }
        }

        function updateWalletStatus(data) {
            document.getElementById('walletAddress').textContent = 
                data.wallet_address || 'Unknown';
            document.getElementById('ethBalance').textContent = 
                `${(data.eth_balance || 0).toFixed(6)} ETH`;
            document.getElementById('usdcBalance').textContent = 
                `${(data.usdc_balance || 0).toFixed(2)} USDC`;
            document.getElementById('networkName').textContent = 
                data.network_name || 'Unknown';

            // Update Aave data
            document.getElementById('totalCollateral').textContent = 
                `$${(data.total_collateral_usdc || 0).toFixed(2)}`;
            document.getElementById('totalDebt').textContent = 
                `$${(data.total_debt_usdc || 0).toFixed(2)}`;
            document.getElementById('availableBorrows').textContent = 
                `$${(data.available_borrows_usdc || 0).toFixed(2)}`;

            updateHealthIndicator(data.health_factor || 0);

            // Update card colors based on success
            const walletCard = document.getElementById('walletCard');
            const aaveCard = document.getElementById('aaveCard');
            
            if (data.success) {
                walletCard.className = 'status-card';
                aaveCard.className = 'status-card';
            } else {
                walletCard.className = 'status-card error';
                aaveCard.className = 'status-card error';
            }
        }

        function updatePerformance(data) {
            document.getElementById('pnl24h').textContent = 
                `${data.pnl_24h > 0 ? '+' : ''}${(data.pnl_24h || 0).toFixed(2)}%`;
            document.getElementById('operations').textContent = 
                data.total_operations || 0;
            document.getElementById('errorRate').textContent = 
                `${(data.error_rate || 0).toFixed(1)}%`;
        }

        function updateEmergencyStatus(data) {
            const status = data.active ? '🚨 ACTIVE' : '✅ Clear';
            document.getElementById('emergencyStatus').textContent = status;
            
            const card = document.getElementById('emergencyCard');
            card.className = data.active ? 'status-card error' : 'status-card';
        }

        function loadParameters() {
            fetch('/api/parameters')
                .then(r => r.json())
                .then(data => {
                    if (data.success !== false) {
                        document.getElementById('healthFactorTarget').value = data.health_factor_target || 1.19;
                        document.getElementById('borrowTrigger').value = data.borrow_trigger_threshold || 0.02;
                        document.getElementById('arbDecline').value = (data.arb_decline_threshold || 0.05) * 100;
                        document.getElementById('autoMode').checked = data.auto_mode !== false;
                    }
                })
                .catch(e => console.log('Parameters load failed:', e));
        }

        function refreshData() {
            updateTime();

            // Fetch wallet status
            fetch('/api/wallet_status')
                .then(r => r.json())
                .then(data => {
                    updateWalletStatus(data);
                    document.getElementById('agentStatus').textContent = 
                        data.success ? '✅ Connected' : '❌ Error';
                })
                .catch(e => {
                    console.log('Wallet status error:', e);
                    document.getElementById('agentStatus').textContent = '❌ Failed';
                });

            // Fetch performance
            fetch('/api/performance')
                .then(r => r.json())
                .then(updatePerformance)
                .catch(e => console.log('Performance error:', e));

            // Fetch emergency status
            fetch('/api/emergency_status')
                .then(r => r.json())
                .then(updateEmergencyStatus)
                .catch(e => console.log('Emergency status error:', e));
        }

        function emergencyStop() {
            if (confirm('Activate emergency stop? This will halt all agent operations.')) {
                fetch('/api/emergency_stop', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({reason: 'Manual stop via dashboard'})
                })
                .then(r => r.json())
                .then(data => {
                    alert(data.message || 'Emergency stop activated');
                    refreshData();
                })
                .catch(e => alert('Emergency stop failed: ' + e));
            }
        }

        function clearEmergencyStop() {
            if (confirm('Clear emergency stop and resume operations?')) {
                fetch('/api/emergency_stop', {method: 'DELETE'})
                .then(r => r.json())
                .then(data => {
                    alert(data.message || 'Emergency stop cleared');
                    refreshData();
                })
                .catch(e => alert('Clear emergency failed: ' + e));
            }
        }

        function saveParameters() {
            const params = {
                health_factor_target: parseFloat(document.getElementById('healthFactorTarget').value),
                borrow_trigger_threshold: parseFloat(document.getElementById('borrowTrigger').value),
                arb_decline_threshold: parseFloat(document.getElementById('arbDecline').value) / 100,
                auto_mode: document.getElementById('autoMode').checked
            };

            fetch('/api/parameters', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params)
            })
            .then(r => r.json())
            .then(data => {
                alert(data.message || 'Parameters saved successfully');
            })
            .catch(e => alert('Save failed: ' + e));
        }

        function resetParameters() {
            if (confirm('Reset all parameters to defaults?')) {
                document.getElementById('healthFactorTarget').value = 1.19;
                document.getElementById('borrowTrigger').value = 0.02;
                document.getElementById('arbDecline').value = 5;
                document.getElementById('autoMode').checked = true;
                saveParameters();
            }
        }

        // Auto refresh every 30 seconds
        setInterval(refreshData, 30000);

        // Initial load
        refreshData();
        loadParameters();
        setInterval(updateTime, 1000);
    </script>
</body>
</html>
"""

class AgentDashboard:
    """Simple dashboard class based on old dashboard.py"""
    def __init__(self, agent):
        self.agent = agent
        self.adjustable_params = {
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'exploration_rate': 0.1,
            'auto_mode': True
        }
        self.load_user_settings()
        
    def load_user_settings(self):
        """Load user-adjusted parameters"""
        try:
            if os.path.exists('user_settings.json'):
                with open('user_settings.json', 'r') as f:
                    saved_params = json.load(f)
                    self.adjustable_params.update(saved_params)
                    print(f"✅ Loaded user settings: {list(saved_params.keys())}")
        except Exception as e:
            print(f"⚠️ Could not load user settings: {e}")
    
    def save_user_settings(self):
        """Save current parameters"""
        try:
            with open('user_settings.json', 'w') as f:
                json.dump(self.adjustable_params, f, indent=2)
            print(f"✅ Saved user settings")
        except Exception as e:
            print(f"❌ Could not save user settings: {e}")

def initialize_agent():
    """Initialize the agent safely"""
    global agent, dashboard_instance
    try:
        print("🔄 Initializing agent for dashboard...")
        
        # Set environment
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        # Try to import and create agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        # Create dashboard instance
        dashboard_instance = AgentDashboard(agent)
        
        print(f"✅ Agent initialized successfully")
        print(f"   Address: {agent.address}")
        print(f"   Network: Chain {agent.w3.eth.chain_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        agent = None
        dashboard_instance = None
        return False

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/wallet_status')
def wallet_status():
    """Get wallet status"""
    try:
        if not agent:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized',
                'wallet_address': 'Not connected',
                'eth_balance': 0,
                'usdc_balance': 0,
                'health_factor': 0,
                'total_collateral': 0,
                'total_debt': 0,
                'available_borrows': 0,
                'total_collateral_usdc': 0,
                'total_debt_usdc': 0,
                'available_borrows_usdc': 0,
                'network_name': 'Not connected',
                'network_mode': 'mainnet',
                'timestamp': time.time()
            })

        # Get basic wallet data
        eth_balance = agent.get_eth_balance()
        
        # Try to get USDC balance
        usdc_balance = 0
        try:
            if hasattr(agent, 'aave') and agent.aave:
                usdc_balance = agent.aave.get_token_balance(agent.aave.usdc_address)
        except:
            pass

        # Try to get Aave data
        health_factor = 0
        total_collateral = 0
        total_debt = 0
        available_borrows = 0
        total_collateral_usdc = 0
        total_debt_usdc = 0
        available_borrows_usdc = 0

        try:
            if hasattr(agent, 'health_monitor') and agent.health_monitor:
                health_data = agent.health_monitor.get_account_data_with_usdc()
                if health_data:
                    health_factor = health_data.get('health_factor', 0)
                    total_collateral = health_data.get('total_collateral_eth', 0)
                    total_debt = health_data.get('total_debt_eth', 0)
                    available_borrows = health_data.get('available_borrows_eth', 0)
                    total_collateral_usdc = health_data.get('total_collateral_usdc', 0)
                    total_debt_usdc = health_data.get('total_debt_usdc', 0)
                    available_borrows_usdc = health_data.get('available_borrows_usdc', 0)
        except:
            pass

        return jsonify({
            'success': True,
            'wallet_address': agent.address,
            'eth_balance': eth_balance,
            'usdc_balance': usdc_balance,
            'health_factor': health_factor,
            'total_collateral': total_collateral,
            'total_debt': total_debt,
            'available_borrows': available_borrows,
            'total_collateral_usdc': total_collateral_usdc,
            'total_debt_usdc': total_debt_usdc,
            'available_borrows_usdc': available_borrows_usdc,
            'network_name': 'Arbitrum Mainnet',
            'network_mode': 'mainnet',
            'timestamp': time.time()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'wallet_address': 'Error',
            'eth_balance': 0,
            'usdc_balance': 0,
            'health_factor': 0,
            'total_collateral': 0,
            'total_debt': 0,
            'available_borrows': 0,
            'total_collateral_usdc': 0,
            'total_debt_usdc': 0,
            'available_borrows_usdc': 0,
            'network_name': 'Error',
            'network_mode': 'mainnet',
            'timestamp': time.time()
        })

@app.route('/api/performance')
def performance_data():
    """Get performance data"""
    try:
        performance_data = []
        if os.path.exists('performance_log.json'):
            with open('performance_log.json', 'r') as f:
                for line in f:
                    try:
                        performance_data.append(json.loads(line))
                    except:
                        continue

        if len(performance_data) >= 2:
            recent = performance_data[-50:]
            avg_performance = sum(p.get('performance_metric', 0) for p in recent) / len(recent)

            if len(recent) > 1:
                start_perf = recent[0].get('performance_metric', 0)
                end_perf = recent[-1].get('performance_metric', 0)
                pnl_pct = ((end_perf - start_perf) / start_perf) * 100 if start_perf > 0 else 0
            else:
                pnl_pct = 0

            error_count = sum(1 for p in recent if p.get('performance_metric', 0) < 0.5)
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
        return jsonify({
            'pnl_24h': 0,
            'avg_performance': 0,
            'error_rate': 0,
            'total_operations': 0,
            'error': str(e),
            'timestamp': time.time()
        })

@app.route('/api/parameters')
def get_parameters():
    """Get current parameters"""
    try:
        if dashboard_instance:
            params = dashboard_instance.adjustable_params.copy()
            params.update({
                'success': True,
                'timestamp': time.time(),
                'network_mode': 'mainnet'
            })
            return jsonify(params)
        else:
            return jsonify({
                'health_factor_target': 1.19,
                'borrow_trigger_threshold': 0.02,
                'arb_decline_threshold': 0.05,
                'exploration_rate': 0.1,
                'auto_mode': True,
                'success': True,
                'timestamp': time.time(),
                'network_mode': 'mainnet'
            })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False,
            'timestamp': time.time()
        })

@app.route('/api/parameters', methods=['POST'])
def save_parameters():
    """Save parameters"""
    try:
        data = request.get_json()
        
        if dashboard_instance:
            dashboard_instance.adjustable_params.update(data)
            dashboard_instance.save_user_settings()
        
        # Also save to user_settings.json directly
        settings_file = 'user_settings.json'
        existing_settings = {}
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                existing_settings = json.load(f)
        
        existing_settings.update(data)
        existing_settings['last_updated'] = time.time()
        
        with open(settings_file, 'w') as f:
            json.dump(existing_settings, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Parameters saved successfully',
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        })

@app.route('/api/emergency_status')
def emergency_status():
    """Get emergency status"""
    try:
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        is_active = os.path.exists(emergency_file)
        
        return jsonify({
            'active': is_active,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'active': False,
            'error': str(e),
            'timestamp': time.time()
        })

@app.route('/api/emergency_stop', methods=['POST'])
def activate_emergency_stop():
    """Activate emergency stop"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Emergency stop via dashboard')
        
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        with open(emergency_file, 'w') as f:
            f.write(f"EMERGENCY STOP ACTIVE\n")
            f.write(f"Reason: {reason}\n")
            f.write(f"Timestamp: {time.time()}\n")
            f.write(f"DateTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop activated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/emergency_stop', methods=['DELETE'])
def clear_emergency_stop():
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
        })

def start_dashboard():
    """Start the dashboard"""
    print("🚀 Starting Working Dashboard...")
    
    # Initialize agent in background
    initialization_thread = threading.Thread(target=initialize_agent, daemon=True)
    initialization_thread.start()
    
    print("🌐 Dashboard starting on port 5000")
    print("🔗 Access via your Replit webview URL")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    start_dashboard()
