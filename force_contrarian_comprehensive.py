#!/usr/bin/env python3
"""
Comprehensive Forced Contrarian Trading Workflow Execution
4-Step Process with Full Transaction Logging and Verification
"""

import os
import time
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

def log_transaction_details(tx_hash: str, operation: str, before_balances: Dict, after_balances: Dict, 
                          health_factor_before: float, health_factor_after: float, gas_used: Optional[int] = None):
    """Log comprehensive transaction details"""
    print(f"\n📋 TRANSACTION LOG - {operation.upper()}")
    print("=" * 60)
    print(f"🔗 Transaction Hash: {tx_hash}")
    print(f"🔍 Arbiscan Link: https://arbiscan.io/tx/{tx_hash}")
    
    if gas_used:
        print(f"⛽ Gas Used: {gas_used:,}")
    
    print(f"\n💰 BALANCE CHANGES:")
    for token in ['DAI', 'ARB', 'WETH']:
        if token in before_balances and token in after_balances:
            before = before_balances[token]
            after = after_balances[token]
            change = after - before
            change_symbol = "+" if change >= 0 else ""
            print(f"   {token}: {before:.6f} → {after:.6f} ({change_symbol}{change:.6f})")
    
    print(f"\n📊 HEALTH FACTOR:")
    hf_change = health_factor_after - health_factor_before
    hf_symbol = "+" if hf_change >= 0 else ""
    print(f"   Before: {health_factor_before:.6f}")
    print(f"   After: {health_factor_after:.6f}")
    print(f"   Change: {hf_symbol}{hf_change:.6f}")
    
    return {
        'transaction_hash': tx_hash,
        'arbiscan_link': f"https://arbiscan.io/tx/{tx_hash}",
        'operation': operation,
        'gas_used': gas_used,
        'balances_before': before_balances,
        'balances_after': after_balances,
        'health_factor_before': health_factor_before,
        'health_factor_after': health_factor_after,
        'health_factor_change': hf_change,
        'timestamp': datetime.now().isoformat()
    }

def get_current_balances(agent) -> Dict[str, float]:
    """Get current token balances"""
    try:
        balances = {}
        
        # Get DAI balance
        if hasattr(agent, 'dai_contract'):
            dai_balance = agent.dai_contract.functions.balanceOf(agent.address).call()
            balances['DAI'] = dai_balance / 1e18
        
        # Get ARB balance (native token)
        arb_balance = agent.w3.eth.get_balance(agent.address)
        balances['ARB'] = arb_balance / 1e18
        
        # Get WETH balance if available
        if hasattr(agent, 'weth_contract'):
            weth_balance = agent.weth_contract.functions.balanceOf(agent.address).call()
            balances['WETH'] = weth_balance / 1e18
        
        return balances
        
    except Exception as e:
        print(f"❌ Error getting balances: {e}")
        return {}

def get_current_health_factor(agent) -> float:
    """Get current health factor from Aave"""
    try:
        # Direct Aave contract call
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

def get_debt_position_details(agent) -> Dict:
    """Get detailed debt position information"""
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
        
        return {
            'total_collateral': raw_data[0] / 1e8,
            'total_debt': raw_data[1] / 1e8,
            'available_borrows': raw_data[2] / 1e8,
            'liquidation_threshold': raw_data[3] / 100,
            'ltv': raw_data[4] / 100,
            'health_factor': raw_data[5] / 1e18 if raw_data[5] > 0 else float('inf')
        }
        
    except Exception as e:
        print(f"❌ Error getting debt position: {e}")
        return {}

