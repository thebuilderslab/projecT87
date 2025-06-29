
#!/usr/bin/env python3
"""
Autonomous Mode Launcher - Automatically starts the DeFi agent in autonomous mode
"""

import os
import sys

def run_autonomous_mode():
    """Launch autonomous mode directly"""
    print("🤖 LAUNCHING AUTONOMOUS DEFI AGENT")
    print("=" * 50)
    
    # Set environment for autonomous mode
    os.environ['AUTO_MODE'] = '1'
    
    # Import and run the autonomous loop
    try:
        from main import autonomous_agent_loop, load_config
        
        print("✅ Starting autonomous agent loop...")
        print("📊 The agent will run continuously and make decisions automatically")
        print("🛑 Press Ctrl+C to stop the agent")
        print("=" * 50)
        
        # Load configuration
        load_config()
        
        # Start the autonomous loop
        autonomous_agent_loop()
        
    except KeyboardInterrupt:
        print("\n🛑 Autonomous mode stopped by user")
    except Exception as e:
        print(f"\n❌ Error in autonomous mode: {e}")
        print("💡 Check your wallet funding and network connection")

if __name__ == "__main__":
    run_autonomous_mode()
