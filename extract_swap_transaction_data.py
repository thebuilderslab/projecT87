
#!/usr/bin/env python3
"""
Transaction Hash Extractor - Find all swap and supply transaction hashes
"""

import os
import re
import json
import glob
from datetime import datetime

def extract_transaction_hashes_from_logs():
    """Extract all transaction hashes from log files and console output"""
    print("🔍 EXTRACTING TRANSACTION HASHES FROM ALL LOGS")
    print("=" * 60)
    
    transaction_data = {
        'borrow_transactions': [],
        'swap_transactions': [],
        'supply_transactions': [],
        'approval_transactions': [],
        'failed_operations': []
    }
    
    # Pattern to match Ethereum transaction hashes
    tx_hash_pattern = r'0x[a-fA-F0-9]{64}'
    
    # Search through all log files
    log_files = glob.glob("*.txt") + glob.glob("*.log") + glob.glob("attached_assets/*.txt")
    
    print(f"📄 Scanning {len(log_files)} log files for transaction hashes...")
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Find all transaction hashes
            tx_hashes = re.findall(tx_hash_pattern, content)
            
            if tx_hashes:
                print(f"\n📄 File: {log_file}")
                print(f"🔗 Found {len(tx_hashes)} transaction hashes")
                
                # Categorize transactions based on context
                for tx_hash in tx_hashes:
                    context = extract_transaction_context(content, tx_hash)
                    
                    tx_data = {
                        'hash': tx_hash,
                        'file': log_file,
                        'context': context,
                        'arbiscan_url': f"https://arbiscan.io/tx/{tx_hash}"
                    }
                    
                    if 'approval' in context.lower():
                        transaction_data['approval_transactions'].append(tx_data)
                        print(f"   📝 APPROVAL: {tx_hash}")
                    elif 'swap' in context.lower() or 'exactInputSingle' in context:
                        transaction_data['swap_transactions'].append(tx_data)
                        print(f"   🔄 SWAP: {tx_hash}")
                    elif 'borrow' in context.lower():
                        transaction_data['borrow_transactions'].append(tx_data)
                        print(f"   🏦 BORROW: {tx_hash}")
                    elif 'supply' in context.lower():
                        transaction_data['supply_transactions'].append(tx_data)
                        print(f"   📈 SUPPLY: {tx_hash}")
                    else:
                        print(f"   ❓ UNKNOWN: {tx_hash}")
                    
                    print(f"      🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash}")
                    print(f"      📝 Context: {context[:100]}...")
                        
        except Exception as e:
            print(f"❌ Error reading {log_file}: {e}")
            continue
    
    # Save extracted data
    output_file = f"extracted_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(transaction_data, f, indent=2)
    
    print(f"\n💾 Transaction data saved to: {output_file}")
    
    # Generate summary report
    generate_transaction_summary(transaction_data)
    
    return transaction_data

def extract_transaction_context(content, tx_hash):
    """Extract context around a transaction hash"""
    try:
        # Find the position of the transaction hash
        tx_position = content.find(tx_hash)
        if tx_position == -1:
            return "No context found"
        
        # Extract 200 characters before and after
        start = max(0, tx_position - 200)
        end = min(len(content), tx_position + len(tx_hash) + 200)
        
        context = content[start:end]
        
        # Clean up context
        context = re.sub(r'\n+', ' ', context)
        context = re.sub(r'\s+', ' ', context)
        
        return context.strip()
        
    except Exception as e:
        return f"Context extraction error: {e}"

