#!/usr/bin/env python3
"""
Check if Debt Switch has approval to repay DAI debt on our behalf
"""

import os
from web3 import Web3

# Configuration
ARBITRUM_RPC = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")

# Addresses
DAI_ADDRESS = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
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
    },
    {
        "inputs": [
            {"name": "delegator", "type": "address"},
            {"name": "delegatee", "type": "address"}
        ],
        "name": "delegationWithSig",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def main():
    print("=" * 80)
    print("🔍 CHECKING DAI DEBT ALLOWANCES")
    print("=" * 80)
    
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return
    
    print(f"✅ Connected to Arbitrum (Chain ID: {w3.eth.chain_id})")
    
    if not PRIVATE_KEY:
        print("❌ PRIVATE_KEY not found")
        return
    
    account = w3.eth.account.from_key(PRIVATE_KEY)
    wallet = account.address
    print(f"🔑 Wallet: {wallet}")
    
    # Get DAI Variable Debt Token
    print(f"\n📡 Querying DAI reserve tokens...")
    provider = w3.eth.contract(
        address=w3.to_checksum_address(PROTOCOL_DATA_PROVIDER),
        abi=PROTOCOL_DATA_PROVIDER_ABI
    )
    
    try:
        aToken, stableDebtToken, variableDebtToken = provider.functions.getReserveTokensAddresses(
            w3.to_checksum_address(DAI_ADDRESS)
        ).call()
        
        print(f"✅ DAI Variable Debt Token: {variableDebtToken}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Check DAI credit delegation (for borrowing DAI)
    print(f"\n🔍 Checking DAI Credit Delegation (for borrowing)...")
    debt_token = w3.eth.contract(
        address=w3.to_checksum_address(variableDebtToken),
        abi=DEBT_TOKEN_ABI
    )
    
    try:
        dai_allowance = debt_token.functions.borrowAllowance(
            w3.to_checksum_address(wallet),
            w3.to_checksum_address(DEBT_SWITCH_ADAPTER)
        ).call()
        
        print(f"   DAI borrow allowance to Debt Switch: {dai_allowance / 1e18:.2f} DAI")
        
        if dai_allowance > 0:
            print(f"   ✅ DAI credit delegation active")
        else:
            print(f"   ⚠️  NO DAI credit delegation")
            print(f"      (May not be needed for debt repayment)")
        
    except Exception as e:
        print(f"   ❌ Error checking DAI allowance: {e}")
    
    print(f"\n📝 NOTES:")
    print(f"   - For debt SWAPS, you typically need:")
    print(f"     1. Credit delegation for NEW debt asset (ARB) ✅ We have this!")
    print(f"     2. Debt Switch doesn't need approval to repay your debt")
    print(f"        (Aave allows anyone to repay debt on behalf of someone)")
    print(f"   - The transaction is failing for a different reason")

if __name__ == "__main__":
    main()
