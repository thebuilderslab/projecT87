#!/usr/bin/env python3
"""
MAINNET LAUNCHER
Safe deployment launcher for Arbitrum Mainnet operations
"""

import os
import sys
import time
import json
from dotenv import load_dotenv
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web_dashboard import app
import threading
import signal
from emergency_stop import check_emergency_status

# Load environment variables
load_dotenv()

class MainnetSafetyManager:
    """Manages safety features for mainnet deployment"""

    def __init__(self):
        self.emergency_stop = False
        self.emergency_stop_file = 'EMERGENCY_STOP_ACTIVE.flag'
        self.monitoring_active = True

    def check_emergency_stop(self):
        """Check if emergency stop has been triggered"""
        return os.path.exists(self.emergency_stop_file) or self.emergency_stop

    def trigger_emergency_stop(self, reason="Manual trigger"):
        """Trigger emergency stop"""
        self.emergency_stop = True
        with open(self.emergency_stop_file, 'w') as f:
            f.write(f"EMERGENCY STOP TRIGGERED\nReason: {reason}\nTimestamp: {time.time()}\n")
        print(f"🚨 EMERGENCY STOP ACTIVATED: {reason}")

    def clear_emergency_stop(self):
        """Clear emergency stop (manual intervention required)"""
        self.emergency_stop = False
        if os.path.exists(self.emergency_stop_file):
            os.remove(self.emergency_stop_file)
        print("✅ Emergency stop cleared")

    def validate_mainnet_readiness(self):
        """Validate system is ready for mainnet deployment"""
        print("🔍 MAINNET READINESS VALIDATION")
        print("=" * 50)

        # Check critical environment variables
        critical_vars = ['COINMARKETCAP_API_KEY', 'PROMPT_KEY']
        
        # Check for private key (PRIVATE_KEY for mainnet)
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print("❌ Missing critical environment variable: PRIVATE_KEY")
            print("💡 Please add PRIVATE_KEY to your Replit Secrets")
            return False
        
        # Validate private key format
        if len(private_key) not in [64, 66]:
            print(f"❌ Invalid private key format (should be 64 or 66 characters)")
            return False
        print("✅ Private key: Configured properly")
        optional_vars = ['MAINET_ACCOUNT_KEY', 'OPTIMIZER_API_KEY']
        
        # Validate critical secrets
        for var in critical_vars:
            value = os.getenv(var)
            if not value:
                print(f"❌ Missing critical environment variable: {var}")
                print(f"💡 Please add {var} to your Replit Secrets")
                return False
                
            if len(value.strip()) == 0:
                print(f"❌ {var} is empty - please set a valid value")
                return False
                
            print(f"✅ {var}: Configured properly")
        
        # Check optional secrets with warnings
        for var in optional_vars:
            value = os.getenv(var)
            if not value or len(value.strip()) == 0:
                print(f"⚠️  {var}: Missing or placeholder (some features may be limited)")
            else:
                print(f"✅ {var}: Configured properly")

        # Check network mode
        network_mode = os.getenv('NETWORK_MODE', 'testnet')
        if network_mode != 'mainnet':
            print(f"❌ CRITICAL: Network mode is '{network_mode}' but mainnet required!")
            print("🔧 Please set NETWORK_MODE=mainnet in Replit Secrets")
            return False
        print(f"✅ Network mode: mainnet")

        # Validate Arbitrum Mainnet RPC
        arbitrum_rpc = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        if 'sepolia' in arbitrum_rpc.lower() or 'testnet' in arbitrum_rpc.lower():
            print(f"❌ RPC URL appears to be testnet: {arbitrum_rpc}")
            print("    Please update ARBITRUM_RPC_URL to mainnet endpoint")
            return False
        print(f"✅ Arbitrum RPC: {arbitrum_rpc}")

        # Check emergency stop system
        if not os.path.exists('emergency_stop.py'):
            print("❌ Emergency stop system not found")
            return False
        print("✅ Emergency stop system: Ready")

        # Validate wallet has funds (conceptual check)
        print("⚠️ IMPORTANT: Ensure your mainnet wallet has:")
        print("   • Minimum 0.1 ETH for gas fees")
        print("   • Sufficient USDC/WETH for Aave operations")
        print("   • Wallet address should match your PRIVATE_KEY")

        return True

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutdown signal received...")
    print("🔄 Checking for emergency stop...")

    # Activate emergency stop on Ctrl+C
    safety_manager = MainnetSafetyManager()
    safety_manager.trigger_emergency_stop("Keyboard interrupt (Ctrl+C)")

    print("👋 Mainnet launcher stopped safely")
    sys.exit(0)

def start_web_dashboard():
    """Start the web dashboard in a separate thread"""
    print("🌐 Starting web dashboard...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def main():
    """Main launcher function"""
    print("🚀 ARBITRUM MAINNET LAUNCHER")
    print("=" * 50)

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize safety manager
    safety_manager = MainnetSafetyManager()

    # Check for existing emergency stop
    if safety_manager.check_emergency_stop():
        print("🚨 EMERGENCY STOP IS ACTIVE!")
        print("Run 'python emergency_stop.py clear' to resume")
        return

    # Validate mainnet readiness
    if not safety_manager.validate_mainnet_readiness():
        print("\n❌ MAINNET VALIDATION FAILED!")
        print("Please fix the issues above before deploying to mainnet")
        return

    print("\n✅ MAINNET VALIDATION PASSED!")
    print("🔄 Starting mainnet operations...")

    # Start web dashboard in background
    dashboard_thread = threading.Thread(target=start_web_dashboard, daemon=True)
    dashboard_thread.start()

    # Initialize mainnet agent
    try:
        print("🤖 Initializing Arbitrum Mainnet Agent...")
        agent = ArbitrumTestnetAgent()  # This will use mainnet settings based on NETWORK_MODE
        print(f"✅ Agent initialized for mainnet")
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: Arbitrum Mainnet")

        # Start the main agent loop with emergency stop checks
        run_id = 1
        while True:
            # Check emergency stop at the beginning of each loop
            if safety_manager.check_emergency_stop():
                print("🚨 Emergency stop detected! Halting operations...")
                break

            print(f"\n🔄 Starting mainnet run #{run_id}")

            try:
                # Run agent operations
                performance = agent.run_real_defi_task(run_id, 0, {
                    'health_factor_target': 1.25,  # More conservative for mainnet
                    'max_iterations_per_run': 50
                })

                print(f"📊 Run #{run_id} performance: {performance:.4f}")

            except Exception as e:
                print(f"❌ Error in run #{run_id}: {e}")
                # Trigger emergency stop on critical errors
                safety_manager.trigger_emergency_stop(f"Critical error: {str(e)}")
                break

            run_id += 1
            time.sleep(60)  # Wait 1 minute between runs for mainnet

    except Exception as e:
        print(f"❌ Failed to initialize mainnet agent: {e}")
        safety_manager.trigger_emergency_stop(f"Initialization error: {str(e)}")
        return

    print("👋 Mainnet launcher stopped")

if __name__ == "__main__":
    main()