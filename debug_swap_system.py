"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""


#!/usr/bin/env python3
"""
Comprehensive DAI → WBTC swap system debugger
Execute: python debug_swap_system.py
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def debug_private_key():
    """Debug private key configuration"""
    print("🔐 PRIVATE KEY DEBUGGING")
    print("=" * 40)
    
    pk1 = os.getenv('PRIVATE_KEY')
    pk2 = os.getenv('PRIVATE_KEY2')
    
    print(f"PRIVATE_KEY exists: {bool(pk1)}")
    print(f"PRIVATE_KEY2 exists: {bool(pk2)}")
    
    if pk1:
        print(f"PRIVATE_KEY length: {len(pk1)}")
        print(f"PRIVATE_KEY preview: {pk1[:10]}...")
        print(f"Contains placeholder: {'placeholder' in pk1.lower() or 'your_private_key_here' in pk1.lower()}")
    
    if pk2:
        print(f"PRIVATE_KEY2 length: {len(pk2)}")
        print(f"PRIVATE_KEY2 preview: {pk2[:10]}...")
        print(f"Contains placeholder: {'placeholder' in pk2.lower() or 'your_private_key_here' in pk2.lower()}")
    
    return bool(pk1 or pk2)

def debug_network_connection(agent):
    """Debug network connectivity"""
    print("\n🌐 NETWORK CONNECTION DEBUGGING")
    print("=" * 40)
    
    try:
        connected = agent.w3.is_connected()
        print(f"Web3 connected: {connected}")
        
        if connected:
            chain_id = agent.w3.eth.chain_id
            latest_block = agent.w3.eth.get_block('latest')
            gas_price = agent.w3.eth.gas_price
            
            print(f"Chain ID: {chain_id}")
            print(f"Latest block: {latest_block.number}")
            print(f"Gas price: {agent.w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
            
            if chain_id == 42161:
                print("✅ Connected to Arbitrum Mainnet")
            elif chain_id == 421614:
                print("✅ Connected to Arbitrum Sepolia")
            else:
                print(f"⚠️ Unknown network: {chain_id}")
            
            return True
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def debug_integrations(agent):
    """Debug DeFi integrations"""
    print("\n🔧 INTEGRATION DEBUGGING")
    print("=" * 40)
    
    try:
        success = agent.initialize_integrations()
        print(f"Integration init result: {success}")
        
        # Check Aave
        if hasattr(agent, 'aave'):
            aave_type = agent.aave.__class__.__name__
            print(f"Aave integration: {aave_type}")
            
            if 'Mock' in aave_type:
                print("⚠️ Using mock Aave - real transactions will fail")
            else:
                print("✅ Real Aave integration loaded")
                
                # Test Aave functionality
                try:
                    DAI_balance = agent.aave.get_token_balance(agent.dai_address)
                    print(f"DAI balance: {DAI_balance:.6f}")
                except Exception as e:
                    print(f"❌ Aave test failed: {e}")
        
        # Check Uniswap
        if hasattr(agent, 'uniswap'):
            uniswap_type = agent.uniswap.__class__.__name__
            print(f"Uniswap integration: {uniswap_type}")
            
            if 'Mock' in uniswap_type:
                print("⚠️ Using mock Uniswap - swaps will fail")
            else:
                print("✅ Real Uniswap integration loaded")
        
        return success
    except Exception as e:
        print(f"❌ Integration error: {e}")
        return False

def debug_token_contracts(agent):
    """Debug token contract connectivity"""
    print("\n💱 TOKEN CONTRACT DEBUGGING")
    print("=" * 40)
    
    contracts = {
        'DAI': agent.dai_address,
        'WBTC': agent.wbtc_address,
        'WETH': agent.weth_address
    }
    
    for name, address in contracts.items():
        try:
            print(f"\n{name} ({address}):")
            
            # Test basic contract call
            contract = agent.w3.eth.contract(
                address=address,
                abi=[{
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                }]
            )
            
            symbol = contract.functions.symbol().call()
            print(f"  Symbol: {symbol}")
            
            # Check balance
            balance_contract = agent.w3.eth.contract(
                address=address,
                abi=[{
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }]
            )
            
            balance_wei = balance_contract.functions.balanceOf(agent.address).call()
            
            if name == 'DAI':
                balance = balance_wei / (10 ** 6)
            elif name == 'WBTC':
                balance = balance_wei / (10 ** 8)
            else:  # WETH
                balance = balance_wei / (10 ** 18)
            
            print(f"  Balance: {balance:.8f}")
            print(f"  ✅ Contract responsive")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")

def main():
    """Main debugging function"""
    print("🔧 SWAP SYSTEM COMPREHENSIVE DEBUGGER")
    print("=" * 50)
    
    # Search for July 21st diagnostic files
    print("🔍 Searching for July 21st diagnostic files...")
    import glob
    july_21_files = glob.glob("*20250721*") + glob.glob("**/*20250721*", recursive=True)
    if july_21_files:
        print(f"📁 Found July 21st files: {july_21_files}")
        for file in july_21_files[:5]:  # Show first 5
            try:
                with open(file, 'r') as f:
                    content = f.read()[:500]  # First 500 chars
                    print(f"📄 {file}: {content}...")
            except:
                pass
    else:
        print("❌ No July 21st diagnostic files found")
    
    print("=" * 50)
    
    # Step 1: Debug private key
    pk_ok = debug_private_key()
    if not pk_ok:
        print("\n❌ CRITICAL: No private key found")
        print("💡 Set PRIVATE_KEY or PRIVATE_KEY2 in Replit Secrets")
        return
    
    try:
        # Step 2: Initialize agent
        print("\n🤖 AGENT INITIALIZATION")
        print("=" * 40)
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized")
        print(f"Address: {agent.address}")
        
        # Step 3: Debug network
        network_ok = debug_network_connection(agent)
        if not network_ok:
            print("\n❌ Network connectivity issues detected")
            return
        
        # Step 4: Debug integrations
        integrations_ok = debug_integrations(agent)
        if not integrations_ok:
            print("\n❌ Integration issues detected")
        
        # Step 5: Debug token contracts
        debug_token_contracts(agent)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 DEBUGGING SUMMARY")
        print("=" * 50)
        
        if integrations_ok and network_ok:
            print("✅ System appears ready for swap operations")
            print("🚀 Try running: python enhanced_swap_DAI_for_wbtc.py")
        else:
            print("❌ Critical issues found - swap will likely fail")
            print("💡 Fix the issues above before attempting swaps")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
