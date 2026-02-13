#!/usr/bin/env python3
"""
Approve WETH Credit Delegation for ParaSwap Debt Swap Adapter V3.
Grants the adapter permission to borrow WETH on behalf of the user during debt swaps.
Uses the CORRECT adapter address: 0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4
"""

import os
import sys
from web3 import Web3

WETH_VARIABLE_DEBT_TOKEN = "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351"
DEBT_SWAP_ADAPTER_V3 = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"

APPROVAL_AMOUNT_WETH = 0.1
APPROVAL_AMOUNT_WEI = int(APPROVAL_AMOUNT_WETH * 10**18)

DEBT_TOKEN_ABI = [
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

def main():
    print("=" * 70)
    print("WETH CREDIT DELEGATION APPROVAL")
    print(f"Approving {APPROVAL_AMOUNT_WETH} WETH for Debt Swap Adapter V3")
    print("=" * 70)

    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        print("❌ PRIVATE_KEY not set in environment")
        return False

    rpc_url = os.environ.get("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return False

    print(f"✅ Connected to Arbitrum (block {w3.eth.block_number:,})")

    account = w3.eth.account.from_key(private_key)
    print(f"\n📋 Delegation Details:")
    print(f"   User Wallet:           {account.address}")
    print(f"   WETH Variable Debt:    {WETH_VARIABLE_DEBT_TOKEN}")
    print(f"   Debt Swap Adapter V3:  {DEBT_SWAP_ADAPTER_V3}")
    print(f"   Approval Amount:       {APPROVAL_AMOUNT_WETH} WETH ({APPROVAL_AMOUNT_WEI} wei)")

    weth_debt = w3.eth.contract(
        address=Web3.to_checksum_address(WETH_VARIABLE_DEBT_TOKEN),
        abi=DEBT_TOKEN_ABI
    )

    print("\n🔍 Current allowance BEFORE approval...")
    allowance_before = weth_debt.functions.borrowAllowance(
        account.address,
        Web3.to_checksum_address(DEBT_SWAP_ADAPTER_V3)
    ).call()
    print(f"   Current: {allowance_before} wei ({allowance_before / 10**18:.6f} WETH)")

    print(f"\n🚀 Sending approveDelegation transaction...")
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price

    tx = weth_debt.functions.approveDelegation(
        Web3.to_checksum_address(DEBT_SWAP_ADAPTER_V3),
        APPROVAL_AMOUNT_WEI
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': int(gas_price * 1.1),
        'chainId': 42161,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    raw_tx = getattr(signed_tx, 'raw_transaction', None) or getattr(signed_tx, 'rawTransaction', None)
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    print(f"   TX Hash: {tx_hash.hex()}")

    print("   Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

    if receipt['status'] == 1:
        print(f"   ✅ Transaction confirmed in block {receipt['blockNumber']}")
        gas_used = receipt['gasUsed']
        gas_cost_eth = gas_used * gas_price / 10**18
        print(f"   Gas used: {gas_used} ({gas_cost_eth:.6f} ETH)")
    else:
        print(f"   ❌ Transaction REVERTED")
        return False

    print("\n🔍 Verifying new allowance AFTER approval...")
    allowance_after = weth_debt.functions.borrowAllowance(
        account.address,
        Web3.to_checksum_address(DEBT_SWAP_ADAPTER_V3)
    ).call()
    print(f"   New allowance: {allowance_after} wei ({allowance_after / 10**18:.6f} WETH)")

    if allowance_after >= APPROVAL_AMOUNT_WEI:
        print(f"\n✅ WETH Credit Delegation APPROVED — {allowance_after / 10**18:.4f} WETH")
        print(f"   Adapter can now borrow up to {APPROVAL_AMOUNT_WETH} WETH for debt swaps")
        return True
    else:
        print(f"\n❌ Allowance verification failed — expected {APPROVAL_AMOUNT_WEI}, got {allowance_after}")
        return False

if __name__ == "__main__":
    result = main()
    print(f"\n{'='*70}")
    print(f"Result: {'PASS' if result else 'FAIL'}")
    print(f"{'='*70}")
    sys.exit(0 if result else 1)
