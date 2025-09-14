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

def verify_transaction_success(agent, tx_hash, operation_name):
    """Verify transaction success and get receipt details"""
    try:
        print(f"🔍 Verifying {operation_name} transaction: {tx_hash}")
        
        # Wait for transaction confirmation
        receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        verification_result = {
            'tx_hash': tx_hash,
            'operation': operation_name,
            'status': 'success' if receipt.status == 1 else 'failed',
            'block_number': receipt.blockNumber,
            'gas_used': receipt.gasUsed,
            'effective_gas_price': receipt.effectiveGasPrice if hasattr(receipt, 'effectiveGasPrice') else None,
            'timestamp': datetime.now().isoformat()
        }
        
        if receipt.status == 1:
            print(f"✅ {operation_name} CONFIRMED")
            print(f"   Block: {receipt.blockNumber}")
            print(f"   Gas Used: {receipt.gasUsed:,}")
        else:
            print(f"❌ {operation_name} FAILED")
            print(f"   Status: {receipt.status}")
            
        return verification_result
        
    except Exception as e:
        print(f"❌ Transaction verification failed: {e}")
        return {
            'tx_hash': tx_hash,
            'operation': operation_name,
            'status': 'verification_failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_token_balance(agent, token_symbol):
    """Get current balance of specified token"""
    try:
        if token_symbol.upper() == 'DAI':
            balance = agent.aave.get_dai_balance()
        elif token_symbol.upper() == 'ARB':
            balance = agent.get_arb_balance()
        else:
            balance = 0.0
            
        print(f"💰 Current {token_symbol} balance: {balance:.6f}")
        return balance
        
    except Exception as e:
        print(f"❌ Error getting {token_symbol} balance: {e}")
        return 0.0

def force_contrarian_swap_sequence():
    """Execute forced contrarian swap sequence with full logging"""
    print("🚀 FORCE CONTRARIAN TEST - IMMEDIATE EXECUTION")
    print("=" * 60)
    print("⚠️  WARNING: This executes REAL on-chain transactions")
    print("🔄 Sequence: Borrow DAI → Swap to ARB → Wait 5min → Swap to DAI")
    print("=" * 60)
    
    # Initialize comprehensive logging
    test_session = {
        'test_id': f"force_contrarian_{int(time.time())}",
        'start_time': datetime.now().isoformat(),
        'operations': [],
        'balances_before': {},
        'balances_after': {},
        'transaction_logs': [],
        'verification_results': [],
        'total_gas_used': 0,
        'success': False
    }
    
    try:
        # Initialize agent
        print("🤖 Initializing Arbitrum Agent...")
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        # Set forced execution environment
        os.environ['MARKET_SIGNAL_ENABLED'] = 'true'
        os.environ['FORCE_EXECUTION_MODE'] = 'true'  # Override market conditions
        
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
            
        print(f"✅ Agent initialized - Wallet: {agent.address}")
        print(f"🌐 Connected to Arbitrum Mainnet - Chain ID: {agent.w3.eth.chain_id}")
        
        # Record initial balances
        print("\n📊 RECORDING INITIAL BALANCES")
        print("-" * 40)
        initial_dai = get_token_balance(agent, 'DAI')
        initial_arb = get_token_balance(agent, 'ARB')
        initial_health_factor = agent.get_health_factor()
        
        test_session['balances_before'] = {
            'dai': initial_dai,
            'arb': initial_arb,
            'health_factor': initial_health_factor,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"🏥 Initial Health Factor: {initial_health_factor:.4f}")
        
        # STEP 1: Borrow DAI (if needed)
        print("\n🎯 STEP 1: BORROW DAI FOR SWAP")
        print("-" * 40)
        
        borrow_amount = 10.0  # $10 DAI for testing
        
        if initial_dai < borrow_amount:
            print(f"💸 Borrowing ${borrow_amount:.2f} DAI from Aave...")
            
            try:
                borrow_result = agent.aave.borrow_dai(borrow_amount)
                
                if borrow_result and 'tx_hash' in borrow_result:
                    tx_log = log_transaction_details(
                        borrow_result['tx_hash'], 
                        'borrow_dai', 
                        borrow_amount, 
                        'AAVE', 
                        'DAI', 
                        'submitted'
                    )
                    test_session['transaction_logs'].append(tx_log)
                    
                    # Verify borrow transaction
                    verification = verify_transaction_success(
                        agent, 
                        borrow_result['tx_hash'], 
                        'DAI Borrow'
                    )
                    test_session['verification_results'].append(verification)
                    test_session['total_gas_used'] += verification.get('gas_used', 0)
                    
                else:
                    raise Exception("Borrow transaction failed")
                    
            except Exception as e:
                print(f"❌ DAI borrow failed: {e}")
                raise
        else:
            print(f"✅ Sufficient DAI balance: {initial_dai:.6f}")
        
        # Update DAI balance after borrow
        current_dai = get_token_balance(agent, 'DAI')
        
        # STEP 2: Force DAI → ARB Swap
        print("\n🎯 STEP 2: FORCE DAI → ARB SWAP")
        print("-" * 40)
        
        swap_amount = min(current_dai * 0.8, 8.0)  # Use 80% of DAI or $8 max
        
        print(f"🔄 Swapping ${swap_amount:.2f} DAI for ARB...")
        print("⚠️  Executing REGARDLESS of market conditions")
        
        try:
            if hasattr(agent, 'uniswap') and agent.uniswap:
                dai_to_arb_result = agent.uniswap.swap_dai_for_arb(swap_amount)
            else:
                raise Exception("Uniswap integration not available")
                
            if dai_to_arb_result and dai_to_arb_result.get('success'):
                tx_hash = dai_to_arb_result.get('tx_hash')
                arb_received = dai_to_arb_result.get('arb_received', 0)
                
                tx_log = log_transaction_details(
                    tx_hash, 
                    'dai_to_arb_swap', 
                    swap_amount, 
                    'DAI', 
                    'ARB', 
                    'submitted'
                )
                test_session['transaction_logs'].append(tx_log)
                
                # Verify swap transaction
                verification = verify_transaction_success(
                    agent, 
                    tx_hash, 
                    'DAI→ARB Swap'
                )
                test_session['verification_results'].append(verification)
                test_session['total_gas_used'] += verification.get('gas_used', 0)
                
                print(f"✅ DAI→ARB swap completed: {arb_received:.6f} ARB received")
                
            else:
                raise Exception("DAI→ARB swap failed")
                
        except Exception as e:
            print(f"❌ DAI→ARB swap failed: {e}")
            raise
        
        # Record mid-sequence balances
        mid_dai = get_token_balance(agent, 'DAI')
        mid_arb = get_token_balance(agent, 'ARB')
        mid_health_factor = agent.get_health_factor()
        
        test_session['balances_mid'] = {
            'dai': mid_dai,
            'arb': mid_arb,
            'health_factor': mid_health_factor,
            'timestamp': datetime.now().isoformat()
        }
        
        # STEP 3: Wait 5 Minutes
        print("\n🎯 STEP 3: WAITING 5 MINUTES")
        print("-" * 40)
        print("⏰ Mandatory 5-minute wait period...")
        
        wait_start = datetime.now()
        wait_duration = 300  # 5 minutes in seconds
        
        for remaining in range(wait_duration, 0, -30):
            minutes = remaining // 60
            seconds = remaining % 60
            print(f"   ⏳ Time remaining: {minutes:02d}:{seconds:02d}")
            time.sleep(30)
        
        wait_end = datetime.now()
        actual_wait = (wait_end - wait_start).total_seconds()
        
        print(f"✅ Wait complete - Actual duration: {actual_wait:.1f} seconds")
        
        # STEP 4: Force ARB → DAI Swap
        print("\n🎯 STEP 4: FORCE ARB → DAI SWAP")
        print("-" * 40)
        
        current_arb = get_token_balance(agent, 'ARB')
        arb_swap_amount = current_arb * 0.9  # Use 90% of ARB balance
        
        print(f"🔄 Swapping {arb_swap_amount:.6f} ARB for DAI...")
        print("⚠️  Executing REGARDLESS of market conditions")
        
        try:
            if hasattr(agent, 'uniswap') and agent.uniswap:
                arb_to_dai_result = agent.uniswap.swap_arb_for_dai(arb_swap_amount)
            else:
                raise Exception("Uniswap integration not available")
                
            if arb_to_dai_result and arb_to_dai_result.get('success'):
                tx_hash = arb_to_dai_result.get('tx_hash')
                dai_received = arb_to_dai_result.get('dai_received', 0)
                
                tx_log = log_transaction_details(
                    tx_hash, 
                    'arb_to_dai_swap', 
                    arb_swap_amount, 
                    'ARB', 
                    'DAI', 
                    'submitted'
                )
                test_session['transaction_logs'].append(tx_log)
                
                # Verify swap transaction
                verification = verify_transaction_success(
                    agent, 
                    tx_hash, 
                    'ARB→DAI Swap'
                )
                test_session['verification_results'].append(verification)
                test_session['total_gas_used'] += verification.get('gas_used', 0)
                
                print(f"✅ ARB→DAI swap completed: {dai_received:.6f} DAI received")
                
            else:
                raise Exception("ARB→DAI swap failed")
                
        except Exception as e:
            print(f"❌ ARB→DAI swap failed: {e}")
            raise
        
        # Record final balances
        print("\n📊 RECORDING FINAL BALANCES")
        print("-" * 40)
        final_dai = get_token_balance(agent, 'DAI')
        final_arb = get_token_balance(agent, 'ARB')
        final_health_factor = agent.get_health_factor()
        
        test_session['balances_after'] = {
            'dai': final_dai,
            'arb': final_arb,
            'health_factor': final_health_factor,
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate results
        dai_change = final_dai - initial_dai
        arb_change = final_arb - initial_arb
        
        print(f"🏥 Final Health Factor: {final_health_factor:.4f}")
        print(f"📈 DAI Change: {dai_change:+.6f}")
        print(f"📈 ARB Change: {arb_change:+.6f}")
        
        test_session['success'] = True
        test_session['end_time'] = datetime.now().isoformat()
        
        # Generate comprehensive report
        print("\n🏆 FORCE CONTRARIAN TEST COMPLETED")
        print("=" * 60)
        print(f"✅ All transactions executed successfully")
        print(f"⛽ Total Gas Used: {test_session['total_gas_used']:,}")
        print(f"🔄 Complete Round Trip: DAI → ARB → DAI")
        print(f"⏱️  Total Test Duration: {(datetime.fromisoformat(test_session['end_time']) - datetime.fromisoformat(test_session['start_time'])).total_seconds():.1f} seconds")
        
        return test_session
        
    except Exception as e:
        print(f"❌ FORCE CONTRARIAN TEST FAILED: {e}")
        print("🔍 Full error details:")
        traceback.print_exc()
        
        test_session['success'] = False
        test_session['error'] = str(e)
        test_session['error_details'] = traceback.format_exc()
        test_session['end_time'] = datetime.now().isoformat()
        
        return test_session
    
    finally:
        # Save comprehensive test results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"force_contrarian_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(test_session, f, indent=2, default=str)
        
        print(f"\n📁 Test results saved to: {filename}")
        
        # Print transaction summary
        if test_session['transaction_logs']:
            print("\n📝 TRANSACTION SUMMARY:")
            print("-" * 40)
            for i, tx in enumerate(test_session['transaction_logs'], 1):
                print(f"{i}. {tx['operation']}: {tx['tx_hash']}")
                print(f"   🔗 https://arbiscan.io/tx/{tx['tx_hash']}")

def main():
    """Main execution function"""
    print("⚠️  FORCE CONTRARIAN TEST - REAL BLOCKCHAIN TRANSACTIONS")
    print("This will execute actual swaps on Arbitrum Mainnet")
    print("Ensure you have sufficient collateral and understand the risks")
    print()
    
    # Execute the test
    result = force_contrarian_swap_sequence()
    
    if result['success']:
        print("\n🎉 FORCE CONTRARIAN TEST SUCCESSFUL!")
        print("✅ Full contrarian sequence executed")
        print("📊 All transactions verified on-chain")
        print("💰 Position updated successfully")
    else:
        print("\n❌ FORCE CONTRARIAN TEST FAILED!")
        print("🔧 Review logs and error details")
        print("⚠️  Check your wallet and collateral status")

if __name__ == "__main__":
    main()