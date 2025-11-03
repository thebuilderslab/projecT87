#!/usr/bin/env python3
"""
Verify ARB Credit Delegation to Debt Switch Adapter
Checks borrowAllowance on ARB Variable Debt Token
"""

import os
from web3 import Web3

# Configuration
ARBITRUM_RPC = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")

# Addresses
ARB_ADDRESS = "0x912CE59144191C1204E64559FE8253a0e49E6548"
DEBT_SWITCH_ADAPTER = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
PROTOCOL_DATA_PROVIDER = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"

# ABIs
PROTOCOL_DATA_PROVIDER_ABI = [
    {
        "inputs": [{"name": "asset", "type": "address"}],
        "name": "getReserveTokensAddresses",
        "outputs": [
            {"name": "aTokenAddress", "type": "address"},
            {"name": "stableDebtTokenAddress", "type": "address"},
            {"name": "variableDebtTokenAddress", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

DEBT_TOKEN_ABI = [
    {
        "inputs": [
            {"name": "fromUser", "type": "address"},
            {"name": "toUser", "type": "address"}
        ],
        "name": "borrowAllowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def main():
    print("=" * 80)
    print("🔍 VERIFYING ARB CREDIT DELEGATION")
    print("=" * 80)
    
    # Connect to Arbitrum
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return
    
    print(f"✅ Connected to Arbitrum (Chain ID: {w3.eth.chain_id})")
    
    # Get wallet address
    if not PRIVATE_KEY:
        print("❌ PRIVATE_KEY not found in environment")
        return
    
    account = w3.eth.account.from_key(PRIVATE_KEY)
    wallet = account.address
    print(f"🔑 Wallet: {wallet}")
    
    # Get ARB Variable Debt Token address
    print(f"\n📡 Querying Aave Protocol Data Provider...")
    provider = w3.eth.contract(
        address=w3.to_checksum_address(PROTOCOL_DATA_PROVIDER),
        abi=PROTOCOL_DATA_PROVIDER_ABI
    )
    
    try:
        aToken, stableDebtToken, variableDebtToken = provider.functions.getReserveTokensAddresses(
            w3.to_checksum_address(ARB_ADDRESS)
        ).call()
        
        print(f"✅ ARB Reserve Tokens:")
        print(f"   aToken: {aToken}")
        print(f"   Stable Debt Token: {stableDebtToken}")
        print(f"   Variable Debt Token: {variableDebtToken}")
        
    except Exception as e:
        print(f"❌ Error querying reserve tokens: {e}")
        return
    
    # Check credit delegation
    print(f"\n🔍 Checking ARB Credit Delegation...")
    debt_token = w3.eth.contract(
        address=w3.to_checksum_address(variableDebtToken),
        abi=DEBT_TOKEN_ABI
    )
    
    try:
        allowance = debt_token.functions.borrowAllowance(
            w3.to_checksum_address(wallet),
            w3.to_checksum_address(DEBT_SWITCH_ADAPTER)
        ).call()
        
        print(f"\n📊 CREDIT DELEGATION STATUS:")
        print(f"   Delegator: {wallet}")
        print(f"   Delegatee: {DEBT_SWITCH_ADAPTER}")
        print(f"   Allowance: {allowance}")
        
        if allowance > 0:
            # Check if it's max uint256
            max_uint256 = 2**256 - 1
            if allowance == max_uint256:
                print(f"   ✅ UNLIMITED delegation (max uint256)")
            else:
                print(f"   ✅ LIMITED delegation: {allowance / 1e18:.2f} ARB")
            
            print(f"\n✅ ARB CREDIT DELEGATION IS ACTIVE")
            print(f"   Debt Switch Adapter can borrow ARB on your behalf")
            return True
        else:
            print(f"\n❌ NO ARB CREDIT DELEGATION FOUND")
            print(f"   Debt swaps will fail until delegation is approved")
            return False
            
    except Exception as e:
        print(f"❌ Error checking credit delegation: {e}")
        return False

if __name__ == "__main__":
    main()
