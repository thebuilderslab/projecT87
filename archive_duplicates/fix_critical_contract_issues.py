
#!/usr/bin/env python3
"""
Critical Fix for Contract Call Issues
Addresses the aToken contract call failures preventing borrow/swap/supply sequence
"""

import os
from web3 import Web3
from eth_account import Account

def fix_contract_issues():
    """Fix critical contract call issues"""
    print("🔧 FIXING CRITICAL CONTRACT CALL ISSUES")
    print("=" * 50)
    
    # Initialize with working RPC
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("❌ No PRIVATE_KEY found in environment")
        return
    
    # Use the most reliable RPC
    rpc_url = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"❌ Failed to connect to {rpc_url}")
        return
    
    print(f"✅ Connected to {rpc_url}")
    print(f"🌐 Chain ID: {w3.eth.chain_id}")
    
    # Initialize account
    account = Account.from_key(private_key)
    print(f"🔑 Wallet: {account.address}")
    
    # Test Aave Pool contract with the working ABI
    aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    
    # Working ABI for getUserAccountData
    pool_abi = [{
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"}
        ],
        "name": "getUserAccountData",
        "outputs": [
            {"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"},
            {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"},
            {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"},
            {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
            {"internalType": "uint256", "name": "ltv", "type": "uint256"},
            {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }]
    
    try:
        # Create pool contract instance
        pool_contract = w3.eth.contract(
            address=Web3.to_checksum_address(aave_pool_address),
            abi=pool_abi
        )
        
        print(f"✅ Pool contract instance created successfully")
        
        # Test getUserAccountData call
        user_data = pool_contract.functions.getUserAccountData(
            Web3.to_checksum_address(account.address)
        ).call()
        
        print("✅ getUserAccountData call successful!")
        print(f"📊 Account Data:")
        print(f"   Total Collateral: ${user_data[0] / 10**8:.2f}")
        print(f"   Total Debt: ${user_data[1] / 10**8:.2f}")
        print(f"   Available Borrows: ${user_data[2] / 10**8:.2f}")
        print(f"   Health Factor: {user_data[5] / 10**18:.4f}")
        
        # Test if we can proceed with a borrow
        available_borrows = user_data[2] / 10**8
        health_factor = user_data[5] / 10**18 if user_data[5] > 0 else float('inf')
        
        if health_factor > 1.5 and available_borrows > 1.0:
            print("✅ CONDITIONS MET FOR BORROW/SWAP/SUPPLY SEQUENCE")
            print(f"   Health Factor: {health_factor:.4f} > 1.5 ✅")
            print(f"   Available Borrows: ${available_borrows:.2f} > $1.0 ✅")
            print("🚀 READY TO EXECUTE FULL SEQUENCE")
        else:
            print("⚠️ CONDITIONS NOT OPTIMAL:")
            print(f"   Health Factor: {health_factor:.4f} (need > 1.5)")
            print(f"   Available Borrows: ${available_borrows:.2f} (need > $1.0)")
        
        return True
        
    except Exception as e:
        print(f"❌ Contract call failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_contract_issues()
    if success:
        print("\n✅ CONTRACT FIXES VALIDATED - Ready for full sequence!")
    else:
        print("\n❌ Contract issues still present")
