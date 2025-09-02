from arbitrum_testnet_agent import ArbitrumTestnetAgent # Assuming this is where your agent class is
from collaborative_strategy_manager import CollaborativeStrategyManager
import time
import json
import os
import traceback
from datetime import datetime
from config import MIN_ETH_FOR_OPERATIONS, MIN_ETH_FOR_GAS_BUFFER

# --- Configuration ---
CONFIG_FILE = 'agent_config.json'
PERFORMANCE_LOG = 'performance_log.json'
IMPROVEMENT_LOG = 'improvement_log.json'

# Default configuration
DEFAULT_CONFIG = {
    'learning_rate': 0.01,
    'exploration_rate': 0.1,
    'max_iterations_per_run': 100,
    'optimization_target_threshold': 0.95
}
agent_config = {}

def load_config():
    """Loads agent configuration from a JSON file."""
    global agent_config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            agent_config = json.load(f)
        print(f"Loaded configuration: {agent_config}")
    else:
        agent_config = DEFAULT_CONFIG
        save_config()
        print(f"No config file found. Created default: {agent_config}")

def save_config():
    """Saves current agent configuration to a JSON file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(agent_config, f, indent=4)
    print("Configuration saved.")

def log_performance(run_id, iteration, performance_metric, timestamp, metadata=None):
    """Logs performance metrics for a given run."""
    formatted_timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
    log_entry = {
        'run_id': run_id,
        'iteration': iteration,
        'performance_metric': performance_metric,
        'timestamp': timestamp,
        'formatted_timestamp': formatted_timestamp,
        'metadata': metadata if metadata else {}
    }
    with open(PERFORMANCE_LOG, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    print(f"📊 [{formatted_timestamp}] Logged performance: Run {run_id}, Iteration {iteration}, Metric: {performance_metric:.3f}")

def get_recent_performance(num_entries=100):
    """Retrieves recent performance entries from the log."""
    performance_data = []
    if os.path.exists(PERFORMANCE_LOG):
        with open(PERFORMANCE_LOG, 'r') as f:
            for line in f:
                try: # Added try-except for robustness against malformed JSON lines
                    performance_data.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON line in {PERFORMANCE_LOG}: {line.strip()}")
                    continue
    return performance_data[-num_entries:]

def log_improvement(timestamp, old_config, new_config, reason, performance_before, performance_after):
    """Logs changes made by the self-improvement mechanism."""
    log_entry = {
        'timestamp': timestamp,
        'old_config': old_config,
        'new_config': new_config,
        'reason': reason,
        'performance_before': performance_before,
        'performance_after': performance_after
    }
    with open(IMPROVEMENT_LOG, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    print(f"Logged improvement: {reason}")

def analyze_and_improve():
    """Analyzes recent performance and adjusts agent configuration for optimization."""
    print("\nAnalyzing performance for self-improvement...")
    recent_performance = get_recent_performance()

    if not recent_performance:
        print("Not enough performance data to analyze yet.")
        return

    total_metric = sum(entry['performance_metric'] for entry in recent_performance)
    average_performance = total_metric / len(recent_performance)
    print(f"Average recent performance: {average_performance:.4f}")

    old_config = agent_config.copy()
    reason = "No significant change."
    performance_before_improvement = average_performance

    if average_performance < agent_config['optimization_target_threshold']:
        if agent_config['exploration_rate'] < 0.5:
            agent_config['exploration_rate'] += agent_config['learning_rate'] * 0.1
            reason = "Increasing exploration rate due to low performance."
    else:
        if agent_config['exploration_rate'] > 0.05:
            agent_config['exploration_rate'] -= agent_config['learning_rate'] * 0.05
            reason = "Decreasing exploration rate due to good performance."

    performance_after_improvement = average_performance * 1.01

    if old_config != agent_config:
        save_config()
        log_improvement(
            time.time(),
            old_config,
            agent_config,
            reason,
            performance_before_improvement,
            performance_after_improvement
        )
    else:
        print("No configuration changes made.")

def autonomous_agent_loop():
    """Main loop that runs the AI agent autonomously with real Arbitrum interactions."""
    load_config()

    # Initialize Arbitrum testnet agent and strategy manager once
    arbitrum_agent = None
    strategy_manager = None

    try:
        arbitrum_agent = ArbitrumTestnetAgent()
        # --- IMPORTANT ADDITION: Initialize DeFi integrations ---
        if not arbitrum_agent.initialize_integrations():
            print("❌ DeFi integrations failed to initialize. Retrying in 30 seconds...")
            time.sleep(30)
            # Don't return here - let it continue and retry in the main loop
        else:
            strategy_manager = CollaborativeStrategyManager(arbitrum_agent)
            print("🚀 Arbitrum agent initialized successfully!")
            print("🤝 Collaborative strategy manager ready!")
    except Exception as e:
        print(f"❌ Failed to initialize Arbitrum agent or its integrations: {e}")
        print("💡 Please ensure your .env file is correctly set up and dependencies are installed.")
        print("🔄 Will retry initialization in the main loop...")
        # Don't return here - let the main loop handle retries

    # --- CONTINUOUS OPERATION LOOP ---
    iteration = 0
    run_id_counter = 0

    while True:  # This ensures the loop runs continuously
        iteration += 1
        print(f"\n--- Autonomous Agent Loop: Iteration {iteration} ---")

        try:
            # Add timestamp to iteration start
            iteration_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            print(f"\n⏰ ITERATION {iteration} STARTED AT: {iteration_timestamp}")

            # Check if agent needs initialization or reinitialization
            if arbitrum_agent is None or not hasattr(arbitrum_agent, 'aave') or arbitrum_agent.aave is None:
                print("🔄 Agent not initialized or missing integrations, attempting to initialize...")
                
                # Validate API keys before initialization
                try:
                    from validate_api_keys import main as validate_apis
                    api_validation = validate_apis()
                    if not api_validation:
                        print("⚠️ API validation failed, but continuing with fallback data...")
                except ImportError:
                    print("⚠️ API validation script not found, continuing...")
                except Exception as e:
                    print(f"⚠️ API validation error: {e}, continuing...")
                
                try:
                    arbitrum_agent = ArbitrumTestnetAgent()
                    if arbitrum_agent.initialize_integrations():
                        try:
                            strategy_manager = CollaborativeStrategyManager(arbitrum_agent)
                            print("✅ Agent and strategy manager successfully initialized!")
                        except ImportError:
                            print("⚠️ Strategy manager not available, continuing with agent only")
                            strategy_manager = None
                    else:
                        print("⚠️ Integration initialization failed, will retry next iteration")
                        time.sleep(45)
                        continue
                except Exception as init_error:
                    print(f"⚠️ Agent initialization error: {init_error}")
                    time.sleep(45)
                    continue

            # Start a new run every 10 iterations or on first run
            if iteration == 1 or (iteration - 1) % 10 == 0:
                run_id_counter += 1
                print(f"\n--- Starting New Autonomous Run: {run_id_counter} ---")

            # Main agent logic
            timestamp = time.time()

            # Check market signal integration status
            market_signals_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
            coinapi_key = os.getenv('COINAPI_KEY') or os.getenv('COIN_API_KEY') 
            coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
            
            # Debug API availability
            if coinapi_key:
                print(f"🎯 CoinAPI key available for primary market data")
            if coinmarketcap_key:
                print(f"🔄 CoinMarketCap key available for secondary market data")
            
            if market_signals_enabled and hasattr(arbitrum_agent, 'market_signal_strategy') and arbitrum_agent.market_signal_strategy:
                try:
                    # Test if strategy is functional
                    strategy_status = arbitrum_agent.market_signal_strategy.get_strategy_status()
                    
                    if strategy_status.get('initialized', False) or strategy_status.get('initialization_successful', False):
                        arbitrum_agent.debt_swap_active = True
                        
                        # Determine operation mode
                        if strategy_status.get('enhanced_mode', False):
                            mode = "Enhanced CoinMarketCap"
                        elif hasattr(arbitrum_agent.market_signal_strategy, 'enhanced_analyzer') and \
                             getattr(arbitrum_agent.market_signal_strategy.enhanced_analyzer, 'mock_mode', False):
                            mode = "Mock Data (Rate Limited)"
                        else:
                            mode = "Conservative Fallback"
                            
                        print("🔄 INTEGRATED TRIGGER SYSTEM: All triggers active")
                        print(f"   • Market Signal Mode: {mode}")
                        print("   • Growth-Triggered System: ✅ Active") 
                        print("   • Capacity-Based System: ✅ Active")
                        print("   • Debt Swap Integration: ✅ Active")
                    else:
                        print("⚠️ Market Signal Strategy initialized but not fully functional")
                        print(f"   Status: {strategy_status}")
                        
                except Exception as status_error:
                    print(f"⚠️ Market Signal Strategy status check failed: {status_error}")
                    
            elif market_signals_enabled:
                print("⚠️ Market signals enabled but strategy not properly initialized")
                if not hasattr(arbitrum_agent, 'market_signal_strategy'):
                    print("   • Strategy attribute missing")
                elif not arbitrum_agent.market_signal_strategy:
                    print("   • Strategy is None")
            else:
                print("ℹ️ Market signals disabled (MARKET_SIGNAL_ENABLED=false)")

            # Use real DeFi operations instead of simulation
            performance = arbitrum_agent.run_real_defi_task(run_id_counter, iteration, agent_config)
            log_performance(run_id_counter, iteration, performance, timestamp)

            # Analyze and improve periodically
            if iteration % 5 == 0:
                analyze_and_improve()

            # Collaborative strategy analysis (only if strategy_manager is available)
            if strategy_manager:
                print("\n🤝 COLLABORATIVE STRATEGY ANALYSIS:")
                strategy_manager.agent_analyze_and_propose()
                pending_proposals = strategy_manager.get_user_input_on_proposals()

                # Check for any auto-approved low-risk improvements
                if pending_proposals:
                    for proposal in pending_proposals:
                        if proposal['risk_level'] == 'Low' and proposal['source'] == 'agent':
                            print(f"🟢 Auto-implementing low-risk proposal: {proposal['id']}")
                            strategy_manager.implement_approved_strategy(proposal['id'])

            completion_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            print(f"✅ [{completion_timestamp}] Iteration {iteration} completed successfully. Waiting for next cycle.")

        except Exception as e:
            # Catch any unexpected errors during an iteration
            print(f"❌ Error in autonomous agent loop during iteration {iteration}: {e}")
            traceback.print_exc()  # Print the full traceback for debugging
            print("❗ Attempting to continue after error...")

            # Try to reinitialize connections if needed
            if "connection" in str(e).lower() or "rpc" in str(e).lower():
                try:
                    print("🔄 Attempting to reinitialize agent connections...")
                    if arbitrum_agent:
                        arbitrum_agent.initialize_integrations()
                    print("✅ Connections reinitialized successfully")
                except Exception as reinit_error:
                    print(f"⚠️ Failed to reinitialize connections: {reinit_error}")

        finally:
            # This block will always execute, whether there was an error or not.
            # It's important for controlling the loop's frequency.
            sleep_duration_seconds = 45  # Sleep for 45 seconds
            print(f"💤 Sleeping for {sleep_duration_seconds} seconds before next iteration...")
            time.sleep(sleep_duration_seconds)

if __name__ == "__main__":
    print("🤖 Starting Real Arbitrum DeFi Agent")
    print("=" * 50)

    # Check if wallet is set up
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("💡 Run 'python setup_test_wallet.py' to set up your test wallet first")
        exit(1)

    # Ensure log files exist
    if not os.path.exists(PERFORMANCE_LOG):
        with open(PERFORMANCE_LOG, 'w') as f:
            pass

    if not os.path.exists(IMPROVEMENT_LOG):
        with open(IMPROVEMENT_LOG, 'w') as f:
            pass

    # Check for auto mode environment variable
    auto_mode = os.getenv('AUTO_MODE')

    if auto_mode:
        choice = "1"
        print("🤖 AUTO MODE DETECTED - Starting autonomous mode...")
    else:
        # Ask user for mode
        print("\nChoose operation mode:")
        print("1. 🤖 Autonomous mode (bot runs automatically)")
        print("2. 🎛️ Manual mode (you control each action)")
        print("3. 🌐 Web dashboard (browser interface)")

        # Get user choice with timeout for preview mode
        try:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Input timeout")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)  # 5 second timeout

            try:
                choice = input("Enter choice (1-3): ").strip()
                signal.alarm(0)  # Cancel timeout
            except (TimeoutError, EOFError):
                signal.alarm(0)
                choice = '3'  # Auto-select dashboard for preview
                print("🌐 Auto-selecting Web Dashboard for preview...")

            # Auto-select dashboard if no input
            if not choice:
                choice = '3'
                print("🌐 Auto-selecting Web Dashboard...")

        except (KeyboardInterrupt):
            print("\n👋 Goodbye!")
            exit(0)

    if choice == "1":
        # Autonomous mode - Enhanced with capacity-based system
        print("🚀 Starting Autonomous Mode with Capacity-Based System...")
        # Assuming AutonomousLauncher is defined elsewhere and properly initialized
        # You may need to import it or define it within this script.
        # Example: from your_module import AutonomousLauncher
        # agent = ...  # Assuming your agent is initialized somewhere
        # launcher = AutonomousLauncher(agent)
        # launcher.run_autonomous_mode()
        autonomous_agent_loop()
    elif choice == "2":
        print("🎛️ Starting manual controls...")
        os.system("python manual_controls.py")
    elif choice == "3":
        print("🌐 Starting web dashboard...")
        os.system("python web_dashboard.py")
    else:
        print("❌ Invalid choice. Starting autonomous mode by default.")
        autonomous_agent_loop()