#!/usr/bin/env python3
"""
Approve WETH credit delegation for Debt Switch Adapter
This allows the adapter to borrow WETH on our behalf during debt swaps
"""

import os
from web3 import Web3

def main():
    print("=" * 80)
    print("WETH CREDIT DELEGATION APPROVAL")
    print("=" * 80)
    
    # Get credentials
    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        print("❌ PRIVATE_KEY not set")
        return False
    
    # Connect to Arbitrum
    rpc = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return False
    
    print("✅ Connected to Arbitrum mainnet")
    print(f"   Block: {w3.eth.block_number:,}")
    
    # Setup account
    account = w3.eth.account.from_key(private_key)
    
    # Contract addresses
    WETH_VARIABLE_DEBT = "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351"
    DEBT_SWITCH_ADAPTER = "0xb0D8cF9560EF31B8Fe6D9727708D19b31F7C90Ec"
    
    print(f"\n📋 Details:")
    print(f"   Wallet: {account.address}")
    print(f"   WETH Variable Debt Token: {WETH_VARIABLE_DEBT}")
    print(f"   Debt Switch Adapter: {DEBT_SWITCH_ADAPTER}")
    
    # Contract ABI
    debt_token_abi = [
        {
            "inputs": [
                {"name": "delegatee", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "approveDelegation",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "fromUser", "type": "address"},
                {"name": "toUser", "type": "address"}
            ],
            "name": "borrowAllowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Initialize contract
    weth_debt = w3.eth.contract(
        address=Web3.to_checksum_address(WETH_VARIABLE_DEBT),
        abi=debt_token_abi
    )
    
    # Check current allowance
    print("\n🔍 Checking current credit delegation...")
    current_allowance = weth_debt.functions.borrowAllowance(
        account.address,
        Web3.to_checksum_address(DEBT_SWITCH_ADAPTER)
    ).call()
    
    current_allowance_eth = current_allowance / 1e18
    print(f"   Current allowance: {current_allowance_eth:.6f} WETH")
    
    if current_allowance_eth >= 10:
        print(f"\n✅ Credit delegation already sufficient!")
        print(f"   You have {current_allowance_eth:.2f} WETH delegated")
        return True
    
    # Approve delegation
    delegation_amount = 100 * 10**18  # 100 WETH
    
    print(f"\n💱 Approving credit delegation...")
    print(f"   Amount: 100 WETH")
    print(f"   This allows Debt Switch Adapter to borrow up to 100 WETH on your behalf")
    
    # Build transaction
    base_fee = w3.eth.gas_price
    max_fee = int(base_fee * 2)  # 2x base fee to ensure it goes through
    priority_fee = w3.to_wei('0.01', 'gwei')
    
    tx = weth_debt.functions.approveDelegation(
        Web3.to_checksum_address(DEBT_SWITCH_ADAPTER),
        delegation_amount
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': priority_fee,
        'chainId': 42161
    })
    
    print(f"\n📝 Transaction details:")
    print(f"   Gas limit: {tx['gas']:,}")
    print(f"   Max fee: {w3.from_wei(tx['maxFeePerGas'], 'gwei'):.4f} Gwei")
    
    # Sign and send
    print(f"\n🔐 Signing transaction...")
    signed_tx = account.sign_transaction(tx)
    
    print(f"📡 Broadcasting...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash_hex = tx_hash.hex()
    
    print(f"\n✅ Transaction sent!")
    print(f"   TX: {tx_hash_hex}")
    print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
    
    # Wait for confirmation
    print(f"\n⏳ Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print(f"\n🎉 SUCCESS!")
        print(f"   Block: {receipt['blockNumber']:,}")
        print(f"   Gas used: {receipt['gasUsed']:,}")
        
        # Verify new allowance
        new_allowance = weth_debt.functions.borrowAllowance(
            account.address,
            Web3.to_checksum_address(DEBT_SWITCH_ADAPTER)
        ).call()
        
        new_allowance_eth = new_allowance / 1e18
        print(f"\n✅ New credit delegation:")
        print(f"   Allowance: {new_allowance_eth:.2f} WETH")
        print(f"   Previous: {current_allowance_eth:.2f} WETH")
        print(f"   Change: +{new_allowance_eth - current_allowance_eth:.2f} WETH")
        
        print(f"\n🎯 You can now execute DAI → WETH debt swaps!")
        return True
    else:
        print(f"\n❌ Transaction FAILED")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ WETH CREDIT DELEGATION: COMPLETE")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ WETH CREDIT DELEGATION: FAILED")
        print("=" * 80)
