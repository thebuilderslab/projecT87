#!/usr/bin/env python3
"""
Test script for enhanced forensic analyzer components
"""

import os
import sys
from datetime import datetime

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    try:
        from web3 import Web3
        import requests
        import json
        print("✅ Core imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_rpc_connection():
    """Test basic RPC connection"""
    print("🔗 Testing RPC connection...")
    try:
        from web3 import Web3
        
        # Test primary RPC
        alchemy_url = os.getenv('ALCHEMY_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        w3 = Web3(Web3.HTTPProvider(alchemy_url))
        
        if w3.is_connected():
            block_number = w3.eth.block_number
            print(f"✅ Connected to Arbitrum - Block: {block_number}")
            return True, w3
        else:
            print("❌ Failed to connect to primary RPC")
            return False, None
            
    except Exception as e:
        print(f"❌ RPC connection failed: {e}")
        return False, None

def test_transaction_fetch(w3, tx_hash):
    """Test basic transaction fetching"""
    print(f"📥 Testing transaction fetch for {tx_hash[:20]}...")
    try:
        tx_data = w3.eth.get_transaction(tx_hash)
        tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        print(f"✅ Transaction fetched:")
        print(f"   Block: {tx_data['blockNumber']}")
        print(f"   From: {tx_data['from']}")
        print(f"   To: {tx_data['to']}")
        print(f"   Status: {'SUCCESS' if tx_receipt['status'] == 1 else 'FAILED'}")
        print(f"   Logs: {len(tx_receipt['logs'])}")
        
        return True, tx_data, tx_receipt
        
    except Exception as e:
        print(f"❌ Transaction fetch failed: {e}")
        return False, None, None

def test_log_decoding(logs):
    """Test basic log decoding"""
    print(f"🔍 Testing log decoding for {len(logs)} logs...")
    
    # Known event signatures
    event_sigs = {
        '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef': 'Transfer',
        '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925': 'Approval'
    }
    
    decoded_count = 0
    event_counts = {}
    
    for log in logs:
        if log['topics']:
            topic0 = log['topics'][0].hex()
            if topic0 in event_sigs:
                event_name = event_sigs[topic0]
                event_counts[event_name] = event_counts.get(event_name, 0) + 1
                decoded_count += 1
    
    print(f"✅ Decoded {decoded_count}/{len(logs)} logs")
    for event, count in event_counts.items():
        print(f"   {event}: {count}")
    
    return decoded_count > 0

def main():
    """Main test function"""
    print(f"🚀 TESTING ENHANCED FORENSIC INFRASTRUCTURE")
    print(f"⏰ {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test transaction hashes
    test_transactions = [
        '0x5f5d8e9b2ddd18cb3ee46a1e1f27d84d10725d61fa965ab272786ceac47f8996',
        '0x3ab14c6aeeae1da04c1b7530067d4980a46d9f6ec807592e020218371fffd33c'
    ]
    
    # Step 1: Test imports
    if not test_imports():
        print("❌ Import test failed - stopping")
        return False
    
    # Step 2: Test RPC connection
    connected, w3 = test_rpc_connection()
    if not connected:
        print("❌ RPC connection failed - stopping")
        return False
    
    # Step 3: Test transaction fetching
    success_count = 0
    for i, tx_hash in enumerate(test_transactions, 1):
        print(f"\n🎯 TESTING TRANSACTION {i}/{len(test_transactions)}")
        
        success, tx_data, tx_receipt = test_transaction_fetch(w3, tx_hash)
        if success:
            success_count += 1
            
            # Test log decoding
            if tx_receipt and tx_receipt['logs']:
                test_log_decoding(tx_receipt['logs'])
            else:
                print("   No logs to decode")
        else:
            print(f"   ❌ Failed to fetch transaction {i}")
    
    # Summary
    print(f"\n✅ TEST SUMMARY")
    print(f"   Imports: ✅")
    print(f"   RPC Connection: ✅")
    print(f"   Transaction Fetch: {success_count}/{len(test_transactions)}")
    print(f"   Basic Infrastructure: {'✅ Working' if success_count > 0 else '❌ Failed'}")
    
    return success_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)