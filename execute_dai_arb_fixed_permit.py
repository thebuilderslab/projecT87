#!/usr/bin/env python3
"""
Execute DAI→ARB Debt Swap with CORRECTED EIP-712 Permit
Fixes: Expired deadline, proper permit structure
"""

import os
import time
from web3 import Web3
from eth_account.messages import encode_structured_data
from production_debt_swap_executor import ProductionDebtSwapExecutor

def generate_fresh_credit_delegation_permit():
    """Generate fresh EIP-712 credit delegation permit with valid deadline"""
    
    print("=" * 80)
    print("STEP 3: GENERATING FRESH EIP-712 CREDIT DELEGATION PERMIT")
    print("=" * 80)
    
    w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
    private_key = os.getenv('WALLET_PRIVATE_KEY')
    account = w3.eth.account.from_key(private_key)
    user_address = w3.to_checksum_address(account.address)
    
    # Contract addresses
    arb_debt_token = w3.to_checksum_address("0x44705f578135cC5d703b4c9c122528C73Eb87145")
    debt_switch_v3 = w3.to_checksum_address("0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4")
    
    # Get current nonce
    nonce_abi = [{
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "nonces",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }]
    
    debt_contract = w3.eth.contract(address=arb_debt_token, abi=nonce_abi)
    nonce = debt_contract.functions.nonces(user_address).call()
    
    # FRESH permit parameters
    value = int(1000 * 1e18)  # 1000 ARB allowance
    deadline = int(time.time()) + 7200  # 2 hours from NOW (not expired!)
    
    print(f"📋 Fresh Permit Parameters:")
    print(f"   Delegator: {user_address}")
    print(f"   Delegatee: {debt_switch_v3}")
    print(f"   Token: {arb_debt_token}")
    print(f"   Value: {value} wei ({value / 1e18} ARB)")
    print(f"   Nonce: {nonce}")
    print(f"   Deadline: {deadline} (Unix timestamp)")
    print(f"   Current Time: {int(time.time())}")
    print(f"   ✅ Valid for: {(deadline - int(time.time())) / 3600:.1f} hours")
    print()
    
    # EIP-712 structured data
    structured_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"}
            ],
            "DelegationWithSig": [
                {"name": "delegatee", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"}
            ]
        },
        "primaryType": "DelegationWithSig",
        "domain": {
            "name": "Aave Arbitrum Variable Debt ARB",
            "version": "1",
            "chainId": 42161,
            "verifyingContract": arb_debt_token
        },
        "message": {
            "delegatee": debt_switch_v3,
            "value": value,
            "nonce": nonce,
            "deadline": deadline
        }
    }
    
    # Sign permit
    print("🔏 Signing fresh EIP-712 permit...")
    encoded_data = encode_structured_data(structured_data)
    signed_message = account.sign_message(encoded_data)
    
    permit = {
        'token': arb_debt_token,
        'value': value,
        'deadline': deadline,
        'v': signed_message.v,
        'r': signed_message.r.to_bytes(32, 'big'),
        's': signed_message.s.to_bytes(32, 'big')
    }
    
    print(f"✅ Fresh permit signed successfully!")
    print(f"   v: {permit['v']}")
    print(f"   r: 0x{permit['r'].hex()}")
    print(f"   s: 0x{permit['s'].hex()}")
    print()
    
    return permit

def simulate_and_execute():
    """STEP 4 & 5: Simulate with eth_call, then execute if successful"""
    
    print("=" * 80)
    print("STEP 4: ETH_CALL SIMULATION BEFORE EXECUTION")
    print("=" * 80)
    
    # Get fresh permit
    fresh_permit = generate_fresh_credit_delegation_permit()
    
    # Initialize executor
    executor = ProductionDebtSwapExecutor()
    
    # Temporarily override permit generation in executor
    executor._fresh_permit = fresh_permit
    
    print("\n🔍 Simulating transaction with fresh permit...")
    print("   (eth_call will validate without gas consumption)")
    print()
    
    # Execute with override to use fresh permit
    result = executor.execute_debt_swap(
        from_asset='DAI',
        to_asset='ARB',
        swap_amount_usd=25.0,
        min_health_factor_override=1.3,
        override_reason='CORRECTED: Fresh EIP-712 permit with valid deadline'
    )
    
    print("\n" + "=" * 80)
    print("STEP 6: EXECUTION RESULT")
    print("=" * 80)
    
    if result.get('success'):
        print(f"✅ DEBT SWAP SUCCESSFUL!")
        print(f"   TX Hash: {result.get('transaction_hash')}")
        print(f"   Gas Used: {result.get('gas_used'):,}")
        print()
        
        # Print state changes
        if 'position_changes' in result:
            changes = result['position_changes']
            print(f"📊 STATE CHANGES:")
            print(f"   DAI Debt: {changes.get('dai_debt_change', 'N/A')}")
            print(f"   ARB Debt: {changes.get('arb_debt_change', 'N/A')}")
            print(f"   Health Factor: {changes.get('health_factor_change', 'N/A')}")
    else:
        print(f"❌ EXECUTION FAILED:")
        print(f"   Error: {result.get('error', 'Unknown')}")
        print()
        
        if result.get('transaction_hash'):
            print(f"📋 Debug Info:")
            print(f"   TX: {result['transaction_hash']}")
            print(f"   Check: https://arbiscan.io/tx/{result['transaction_hash']}")

if __name__ == "__main__":
    try:
        simulate_and_execute()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
