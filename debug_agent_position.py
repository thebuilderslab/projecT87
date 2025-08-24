
#!/usr/bin/env python3
"""
Debug Agent Position Detection
Identifies why the autonomous agent isn't detecting real Aave position changes
"""

import os
import time
from web3 import Web3
from eth_account import Account

def debug_agent_position():
    """Debug why agent isn't detecting position properly"""
    print("🔍 DEBUGGING AGENT POSITION DETECTION")
    print("=" * 60)
    
    # Initialize connection
    private_key = os.getenv('PRIVATE_KEY')
    rpc_url = "https://arbitrum-mainnet.infura.io/v3/5d36f0061cbc4dda980f938ff891c141"
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = Account.from_key(private_key)
    address = account.address
    
    print(f"📍 Wallet: {address}")
    print(f"🌐 Chain ID: {w3.eth.chain_id}")
    print(f"💰 ETH Balance: {w3.from_wei(w3.eth.get_balance(address), 'ether'):.6f} ETH")
    
    # Aave V3 Pool on Arbitrum
    aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    
    # Standard Aave Pool ABI for getUserAccountData
    pool_abi = [{
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {"name": "totalCollateralBase", "type": "uint256"},
            {"name": "totalDebtBase", "type": "uint256"},
            {"name": "availableBorrowsBase", "type": "uint256"},
            {"name": "currentLiquidationThreshold", "type": "uint256"},
            {"name": "ltv", "type": "uint256"},
            {"name": "healthFactor", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }]
    
    try:
        print(f"\n🏦 TESTING AAVE POSITION DETECTION:")
        
        # Method 1: Direct Aave Pool Query
        pool_contract = w3.eth.contract(address=aave_pool, abi=pool_abi)
        account_data = pool_contract.functions.getUserAccountData(address).call()
        
        total_collateral_usd = account_data[0] / (10**8)  # Aave uses 8 decimals for USD
        total_debt_usd = account_data[1] / (10**8)
        available_borrows_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"   ✅ Direct Aave Query Results:")
        print(f"      Total Collateral: ${total_collateral_usd:,.2f}")
        print(f"      Total Debt: ${total_debt_usd:,.2f}")
        print(f"      Available Borrows: ${available_borrows_usd:,.2f}")
        print(f"      Health Factor: {health_factor:.4f}")
        
        # Method 2: Check Individual aToken Balances
        print(f"\n🔍 TESTING INDIVIDUAL ATOKEN BALANCES:")
        
        # aToken addresses on Arbitrum Mainnet
        atoken_addresses = {
            "aWBTC": "0x6533afac2E7BCCB20dca161449A13A2D2d5B739A",
            "aWETH": "0xe50fA9b4c56454E2edF6BFf7c81b50c5F05aBE61", 
            "aUSDC": "0x724dc807b04555b71ed48a6896b6F41593b8C637"
        }
        
        atoken_abi = [{
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        total_detected = 0
        for token_name, token_address in atoken_addresses.items():
            try:
                token_contract = w3.eth.contract(address=token_address, abi=atoken_abi)
                balance = token_contract.functions.balanceOf(address).call()
                
                # Convert to readable format
                if token_name == "aUSDC":
                    decimals = 6
                elif token_name == "aWBTC":
                    decimals = 8
                else:
                    decimals = 18
                    
                readable_balance = balance / (10**decimals)
                print(f"      {token_name}: {readable_balance:.8f}")
                
                if readable_balance > 0:
                    total_detected += 1
                    
            except Exception as e:
                print(f"      {token_name}: ❌ Error - {e}")
        
        print(f"\n📊 POSITION ANALYSIS:")
        print(f"   Aave shows collateral: ${total_collateral_usd:,.2f}")
        print(f"   Individual aTokens detected: {total_detected}")
        print(f"   Agent baseline: $175.17")
        print(f"   Growth needed for trigger: $12.00")
        print(f"   Current growth: ${total_collateral_usd - 175.17:,.2f}")
        
        if total_collateral_usd >= (175.17 + 12):
            print(f"   🚀 TRIGGER SHOULD ACTIVATE!")
        else:
            print(f"   ⏸️ Trigger threshold not met")
            
        # Method 3: Test Dashboard Data Function
        print(f"\n🔍 TESTING DASHBOARD DATA FUNCTION:")
        try:
            from web_dashboard import get_live_agent_data
            dashboard_data = get_live_agent_data()
            
            if dashboard_data:
                print(f"   ✅ Dashboard data retrieved:")
                print(f"      Source: {dashboard_data.get('data_source', 'unknown')}")
                print(f"      Health Factor: {dashboard_data.get('health_factor', 0):.4f}")
                print(f"      Collateral: ${dashboard_data.get('total_collateral_usdc', 0):,.2f}")
                print(f"      Debt: ${dashboard_data.get('total_debt_usdc', 0):,.2f}")
            else:
                print(f"   ❌ No dashboard data retrieved")
                
        except Exception as e:
            print(f"   ❌ Dashboard data error: {e}")
            
        # Method 4: Compare with Baseline File
        print(f"\n📋 CHECKING BASELINE STORAGE:")
        baseline_file = "agent_baseline.json"
        if os.path.exists(baseline_file):
            import json
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
                print(f"   Stored baseline: ${baseline_data.get('last_collateral_value_usd', 0):,.2f}")
        else:
            print(f"   No baseline file found")
            
        # Recommendations
        print(f"\n💡 DEBUGGING RECOMMENDATIONS:")
        
        if total_collateral_usd > 180:
            print(f"   1. ✅ Position detected correctly: ${total_collateral_usd:,.2f}")
            print(f"   2. 🔧 Agent trigger logic needs adjustment")
            print(f"   3. 🎯 Current position should trigger autonomous sequence")
        elif total_detected == 0:
            print(f"   1. ❌ aToken balance detection failing")
            print(f"   2. 🔧 RPC endpoint may have limitations")
            print(f"   3. 🎯 Try alternative data source")
        else:
            print(f"   1. ⚠️ Partial detection - some tokens visible")
            print(f"   2. 🔧 Mixed data source reliability")
            print(f"   3. 🎯 Use direct Aave pool data as primary source")
            
        return {
            'aave_collateral': total_collateral_usd,
            'aave_debt': total_debt_usd,
            'health_factor': health_factor,
            'atoken_detected': total_detected,
            'trigger_ready': total_collateral_usd >= (175.17 + 12)
        }
        
    except Exception as e:
        print(f"❌ Critical error in debugging: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_agent_position()
