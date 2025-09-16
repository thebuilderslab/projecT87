#!/usr/bin/env python3
"""
ONCHAIN ACTIVITY TEST
Test EIP-712 signature and debt token interaction to generate real blockchain activity
"""

import os
import time
from web3 import Web3
from eth_account.messages import encode_structured_data

def test_onchain_signature_validation():
    """Test EIP-712 signature validation with real on-chain call"""
    
    print("🧪 TESTING ONCHAIN EIP-712 SIGNATURE VALIDATION")
    print("=" * 60)
    
    # Setup Web3
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("❌ PRIVATE_KEY not found")
        return False
    
    w3 = Web3(Web3.HTTPProvider("https://arbitrum-one.public.blastapi.io"))
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return False
    
    account = w3.eth.account.from_key(private_key)
    user_address = account.address
    
    print(f"✅ Connected to Arbitrum")
    print(f"   User: {user_address}")
    print(f"   Block: {w3.eth.block_number}")
    
    # ARB debt token address
    arb_debt_token = "0x44705f578135cC5d703b4c9c122528C73Eb87145"
    adapter_address = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
    
    print(f"   ARB Debt Token: {arb_debt_token}")
    print(f"   Adapter: {adapter_address}")
    
    try:
        # Test 1: Check current nonce (real on-chain read)
        debt_token_abi = [
            {"inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "owner", "type": "address"}], "name": "nonces", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "borrowAllowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
        ]
        
        debt_token_contract = w3.eth.contract(address=arb_debt_token, abi=debt_token_abi)
        
        print(f"\n📊 ONCHAIN READS:")
        token_name = debt_token_contract.functions.name().call()
        current_nonce = debt_token_contract.functions.nonces(user_address).call()
        current_allowance = debt_token_contract.functions.borrowAllowance(user_address, adapter_address).call()
        
        print(f"   Token Name: {token_name}")
        print(f"   User Nonce: {current_nonce}")
        print(f"   Current Allowance: {current_allowance}")
        
        # Test 2: Create valid EIP-712 signature
        print(f"\n📝 CREATING EIP-712 SIGNATURE:")
        
        deadline = int(time.time()) + 3600
        
        domain = {
            'name': token_name,
            'version': '1', 
            'chainId': 42161,
            'verifyingContract': arb_debt_token
        }
        
        types = {
            'EIP712Domain': [
                {'name': 'name', 'type': 'string'},
                {'name': 'version', 'type': 'string'},
                {'name': 'chainId', 'type': 'uint256'},
                {'name': 'verifyingContract', 'type': 'address'}
            ],
            'DelegationWithSig': [
                {'name': 'delegator', 'type': 'address'},
                {'name': 'delegatee', 'type': 'address'},
                {'name': 'value', 'type': 'uint256'},
                {'name': 'nonce', 'type': 'uint256'},
                {'name': 'deadline', 'type': 'uint256'}
            ]
        }
        
        message = {
            'delegator': user_address,
            'delegatee': adapter_address,
            'value': 1000000000000000000,  # 1 token allowance for testing
            'nonce': current_nonce,
            'deadline': deadline
        }
        
        structured_data = {'types': types, 'domain': domain, 'primaryType': 'DelegationWithSig', 'message': message}
        encoded_data = encode_structured_data(structured_data)
        signature = account.sign_message(encoded_data)
        
        print(f"   ✅ Signature created successfully!")
        
        # Test 3: Validate signature with on-chain call (this generates activity!)
        print(f"\n⚡ TESTING ONCHAIN SIGNATURE VALIDATION:")
        
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
        
        delegation_contract = w3.eth.contract(address=arb_debt_token, abi=delegation_abi)
        
        # Test signature validation with eth_call (no gas cost)
        try:
            w3.eth.call({
                'to': arb_debt_token,
                'from': user_address,
                'data': delegation_contract.functions.delegationWithSig(
                    user_address,
                    adapter_address, 
                    1000000000000000000,
                    deadline,
                    signature.v,
                    signature.r.to_bytes(32, 'big'),
                    signature.s.to_bytes(32, 'big')
                )._encode_transaction_data()
            })
            print(f"   ✅ Signature validation passed!")
            
            # Test 4: Send actual transaction for onchain activity
            print(f"\n🚀 SENDING REAL TRANSACTION:")
            
            function_call = delegation_contract.functions.delegationWithSig(
                user_address,
                adapter_address,
                1000000000000000000, 
                deadline,
                signature.v,
                signature.r.to_bytes(32, 'big'),
                signature.s.to_bytes(32, 'big')
            )
            
            gas_estimate = function_call.estimate_gas({'from': user_address})
            print(f"   Gas estimate: {gas_estimate:,}")
            
            transaction = function_call.build_transaction({
                'from': user_address,
                'gas': int(gas_estimate * 1.2),
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(user_address)
            })
            
            signed_tx = account.sign_transaction(transaction)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"   📤 Transaction sent: {tx_hash.hex()}")
            print(f"   🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
            
            print(f"   ⏳ Waiting for confirmation...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            success = receipt['status'] == 1
            print(f"   {'✅ CONFIRMED!' if success else '❌ FAILED!'}")
            print(f"   Block: {receipt['blockNumber']}")
            print(f"   Gas used: {receipt['gasUsed']:,}")
            
            # Verify allowance increased
            new_allowance = debt_token_contract.functions.borrowAllowance(user_address, adapter_address).call()
            print(f"   New allowance: {new_allowance}")
            
            return True
            
        except Exception as e:
            print(f"   ⚠️ Signature validation issue: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_onchain_signature_validation()
    print(f"\n{'🎉 ONCHAIN ACTIVITY GENERATED!' if success else '❌ NO ONCHAIN ACTIVITY'}")