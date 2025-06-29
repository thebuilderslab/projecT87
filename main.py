from arbitrum_testnet_agent import ArbitrumTestnetAgent # Assuming this is where your agent class is
from collaborative_strategy_manager import CollaborativeStrategyManager
import time
import json
import os

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
    log_entry = {
        'run_id': run_id,
        'iteration': iteration,
        'performance_metric': performance_metric,
        'timestamp': timestamp,
        'metadata': metadata if metadata else {}
    }
    with open(PERFORMANCE_LOG, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    print(f"Logged performance: Run {run_id}, Iteration {iteration}, Metric: {performance_metric}")

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

    # Initialize Arbitrum testnet agent
    try:
        arbitrum_agent = ArbitrumTestnetAgent()
        # --- IMPORTANT ADDITION: Initialize DeFi integrations ---
        if not arbitrum_agent.initialize_integrations():
            print("❌ DeFi integrations failed to initialize. Cannot proceed with autonomous loop.")
            return # Exit if integrations fail

        strategy_manager = CollaborativeStrategyManager(arbitrum_agent)
        print("🚀 Arbitrum agent initialized successfully!")
        print("🤝 Collaborative strategy manager ready!")
    except Exception as e:
        print(f"❌ Failed to initialize Arbitrum agent or its integrations: {e}")
        print("💡 Please ensure your .env file is correctly set up and dependencies are installed.")
        return

    run_id_counter = 0

    while True:
        run_id_counter += 1
        print(f"\n--- Starting New Autonomous Run: {run_id_counter} ---")

        for iteration in range(agent_config['max_iterations_per_run']):
            timestamp = time.time()

            # Use real DeFi operations instead of simulation
            performance = arbitrum_agent.run_real_defi_task(run_id_counter, iteration, agent_config)
            log_performance(run_id_counter, iteration, performance, timestamp)

            if performance >= 0.99 and iteration > 5:
                print(f"Achieved high performance ({performance:.2f}), breaking current run early.")
                break

            time.sleep(1)

        analyze_and_improve()

        # Collaborative strategy analysis
        print("\n🤝 COLLABORATIVE STRATEGY ANALYSIS:")
        strategy_manager.agent_analyze_and_propose()
        pending_proposals = strategy_manager.get_user_input_on_proposals()

        # Check for any auto-approved low-risk improvements
        if pending_proposals:
            for proposal in pending_proposals:
                if proposal['risk_level'] == 'Low' and proposal['source'] == 'agent':
                    print(f"🟢 Auto-implementing low-risk proposal: {proposal['id']}")
                    strategy_manager.implement_approved_strategy(proposal['id'])

        print(f"\n--- Autonomous Run {run_id_counter} Completed. Waiting for next run... ---")
        time.sleep(5)

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

    # Ask user for mode
    print("\nChoose operation mode:")
    print("1. 🤖 Autonomous mode (bot runs automatically)")
    print("2. 🎛️ Manual mode (you control each action)")
    print("3. 🌐 Web dashboard (browser interface)")

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
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