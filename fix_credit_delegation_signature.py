#!/usr/bin/env python3
"""
Comprehensive Credit Delegation Signature Fix
Try multiple EIP-712 formats to find the correct one for Aave V3 ARB debt token
"""

import os
import time
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_structured_data

def try_multiple_signature_formats():
    """Try multiple EIP-712 signature formats for credit delegation"""
    
    print("🔧 COMPREHENSIVE EIP-712 SIGNATURE FORMAT FIX")
    print("=" * 60)
    
    # Setup
    w3 = Web3(Web3.HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU'))
    user_address = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    adapter = "0xCf85FF1c37c594a10195F7A9Ab85CBb0a03f69dE"
    arb_debt_token = "0x44705f578135cC5d703b4c9c122528C73Eb87145"
    private_key = os.getenv('AGENT_PRIVATE_KEY')
    
    if not private_key:
        print("❌ Private key not found")
        return None
    
    account = Account.from_key(private_key)
    deadline = int(time.time()) + 3600
    value = 2**256 - 1
    nonce = 0
    
    # Multiple signature formats to try
    signature_formats = [
        {
            "name": "Standard Aave V3 (Version 1)",
            "domain": {
                'name': 'Aave Arbitrum Variable Debt ARB',
                'version': '1',
                'chainId': 42161,
                'verifyingContract': arb_debt_token
            },
            "primaryType": "DelegationWithSig",
            "types": {
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
            },
            "message": {
                'delegatee': adapter,
                'value': value,
                'nonce': nonce,
                'deadline': deadline
            }
        },
        {
            "name": "Aave V3 with Owner Field",
            "domain": {
                'name': 'Aave Arbitrum Variable Debt ARB',
                'version': '1',
                'chainId': 42161,
                'verifyingContract': arb_debt_token
            },
            "primaryType": "DelegationWithSig",
            "types": {
                'EIP712Domain': [
                    {'name': 'name', 'type': 'string'},
                    {'name': 'version', 'type': 'string'},
                    {'name': 'chainId', 'type': 'uint256'},
                    {'name': 'verifyingContract', 'type': 'address'}
                ],
                'DelegationWithSig': [
                    {'name': 'owner', 'type': 'address'},
                    {'name': 'spender', 'type': 'address'},
                    {'name': 'value', 'type': 'uint256'},
                    {'name': 'nonce', 'type': 'uint256'},
                    {'name': 'deadline', 'type': 'uint256'}
                ]
            },
            "message": {
                'owner': user_address,
                'spender': adapter,
                'value': value,
                'nonce': nonce,
                'deadline': deadline
            }
        },
        {
            "name": "Standard Permit Format",
            "domain": {
                'name': 'Aave Arbitrum Variable Debt ARB',
                'version': '1',
                'chainId': 42161,
                'verifyingContract': arb_debt_token
            },
            "primaryType": "Permit",
            "types": {
                'EIP712Domain': [
                    {'name': 'name', 'type': 'string'},
                    {'name': 'version', 'type': 'string'},
                    {'name': 'chainId', 'type': 'uint256'},
                    {'name': 'verifyingContract', 'type': 'address'}
                ],
                'Permit': [
                    {'name': 'owner', 'type': 'address'},
                    {'name': 'spender', 'type': 'address'},
                    {'name': 'value', 'type': 'uint256'},
                    {'name': 'nonce', 'type': 'uint256'},
                    {'name': 'deadline', 'type': 'uint256'}
                ]
            },
            "message": {
                'owner': user_address,
                'spender': adapter,
                'value': value,
                'nonce': nonce,
                'deadline': deadline
            }
        }
    ]
    
    # Test each format
    for i, format_config in enumerate(signature_formats, 1):
        print(f"\n{i}️⃣ TESTING: {format_config['name']}")
        print("-" * 40)
        
        try:
            # Create structured data
            structured_data = {
                'types': format_config['types'],
                'domain': format_config['domain'],
                'primaryType': format_config['primaryType'],
                'message': format_config['message']
            }
            
            # Sign
            encoded_data = encode_structured_data(structured_data)
            signature = account.sign_message(encoded_data)
            
            # Create permit data
            permit_data = {
                'token': arb_debt_token,
                'delegatee': adapter,
                'value': value,
                'deadline': deadline,
                'v': signature.v,
                'r': signature.r.to_bytes(32, 'big'),
                's': signature.s.to_bytes(32, 'big')
            }
            
            print(f"✅ Signature created successfully")
            print(f"   V: {permit_data['v']}")
            print(f"   R: {permit_data['r'].hex()}")
            print(f"   S: {permit_data['s'].hex()}")
            
            # Test with minimal transaction build (don't send)
            print(f"🧪 Testing transaction build...")
            
            debt_swap_abi = [{
                "inputs": [
                    {"name": "assetToSwapFrom", "type": "address"},
                    {"name": "assetToSwapTo", "type": "address"},
                    {"name": "amountToSwap", "type": "uint256"},
                    {"name": "paraswapData", "type": "bytes"},
                    {
                        "components": [
                            {"name": "token", "type": "address"},
                            {"name": "delegatee", "type": "address"},
                            {"name": "value", "type": "uint256"},
                            {"name": "deadline", "type": "uint256"},
                            {"name": "v", "type": "uint8"},
                            {"name": "r", "type": "bytes32"},
                            {"name": "s", "type": "bytes32"}
                        ],
                        "name": "creditDelegationPermit",
                        "type": "tuple"
                    }
                ],
                "name": "swapDebt",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            contract = w3.eth.contract(address=adapter, abi=debt_swap_abi)
            
            # Test function call build
            function_call = contract.functions.swapDebt(
                "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # DAI
                "0x912CE59144191C1204E64559FE8253a0e49E6548",  # ARB
                int(1e18),  # $1 test
                b"0x00",  # dummy calldata
                (
                    permit_data['token'],
                    permit_data['delegatee'],
                    permit_data['value'],
                    permit_data['deadline'],
                    permit_data['v'],
                    permit_data['r'],
                    permit_data['s']
                )
            )
            
            # Try to estimate gas (this will fail if signature format is wrong)
            try:
                gas_estimate = function_call.estimate_gas({'from': user_address})
                print(f"🎉 GAS ESTIMATION SUCCESS: {gas_estimate:,}")
                print(f"   → This signature format works!")
                
                return {
                    'format_name': format_config['name'],
                    'permit_data': permit_data,
                    'format_config': format_config,
                    'success': True
                }
                
            except Exception as gas_error:
                print(f"❌ Gas estimation failed: {str(gas_error)[:100]}...")
                print(f"   → Signature format rejected")
                
        except Exception as e:
            print(f"❌ Signature creation failed: {e}")
    
    print(f"\n❌ ALL SIGNATURE FORMATS FAILED")
    print(f"   → Need to investigate contract ABI further")
    return None

if __name__ == "__main__":
    result = try_multiple_signature_formats()
    if result:
        print(f"\n🎉 FOUND WORKING FORMAT: {result['format_name']}")
    else:
        print(f"\n❌ NO WORKING FORMAT FOUND")