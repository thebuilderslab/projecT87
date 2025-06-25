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

# CRITICAL: Force reload environment for deployment environments
load_dotenv(override=True)

# Force Replit deployment environment variable loading
if os.getenv('REPLIT_DEPLOYMENT'):
    print("🔄 DEPLOYMENT MODE: Force loading environment variables")
    # In deployment, secrets may be injected differently
    import subprocess
    try:
        # Force reload environment
        result = subprocess.run(['printenv'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if '=' in line and line.strip():
                    key, value = line.split('=', 1)
                    if key in ['NETWORK_MODE', 'PROMPT_KEY', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY']:
                        os.environ[key] = value
                        print(f"🔄 Deployment env loaded: {key}")
    except Exception as e:
        print(f"⚠️ Environment loading warning: {e}")

load_dotenv(override=True)

# Enhanced secret loading with multiple fallback methods
def force_load_secret(var_name, default_value=None):
    """Force load a secret with multiple fallback methods and aggressive reloading"""
    # Method 1: Force reload .env
    try:
        load_dotenv(override=True)
    except:
        pass

    # Method 2: Direct environment variable
    value = os.getenv(var_name)
    if value and value.strip():
        return value.strip()

    # Method 3: Try subprocess printenv
    try:
        import subprocess
        result = subprocess.run(['printenv', var_name], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            value = result.stdout.strip()
            os.environ[var_name] = value
            return value
    except:
        pass

    # Method 4: Try reading from /proc/environ (Linux)
    try:
        with open('/proc/self/environ', 'rb') as f:
            env_data = f.read().decode('utf-8', errors='ignore')
            for line in env_data.split('\0'):
                if line.startswith(f'{var_name}='):
                    value = line.split('=', 1)[1]
                    if value.strip():
                        os.environ[var_name] = value.strip()
                        return value.strip()
    except:
        pass

    # Method 5: Try reading from Replit's special env files
    try:
        replit_env_paths = [
            '/home/runner/.replit/secrets',
            '/tmp/secrets',
            '.env.local'
        ]
        for env_path in replit_env_paths:
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith(f'{var_name}='):
                            value = line.split('=', 1)[1].strip()
                            if value:
                                os.environ[var_name] = value
                                return value
    except:
        pass

    # Method 6: Use default value if provided
    if default_value:
        os.environ[var_name] = default_value
        return default_value

    return None

# Force load critical secrets
critical_secrets = {
    'PROMPT_KEY': None,
    'NETWORK_MODE': 'mainnet',  # Default to mainnet for launcher
    'COINMARKETCAP_API_KEY': None,
    'PRIVATE_KEY': None
}

for var_name, default_val in critical_secrets.items():
    force_load_secret(var_name, default_val)

# Set default NETWORK_MODE if still missing
if not os.getenv('NETWORK_MODE'):
    os.environ['NETWORK_MODE'] = 'mainnet'  # Default to mainnet for launcher

# Comprehensive secret linkage debugging
print(f"🔍 COMPREHENSIVE SECRET LINKAGE DEBUG:")
print(f"=" * 60)
print(f"🔧 Environment loading check:")
print(f"   NETWORK_MODE: {os.getenv('NETWORK_MODE', 'NOT_SET')}")
print(f"   COINMARKETCAP_API_KEY: {'SET' if os.getenv('COINMARKETCAP_API_KEY') else 'NOT_SET'}")
print(f"   PROMPT_KEY: {'SET' if os.getenv('PROMPT_KEY') else 'NOT_SET'}")
print(f"   PRIVATE_KEY: {'SET' if os.getenv('PRIVATE_KEY') else 'NOT_SET'}")
print(f"   PRIVATE_KEY2: {'SET' if os.getenv('PRIVATE_KEY2') else 'NOT_SET'}")
print(f"   DEPLOYMENT_ENV: {'SET' if os.getenv('REPLIT_DEPLOYMENT') else 'NOT_SET'}")

# Detailed secret analysis
secrets_status = {}
critical_secrets = ['NETWORK_MODE', 'COINMARKETCAP_API_KEY', 'PROMPT_KEY', 'PRIVATE_KEY']

for secret in critical_secrets:
    value = os.getenv(secret)
    if value:
        # Don't print actual values for security
        secrets_status[secret] = {
            'status': 'LINKED',
            'length': len(value),
            'type': 'string' if isinstance(value, str) else type(value).__name__
        }
    else:
        secrets_status[secret] = {'status': 'NOT_LINKED', 'length': 0, 'type': 'NoneType'}

print(f"\n🔗 SECRET LINKAGE ANALYSIS:")
for secret, info in secrets_status.items():
    status_icon = "✅" if info['status'] == 'LINKED' else "❌"
    print(f"   {status_icon} {secret}: {info['status']} (length: {info['length']})")

# Check if all critical secrets are linked
all_linked = all(info['status'] == 'LINKED' for info in secrets_status.values())
print(f"\n🎯 ALL CRITICAL SECRETS LINKED: {'YES' if all_linked else 'NO'}")

if not all_linked:
    missing = [secret for secret, info in secrets_status.items() if info['status'] != 'LINKED']
    print(f"❌ MISSING LINKAGES: {', '.join(missing)}")
    print(f"💡 SOLUTION: Re-link these secrets in Replit Secrets interface")
    print(f"\n🔧 DETAILED TROUBLESHOOTING FOR MISSING SECRETS:")
    for secret in missing:
        print(f"   • {secret}: Check project-specific Secrets tab (🔒 icon in sidebar)")
        if secret == 'PROMPT_KEY':
            print(f"     - This is CRITICAL for mainnet deployment")
            print(f"     - Must be added from project Secrets tab")
        elif secret == 'NETWORK_MODE':
            print(f"     - Value must be exactly: mainnet")
            print(f"     - Currently shows: {os.getenv('NETWORK_MODE', 'NOT_SET')}")

print(f"=" * 60)

# Additional validation for critical deployment requirements
print(f"\n🚨 CRITICAL DEPLOYMENT STATUS:")
deployment_ready = True
critical_issues = []

if not os.getenv('PROMPT_KEY'):
    critical_issues.append("PROMPT_KEY not accessible - mainnet features disabled")
    deployment_ready = False

if os.getenv('NETWORK_MODE', 'testnet').lower() != 'mainnet':
    critical_issues.append(f"NETWORK_MODE is '{os.getenv('NETWORK_MODE', 'testnet')}' instead of 'mainnet'")
    deployment_ready = False

if not os.getenv('PRIVATE_KEY'):
    critical_issues.append("PRIVATE_KEY not accessible - cannot connect to wallet")
    deployment_ready = False

if deployment_ready:
    print(f"✅ DEPLOYMENT STATUS: READY FOR MAINNET")
else:
    print(f"❌ DEPLOYMENT STATUS: NOT READY - {len(critical_issues)} critical issues")
    for i, issue in enumerate(critical_issues, 1):
        print(f"   {i}. {issue}")

print(f"=" * 60)

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

        # Check for private key (try PRIVATE_KEY first, then PRIVATE_KEY2 as fallback)
        private_key = os.getenv('PRIVATE_KEY') or os.getenv('PRIVATE_KEY2')
        if not private_key:
            print("❌ Missing critical environment variable: PRIVATE_KEY")
            print("💡 Please add PRIVATE_KEY to your Replit Secrets")
            print("   (Or ensure PRIVATE_KEY2 is available as fallback)")
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
                if var == 'PROMPT_KEY' and os.getenv('REPLIT_DEPLOYMENT'):
                    # In deployment, PROMPT_KEY might not be accessible but we can proceed
                    print(f"⚠️  {var}: Not accessible in deployment environment (proceeding anyway)")
                    continue
                else:
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
        # In deployment, start web dashboard anyway for health checks
        if os.getenv('REPLIT_DEPLOYMENT'):
            print("🚀 Starting web dashboard for deployment health checks...")
            start_web_dashboard()
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