
#!/usr/bin/env python3
"""
Raw Comprehensive Log Extractor - Get the complete execution log
"""

import os
import glob
from datetime import datetime

def extract_raw_comprehensive_log():
    """Extract the most comprehensive raw log for analysis"""
    print("📄 EXTRACTING RAW COMPREHENSIVE LOG")
    print("=" * 60)
    
    # Find the most comprehensive diagnostic file
    comprehensive_files = sorted(glob.glob("attached_assets/Pasted--COMPREHENSIVE-BORROWING-DIAGNOSTIC--*.txt"))
    
    if not comprehensive_files:
        print("❌ No comprehensive diagnostic files found")
        return
    
    # Get the most recent comprehensive log
    latest_file = comprehensive_files[-1]
    print(f"📄 Using latest comprehensive log: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Save as a clean raw log file
        output_file = f"RAW_COMPREHENSIVE_LOG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(output_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("RAW COMPREHENSIVE EXECUTION LOG\n")
            f.write("=" * 80 + "\n")
            f.write(f"Extracted from: {latest_file}\n")
            f.write(f"Extraction time: {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            f.write(content)
        
        print(f"✅ Raw log extracted to: {output_file}")
        
        # Analyze the log for key indicators
        analyze_raw_log_content(content, output_file)
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error extracting raw log: {e}")
        return None

def analyze_raw_log_content(content, log_file):
    """Analyze raw log content for specific failure patterns"""
    print(f"\n🔍 ANALYZING RAW LOG CONTENT")
    print("=" * 40)
    
    # Extract transaction hashes
    import re
    tx_hashes = re.findall(r'0x[a-fA-F0-9]{64}', content)
    
    print(f"🔗 Transaction hashes found: {len(tx_hashes)}")
    
    # Look for specific patterns
    patterns = {
        'borrow_success': r'✅.*[Bb]orrow.*successful',
        'swap_success': r'✅.*[Ss]wap.*successful',
        'supply_success': r'✅.*[Ss]upply.*successful',
        'borrow_failure': r'❌.*[Bb]orrow.*failed',
        'swap_failure': r'❌.*[Ss]wap.*failed',
        'supply_failure': r'❌.*[Ss]upply.*failed',
        'execution_reverted': r'execution reverted',
        'insufficient_funds': r'insufficient funds',
        'gas_estimation_failed': r'Gas estimation.*failed'
    }
    
    analysis_results = {}
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        analysis_results[pattern_name] = len(matches)
        
        if matches:
            print(f"🔍 {pattern_name}: {len(matches)} occurrences")
            # Show first few matches for context
            for match in matches[:3]:
                print(f"    • {match}")
    
    # Generate specific Arbiscan links
    print(f"\n🔗 ARBISCAN VERIFICATION LINKS:")
    print("=" * 40)
    
    unique_hashes = list(set(tx_hashes))
    for i, tx_hash in enumerate(unique_hashes[-10:], 1):  # Show last 10
        print(f"{i}. https://arbiscan.io/tx/{tx_hash}")
    
    # Save analysis
    analysis_file = f"transaction_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(analysis_file, 'w') as f:
        json.dump({
            'log_file': log_file,
            'transaction_hashes': unique_hashes,
            'pattern_analysis': analysis_results,
            'arbiscan_links': [f"https://arbiscan.io/tx/{tx}" for tx in unique_hashes]
        }, f, indent=2)
    
    print(f"\n💾 Analysis saved to: {analysis_file}")

def get_wallet_transaction_history():
    """Get recent transactions from wallet for verification"""
    print(f"\n💰 WALLET TRANSACTION VERIFICATION")
    print("=" * 40)
    
    wallet_address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    
    print(f"🔗 Wallet Address: {wallet_address}")
    print(f"🌐 Arbiscan Wallet: https://arbiscan.io/address/{wallet_address}")
    print(f"📊 Direct wallet transaction history available on Arbiscan")
    
    # Key contract interactions to look for
    key_contracts = {
        'Aave Pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
        'Uniswap Router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
        'DAI Token': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
        'WBTC Token': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',
        'WETH Token': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
    }
    
    print(f"\n🎯 LOOK FOR INTERACTIONS WITH:")
    for name, address in key_contracts.items():
        print(f"   {name}: {address}")
        print(f"      🔗 https://arbiscan.io/address/{address}")

def main():
    """Main execution function"""
    print("🚀 COMPREHENSIVE TRANSACTION DATA EXTRACTION")
    print("=" * 60)
    
    # Step 1: Extract raw comprehensive log
    raw_log_file = extract_raw_comprehensive_log()
    
    # Step 2: Extract all transaction hashes
    transaction_data = extract_transaction_hashes_from_logs()
    
    # Step 3: Provide wallet verification guide
    get_wallet_transaction_history()
    
    print(f"\n✅ EXTRACTION COMPLETE")
    print("=" * 40)
    print(f"📄 Raw log file: {raw_log_file}")
    print(f"🔗 Transaction data: extracted_transactions_*.json")
    print(f"🌐 Verify all transactions on Arbiscan using the provided links")

if __name__ == "__main__":
    main()
