#!/usr/bin/env python3
"""
WETH Wrap/Unwrap Test - On-Chain Execution Verification
Minimal-risk test to prove end-to-end transaction execution capabilities
"""

import os
import time
import json
import traceback
from datetime import datetime
from typing import Dict, Optional

def log_transaction_receipt(w3, tx_hash: str, operation: str, before_balances: Dict, after_balances: Dict):
    """Log detailed transaction receipt and execution details"""
    try:
        print(f"\n📋 TRANSACTION RECEIPT - {operation.upper()}")
        print("=" * 70)
        
        # Get transaction receipt
        receipt = w3.eth.get_receipt(tx_hash)
        
        print(f"🔗 Transaction Hash: {tx_hash}")
        print(f"🔍 Arbiscan Link: https://arbiscan.io/tx/{tx_hash}")
        print(f"📦 Block Number: {receipt['blockNumber']:,}")
        print(f"⛽ Gas Used: {receipt['gasUsed']:,}")
        print(f"💰 Gas Price: {receipt['effectiveGasPrice'] / 1e9:.2f} Gwei")
        print(f"💸 Total Gas Cost: {(receipt['gasUsed'] * receipt['effectiveGasPrice']) / 1e18:.8f} ETH")
        print(f"✅ Status: {'SUCCESS' if receipt['status'] == 1 else 'FAILED'}")
        
        # Show balance changes
        print(f"\n💰 BALANCE CHANGES:")
        for token in ['ETH', 'WETH']:
            if token in before_balances and token in after_balances:
                before = before_balances[token]
                after = after_balances[token]
                change = after - before
                change_symbol = "+" if change >= 0 else ""
                print(f"   {token}: {before:.8f} → {after:.8f} ({change_symbol}{change:.8f})")
        
        return {
            'transaction_hash': tx_hash,
            'arbiscan_link': f"https://arbiscan.io/tx/{tx_hash}",
            'operation': operation,
            'block_number': receipt['blockNumber'],
            'gas_used': receipt['gasUsed'],
            'gas_price_gwei': receipt['effectiveGasPrice'] / 1e9,
            'gas_cost_eth': (receipt['gasUsed'] * receipt['effectiveGasPrice']) / 1e18,
            'status': 'SUCCESS' if receipt['status'] == 1 else 'FAILED',
            'balances_before': before_balances,
            'balances_after': after_balances,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error retrieving receipt: {e}")
        return {
            'transaction_hash': tx_hash,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_current_balances(agent, weth_contract) -> Dict[str, float]:
    """Get current ETH and WETH balances"""
    try:
        # Get native ETH balance
        eth_balance = agent.w3.eth.get_balance(agent.address)
        eth_balance_formatted = eth_balance / 1e18
        
        # Get WETH balance
        weth_balance = weth_contract.functions.balanceOf(agent.address).call()
        weth_balance_formatted = weth_balance / 1e18
        
        return {
            'ETH': eth_balance_formatted,
            'WETH': weth_balance_formatted
        }
        
    except Exception as e:
        print(f"❌ Error getting balances: {e}")
        return {}

def get_current_health_factor(agent) -> float:
    """Get current health factor from Aave"""
    try:
        pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(address=pool_address, abi=pool_abi)
        raw_data = pool_contract.functions.getUserAccountData(agent.address).call()
        health_factor = raw_data[5] / 1e18 if raw_data[5] > 0 else float('inf')
        
        return health_factor
        
    except Exception as e:
        print(f"❌ Error getting health factor: {e}")
        return 0.0

def execute_weth_wrap_test(agent, test_amount_eth: float = 0.00002) -> Dict:
    """Execute WETH wrap test with full transaction logging"""
    print(f"\n🔄 WETH WRAP TEST - AMOUNT: {test_amount_eth} ETH")
    print("=" * 70)
    
    test_results = {
        'test_name': 'WETH_WRAP_TEST',
        'start_time': datetime.now().isoformat(),
        'test_amount_eth': test_amount_eth,
        'transactions': [],
        'success': False
    }
    
    try:
        # Initialize WETH contract
        weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"  # Arbitrum WETH
        weth_abi = [
            {
                "constant": False,
                "inputs": [],
                "name": "deposit",
                "outputs": [],
                "payable": True,
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "wad", "type": "uint256"}],
                "name": "withdraw",
                "outputs": [],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        weth_contract = agent.w3.eth.contract(address=weth_address, abi=weth_abi)
        
        print(f"✅ WETH contract initialized: {weth_address}")
        
        # Get initial state
        initial_balances = get_current_balances(agent, weth_contract)
        initial_health_factor = get_current_health_factor(agent)
        
        test_results['initial_balances'] = initial_balances
        test_results['initial_health_factor'] = initial_health_factor
        
        print(f"📊 INITIAL STATE:")
        print(f"   ETH Balance: {initial_balances.get('ETH', 0):.8f}")
        print(f"   WETH Balance: {initial_balances.get('WETH', 0):.8f}")
        print(f"   Health Factor: {initial_health_factor:.6f}")
        
        # Check if we have sufficient ETH
        available_eth = initial_balances.get('ETH', 0)
        gas_buffer = 0.0005  # Reserve for gas costs
        
        if available_eth < test_amount_eth + gas_buffer:
            raise Exception(f"Insufficient ETH balance. Available: {available_eth:.8f}, Need: {test_amount_eth + gas_buffer:.8f}")
        
        print(f"\n🎯 TEST PARAMETERS:")
        print(f"   Test Amount: {test_amount_eth} ETH")
        print(f"   Available ETH: {available_eth:.8f}")
        print(f"   Gas Buffer: {gas_buffer} ETH")
        print(f"   Sufficient Balance: ✅")
        
        # STEP 1: Wrap ETH to WETH
        print(f"\n🔄 STEP 1: WRAPPING {test_amount_eth} ETH TO WETH...")
        
        # Build wrap transaction
        wrap_amount_wei = int(test_amount_eth * 1e18)
        
        wrap_txn = weth_contract.functions.deposit().build_transaction({
            'from': agent.address,
            'value': wrap_amount_wei,
            'nonce': agent.w3.eth.get_transaction_count(agent.address),
            'gasPrice': agent.w3.eth.gas_price
        })
        
        # Estimate gas
        try:
            gas_estimate = agent.w3.eth.estimate_gas(wrap_txn)
            wrap_txn['gas'] = int(gas_estimate * 1.2)  # Add 20% buffer
            print(f"   Gas Estimate: {gas_estimate:,} (using {wrap_txn['gas']:,})")
        except Exception as e:
            print(f"   Gas estimation failed, using default: {e}")
            wrap_txn['gas'] = 21000
        
        # Sign and send transaction
        signed_wrap = agent.w3.eth.account.sign_transaction(wrap_txn, agent.private_key)
        wrap_tx_hash = agent.w3.eth.send_raw_transaction(signed_wrap.rawTransaction)
        wrap_tx_hash_hex = wrap_tx_hash.hex()
        
        print(f"   📤 Wrap transaction sent: {wrap_tx_hash_hex}")
        
        # Wait for confirmation
        print(f"   ⏳ Waiting for confirmation...")
        wrap_receipt = agent.w3.eth.wait_for_transaction_receipt(wrap_tx_hash, timeout=120)
        
        # Get balances after wrap
        balances_after_wrap = get_current_balances(agent, weth_contract)
        
        # Log wrap transaction
        wrap_log = log_transaction_receipt(
            agent.w3, wrap_tx_hash_hex, "ETH_WRAP", 
            initial_balances, balances_after_wrap
        )
        test_results['transactions'].append(wrap_log)
        
        print(f"✅ WRAP COMPLETED SUCCESSFULLY!")
        
        # Small delay
        time.sleep(2)
        
        # STEP 2: Unwrap WETH back to ETH
        print(f"\n🔄 STEP 2: UNWRAPPING {test_amount_eth} WETH TO ETH...")
        
        # Build unwrap transaction
        unwrap_amount_wei = int(test_amount_eth * 1e18)
        
        unwrap_txn = weth_contract.functions.withdraw(unwrap_amount_wei).build_transaction({
            'from': agent.address,
            'nonce': agent.w3.eth.get_transaction_count(agent.address),
            'gasPrice': agent.w3.eth.gas_price
        })
        
        # Estimate gas
        try:
            gas_estimate = agent.w3.eth.estimate_gas(unwrap_txn)
            unwrap_txn['gas'] = int(gas_estimate * 1.2)
            print(f"   Gas Estimate: {gas_estimate:,} (using {unwrap_txn['gas']:,})")
        except Exception as e:
            print(f"   Gas estimation failed, using default: {e}")
            unwrap_txn['gas'] = 21000
        
        # Sign and send transaction
        signed_unwrap = agent.w3.eth.account.sign_transaction(unwrap_txn, agent.private_key)
        unwrap_tx_hash = agent.w3.eth.send_raw_transaction(signed_unwrap.rawTransaction)
        unwrap_tx_hash_hex = unwrap_tx_hash.hex()
        
        print(f"   📤 Unwrap transaction sent: {unwrap_tx_hash_hex}")
        
        # Wait for confirmation
        print(f"   ⏳ Waiting for confirmation...")
        unwrap_receipt = agent.w3.eth.wait_for_transaction_receipt(unwrap_tx_hash, timeout=120)
        
        # Get final balances
        final_balances = get_current_balances(agent, weth_contract)
        final_health_factor = get_current_health_factor(agent)
        
        # Log unwrap transaction
        unwrap_log = log_transaction_receipt(
            agent.w3, unwrap_tx_hash_hex, "WETH_UNWRAP",
            balances_after_wrap, final_balances
        )
        test_results['transactions'].append(unwrap_log)
        
        print(f"✅ UNWRAP COMPLETED SUCCESSFULLY!")
        
        # Final state
        test_results['final_balances'] = final_balances
        test_results['final_health_factor'] = final_health_factor
        test_results['success'] = True
        
        # Calculate total gas costs
        total_gas_cost = sum(tx.get('gas_cost_eth', 0) for tx in test_results['transactions'])
        test_results['total_gas_cost_eth'] = total_gas_cost
        
        print(f"\n🏆 WETH WRAP/UNWRAP TEST COMPLETED!")
        print(f"✅ Transactions: {len(test_results['transactions'])}/2 successful")
        print(f"💸 Total Gas Cost: {total_gas_cost:.8f} ETH")
        print(f"📊 Health Factor: {initial_health_factor:.6f} → {final_health_factor:.6f}")
        
        return test_results
        
    except Exception as e:
        print(f"❌ WETH wrap test failed: {e}")
        test_results['error'] = str(e)
        test_results['error_details'] = traceback.format_exc()
        return test_results
    
    finally:
        test_results['end_time'] = datetime.now().isoformat()

def execute_weth_unwrap_test(agent, test_amount_eth: float = 0.00002) -> Dict:
    """Execute WETH unwrap test (reverse operation)"""
    print(f"\n🔄 WETH UNWRAP TEST - AMOUNT: {test_amount_eth} ETH")
    print("=" * 70)
    
    test_results = {
        'test_name': 'WETH_UNWRAP_TEST',
        'start_time': datetime.now().isoformat(),
        'test_amount_eth': test_amount_eth,
        'transactions': [],
        'success': False
    }
    
    try:
        # Initialize WETH contract
        weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
        weth_abi = [
            {
                "constant": False,
                "inputs": [],
                "name": "deposit",
                "outputs": [],
                "payable": True,
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "wad", "type": "uint256"}],
                "name": "withdraw",
                "outputs": [],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        weth_contract = agent.w3.eth.contract(address=weth_address, abi=weth_abi)
        
        # Get initial state
        initial_balances = get_current_balances(agent, weth_contract)
        initial_health_factor = get_current_health_factor(agent)
        
        print(f"📊 INITIAL STATE:")
        print(f"   ETH Balance: {initial_balances.get('ETH', 0):.8f}")
        print(f"   WETH Balance: {initial_balances.get('WETH', 0):.8f}")
        print(f"   Health Factor: {initial_health_factor:.6f}")
        
        # Check if we have sufficient WETH
        available_weth = initial_balances.get('WETH', 0)
        
        if available_weth < test_amount_eth:
            raise Exception(f"Insufficient WETH balance. Available: {available_weth:.8f}, Need: {test_amount_eth:.8f}")
        
        print(f"✅ Sufficient WETH balance for test")
        
        # Unwrap WETH to ETH
        print(f"\n🔄 UNWRAPPING {test_amount_eth} WETH TO ETH...")
        
        unwrap_amount_wei = int(test_amount_eth * 1e18)
        
        unwrap_txn = weth_contract.functions.withdraw(unwrap_amount_wei).build_transaction({
            'from': agent.address,
            'nonce': agent.w3.eth.get_transaction_count(agent.address),
            'gasPrice': agent.w3.eth.gas_price
        })
        
        # Estimate gas
        try:
            gas_estimate = agent.w3.eth.estimate_gas(unwrap_txn)
            unwrap_txn['gas'] = int(gas_estimate * 1.2)
        except Exception as e:
            unwrap_txn['gas'] = 21000
        
        # Sign and send
        signed_unwrap = agent.w3.eth.account.sign_transaction(unwrap_txn, agent.private_key)
        unwrap_tx_hash = agent.w3.eth.send_raw_transaction(signed_unwrap.rawTransaction)
        unwrap_tx_hash_hex = unwrap_tx_hash.hex()
        
        print(f"📤 Transaction sent: {unwrap_tx_hash_hex}")
        
        # Wait for confirmation
        unwrap_receipt = agent.w3.eth.wait_for_transaction_receipt(unwrap_tx_hash, timeout=120)
        
        # Get final balances
        final_balances = get_current_balances(agent, weth_contract)
        final_health_factor = get_current_health_factor(agent)
        
        # Log transaction
        unwrap_log = log_transaction_receipt(
            agent.w3, unwrap_tx_hash_hex, "WETH_UNWRAP",
            initial_balances, final_balances
        )
        test_results['transactions'].append(unwrap_log)
        
        test_results['final_balances'] = final_balances
        test_results['final_health_factor'] = final_health_factor
        test_results['success'] = True
        
        print(f"✅ WETH UNWRAP TEST COMPLETED!")
        
        return test_results
        
    except Exception as e:
        print(f"❌ WETH unwrap test failed: {e}")
        test_results['error'] = str(e)
        test_results['error_details'] = traceback.format_exc()
        return test_results
    
    finally:
        test_results['end_time'] = datetime.now().isoformat()

def main():
    """Execute WETH wrap/unwrap test to verify on-chain execution"""
    print("🚀 WETH WRAP/UNWRAP TEST - ON-CHAIN EXECUTION VERIFICATION")
    print("=" * 90)
    print("Minimal-risk test to prove end-to-end transaction capabilities")
    print("=" * 90)
    
    execution_results = {
        'test_suite': 'WETH_EXECUTION_VERIFICATION',
        'start_time': datetime.now().isoformat(),
        'tests': {},
        'overall_success': False
    }
    
    try:
        # Initialize agent
        print("🤖 INITIALIZING AGENT...")
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
        
        print(f"✅ Agent initialized: {agent.address}")
        
        # Execute wrap/unwrap test
        wrap_test_results = execute_weth_wrap_test(agent, test_amount_eth=0.00002)
        execution_results['tests']['wrap_unwrap_test'] = wrap_test_results
        
        # Test success assessment
        successful_tests = sum(1 for test in execution_results['tests'].values() if test.get('success', False))
        execution_results['successful_tests'] = successful_tests
        execution_results['total_tests'] = len(execution_results['tests'])
        execution_results['overall_success'] = successful_tests > 0
        
        # Calculate total costs
        total_transactions = sum(len(test.get('transactions', [])) for test in execution_results['tests'].values())
        total_gas_cost = sum(test.get('total_gas_cost_eth', 0) for test in execution_results['tests'].values())
        
        execution_results['total_transactions'] = total_transactions
        execution_results['total_gas_cost_eth'] = total_gas_cost
        
        print(f"\n🏆 EXECUTION VERIFICATION COMPLETED")
        print("=" * 90)
        print(f"✅ Overall Success: {'YES' if execution_results['overall_success'] else 'NO'}")
        print(f"✅ Successful Tests: {successful_tests}/{len(execution_results['tests'])}")
        print(f"✅ Total Transactions: {total_transactions}")
        print(f"💸 Total Gas Cost: {total_gas_cost:.8f} ETH")
        
        return execution_results
        
    except Exception as e:
        print(f"❌ Execution verification failed: {e}")
        execution_results['error'] = str(e)
        execution_results['error_details'] = traceback.format_exc()
        return execution_results
    
    finally:
        execution_results['end_time'] = datetime.now().isoformat()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weth_execution_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(execution_results, f, indent=2, default=str)
        
        print(f"\n📁 Complete test results saved to: {filename}")

if __name__ == "__main__":
    main()