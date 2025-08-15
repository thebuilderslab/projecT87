
#!/usr/bin/env python3
"""
EMERGENCY FUNDING MANAGER
Handles low ETH balance and gas fee optimization
"""

import os
from web3 import Web3
from enhanced_rpc_manager import EnhancedRPCManager

class EmergencyFundingManager:
    def __init__(self):
        self.rpc_manager = EnhancedRPCManager()
        self.min_eth_required = 0.005  # Minimum ETH for operations
        
    def check_and_optimize_gas(self, wallet_address):
        """Check ETH balance and optimize gas usage"""
        if not self.rpc_manager.find_working_rpc():
            return False
        
        w3 = self.rpc_manager.w3
        eth_balance = w3.eth.get_balance(wallet_address) / 10**18
        
        print(f"⚡ Current ETH Balance: {eth_balance:.6f} ETH")
        print(f"💡 Minimum Required: {self.min_eth_required:.6f} ETH")
        
        if eth_balance < self.min_eth_required:
            print("❌ Insufficient ETH for gas fees")
            self.provide_funding_guidance(wallet_address, eth_balance)
            return False
        else:
            print("✅ Sufficient ETH for gas fees")
            return True
    
    def provide_funding_guidance(self, wallet_address, current_balance):
        """Provide specific funding guidance"""
        needed_eth = self.min_eth_required - current_balance
        
        print(f"\n💰 FUNDING GUIDANCE")
        print(f"=" * 40)
        print(f"📍 Wallet: {wallet_address}")
        print(f"🏦 Current: {current_balance:.6f} ETH")
        print(f"💎 Needed: {needed_eth:.6f} ETH")
        print(f"💵 USD Cost: ~${needed_eth * 2500:.2f}")
        
        print(f"\n🚀 FUNDING OPTIONS:")
        print(f"1. 🏦 CEX Transfer: Send from Coinbase/Binance")
        print(f"2. 🌉 Bridge: Use Arbitrum bridge from mainnet")
        print(f"3. 💳 Buy directly: Use on-ramp services")
        
        print(f"\n⚡ OPTIMIZED GAS SETTINGS:")
        print(f"• Use 0.01 Gwei gas price (Arbitrum is cheap)")
        print(f"• Batch transactions when possible")
        print(f"• Monitor gas prices before executing")
    
    def calculate_optimized_gas(self, operation_type="swap"):
        """Calculate optimized gas settings"""
        if not self.rpc_manager.w3:
            return None
        
        try:
            # Get current gas price
            current_gas_price = self.rpc_manager.w3.eth.gas_price
            
            # Arbitrum typically has very low gas prices
            optimized_gas_price = min(current_gas_price, self.rpc_manager.w3.to_wei(0.1, 'gwei'))
            
            # Gas limits for different operations
            gas_limits = {
                'approve': 60000,
                'swap': 300000,
                'supply': 200000,
                'borrow': 250000
            }
            
            gas_limit = gas_limits.get(operation_type, 200000)
            
            estimated_cost_eth = (optimized_gas_price * gas_limit) / 10**18
            estimated_cost_usd = estimated_cost_eth * 2500
            
            return {
                'gas_price': optimized_gas_price,
                'gas_limit': gas_limit,
                'estimated_cost_eth': estimated_cost_eth,
                'estimated_cost_usd': estimated_cost_usd
            }
            
        except Exception as e:
            print(f"❌ Gas calculation error: {e}")
            return None

if __name__ == "__main__":
    # Test the funding manager
    manager = EmergencyFundingManager()
    
    # Example wallet address (replace with actual)
    test_wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    
    result = manager.check_and_optimize_gas(test_wallet)
    print(f"\nFunding check result: {'✅ READY' if result else '❌ NEEDS FUNDING'}")

# --- Emergency stop functionality integrated ---
import time
import json

EMERGENCY_STOP_FILE = "EMERGENCY_STOP_ACTIVE.flag"
EMERGENCY_LOG_FILE = "emergency_stop_log.json"

