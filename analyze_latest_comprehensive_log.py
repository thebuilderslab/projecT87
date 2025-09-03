
#!/usr/bin/env python3
"""
Latest Comprehensive Log Analyzer - Extract specific transaction sequence
"""

import re
import os
from datetime import datetime

def analyze_latest_comprehensive_log():
    """Analyze the latest comprehensive borrowing diagnostic log"""
    print("🔍 ANALYZING LATEST COMPREHENSIVE DIAGNOSTIC LOG")
    print("=" * 70)
    
    # The latest comprehensive log from your attached assets
    log_content = """
    🔍 COMPREHENSIVE BORROWING DIAGNOSTIC
============================================================
🤖 Initializing Arbitrum Agent...
🤖 Initializing Arbitrum Testnet Agent...
DEBUG: WALLET_PRIVATE_KEY loaded from environment: [REDACTED]
🔍 DEBUG: Starting RPC manager initialization...
🔍 DEBUG: Network mode: mainnet
DEBUG: ALCHEMY_RPC_URL loaded from environment: https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU
✅ RPC passed tests: https://arbitrum-one.public.blastapi.io (0.11s)
📊 RPC Test Results: 5/5 endpoints working
🌐 Operating on Arbitrum Mainnet
🚨 NETWORK_MODE from environment: 'mainnet'
🔗 Primary RPC: https://arbitrum-one.public.blastapi.io
🔄 Fallback RPCs: 4 available
🔑 Wallet Address: 0x5B823270e3719CDe8669e5e5326B455EaA8a350b
💰 AGENT INITIALIZED WITH WALLET: 0x5B823270e3719CDe8669e5e5326B455EaA8a350b
✅ Private key format validated and normalized
📋 Mainnet Token addresses verified:
   USDC: 0xAf88D065e77C8cF0EAEfF3e253e648A15CEe23dC
   WBTC: 0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f
   WETH: 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1
   DAI: 0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1
   Aave Pool: 0x794a61358D6845594F94dc1DB02A252b5b4814aD
✅ All DeFi integrations initialized successfully!
✅ Agent initialized successfully

🏥 DIAGNOSING HEALTH FACTOR VALIDATION...
✅ LIVE AAVE DATA RETRIEVED:
   Health Factor: 4.2627
   Collateral: $190.09
   Debt: $35.07
   Available Borrows: $105.12
   Data Source: LIVE_AAVE_CONTRACT
   Data Quality: ✅ VALIDATED
✅ Health Factor validation passed

⛽ DIAGNOSING GAS OPTIMIZATION...
   Gas Limit: 300,000
   Gas Price: 43,544,600 wei (0.044 gwei)
   Network Gas Price: 19,793,000 wei (0.020 gwei)
✅ Gas optimization diagnosis completed

💰 DIAGNOSING TOKEN BALANCES...
   ETH Balance: 0.001954 ETH
❌ Error getting supplied balance for 0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f: Could not transact with/call contract function, is contract deployed correctly and chain synced?
   WBTC Supplied: 0.000000
❌ Error getting supplied balance for 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1: Could not transact with/call contract function, is contract deployed correctly and chain synced?
   WETH Supplied: 0.000000
✅ Supplied 0.00000000 of token 0xAf88D065e77C8cF0EAEfF3e253e648A15CEe23dC (aToken: 0x724dc807b04555b71ed48a6896b6F41593b8C637)
   USDC Supplied: 0.000000
   Estimated Total Supplied Value: $0.00

🏦 DIAGNOSING AAVE PROTOCOL STATE...
✅ LIVE AAVE DATA RETRIEVED:
   Health Factor: 4.2627
   Collateral: $190.09
   Debt: $35.07
   Available Borrows: $105.12
   Data Source: LIVE_AAVE_CONTRACT
   Data Quality: ✅ VALIDATED

🧪 TESTING SMALL BORROW OPERATION...
   Testing borrow of $1.00 USDC...
   Enhanced Borrow Manager: ✅ Available
❌ Borrow simulation failed: execution reverted
"""

    # Extract key data points
    print("📊 KEY DATA POINTS FROM LATEST LOG:")
    print("=" * 40)
    
    # Extract wallet address
    wallet_match = re.search(r'Wallet Address: (0x[a-fA-F0-9]{40})', log_content)
    if wallet_match:
        wallet_address = wallet_match.group(1)
        print(f"💳 Wallet: {wallet_address}")
        print(f"🔗 Arbiscan: https://arbiscan.io/address/{wallet_address}")
    
    # Extract health factor
    hf_match = re.search(r'Health Factor: ([\d.]+)', log_content)
    if hf_match:
        health_factor = hf_match.group(1)
        print(f"🏥 Health Factor: {health_factor}")
    
    # Extract collateral and debt
    collateral_match = re.search(r'Collateral: \$(\d+\.\d+)', log_content)
    debt_match = re.search(r'Debt: \$(\d+\.\d+)', log_content)
    available_match = re.search(r'Available Borrows: \$(\d+\.\d+)', log_content)
    
    if collateral_match:
        print(f"💰 Collateral: ${collateral_match.group(1)}")
    if debt_match:
        print(f"💸 Debt: ${debt_match.group(1)}")
    if available_match:
        print(f"📈 Available Borrows: ${available_match.group(1)}")
    
    # Extract transaction hashes
    tx_hashes = re.findall(r'0x[a-fA-F0-9]{64}', log_content)
    
    print(f"\n🔗 TRANSACTION HASHES FOUND: {len(tx_hashes)}")
    for i, tx_hash in enumerate(tx_hashes, 1):
        print(f"{i}. {tx_hash}")
        print(f"   🔗 https://arbiscan.io/tx/{tx_hash}")
    
    # Look for specific error patterns
    print(f"\n❌ ERROR PATTERNS IDENTIFIED:")
    
    if "execution reverted" in log_content:
        print("• Borrow simulation failed: execution reverted")
        print("  💡 This suggests insufficient collateral or contract issues")
    
    if "Could not transact with/call contract function" in log_content:
        print("• aToken contract call failures")
        print("  💡 This suggests aToken address issues or network problems")
    
    # Generate specific investigation guide
    print(f"\n🎯 SPECIFIC INVESTIGATION ACTIONS:")
    print("1. Check wallet transaction history on Arbiscan")
    print("2. Verify recent interactions with these contracts:")
    print("   - Aave Pool: 0x794a61358D6845594F94dc1DB02A252b5b4814aD")
    print("   - Uniswap Router: 0xE592427A0AEce92De3Edee1F18E0157C05861564")
    print("3. Look for failed 'supply' transactions after successful swaps")
    print("4. Check if WBTC/WETH tokens are stuck in wallet")

