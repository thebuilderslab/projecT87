#!/usr/bin/env python3
"""
Check WETH Credit Delegation for ParaSwap Debt Swap Adapter V3.
If allowance < 0.1 WETH, automatically approves 0.1 WETH delegation on-chain.
"""

import os
from web3 import Web3

WETH_VARIABLE_DEBT_TOKEN = "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351"
DEBT_SWAP_ADAPTER_V3 = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
REQUIRED_ALLOWANCE_WETH = 0.1
REQUIRED_ALLOWANCE_WEI = int(REQUIRED_ALLOWANCE_WETH * 10**18)

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
    },
    {
        "inputs": [
            {"name": "delegatee", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approveDelegation",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def main():
    print("=" * 70)
    print("WETH CREDIT DELEGATION — CHECK + AUTO-FIX")
    print("=" * 70)

    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        print("❌ PRIVATE_KEY not set in environment")
        return False

    rpc_url = os.environ.get("ALCHEMY_RPC_URL") or os.environ.get("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
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
    print(f"   Required Allowance:    {REQUIRED_ALLOWANCE_WETH} WETH")

    weth_debt = w3.eth.contract(
        address=Web3.to_checksum_address(WETH_VARIABLE_DEBT_TOKEN),
        abi=DEBT_TOKEN_ABI
    )

    allowance = weth_debt.functions.borrowAllowance(
        account.address,
        Web3.to_checksum_address(DEBT_SWAP_ADAPTER_V3)
    ).call()

    allowance_eth = allowance / 10**18
    print(f"\n🔍 Current allowance: {allowance} wei ({allowance_eth:.6f} WETH)")

    if allowance >= REQUIRED_ALLOWANCE_WEI:
        print(f"\n✅ WETH Credit Delegation is SUFFICIENT.")
        print(f"   Adapter can borrow up to {allowance_eth:.4f} WETH on your behalf.")
        return True

    print(f"\n⚠️ Allowance {allowance_eth:.6f} WETH < required {REQUIRED_ALLOWANCE_WETH} WETH")
    print(f"🔧 AUTO-FIX: Approving {REQUIRED_ALLOWANCE_WETH} WETH delegation now...")

    nonce = w3.eth.get_transaction_count(account.address)
    base_gas_price = w3.eth.gas_price

    tx = weth_debt.functions.approveDelegation(
        Web3.to_checksum_address(DEBT_SWAP_ADAPTER_V3),
        REQUIRED_ALLOWANCE_WEI
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': int(base_gas_price * 2.5),
        'chainId': 42161,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    raw_tx = getattr(signed_tx, 'raw_transaction', None) or getattr(signed_tx, 'rawTransaction', None)
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    print(f"   TX Hash: {tx_hash.hex()}")

    print("   Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

    if receipt['status'] == 1:
        print(f"   ✅ Approval confirmed in block {receipt['blockNumber']}")
    else:
        print(f"   ❌ Approval transaction REVERTED")
        return False

    new_allowance = weth_debt.functions.borrowAllowance(
        account.address,
        Web3.to_checksum_address(DEBT_SWAP_ADAPTER_V3)
    ).call()
    new_allowance_eth = new_allowance / 10**18
    print(f"\n🔍 Verified allowance: {new_allowance} wei ({new_allowance_eth:.6f} WETH)")

    if new_allowance >= REQUIRED_ALLOWANCE_WEI:
        print(f"\n✅ AUTO-FIX SUCCESS — Delegation now {new_allowance_eth:.4f} WETH")
        return True
    else:
        print(f"\n❌ AUTO-FIX FAILED — Allowance still {new_allowance_eth:.6f} WETH")
        return False

if __name__ == "__main__":
    result = main()
    print(f"\n{'='*70}")
    print(f"Result: {'PASS ✅' if result else 'FAIL ❌'}")
    print(f"{'='*70}")
