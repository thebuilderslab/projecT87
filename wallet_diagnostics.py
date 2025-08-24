
#!/usr/bin/env python3
"""
Wallet Diagnostics Module
Comprehensive wallet and network connectivity testing
"""

import os
import sys
from web3 import Web3

def test_wallet_connectivity():
    """Test wallet connectivity and basic functionality"""
    print("🔍 WALLET CONNECTIVITY DIAGNOSTICS")
    print("=" * 50)
    
    try:
        # Test environment variables
        private_key = os.getenv('WALLET_PRIVATE_KEY')
        if not private_key:
            print("❌ WALLET_PRIVATE_KEY not found in environment")
            return False
        
        print("✅ WALLET_PRIVATE_KEY found in environment")
        
        # Test key format
        if private_key.startswith('0x'):
            hex_part = private_key[2:]
        else:
            hex_part = private_key
            
        if len(hex_part) != 64:
            print(f"❌ Invalid private key length: {len(hex_part)} (expected 64)")
            return False
            
        print("✅ Private key format validation passed")
        
        # Test RPC connectivity
        rpc_urls = [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.public.blastapi.io",
            "https://arbitrum-one.publicnode.com"
        ]
        
        working_rpcs = 0
        for rpc_url in rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                if w3.is_connected():
                    chain_id = w3.eth.chain_id
                    if chain_id == 42161:
                        print(f"✅ RPC working: {rpc_url}")
                        working_rpcs += 1
                    else:
                        print(f"❌ Wrong chain ID {chain_id}: {rpc_url}")
                else:
                    print(f"❌ Connection failed: {rpc_url}")
            except Exception as e:
                print(f"❌ RPC error {rpc_url}: {e}")
                
        if working_rpcs > 0:
            print(f"✅ {working_rpcs}/{len(rpc_urls)} RPC endpoints working")
            return True
        else:
            print("❌ No working RPC endpoints found")
            return False
            
    except Exception as e:
        print(f"❌ Wallet diagnostics failed: {e}")
        return False

if __name__ == "__main__":
    success = test_wallet_connectivity()
    sys.exit(0 if success else 1)