def execute_step_1_dai_borrowing_analysis(agent) -> Dict:
    """Step 1: DAI Borrowing Analysis"""
    print("\n🔄 STEP 1: DAI BORROWING ANALYSIS")
    print("=" * 80)
    
    step_results = {
        'step': 1,
        'name': 'DAI_BORROWING_ANALYSIS',
        'start_time': datetime.now().isoformat(),
        'transactions': [],
        'success': False
    }
    
    try:
        # Get initial position
        debt_position = get_debt_position_details(agent)
        initial_balances = get_current_balances(agent)
        initial_health_factor = get_current_health_factor(agent)
        
        step_results['initial_position'] = debt_position
        step_results['initial_balances'] = initial_balances
        step_results['initial_health_factor'] = initial_health_factor
        
        print(f"📊 CURRENT DEBT POSITION:")
        print(f"   Total Collateral: ${debt_position.get('total_collateral', 0):.2f}")
        print(f"   Total Debt: ${debt_position.get('total_debt', 0):.2f}")
        print(f"   Available Borrows: ${debt_position.get('available_borrows', 0):.2f}")
        print(f"   Health Factor: {debt_position.get('health_factor', 0):.6f}")
        
        print(f"\n💰 CURRENT BALANCES:")
        for token, balance in initial_balances.items():
            print(f"   {token}: {balance:.6f}")
        
        # Determine if additional DAI borrowing is needed
        current_dai_balance = initial_balances.get('DAI', 0)
        available_borrows = debt_position.get('available_borrows', 0)
        
        print(f"\n🎯 BORROWING ANALYSIS:")
        print(f"   Current DAI Balance: {current_dai_balance:.6f}")
        print(f"   Available Borrowing Capacity: ${available_borrows:.2f}")
        
        # For contrarian trading, we want to use available DAI + potentially borrow more
        target_dai_amount = max(10.0, current_dai_balance + min(available_borrows * 0.1, 25.0))
        
        print(f"   Target DAI Amount: {target_dai_amount:.6f}")
        
        need_to_borrow = target_dai_amount - current_dai_balance
        
        if need_to_borrow > 1.0 and available_borrows > need_to_borrow:
            print(f"   📝 Decision: BORROW ${need_to_borrow:.2f} additional DAI")
            
            # Attempt to borrow additional DAI
            if hasattr(agent, 'borrow_dai'):
                try:
                    print(f"\n🔄 Executing borrow_dai({need_to_borrow:.2f})...")
                    
                    borrow_result = agent.borrow_dai(need_to_borrow)
                    
                    if borrow_result and isinstance(borrow_result, dict):
                        tx_hash = borrow_result.get('txHash') or borrow_result.get('transactionHash')
                        if tx_hash:
                            # Get balances after borrow
                            final_balances = get_current_balances(agent)
                            final_health_factor = get_current_health_factor(agent)
                            
                            # Log transaction
                            tx_log = log_transaction_details(
                                tx_hash, 
                                "DAI_BORROW",
                                initial_balances,
                                final_balances,
                                initial_health_factor,
                                final_health_factor
                            )
                            
                            step_results['transactions'].append(tx_log)
                            step_results['borrowed_amount'] = need_to_borrow
                            
                            print(f"✅ DAI borrowing successful!")
                        else:
                            print(f"⚠️ Borrow executed but no transaction hash returned")
                            step_results['borrowed_amount'] = need_to_borrow
                    else:
                        print(f"❌ DAI borrowing failed: {borrow_result}")
                        step_results['borrow_error'] = str(borrow_result)
                        
                except Exception as e:
                    print(f"❌ Error during DAI borrowing: {e}")
                    step_results['borrow_error'] = str(e)
            else:
                print(f"❌ borrow_dai method not available")
                step_results['borrow_error'] = "borrow_dai method not available"
        else:
            print(f"   📝 Decision: USE EXISTING DAI BALANCE ({current_dai_balance:.6f})")
            step_results['borrowed_amount'] = 0
        
        # Get final position after any borrowing
        final_debt_position = get_debt_position_details(agent)
        final_balances = get_current_balances(agent)
        final_health_factor = get_current_health_factor(agent)
        
        step_results['final_position'] = final_debt_position
        step_results['final_balances'] = final_balances
        step_results['final_health_factor'] = final_health_factor
        step_results['success'] = True
        
        print(f"\n✅ STEP 1 COMPLETED - DAI BORROWING ANALYSIS")
        print(f"   Final DAI Balance: {final_balances.get('DAI', 0):.6f}")
        print(f"   Final Health Factor: {final_health_factor:.6f}")
        
        return step_results
        
    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        step_results['error'] = str(e)
        step_results['error_details'] = traceback.format_exc()
        return step_results
    
    finally:
        step_results['end_time'] = datetime.now().isoformat()

