#!/usr/bin/env python3
"""
FINAL DEBT SWAP EXECUTOR - EIP-712 FIX APPLIED
Fixes missing 'delegator' field in DelegationWithSig message structure
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account.messages import encode_structured_data
from arbitrum_testnet_agent import ArbitrumTestnetAgent

class FinalDebtSwapExecutor:
    """Final production-ready debt swap executor with corrected EIP-712 signature"""
    
    def __init__(self):
        """Initialize with agent instance"""
        print("🚀 FINAL DEBT SWAP EXECUTOR - EIP-712 FIX APPLIED")
        print("=" * 60)
        
        # Initialize agent
        self.agent = ArbitrumTestnetAgent()
        self.w3 = self.agent.w3
        self.user_address = self.agent.address
        self.private_key = self.agent.private_key
        self.account = self.agent.account
        
        # Verified contract addresses - Canonical Aave ParaSwapDebtSwapAdapter V3
        self.paraswap_debt_swap_adapter = "0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.augustus_swapper = "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        # Debt swap adapter ABI
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
        
        print(f"✅ Initialized with wallet: {self.user_address}")
        print(f"   Debt Swap Adapter: {self.paraswap_debt_swap_adapter}")

    def get_aave_position(self) -> Dict:
        """Get current Aave position"""
        try:
            pool_abi = [{
                "inputs": [{"name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"name": "totalCollateralBase", "type": "uint256"},
                    {"name": "totalDebtBase", "type": "uint256"},
                    {"name": "availableBorrowsBase", "type": "uint256"},
                    {"name": "currentLiquidationThreshold", "type": "uint256"},
                    {"name": "ltv", "type": "uint256"},
                    {"name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }]
            
            pool_contract = self.w3.eth.contract(address=self.aave_pool, abi=pool_abi)
            account_data = pool_contract.functions.getUserAccountData(self.user_address).call()
            
            return {
                'total_collateral_usd': account_data[0] / 1e8,
                'total_debt_usd': account_data[1] / 1e8,
                'available_borrows_usd': account_data[2] / 1e8,
                'health_factor': account_data[5] / 1e18 if account_data[5] > 0 else float('inf')
            }
            
        except Exception as e:
            print(f"❌ Error getting Aave position: {e}")
            return {}

    def get_debt_token_address(self, asset_symbol: str) -> str:
        """Get variable debt token address"""
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
            
            print(f"📋 {asset_symbol} debt token: {variable_debt_token}")
            return variable_debt_token
            
        except Exception as e:
            print(f"❌ Error getting debt token address: {e}")
            return ""

    def get_paraswap_calldata(self, from_asset: str, to_asset: str, amount: int) -> Dict:
        """Get ParaSwap calldata with reverse routing for debt swaps"""
        try:
            # For debt swaps: DAI→ARB debt requires ARB→DAI routing
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']
                dest_token = self.tokens['DAI']
                print(f"🔄 REVERSE ROUTING: ARB → DAI (for DAI debt → ARB debt)")
            elif from_asset.upper() == 'ARB' and to_asset.upper() == 'DAI':
                src_token = self.tokens['DAI']
                dest_token = self.tokens['ARB']
                print(f"🔄 REVERSE ROUTING: DAI → ARB (for ARB debt → DAI debt)")
            else:
                raise ValueError(f"Unsupported swap: {from_asset} → {to_asset}")
            
            # Get price quote
            price_url = "https://apiv5.paraswap.io/prices"
            price_params = {
                'srcToken': src_token,
                'destToken': dest_token,
                'amount': str(amount),
                'srcDecimals': 18,
                'destDecimals': 18,
                'side': 'BUY',
                'network': 42161,
                'partner': 'aave',
                'maxImpact': '15'
            }
            
            print(f"🌐 Getting ParaSwap price quote...")
            price_response = requests.get(price_url, params=price_params, timeout=10)
            
            if price_response.status_code != 200:
                raise Exception(f"ParaSwap price API failed: {price_response.status_code}")
            
            price_data = price_response.json()
            
            if 'priceRoute' not in price_data:
                raise Exception("No price route found")
            
            # Get transaction data
            tx_url = "https://apiv5.paraswap.io/transactions/42161"
            tx_params = {
                'deadline': str(int(time.time()) + 1800),
                'ignoreChecks': 'true'
            }
            
            tx_payload = {
                'srcToken': src_token,
                'destToken': dest_token,
                'srcAmount': price_data['priceRoute']['srcAmount'],
                'destAmount': price_data['priceRoute']['destAmount'],
                'priceRoute': price_data['priceRoute'],
                'userAddress': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter),
                'receiver': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter),
                'partner': 'aave',
                'partnerAddress': self.w3.to_checksum_address(self.paraswap_debt_swap_adapter),
                'partnerFeeBps': '0',
                'takeSurplus': False
            }
            
            print(f"🌐 Getting ParaSwap transaction data...")
            tx_response = requests.post(tx_url, params=tx_params, json=tx_payload, timeout=15)
            
            if tx_response.status_code != 200:
                raise Exception(f"ParaSwap transaction API failed: {tx_response.status_code}")
            
            tx_data = tx_response.json()
            
            return {
                'calldata': tx_data.get('data', '0x'),
                'expected_amount': price_data['priceRoute']['destAmount'],
                'price_route': price_data['priceRoute']
            }
            
        except Exception as e:
            print(f"❌ Error getting ParaSwap calldata: {e}")
            return {}

    def create_fixed_credit_delegation_permit(self, debt_token_address: str) -> Dict:
        """Create FIXED EIP-712 credit delegation permit with 'delegator' field"""
        try:
            print(f"📝 Creating FIXED credit delegation permit")
            print(f"   🔧 APPLYING ARCHITECT FIX: Adding missing 'delegator' field")
            print(f"   Debt Token: {debt_token_address}")
            print(f"   Delegatee: {self.paraswap_debt_swap_adapter}")
            
            # Get debt token contract info
            debt_token_abi = [{
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "stateMutability": "view",
                "type": "function"
            }, {
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "delegationNonces",
                "outputs": [{"name": "", "type": "uint256"}],
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
            
            # Get token info with fallback nonce handling
            token_name = debt_token_contract.functions.name().call()
            
            # Try delegationNonces first, fallback to nonces for compatibility
            try:
                nonce = debt_token_contract.functions.delegationNonces(self.user_address).call()
                print(f"   Using delegationNonces: {nonce}")
            except Exception as e:
                print(f"   delegationNonces failed: {e}")
                print(f"   Falling back to standard nonces...")
                nonce = debt_token_contract.functions.nonces(self.user_address).call()
                print(f"   Using standard nonces: {nonce}")
            
            deadline = int(time.time()) + 3600
            
            print(f"   Token Name: {token_name}")
            print(f"   User: {self.user_address}")
            print(f"   Nonce: {nonce}")
            
            # FIXED EIP-712 domain
            domain = {
                'name': token_name,
                'version': '1',
                'chainId': 42161,
                'verifyingContract': debt_token_address
            }
            
            # FIXED EIP-712 types with DELEGATOR field
            types = {
                'EIP712Domain': [
                    {'name': 'name', 'type': 'string'},
                    {'name': 'version', 'type': 'string'},
                    {'name': 'chainId', 'type': 'uint256'},
                    {'name': 'verifyingContract', 'type': 'address'}
                ],
                'DelegationWithSig': [
                    {'name': 'delegator', 'type': 'address'},  # 🔧 ARCHITECT FIX: Added missing field
                    {'name': 'delegatee', 'type': 'address'},
                    {'name': 'value', 'type': 'uint256'},
                    {'name': 'nonce', 'type': 'uint256'},
                    {'name': 'deadline', 'type': 'uint256'}
                ]
            }
            
            # FIXED message structure with DELEGATOR field
            message = {
                'delegator': self.user_address,              # 🔧 ARCHITECT FIX: Added missing field
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'nonce': nonce,
                'deadline': deadline
            }
            
            print(f"   🔧 FIXED MESSAGE STRUCTURE:")
            print(f"     delegator: {message['delegator']}")
            print(f"     delegatee: {message['delegatee']}")
            print(f"     value: {message['value']}")
            print(f"     nonce: {message['nonce']}")
            print(f"     deadline: {message['deadline']}")
            
            # Create structured data
            structured_data = {
                'types': types,
                'domain': domain,
                'primaryType': 'DelegationWithSig',
                'message': message
            }
            
            # Sign the permit
            encoded_data = encode_structured_data(structured_data)
            signature = self.account.sign_message(encoded_data)
            
            permit_data = {
                'token': debt_token_address,
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'deadline': deadline,
                'v': signature.v if signature.v >= 27 else signature.v + 27,  # EIP-155 fix
                'r': signature.r.to_bytes(32, 'big'),
                's': signature.s.to_bytes(32, 'big')
            }
            
            print(f"✅ FIXED credit delegation permit created")
            print(f"   🔧 ARCHITECT FIX APPLIED: 'delegator' field included in message")
            
            return permit_data
            
        except Exception as e:
            print(f"❌ Error creating fixed credit delegation permit: {e}")
            import traceback
            print(traceback.format_exc())
            return {}

    def validate_signature_preflight(self, debt_token_address: str, permit: Dict) -> Tuple[bool, str]:
        """Validate signature against debt token using eth_call preflight"""
        try:
            print(f"\n🔍 SIGNATURE VALIDATION PREFLIGHT")
            print("=" * 50)
            
            # Debt token delegation ABI
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
            
            debt_token_contract = self.w3.eth.contract(
                address=debt_token_address,
                abi=delegation_abi
            )
            
            # Build delegation call for testing
            delegation_call = debt_token_contract.functions.delegationWithSig(
                self.user_address,          # delegator
                permit['delegatee'],        # delegatee
                permit['value'],            # value
                permit['deadline'],         # deadline
                permit['v'],                # v
                permit['r'],                # r
                permit['s']                 # s
            )
            
            # Test with eth_call
            try:
                print(f"Testing signature validation...")
                result = self.w3.eth.call({
                    'to': debt_token_address,
                    'from': self.user_address,
                    'data': delegation_call._encode_transaction_data(),
                    'gas': 500000
                })
                
                print(f"✅ SIGNATURE VALIDATION PASSED")
                print(f"   Result: {result.hex() if result else '0x'}")
                return True, "Signature validation successful"
                
            except Exception as call_error:
                error_str = str(call_error)
                print(f"❌ SIGNATURE VALIDATION FAILED")
                print(f"   Error: {error_str}")
                return False, f"Signature validation failed: {error_str}"
                
        except Exception as e:
            error_msg = f"Signature validation preflight failed: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def execute_debt_swap(self, from_asset: str, to_asset: str, amount_usd: float) -> Dict:
        """Execute debt swap with complete validation and execution"""
        result = {
            'operation': f'{from_asset}_to_{to_asset}_debt_swap',
            'amount_usd': amount_usd,
            'start_time': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            print(f"\n🔄 EXECUTING DEBT SWAP")
            print("=" * 60)
            print(f"Operation: {from_asset} debt → {to_asset} debt")
            print(f"Amount: ${amount_usd:.2f}")
            
            # Get position before
            position_before = self.get_aave_position()
            print(f"📊 BEFORE - Health Factor: {position_before.get('health_factor', 0):.3f}")
            
            # Get debt token address
            to_debt_token = self.get_debt_token_address(to_asset)
            if not to_debt_token:
                raise Exception(f"Failed to get {to_asset} debt token address")
            
            # Estimate amount in wei
            amount_wei = int(amount_usd * 1e18) if from_asset.upper() == 'DAI' else int(amount_usd / 0.55 * 1e18)
            
            # Get ParaSwap data
            print(f"🌐 Getting ParaSwap quote...")
            paraswap_data = self.get_paraswap_calldata(from_asset, to_asset, amount_wei)
            if not paraswap_data:
                raise Exception("Failed to get ParaSwap calldata")
            
            amount_to_swap = int(paraswap_data['expected_amount'])
            print(f"✅ Amount to swap: {amount_to_swap} ({amount_to_swap / 1e18:.6f})")
            
            # Create FIXED credit delegation permit
            permit = self.create_fixed_credit_delegation_permit(to_debt_token)
            if not permit:
                raise Exception("Failed to create credit delegation permit")
            
            # PREFLIGHT: Validate signature
            print(f"\n🔍 Running signature validation preflight...")
            sig_valid, sig_msg = self.validate_signature_preflight(to_debt_token, permit)
            if not sig_valid:
                raise Exception(f"Signature validation failed: {sig_msg}")
            
            print(f"✅ SIGNATURE VALIDATION PASSED - Proceeding with swap")
            
            # Build debt swap transaction
            debt_swap_contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter,
                abi=self.debt_swap_abi
            )
            
            function_call = debt_swap_contract.functions.swapDebt(
                self.tokens[from_asset.upper()],
                self.tokens[to_asset.upper()],
                amount_to_swap,
                bytes.fromhex(paraswap_data['calldata'][2:]),
                (
                    permit['token'],
                    permit['delegatee'],
                    permit['value'],
                    permit['deadline'],
                    permit['v'],
                    permit['r'],
                    permit['s']
                )
            )
            
            # Gas estimation
            try:
                gas_estimate = function_call.estimate_gas({'from': self.user_address})
                gas_limit = int(gas_estimate * 1.2)
                print(f"✅ Gas estimate: {gas_estimate:,}")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                gas_limit = 800000
            
            # Build and execute transaction
            transaction = function_call.build_transaction({
                'from': self.user_address,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            print(f"\n🚀 EXECUTING TRANSACTION...")
            signed_tx = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            tx_hash_hex = tx_hash.hex()
            print(f"📡 Transaction sent: {tx_hash_hex}")
            print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                print(f"✅ TRANSACTION SUCCESS!")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas Used: {receipt['gasUsed']:,}")
                
                # Get position after
                position_after = self.get_aave_position()
                print(f"📊 AFTER - Health Factor: {position_after.get('health_factor', 0):.3f}")
                
                result.update({
                    'success': True,
                    'tx_hash': tx_hash_hex,
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'health_factor_before': position_before.get('health_factor', 0),
                    'health_factor_after': position_after.get('health_factor', 0)
                })
                
            else:
                print(f"❌ TRANSACTION FAILED")
                result['error'] = 'Transaction reverted'
            
            return result
            
        except Exception as e:
            error_msg = f"Debt swap execution failed: {e}"
            print(f"❌ {error_msg}")
            result['error'] = error_msg
            return result
        
        finally:
            result['end_time'] = datetime.now().isoformat()

def main():
    """Execute complete debt swap cycle"""
    print("🚀 FINAL DEBT SWAP EXECUTOR - COMPLETE CYCLE")
    print("=" * 80)
    print("🔧 ARCHITECT FIX APPLIED: Added missing 'delegator' field to EIP-712 message")
    print("=" * 80)
    
    try:
        executor = FinalDebtSwapExecutor()
        
        # Test minimal amount first
        print(f"\n🧪 PHASE 1: MINIMAL TEST ($0.50)")
        test_result = executor.execute_debt_swap('DAI', 'ARB', 0.5)
        
        if test_result['success']:
            print(f"✅ MINIMAL TEST PASSED - EIP-712 fix successful!")
            
            # Save test result
            with open('eip712_fix_success.json', 'w') as f:
                json.dump(test_result, f, indent=2)
            
            # Execute larger cycle
            print(f"\n🚀 PHASE 2: FULL CYCLE EXECUTION")
            
            # DAI → ARB debt swap
            print(f"\n🔄 Step 1: DAI → ARB debt swap ($5.00)")
            dai_to_arb_result = executor.execute_debt_swap('DAI', 'ARB', 5.0)
            
            if dai_to_arb_result['success']:
                print(f"✅ DAI → ARB swap successful!")
                
                # Wait 5 minutes
                print(f"\n⏳ Step 2: Waiting 5 minutes for optimal conditions...")
                time.sleep(300)  # 5 minutes
                
                # ARB → DAI debt swap
                print(f"\n🔄 Step 3: ARB → DAI debt swap ($5.00)")
                arb_to_dai_result = executor.execute_debt_swap('ARB', 'DAI', 5.0)
                
                if arb_to_dai_result['success']:
                    print(f"✅ ARB → DAI swap successful!")
                    
                    # Calculate complete cycle results
                    complete_cycle = {
                        'cycle_complete': True,
                        'test_result': test_result,
                        'dai_to_arb_result': dai_to_arb_result,
                        'arb_to_dai_result': arb_to_dai_result,
                        'total_transactions': 3,
                        'total_gas_used': test_result['gas_used'] + dai_to_arb_result['gas_used'] + arb_to_dai_result['gas_used'],
                        'arbitrage_complete': True
                    }
                    
                    # Save complete results
                    with open('complete_debt_swap_cycle.json', 'w') as f:
                        json.dump(complete_cycle, f, indent=2)
                    
                    print(f"\n🎉 COMPLETE DEBT SWAP CYCLE SUCCESSFUL!")
                    print(f"   Test TX: {test_result['tx_hash']}")
                    print(f"   DAI→ARB TX: {dai_to_arb_result['tx_hash']}")
                    print(f"   ARB→DAI TX: {arb_to_dai_result['tx_hash']}")
                    print(f"   Total Gas Used: {complete_cycle['total_gas_used']:,}")
                    
                    return True
                else:
                    print(f"❌ ARB → DAI swap failed")
            else:
                print(f"❌ DAI → ARB swap failed")
        else:
            print(f"❌ MINIMAL TEST FAILED - EIP-712 signature issue remains")
            print(f"Error: {test_result.get('error', 'Unknown error')}")
        
        return False
        
    except Exception as e:
        print(f"❌ Complete cycle failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")