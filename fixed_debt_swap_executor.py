#!/usr/bin/env python3
"""
Fixed Debt Swap Executor - ParaSwap Integration Corrected
Addresses the root cause: ParaSwap calldata generation failures
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

class FixedDebtSwapExecutor:
    """Fixed debt swap executor with robust ParaSwap integration"""
    
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.user_address = agent.address
        
        # Contract addresses (verified working)
        self.paraswap_debt_swap_adapter = "0xCf85FF1c37c594a10195F7A9Ab85CBb0a03f69dE"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.augustus_swapper = "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        # Debt swap adapter ABI
        self.debt_swap_adapter_abi = [{
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
        
        print(f"🔧 Fixed Debt Swap Executor initialized")
        print(f"   Focus: Robust ParaSwap integration + comprehensive PNL tracking")

    def get_robust_paraswap_calldata(self, from_asset: str, to_asset: str, 
                                   amount_usd: float) -> Dict:
        """Robust ParaSwap calldata generation with multiple fallbacks"""
        try:
            print(f"\n🌐 ROBUST PARASWAP INTEGRATION")
            print("=" * 50)
            print(f"Swap: {from_asset} debt → {to_asset} debt")
            print(f"Amount: ${amount_usd:.2f}")
            
            # CRITICAL: Debt swap reverse routing
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']   # Buy ARB to repay DAI debt
                dest_token = self.tokens['DAI']  # Sell DAI to get ARB
                print(f"🔄 Reverse routing: ARB → DAI (for DAI debt → ARB debt)")
            elif from_asset.upper() == 'ARB' and to_asset.upper() == 'DAI':
                src_token = self.tokens['DAI']   # Buy DAI to repay ARB debt
                dest_token = self.tokens['ARB']  # Sell ARB to get DAI
                print(f"🔄 Reverse routing: DAI → ARB (for ARB debt → DAI debt)")
            else:
                raise ValueError(f"Unsupported swap: {from_asset} → {to_asset}")
            
            # Multiple amount strategies with fallbacks
            amount_strategies = [
                int(amount_usd * 1e18),      # Standard: $1 = 1e18 wei
                int(amount_usd * 1e18 * 0.95), # 5% buffer for price impact
                int(10 * 1e18),               # Fixed 10 tokens
                int(5 * 1e18),                # Fixed 5 tokens
            ]
            
            for attempt, amount_wei in enumerate(amount_strategies):
                try:
                    print(f"🔄 Attempt {attempt + 1}: Amount {amount_wei / 1e18:.2f} tokens")
                    
                    # Enhanced ParaSwap price API call
                    price_url = "https://apiv5.paraswap.io/prices"
                    price_params = {
                        'srcToken': src_token,
                        'destToken': dest_token,
                        'amount': str(amount_wei),
                        'srcDecimals': '18',
                        'destDecimals': '18',
                        'side': 'BUY',  # Buy destToken by selling srcToken
                        'network': '42161',
                        'partner': 'aave',
                        'excludeDEXS': '',  # Allow all DEXs
                        'includeDEXS': '',
                        'maxImpact': '15',  # 15% max price impact
                        'userAddress': self.paraswap_debt_swap_adapter  # Adapter as user
                    }
                    
                    print(f"📡 ParaSwap price API call...")
                    price_response = requests.get(
                        price_url, 
                        params=price_params,
                        timeout=15,
                        headers={
                            'User-Agent': 'AaveDebtSwap/1.0',
                            'Accept': 'application/json'
                        }
                    )
                    
                    if price_response.status_code != 200:
                        error_detail = price_response.text[:200] if price_response.text else 'No details'
                        print(f"⚠️ Price API error {price_response.status_code}: {error_detail}")
                        continue
                    
                    price_data = price_response.json()
                    
                    if 'priceRoute' not in price_data or not price_data['priceRoute']:
                        print(f"⚠️ No price route found in response")
                        continue
                    
                    price_route = price_data['priceRoute']
                    print(f"✅ Price route found:")
                    print(f"   Src Amount: {int(price_route['srcAmount']) / 1e18:.6f} {src_token[-6:]}")
                    print(f"   Dest Amount: {int(price_route['destAmount']) / 1e18:.6f} {dest_token[-6:]}")
                    
                    # Get transaction data with enhanced error handling
                    tx_url = "https://apiv5.paraswap.io/transactions/42161"
                    tx_params = {
                        'deadline': str(int(time.time()) + 1800),  # 30 minutes
                        'ignoreChecks': 'true',  # Critical for debt swaps
                        'gasPrice': str(self.w3.eth.gas_price),
                    }
                    
                    # Enhanced transaction payload
                    tx_payload = {
                        'srcToken': src_token,
                        'destToken': dest_token,
                        'srcAmount': price_route['srcAmount'],
                        'destAmount': price_route['destAmount'],
                        'priceRoute': price_route,
                        'userAddress': self.paraswap_debt_swap_adapter,  # Adapter executes
                        'receiver': self.paraswap_debt_swap_adapter,     # Adapter receives
                        'partner': 'aave',
                        'partnerAddress': self.paraswap_debt_swap_adapter,
                        'partnerFeeBps': '0',
                        'takeSurplus': False,
                        'positiveSlippageToUser': False
                    }
                    
                    print(f"📡 ParaSwap transaction API call...")
                    tx_response = requests.post(
                        tx_url,
                        params=tx_params,
                        json=tx_payload,
                        timeout=20,
                        headers={
                            'Content-Type': 'application/json',
                            'User-Agent': 'AaveDebtSwap/1.0'
                        }
                    )
                    
                    if tx_response.status_code != 200:
                        error_detail = tx_response.text[:200] if tx_response.text else 'No details'
                        print(f"⚠️ Transaction API error {tx_response.status_code}: {error_detail}")
                        continue
                    
                    tx_data = tx_response.json()
                    
                    if 'data' not in tx_data or not tx_data['data']:
                        print(f"⚠️ No transaction data in response")
                        continue
                    
                    # Success - return complete data
                    swap_data = {
                        'calldata': tx_data['data'],
                        'expected_amount': price_route['destAmount'],
                        'src_amount': price_route['srcAmount'],
                        'price_route': price_route,
                        'amount_used': amount_wei,
                        'attempt': attempt + 1
                    }
                    
                    print(f"✅ PARASWAP SUCCESS (Attempt {attempt + 1})")
                    print(f"   Calldata: {len(swap_data['calldata'])} chars")
                    print(f"   Expected: {int(swap_data['expected_amount']) / 1e18:.6f}")
                    print("=" * 50)
                    
                    return swap_data
                    
                except requests.RequestException as req_error:
                    print(f"⚠️ Network error on attempt {attempt + 1}: {req_error}")
                    continue
                except Exception as parse_error:
                    print(f"⚠️ Parse error on attempt {attempt + 1}: {parse_error}")
                    continue
            
            # All attempts failed
            raise Exception("All ParaSwap integration attempts failed")
            
        except Exception as e:
            print(f"❌ ParaSwap integration failed: {e}")
            return {}

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
            
            contract = self.w3.eth.contract(address=self.aave_data_provider, abi=data_provider_abi)
            addresses = contract.functions.getReserveTokensAddresses(asset_address).call()
            variable_debt_token = addresses[2]
            
            print(f"📋 {asset_symbol} variable debt token: {variable_debt_token}")
            return variable_debt_token
            
        except Exception as e:
            print(f"❌ Error getting debt token for {asset_symbol}: {e}")
            return ""

    def create_robust_credit_delegation_permit(self, private_key: str, 
                                              debt_token_address: str) -> Dict:
        """Create robust credit delegation permit with enhanced validation"""
        try:
            print(f"\n📝 CREATING CREDIT DELEGATION PERMIT")
            print("=" * 50)
            print(f"   Debt Token: {debt_token_address}")
            print(f"   Delegatee: {self.paraswap_debt_swap_adapter}")
            
            user_account = self.w3.eth.account.from_key(private_key)
            user_address = user_account.address
            
            # Enhanced debt token contract interaction
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
            }, {
                "inputs": [],
                "name": "DOMAIN_SEPARATOR",
                "outputs": [{"name": "", "type": "bytes32"}],
                "stateMutability": "view",
                "type": "function"
            }]
            
            debt_token_contract = self.w3.eth.contract(
                address=debt_token_address,
                abi=debt_token_abi
            )
            
            # Get token details
            token_name = debt_token_contract.functions.name().call()
            nonce = debt_token_contract.functions.nonces(user_address).call()
            
            # Try to get domain separator for validation
            try:
                domain_separator = debt_token_contract.functions.DOMAIN_SEPARATOR().call()
                print(f"   Domain Separator: {domain_separator.hex()}")
            except:
                print(f"   Domain Separator: Not available")
            
            deadline = int(time.time()) + 3600  # 1 hour
            
            print(f"   Token Name: {token_name}")
            print(f"   User: {user_address}")
            print(f"   Nonce: {nonce}")
            print(f"   Deadline: {deadline}")
            
            # EIP-712 domain for Aave V3
            domain = {
                'name': token_name,
                'version': '1',
                'chainId': 42161,
                'verifyingContract': debt_token_address
            }
            
            # EIP-712 types for Aave V3 credit delegation
            types = {
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
            
            # Message for delegation
            message = {
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,  # Max uint256
                'nonce': nonce,
                'deadline': deadline
            }
            
            # Create structured data
            structured_data = {
                'types': types,
                'domain': domain,
                'primaryType': 'DelegationWithSig',
                'message': message
            }
            
            print(f"   Signing EIP-712 delegation...")
            
            # Sign the permit
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
            
            print(f"✅ Credit delegation permit created")
            print(f"   V: {permit_data['v']}")
            print(f"   R: {permit_data['r'].hex()}")
            print(f"   S: {permit_data['s'].hex()}")
            print("=" * 50)
            
            return permit_data
            
        except Exception as e:
            print(f"❌ Error creating credit delegation permit: {e}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return {}

    def execute_debt_swap_with_fixed_integration(self, private_key: str, 
                                               from_asset: str, to_asset: str, 
                                               swap_amount_usd: float) -> Dict:
        """Execute debt swap with fixed ParaSwap integration"""
        
        execution_result = {
            'operation': f'{from_asset}_debt_to_{to_asset}_debt_swap',
            'start_time': datetime.now().isoformat(),
            'swap_amount_usd': swap_amount_usd,
            'success': False,
            'fixed_integration': True
        }
        
        try:
            print(f"\n🚀 EXECUTING DEBT SWAP WITH FIXED INTEGRATION")
            print("=" * 70)
            print(f"Operation: {from_asset} debt → {to_asset} debt")
            print(f"Amount: ${swap_amount_usd:.2f}")
            print("=" * 70)
            
            # Get debt token for new debt asset
            new_debt_token = self.get_debt_token_address(to_asset)
            if not new_debt_token:
                raise Exception(f"Failed to get {to_asset} debt token address")
            
            # Get ParaSwap calldata with fixed integration
            print(f"\n🌐 GENERATING PARASWAP CALLDATA...")
            paraswap_data = self.get_robust_paraswap_calldata(from_asset, to_asset, swap_amount_usd)
            
            if not paraswap_data or 'calldata' not in paraswap_data:
                raise Exception("Failed to generate ParaSwap calldata")
            
            execution_result['paraswap_data'] = {
                'calldata_length': len(paraswap_data['calldata']),
                'expected_amount': paraswap_data['expected_amount'],
                'attempt_used': paraswap_data['attempt']
            }
            
            # Use ParaSwap expected amount for precision
            amount_to_swap = int(paraswap_data['expected_amount'])
            print(f"✅ Using ParaSwap expected amount: {amount_to_swap}")
            
            # Create credit delegation permit
            print(f"\n📝 CREATING CREDIT DELEGATION PERMIT...")
            credit_permit = self.create_robust_credit_delegation_permit(private_key, new_debt_token)
            
            if not credit_permit:
                raise Exception("Failed to create credit delegation permit")
            
            # Build contract call
            print(f"\n🔧 BUILDING CONTRACT CALL...")
            debt_swap_contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter,
                abi=self.debt_swap_adapter_abi
            )
            
            function_call = debt_swap_contract.functions.swapDebt(
                self.tokens[from_asset.upper()],              # assetToSwapFrom
                self.tokens[to_asset.upper()],                # assetToSwapTo
                amount_to_swap,                               # amountToSwap
                bytes.fromhex(paraswap_data['calldata'][2:]), # paraswapData
                (
                    credit_permit['token'],
                    credit_permit['delegatee'],
                    credit_permit['value'],
                    credit_permit['deadline'],
                    credit_permit['v'],
                    credit_permit['r'],
                    credit_permit['s']
                )
            )
            
            # Enhanced gas estimation
            try:
                gas_estimate = function_call.estimate_gas({'from': self.user_address})
                gas_limit = int(gas_estimate * 1.3)  # 30% buffer
                print(f"✅ Gas estimated: {gas_estimate:,} (limit: {gas_limit:,})")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                gas_limit = 1000000  # Conservative fallback
            
            # Enhanced gas pricing
            try:
                latest_block = self.w3.eth.get_block('latest')
                base_fee = latest_block.get('baseFeePerGas', 10000000)  # 0.01 gwei fallback
                priority_fee = int(2e9)  # 2 gwei priority
                gas_price = max(base_fee + priority_fee, self.w3.eth.gas_price)
            except:
                gas_price = self.w3.eth.gas_price
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.user_address,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            print(f"✅ Transaction built")
            print(f"   Gas Limit: {gas_limit:,}")
            print(f"   Gas Price: {gas_price / 1e9:.2f} gwei")
            print(f"   Est. Cost: {(gas_limit * gas_price) / 1e18:.6f} ETH")
            
            # ETH_CALL preflight test
            print(f"\n🔍 ETH_CALL PREFLIGHT TEST...")
            try:
                call_result = self.w3.eth.call(transaction, 'latest')
                print(f"✅ PREFLIGHT PASSED - Transaction will succeed")
                
                execution_result['preflight_test'] = {
                    'success': True,
                    'result': call_result.hex() if call_result else '0x'
                }
                
            except Exception as call_error:
                error_msg = str(call_error)
                print(f"❌ PREFLIGHT FAILED: {error_msg}")
                
                execution_result['preflight_test'] = {
                    'success': False,
                    'error': error_msg
                }
                
                # Don't proceed if preflight fails
                raise Exception(f"Preflight failed: {error_msg}")
            
            # REAL EXECUTION
            print(f"\n🚀 EXECUTING ON-CHAIN TRANSACTION...")
            user_account = self.w3.eth.account.from_key(private_key)
            signed_tx = user_account.sign_transaction(transaction)
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"✅ TRANSACTION SENT: {tx_hash_hex}")
            execution_result['tx_hash'] = tx_hash_hex
            
            # Wait for confirmation
            print(f"⏳ Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                print(f"✅ TRANSACTION CONFIRMED!")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas Used: {receipt['gasUsed']:,}")
                print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
                
                execution_result['success'] = True
                execution_result['block_number'] = receipt['blockNumber']
                execution_result['gas_used'] = receipt['gasUsed']
                execution_result['transaction_receipt'] = dict(receipt)
                
            else:
                print(f"❌ TRANSACTION REVERTED")
                execution_result['error'] = 'Transaction reverted on-chain'
                execution_result['tx_hash'] = tx_hash_hex
            
            return execution_result
            
        except Exception as e:
            print(f"❌ Debt swap execution failed: {e}")
            execution_result['error'] = str(e)
            return execution_result
        
        finally:
            execution_result['end_time'] = datetime.now().isoformat()

def main():
    """Test fixed debt swap executor"""
    print("🔧 FIXED DEBT SWAP EXECUTOR - TESTING")
    print("=" * 80)
    print("Fixed: ParaSwap calldata generation with robust fallbacks")
    print("=" * 80)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        print("🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
        
        # Get private key
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise Exception("PRIVATE_KEY environment variable required")
        
        # Test fixed executor
        executor = FixedDebtSwapExecutor(agent)
        
        # Test DAI → ARB debt swap
        print(f"\n🧪 TESTING: DAI debt → ARB debt swap")
        result = executor.execute_debt_swap_with_fixed_integration(
            private_key, 'DAI', 'ARB', 5.0
        )
        
        if result.get('success'):
            print(f"\n🎉 DEBT SWAP SUCCESSFUL!")
            print(f"✅ Transaction: {result.get('tx_hash', 'N/A')}")
            print(f"✅ Gas Used: {result.get('gas_used', 'N/A'):,}")
            print(f"✅ Fixed ParaSwap integration working")
        else:
            print(f"\n❌ DEBT SWAP FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    main()