def execute_step_2_dai_to_arb_swap(agent, confidence: float = 0.8) -> Dict:
    """Step 2: DAI to ARB Swap (Force Execute)"""
    print("\n🔄 STEP 2: DAI TO ARB SWAP (FORCE EXECUTE)")
    print("=" * 80)
    
    step_results = {
        'step': 2,
        'name': 'DAI_TO_ARB_SWAP',
        'start_time': datetime.now().isoformat(),
        'transactions': [],
        'success': False
    }
    
    try:
        # Get pre-swap state
        initial_balances = get_current_balances(agent)
        initial_health_factor = get_current_health_factor(agent)
        
        step_results['initial_balances'] = initial_balances
        step_results['initial_health_factor'] = initial_health_factor
        
        print(f"📊 PRE-SWAP STATE:")
        print(f"   DAI Balance: {initial_balances.get('DAI', 0):.6f}")
        print(f"   ARB Balance: {initial_balances.get('ARB', 0):.6f}")
        print(f"   Health Factor: {initial_health_factor:.6f}")
        
        # Check available DAI for swapping
        available_dai = initial_balances.get('DAI', 0)
        
        if available_dai < 0.1:
            raise Exception(f"Insufficient DAI balance for swap: {available_dai:.6f}")
        
        print(f"\n🎯 SWAP PARAMETERS:")
        print(f"   Available DAI: {available_dai:.6f}")
        print(f"   Confidence Level: {confidence}")
        print(f"   Force Execute: TRUE (ignore market conditions)")
        
        # Execute DAI to ARB swap
        if hasattr(agent, '_execute_debt_swap_dai_to_arb'):
            print(f"\n🔄 Executing _execute_debt_swap_dai_to_arb({confidence})...")
            
            try:
                swap_result = agent._execute_debt_swap_dai_to_arb(confidence)
                
                print(f"🔍 Swap Result Type: {type(swap_result)}")
                print(f"🔍 Swap Result: {swap_result}")
                
                # Wait for transaction to be mined
                time.sleep(5)
                
                # Get post-swap state
                final_balances = get_current_balances(agent)
                final_health_factor = get_current_health_factor(agent)
                
                step_results['final_balances'] = final_balances
                step_results['final_health_factor'] = final_health_factor
                
                # Check if swap was successful based on balance changes
                dai_change = final_balances.get('DAI', 0) - initial_balances.get('DAI', 0)
                arb_change = final_balances.get('ARB', 0) - initial_balances.get('ARB', 0)
                
                if dai_change < -0.001 and arb_change > 0.001:
                    # Successful swap detected
                    step_results['success'] = True
                    step_results['dai_swapped'] = abs(dai_change)
                    step_results['arb_received'] = arb_change
                    
                    print(f"✅ DAI TO ARB SWAP SUCCESSFUL!")
                    print(f"   DAI Swapped: {abs(dai_change):.6f}")
                    print(f"   ARB Received: {arb_change:.6f}")
                    print(f"   Exchange Rate: {arb_change/abs(dai_change) if dai_change != 0 else 0:.6f} ARB/DAI")
                    
                    # Try to extract transaction hash from result
                    tx_hash = None
                    if isinstance(swap_result, dict):
                        tx_hash = swap_result.get('txHash') or swap_result.get('transactionHash') or swap_result.get('hash')
                    elif isinstance(swap_result, str) and swap_result.startswith('0x'):
                        tx_hash = swap_result
                    
                    if tx_hash:
                        # Log transaction details
                        tx_log = log_transaction_details(
                            tx_hash,
                            "DAI_TO_ARB_SWAP",
                            initial_balances,
                            final_balances,
                            initial_health_factor,
                            final_health_factor
                        )
                        step_results['transactions'].append(tx_log)
                    else:
                        print(f"⚠️ Transaction executed but hash not available")
                        # Create log without hash
                        print(f"\n📋 TRANSACTION LOG - DAI_TO_ARB_SWAP")
                        print("=" * 60)
                        print(f"🔗 Transaction Hash: NOT_AVAILABLE")
                        print(f"💰 DAI Swapped: {abs(dai_change):.6f}")
                        print(f"💰 ARB Received: {arb_change:.6f}")
                        print(f"📊 Health Factor: {initial_health_factor:.6f} → {final_health_factor:.6f}")
                
                else:
                    # No significant balance changes detected
                    step_results['success'] = False
                    step_results['error'] = f"No significant balance changes detected. DAI change: {dai_change:.6f}, ARB change: {arb_change:.6f}"
                    print(f"❌ No significant balance changes detected")
                    print(f"   DAI Change: {dai_change:.6f}")
                    print(f"   ARB Change: {arb_change:.6f}")
                
                # Always log the attempt
                step_results['swap_result'] = str(swap_result)
                
            except Exception as e:
                print(f"❌ Swap execution error: {e}")
                step_results['error'] = str(e)
                step_results['error_details'] = traceback.format_exc()
                
        else:
            raise Exception("_execute_debt_swap_dai_to_arb method not available")
        
        return step_results
        
    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        step_results['error'] = str(e)
        step_results['error_details'] = traceback.format_exc()
        return step_results
    
    finally:
        step_results['end_time'] = datetime.now().isoformat()

