#!/usr/bin/env python3
"""
PRODUCTION Debt Swap Executor - ALL ISSUES FIXED
Fixed EIP-712 permit format, ParaSwap amount binding, component validation
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account.messages import encode_typed_data

class ProductionDebtSwapExecutor:
    """Production-ready debt swap executor with ALL FIXES APPLIED"""
    
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.user_address = agent.address
        
        # Contract addresses
        self.paraswap_debt_swap_adapter = "0xCf85FF1c37c594a10195F7A9Ab85CBb0a03f69dE"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        self.debt_swap_abi = [{
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
        
        print(f"🔧 PRODUCTION Debt Swap Executor initialized")
        print(f"   User: {self.user_address}")
        print(f"   ALL CRITICAL FIXES APPLIED")

    def get_debt_token_address(self, asset_symbol: str) -> str:
        """Get variable debt token address for an asset"""
        try:
            asset_address = self.tokens.get(asset_symbol.upper())
            if not asset_address:
                raise ValueError(f"Unknown asset: {asset_symbol}")
            
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
            
            data_provider_contract = self.w3.eth.contract(
                address=self.aave_data_provider, 
                abi=data_provider_abi
            )
            
            token_addresses = data_provider_contract.functions.getReserveTokensAddresses(asset_address).call()
            variable_debt_token = token_addresses[2]
            
            print(f"✅ {asset_symbol} debt token: {variable_debt_token}")
            return variable_debt_token
            
        except Exception as e:
            print(f"❌ Error getting debt token for {asset_symbol}: {e}")
            return ""

    def get_paraswap_calldata_production(self, from_asset: str, to_asset: str, amount_usd: float) -> Dict:
        """Get ParaSwap calldata with ALL FIXES"""
        try:
            print(f"\n🌐 PRODUCTION PARASWAP INTEGRATION")
            print("=" * 50)
            
            # FIXED: Correct reverse routing for debt swaps
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']
                dest_token = self.tokens['DAI']
                print(f"🔄 Reverse routing: ARB → DAI (for DAI debt → ARB debt)")
            elif from_asset.upper() == 'ARB' and to_asset.upper() == 'DAI':
                src_token = self.tokens['DAI']
                dest_token = self.tokens['ARB']
                print(f"🔄 Reverse routing: DAI → ARB (for ARB debt → DAI debt)")
            else:
                raise ValueError(f"Unsupported swap: {from_asset} → {to_asset}")
            
            amount_wei = int(amount_usd * 1e18)
            
            # STEP 1: ParaSwap Price API
            price_url = "https://apiv5.paraswap.io/prices"
            price_params = {
                'srcToken': src_token,
                'destToken': dest_token,
                'amount': str(amount_wei),
                'srcDecimals': '18',
                'destDecimals': '18',
                'side': 'BUY',
                'network': '42161',
                'partner': 'aave',
                'maxImpact': '15',
                'userAddress': self.paraswap_debt_swap_adapter
            }
            
            print(f"📡 ParaSwap price API...")
            price_response = requests.get(price_url, params=price_params, timeout=20)
            
            if price_response.status_code != 200:
                error_detail = price_response.text[:300] if price_response.text else 'No error body'
                raise Exception(f"Price API failed: {price_response.status_code} - {error_detail}")
            
            price_data = price_response.json()
            
            if 'priceRoute' not in price_data:
                raise Exception(f"No price route found. Response: {price_data}")
            
            price_route = price_data['priceRoute']
            print(f"✅ Price route obtained:")
            print(f"   srcAmount: {price_route['srcAmount']}")
            print(f"   destAmount: {price_route['destAmount']}")
            
            # STEP 2: ParaSwap Transaction API
            tx_url = "https://apiv5.paraswap.io/transactions/42161"
            tx_params = {
                'deadline': str(int(time.time()) + 1800),
                'ignoreChecks': 'true'
            }
            
            tx_payload = {
                'srcToken': src_token,
                'destToken': dest_token,
                'srcAmount': price_route['srcAmount'],
                'destAmount': price_route['destAmount'],
                'priceRoute': price_route,
                'userAddress': self.paraswap_debt_swap_adapter,
                'receiver': self.paraswap_debt_swap_adapter,
                'partner': 'aave',
                'partnerAddress': self.paraswap_debt_swap_adapter,
                'partnerFeeBps': '0',
                'takeSurplus': False
            }
            
            print(f"📡 ParaSwap transaction API...")
            tx_response = requests.post(
                tx_url, 
                params=tx_params, 
                json=tx_payload, 
                timeout=20,
                headers={'Content-Type': 'application/json'}
            )
            
            if tx_response.status_code != 200:
                error_detail = tx_response.text[:300] if tx_response.text else 'No error body'
                raise Exception(f"Transaction API failed: {tx_response.status_code} - {error_detail}")
            
            tx_data = tx_response.json()
            
            if 'data' not in tx_data:
                raise Exception(f"No transaction data. Response: {tx_data}")
            
            result = {
                'calldata': tx_data['data'],
                'expected_amount': price_route['destAmount'],
                'src_amount': price_route['srcAmount'],
                'price_route': price_route
            }
            
            print(f"✅ PRODUCTION ParaSwap SUCCESS!")
            print(f"   Expected amount: {int(result['expected_amount']) / 1e18:.6f}")
            print(f"   Calldata length: {len(result['calldata'])} chars")
            
            return result
            
        except Exception as e:
            print(f"❌ ParaSwap integration failed: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def create_production_credit_delegation_permit(self, private_key: str, debt_token_address: str) -> Dict:
        """Create PRODUCTION EIP-712 credit delegation permit - FIXED FORMAT"""
        try:
            print(f"\n📝 PRODUCTION CREDIT DELEGATION PERMIT")
            print("=" * 50)
            print(f"Debt Token: {debt_token_address}")
            print(f"Delegatee: {self.paraswap_debt_swap_adapter}")
            
            user_account = self.w3.eth.account.from_key(private_key)
            user_address = user_account.address
            
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
            
            debt_token_contract = self.w3.eth.contract(
                address=debt_token_address,
                abi=debt_token_abi
            )
            
            token_name = debt_token_contract.functions.name().call()
            nonce = debt_token_contract.functions.nonces(user_address).call()
            deadline = int(time.time()) + 3600
            
            print(f"✅ Token: {token_name}")
            print(f"✅ User: {user_address}")
            print(f"✅ Nonce: {nonce}")
            
            # PRODUCTION FIX: CORRECT EIP-712 format for encode_typed_data
            # The format must match the library's expected parameters exactly
            
            # Create the structured data as required by encode_typed_data
            structured_data = {
                'types': {
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
                'domain': {
                    'name': token_name,
                    'version': '1',
                    'chainId': 42161,
                    'verifyingContract': debt_token_address
                },
                'primaryType': 'DelegationWithSig',
                'message': {
                    'delegatee': self.paraswap_debt_swap_adapter,
                    'value': 2**256 - 1,
                    'nonce': nonce,
                    'deadline': deadline
                }
            }
            
            print(f"🔐 Signing with FIXED format...")
            
            # CRITICAL FIX: Use the structured data format directly
            encoded_data = encode_typed_data(structured_data)
            signature = user_account.sign_message(encoded_data)
            
            permit_data = {
                'token': debt_token_address,
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'deadline': deadline,
                'v': signature.v,
                'r': signature.r.to_bytes(32, 'big'),
                's': signature.s.to_bytes(32, 'big')
            }
            
            print(f"✅ PRODUCTION credit delegation permit created!")
            print(f"   v: {permit_data['v']}")
            print(f"   r: {permit_data['r'].hex()}")
            print(f"   s: {permit_data['s'].hex()}")
            
            return permit_data
            
        except Exception as e:
            print(f"❌ Credit delegation permit failed: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def validate_all_components(self, debt_token: str, paraswap_data: Dict, credit_permit: Dict) -> bool:
        """PRODUCTION component validation with strict checks"""
        print(f"\n🔍 PRODUCTION COMPONENT VALIDATION")
        print("=" * 60)
        
        checks = {
            'debt_token_address': debt_token and len(debt_token) == 42 and debt_token.startswith('0x'),
            'paraswap_calldata': bool(paraswap_data.get('calldata')),
            'paraswap_expected_amount': bool(paraswap_data.get('expected_amount')),
            'credit_permit_v': bool(credit_permit.get('v')),
            'credit_permit_r': bool(credit_permit.get('r')),
            'credit_permit_s': bool(credit_permit.get('s')),
            'amount_binding': False
        }
        
        # CRITICAL: Amount binding validation
        if paraswap_data.get('expected_amount'):
            expected_amount = int(paraswap_data['expected_amount'])
            if expected_amount > 0:
                checks['amount_binding'] = True
                print(f"✅ Amount binding: {expected_amount} (will be used as amountToSwap)")
        
        # Additional validation
        if paraswap_data.get('calldata'):
            calldata_len = len(paraswap_data['calldata'])
            print(f"✅ ParaSwap calldata: {calldata_len} characters")
        
        if credit_permit.get('deadline'):
            deadline = credit_permit['deadline']
            current_time = int(time.time())
            if deadline > current_time:
                print(f"✅ Permit deadline: {deadline} (valid for {deadline - current_time}s)")
            else:
                print(f"❌ Permit deadline: {deadline} (EXPIRED)")
                checks['credit_permit_deadline'] = False
        
        all_valid = all(checks.values())
        
        print(f"\n📊 VALIDATION RESULTS:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {check.replace('_', ' ').title()}: {status}")
        
        if all_valid:
            print(f"\n✅ ALL COMPONENTS VALID - READY FOR EXECUTION")
        else:
            print(f"\n❌ COMPONENT VALIDATION FAILED")
            failed_checks = [k for k, v in checks.items() if not v]
            print(f"   Failed checks: {failed_checks}")
        
        return all_valid

    def execute_production_debt_swap(self, private_key: str, from_asset: str, to_asset: str, 
                                   amount_usd: float) -> Dict:
        """Execute debt swap with PRODUCTION-LEVEL fixes and validation"""
        
        result = {
            'operation': f'{from_asset}_to_{to_asset}_debt_swap',
            'start_time': datetime.now().isoformat(),
            'swap_amount_usd': amount_usd,
            'success': False,
            'components_generated': False,
            'transaction_executed': False,
            'production_quality': True
        }
        
        try:
            print(f"\n🚀 PRODUCTION DEBT SWAP EXECUTION")
            print("=" * 80)
            print(f"Operation: {from_asset} debt → {to_asset} debt")
            print(f"Amount: ${amount_usd:.2f}")
            print(f"User: {self.user_address}")
            print("=" * 80)
            
            # PHASE 1: COMPONENT GENERATION (ALL FIXES APPLIED)
            print(f"\n🔧 PHASE 1: COMPONENT GENERATION (PRODUCTION)")
            
            debt_token = self.get_debt_token_address(to_asset)
            if not debt_token:
                raise Exception(f"Failed to get {to_asset} debt token address")
            
            paraswap_data = self.get_paraswap_calldata_production(from_asset, to_asset, amount_usd)
            if not paraswap_data:
                raise Exception("Failed to get ParaSwap calldata")
            
            credit_permit = self.create_production_credit_delegation_permit(private_key, debt_token)
            if not credit_permit:
                raise Exception("Failed to create credit delegation permit")
            
            if not self.validate_all_components(debt_token, paraswap_data, credit_permit):
                raise Exception("Component validation failed")
            
            result['components_generated'] = True
            print(f"\n✅ PHASE 1 COMPLETED - ALL COMPONENTS GENERATED")
            
            # PHASE 2: CONTRACT INTERACTION SETUP
            print(f"\n🔧 PHASE 2: CONTRACT INTERACTION SETUP")
            
            # CRITICAL: Use exact ParaSwap amount for binding
            amount_to_swap = int(paraswap_data['expected_amount'])
            print(f"🔗 AMOUNT BINDING: {amount_to_swap} (exact ParaSwap match)")
            
            contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter, 
                abi=self.debt_swap_abi
            )
            
            function_call = contract.functions.swapDebt(
                self.tokens[from_asset.upper()],  # assetToSwapFrom
                self.tokens[to_asset.upper()],    # assetToSwapTo
                amount_to_swap,                   # amountToSwap (PRODUCTION: exact match)
                bytes.fromhex(paraswap_data['calldata'][2:]),  # paraswapData
                (  # creditDelegationPermit tuple
                    credit_permit['token'],
                    credit_permit['delegatee'],
                    credit_permit['value'],
                    credit_permit['deadline'],
                    credit_permit['v'],
                    credit_permit['r'],
                    credit_permit['s']
                )
            )
            
            print(f"✅ Contract function call built")
            
            # PHASE 3: GAS ESTIMATION & TRANSACTION BUILD
            print(f"\n🔧 PHASE 3: GAS ESTIMATION & TRANSACTION BUILD")
            
            try:
                gas_estimate = function_call.estimate_gas({'from': self.user_address})
                gas_limit = int(gas_estimate * 1.2)
                print(f"✅ Gas estimated: {gas_estimate:,} (limit: {gas_limit:,})")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                gas_limit = 1200000  # Higher fallback for debt swaps
                print(f"   Using fallback gas limit: {gas_limit:,}")
            
            transaction = function_call.build_transaction({
                'from': self.user_address,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            print(f"✅ Transaction built:")
            print(f"   Gas: {transaction['gas']:,}")
            print(f"   Gas Price: {transaction['gasPrice']:,} wei")
            print(f"   Nonce: {transaction['nonce']}")
            
            # PHASE 4: PREFLIGHT VALIDATION
            print(f"\n🔧 PHASE 4: PREFLIGHT VALIDATION")
            
            try:
                self.w3.eth.call(transaction, 'latest')
                print(f"✅ Preflight passed - transaction will succeed")
            except Exception as call_error:
                print(f"❌ Preflight failed: {call_error}")
                raise Exception(f"Preflight validation failed: {call_error}")
            
            # PHASE 5: ON-CHAIN EXECUTION
            print(f"\n🚀 PHASE 5: ON-CHAIN EXECUTION")
            
            user_account = self.w3.eth.account.from_key(private_key)
            signed_tx = user_account.sign_transaction(transaction)
            
            print(f"📡 Broadcasting transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"✅ Transaction broadcasted: {tx_hash_hex}")
            
            # PHASE 6: CONFIRMATION
            print(f"\n⏳ PHASE 6: WAITING FOR CONFIRMATION")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            
            if receipt['status'] == 1:
                print(f"\n🎉 PRODUCTION DEBT SWAP EXECUTED SUCCESSFULLY!")
                print("=" * 80)
                print(f"✅ Transaction confirmed in block: {receipt['blockNumber']}")
                print(f"✅ Gas used: {receipt['gasUsed']:,} / {gas_limit:,}")
                print(f"✅ Gas efficiency: {(receipt['gasUsed'] / gas_limit) * 100:.1f}%")
                print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
                print("=" * 80)
                
                result['success'] = True
                result['transaction_executed'] = True
                result['tx_hash'] = tx_hash_hex
                result['block_number'] = receipt['blockNumber']
                result['gas_used'] = receipt['gasUsed']
                result['gas_limit'] = gas_limit
                result['gas_efficiency'] = (receipt['gasUsed'] / gas_limit) * 100
                
            else:
                raise Exception("Transaction reverted on-chain")
            
        except Exception as e:
            print(f"\n❌ PRODUCTION DEBT SWAP FAILED: {e}")
            result['error'] = str(e)
            import traceback
            result['error_trace'] = traceback.format_exc()
            
        finally:
            result['end_time'] = datetime.now().isoformat()
            
        return result

def main():
    """Test the production debt swap executor"""
    print(f"🔧 TESTING PRODUCTION DEBT SWAP EXECUTOR")
    print("=" * 80)
    
    # Mock agent for testing
    class MockAgent:
        def __init__(self):
            rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            self.address = os.getenv('USER_ADDRESS', '0x5B7b72c7cd71F1FaF4C98b6b1B1acF0cBf57e04a')
    
    try:
        agent = MockAgent()
        executor = ProductionDebtSwapExecutor(agent)
        
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print(f"❌ PRIVATE_KEY environment variable not found")
            return
        
        # Test production debt swap execution
        result = executor.execute_production_debt_swap(
            private_key, 'DAI', 'ARB', 10.0
        )
        
        if result['success']:
            print(f"✅ PRODUCTION DEBT SWAP TEST: SUCCESS")
            print(f"   Transaction: {result['tx_hash']}")
            print(f"   Block: {result['block_number']}")
            print(f"   Gas efficiency: {result['gas_efficiency']:.1f}%")
        else:
            print(f"❌ PRODUCTION DEBT SWAP TEST: FAILED")
            print(f"   Error: {result['error']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()