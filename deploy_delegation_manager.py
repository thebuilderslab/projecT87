#!/usr/bin/env python3
"""
Deploy REAADelegationManager.sol to Arbitrum mainnet.

Usage:
  python deploy_delegation_manager.py               # Dry-run (compile only)
  python deploy_delegation_manager.py --deploy       # Deploy to Arbitrum mainnet

Requirements:
  pip install py-solc-x web3

Environment variables:
  BOT_PRIVATE_KEY or PRIVATE_KEY  — The deployer/owner private key (also becomes the funder)
  ALCHEMY_RPC_URL or ARBITRUM_RPC_URL — Optional, falls back to public RPCs

After deployment:
  Set DELEGATION_MANAGER_ADDRESS=<deployed_address> in your environment secrets.
"""

import os
import sys
import json
import argparse

from web3 import Web3

ARBITRUM_RPCS = [
    "https://arbitrum-one.public.blastapi.io",
    "https://arb1.arbitrum.io/rpc",
    "https://arbitrum-one.publicnode.com",
]

CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "contracts", "REAADelegationManager.sol")


def get_web3():
    alchemy = os.getenv("ALCHEMY_RPC_URL") or os.getenv("ARBITRUM_RPC_URL")
    rpcs = ([alchemy] if alchemy else []) + ARBITRUM_RPCS
    for url in rpcs:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 15}))
            if w3.is_connected() and w3.eth.chain_id == 42161:
                print(f"Connected to Arbitrum via {url}")
                return w3
        except Exception:
            continue
    print("ERROR: Could not connect to any Arbitrum RPC")
    sys.exit(1)


def compile_contract():
    try:
        import solcx
    except ImportError:
        print("Installing py-solc-x...")
        os.system(f"{sys.executable} -m pip install py-solc-x")
        import solcx

    solc_version = "0.8.20"
    installed = [str(v) for v in solcx.get_installed_solc_versions()]
    if solc_version not in installed:
        print(f"Installing solc {solc_version}...")
        solcx.install_solc(solc_version)

    solcx.set_solc_version(solc_version)

    with open(CONTRACT_PATH, "r") as f:
        source = f.read()

    print("Compiling REAADelegationManager.sol...")
    compiled = solcx.compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=solc_version,
    )

    contract_key = None
    for key in compiled:
        if "REAADelegationManager" in key:
            contract_key = key
            break

    if not contract_key:
        print(f"ERROR: REAADelegationManager not found in compiled output. Keys: {list(compiled.keys())}")
        sys.exit(1)

    abi = compiled[contract_key]["abi"]
    bytecode = compiled[contract_key]["bin"]

    print(f"Compilation successful!")
    print(f"  Contract key: {contract_key}")
    print(f"  ABI functions: {len([a for a in abi if a.get('type') == 'function'])}")
    print(f"  ABI events: {len([a for a in abi if a.get('type') == 'event'])}")
    print(f"  Bytecode size: {len(bytecode) // 2} bytes")

    artifacts_dir = os.path.join(os.path.dirname(__file__), "contracts", "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    with open(os.path.join(artifacts_dir, "REAADelegationManager.json"), "w") as f:
        json.dump({"abi": abi, "bytecode": bytecode}, f, indent=2)
    print(f"  Artifacts saved to contracts/artifacts/REAADelegationManager.json")

    return abi, bytecode


def deploy(abi, bytecode, bot_address=None):
    pk = os.getenv("BOT_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
    if not pk:
        print("ERROR: BOT_PRIVATE_KEY or PRIVATE_KEY environment variable required for deployment")
        sys.exit(1)

    w3 = get_web3()
    account = w3.eth.account.from_key(pk)
    deployer = account.address
    bot_operator = bot_address if bot_address else deployer

    print(f"\n--- Deployment Details ---")
    print(f"  Network: Arbitrum Mainnet (42161)")
    print(f"  Deployer/Owner: {deployer}")
    print(f"  Bot Operator: {bot_operator}")
    if bot_address:
        print(f"  (Custom bot address provided)")
    else:
        print(f"  (Bot = deployer; use --bot-address to set a different bot operator)")

    balance = w3.eth.get_balance(deployer)
    balance_eth = w3.from_wei(balance, "ether")
    print(f"  Deployer ETH balance: {balance_eth:.6f} ETH")

    if balance_eth < 0.001:
        print(f"ERROR: Insufficient ETH for deployment. Need at least 0.001 ETH, have {balance_eth:.6f}")
        sys.exit(1)

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    print("\nBuilding deployment transaction...")
    gas_price = w3.eth.gas_price
    nonce = w3.eth.get_transaction_count(deployer)

    constructor_tx = contract.constructor(bot_operator).build_transaction({
        "chainId": 42161,
        "from": deployer,
        "nonce": nonce,
        "gasPrice": gas_price,
    })

    gas_estimate = w3.eth.estimate_gas(constructor_tx)
    constructor_tx["gas"] = int(gas_estimate * 1.2)

    cost_wei = constructor_tx["gas"] * gas_price
    cost_eth = w3.from_wei(cost_wei, "ether")
    print(f"  Estimated gas: {gas_estimate}")
    print(f"  Gas price: {w3.from_wei(gas_price, 'gwei'):.4f} gwei")
    print(f"  Estimated cost: {cost_eth:.6f} ETH")

    print("\nSigning and sending deployment transaction...")
    signed_tx = w3.eth.account.sign_transaction(constructor_tx, pk)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"  Tx hash: {tx_hash.hex()}")
    print(f"  Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")

    print("\nWaiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt["status"] == 1:
        contract_address = receipt["contractAddress"]
        print(f"\n{'='*60}")
        print(f"  DEPLOYMENT SUCCESSFUL!")
        print(f"  Contract Address: {contract_address}")
        print(f"  Arbiscan: https://arbiscan.io/address/{contract_address}")
        print(f"  Gas Used: {receipt['gasUsed']}")
        print(f"{'='*60}")
        print(f"\n  Next step: Set this as your environment secret:")
        print(f"    DELEGATION_MANAGER_ADDRESS={contract_address}")
        return contract_address
    else:
        print(f"\nERROR: Deployment transaction reverted!")
        print(f"  Tx hash: {tx_hash.hex()}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Deploy REAADelegationManager to Arbitrum")
    parser.add_argument("--deploy", action="store_true", help="Actually deploy (default is dry-run/compile only)")
    parser.add_argument("--bot-address", type=str, default=None, help="Bot operator address (defaults to deployer)")
    args = parser.parse_args()

    print("=" * 60)
    print("REAADelegationManager Deployment Tool")
    print("=" * 60)

    abi, bytecode = compile_contract()

    if args.deploy:
        print("\n--- LIVE DEPLOYMENT MODE ---")
        deploy(abi, bytecode, bot_address=args.bot_address)
    else:
        print("\n--- DRY RUN (compile only) ---")
        print("Contract compiled successfully. Run with --deploy to deploy to Arbitrum mainnet.")
        print(f"\nTo deploy:\n  python deploy_delegation_manager.py --deploy")


if __name__ == "__main__":
    main()