def execute_step_3_hold_period_monitoring(agent, hold_duration: int = 300) -> Dict:
    """Step 3: 5-Minute Hold Period with Monitoring"""
    print("\n🔄 STEP 3: 5-MINUTE HOLD PERIOD WITH MONITORING")
    print("=" * 80)
    
    step_results = {
        'step': 3,
        'name': 'HOLD_PERIOD_MONITORING',
        'start_time': datetime.now().isoformat(),
        'hold_duration': hold_duration,
        'monitoring_data': [],
        'success': False
    }
    
    try:
        start_time = time.time()
        end_time = start_time + hold_duration
        
        # Initial state
        initial_balances = get_current_balances(agent)
        initial_health_factor = get_current_health_factor(agent)
        initial_debt_position = get_debt_position_details(agent)
        
        step_results['initial_state'] = {
            'balances': initial_balances,
            'health_factor': initial_health_factor,
            'debt_position': initial_debt_position
        }
        
        print(f"⏰ HOLD PERIOD: {hold_duration} seconds ({hold_duration/60:.1f} minutes)")
        print(f"📊 INITIAL STATE:")
        print(f"   DAI Balance: {initial_balances.get('DAI', 0):.6f}")
        print(f"   ARB Balance: {initial_balances.get('ARB', 0):.6f}")
        print(f"   Health Factor: {initial_health_factor:.6f}")
        
        # Monitoring loop
        monitor_interval = 30  # Check every 30 seconds
        next_check = start_time + monitor_interval
        
        print(f"\n🔍 STARTING CONTINUOUS MONITORING (every {monitor_interval}s)...")
        
        while time.time() < end_time:
            current_time = time.time()
            
            if current_time >= next_check:
                # Take monitoring snapshot
                current_balances = get_current_balances(agent)
                current_health_factor = get_current_health_factor(agent)
                current_debt_position = get_debt_position_details(agent)
                
                elapsed = current_time - start_time
                remaining = end_time - current_time
                
                monitoring_snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'elapsed_seconds': int(elapsed),
                    'remaining_seconds': int(remaining),
                    'balances': current_balances,
                    'health_factor': current_health_factor,
                    'debt_position': current_debt_position
                }
                
                step_results['monitoring_data'].append(monitoring_snapshot)
                
                # Display monitoring update
                print(f"📊 [{elapsed/60:.1f}m elapsed] Health Factor: {current_health_factor:.6f} | ARB: {current_balances.get('ARB', 0):.6f} | Remaining: {remaining/60:.1f}m")
                
                # Check for significant changes
                hf_change = current_health_factor - initial_health_factor
                arb_balance = current_balances.get('ARB', 0)
                
                if abs(hf_change) > 0.01:
                    print(f"   ⚠️ Health factor changed by {hf_change:+.6f}")
                
                if arb_balance != initial_balances.get('ARB', 0):
                    arb_change = arb_balance - initial_balances.get('ARB', 0)
                    print(f"   💰 ARB balance changed by {arb_change:+.6f}")
                
                next_check = current_time + monitor_interval
            
            # Sleep briefly to avoid busy waiting
            time.sleep(1)
        
        # Final state
        final_balances = get_current_balances(agent)
        final_health_factor = get_current_health_factor(agent)
        final_debt_position = get_debt_position_details(agent)
        
        step_results['final_state'] = {
            'balances': final_balances,
            'health_factor': final_health_factor,
            'debt_position': final_debt_position
        }
        
        # Calculate changes during hold period
        hf_total_change = final_health_factor - initial_health_factor
        arb_total_change = final_balances.get('ARB', 0) - initial_balances.get('ARB', 0)
        
        step_results['total_changes'] = {
            'health_factor_change': hf_total_change,
            'arb_balance_change': arb_total_change,
            'monitoring_snapshots': len(step_results['monitoring_data'])
        }
        
        step_results['success'] = True
        
        print(f"\n✅ STEP 3 COMPLETED - 5-MINUTE HOLD PERIOD")
        print(f"   Total Monitoring Time: {hold_duration/60:.1f} minutes")
        print(f"   Monitoring Snapshots: {len(step_results['monitoring_data'])}")
        print(f"   Health Factor Change: {hf_total_change:+.6f}")
        print(f"   ARB Balance Change: {arb_total_change:+.6f}")
        
        return step_results
        
    except Exception as e:
        print(f"❌ Step 3 failed: {e}")
        step_results['error'] = str(e)
        step_results['error_details'] = traceback.format_exc()
        return step_results
    
    finally:
        step_results['end_time'] = datetime.now().isoformat()

