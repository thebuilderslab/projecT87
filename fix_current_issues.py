
#!/usr/bin/env python3
"""
COMPREHENSIVE FIX SCRIPT
Addresses current RPC connectivity and balance issues
"""

import os
import time
from web3 import Web3
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_rpc_endpoints():
    """Test all RPC endpoints and find working ones"""
    print("🔍 TESTING RPC ENDPOINTS")
    print("=" * 40)
    
    mainnet_rpcs = [
        'https://arb1.arbitrium.io/rpc',
        'https://arbitrum-one.publicnode.com',
        'https://arbitrum.llama.fi',
        'https://rpc.ankr.com/arbitrum',
        'https://arbitrum-one.public.blastapi.io',
        'https://arbitrum.blockpi.network/v1/rpc/public'
    ]
    
    working_rpcs = []
    
    for rpc_url in mainnet_rpcs:
        try:
            print(f"🔄 Testing {rpc_url}")
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
            
            if w3.is_connected():
                chain_id = w3.eth.chain_id
                block_number = w3.eth.block_number
                
                if chain_id == 42161:  # Arbitrum Mainnet
                    print(f"✅ {rpc_url} - Chain: {chain_id}, Block: {block_number}")
                    working_rpcs.append(rpc_url)
                else:
                    print(f"❌ {rpc_url} - Wrong chain: {chain_id}")
            else:
                print(f"❌ {rpc_url} - Connection failed")
                
        except Exception as e:
            print(f"❌ {rpc_url} - Error: {e}")
    
    print(f"\n✅ Found {len(working_rpcs)} working RPC endpoints")
    return working_rpcs

def test_token_balance_retrieval(agent):
    """Test token balance retrieval with different methods - DAI COMPLIANCE ENFORCED"""
    print("\n🔍 TESTING TOKEN BALANCE RETRIEVAL")
    print("=" * 50)
    
    dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
    
    # Method 1: Direct Web3 call
    try:
        print("🔄 Method 1: Direct Web3 balance call")
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
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
        
        dai_contract = agent.w3.eth.contract(
            address=Web3.to_checksum_address(dai_address),
            abi=erc20_abi
        )
        
        balance_wei = dai_contract.functions.balanceOf(agent.address).call()
        decimals = dai_contract.functions.decimals().call()
        balance = balance_wei / (10 ** decimals)
        
        print(f"✅ Direct call successful: {balance:.6f} DAI")
        return True
        
    except Exception as e:
        print(f"❌ Direct call failed: {e}")
        
        # Method 2: Low-level call
        try:
            print("🔄 Method 2: Low-level eth_call")
            # balanceOf function signature
            function_sig = "0x70a08231"  # balanceOf(address)
            padded_address = agent.address[2:].zfill(64)
            data = function_sig + padded_address
            
            result = agent.w3.eth.call({
                'to': dai_address,
                'data': data
            })
            
            balance_wei = int(result.hex(), 16)
            balance = balance_wei / (10 ** 18)  # DAI has 18 decimals
            
            print(f"✅ Low-level call successful: {balance:.6f} DAI")
            return True
            
        except Exception as e2:
            print(f"❌ Low-level call failed: {e2}")
            return False

def fix_issues():
    """Main fix function"""
    print("🔧 COMPREHENSIVE ISSUE FIX")
    print("=" * 50)
    
    try:
        # Test RPC endpoints
        working_rpcs = test_rpc_endpoints()
        
        if not working_rpcs:
            print("❌ No working RPC endpoints found")
            return False
        
        # Initialize agent
        print("\n🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        # Test integrations
        print("\n🔧 Testing integrations...")
        success = agent.initialize_integrations()
        
        if success:
            print("✅ Integrations initialized successfully")
            
            # Test token balance retrieval
            balance_test = test_token_balance_retrieval(agent)
            
            if balance_test:
                print("\n🎉 ALL FIXES SUCCESSFUL!")
                print("✅ RPC connectivity restored")
                print("✅ Token balance retrieval working")
                return True
            else:
                print("\n⚠️ Balance retrieval still having issues")
                print("💡 This might be due to network connectivity or rate limiting")
                return False
        else:
            print("❌ Integration initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Fix process failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_issues()
    
    if success:
        print("\n🚀 Ready to proceed!")
        print("Run: python verify_readiness.py")
    else:
        print("\n💡 Some issues remain - may need manual intervention")
