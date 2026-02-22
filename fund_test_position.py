#!/usr/bin/env python3
"""
Fund Test Position on Tenderly Fork
Wraps ETH → WETH, approves Aave Pool, supplies WETH as collateral.
Safe to run — only works on Tenderly fork (NETWORK_MODE=fork).
"""
import os
import sys
import json
from web3 import Web3
from eth_account import Account

WETH_ADDRESS = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
AAVE_POOL_ADDRESS = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
AAVE_DATA_PROVIDER = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"

WETH_ABI = json.loads('[{"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')

POOL_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"supply","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserAccountData","outputs":[{"internalType":"uint256","name":"totalCollateralBase","type":"uint256"},{"internalType":"uint256","name":"totalDebtBase","type":"uint256"},{"internalType":"uint256","name":"availableBorrowsBase","type":"uint256"},{"internalType":"uint256","name":"currentLiquidationThreshold","type":"uint256"},{"internalType":"uint256","name":"ltv","type":"uint256"},{"internalType":"uint256","name":"healthFactor","type":"uint256"}],"stateMutability":"view","type":"function"}]')

MAX_UINT256 = 2**256 - 1


def get_private_key():
    return os.getenv('PRIVATE_KEY2') or os.getenv('PRIVATE_KEY') or None


def main():
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    if network_mode != 'fork':
        print("❌ SAFETY: This script only runs in fork mode (NETWORK_MODE=fork)")
        print(f"   Current NETWORK_MODE: {network_mode}")
        sys.exit(1)

    rpc_url = os.getenv('TENDERLY_RPC_URL')
    if not rpc_url:
        print("❌ TENDERLY_RPC_URL not set")
        sys.exit(1)

    private_key = get_private_key()
    if not private_key:
        print("❌ No private key found (PRIVATE_KEY2 or PRIVATE_KEY)")
        sys.exit(1)

    eth_amount = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
    if not w3.is_connected():
        print("❌ Cannot connect to Tenderly RPC")
        sys.exit(1)

    account = Account.from_key(private_key)
    wallet = account.address
    chain_id = w3.eth.chain_id

    print(f"🧪 Fund Test Position on Tenderly Fork")
    print(f"=" * 50)
    print(f"🔗 Chain ID: {chain_id}")
    print(f"👛 Wallet: {wallet}")
    print(f"💰 ETH to wrap & supply: {eth_amount} ETH")

    eth_balance = w3.eth.get_balance(wallet)
    eth_bal_human = w3.from_wei(eth_balance, 'ether')
    print(f"📊 Current ETH balance: {eth_bal_human:.6f} ETH")

    if eth_balance < w3.to_wei(eth_amount + 0.01, 'ether'):
        print(f"❌ Insufficient ETH. Need {eth_amount + 0.01} ETH, have {eth_bal_human:.6f}")
        sys.exit(1)

    weth = w3.eth.contract(address=Web3.to_checksum_address(WETH_ADDRESS), abi=WETH_ABI)
    pool = w3.eth.contract(address=Web3.to_checksum_address(AAVE_POOL_ADDRESS), abi=POOL_ABI)

    weth_before = weth.functions.balanceOf(wallet).call()
    print(f"📊 Current WETH balance: {w3.from_wei(weth_before, 'ether'):.6f} WETH")

    print(f"\n--- Step 1: Wrap {eth_amount} ETH → WETH ---")
    wrap_amount = w3.to_wei(eth_amount, 'ether')
    nonce = w3.eth.get_transaction_count(wallet)

    tx = weth.functions.deposit().build_transaction({
        'from': wallet,
        'value': wrap_amount,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'chainId': chain_id,
    })
    def send_signed(signed_tx):
        raw = getattr(signed_tx, 'rawTransaction', None) or getattr(signed_tx, 'raw_transaction', None)
        return w3.eth.send_raw_transaction(raw)

    signed = account.sign_transaction(tx)
    tx_hash = send_signed(signed)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if receipt.status != 1:
        print(f"❌ Wrap TX failed: {tx_hash.hex()}")
        sys.exit(1)
    print(f"✅ Wrapped {eth_amount} ETH → WETH (tx: {tx_hash.hex()[:16]}...)")

    weth_after = weth.functions.balanceOf(wallet).call()
    print(f"📊 WETH balance now: {w3.from_wei(weth_after, 'ether'):.6f} WETH")

    print(f"\n--- Step 2: Approve Aave Pool to spend WETH ---")
    allowance = weth.functions.allowance(wallet, AAVE_POOL_ADDRESS).call()
    if allowance < wrap_amount:
        nonce = w3.eth.get_transaction_count(wallet)
        approve_tx = weth.functions.approve(AAVE_POOL_ADDRESS, MAX_UINT256).build_transaction({
            'from': wallet,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': chain_id,
        })
        signed = account.sign_transaction(approve_tx)
        tx_hash = send_signed(signed)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.status != 1:
            print(f"❌ Approve TX failed: {tx_hash.hex()}")
            sys.exit(1)
        print(f"✅ Approved Aave Pool (tx: {tx_hash.hex()[:16]}...)")
    else:
        print(f"✅ Already approved (allowance sufficient)")

    print(f"\n--- Step 3: Supply {eth_amount} WETH to Aave ---")
    nonce = w3.eth.get_transaction_count(wallet)
    supply_tx = pool.functions.supply(
        Web3.to_checksum_address(WETH_ADDRESS),
        wrap_amount,
        wallet,
        0
    ).build_transaction({
        'from': wallet,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price,
        'chainId': chain_id,
    })
    signed = account.sign_transaction(supply_tx)
    tx_hash = send_signed(signed)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if receipt.status != 1:
        print(f"❌ Supply TX failed: {tx_hash.hex()}")
        sys.exit(1)
    print(f"✅ Supplied {eth_amount} WETH to Aave (tx: {tx_hash.hex()[:16]}...)")

    print(f"\n--- Final Position ---")
    try:
        result = pool.functions.getUserAccountData(wallet).call()
        total_collateral = result[0] / 1e8
        total_debt = result[1] / 1e8
        available_borrows = result[2] / 1e8
        health_factor = result[5] / 1e18

        print(f"💎 Total Collateral:   ${total_collateral:,.2f}")
        print(f"💳 Total Debt:         ${total_debt:,.2f}")
        print(f"🏦 Available Borrows:  ${available_borrows:,.2f}")
        if health_factor > 1e10:
            print(f"❤️ Health Factor:     ∞ (no debt)")
        else:
            print(f"❤️ Health Factor:     {health_factor:.4f}")
        print(f"\n🎯 Ready to test triggers!")
        print(f"   Growth Path needs: HF > 3.10, available borrows > $12")
        print(f"   Capacity Path needs: HF > 2.90, available borrows > $7")
    except Exception as e:
        print(f"⚠️ Could not read position: {e}")

    remaining_eth = w3.eth.get_balance(wallet)
    print(f"\n📊 Remaining ETH: {w3.from_wei(remaining_eth, 'ether'):.6f} ETH")
    print(f"✅ Done! Position funded on Tenderly fork.")


if __name__ == '__main__':
    main()
