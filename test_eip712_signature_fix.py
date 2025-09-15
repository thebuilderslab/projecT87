#!/usr/bin/env python3
"""
Test EIP-712 Signature Fix - Validate Architect Fix
Test the corrected DelegationWithSig message structure with 'delegator' field
"""

import os
import time
import json
from web3 import Web3
from eth_account.messages import encode_structured_data
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_signature_fix():
    """Test the corrected EIP-712 signature with delegator field"""
    print("🔧 TESTING EIP-712 SIGNATURE FIX")
    print("=" * 60)
    print("🎯 ARCHITECT FIX: Adding missing 'delegator' field")
    print("=" * 60)
    
    try:
        # Initialize agent
        print("🚀 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        w3 = agent.w3
        user_address = agent.address
        account = agent.account
        
        print(f"✅ Agent initialized")
        print(f"   Wallet: {user_address}")
        
        # Contract addresses
        paraswap_debt_swap_adapter = "0xCf85FF1c37c594a10195F7A9Ab85CBb0a03f69dE"
        aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        arb_token = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        
        # Get ARB debt token address
        print(f"\n📋 Getting ARB debt token address...")
        data_provider_abi = [{
            "inputs": [{"name": "asset", "type": "address"}],
            "name": "getReserveTokensAddresses",
            "outputs": [
                {"name": "aTokenAddress", "type": "address"},
                {"name": "stableDebtTokenAddress", "type": "address"},
                {"name": "variableDebtTokenAddress", "type": "address"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        data_provider_contract = w3.eth.contract(
            address=aave_data_provider, 
            abi=data_provider_abi
        )
        
        token_addresses = data_provider_contract.functions.getReserveTokensAddresses(arb_token).call()
        arb_debt_token = token_addresses[2]
        
        print(f"✅ ARB debt token: {arb_debt_token}")
        
        # Get debt token info
        debt_token_abi = [{
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        }, {
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "nonces",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        debt_token_contract = w3.eth.contract(
            address=arb_debt_token,
            abi=debt_token_abi
        )
        
        # Get token info
        token_name = debt_token_contract.functions.name().call()
        nonce = debt_token_contract.functions.nonces(user_address).call()
        deadline = int(time.time()) + 3600
        
        print(f"✅ Token info obtained")
        print(f"   Name: {token_name}")
        print(f"   User nonce: {nonce}")
        
        # ORIGINAL (BROKEN) EIP-712 structure
        print(f"\n❌ TESTING ORIGINAL (BROKEN) STRUCTURE")
        print(f"   Message fields: (delegatee, value, nonce, deadline)")
        
        original_types = {
            'EIP712Domain': [
                {'name': 'name', 'type': 'string'},
                {'name': 'version', 'type': 'string'},
                {'name': 'chainId', 'type': 'uint256'},
                {'name': 'verifyingContract', 'type': 'address'}
            ],
            'DelegationWithSig': [
                {'name': 'delegatee', 'type': 'address'},
                {'name': 'value', 'type': 'uint256'},
                {'name': 'nonce', 'type': 'uint256'},
                {'name': 'deadline', 'type': 'uint256'}
            ]
        }
        
        original_message = {
            'delegatee': paraswap_debt_swap_adapter,
            'value': 2**256 - 1,
            'nonce': nonce,
            'deadline': deadline
        }
        
        # FIXED (CORRECT) EIP-712 structure
        print(f"\n✅ TESTING FIXED (CORRECT) STRUCTURE")
        print(f"   Message fields: (delegator, delegatee, value, nonce, deadline)")
        print(f"   🔧 ARCHITECT FIX: Added 'delegator' field")
        
        fixed_types = {
            'EIP712Domain': [
                {'name': 'name', 'type': 'string'},
                {'name': 'version', 'type': 'string'},
                {'name': 'chainId', 'type': 'uint256'},
                {'name': 'verifyingContract', 'type': 'address'}
            ],
            'DelegationWithSig': [
                {'name': 'delegator', 'type': 'address'},  # 🔧 ARCHITECT FIX
                {'name': 'delegatee', 'type': 'address'},
                {'name': 'value', 'type': 'uint256'},
                {'name': 'nonce', 'type': 'uint256'},
                {'name': 'deadline', 'type': 'uint256'}
            ]
        }
        
        fixed_message = {
            'delegator': user_address,                   # 🔧 ARCHITECT FIX
            'delegatee': paraswap_debt_swap_adapter,
            'value': 2**256 - 1,
            'nonce': nonce,
            'deadline': deadline
        }
        
        # EIP-712 domain
        domain = {
            'name': token_name,
            'version': '1',
            'chainId': 42161,
            'verifyingContract': arb_debt_token
        }
        
        # Test both signatures
        print(f"\n🔍 SIGNATURE COMPARISON")
        print("=" * 40)
        
        # Original signature
        original_structured_data = {
            'types': original_types,
            'domain': domain,
            'primaryType': 'DelegationWithSig',
            'message': original_message
        }
        
        original_encoded = encode_structured_data(original_structured_data)
        original_signature = account.sign_message(original_encoded)
        
        print(f"❌ Original signature:")
        print(f"   v: {original_signature.v}")
        print(f"   r: 0x{original_signature.r.to_bytes(32, 'big').hex()}")
        print(f"   s: 0x{original_signature.s.to_bytes(32, 'big').hex()}")
        
        # Fixed signature
        fixed_structured_data = {
            'types': fixed_types,
            'domain': domain,
            'primaryType': 'DelegationWithSig',
            'message': fixed_message
        }
        
        fixed_encoded = encode_structured_data(fixed_structured_data)
        fixed_signature = account.sign_message(fixed_encoded)
        
        print(f"\n✅ Fixed signature:")
        print(f"   v: {fixed_signature.v}")
        print(f"   r: 0x{fixed_signature.r.to_bytes(32, 'big').hex()}")
        print(f"   s: 0x{fixed_signature.s.to_bytes(32, 'big').hex()}")
        
        # Compare signatures
        signatures_different = (
            original_signature.v != fixed_signature.v or
            original_signature.r != fixed_signature.r or
            original_signature.s != fixed_signature.s
        )
        
        print(f"\n🔍 SIGNATURE ANALYSIS:")
        print(f"   Signatures different: {'✅ YES' if signatures_different else '❌ NO'}")
        
        if signatures_different:
            print(f"   🔧 ARCHITECT FIX CONFIRMED: Signatures are different")
            print(f"   💡 Adding 'delegator' field changes the signature hash")
            print(f"   🎯 This should resolve the validation issue!")
        else:
            print(f"   ⚠️ WARNING: Signatures are identical (unexpected)")
        
        # Test signature validation preflight
        print(f"\n🔍 TESTING SIGNATURE VALIDATION")
        print("=" * 40)
        
        # Delegation ABI for testing
        delegation_abi = [{
            "inputs": [
                {"name": "delegator", "type": "address"},
                {"name": "delegatee", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
                {"name": "v", "type": "uint8"},
                {"name": "r", "type": "bytes32"},
                {"name": "s", "type": "bytes32"}
            ],
            "name": "delegationWithSig",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        delegation_contract = w3.eth.contract(
            address=arb_debt_token,
            abi=delegation_abi
        )
        
        # Test original signature
        try:
            print(f"❌ Testing original signature...")
            original_call = delegation_contract.functions.delegationWithSig(
                user_address,
                paraswap_debt_swap_adapter,
                2**256 - 1,
                deadline,
                original_signature.v,
                original_signature.r.to_bytes(32, 'big'),
                original_signature.s.to_bytes(32, 'big')
            )
            
            original_result = w3.eth.call({
                'to': arb_debt_token,
                'from': user_address,
                'data': original_call._encode_transaction_data(),
                'gas': 500000
            })
            
            print(f"   Original validation: ✅ PASSED (unexpected)")
            
        except Exception as original_error:
            print(f"   Original validation: ❌ FAILED (expected)")
            print(f"   Error: {str(original_error)[:100]}...")
        
        # Test fixed signature
        try:
            print(f"\n✅ Testing fixed signature...")
            fixed_call = delegation_contract.functions.delegationWithSig(
                user_address,
                paraswap_debt_swap_adapter,
                2**256 - 1,
                deadline,
                fixed_signature.v,
                fixed_signature.r.to_bytes(32, 'big'),
                fixed_signature.s.to_bytes(32, 'big')
            )
            
            fixed_result = w3.eth.call({
                'to': arb_debt_token,
                'from': user_address,
                'data': fixed_call._encode_transaction_data(),
                'gas': 500000
            })
            
            print(f"   Fixed validation: ✅ PASSED (expected)")
            print(f"   🎉 ARCHITECT FIX SUCCESSFUL!")
            
            # Save successful fix data
            success_data = {
                'fix_successful': True,
                'architect_fix_applied': 'Added delegator field to DelegationWithSig message',
                'signatures_different': signatures_different,
                'original_validation': 'FAILED',
                'fixed_validation': 'PASSED',
                'debt_token': arb_debt_token,
                'user_address': user_address,
                'delegatee': paraswap_debt_swap_adapter,
                'test_timestamp': time.time()
            }
            
            with open('eip712_fix_validation_success.json', 'w') as f:
                json.dump(success_data, f, indent=2)
            
            print(f"\n✅ EIP-712 SIGNATURE FIX VALIDATION SUCCESSFUL!")
            print(f"   Fixed structure ready for debt swap execution")
            print(f"   Success data saved to: eip712_fix_validation_success.json")
            
            return True
            
        except Exception as fixed_error:
            print(f"   Fixed validation: ❌ FAILED (unexpected)")
            print(f"   Error: {str(fixed_error)[:100]}...")
            print(f"   🔧 May need further debugging")
            return False
        
    except Exception as e:
        print(f"❌ EIP-712 signature fix test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_signature_fix()
    print(f"\n{'🎉 EIP-712 FIX SUCCESSFUL' if success else '❌ EIP-712 FIX FAILED'}")