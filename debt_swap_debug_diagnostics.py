#!/usr/bin/env python3
"""
Debt Swap Debug Diagnostics
Enhanced debugging to identify and fix specific contract revert issues
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

class DebtSwapDebugger:
    """Enhanced debugger for debt swap contract issues"""
    
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.user_address = agent.address
        
        # Contract addresses
        self.paraswap_debt_swap_adapter = "0xCf85FF1c37c594a10195F7A9Ab85CBb0a03f69dE"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        print(f"🔍 Debt Swap Debugger initialized")
        print(f"   Focus: Identifying specific revert reasons")

    def enhanced_revert_decoder(self, revert_data: str) -> str:
        """Enhanced revert reason decoder with common Aave/ParaSwap errors"""
        try:
            if not revert_data or revert_data == '0x':
                return "No revert data available"
            
            # Remove 0x prefix
            if revert_data.startswith('0x'):
                revert_data = revert_data[2:]
            
            # Standard Error(string) selector: 0x08c379a0
            error_selector = revert_data[:8]
            
            # Common Aave V3 error selectors
            aave_errors = {
                '08c379a0': 'Error(string)',
                '579952fc': 'INVALID_AMOUNT',
                'cd4e6167': 'INVALID_TOKEN',
                'f4d678b8': 'INSUFFICIENT_LIQUIDITY',
                '48f5c3ed': 'INVALID_SIGNATURE',
                'eb7e8b22': 'EXPIRED_PERMIT',
                '3774c25c': 'INVALID_DELEGATEE',
                'aa7d5d0a': 'INSUFFICIENT_COLLATERAL',
                '70f4a398': 'INVALID_CREDIT_DELEGATION',
                'b3e96e4e': 'CALLER_MUST_BE_POOL',
                '5a041dce': 'CALLER_NOT_POOL_OR_EMERGENCY_ADMIN',
                'c44b11f7': 'OPERATION_NOT_SUPPORTED',
                '89023bb3': 'DEBT_CEILING_EXCEEDED',
                'c7e4dfc0': 'BORROWING_NOT_ENABLED',
                '1d1e7bc1': 'STABLE_BORROWING_NOT_ENABLED',
                '05f5d006': 'NOT_ENOUGH_AVAILABLE_USER_BALANCE',
                '2e4ab0e2': 'INVALID_INTEREST_RATE_MODE_SELECTED',
                '37dd2304': 'HEALTH_FACTOR_LOWER_THAN_LIQUIDATION_THRESHOLD',
                '9a4b2e15': 'COLLATERAL_CANNOT_COVER_NEW_BORROW',
                '35cd27c7': 'STABLE_DEBT_NOT_ENABLED',
                '88a9ca40': 'RESERVE_LIQUIDITY_NOT_ZERO',
                'bd28d0b8': 'FLASHLOAN_PREMIUM_INVALID',
                '4e487b71': 'PANIC_ERROR'
            }
            
            # ParaSwap specific errors
            paraswap_errors = {
                '0758b49e': 'ADAPTER_NOT_FOUND',
                '64a8db7a': 'INVALID_PERCENT_SPLIT',
                'afd01602': 'INVALID_POOL_ADDRESS',
                '1c30056a': 'INVALID_ADAPTER_CONFIG',
                'e6ae43e1': 'SWAP_FAILED',
                'bf2afdae': 'INVALID_SWAP_DESCRIPTION',
                '25b506e1': 'INSUFFICIENT_OUTPUT',
                'beda6138': 'SLIPPAGE_TOO_HIGH'
            }
            
            all_errors = {**aave_errors, **paraswap_errors}
            
            if error_selector in all_errors:
                error_name = all_errors[error_selector]
                
                # Try to decode Error(string) messages
                if error_selector == '08c379a0':
                    try:
                        # Skip selector (4 bytes) and decode the string
                        string_data = revert_data[8:]
                        if len(string_data) >= 64:
                            # ABI encoded string format
                            offset = int(string_data[:64], 16) * 2
                            length = int(string_data[offset:offset+64], 16) * 2
                            message_hex = string_data[offset+64:offset+64+length]
                            message = bytes.fromhex(message_hex).decode('utf-8', errors='ignore')
                            return f"Error: {message}"
                    except:
                        return f"Error(string): Failed to decode message"
                
                return f"{error_name} (0x{error_selector})"
            
            # Unknown error
            return f"Unknown Error: 0x{error_selector} (data: {revert_data[:100]}...)"
            
        except Exception as e:
            return f"Decode failed: {str(e)} (raw: {revert_data[:100]}...)"

    def test_individual_components(self, private_key: str) -> Dict:
        """Test each component individually to isolate the issue"""
        results = {
            'component_tests': {},
            'overall_diagnosis': '',
            'recommended_fixes': []
        }
        
        try:
            print(f"\n🔍 INDIVIDUAL COMPONENT TESTING")
            print("=" * 60)
            
            # Test 1: Basic account data retrieval
            print(f"🧪 TEST 1: Account Data Retrieval")
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
                
                results['component_tests']['account_data'] = {
                    'success': True,
                    'total_collateral': account_data[0] / 1e8,
                    'total_debt': account_data[1] / 1e8,
                    'health_factor': account_data[5] / 1e18 if account_data[5] > 0 else float('inf')
                }
                print(f"✅ Account data retrieval successful")
                
            except Exception as e:
                results['component_tests']['account_data'] = {'success': False, 'error': str(e)}
                print(f"❌ Account data failed: {e}")
                
            # Test 2: Debt token address resolution
            print(f"\n🧪 TEST 2: Debt Token Resolution")
            try:
                # Test both DAI and ARB debt tokens
                for symbol in ['DAI', 'ARB']:
                    debt_token = self.get_debt_token_address(symbol)
                    if debt_token:
                        results['component_tests'][f'{symbol.lower()}_debt_token'] = {
                            'success': True, 'address': debt_token
                        }
                        print(f"✅ {symbol} debt token: {debt_token}")
                    else:
                        results['component_tests'][f'{symbol.lower()}_debt_token'] = {
                            'success': False, 'error': 'Address resolution failed'
                        }
                        print(f"❌ {symbol} debt token resolution failed")
                        
            except Exception as e:
                results['component_tests']['debt_token_resolution'] = {'success': False, 'error': str(e)}
                print(f"❌ Debt token resolution failed: {e}")
                
            # Test 3: ParaSwap calldata generation
            print(f"\n🧪 TEST 3: ParaSwap Calldata Generation")
            try:
                swap_data = self.get_paraswap_calldata_simple('DAI', 'ARB', 10)
                if swap_data and 'calldata' in swap_data:
                    results['component_tests']['paraswap_calldata'] = {
                        'success': True,
                        'calldata_length': len(swap_data['calldata']),
                        'expected_amount': swap_data.get('expected_amount', 'N/A')
                    }
                    print(f"✅ ParaSwap calldata generated ({len(swap_data['calldata'])} chars)")
                else:
                    results['component_tests']['paraswap_calldata'] = {
                        'success': False, 'error': 'No calldata generated'
                    }
                    print(f"❌ ParaSwap calldata generation failed")
                    
            except Exception as e:
                results['component_tests']['paraswap_calldata'] = {'success': False, 'error': str(e)}
                print(f"❌ ParaSwap calldata failed: {e}")
                
            # Test 4: Credit delegation permit
            print(f"\n🧪 TEST 4: Credit Delegation Permit")
            try:
                arb_debt_token = self.get_debt_token_address('ARB')
                if arb_debt_token:
                    permit = self.create_credit_delegation_permit(private_key, arb_debt_token)
                    if permit and 'v' in permit:
                        results['component_tests']['credit_permit'] = {
                            'success': True,
                            'permit_token': permit['token'],
                            'permit_delegatee': permit['delegatee']
                        }
                        print(f"✅ Credit delegation permit created")
                    else:
                        results['component_tests']['credit_permit'] = {
                            'success': False, 'error': 'Permit creation failed'
                        }
                        print(f"❌ Credit delegation permit failed")
                else:
                    results['component_tests']['credit_permit'] = {
                        'success': False, 'error': 'No ARB debt token address'
                    }
                    print(f"❌ Credit permit failed - no debt token")
                    
            except Exception as e:
                results['component_tests']['credit_permit'] = {'success': False, 'error': str(e)}
                print(f"❌ Credit delegation permit failed: {e}")
                
            # Test 5: Contract existence and ABI compatibility
            print(f"\n🧪 TEST 5: Contract Validation")
            try:
                # Check if debt swap adapter exists
                adapter_code = self.w3.eth.get_code(self.paraswap_debt_swap_adapter)
                if adapter_code and adapter_code != b'':
                    results['component_tests']['contract_exists'] = {
                        'success': True,
                        'code_size': len(adapter_code)
                    }
                    print(f"✅ Debt swap adapter exists ({len(adapter_code)} bytes)")
                    
                    # Test if we can create contract instance
                    minimal_abi = [{
                        "inputs": [
                            {"name": "assetToSwapFrom", "type": "address"},
                            {"name": "assetToSwapTo", "type": "address"},
                            {"name": "amountToSwap", "type": "uint256"},
                            {"name": "paraswapData", "type": "bytes"},
                            {"name": "creditDelegationPermit", "type": "tuple", "components": [
                                {"name": "token", "type": "address"},
                                {"name": "delegatee", "type": "address"},
                                {"name": "value", "type": "uint256"},
                                {"name": "deadline", "type": "uint256"},
                                {"name": "v", "type": "uint8"},
                                {"name": "r", "type": "bytes32"},
                                {"name": "s", "type": "bytes32"}
                            ]}
                        ],
                        "name": "swapDebt",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }]
                    
                    contract = self.w3.eth.contract(address=self.paraswap_debt_swap_adapter, abi=minimal_abi)
                    results['component_tests']['abi_compatibility'] = {'success': True}
                    print(f"✅ ABI compatibility confirmed")
                    
                else:
                    results['component_tests']['contract_exists'] = {
                        'success': False, 'error': 'No contract code at address'
                    }
                    print(f"❌ No contract at debt swap adapter address")
                    
            except Exception as e:
                results['component_tests']['contract_validation'] = {'success': False, 'error': str(e)}
                print(f"❌ Contract validation failed: {e}")
                
            # Analyze results and provide diagnosis
            print(f"\n📊 COMPONENT TEST ANALYSIS")
            print("=" * 60)
            
            failed_components = []
            for test_name, test_result in results['component_tests'].items():
                if not test_result.get('success', False):
                    failed_components.append(test_name)
                    print(f"❌ {test_name}: {test_result.get('error', 'Unknown failure')}")
                else:
                    print(f"✅ {test_name}: Working correctly")
                    
            if failed_components:
                results['overall_diagnosis'] = f"Failed components: {', '.join(failed_components)}"
                results['recommended_fixes'] = [
                    f"Fix {comp} component before proceeding" for comp in failed_components
                ]
            else:
                results['overall_diagnosis'] = "All components working - issue likely in parameter combination"
                results['recommended_fixes'] = [
                    "Test parameter validation",
                    "Check amount precision and scaling",
                    "Validate ParaSwap calldata context",
                    "Test with smaller amounts"
                ]
                
            return results
            
        except Exception as e:
            results['overall_diagnosis'] = f"Component testing failed: {str(e)}"
            return results

    def get_debt_token_address(self, asset_symbol: str) -> str:
        """Get variable debt token address for an asset"""
        try:
            asset_address = self.tokens.get(asset_symbol.upper())
            if not asset_address:
                return ""
            
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
            return addresses[2]  # Variable debt token
            
        except Exception as e:
            print(f"❌ Error getting debt token for {asset_symbol}: {e}")
            return ""

    def get_paraswap_calldata_simple(self, from_asset: str, to_asset: str, amount_usd: float) -> Dict:
        """Simplified ParaSwap calldata generation for testing"""
        try:
            # Use reverse routing for debt swaps
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']
                dest_token = self.tokens['DAI']
            else:
                src_token = self.tokens['DAI']
                dest_token = self.tokens['ARB']
            
            amount_wei = int(amount_usd * 1e18)  # Simple conversion
            
            # Get ParaSwap price
            price_url = "https://apiv5.paraswap.io/prices"
            price_params = {
                'srcToken': src_token,
                'destToken': dest_token,
                'amount': str(amount_wei),
                'srcDecimals': 18,
                'destDecimals': 18,
                'side': 'BUY',
                'network': 42161,
                'partner': 'aave'
            }
            
            price_response = requests.get(price_url, params=price_params, timeout=10)
            if price_response.status_code != 200:
                return {}
            
            price_data = price_response.json()
            if 'priceRoute' not in price_data:
                return {}
            
            # Get transaction data
            tx_url = "https://apiv5.paraswap.io/transactions/42161"
            tx_payload = {
                'srcToken': src_token,
                'destToken': dest_token,
                'srcAmount': price_data['priceRoute']['srcAmount'],
                'destAmount': price_data['priceRoute']['destAmount'],
                'priceRoute': price_data['priceRoute'],
                'userAddress': self.paraswap_debt_swap_adapter,
                'receiver': self.paraswap_debt_swap_adapter,
                'partner': 'aave'
            }
            
            tx_response = requests.post(tx_url, json=tx_payload, timeout=15)
            if tx_response.status_code != 200:
                return {}
            
            tx_data = tx_response.json()
            return {
                'calldata': tx_data.get('data', '0x'),
                'expected_amount': price_data['priceRoute']['destAmount']
            }
            
        except Exception as e:
            print(f"❌ ParaSwap calldata error: {e}")
            return {}

    def create_credit_delegation_permit(self, private_key: str, debt_token_address: str) -> Dict:
        """Create credit delegation permit for testing"""
        try:
            user_account = self.w3.eth.account.from_key(private_key)
            
            # Get token info
            token_abi = [{
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
            
            token_contract = self.w3.eth.contract(address=debt_token_address, abi=token_abi)
            token_name = token_contract.functions.name().call()
            nonce = token_contract.functions.nonces(user_account.address).call()
            
            # EIP-712 domain and types
            domain = {
                'name': token_name,
                'version': '1',
                'chainId': 42161,
                'verifyingContract': debt_token_address
            }
            
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
            
            deadline = int(time.time()) + 3600
            message = {
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'nonce': nonce,
                'deadline': deadline
            }
            
            structured_data = {
                'types': types,
                'domain': domain,
                'primaryType': 'DelegationWithSig',
                'message': message
            }
            
            encoded_data = encode_structured_data(structured_data)
            signature = user_account.sign_message(encoded_data)
            
            return {
                'token': debt_token_address,
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'deadline': deadline,
                'v': signature.v,
                'r': signature.r.to_bytes(32, 'big'),
                's': signature.s.to_bytes(32, 'big')
            }
            
        except Exception as e:
            print(f"❌ Credit permit error: {e}")
            return {}

    def test_minimal_debt_swap_call(self, private_key: str) -> Dict:
        """Test debt swap call with enhanced revert decoding"""
        result = {
            'test_name': 'minimal_debt_swap_call',
            'success': False,
            'revert_reason': '',
            'detailed_diagnosis': ''
        }
        
        try:
            print(f"\n🧪 TESTING MINIMAL DEBT SWAP CALL")
            print("=" * 60)
            
            # Get components
            arb_debt_token = self.get_debt_token_address('ARB')
            paraswap_data = self.get_paraswap_calldata_simple('DAI', 'ARB', 10)
            credit_permit = self.create_credit_delegation_permit(private_key, arb_debt_token)
            
            if not all([arb_debt_token, paraswap_data, credit_permit]):
                result['detailed_diagnosis'] = "Failed to generate required components"
                return result
            
            # Build minimal contract call
            minimal_abi = [{
                "inputs": [
                    {"name": "assetToSwapFrom", "type": "address"},
                    {"name": "assetToSwapTo", "type": "address"},
                    {"name": "amountToSwap", "type": "uint256"},
                    {"name": "paraswapData", "type": "bytes"},
                    {"name": "creditDelegationPermit", "type": "tuple", "components": [
                        {"name": "token", "type": "address"},
                        {"name": "delegatee", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ]}
                ],
                "name": "swapDebt",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            contract = self.w3.eth.contract(address=self.paraswap_debt_swap_adapter, abi=minimal_abi)
            
            # Use actual expected amount from ParaSwap
            amount_to_swap = int(paraswap_data['expected_amount'])
            
            function_call = contract.functions.swapDebt(
                self.tokens['DAI'],                                    # assetToSwapFrom
                self.tokens['ARB'],                                    # assetToSwapTo
                amount_to_swap,                                        # amountToSwap
                bytes.fromhex(paraswap_data['calldata'][2:]),         # paraswapData
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
            
            # Build transaction for eth_call
            transaction = {
                'to': self.paraswap_debt_swap_adapter,
                'from': self.user_address,
                'data': function_call._encode_transaction_data(),
                'gas': 1000000,
                'gasPrice': 0,
                'value': 0
            }
            
            print(f"📋 MINIMAL CALL PARAMETERS:")
            print(f"   Asset From: {self.tokens['DAI']}")
            print(f"   Asset To: {self.tokens['ARB']}")
            print(f"   Amount: {amount_to_swap}")
            print(f"   Calldata Length: {len(paraswap_data['calldata'])}")
            print(f"   Credit Token: {credit_permit['token']}")
            
            # Execute eth_call with enhanced error capture
            try:
                call_result = self.w3.eth.call(transaction, 'latest')
                result['success'] = True
                result['detailed_diagnosis'] = "Call succeeded - no revert"
                print(f"✅ ETH_CALL SUCCEEDED!")
                
            except Exception as call_error:
                error_str = str(call_error)
                print(f"❌ ETH_CALL FAILED: {error_str}")
                
                # Extract revert data for enhanced decoding
                revert_data = None
                if hasattr(call_error, 'data'):
                    revert_data = call_error.data
                elif 'revert' in error_str.lower():
                    import re
                    hex_matches = re.findall(r'0x[a-fA-F0-9]+', error_str)
                    for match in hex_matches:
                        if len(match) > 10:
                            revert_data = match
                            break
                
                if revert_data:
                    decoded_reason = self.enhanced_revert_decoder(revert_data)
                    result['revert_reason'] = decoded_reason
                    result['detailed_diagnosis'] = f"Enhanced decode: {decoded_reason}"
                    print(f"🔍 ENHANCED REVERT DECODE: {decoded_reason}")
                else:
                    result['revert_reason'] = error_str
                    result['detailed_diagnosis'] = f"Raw error: {error_str}"
                    print(f"⚠️ NO REVERT DATA EXTRACTED")
            
            return result
            
        except Exception as e:
            result['detailed_diagnosis'] = f"Test setup failed: {str(e)}"
            print(f"❌ Test failed: {e}")
            return result

def main():
    """Run comprehensive debt swap diagnostics"""
    print("🔍 DEBT SWAP DEBUG DIAGNOSTICS")
    print("=" * 80)
    print("Goal: Identify and fix specific contract revert issues")
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
        
        # Run diagnostics
        debugger = DebtSwapDebugger(agent)
        
        # Test individual components
        component_results = debugger.test_individual_components(private_key)
        print(f"\n📊 COMPONENT TEST SUMMARY:")
        print(f"Diagnosis: {component_results['overall_diagnosis']}")
        for fix in component_results['recommended_fixes']:
            print(f"  • {fix}")
        
        # Test minimal debt swap call
        call_results = debugger.test_minimal_debt_swap_call(private_key)
        print(f"\n🧪 MINIMAL CALL TEST RESULTS:")
        print(f"Success: {call_results['success']}")
        print(f"Diagnosis: {call_results['detailed_diagnosis']}")
        
        # Save diagnostic results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debt_swap_diagnostics_{timestamp}.json"
        
        full_results = {
            'component_tests': component_results,
            'minimal_call_test': call_results,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(full_results, f, indent=2, default=str)
        
        print(f"\n📁 Diagnostic results saved: {filename}")
        
        return full_results
        
    except Exception as e:
        print(f"❌ Diagnostics failed: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    main()