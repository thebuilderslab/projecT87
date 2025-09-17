#!/usr/bin/env python3
"""
Verify ARB Token Approval to ParaSwap
"""

from production_debt_swap_executor import ProductionDebtSwapExecutor

def main():
    executor = ProductionDebtSwapExecutor()
    
    print('🔍 VERIFYING ARB TOKEN APPROVAL')
    print('=' * 32)
    
    # Contract details
    arb_token = '0x912ce59144191c1204e64559fe8253a0e49e6548'
    paraswap_router = '0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57'
    
    erc20_abi = [
        {
            'inputs': [
                {'name': 'owner', 'type': 'address'},
                {'name': 'spender', 'type': 'address'}
            ],
            'name': 'allowance',
            'outputs': [{'name': '', 'type': 'uint256'}],
            'stateMutability': 'view',
            'type': 'function'
        }
    ]
    
    try:
        arb_contract = executor.w3.eth.contract(
            address=executor.w3.to_checksum_address(arb_token),
            abi=erc20_abi
        )
        
        allowance = arb_contract.functions.allowance(
            executor.user_address,
            paraswap_router
        ).call()
        
        allowance_arb = allowance / 1e18
        
        print(f'Wallet: {executor.user_address}')
        print(f'ARB Token: {arb_token}')
        print(f'ParaSwap Router: {paraswap_router}')
        print(f'Current Allowance: {allowance_arb:.6f} ARB')
        print()
        
        if allowance_arb >= 55:
            print('✅ SUCCESS: ARB approval confirmed!')
            print('✅ You can now retry the debt swap')
            print()
            print('NEXT STEPS:')
            print('1. Run the debt swap test again')
            print('2. The transaction should succeed this time')
        else:
            print('❌ INCOMPLETE: Approval not sufficient')
            print(f'❌ Need at least 55 ARB, you have {allowance_arb:.6f}')
            print('💡 Please complete the approval process first')
            
    except Exception as e:
        print(f'Error checking approval: {e}')

if __name__ == "__main__":
    main()