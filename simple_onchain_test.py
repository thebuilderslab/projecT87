#!/usr/bin/env python3
"""
SIMPLE ONCHAIN TRANSACTION TEST
Generate visible blockchain activity with basic transaction
"""

import os
from web3 import Web3

def send_simple_transaction():
    """Send a simple transaction to generate on-chain activity"""
    
    print("🚀 SENDING SIMPLE TRANSACTION FOR ONCHAIN ACTIVITY")
    print("=" * 60)
    
    # Setup
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("❌ PRIVATE_KEY not found")
        return False
    
    w3 = Web3(Web3.HTTPProvider("https://arbitrum-one.public.blastapi.io"))
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return False
    
    account = w3.eth.account.from_key(private_key)
    user_address = account.address
    
    print(f"✅ Connected to Arbitrum")
    print(f"   User: {user_address}")
    print(f"   Block: {w3.eth.block_number}")
    print(f"   Balance: {w3.eth.get_balance(user_address) / 1e18:.6f} ETH")
    
    try:
        # Simple self-send transaction with data
        print(f"\n⚡ SENDING SIMPLE SELF-TRANSACTION:")
        
        # Create transaction with custom data
        transaction = {
            'to': user_address,  # Self-send
            'value': 0,  # No value transfer
            'gas': 23000,  # Extra gas for data
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(user_address),
            'chainId': 42161,  # Arbitrum chain ID
            'data': '0x' + 'Hello DeFi Agent!'.encode().hex()  # Custom data
        }
        
        print(f"   Gas price: {transaction['gasPrice'] / 1e9:.2f} gwei")
        print(f"   Custom data: {transaction['data']}")
        
        # Sign and send
        signed_tx = account.sign_transaction(transaction)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"   📤 Transaction sent: {tx_hash.hex()}")
        print(f"   🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
        
        # Wait for confirmation
        print(f"   ⏳ Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        success = receipt['status'] == 1
        print(f"   {'✅ CONFIRMED!' if success else '❌ FAILED!'}")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   Gas used: {receipt['gasUsed']:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Transaction failed: {e}")
        return False

if __name__ == "__main__":
    success = send_simple_transaction()
    print(f"\n{'🎉 ONCHAIN ACTIVITY CREATED!' if success else '❌ NO ACTIVITY GENERATED'}")
    if success:
        print("You can now see this transaction on Arbiscan!")