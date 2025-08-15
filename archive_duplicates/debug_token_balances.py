
#!/usr/bin/env python3
"""
Debug script to diagnose token balance issues with detailed logging
"""

import logging
import sys
from datetime import datetime

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("debug_log_phase1_step1_1.txt")
    ]
)

def main():
    """Run enhanced token balance diagnostic"""
    print("🔍 ENHANCED TOKEN BALANCE DIAGNOSTIC")
    print("=" * 50)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    try:
        # Initialize the agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        logging.debug("DEBUG: Initializing ArbitrumTestnetAgent")
        agent = ArbitrumTestnetAgent()
        logging.debug(f"DEBUG: Agent initialized with address: {agent.address}")
        
        # Initialize DeFi integrations
        if not hasattr(agent, 'aave') or agent.aave is None:
            logging.debug("DEBUG: Initializing DeFi integrations")
            success = agent.initialize_integrations()
            logging.debug(f"DEBUG: DeFi integrations initialized: {success}")
        
        # Initialize the diagnostic tool
        from borrow_diagnostic_tool import BorrowDiagnosticTool
        logging.debug("DEBUG: Initializing BorrowDiagnosticTool")
        diagnostic = BorrowDiagnosticTool(agent)
        
        # Run the token balance diagnostic
        logging.debug("DEBUG: Running token balance diagnostic")
        diagnostic.diagnose_token_balances()
        
        print("\n✅ Enhanced diagnostic completed successfully")
        print(f"📄 Debug log saved to: debug_log_phase1_step1_1.txt")
        
    except Exception as e:
        logging.error(f"ERROR: Enhanced diagnostic failed: {e}", exc_info=True)
        print(f"❌ Diagnostic failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
