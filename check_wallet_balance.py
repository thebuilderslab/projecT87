
#!/usr/bin/env python3
"""
Check wallet balance and provide funding guidance
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Check current wallet balances and provide funding guidance"""
    print("💰 WALLET BALANCE CHECK")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        print(f"📍 Wallet Address: {agent.address}")
        print(f"🌐 Network: {agent.w3.eth.chain_id} ({'Mainnet' if agent.w3.eth.chain_id == 42161 else 'Testnet'})")
        
        # Initialize integrations
        if agent.initialize_integrations():
            print("✅ Integrations initialized")
            
            # Check ETH balance
            eth_balance = agent.get_eth_balance()
            print(f"⚡ ETH Balance: {eth_balance:.6f} ETH")
            
            if eth_balance < 0.01:
                print("⚠️ Low ETH balance - you need ETH for gas fees")
                print("💡 Recommended: At least 0.1 ETH for multiple transactions")
            
            # Check token balances
            if hasattr(agent, 'aave') and agent.aave:
                try:
                    usdc_balance = agent.aave.get_token_balance(agent.usdc_address)
                    wbtc_balance = agent.aave.get_token_balance(agent.wbtc_address)
                    
                    print(f"💵 USDC Balance: {usdc_balance:.6f} USDC")
                    print(f"🪙 WBTC Balance: {wbtc_balance:.8f} WBTC")
                    
                    # Check if sufficient for swap
                    required_usdc = 40.6293
                    if usdc_balance >= required_usdc:
                        print(f"✅ Sufficient USDC for swap ({required_usdc} USDC required)")
                    else:
                        print(f"❌ Insufficient USDC for swap")
                        print(f"   Required: {required_usdc:.4f} USDC")
                        print(f"   Current:  {usdc_balance:.4f} USDC")
                        print(f"   Needed:   {required_usdc - usdc_balance:.4f} USDC")
                        
                        print("\n💡 FUNDING OPTIONS:")
                        print("1. Transfer USDC to your wallet from an exchange")
                        print("2. Use a DEX to swap ETH → USDC")
                        print("3. Bridge USDC from another chain")
                        print(f"   Wallet: {agent.address}")
                        
                except Exception as e:
                    print(f"⚠️ Could not check token balances: {e}")
        else:
            print("❌ Failed to initialize integrations")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