def generate_transaction_summary(transaction_data):
    """Generate a comprehensive summary of all transactions"""
    print(f"\n📊 TRANSACTION SUMMARY REPORT")
    print("=" * 60)
    
    total_approvals = len(transaction_data['approval_transactions'])
    total_swaps = len(transaction_data['swap_transactions'])
    total_borrows = len(transaction_data['borrow_transactions'])
    total_supplies = len(transaction_data['supply_transactions'])
    
    print(f"📝 APPROVAL Transactions: {total_approvals}")
    print(f"🔄 SWAP Transactions: {total_swaps}")
    print(f"🏦 BORROW Transactions: {total_borrows}")
    print(f"📈 SUPPLY Transactions: {total_supplies}")
    
    print(f"\n🔍 CRITICAL ANALYSIS:")
    
    if total_swaps > 0 and total_supplies == 0:
        print(f"❌ ISSUE IDENTIFIED: Swaps executed but no supply transactions found")
        print(f"💡 This suggests the swap → supply sequence is breaking")
    elif total_swaps == total_supplies:
        print(f"✅ SEQUENCE OK: Equal number of swaps and supplies")
    elif total_supplies > total_swaps:
        print(f"⚠️ More supplies than swaps - unexpected pattern")
    
    # Show recent transactions
    print(f"\n🔗 RECENT SWAP TRANSACTIONS (Check these on Arbiscan):")
    for i, tx in enumerate(transaction_data['swap_transactions'][-5:], 1):
        print(f"{i}. {tx['hash']}")
        print(f"   🔗 https://arbiscan.io/tx/{tx['hash']}")
        print(f"   📄 Source: {tx['file']}")
        print()

def find_specific_borrow_swap_sequence():
    """Find a specific sequence where borrow → swap → supply was attempted"""
    print(f"\n🎯 SEARCHING FOR COMPLETE BORROW → SWAP → SUPPLY SEQUENCE")
    print("=" * 60)
    
    # Look for the most comprehensive diagnostic log
    comprehensive_files = [f for f in glob.glob("attached_assets/*.txt") if "COMPREHENSIVE" in f]
    
    for file in comprehensive_files:
        print(f"\n📄 Analyzing: {file}")
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for the complete sequence
            if all(keyword in content for keyword in ['borrowed', 'swap', 'DAI', 'WBTC']):
                print(f"✅ Found complete sequence in {file}")
                
                # Extract key transaction hashes
                tx_hashes = re.findall(r'0x[a-fA-F0-9]{64}', content)
                
                print(f"🔗 Transaction hashes found in this sequence:")
                for i, tx_hash in enumerate(tx_hashes, 1):
                    print(f"{i}. {tx_hash}")
                    print(f"   🔗 https://arbiscan.io/tx/{tx_hash}")
                
                # Save this specific sequence
                sequence_file = f"borrow_swap_sequence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(sequence_file, 'w') as f:
                    f.write(content)
                
                print(f"\n💾 Complete sequence saved to: {sequence_file}")
                return tx_hashes
                
        except Exception as e:
            print(f"❌ Error analyzing {file}: {e}")
    
    return []

def check_arbiscan_for_transactions():
    """Generate Arbiscan links for manual verification"""
    print(f"\n🔍 MANUAL VERIFICATION GUIDE")
    print("=" * 60)
    
    print(f"🌐 Wallet Address: 0x5B823270e3719CDe8669e5e5326B455EaA8a350b")
    print(f"🔗 Arbiscan Wallet: https://arbiscan.io/address/0x5B823270e3719CDe8669e5e5326B455EaA8a350b")
    
    print(f"\n📊 KEY CONTRACT ADDRESSES TO CHECK:")
    print(f"🏦 Aave Pool: https://arbiscan.io/address/0x794a61358D6845594F94dc1DB02A252b5b4814aD")
    print(f"🔄 Uniswap Router: https://arbiscan.io/address/0xE592427A0AEce92De3Edee1F18E0157C05861564")
    print(f"💰 DAI Token: https://arbiscan.io/address/0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
    print(f"₿ WBTC Token: https://arbiscan.io/address/0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f")
    print(f"⚡ WETH Token: https://arbiscan.io/address/0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
    
    print(f"\n🔍 WHAT TO LOOK FOR:")
    print(f"1. Recent 'borrow' transactions to Aave Pool")
    print(f"2. Subsequent 'exactInputSingle' transactions to Uniswap Router")
    print(f"3. Missing 'supply' transactions back to Aave Pool")
    print(f"4. Check if swapped tokens are sitting in wallet instead of being supplied")

if __name__ == "__main__":
    print("🚀 Starting Transaction Hash Extraction...")
    
    # Extract all transaction data
    transaction_data = extract_transaction_hashes_from_logs()
    
    # Find specific sequences
    sequence_hashes = find_specific_borrow_swap_sequence()
    
    # Provide manual verification guide
    check_arbiscan_for_transactions()
    
    print(f"\n✅ Transaction extraction complete!")
    print(f"📊 Check the generated files for complete analysis data")
