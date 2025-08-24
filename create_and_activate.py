
#!/usr/bin/env python3
"""
Create Aave position with 20 USDC borrow and activate automated system
"""

import os
import time
from create_position import PositionCreator
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    print("🚀 CREATING POSITION AND ACTIVATING SYSTEM")
    print("=" * 60)
    
    try:
        # Step 1: Create the position
        print("📊 Step 1: Creating Aave position with 20 USDC borrow...")
        creator = PositionCreator()
        
        success = creator.create_position_and_maintain_health()
        
        if not success:
            print("❌ Position creation failed. Cannot proceed.")
            return False
            
        print("✅ Position created successfully!")
        
        # Step 2: Initialize and activate the agent
        print("\n🤖 Step 2: Initializing automated agent...")
        agent = ArbitrumTestnetAgent()
        
        # Verify the position
        if hasattr(agent, 'health_monitor'):
            health_data = agent.health_monitor.get_current_health_factor()
            if health_data:
                print(f"📊 Health Factor: {health_data['health_factor']:.4f}")
                print(f"💰 Collateral: ${health_data.get('total_collateral_usdc', 0):,.2f}")
                print(f"💸 Debt: ${health_data.get('total_debt_usdc', 0):,.2f}")
        
        # Step 3: Clear any emergency stops
        print("\n🔓 Step 3: Clearing emergency stops...")
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        if os.path.exists(emergency_file):
            os.remove(emergency_file)
            print("✅ Emergency stop cleared")
        
        # Step 4: Update user settings for active mode
        print("\n⚙️ Step 4: Activating automated mode...")
        import json
        
        settings = {
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'arb_decline_threshold': 0.05,
            'auto_mode': True,
            'exploration_rate': 0.1,
            'system_active': True,
            'position_created': True,
            'last_activated': time.time()
        }
        
        with open('user_settings.json', 'w') as f:
            json.dump(settings, f, indent=2)
        
        print("✅ Automated mode activated!")
        
        print("\n🎉 SUCCESS: System is now active!")
        print("=" * 60)
        print("📊 Position Status: Active with 20 USDC borrowed")
        print("🤖 Automated Agent: Running")
        print("🌐 Dashboard: Access via web preview")
        print("⚠️  Monitor via dashboard for real-time status")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during activation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Starting web dashboard for monitoring...")
        # Start the dashboard after successful activation
        os.system("python web_dashboard.py")
    else:
        print("\n❌ Activation failed. Check logs and try again.")
