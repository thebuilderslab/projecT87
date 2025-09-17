#!/usr/bin/env python3
"""
Check and approve credit delegation for ARB debt token
"""

import os
import sys

def check_credit_delegation():
    """Check current credit delegation and approve if needed"""
    
    print("🔍 CREDIT DELEGATION CHECK & APPROVAL")
    print("=" * 60)
    
    try:
        # Import agent
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        print("⏳ Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        print(f"✅ Agent ready: {agent.address}")
        
        # Step 1: Get ARB token addresses from protocol data provider
        print(f"\n📊 STEP 1: Get ARB Token Addresses")
        
        data_provider_abi = [{
            'inputs': [{'name': 'asset', 'type': 'address'}],
            'name': 'getReserveTokensAddresses',
            'outputs': [
                {'name': 'aTokenAddress', 'type': 'address'},
                {'name': 'stableDebtTokenAddress', 'type': 'address'},
                {'name': 'variableDebtTokenAddress', 'type': 'address'}
            ],
            'stateMutability': 'view',
            'type': 'function'
        }]
        
        data_provider = agent.w3.eth.contract(
            address='0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654',
            abi=data_provider_abi
        )
        
        arb_underlying = '0x912CE59144191C1204E64559FE8253a0e49E6548'  # ARB token
        debt_swap_adapter = '0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4'
        
        token_addresses = data_provider.functions.getReserveTokensAddresses(arb_underlying).call()
        
        arb_a_token = token_addresses[0]
        arb_stable_debt = token_addresses[1]
        arb_variable_debt = token_addresses[2]
        
        print(f"   ARB underlying: {arb_underlying}")
        print(f"   ARB aToken: {arb_a_token}")
        print(f"   ARB stable debt: {arb_stable_debt}")
        print(f"   ARB variable debt: {arb_variable_debt}")
        
        # Step 2: Check current credit delegation allowance
        print(f"\n📊 STEP 2: Check Current Credit Delegation")
        
        delegation_abi = [{
            'inputs': [
                {'name': 'delegator', 'type': 'address'},
                {'name': 'delegatee', 'type': 'address'}
            ],
            'name': 'borrowAllowance',
            'outputs': [{'name': '', 'type': 'uint256'}],
            'stateMutability': 'view',
            'type': 'function'
        }, {
            'inputs': [
                {'name': 'delegatee', 'type': 'address'},
                {'name': 'amount', 'type': 'uint256'}
            ],
            'name': 'approveDelegation',
            'outputs': [],
            'stateMutability': 'nonpayable',
            'type': 'function'
        }]
        
        arb_debt_contract = agent.w3.eth.contract(
            address=arb_variable_debt,
            abi=delegation_abi
        )
        
        current_allowance = arb_debt_contract.functions.borrowAllowance(
            agent.address,      # delegator (our agent)
            debt_swap_adapter   # delegatee (debt swap adapter)
        ).call()
        
        allowance_eth = current_allowance / 1e18
        print(f"   Current allowance: {allowance_eth:.6f} ARB")
        
        # Step 3: Approve credit delegation if needed
        if current_allowance < agent.w3.to_wei(100, 'ether'):  # If less than 100 ARB allowance
            print(f"\n🔧 STEP 3: Approve Credit Delegation")
            print(f"   Approving 1000 ARB credit delegation...")
            
            # Approve 1000 ARB delegation
            approval_amount = agent.w3.to_wei(1000, 'ether')
            
            approve_tx = arb_debt_contract.functions.approveDelegation(
                debt_swap_adapter,
                approval_amount
            ).build_transaction({
                'from': agent.address,
                'gas': 200000,
                'gasPrice': agent.w3.eth.gas_price,
                'nonce': agent.w3.eth.get_transaction_count(agent.address)
            })
            
            print(f"   Signing transaction...")
            signed_tx = agent.w3.eth.account.sign_transaction(approve_tx, agent.private_key)
            
            print(f"   Sending transaction...")
            tx_hash = agent.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"   ✅ Transaction sent: {tx_hash.hex()}")
            print(f"   🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
            
            # Wait for confirmation
            print(f"   ⏳ Waiting for confirmation...")
            receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                print(f"   ✅ Credit delegation approved successfully!")
                
                # Verify new allowance
                new_allowance = arb_debt_contract.functions.borrowAllowance(
                    agent.address,
                    debt_swap_adapter
                ).call()
                
                new_allowance_eth = new_allowance / 1e18
                print(f"   New allowance: {new_allowance_eth:.6f} ARB")
                
                return True
            else:
                print(f"   ❌ Credit delegation failed!")
                return False
        else:
            print(f"   ✅ Credit delegation already sufficient: {allowance_eth:.6f} ARB")
            return True
        
    except Exception as e:
        print(f"❌ Credit delegation check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_credit_delegation()
    
    if success:
        print(f"\n✅ CREDIT DELEGATION: READY")
        print(f"Debt swap adapter has permission to create ARB debt")
    else:
        print(f"\n❌ CREDIT DELEGATION: FAILED")
        print(f"Need to fix credit delegation before debt swap")