def log_emergency_action(action, reason="Manual trigger"):
    """Log emergency stop actions with timestamp"""
    log_entry = {
        'timestamp': time.time(),
        'action': action,
        'reason': reason,
        'datetime': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }
    
    # Append to log file
    if os.path.exists(EMERGENCY_LOG_FILE):
        with open(EMERGENCY_LOG_FILE, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(EMERGENCY_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def emergency_stop(reason="Manual trigger via emergency_stop.py"):
    """Trigger immediate emergency stop with comprehensive logging"""
    
    emergency_details = {
        'reason': reason,
        'timestamp': time.time(),
        'datetime': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'triggered_by': 'manual',
        'system_state': capture_system_state()
    }
    
    with open(EMERGENCY_STOP_FILE, 'w') as f:
        f.write(f"EMERGENCY STOP ACTIVE\n")
        f.write(f"Reason: {reason}\n")
        f.write(f"Timestamp: {time.time()}\n")
        f.write(f"DateTime: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
        f.write(f"System State: {json.dumps(emergency_details['system_state'], indent=2)}\n")
    
    log_emergency_action("EMERGENCY_STOP_ACTIVATED", reason)
    
    # Save detailed emergency report
    with open(f"emergency_report_{int(time.time())}.json", 'w') as f:
        json.dump(emergency_details, f, indent=2)
    
    print("🚨 EMERGENCY STOP ACTIVATED!")
    print("🛑 All agent operations will halt immediately")
    print(f"📁 Emergency stop file created: {EMERGENCY_STOP_FILE}")
    print(f"📋 Reason: {reason}")
    print(f"📊 System state captured in emergency report")
    print("\n🔧 To resume operations:")
    print("1. Investigate the issue thoroughly")
    print("2. Review emergency report")
    print("3. Run: python emergency_stop.py clear")
    print("4. Restart the agent")

def capture_system_state():
    """Capture current system state for emergency analysis"""
    try:
        return {
            'timestamp': time.time(),
            'active_processes': True,  # Could implement process checking
            'recent_performance': get_recent_performance_summary(),
            'wallet_status': 'unknown',  # Could implement wallet checking
            'api_status': 'unknown'      # Could implement API checking
        }
    except Exception as e:
        return {'error': str(e)}

def get_recent_performance_summary():
    """Get summary of recent performance for emergency analysis"""
    try:
        if os.path.exists('performance_log.json'):
            recent_data = []
            with open('performance_log.json', 'r') as f:
                for line in f.readlines()[-10:]:  # Last 10 entries
                    try:
                        recent_data.append(json.loads(line))
                    except:
                        continue
            
            if recent_data:
                avg_performance = sum(p['performance_metric'] for p in recent_data) / len(recent_data)
                return {
                    'avg_recent_performance': avg_performance,
                    'recent_entries': len(recent_data),
                    'last_timestamp': recent_data[-1].get('timestamp', 0)
                }
        
        return {'status': 'no_recent_data'}
    except Exception as e:
        return {'error': str(e)}

def clear_emergency_stop():
    """Clear emergency stop"""
    
    if os.path.exists(EMERGENCY_STOP_FILE):
        os.remove(EMERGENCY_STOP_FILE)
        log_emergency_action("EMERGENCY_STOP_CLEARED", "Manual clear")
        print("✅ Emergency stop cleared")
        print("🔄 You can now restart the agent")
    else:
        print("ℹ️ No emergency stop file found")

def check_emergency_status():
    """Check if emergency stop is currently active"""
    if os.path.exists(EMERGENCY_STOP_FILE):
        print("🚨 EMERGENCY STOP IS ACTIVE")
        with open(EMERGENCY_STOP_FILE, 'r') as f:
            content = f.read()
            print(content)
        return True
    else:
        print("✅ No emergency stop active")
        return False

def get_emergency_logs():
    """Get recent emergency stop logs"""
    if os.path.exists(EMERGENCY_LOG_FILE):
        with open(EMERGENCY_LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        print("📋 Recent Emergency Stop Actions:")
        for log in logs[-5:]:  # Show last 5 actions
            print(f"  {log['datetime']}: {log['action']} - {log['reason']}")
    else:
        print("ℹ️ No emergency stop logs found")
# --- Merged from emergency_launch.py ---

def dashboard():
    return render_template_string(TEMPLATE)

def status():
    return {
        'status': 'emergency_mode',
        'network': 'arbitrum_mainnet',
        'dashboard': 'online'
    }