def get_most_recent_diagnostic_files():
    """Get the most recent diagnostic files for analysis"""
    print(f"\n📄 RECENT DIAGNOSTIC FILES:")
    print("=" * 30)
    
    # Get recent borrow diagnostic files
    borrow_files = sorted(glob.glob("borrow_diagnostic_*.json"))
    failure_files = sorted(glob.glob("borrow_failure_*.json"))
    
    print(f"📊 Recent borrow diagnostics ({len(borrow_files)} files):")
    for file in borrow_files[-5:]:  # Last 5
        print(f"   • {file}")
    
    print(f"📊 Recent borrow failures ({len(failure_files)} files):")
    for file in failure_files[-5:]:  # Last 5
        print(f"   • {file}")
    
    # Show the content of the most recent files
    if borrow_files:
        latest_diagnostic = borrow_files[-1]
        print(f"\n📋 Latest Diagnostic: {latest_diagnostic}")
        try:
            with open(latest_diagnostic, 'r') as f:
                data = json.load(f)
            
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"   Network: {data.get('network_mode', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Issues: {len(data.get('issues_found', []))}")
            
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

if __name__ == "__main__":
    print("🚀 Starting Raw Log Analysis...")
    
    # Extract and analyze the comprehensive log
    log_file = extract_raw_comprehensive_log()
    
    # Get recent diagnostic files
    get_most_recent_diagnostic_files()
    
    print(f"\n✅ Raw log analysis complete!")
    print(f"📄 Use the generated files and Arbiscan links for detailed investigation")
