
#!/usr/bin/env python3
"""
Token Address Verification Script
Verifies correct token addresses and balances for Arbitrum Mainnet
"""

import os
from web3 import Web3
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def verify_token_addresses():
    """Verify all token addresses are correct for Arbitrum Mainnet"""
    print("🔍 TOKEN ADDRESS VERIFICATION")
    print("=" * 50)
    
    # Correct Arbitrum Mainnet token addresses
    correct_addresses = {
        'WBTC': '0x2f2a2543B76A4166549F7BffBE68df6Fc579b2F3',
        'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1', 
        'USDC': '0xaf88d065eec38faD0AEfF3e253e648a15cEe23dC',
        'ARB': '0x912CE59144191C1204E64559FE8253a0e49E6548'
    }
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent('mainnet')
        print(f"✅ Connected to Arbitrum Mainnet (Chain ID: {agent.w3.eth.chain_id})")
        print(f"📍 Wallet: {agent.address}")
        
        # ERC20 ABI for balance and name checking
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol", 
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
        
        print(f"\n🪙 TOKEN VERIFICATION RESULTS:")
        print("-" * 40)
        
        for token_name, address in correct_addresses.items():
            try:
                # Create contract instance
                contract = agent.w3.eth.contract(
                    address=Web3.to_checksum_address(address),
                    abi=erc20_abi
                )
                
                # Get token info
                try:
                    name = contract.functions.name().call()
                    symbol = contract.functions.symbol().call()
                    decimals = contract.functions.decimals().call()
                    balance_wei = contract.functions.balanceOf(agent.address).call()
                    balance = balance_wei / (10 ** decimals)
                    
                    print(f"✅ {token_name}: {address}")
                    print(f"   Name: {name}")
                    print(f"   Symbol: {symbol}")
                    print(f"   Decimals: {decimals}")
                    print(f"   Balance: {balance:.8f} {symbol}")
                    print()
                    
                except Exception as call_error:
                    print(f"⚠️ {token_name}: {address}")
                    print(f"   Contract exists but call failed: {call_error}")
                    print()
                    
            except Exception as e:
                print(f"❌ {token_name}: {address}")
                print(f"   Error: {e}")
                print()
        
        # Test current balance fetching
        print(f"🔍 TESTING CURRENT BALANCE FETCHING:")
        print("-" * 40)
        
        from accurate_debank_fetcher import AccurateWalletDataFetcher
        fetcher = AccurateWalletDataFetcher(agent.w3, agent.address)
        
        for token_name in ['WBTC', 'WETH', 'USDC']:
            token_address = correct_addresses[token_name]
            balance = fetcher._get_token_balance_reliable(token_address, token_name)
            print(f"💰 {token_name}: {balance:.8f}")
        
        print(f"\n✅ Token address verification complete")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    verify_token_addresses()
