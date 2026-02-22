#!/usr/bin/env python3
"""
Deploy REAADelegationManager and OpenClawVault to Arbitrum Mainnet.

Usage:
  python deploy_contracts_mainnet.py

Requirements:
  - DEPLOYER_PRIVATE_KEY (or PRIVATE_KEY) in Replit Secrets
  - Deployer wallet needs ~0.001 ETH on Arbitrum for gas
  - BOT_PRIVATE_KEY (or PRIVATE_KEY) to derive the bot operator address

After deployment, update these Replit Secrets:
  - DELEGATION_MANAGER_ADDRESS = <deployed DM address>
  - OPENCLAW_VAULT_ADDRESS = <deployed Vault address>
"""

import os
import sys
import json
import time
from web3 import Web3
from eth_account import Account

ARBITRUM_USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
ARBITRUM_CHAIN_ID = 42161

OPENCLAW_VAULT_SOL = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

contract OpenClawVault {
    IERC20 public usdc;
    address public owner;

    constructor(address _usdcAddress) {
        usdc = IERC20(_usdcAddress);
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized by OpenClaw API");
        _;
    }

    function executeTransfer(address userWallet, address destinationWallet, uint256 amount) external onlyOwner {
        require(usdc.transferFrom(userWallet, destinationWallet, amount), "USDC transfer failed. Check user allowance.");
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid address");
        owner = newOwner;
    }
}
"""


def get_rpc():
    rpcs = []
    arb = os.getenv("ARBITRUM_RPC_URL")
    if arb:
        rpcs.append(arb)
    alchemy = os.getenv("ALCHEMY_ARB_RPC") or os.getenv("ALCHEMY_RPC_URL")
    if alchemy and alchemy not in rpcs:
        rpcs.append(alchemy)
    rpcs.extend([
        "https://arbitrum-one.public.blastapi.io",
        "https://arb1.arbitrum.io/rpc",
        "https://arbitrum-one.publicnode.com",
    ])
    for url in rpcs:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 15}))
            if w3.is_connected() and w3.eth.chain_id == ARBITRUM_CHAIN_ID:
                print(f"  Connected to Arbitrum via {url[:50]}...")
                return w3
        except Exception:
            continue
    return None


def get_deployer_key():
    for key_name in ["DEPLOYER_PRIVATE_KEY", "PRIVATE_KEY", "BOT_PRIVATE_KEY"]:
        pk = os.getenv(key_name)
        if pk and len(pk) >= 64:
            print(f"  Using {key_name} for deployment")
            return pk
    return None


def get_bot_operator_address():
    for key_name in ["BOT_PRIVATE_KEY", "PRIVATE_KEY"]:
        pk = os.getenv(key_name)
        if pk and len(pk) >= 64:
            if not pk.startswith("0x"):
                pk = "0x" + pk
            acct = Account.from_key(pk)
            return acct.address
    return None


def compile_contract(source_code, contract_name):
    import solcx
    installed = solcx.get_installed_solc_versions()
    target_version = "0.8.20"
    if not any(str(v).startswith("0.8.2") for v in installed):
        print(f"  Installing Solidity compiler v{target_version}...")
        solcx.install_solc(target_version)
    solcx.set_solc_version(target_version)

    compiled = solcx.compile_source(
        source_code,
        output_values=["abi", "bin"],
        solc_version=target_version,
    )
    contract_key = None
    for key in compiled:
        if contract_name in key:
            contract_key = key
            break
    if not contract_key:
        print(f"  ERROR: Contract '{contract_name}' not found in compiled output")
        print(f"  Available: {list(compiled.keys())}")
        return None, None
    abi = compiled[contract_key]["abi"]
    bytecode = compiled[contract_key]["bin"]
    return abi, bytecode


def deploy_contract(w3, deployer_key, abi, bytecode, constructor_args, contract_name):
    if not deployer_key.startswith("0x"):
        deployer_key = "0x" + deployer_key
    acct = Account.from_key(deployer_key)
    deployer = acct.address

    balance = w3.eth.get_balance(deployer)
    eth_balance = w3.from_wei(balance, "ether")
    print(f"  Deployer: {deployer}")
    print(f"  ETH Balance: {eth_balance:.6f} ETH")
    if balance == 0:
        print("  ERROR: Deployer has no ETH for gas. Send ~0.001 ETH to this address on Arbitrum.")
        return None, None

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer)

    try:
        latest = w3.eth.get_block("latest")
        base_fee = latest.get("baseFeePerGas", w3.eth.gas_price)
    except Exception:
        base_fee = w3.eth.gas_price
    max_priority = w3.to_wei(0.1, "gwei")
    max_fee = base_fee * 2 + max_priority

    tx = contract.constructor(*constructor_args).build_transaction({
        "chainId": ARBITRUM_CHAIN_ID,
        "from": deployer,
        "nonce": nonce,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority,
    })

    try:
        gas_estimate = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas_estimate * 1.2)
    except Exception as e:
        print(f"  Gas estimation failed: {e}")
        tx["gas"] = 3_000_000

    print(f"  Estimated gas: {tx['gas']}")
    cost_wei = tx["gas"] * max_fee
    print(f"  Estimated cost: {w3.from_wei(cost_wei, 'ether'):.6f} ETH")

    if balance < cost_wei:
        print(f"  ERROR: Insufficient ETH. Need ~{w3.from_wei(cost_wei, 'ether'):.6f}, have {eth_balance:.6f}")
        return None, None

    signed = w3.eth.account.sign_transaction(tx, deployer_key)
    print(f"  Sending deployment transaction for {contract_name}...")
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"  TX Hash: {tx_hash.hex()}")
    print(f"  Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
    print(f"  Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status == 1:
        print(f"  SUCCESS! {contract_name} deployed at: {receipt.contractAddress}")
        return receipt.contractAddress, tx_hash.hex()
    else:
        print(f"  FAILED! Transaction reverted.")
        return None, tx_hash.hex()


def main():
    print("=" * 60)
    print("  PROJECT 87 - Arbitrum Mainnet Contract Deployment")
    print("=" * 60)

    print("\n[1/5] Connecting to Arbitrum mainnet...")
    w3 = get_rpc()
    if not w3:
        print("  FATAL: Could not connect to any Arbitrum RPC")
        sys.exit(1)

    print("\n[2/5] Loading deployer wallet...")
    deployer_key = get_deployer_key()
    if not deployer_key:
        print("  FATAL: No deployer private key found.")
        print("  Set DEPLOYER_PRIVATE_KEY or PRIVATE_KEY in Replit Secrets")
        sys.exit(1)

    bot_address = get_bot_operator_address()
    if not bot_address:
        print("  FATAL: Could not derive bot operator address")
        sys.exit(1)
    print(f"  Bot operator address: {bot_address}")

    print("\n[3/5] Compiling contracts...")
    dm_sol_path = "contracts/REAADelegationManager.sol"
    if not os.path.exists(dm_sol_path):
        print(f"  FATAL: {dm_sol_path} not found")
        sys.exit(1)
    with open(dm_sol_path, "r") as f:
        dm_source = f.read()

    print("  Compiling REAADelegationManager...")
    dm_abi, dm_bytecode = compile_contract(dm_source, "REAADelegationManager")
    if not dm_abi:
        sys.exit(1)
    print(f"  REAADelegationManager compiled ({len(dm_bytecode)} bytes)")

    print("  Compiling OpenClawVault...")
    vault_abi, vault_bytecode = compile_contract(OPENCLAW_VAULT_SOL, "OpenClawVault")
    if not vault_abi:
        sys.exit(1)
    print(f"  OpenClawVault compiled ({len(vault_bytecode)} bytes)")

    with open("contracts/REAADelegationManager_abi.json", "w") as f:
        json.dump(dm_abi, f, indent=2)
    with open("contracts/OpenClawVault_abi.json", "w") as f:
        json.dump(vault_abi, f, indent=2)
    print("  ABIs saved to contracts/ directory")

    print("\n[4/5] Deploying REAADelegationManager...")
    print(f"  Constructor arg: botOperator = {bot_address}")
    dm_address, dm_tx = deploy_contract(
        w3, deployer_key, dm_abi, dm_bytecode,
        [bot_address], "REAADelegationManager"
    )
    if not dm_address:
        print("  Deployment failed. Check deployer balance and try again.")
        sys.exit(1)

    time.sleep(2)

    print("\n[5/5] Deploying OpenClawVault...")
    print(f"  Constructor arg: usdcAddress = {ARBITRUM_USDC}")
    vault_address, vault_tx = deploy_contract(
        w3, deployer_key, vault_abi, vault_bytecode,
        [ARBITRUM_USDC], "OpenClawVault"
    )
    if not vault_address:
        print("  Deployment failed. Check deployer balance and try again.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\n  REAADelegationManager: {dm_address}")
    print(f"    TX: https://arbiscan.io/tx/{dm_tx}")
    print(f"\n  OpenClawVault: {vault_address}")
    print(f"    TX: https://arbiscan.io/tx/{vault_tx}")
    print(f"\n  UPDATE YOUR REPLIT SECRETS:")
    print(f"    DELEGATION_MANAGER_ADDRESS = {dm_address}")
    print(f"    OPENCLAW_VAULT_ADDRESS     = {vault_address}")
    print(f"\n  Verify on Arbiscan:")
    print(f"    https://arbiscan.io/address/{dm_address}")
    print(f"    https://arbiscan.io/address/{vault_address}")
    print("=" * 60)

    results = {
        "delegation_manager": {"address": dm_address, "tx": dm_tx},
        "openclaw_vault": {"address": vault_address, "tx": vault_tx},
        "bot_operator": bot_address,
        "deployer": Account.from_key("0x" + deployer_key if not deployer_key.startswith("0x") else deployer_key).address,
        "chain_id": ARBITRUM_CHAIN_ID,
        "timestamp": int(time.time()),
    }
    with open("contracts/deployment_result.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n  Deployment details saved to contracts/deployment_result.json")


if __name__ == "__main__":
    main()
