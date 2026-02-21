#!/usr/bin/env python3
"""
Deploy REAADelegationManager.sol to Arbitrum Mainnet.

Requirements:
  - DEPLOYER_PRIVATE_KEY in environment (wallet that pays gas and becomes contract owner)
  - BOT_PRIVATE_KEY in environment (derived address becomes botOperator)
  - ARBITRUM_RPC_URL in environment (or falls back to public RPC)
  - py-solc-x (solcx) and web3 installed

Outputs:
  - Prints new contract address
  - Saves ABI to dm_abi.json
"""

import os
import sys
import json
import time

from web3 import Web3
from eth_account import Account

import solcx

SOLC_VERSION = "0.8.20"

ARBITRUM_RPCS = [
    os.environ.get("ARBITRUM_RPC_URL", ""),
    os.environ.get("ALCHEMY_RPC_URL", ""),
    "https://arb1.arbitrum.io/rpc",
    "https://arbitrum-one.publicnode.com",
    "https://arbitrum-one.public.blastapi.io",
]

CHAIN_ID = 42161

def get_web3():
    for rpc in ARBITRUM_RPCS:
        rpc = rpc.strip()
        if not rpc:
            continue
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))
            if w3.is_connected() and w3.eth.chain_id == CHAIN_ID:
                print(f"  Connected to RPC: {rpc[:60]}...")
                return w3
        except Exception:
            continue
    return None


def compile_contract(sol_path: str):
    print(f"\n[2/5] Compiling {sol_path} with solc {SOLC_VERSION}...")

    installed = [str(v) for v in solcx.get_installed_solc_versions()]
    if SOLC_VERSION not in installed:
        print(f"  Installing solc {SOLC_VERSION}...")
        solcx.install_solc(SOLC_VERSION)
        print(f"  solc {SOLC_VERSION} installed.")

    solcx.set_solc_version(SOLC_VERSION)

    with open(sol_path, "r") as f:
        source = f.read()

    compiled = solcx.compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=SOLC_VERSION,
    )

    contract_key = None
    for key in compiled:
        if "REAADelegationManager" in key:
            contract_key = key
            break

    if not contract_key:
        print(f"  ERROR: REAADelegationManager not found in compiled output.")
        print(f"  Available contracts: {list(compiled.keys())}")
        sys.exit(1)

    abi = compiled[contract_key]["abi"]
    bytecode = compiled[contract_key]["bin"]
    print(f"  Compilation successful. ABI has {len(abi)} entries, bytecode is {len(bytecode)} chars.")
    return abi, bytecode


