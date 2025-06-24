
import os
import time
import threading
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from collaborative_strategy_manager import CollaborativeStrategyManager

class MainnetSafetyManager:
    """Manages safety features for mainnet deployment"""
    
    def __init__(self):
        self.emergency_stop = False
        self.emergency_stop_file = 'EMERGENCY_STOP.txt'
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

def launch_mainnet_agent():
    """MAINNET DEPLOYMENT LAUNCHER WITH SAFETY FEATURES"""
    print("🚨" * 30)
    print("MAINNET DEPLOYMENT - REAL FUNDS AT RISK")
    print("🚨" * 30)
    
    # Initialize safety manager
    safety_manager = MainnetSafetyManager()
    
    # Multiple confirmation steps
    print("\n📋 PRE-DEPLOYMENT CHECKLIST:")
    print("1. ✓ All tests passed (run python test_agent.py)")
    print("2. ✓ Wallet funded with sufficient ETH and collateral")
    print("3. ✓ All secrets configured for mainnet")
    print("4. ✓ Emergency stop mechanism understood")
    print("5. ✓ Monitoring dashboard accessible")
    
    confirmation1 = input("\n❓ Have you completed ALL items above? (type 'YES'): ")
    if confirmation1 != 'YES':
        print("❌ Deployment cancelled - complete checklist first")
        return
    
    print(f"\n🛑 EMERGENCY STOP INSTRUCTIONS:")
    print(f"   - Create file: {safety_manager.emergency_stop_file}")
    print(f"   - Or press Ctrl+C in console")
    print(f"   - Agent will halt all operations immediately")
    
    confirmation2 = input("\n❓ Type 'DEPLOY_MAINNET_WITH_REAL_FUNDS' to proceed: ")
    if confirmation2 != 'DEPLOY_MAINNET_WITH_REAL_FUNDS':
        print("❌ Deployment cancelled")
        return
    
    try:
        # Initialize mainnet agent with safety checks
        print("🔄 Initializing mainnet agent...")
        agent = ArbitrumTestnetAgent('mainnet')
        strategy_manager = CollaborativeStrategyManager(agent)
        
        print("🚀 MAINNET AGENT ACTIVE")
        print(f"💰 Wallet: {agent.address}")
        print(f"🌐 Network: Arbitrum Mainnet (Chain ID: {agent.w3.eth.chain_id})")
        print(f"💵 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Verify sufficient balance
        eth_balance = agent.get_eth_balance()
        if eth_balance < 0.01:  # Minimum 0.01 ETH for gas
            safety_manager.trigger_emergency_stop("Insufficient ETH balance for gas")
            return
        
        # Start monitoring thread
        def safety_monitor():
            while safety_manager.monitoring_active:
                if safety_manager.check_emergency_stop():
                    print("🛑 EMERGENCY STOP DETECTED - HALTING ALL OPERATIONS")
                    return
                time.sleep(5)  # Check every 5 seconds
        
        monitoring_thread = threading.Thread(target=safety_monitor, daemon=True)
        monitoring_thread.start()
        
        # Start autonomous loop with enhanced safety
        run_id_counter = 0
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while not safety_manager.check_emergency_stop():
            try:
                run_id_counter += 1
                print(f"\n--- MAINNET RUN: {run_id_counter} ---")
                
                # Pre-execution safety checks
                current_hf = None
                if hasattr(agent, 'health_monitor'):
                    hf_data = agent.health_monitor.get_current_health_factor()
                    if hf_data:
                        current_hf = hf_data['health_factor']
                        
                        # Emergency stop if health factor too low
                        if current_hf < 1.05:
                            safety_manager.trigger_emergency_stop(f"Critical health factor: {current_hf}")
                            break
                
                # Execute with conservative settings for mainnet
                conservative_config = {
                    'exploration_rate': 0.02,  # Very conservative
                    'health_factor_target': 1.25,  # Higher safety margin
                    'max_single_operation_eth': 0.1  # Limit operation size
                }
                
                performance = agent.run_real_defi_task(run_id_counter, 1, conservative_config)
                
                # Safety performance thresholds
                if performance < 0.3:
                    consecutive_failures += 1
                    print(f"⚠️ Poor performance ({performance:.2f}) - Failure count: {consecutive_failures}")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        safety_manager.trigger_emergency_stop("Too many consecutive failures")
                        break
                else:
                    consecutive_failures = 0  # Reset failure counter
                
                # Conservative sleep between operations
                time.sleep(60)  # 1 minute between operations
                
            except KeyboardInterrupt:
                safety_manager.trigger_emergency_stop("User interrupted (Ctrl+C)")
                break
            except Exception as e:
                consecutive_failures += 1
                print(f"❌ MAINNET ERROR: {e}")
                
                if consecutive_failures >= max_consecutive_failures:
                    safety_manager.trigger_emergency_stop(f"Critical error: {e}")
                    break
                
                print("🛡️ Entering safe mode for 2 minutes...")
                time.sleep(120)
        
        # Cleanup
        safety_manager.monitoring_active = False
        print("🏁 Mainnet agent stopped safely")
        
    except Exception as e:
        safety_manager.trigger_emergency_stop(f"Initialization error: {e}")
        print(f"❌ CRITICAL ERROR: {e}")

def emergency_stop():
    """Manual emergency stop trigger"""
    safety_manager = MainnetSafetyManager()
    safety_manager.trigger_emergency_stop("Manual emergency stop")
    print("🚨 Emergency stop activated!")

if __name__ == "__main__":
    launch_mainnet_agent()
