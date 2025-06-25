
#!/usr/bin/env python3
"""
Supply WBTC to Aave V3 Script
Execute: python supply_wbtc.py
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from manual_controls import ManualControls

def main():
    """Supply 0.0004087 WBTC to Aave V3 as collateral"""
    print("🪙 WBTC Supply to Aave V3")
    print("=" * 50)
    
    # Check environment
    if not os.getenv('PRIVATE_KEY') and not os.getenv('PRIVATE_KEY2'):
        print("❌ No private key found in environment!")
        print("💡 Please ensure PRIVATE_KEY is set in Replit Secrets")
        return
    
    network_mode = os.getenv('NETWORK_MODE', 'testnet')
    print(f"🌐 Network Mode: {network_mode}")
    
    if network_mode == 'mainnet':
        print("🚨 MAINNET MODE - Using real funds!")
    else:
        print("🧪 TESTNET MODE - Safe for testing")
    
    try:
        # Initialize agent
        print("🤖 Initializing DeFi agent...")
        agent = ArbitrumTestnetAgent()
        
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Chain ID: {agent.w3.eth.chain_id}")
        
        # Check WBTC balance
        wbtc_balance = agent.aave.get_token_balance(agent.aave.wbtc_address)
        print(f"💰 Current WBTC balance: {wbtc_balance:.8f}")
        
        target_amount = 0.0004087
        print(f"🎯 Target supply amount: {target_amount:.8f} WBTC")
        
        if wbtc_balance < target_amount:
            print(f"❌ Insufficient WBTC balance!")
            print(f"   Need: {target_amount:.8f} WBTC")
            print(f"   Have: {wbtc_balance:.8f} WBTC")
            print(f"   Missing: {target_amount - wbtc_balance:.8f} WBTC")
            print("💡 Please ensure your wallet has sufficient WBTC balance")
            return
        
        # Supply WBTC to Aave
        print(f"\n🚀 Executing WBTC supply to Aave V3...")
        tx_hash = agent.aave.supply_wbtc_to_aave(target_amount)
        
        if tx_hash:
            print(f"✅ SUCCESS! WBTC supplied to Aave V3")
            print(f"📄 Transaction Hash: {tx_hash}")
            print(f"💡 You can now borrow against this WBTC collateral")
            
            # Check new health factor
            try:
                health_data = agent.health_monitor.get_current_health_factor()
                if health_data:
                    print(f"🏥 New Health Factor: {health_data['health_factor']:.4f}")
                else:
                    print("📊 Health factor will be available after transaction confirmation")
            except Exception as e:
                print(f"⚠️ Could not fetch health factor: {e}")
        else:
            print(f"❌ WBTC supply failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Ensure your wallet is properly funded and try again")

if __name__ == "__main__":
    main()