def deploy_contract(w3, abi, bytecode, deployer_key, bot_operator_address):
    print(f"\n[4/5] Deploying to Arbitrum Mainnet (chain {CHAIN_ID})...")
    deployer_account = Account.from_key(deployer_key)
    deployer_address = deployer_account.address
    print(f"  Deployer address: {deployer_address}")
    print(f"  Bot operator address: {bot_operator_address}")

    balance_wei = w3.eth.get_balance(deployer_address)
    balance_eth = balance_wei / 1e18
    print(f"  Deployer ETH balance: {balance_eth:.6f} ETH")

    if balance_eth < 0.0005:
        print(f"  ERROR: Insufficient ETH for deployment gas. Need at least 0.0005 ETH.")
        sys.exit(1)

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer_address)

    gas_price = w3.eth.gas_price
    print(f"  Current gas price: {gas_price / 1e9:.4f} Gwei")

    construct_txn = contract.constructor(bot_operator_address).build_transaction({
        "from": deployer_address,
        "nonce": nonce,
        "gasPrice": int(gas_price * 1.15),
        "chainId": CHAIN_ID,
    })

    estimated_gas = w3.eth.estimate_gas(construct_txn)
    construct_txn["gas"] = int(estimated_gas * 1.2)
    print(f"  Estimated gas: {estimated_gas}, using: {construct_txn['gas']}")

    estimated_cost = construct_txn["gas"] * construct_txn["gasPrice"] / 1e18
    print(f"  Estimated deployment cost: {estimated_cost:.6f} ETH")

    signed_txn = w3.eth.account.sign_transaction(construct_txn, deployer_key)
    raw = getattr(signed_txn, 'raw_transaction', None) or signed_txn.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    tx_hash_hex = tx_hash.hex()
    print(f"  Transaction sent: 0x{tx_hash_hex}")
    print(f"  Arbiscan: https://arbiscan.io/tx/0x{tx_hash_hex}")
    print(f"  Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt.status == 1:
        contract_address = receipt.contractAddress
        print(f"\n  ========================================")
        print(f"  DEPLOYMENT SUCCESSFUL!")
        print(f"  Contract Address: {contract_address}")
        print(f"  Block: {receipt.blockNumber}")
        print(f"  Gas Used: {receipt.gasUsed}")
        actual_cost = receipt.gasUsed * construct_txn["gasPrice"] / 1e18
        print(f"  Actual Cost: {actual_cost:.6f} ETH")
        print(f"  ========================================")
        return contract_address
    else:
        print(f"  ERROR: Transaction REVERTED!")
        print(f"  Receipt: {receipt}")
        sys.exit(1)


def verify_contract(w3, contract_address, abi, bot_operator_address, deployer_address):
    print(f"\n[5/5] Verifying deployed contract...")
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=abi)

    owner = contract.functions.owner().call()
    bot_op = contract.functions.botOperator().call()
    is_paused = contract.functions.paused().call()

    print(f"  Owner: {owner}")
    print(f"  Bot Operator: {bot_op}")
    print(f"  Paused: {is_paused}")

    assert owner.lower() == deployer_address.lower(), f"Owner mismatch: {owner} != {deployer_address}"
    assert bot_op.lower() == bot_operator_address.lower(), f"BotOperator mismatch: {bot_op} != {bot_operator_address}"
    assert not is_paused, "Contract is paused after deployment!"

    fn_names = [item["name"] for item in abi if item.get("type") == "function"]
    critical_fns = [
        "executeBorrowAndTransfer", "executeBorrow", "executeSupply",
        "executeRepay", "executeWithdraw", "approveDelegation",
        "revokeDelegation", "getDelegation",
    ]
    for fn in critical_fns:
        if fn in fn_names:
            print(f"  ✅ {fn} — present")
        else:
            print(f"  ❌ {fn} — MISSING!")

    print(f"\n  Contract verification PASSED.")


def main():
    print("=" * 60)
    print("  REAADelegationManager Deployment Script")
    print("  Target: Arbitrum Mainnet (Chain ID 42161)")
    print("=" * 60)

    deployer_key = os.environ.get("DEPLOYER_PRIVATE_KEY", "").strip()
    bot_key = os.environ.get("BOT_PRIVATE_KEY", "").strip()

    if not deployer_key:
        deployer_key = os.environ.get("PRIVATE_KEY", "").strip()
        if deployer_key:
            print("  Note: Using PRIVATE_KEY as deployer (DEPLOYER_PRIVATE_KEY not found)")

    if not deployer_key:
        print("ERROR: No DEPLOYER_PRIVATE_KEY or PRIVATE_KEY found in environment.")
        sys.exit(1)
    if not bot_key:
        print("ERROR: BOT_PRIVATE_KEY not found in environment.")
        sys.exit(1)

    if not deployer_key.startswith("0x"):
        deployer_key = "0x" + deployer_key
    if not bot_key.startswith("0x"):
        bot_key = "0x" + bot_key

    deployer_account = Account.from_key(deployer_key)
    bot_account = Account.from_key(bot_key)
    deployer_address = deployer_account.address
    bot_operator_address = bot_account.address

    print(f"\n[1/5] Connecting to Arbitrum Mainnet...")
    w3 = get_web3()
    if not w3:
        print("ERROR: Could not connect to any Arbitrum RPC.")
        sys.exit(1)

    sol_path = "contracts/REAADelegationManager.sol"
    if not os.path.exists(sol_path):
        print(f"ERROR: {sol_path} not found.")
        sys.exit(1)

    abi, bytecode = compile_contract(sol_path)

    abi_path = "dm_abi.json"
    with open(abi_path, "w") as f:
        json.dump(abi, f, indent=2)
    print(f"\n[3/5] ABI saved to {abi_path}")

    contract_address = deploy_contract(w3, abi, bytecode, deployer_key, bot_operator_address)

    verify_contract(w3, contract_address, abi, bot_operator_address, deployer_address)

    print("\n" + "=" * 60)
    print("  DEPLOYMENT COMPLETE")
    print(f"  New Contract Address: {contract_address}")
    print("=" * 60)
    print(f"\n  >>> NEXT STEP: Update DELEGATION_MANAGER_ADDRESS secret to:")
    print(f"  >>> {contract_address}")
    print()


if __name__ == "__main__":
    main()
