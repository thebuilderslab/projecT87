#!/usr/bin/env python3
"""
Real Agent Testing Module
Test actual agent initialization and basic functionality
"""

import os
import sys

def test_real_agent_initialization():
    """Test real agent initialization"""
    print("🔍 REAL AGENT INITIALIZATION TEST")
    print("=" * 50)

    try:
        # Import and initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        print("✅ Agent module imported successfully")

        # Test initialization
        agent = ArbitrumTestnetAgent()
        print("✅ Agent initialized successfully")

        # Test basic properties
        if hasattr(agent, 'address') and agent.address:
            print(f"✅ Wallet address: {agent.address}")
        else:
            print("❌ Wallet address not set")
            return False

        if hasattr(agent, 'network_mode'):
            print(f"✅ Network mode: {agent.network_mode}")
        else:
            print("❌ Network mode not set")
            return False

        # Test Web3 connection
        if hasattr(agent, 'w3') and agent.w3 and agent.w3.is_connected():
            chain_id = agent.w3.eth.chain_id
            print(f"✅ Web3 connected - Chain ID: {chain_id}")
        else:
            print("❌ Web3 connection failed")
            return False

        # Test DeFi integrations initialization
        try:
            success = agent.initialize_integrations()
            if success:
                print("✅ DeFi integrations initialized successfully")
            else:
                print("⚠️ DeFi integrations partially initialized")
        except Exception as e:
            print(f"⚠️ DeFi integration error: {e}")

        print("✅ Real agent test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Real agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_agent_initialization()
    sys.exit(0 if success else 1)