#!/usr/bin/env python3
"""
Check WETH Credit Delegation status for the ParaSwap Debt Swap Adapter V3.
Verifies that the adapter has borrowAllowance to borrow WETH on behalf of the user.
"""

import os
from web3 import Web3

WETH_VARIABLE_DEBT_TOKEN = "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351"
DEBT_SWAP_ADAPTER_V3 = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"

DEBT_TOKEN_ABI = [
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
    print("WETH CREDIT DELEGATION CHECK")
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
    print(f"\n📋 Checking delegation:")
    print(f"   User Wallet:           {account.address}")
    print(f"   WETH Variable Debt:    {WETH_VARIABLE_DEBT_TOKEN}")
    print(f"   Debt Swap Adapter V3:  {DEBT_SWAP_ADAPTER_V3}")

    weth_debt = w3.eth.contract(
        address=Web3.to_checksum_address(WETH_VARIABLE_DEBT_TOKEN),
        abi=DEBT_TOKEN_ABI
    )

    allowance = weth_debt.functions.borrowAllowance(
        account.address,
        Web3.to_checksum_address(DEBT_SWAP_ADAPTER_V3)
    ).call()

    allowance_eth = allowance / 10**18
    print(f"\n🔍 borrowAllowance result: {allowance} wei ({allowance_eth:.6f} WETH)")

    if allowance > 0:
        print(f"\n✅ WETH Credit Delegation is ACTIVE.")
        print(f"   Adapter can borrow up to {allowance_eth:.4f} WETH on your behalf.")
        return True
    else:
        print(f"\n❌ WETH Credit Delegation MISSING. Must approve before debt swaps will work.")
        print(f"   Run: delegate_weth_credit.py (with correct adapter address)")
        return False

if __name__ == "__main__":
    result = main()
    print(f"\n{'='*70}")
    print(f"Result: {'PASS' if result else 'FAIL'}")
    print(f"{'='*70}")
