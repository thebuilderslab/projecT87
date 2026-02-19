
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
from config_constants import get_target_wallet, get_delegation_mode

try:
    from real_estate_tasks import check_and_run_scheduled_tasks
    RE_TASKS_AVAILABLE = True
except ImportError:
    RE_TASKS_AVAILABLE = False

try:
    from auto_supply import run_auto_supply_cycle
    AUTO_SUPPLY_AVAILABLE = True
except ImportError:
    AUTO_SUPPLY_AVAILABLE = False

try:
    import db as database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


def run_strategies_for_user(user_id, wallet_address, agent, run_id, iteration, config):
    if DB_AVAILABLE and not database.is_bot_enabled(user_id):
        log_agent_activity(f"⏸️ Bot disabled for user {user_id} ({wallet_address[:10]}...) — skipping strategies")
        return None
    performance = agent.run_real_defi_task(run_id, iteration, config)
    return performance

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
    target_wallet = get_target_wallet()
    delegation_label = get_delegation_mode()
    
    print("🚀 ARBITRUM MAINNET AUTONOMOUS AGENT")
    print("=" * 60)
    print("🌐 Network: Arbitrum Mainnet (Chain ID: 42161)")
    print(f"🔑 Operation Mode: {delegation_label}")
    if target_wallet:
        print(f"👤 Target Wallet: {target_wallet}")
        print("📋 Delegation Required: User must approveBorrowAllowance for DAI + WETH")
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
        
        state_file = "execution_state.json"
        if os.path.exists(state_file):
            os.remove(state_file)
            log_agent_activity(f"🗑️ {state_file} deleted — forcing clean start")
        else:
            log_agent_activity(f"✅ {state_file} not found — already clean")
        
        # Initial status check
        log_agent_activity("📊 Performing initial status check...")
        eth_balance = agent.get_eth_balance()
        log_agent_activity(f"💰 ETH Balance: {eth_balance:.6f} ETH")
        
        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(agent.health_monitor.get_current_health_factor)
                health_data = future.result(timeout=15)
                if health_data:
                    hf = health_data.get('health_factor', 0)
                    log_agent_activity(f"❤️ Initial Health Factor: {hf:.4f}")
                else:
                    log_agent_activity("⚠️ Could not retrieve initial health factor")
        except concurrent.futures.TimeoutError:
            log_agent_activity("⚠️ Health factor check timed out (15s) — skipping")
        except Exception as e:
            log_agent_activity(f"⚠️ Health factor check error: {e}")
        
        log_agent_activity("✅ Clean start confirmed — no pending execution state")

        print("\n" + "="*60)
        print("📋 PRE-FLIGHT AUDIT — USDC PAY YOURSELF FIRST MODE")
        print("="*60)
        print(f"   Operation Mode: {delegation_label}")
        if target_wallet:
            print(f"   Target Wallet: {target_wallet}")
        print(f"   HF Thresholds: Growth 3.10 / Macro 3.05 / Micro 3.00 / Capacity 2.90")
        print(f"   Slippage Tolerance: 1%")
        print(f"   State File: CLEARED (clean run)")
        print(f"   Growth Path: $11.40 DAI borrow ($2.80 WBTC / $2.45 WETH / $2.75 USDT / $1.10 gas / $1.10 WalletS / $1.20 Tax)")
        print(f"   Capacity Path: $6.70 DAI borrow ($1.10 each: WBTC/WETH/USDT/gas/WalletS + $1.20 Tax)")
        print(f"   Liability Short: Phase 2 Target Profit Engine (Round Trip)")
        print(f"   Macro Short: $10.90 WETH → 40% WBTC / 35% USDT / 25% WETH collateral")
        print(f"   Micro Short: $7.20 WETH → 40% WBTC / 35% USDT / 25% WETH collateral")
        print(f"   Short Flow: Borrow WETH → Split 40/35/25 → Supply → Hunt → Close → 20/20/60")
        print(f"   Velocity Monitor: 40min buffer | Micro: $30 drop in 20min (4h CD) | Macro: $50 drop in 30min (12h CD)")
        print(f"   USDC Tax: $1.20 per Growth/Capacity borrow → DAI→USDC → WALLET_B")
        print(f"   Nurse Mode: $2.00 hard floor, USDC whitelisted (profit)")
        print(f"   Force-Approve: All tokens on startup (Aave + Uniswap)")
        print(f"   Dust Guard: Active ($1.00 minimum swap)")
        print(f"   Per-Step Approvals: Active ($15 DAI threshold)")
        print(f"   Proportional Recovery: Enabled")
        print(f"   Max Recovery Attempts: 5")
        print(f"   🎯 Polling: Dynamic (90s Sentry / 15s Hunter Mode)")
        print("="*60 + "\n")

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
                agent._perform_safety_sweep()

                log_agent_activity(f"🔄 Monitoring cycle {run_id}-{iteration}")
                
                bot_wallet = agent.address
                bot_user_id = None
                if DB_AVAILABLE:
                    bot_user = database.get_user_by_wallet(bot_wallet)
                    if bot_user:
                        bot_user_id = bot_user['id']

                config = {
                    'health_factor_target': 3.10,
                    'max_iterations_per_run': 100
                }

                if bot_user_id is not None:
                    performance = run_strategies_for_user(bot_user_id, bot_wallet, agent, run_id, iteration, config)
                else:
                    performance = agent.run_real_defi_task(run_id, iteration, config)

                if performance is None:
                    performance = 0.0
                
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

                try:
                    agent._process_injection_trigger()
                except Exception as inj_err:
                    log_agent_activity(f"⚠️ Injection trigger error: {inj_err}", "WARNING")

                try:
                    agent._check_profit_bucket()
                except Exception as bucket_err:
                    log_agent_activity(f"⚠️ Profit bucket check error: {bucket_err}", "WARNING")

                if RE_TASKS_AVAILABLE:
                    try:
                        re_result = check_and_run_scheduled_tasks()
                        if re_result:
                            log_agent_activity(f"🏠 RE Task: {re_result.get('task', 'unknown')} → {re_result.get('status', 'unknown')}: {re_result.get('message', '')}")
                    except Exception as re_err:
                        log_agent_activity(f"⚠️ Real estate task error: {re_err}", "WARNING")

                if AUTO_SUPPLY_AVAILABLE:
                    try:
                        supply_count = run_auto_supply_cycle()
                        if supply_count > 0:
                            log_agent_activity(f"💰 Auto-supply: {supply_count} wallet(s) supplied WBTC to Aave")
                    except Exception as supply_err:
                        log_agent_activity(f"⚠️ Auto-supply cycle error: {supply_err}", "WARNING")

            except Exception as e:
                log_agent_activity(f"❌ Error in monitoring cycle: {e}", "ERROR")
                log_agent_activity("⏸️ Continuing monitoring after error...")
            
            poll_interval = 45
            try:
                if hasattr(agent, 'liability_short_strategy') and agent.liability_short_strategy:
                    poll_interval = agent.liability_short_strategy.get_polling_interval()
            except Exception:
                pass
            time.sleep(poll_interval)
            
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
