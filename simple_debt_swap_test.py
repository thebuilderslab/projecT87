#!/usr/bin/env python3
"""
SIMPLE DEBT SWAP TEST - Focus on core execution issue
Test with very small amount and detailed error analysis
"""

from production_debt_swap_executor import ProductionDebtSwapExecutor
import json

def test_small_amount():
    """Test with $0.50 to minimize impact and isolate the issue"""
    
    print("🔬 SIMPLE DEBT SWAP TEST - $0.50")
    print("=" * 60)
    
    try:
        executor = ProductionDebtSwapExecutor()
        
        # Test with very small amount
        test_amount = 0.5  # $0.50
        
        print(f"Testing: ${test_amount} DAI debt → ARB debt")
        
        # Get current position
        position_before = executor.get_aave_position()
        print(f"\n📊 BEFORE: DAI debt ${position_before['debt_values_usd']['DAI']:.2f}, Health Factor: {position_before['health_factor']:.3f}")
        
        # Check borrowing capacity for ARB
        available_borrows = position_before['available_borrows_usd']
        print(f"Available borrows: ${available_borrows:.2f}")
        
        if available_borrows < test_amount * 2:  # Need some buffer
            print(f"❌ Insufficient borrowing capacity: ${available_borrows:.2f} < ${test_amount * 2:.2f} needed")
            return
        
        # Get debt token
        arb_debt_token = executor.get_debt_token_address('ARB')
        print(f"ARB debt token: {arb_debt_token}")
        
        # Calculate amount in wei
        amount_wei = int(test_amount * 1e18)  # $0.50 worth of DAI
        
        # Get ParaSwap data
        print(f"\nGetting ParaSwap data for {amount_wei} wei...")
        paraswap_data = executor.get_paraswap_calldata('DAI', 'ARB', amount_wei)
        
        if not paraswap_data:
            print("❌ ParaSwap failed")
            return
        
        # Use ParaSwap expected amount
        amount_to_swap = int(paraswap_data['expected_amount'])
        print(f"Amount to swap: {amount_to_swap} ({amount_to_swap / 1e18:.6f})")
        
        # Create permit
        print(f"\nCreating permit...")
        permit = executor.create_credit_delegation_permit(arb_debt_token)
        
        if not permit:
            print("❌ Permit creation failed")
            return
        
        # Build transaction with detailed logging
        print(f"\nBuilding transaction...")
        debt_swap_contract = executor.w3.eth.contract(
            address=executor.paraswap_debt_swap_adapter,
            abi=executor.debt_swap_abi
        )
        
        print(f"Contract address: {executor.paraswap_debt_swap_adapter}")
        print(f"Asset from (DAI): {executor.tokens['DAI']}")
        print(f"Asset to (ARB): {executor.tokens['ARB']}")
        print(f"Amount to swap: {amount_to_swap}")
        print(f"ParaSwap data: {len(paraswap_data['calldata'])} chars")
        print(f"Permit token: {permit['token']}")
        print(f"Permit delegatee: {permit['delegatee']}")
        print(f"Permit value: {permit['value']}")
        print(f"Permit deadline: {permit['deadline']}")
        
        # Try a different approach - check if we need to delegate credit first
        print(f"\n🔍 CHECKING CREDIT DELEGATION STATUS...")
        
        # Check current delegation (if any)
        delegation_abi = [{
            "inputs": [{"name": "fromUser", "type": "address"}, {"name": "toUser", "type": "address"}],
            "name": "borrowAllowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        try:
            arb_debt_contract = executor.w3.eth.contract(address=arb_debt_token, abi=delegation_abi)
            current_allowance = arb_debt_contract.functions.borrowAllowance(
                executor.user_address, 
                executor.paraswap_debt_swap_adapter
            ).call()
            print(f"Current credit delegation: {current_allowance}")
        except Exception as e:
            print(f"Could not check delegation: {e}")
        
        # Try building the swap transaction
        try:
            function_call = debt_swap_contract.functions.swapDebt(
                executor.tokens['DAI'],               # assetToSwapFrom
                executor.tokens['ARB'],               # assetToSwapTo  
                amount_to_swap,                       # amountToSwap
                bytes.fromhex(paraswap_data['calldata'][2:]),  # paraswapData
                (
                    permit['token'],                  # token
                    permit['delegatee'],              # delegatee
                    permit['value'],                  # value
                    permit['deadline'],               # deadline
                    permit['v'],                      # v
                    permit['r'],                      # r
                    permit['s']                       # s
                )
            )
            
            print("✅ Function call constructed successfully")
            
            # Try gas estimation with error handling
            try:
                gas_estimate = function_call.estimate_gas({
                    'from': executor.user_address,
                    'value': 0
                })
                print(f"✅ Gas estimate successful: {gas_estimate:,}")
                
                # If gas estimation works, try the actual execution
                print(f"\n🚀 EXECUTING TRANSACTION...")
                
                tx_data = function_call.build_transaction({
                    'from': executor.user_address,
                    'gas': int(gas_estimate * 1.2),
                    'gasPrice': executor.w3.eth.gas_price,
                    'nonce': executor.w3.eth.get_transaction_count(executor.user_address)
                })
                
                signed_tx = executor.account.sign_transaction(tx_data)
                tx_hash = executor.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                
                print(f"📡 Transaction sent: {tx_hash.hex()}")
                print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
                
                # Wait for receipt
                receipt = executor.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                
                if receipt['status'] == 1:
                    print(f"✅ SUCCESS! Gas used: {receipt['gasUsed']:,}")
                    
                    # Check position after
                    position_after = executor.get_aave_position()
                    dai_change = position_after['debt_balances']['DAI'] - position_before['debt_balances']['DAI']
                    arb_change = position_after['debt_balances']['ARB'] - position_before['debt_balances']['ARB']
                    
                    print(f"📊 CHANGES:")
                    print(f"   DAI debt: {dai_change:.6f}")
                    print(f"   ARB debt: {arb_change:.6f}")
                    
                    # Save success data
                    result = {
                        'success': True,
                        'tx_hash': tx_hash.hex(),
                        'gas_used': receipt['gasUsed'],
                        'dai_debt_change': dai_change,
                        'arb_debt_change': arb_change
                    }
                    
                    with open('simple_test_success.json', 'w') as f:
                        json.dump(result, f, indent=2)
                    
                    print(f"✅ SIMPLE TEST PASSED!")
                    
                else:
                    print(f"❌ Transaction failed")
                
            except Exception as gas_error:
                print(f"❌ Gas estimation failed: {gas_error}")
                
                # Try to get more specific error information
                if "execution reverted" in str(gas_error):
                    print("Transaction would revert. Possible causes:")
                    print("1. Insufficient collateral for new ARB debt")
                    print("2. Health factor would drop too low")
                    print("3. ParaSwap route not available")
                    print("4. Credit delegation signature invalid")
                    
                    # Check health factor impact
                    arb_price = position_before['prices']['ARB']
                    additional_debt_usd = (amount_to_swap / 1e18) * arb_price
                    new_total_debt = position_before['total_debt_usd'] + additional_debt_usd
                    estimated_hf = position_before['total_collateral_usd'] / new_total_debt if new_total_debt > 0 else float('inf')
                    
                    print(f"Estimated health factor after swap: {estimated_hf:.3f}")
                    if estimated_hf < 1.1:
                        print("❌ Health factor would be too low!")
                
        except Exception as build_error:
            print(f"❌ Function construction failed: {build_error}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_small_amount()