#!/usr/bin/env python3
"""
Approve Credit Delegation and Execute Debt Swap
"""

import os
import sys
from web3 import Web3
import time

# Configuration
ARBITRUM_RPC = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")

# Contract addresses
DAI_VARIABLE_DEBT = "0x8619d80FB0141ba7F184CbF22fd724116D9f7ffC"  # DAI Variable Debt Token
DEBT_SWITCH_V3 = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
DELEGATION_AMOUNT = int(1000 * 1e18)  # 1000 DAI delegation

# Variable Debt Token ABI
DEBT_TOKEN_ABI = [
    {
        'inputs': [
            {'name': 'delegatee', 'type': 'address'},
            {'name': 'amount', 'type': 'uint256'}
        ],
        'name': 'approveDelegation',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function'
    }
]

def main():
    print("=" * 80)
    print("🔐 APPROVING CREDIT DELEGATION FOR DEBT SWAP")
    print("=" * 80)
    
    # Validate private key
    if not PRIVATE_KEY:
        print("❌ ERROR: PRIVATE_KEY not found")
        sys.exit(1)
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    if not w3.is_connected():
        print("❌ ERROR: Failed to connect to Arbitrum")
        sys.exit(1)
    
    print(f"✅ Connected to Arbitrum (Chain ID: {w3.eth.chain_id})")
    
    # Get wallet
    account = w3.eth.account.from_key(PRIVATE_KEY)
    wallet = account.address
    print(f"🔑 Wallet: {wallet}")
    
    # Create contract
    debt_token = w3.eth.contract(
        address=w3.to_checksum_address(DAI_VARIABLE_DEBT),
        abi=DEBT_TOKEN_ABI
    )
    
    print(f"\n📋 DELEGATION APPROVAL:")
    print(f"   Token: DAI Variable Debt Token")
    print(f"   Delegatee: Debt Switch V3")
    print(f"   Amount: {DELEGATION_AMOUNT / 1e18:.0f} DAI")
    
    # Build EIP-1559 transaction
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.to_wei(0.01, 'gwei')
    max_fee = int(base_fee * 1.5) + max_priority_fee
    
    tx = debt_token.functions.approveDelegation(
        w3.to_checksum_address(DEBT_SWITCH_V3),
        DELEGATION_AMOUNT
    ).build_transaction({
        'from': wallet,
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': w3.eth.get_transaction_count(wallet),
        'chainId': 42161
    })
    
    gas_cost_eth = w3.from_wei(tx['gas'] * max_fee, 'ether')
    print(f"\n⛽ GAS ESTIMATE:")
    print(f"   Gas Limit: {tx['gas']:,}")
    print(f"   Max Cost: {gas_cost_eth:.6f} ETH (~${float(gas_cost_eth) * 3800:.2f})")
    
    # Sign and send
    print(f"\n🚀 AUTO-EXECUTING DELEGATION APPROVAL...")
    print(f"📝 Signing transaction...")
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    
    print(f"📡 Broadcasting transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash_hex = tx_hash.hex()
    
    print(f"✅ Transaction broadcast!")
    print(f"   TX Hash: {tx_hash_hex}")
    print(f"   Explorer: https://arbiscan.io/tx/{tx_hash_hex}")
    
    print(f"\n⏳ Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print(f"✅ DELEGATION APPROVED SUCCESSFULLY!")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   Gas Used: {receipt['gasUsed']:,}")
        
        print(f"\n" + "=" * 80)
        print(f"🎉 READY FOR DEBT SWAP!")
        print(f"   You can now execute debt swaps up to 1000 DAI")
        print(f"=" * 80)
        
        # Now execute the debt swap
        print(f"\n⏳ Waiting 3 seconds before executing debt swap...")
        time.sleep(3)
        
        print(f"\n" + "=" * 80)
        print(f"🔄 EXECUTING $25 DEBT SWAP...")
        print(f"=" * 80)
        
        import subprocess
        result = subprocess.run(['python', 'execute_debt_swap_25.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            sys.exit(result.returncode)
        
    else:
        print(f"❌ DELEGATION APPROVAL FAILED")
        print(f"   Status: {receipt['status']}")
        print(f"   Check explorer: https://arbiscan.io/tx/{tx_hash_hex}")
        sys.exit(1)

if __name__ == "__main__":
    main()