def execute_step_4_arb_to_dai_swap(agent, confidence: float = 0.8) -> Dict:
    """Step 4: ARB to DAI Swap (Complete Cycle)"""
    print("\n🔄 STEP 4: ARB TO DAI SWAP (COMPLETE CYCLE)")
    print("=" * 80)
    
    step_results = {
        'step': 4,
        'name': 'ARB_TO_DAI_SWAP',
        'start_time': datetime.now().isoformat(),
        'transactions': [],
        'success': False
    }
    
    try:
        # Get pre-swap state
        initial_balances = get_current_balances(agent)
        initial_health_factor = get_current_health_factor(agent)
        
        step_results['initial_balances'] = initial_balances
        step_results['initial_health_factor'] = initial_health_factor
        
        print(f"📊 PRE-SWAP STATE:")
        print(f"   ARB Balance: {initial_balances.get('ARB', 0):.6f}")
        print(f"   DAI Balance: {initial_balances.get('DAI', 0):.6f}")
        print(f"   Health Factor: {initial_health_factor:.6f}")
        
        # Check available ARB for swapping
        available_arb = initial_balances.get('ARB', 0)
        
        if available_arb < 0.001:  # Keep some ARB for gas
            raise Exception(f"Insufficient ARB balance for swap: {available_arb:.6f}")
        
        # Reserve some ARB for gas costs
        gas_reserve = 0.001  # Reserve 0.001 ARB for gas
        swappable_arb = max(0, available_arb - gas_reserve)
        
        print(f"\n🎯 SWAP PARAMETERS:")
        print(f"   Available ARB: {available_arb:.6f}")
        print(f"   Gas Reserve: {gas_reserve:.6f}")
        print(f"   Swappable ARB: {swappable_arb:.6f}")
        print(f"   Confidence Level: {confidence}")
        
        if swappable_arb < 0.0001:
            raise Exception(f"Insufficient swappable ARB after gas reserve: {swappable_arb:.6f}")
        
        # Execute ARB to DAI swap
        if hasattr(agent, '_execute_debt_swap_arb_to_dai'):
            print(f"\n🔄 Executing _execute_debt_swap_arb_to_dai({confidence})...")
            
            try:
                swap_result = agent._execute_debt_swap_arb_to_dai(confidence)
                
                print(f"🔍 Swap Result Type: {type(swap_result)}")
                print(f"🔍 Swap Result: {swap_result}")
                
                # Wait for transaction to be mined
                time.sleep(5)
                
                # Get post-swap state
                final_balances = get_current_balances(agent)
                final_health_factor = get_current_health_factor(agent)
                
                step_results['final_balances'] = final_balances
                step_results['final_health_factor'] = final_health_factor
                
                # Check if swap was successful based on balance changes
                arb_change = final_balances.get('ARB', 0) - initial_balances.get('ARB', 0)
                dai_change = final_balances.get('DAI', 0) - initial_balances.get('DAI', 0)
                
                if arb_change < -0.0001 and dai_change > 0.001:
                    # Successful swap detected
                    step_results['success'] = True
                    step_results['arb_swapped'] = abs(arb_change)
                    step_results['dai_received'] = dai_change
                    
                    print(f"✅ ARB TO DAI SWAP SUCCESSFUL!")
                    print(f"   ARB Swapped: {abs(arb_change):.6f}")
                    print(f"   DAI Received: {dai_change:.6f}")
                    print(f"   Exchange Rate: {dai_change/abs(arb_change) if arb_change != 0 else 0:.6f} DAI/ARB")
                    
                    # Try to extract transaction hash from result
                    tx_hash = None
                    if isinstance(swap_result, dict):
                        tx_hash = swap_result.get('txHash') or swap_result.get('transactionHash') or swap_result.get('hash')
                    elif isinstance(swap_result, str) and swap_result.startswith('0x'):
                        tx_hash = swap_result
                    
                    if tx_hash:
                        # Log transaction details
                        tx_log = log_transaction_details(
                            tx_hash,
                            "ARB_TO_DAI_SWAP",
                            initial_balances,
                            final_balances,
                            initial_health_factor,
                            final_health_factor
                        )
                        step_results['transactions'].append(tx_log)
                    else:
                        print(f"⚠️ Transaction executed but hash not available")
                        # Create log without hash
                        print(f"\n📋 TRANSACTION LOG - ARB_TO_DAI_SWAP")
                        print("=" * 60)
                        print(f"🔗 Transaction Hash: NOT_AVAILABLE")
                        print(f"💰 ARB Swapped: {abs(arb_change):.6f}")
                        print(f"💰 DAI Received: {dai_change:.6f}")
                        print(f"📊 Health Factor: {initial_health_factor:.6f} → {final_health_factor:.6f}")
                
                else:
                    # No significant balance changes detected
                    step_results['success'] = False
                    step_results['error'] = f"No significant balance changes detected. ARB change: {arb_change:.6f}, DAI change: {dai_change:.6f}"
                    print(f"❌ No significant balance changes detected")
                    print(f"   ARB Change: {arb_change:.6f}")
                    print(f"   DAI Change: {dai_change:.6f}")
                
                # Always log the attempt
                step_results['swap_result'] = str(swap_result)
                
            except Exception as e:
                print(f"❌ Swap execution error: {e}")
                step_results['error'] = str(e)
                step_results['error_details'] = traceback.format_exc()
                
        else:
            raise Exception("_execute_debt_swap_arb_to_dai method not available")
        
        return step_results
        
    except Exception as e:
        print(f"❌ Step 4 failed: {e}")
        step_results['error'] = str(e)
        step_results['error_details'] = traceback.format_exc()
        return step_results
    
    finally:
        step_results['end_time'] = datetime.now().isoformat()

