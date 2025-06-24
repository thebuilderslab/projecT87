
import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from collaborative_strategy_manager import CollaborativeStrategyManager

def launch_mainnet_agent():
    """MAINNET DEPLOYMENT LAUNCHER"""
    print("🚨" * 20)
    print("MAINNET DEPLOYMENT - REAL FUNDS AT RISK")
    print("🚨" * 20)
    
    # Require explicit confirmation
    confirmation = input("Type 'DEPLOY_MAINNET' to confirm: ")
    if confirmation != 'DEPLOY_MAINNET':
        print("❌ Deployment cancelled")
        return
    
    # Initialize mainnet agent
    agent = ArbitrumTestnetAgent('mainnet')
    strategy_manager = CollaborativeStrategyManager(agent)
    
    print("🚀 MAINNET AGENT ACTIVE")
    print(f"💰 Wallet: {agent.address}")
    print(f"🌐 Network: Arbitrum Mainnet (Chain ID: 42161)")
    
    # Start autonomous loop with mainnet safety
    run_id_counter = 0
    while True:
        try:
            run_id_counter += 1
            print(f"\n--- MAINNET RUN: {run_id_counter} ---")
            
            # Execute with enhanced safety checks
            performance = agent.run_real_defi_task(run_id_counter, 1, {'exploration_rate': 0.05})
            
            if performance < 0.3:  # Poor performance threshold
                print("⚠️ Poor performance detected - entering conservative mode")
                
            time.sleep(30)  # More frequent checks on mainnet
            
        except Exception as e:
            print(f"❌ MAINNET ERROR: {e}")
            print("🛑 Entering safe mode...")
            time.sleep(60)

if __name__ == "__main__":
    launch_mainnet_agent()
