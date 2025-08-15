
#!/usr/bin/env python3
"""
Fix Aave Contract Calls - Test the fixed ABI and RPC endpoints
"""

import os
from web3 import Web3
from eth_account import Account

def test_fixed_aave_calls():
    """Test the fixed Aave contract calls"""
    print("🔧 TESTING FIXED AAVE CONTRACT CALLS")
    print("=" * 50)
    
    # Initialize with working RPC
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("❌ No PRIVATE_KEY found in environment")
        return
    
    # Use working RPC endpoint
    rpc_url = "https://arbitrum-one.public.blastapi.io"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"❌ Failed to connect to {rpc_url}")
        return
    
    print(f"✅ Connected to {rpc_url}")
    print(f"🌐 Chain ID: {w3.eth.chain_id}")
    
    # Initialize account
    account = Account.from_key(private_key)
    print(f"🔑 Wallet: {account.address}")
    
    # Test Aave Pool contract with complete ABI
    aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    
    # Complete ABI including getUserAccountData
    complete_abi = [{
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
        # Create contract instance
        pool_contract = w3.eth.contract(
            address=Web3.to_checksum_address(aave_pool_address),
            abi=complete_abi
        )
        
        print(f"✅ Contract instance created successfully")
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ Contract call failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fixed_aave_calls()
    if success:
        print("\n✅ ALL FIXES SUCCESSFUL - Contract calls working!")
    else:
        print("\n❌ Contract call issues still present")