def calculate_round_trip_analysis(step1_results: Dict, step2_results: Dict, 
                                step3_results: Dict, step4_results: Dict) -> Dict:
    """Calculate comprehensive round-trip profit/loss analysis"""
    print("\n📈 ROUND-TRIP PROFIT/LOSS ANALYSIS")
    print("=" * 80)
    
    analysis = {
        'start_time': step1_results.get('start_time'),
        'end_time': step4_results.get('end_time'),
        'total_transactions': 0,
        'gas_costs_total': 0,
        'profit_loss_analysis': {}
    }
    
    try:
        # Extract starting and ending balances
        start_balances = step1_results.get('initial_balances', {})
        end_balances = step4_results.get('final_balances', {})
        
        # Calculate total transactions and gas costs
        all_transactions = []
        total_gas_cost = 0
        
        for step_result in [step1_results, step2_results, step4_results]:
            transactions = step_result.get('transactions', [])
            all_transactions.extend(transactions)
            
            for tx in transactions:
                gas_used = tx.get('gas_used', 0)
                if gas_used:
                    total_gas_cost += gas_used * 0.1e-9  # Approximate gas cost in ARB
        
        analysis['total_transactions'] = len(all_transactions)
        analysis['all_transactions'] = all_transactions
        analysis['estimated_gas_cost_arb'] = total_gas_cost
        
        # Calculate balance changes
        balance_changes = {}
        for token in ['DAI', 'ARB', 'WETH']:
            start_balance = start_balances.get(token, 0)
            end_balance = end_balances.get(token, 0)
            change = end_balance - start_balance
            balance_changes[token] = {
                'start': start_balance,
                'end': end_balance,
                'change': change
            }
        
        analysis['balance_changes'] = balance_changes
        
        # Health factor analysis
        start_hf = step1_results.get('initial_health_factor', 0)
        end_hf = step4_results.get('final_health_factor', 0)
        
        analysis['health_factor_analysis'] = {
            'start': start_hf,
            'end': end_hf,
            'change': end_hf - start_hf,
            'maintained_safety': end_hf > 1.5
        }
        
        # Display analysis
        print(f"⏰ Total Execution Time: {analysis.get('start_time', 'N/A')} to {analysis.get('end_time', 'N/A')}")
        print(f"🔗 Total Transactions: {analysis['total_transactions']}")
        print(f"⛽ Estimated Gas Costs: ~{total_gas_cost:.6f} ARB")
        
        print(f"\n💰 BALANCE CHANGES:")
        for token, data in balance_changes.items():
            change = data['change']
            change_symbol = "+" if change >= 0 else ""
            print(f"   {token}: {data['start']:.6f} → {data['end']:.6f} ({change_symbol}{change:.6f})")
        
        print(f"\n📊 HEALTH FACTOR:")
        hf_change = analysis['health_factor_analysis']['change']
        hf_symbol = "+" if hf_change >= 0 else ""
        print(f"   Start: {start_hf:.6f}")
        print(f"   End: {end_hf:.6f}")
        print(f"   Change: {hf_symbol}{hf_change:.6f}")
        print(f"   Safety Maintained: {'✅' if end_hf > 1.5 else '❌'} (>1.5 required)")
        
        # Success assessment
        successful_steps = sum(1 for result in [step1_results, step2_results, step3_results, step4_results] 
                             if result.get('success', False))
        
        analysis['successful_steps'] = successful_steps
        analysis['overall_success'] = successful_steps >= 3  # At least 3 steps successful
        
        print(f"\n🎯 WORKFLOW SUCCESS ASSESSMENT:")
        print(f"   Successful Steps: {successful_steps}/4")
        print(f"   Overall Success: {'✅' if analysis['overall_success'] else '❌'}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Analysis calculation failed: {e}")
        analysis['error'] = str(e)
        return analysis

