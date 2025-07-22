
#!/usr/bin/env python3
"""
Transaction Success vs Failure Analyzer
Compares conditions when transactions succeeded vs when they fail
"""

import json
import os
import glob
from datetime import datetime

def analyze_transaction_patterns():
    """Analyze patterns between successful and failing transactions"""
    print("🔍 TRANSACTION SUCCESS vs FAILURE ANALYZER")
    print("=" * 60)
    
    # Find all diagnostic files
    diagnostic_files = glob.glob("borrow_diagnostic_*.json") + glob.glob("borrow_failure_*.json")
    diagnostic_files.sort()
    
    successful_conditions = []
    failed_conditions = []
    
    print(f"📊 Found {len(diagnostic_files)} diagnostic files to analyze")
    
    for file in diagnostic_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                
            # Extract key conditions
            conditions = {
                'file': file,
                'timestamp': data.get('timestamp', 0),
                'health_factor': data.get('aave_status', {}).get('healthFactor', 0),
                'collateral_usd': data.get('aave_status', {}).get('totalCollateralUSD', 0),
                'available_borrows': data.get('aave_status', {}).get('availableBorrowsUSD', 0),
                'eth_balance': data.get('wallet_status', {}).get('eth_balance', 0),
                'error': data.get('error', ''),
                'success': not data.get('error', '') and data.get('borrow_recommendation', {}).get('safe_to_proceed', False)
            }
            
            if conditions['success']:
                successful_conditions.append(conditions)
            else:
                failed_conditions.append(conditions)
                
        except Exception as e:
            print(f"⚠️ Could not parse {file}: {e}")
    
    print(f"\n📈 Successful transactions: {len(successful_conditions)}")
    print(f"📉 Failed transactions: {len(failed_conditions)}")
    
    # Analyze successful conditions
    if successful_conditions:
        print("\n✅ CONDITIONS DURING SUCCESSFUL TRANSACTIONS:")
        for success in successful_conditions[-3:]:  # Last 3 successful
            print(f"   📅 {datetime.fromtimestamp(success['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   💰 Health Factor: {success['health_factor']:.4f}")
            print(f"   🏦 Collateral: ${success['collateral_usd']:.2f}")
            print(f"   💳 Available Borrows: ${success['available_borrows']:.2f}")
            print(f"   ⛽ ETH Balance: {success['eth_balance']:.6f}")
            print("   " + "-" * 40)
    
    # Analyze failed conditions
    if failed_conditions:
        print("\n❌ CONDITIONS DURING FAILED TRANSACTIONS:")
        for failure in failed_conditions[-3:]:  # Last 3 failures
            print(f"   📅 {datetime.fromtimestamp(failure['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   💰 Health Factor: {failure['health_factor']:.4f}")
            print(f"   🏦 Collateral: ${failure['collateral_usd']:.2f}")
            print(f"   💳 Available Borrows: ${failure['available_borrows']:.2f}")
            print(f"   ⛽ ETH Balance: {failure['eth_balance']:.6f}")
            print(f"   🚨 Error: {failure['error'][:100]}...")
            print("   " + "-" * 40)
    
    # Find patterns
    print("\n🔍 PATTERN ANALYSIS:")
    
    if successful_conditions and failed_conditions:
        # Compare averages
        success_avg_hf = sum(s['health_factor'] for s in successful_conditions) / len(successful_conditions)
        failed_avg_hf = sum(f['health_factor'] for f in failed_conditions) / len(failed_conditions)
        
        success_avg_collateral = sum(s['collateral_usd'] for s in successful_conditions) / len(successful_conditions)
        failed_avg_collateral = sum(f['collateral_usd'] for f in failed_conditions) / len(failed_conditions)
        
        print(f"📊 Average Health Factor - Success: {success_avg_hf:.4f} vs Failed: {failed_avg_hf:.4f}")
        print(f"📊 Average Collateral - Success: ${success_avg_collateral:.2f} vs Failed: ${failed_avg_collateral:.2f}")
        
        # Common error patterns
        error_patterns = {}
        for failure in failed_conditions:
            error_key = failure['error'][:50]  # First 50 chars of error
            error_patterns[error_key] = error_patterns.get(error_key, 0) + 1
        
        print("\n🚨 COMMON ERROR PATTERNS:")
        for error, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"   {count}x: {error}...")
    
    # Current system analysis
    print("\n🔬 CURRENT SYSTEM STATUS ANALYSIS:")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        current_data = agent.aave.get_user_account_data()
        print(f"   💰 Current Health Factor: {current_data.get('healthFactor', 0):.4f}")
        print(f"   🏦 Current Collateral: ${current_data.get('totalCollateralUSD', 0):.2f}")
        print(f"   💳 Current Available: ${current_data.get('availableBorrowsUSD', 0):.2f}")
        
        # Compare with historical success patterns
        if successful_conditions:
            avg_success_hf = sum(s['health_factor'] for s in successful_conditions) / len(successful_conditions)
            if current_data.get('healthFactor', 0) >= avg_success_hf:
                print("   ✅ Current HF matches successful transaction range")
            else:
                print("   ⚠️ Current HF below successful transaction average")
    
    except Exception as e:
        print(f"   ❌ Could not get current system status: {e}")
    
    return successful_conditions, failed_conditions

if __name__ == "__main__":
    analyze_transaction_patterns()
