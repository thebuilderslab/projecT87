#!/usr/bin/env python3
import sys
sys.path.append('.')
import os
os.environ['NETWORK_MODE'] = 'mainnet'
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3

# Initialize agent
agent = ArbitrumTestnetAgent()

print(f'Wallet Address: {agent.address}')
print(f'Chain ID: {agent.w3.eth.chain_id}')

# Check ETH balance
eth_balance = agent.get_eth_balance()
print(f'ETH Balance: {eth_balance:.6f}')

# Check DAI balance from contract
dai_address = '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
dai_contract = agent.w3.eth.contract(
    address=Web3.to_checksum_address(dai_address),
    abi=[{
        'inputs': [{'name': 'account', 'type': 'address'}],
        'name': 'balanceOf', 
        'outputs': [{'name': '', 'type': 'uint256'}],
        'stateMutability': 'view',
        'type': 'function'
    }]
)
dai_balance_wei = dai_contract.functions.balanceOf(agent.address).call()
dai_balance = Web3.from_wei(dai_balance_wei, 'ether')
print(f'DAI Balance: {dai_balance:.6f}')

# Check ARB balance from contract
arb_address = '0x912CE59144191C1204E64559FE8253a0e49E6548'
arb_contract = agent.w3.eth.contract(
    address=Web3.to_checksum_address(arb_address),
    abi=[{
        'inputs': [{'name': 'account', 'type': 'address'}],
        'name': 'balanceOf',
        'outputs': [{'name': '', 'type': 'uint256'}],
        'stateMutability': 'view', 
        'type': 'function'
    }]
)
arb_balance_wei = arb_contract.functions.balanceOf(agent.address).call()
arb_balance = Web3.from_wei(arb_balance_wei, 'ether')
print(f'ARB Balance: {arb_balance:.6f}')

# Check Aave position 
if hasattr(agent, 'aave_integration'):
    print('\nChecking Aave position...')
    try:
        health_data = agent.health_monitor.get_current_health_factor()
        if health_data:
            print(f'Health Factor: {health_data.get("health_factor", 0):.4f}')
            print(f'Available Borrows: ${health_data.get("available_borrows_usd", 0):.2f}')
    except Exception as e:
        print(f'Error checking health: {e}')

# Check if we need to borrow DAI first
if dai_balance < 10:
    print(f'\n⚠️ Insufficient DAI balance for 10 DAI swap: {dai_balance:.6f}')
    print('Options:')
    print('1. Modify swap amount to use available DAI')
    print('2. Borrow DAI from Aave first')
    print('3. Use a smaller amount for demonstration')
else:
    print(f'\n✅ Sufficient DAI balance for 10 DAI swap: {dai_balance:.6f}')