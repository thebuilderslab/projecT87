
#!/usr/bin/env python3
"""
WALLET VALUE CHECKER
Check the total value of any wallet address on Arbitrum
"""

import os
from web3 import Web3
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def check_wallet_value(wallet_address):
    """Check the total value of a specific wallet address"""
    print(f"💰 WALLET VALUE ANALYSIS")
    print("=" * 50)
    print(f"📍 Wallet: {wallet_address}")
    
    try:
        # Initialize agent to get Web3 connection
        agent = ArbitrumTestnetAgent()
        w3 = agent.w3
        
        print(f"🌐 Network: {w3.eth.chain_id} ({'Arbitrum Mainnet' if w3.eth.chain_id == 42161 else 'Arbitrum Testnet'})")
        
        total_value_usd = 0.0
        
        # Check ETH balance
        eth_balance = w3.eth.get_balance(wallet_address)
        eth_balance_ether = float(w3.from_wei(eth_balance, 'ether'))
        eth_value_usd = eth_balance_ether * 2500  # Approximate ETH price
        total_value_usd += eth_value_usd
        
        print(f"⚡ ETH Balance: {eth_balance_ether:.6f} ETH (${eth_value_usd:.2f})")
        
        # Initialize Aave integration for token checks
        if agent.initialize_integrations():
            # Check major token balances
            tokens_to_check = {
                'USDC': {'address': '0xaf88d065eec38fad0aeff3e253e648a15cee23dc', 'decimals': 6, 'price': 1.0},
                'WBTC': {'address': '0x2f2a2543b76a4166549f7bffbe68df6fc579b2f3', 'decimals': 8, 'price': 95000},
                'WETH': {'address': '0x82af49447d8a07e3bd95bd0d56f35241523fbab1', 'decimals': 18, 'price': 2500},
                'ARB': {'address': '0x912ce59144191c1f20bdd2ce08f2a688feaebb0b', 'decimals': 18, 'price': 0.75},
                'DAI': {'address': '0xda10009cbd56d0f34a29c7aa35e34d246da651d0', 'decimals': 18, 'price': 1.0}
            }
            
            print(f"\n🪙 TOKEN BALANCES:")
            for token_name, token_info in tokens_to_check.items():
                try:
                    # Create token contract
                    token_abi = [{
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function"
                    }]
                    
                    contract = w3.eth.contract(
                        address=Web3.to_checksum_address(token_info['address']),
                        abi=token_abi
                    )
                    
                    balance_wei = contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
                    balance = balance_wei / (10 ** token_info['decimals'])
                    
                    if balance > 0:
                        value_usd = balance * token_info['price']
                        total_value_usd += value_usd
                        print(f"   {token_name}: {balance:.6f} (${value_usd:.2f})")
                    else:
                        print(f"   {token_name}: 0.000000")
                        
                except Exception as e:
                    print(f"   {token_name}: Error checking balance ({str(e)[:50]})")
            
            # Check Aave positions if available
            try:
                from aave_health_monitor import AaveHealthMonitor
                health_monitor = AaveHealthMonitor(w3, wallet_address, agent.aave_pool_address)
                
                health_data = health_monitor.get_current_health_factor()
                if health_data and health_data.get('total_collateral_eth', 0) > 0:
                    print(f"\n🏦 AAVE POSITIONS:")
                    
                    collateral_usd = health_data.get('total_collateral_eth', 0) * 2500
                    debt_usd = health_data.get('total_debt_eth', 0) * 2500
                    net_aave_value = collateral_usd - debt_usd
                    
                    print(f"   💰 Collateral: ${collateral_usd:.2f}")
                    print(f"   💸 Debt: ${debt_usd:.2f}")
                    print(f"   📊 Net Aave Value: ${net_aave_value:.2f}")
                    print(f"   🔒 Health Factor: {health_data.get('health_factor', 0):.3f}")
                    
                    total_value_usd += net_aave_value
                else:
                    print(f"\n🏦 AAVE POSITIONS: None found")
                    
            except Exception as e:
                print(f"\n🏦 AAVE POSITIONS: Could not check ({str(e)[:50]})")
        
        else:
            print("⚠️ Could not initialize integrations for detailed token analysis")
        
        print(f"\n💎 TOTAL WALLET VALUE")
        print("=" * 30)
        print(f"💰 Estimated Total: ${total_value_usd:.2f} USD")
        
        if total_value_usd > 1000:
            print(f"✅ High-value wallet detected")
        elif total_value_usd > 100:
            print(f"💡 Medium-value wallet")
        else:
            print(f"🔍 Low-value or empty wallet")
        
        return total_value_usd
        
    except Exception as e:
        print(f"❌ Error analyzing wallet: {e}")
        return 0.0

def main():
    """Main function to check wallet value"""
    # Check the specific wallet address
    wallet_address = "0x5b823270e3719cde8669e5e5326b455eaa8a350b"
    
    try:
        # Validate address format
        checksum_address = Web3.to_checksum_address(wallet_address)
        total_value = check_wallet_value(checksum_address)
        
        print(f"\n🎯 ANALYSIS COMPLETE")
        print(f"Wallet {wallet_address} has an estimated value of ${total_value:.2f} USD")
        
    except Exception as e:
        print(f"❌ Invalid wallet address or analysis failed: {e}")

if __name__ == "__main__":
    main()