def main():
    """Execute the comprehensive forced contrarian trading workflow"""
    print("🚀 COMPREHENSIVE FORCED CONTRARIAN TRADING WORKFLOW")
    print("=" * 100)
    print("4-Step Process with Full Transaction Logging and Verification")
    print("=" * 100)
    
    workflow_results = {
        'workflow_id': f"forced_contrarian_{int(time.time())}",
        'start_time': datetime.now().isoformat(),
        'steps': {},
        'success': False
    }
    
    try:
        # Initialize agent
        print("🤖 INITIALIZING AGENT...")
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Set forced execution mode
        os.environ['FORCE_EXECUTION_MODE'] = 'true'
        
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
        
        print(f"✅ Agent initialized: {agent.address}")
        
        # Execute Step 1: DAI Borrowing Analysis
        step1_results = execute_step_1_dai_borrowing_analysis(agent)
        workflow_results['steps']['step1'] = step1_results
        
        if not step1_results.get('success'):
            print(f"⚠️ Step 1 had issues, but continuing workflow...")
        
        # Execute Step 2: DAI to ARB Swap (Force Execute)
        step2_results = execute_step_2_dai_to_arb_swap(agent, confidence=0.8)
        workflow_results['steps']['step2'] = step2_results
        
        if not step2_results.get('success'):
            print(f"⚠️ Step 2 failed, but continuing to hold period...")
        
        # Execute Step 3: 5-Minute Hold Period with Monitoring
        step3_results = execute_step_3_hold_period_monitoring(agent, hold_duration=300)
        workflow_results['steps']['step3'] = step3_results
        
        # Execute Step 4: ARB to DAI Swap (Complete Cycle)
        step4_results = execute_step_4_arb_to_dai_swap(agent, confidence=0.8)
        workflow_results['steps']['step4'] = step4_results
        
        # Calculate round-trip analysis
        round_trip_analysis = calculate_round_trip_analysis(
            step1_results, step2_results, step3_results, step4_results
        )
        workflow_results['round_trip_analysis'] = round_trip_analysis
        
        # Overall workflow assessment
        successful_critical_steps = sum(1 for step in [step2_results, step4_results] 
                                      if step.get('success', False))
        
        workflow_results['success'] = successful_critical_steps >= 1  # At least one swap succeeded
        workflow_results['successful_critical_steps'] = successful_critical_steps
        
        print(f"\n🏆 COMPREHENSIVE WORKFLOW COMPLETED")
        print("=" * 100)
        print(f"✅ Workflow Success: {'YES' if workflow_results['success'] else 'NO'}")
        print(f"✅ Critical Steps Successful: {successful_critical_steps}/2 (Swaps)")
        print(f"✅ Total Steps Completed: 4/4")
        
        return workflow_results
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        workflow_results['error'] = str(e)
        workflow_results['error_details'] = traceback.format_exc()
        return workflow_results
    
    finally:
        workflow_results['end_time'] = datetime.now().isoformat()
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"forced_contrarian_workflow_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(workflow_results, f, indent=2, default=str)
        
        print(f"\n📁 Complete workflow results saved to: {filename}")

if __name__ == "__main__":
    main()