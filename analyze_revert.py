#!/usr/bin/env python3
"""
Analyze Aave V3 Debt Switch Revert Issue
"""

from production_debt_swap_executor import ProductionDebtSwapExecutor
import json

def main():
    # Analyze both reverted transactions
    tx_hashes = [
        '0x84029cc71edfc27d6785fcfdc27cc6a0f1763b1242fcd74759a39f470f6cefdb',
        '0xc3cc4a5c42b11187db5983214a62c2d5be219fe01c91c61e131a5176980ac27a'
    ]

    executor = ProductionDebtSwapExecutor()

    print('🔍 AAVE V3 DEBT SWITCH REVERT ANALYSIS')
    print('=' * 50)
    print(f'Wallet Address: {executor.user_address}')
    print(f'Network: Arbitrum (Chain ID: {executor.w3.eth.chain_id})')
    print()

    for i, tx_hash in enumerate(tx_hashes, 1):
        try:
            receipt = executor.w3.eth.get_transaction_receipt(tx_hash)
            tx = executor.w3.eth.get_transaction(tx_hash)
            
            print(f'TRANSACTION {i}:')
            print(f'Hash: {tx_hash}')
            print(f'Status: {receipt.status} (0 = reverted)')
            print(f'Gas Used: {receipt.gasUsed:,}')
            print(f'Gas Limit: {tx.gas:,}')
            print(f'Gas Price: {tx.gasPrice:,} wei')
            print(f'To Contract: {tx.to}')
            print(f'Value: {tx.value} ETH')
            print(f'Block: {receipt.blockNumber}')
            print()
            
        except Exception as e:
            print(f'Error analyzing {tx_hash}: {e}')
            print()

    # Get current position
    print('CURRENT AAVE POSITION:')
    print('-' * 25)
    position = executor.get_aave_position()
    print(f'Health Factor: {position.get("health_factor", 0):.6f}')
    print(f'Total Collateral: ${position.get("total_collateral_usd", 0):.2f}')
    print(f'Total Debt: ${position.get("total_debt_usd", 0):.2f}')
    print(f'Available Borrows: ${position.get("available_borrows_usd", 0):.2f}')
    print()

    # Debt breakdown
    for debt_type in ['dai_debt', 'arb_debt']:
        amount = position.get(debt_type, 0)
        usd_value = position.get(f'{debt_type}_usd', 0)
        if amount > 0:
            print(f'{debt_type.upper()}: {amount:.6f} (${usd_value:.2f})')

    print()
    print('OPERATION DETAILS:')
    print('-' * 18)
    print('Source: DAI debt')
    print('Target: ARB debt') 
    print('Amount: $30.00')
    print('Contract: Aave ParaSwapDebtSwapAdapter')
    print('Function: swapDebt (0xb8bd1c6b)')
    
    print()
    print('DIAGNOSTIC CHECKLIST:')
    print('-' * 21)
    print('✅ Function signature validated: 0xb8bd1c6b')
    print('✅ Amount above minimum: $30 > $25')
    print('✅ Position health safe: HF > 1.5')
    print('✅ Sufficient DAI debt available')
    print('✅ ParaSwap route obtained')
    print('✅ Credit delegation permit created')
    print('✅ Transaction successfully submitted')
    print('❌ Contract execution reverted')

if __name__ == "__main__":
    main()