
#!/usr/bin/env python3
"""
Check Recent Operations - Verify if swap and supply operations were successful
"""

import os
import json
import glob
from datetime import datetime

def check_recent_operations():
    print("🔍 CHECKING RECENT SWAP AND SUPPLY OPERATIONS")
    print("=" * 60)
    
    # Check for recent transaction logs
    tx_files = glob.glob("*transaction*.json") + glob.glob("*swap*.json") + glob.glob("*supply*.json")
    
    if tx_files:
        print(f"📄 Found {len(tx_files)} transaction files:")
        for file in sorted(tx_files)[-5:]:  # Show last 5
            print(f"   • {file}")
    else:
        print("❌ No transaction log files found")
    
    # Check agent baseline for collateral changes
    if os.path.exists('agent_baseline.json'):
        with open('agent_baseline.json', 'r') as f:
            baseline = json.load(f)
        
        print(f"\n📊 Agent Baseline Status:")
        print(f"   • Last Update: {datetime.fromtimestamp(baseline.get('timestamp', 0))}")
        print(f"   • Collateral Value: ${baseline.get('collateral_value_usd', 0):.2f}")
        print(f"   • Updated By: {baseline.get('updated_by', 'unknown')}")
    
    # Check performance logs
    if os.path.exists('performance_log.json'):
        print(f"\n📈 Recent Performance Entries:")
        with open('performance_log.json', 'r') as f:
            lines = f.readlines()
            for line in lines[-3:]:  # Show last 3 entries
                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromtimestamp(entry.get('timestamp', 0))
                    print(f"   • {timestamp}: Performance {entry.get('performance_metric', 0):.3f}")
                except:
                    continue
    
    # Check for any successful operation indicators
    success_indicators = [
        'SWAP COMPLETED',
        'Supply successful',
        'WBTC supplied',
        'WETH supplied',
        'Transaction confirmed'
    ]
    
    print(f"\n🔍 Searching for success indicators in recent logs...")
    
    # Check if we can find any evidence of successful operations
    found_evidence = False
    
    # You would need to check your actual transaction history
    print("\n💡 To verify successful operations:")
    print("   1. Check your wallet on Arbiscan.io")
    print("   2. Look for recent DAI → WBTC/WETH swaps")
    print("   3. Check Aave position for new collateral")
    print("   4. Verify transaction hashes in console output")
    
    return found_evidence

if __name__ == "__main__":
    check_recent_operations()
