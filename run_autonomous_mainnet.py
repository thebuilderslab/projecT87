
#!/usr/bin/env python3
"""
Autonomous Mainnet Agent Launcher
Runs the ArbitrumTestnetAgent in continuous autonomous mode on Arbitrum Mainnet
"""

import os
import sys
import time
import json
from datetime import datetime
import pytz
from arbitrum_testnet_agent import ArbitrumTestnetAgent

# Force mainnet mode
os.environ['NETWORK_MODE'] = 'mainnet'

def log_agent_activity(message, level="INFO"):
    """Log agent activity with timestamp"""
    eastern = pytz.timezone('US/Eastern')
    timestamp = datetime.now(eastern).strftime("%H:%M:%S EST")
    print(f"[{timestamp}] {level}: {message}")

def check_emergency_stop():
    """Check for emergency stop flag"""
    return os.path.exists("EMERGENCY_STOP_ACTIVE.flag")

def run_autonomous_mainnet_agent():
    """Run the autonomous agent on Arbitrum Mainnet"""
    print("🚀 ARBITRUM MAINNET AUTONOMOUS AGENT")
    print("=" * 60)
    print("🌐 Network: Arbitrum Mainnet (Chain ID: 42161)")
    print("🤖 Mode: Continuous Autonomous Operation")
    print("🛑 Emergency Stop: Create 'EMERGENCY_STOP_ACTIVE.flag' to halt")
    print("=" * 60)
    
    try:
        # Initialize the agent for mainnet
        log_agent_activity("Initializing Arbitrum Mainnet Agent...")
        
        # Import the correct agent class
        try:
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            
            # Ensure it's connected to mainnet
            if not agent or not hasattr(agent, 'w3'):
                raise Exception("Agent initialization failed - no web3 connection")
                
        except Exception as init_error:
            log_agent_activity(f"❌ Agent initialization failed: {init_error}")
            raise Exception(f"Failed to initialize agent: {init_error}")
        
        # Verify mainnet connection
        actual_chain_id = agent.w3.eth.chain_id
        if actual_chain_id != 42161:
            raise Exception(f"❌ Expected Chain ID 42161 (Arbitrum Mainnet), got {actual_chain_id}")
        
        log_agent_activity(f"✅ Connected to Arbitrum Mainnet (Chain ID: {actual_chain_id})")
        log_agent_activity(f"📍 Wallet Address: {agent.address}")
        
        # Initialize DeFi integrations
        log_agent_activity("🔄 Initializing DeFi integrations...")
        if not agent.initialize_integrations():
            raise Exception("❌ Failed to initialize DeFi integrations")
        log_agent_activity("✅ DeFi integrations initialized successfully")
        
        # Initial status check
        log_agent_activity("📊 Performing initial status check...")
        eth_balance = agent.get_eth_balance()
        log_agent_activity(f"💰 ETH Balance: {eth_balance:.6f} ETH")
        
        # Check initial health factor
        try:
            health_data = agent.health_monitor.get_current_health_factor()
            if health_data:
                hf = health_data.get('health_factor', 0)
                log_agent_activity(f"❤️ Initial Health Factor: {hf:.4f}")
            else:
                log_agent_activity("⚠️ Could not retrieve initial health factor")
        except Exception as e:
            log_agent_activity(f"⚠️ Health factor check error: {e}")
        
        # Start autonomous loop
        log_agent_activity("🎯 Starting autonomous monitoring loop...")
        print("\n" + "="*60)
        print("🔍 MONITORING AAVE POSITIONS FOR TRIGGERS")
        print("💡 Add funds to your Aave supply to test trigger activation")
        print("🔔 Watch for 'TRIGGER ACTIVATED' messages below")
        print("="*60 + "\n")
        
        run_id = 1
        iteration = 0
        
        while True:
            # Emergency stop check
            if check_emergency_stop():
                log_agent_activity("🛑 Emergency stop detected! Halting operations...", "EMERGENCY")
                break
            
            try:
                # Log monitoring cycle
                log_agent_activity(f"🔄 Monitoring cycle {run_id}-{iteration}")
                
                # Run the autonomous task
                performance = agent.run_real_defi_task(run_id, iteration, {
                    'health_factor_target': 1.25,  # Conservative for mainnet
                    'max_iterations_per_run': 100
                })
                
                # Log performance
                if performance > 0.9:
                    log_agent_activity(f"✅ High performance cycle: {performance:.3f}", "SUCCESS")
                elif performance > 0.5:
                    log_agent_activity(f"✔️ Moderate performance cycle: {performance:.3f}", "INFO")
                else:
                    log_agent_activity(f"⚠️ Low performance cycle: {performance:.3f}", "WARNING")
                
                iteration += 1
                
                # Reset run ID every 50 iterations
                if iteration >= 50:
                    run_id += 1
                    iteration = 0
                    log_agent_activity(f"🔄 Starting new run cycle #{run_id}")
                
            except Exception as e:
                log_agent_activity(f"❌ Error in monitoring cycle: {e}", "ERROR")
                log_agent_activity("⏸️ Continuing monitoring after error...")
            
            # Wait before next cycle (shorter for mainnet responsiveness)
            time.sleep(30)  # 30 seconds between checks
            
    except KeyboardInterrupt:
        log_agent_activity("👋 Autonomous agent stopped by user (Ctrl+C)", "INFO")
    except Exception as e:
        log_agent_activity(f"💥 Critical error: {e}", "CRITICAL")
        log_agent_activity("🛑 Agent halted due to critical error", "CRITICAL")

if __name__ == "__main__":
    # Ensure mainnet mode
    os.environ['NETWORK_MODE'] = 'mainnet'
    
    # Check for required secrets
    required_secrets = ['PRIVATE_KEY', 'COINMARKETCAP_API_KEY']
    missing_secrets = [secret for secret in required_secrets if not os.getenv(secret)]
    
    if missing_secrets:
        print(f"❌ Missing required secrets: {missing_secrets}")
        print("💡 Please add these to your Replit Secrets")
        sys.exit(1)
    
    run_autonomous_mainnet_agent()
