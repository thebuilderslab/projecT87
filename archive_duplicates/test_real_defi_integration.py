
def test_real_defi_integration():
    """Test function for real DeFi integration"""
    print("🧪 Testing real DeFi integration...")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: {agent.network_mode}")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_real_defi_integration()
