#!/usr/bin/env python3
"""
DEBUG DEBT SWAP EXECUTION
Identify the specific issue causing gas estimation failure
"""

from production_debt_swap_executor import ProductionDebtSwapExecutor

def main():
    print("🔍 DEBUGGING DEBT SWAP EXECUTION")
    print("=" * 60)
    
    try:
        executor = ProductionDebtSwapExecutor()
        
        # Test the components step by step
        print("\n1. Testing Position Validation...")
        position = executor.get_aave_position()
        print(f"   ✅ Position: ${position['total_debt_usd']:.2f} debt, HF: {position['health_factor']:.3f}")
        
        print("\n2. Testing Debt Token Address...")
        arb_debt_token = executor.get_debt_token_address('ARB')
        print(f"   ✅ ARB debt token: {arb_debt_token}")
        
        print("\n3. Testing ParaSwap Integration...")
        amount_wei = int(2.0 * 1e18)  # $2 worth
        paraswap_data = executor.get_paraswap_calldata('DAI', 'ARB', amount_wei)
        
        if paraswap_data:
            print(f"   ✅ ParaSwap calldata: {len(paraswap_data['calldata'])} chars")
            print(f"   Expected amount: {paraswap_data['expected_amount']}")
        else:
            print("   ❌ ParaSwap failed")
            return
        
        print("\n4. Testing Credit Delegation Permit...")
        permit = executor.create_credit_delegation_permit(arb_debt_token)
        
        if permit:
            print(f"   ✅ Permit created, deadline: {permit['deadline']}")
        else:
            print("   ❌ Permit creation failed")
            return
        
        print("\n5. Testing Transaction Building...")
        
        # Build the contract call manually for debugging
        debt_swap_contract = executor.w3.eth.contract(
            address=executor.paraswap_debt_swap_adapter,
            abi=executor.debt_swap_abi
        )
        
        # Use exact amount from ParaSwap
        amount_to_swap = int(paraswap_data['expected_amount'])
        
        print(f"   Asset from: {executor.tokens['DAI']}")
        print(f"   Asset to: {executor.tokens['ARB']}")
        print(f"   Amount to swap: {amount_to_swap}")
        print(f"   ParaSwap data length: {len(paraswap_data['calldata'])} chars")
        
        # Test contract function call construction
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
            print("   ✅ Function call constructed")
            
            # Test gas estimation with detailed error handling
            try:
                print("   Testing gas estimation...")
                gas_estimate = function_call.estimate_gas({'from': executor.user_address})
                print(f"   ✅ Gas estimate: {gas_estimate:,}")
                
            except Exception as gas_error:
                print(f"   ❌ Gas estimation failed: {gas_error}")
                
                # Try eth_call for more detailed error
                try:
                    tx_data = function_call.build_transaction({
                        'from': executor.user_address,
                        'gas': 1000000,
                        'gasPrice': executor.w3.eth.gas_price,
                        'nonce': executor.w3.eth.get_transaction_count(executor.user_address)
                    })
                    
                    print("   Testing with eth_call...")
                    call_result = executor.w3.eth.call({
                        'to': tx_data['to'],
                        'from': tx_data['from'],
                        'data': tx_data['data'],
                        'gas': 1000000
                    })
                    print(f"   ✅ eth_call succeeded: {call_result.hex()}")
                    
                except Exception as call_error:
                    print(f"   ❌ eth_call failed: {call_error}")
                    
                    # Try to decode the revert reason
                    revert_reason = executor.decode_revert_reason(str(call_error))
                    print(f"   Decoded revert: {revert_reason}")
                    
        except Exception as build_error:
            print(f"   ❌ Function call construction failed: {build_error}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()