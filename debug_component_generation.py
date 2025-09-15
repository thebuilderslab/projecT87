#!/usr/bin/env python3
"""
Component Generation Debug Harness
Comprehensive testing of debt swap component generation to identify and fix failures
"""

import os
import time
import json
import requests
import traceback
from datetime import datetime
from typing import Dict, Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account.messages import encode_typed_data

class ComponentGenerationDebugger:
    """Debug component generation for debt swap execution"""
    
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
        
        print(f"🔧 Component Generation Debugger initialized")
        print(f"   User: {self.user_address}")
        print(f"   Adapter: {self.paraswap_debt_swap_adapter}")

    def test_environment_setup(self) -> Dict:
        """Test environment and prerequisites"""
        print(f"\n🌐 TESTING ENVIRONMENT SETUP")
        print("=" * 60)
        
        results = {
            'web3_connection': False,
            'user_address': False,
            'private_key_available': False,
            'coinmarketcap_api': False,
            'arbitrum_network': False
        }
        
        try:
            # Test Web3 connection
            latest_block = self.w3.eth.block_number
            results['web3_connection'] = True
            print(f"✅ Web3 connected - Latest block: {latest_block:,}")
            
            # Test user address
            if self.user_address and len(self.user_address) == 42:
                results['user_address'] = True
                print(f"✅ User address valid: {self.user_address}")
            else:
                print(f"❌ Invalid user address: {self.user_address}")
            
            # Test private key availability (check if PRIVATE_KEY env var exists)
            private_key_env = os.getenv('PRIVATE_KEY')
            if private_key_env:
                results['private_key_available'] = True
                print(f"✅ Private key available (length: {len(private_key_env)})")
            else:
                print(f"❌ Private key not found in environment")
            
            # Test CoinMarketCap API
            cmc_key = os.getenv('COINMARKETCAP_API_KEY')
            if cmc_key:
                results['coinmarketcap_api'] = True
                print(f"✅ CoinMarketCap API key available")
            else:
                print(f"⚠️ CoinMarketCap API key not found (will use fallback prices)")
            
            # Test network (verify we're on Arbitrum)
            chain_id = self.w3.eth.chain_id
            if chain_id == 42161:
                results['arbitrum_network'] = True
                print(f"✅ Connected to Arbitrum mainnet (chain ID: {chain_id})")
            else:
                print(f"❌ Wrong network - Chain ID: {chain_id} (expected 42161)")
                
        except Exception as e:
            print(f"❌ Environment test failed: {e}")
            
        return results

    def test_debt_token_resolution(self, asset_symbol: str) -> Dict:
        """Test debt token address resolution"""
        print(f"\n🏦 TESTING DEBT TOKEN RESOLUTION: {asset_symbol}")
        print("=" * 60)
        
        result = {
            'asset_symbol': asset_symbol,
            'success': False,
            'asset_address': None,
            'debt_token_address': None,
            'error': None
        }
        
        try:
            # Get asset address
            asset_address = self.tokens.get(asset_symbol.upper())
            if not asset_address:
                raise ValueError(f"Unknown asset: {asset_symbol}")
            
            result['asset_address'] = asset_address
            print(f"📋 Asset address: {asset_address}")
            
            # Aave Protocol Data Provider ABI
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
            
            # Get debt token addresses
            token_addresses = data_provider_contract.functions.getReserveTokensAddresses(asset_address).call()
            variable_debt_token = token_addresses[2]
            
            result['debt_token_address'] = variable_debt_token
            result['success'] = True
            
            print(f"✅ Debt token resolution successful:")
            print(f"   aToken: {token_addresses[0]}")
            print(f"   Stable debt: {token_addresses[1]}")
            print(f"   Variable debt: {variable_debt_token}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Debt token resolution failed: {e}")
            print(f"🔍 Full error trace:")
            traceback.print_exc()
            
        return result

    def test_paraswap_api_detailed(self, from_asset: str, to_asset: str, amount_usd: float) -> Dict:
        """Test ParaSwap API with detailed logging"""
        print(f"\n🌐 TESTING PARASWAP API: {from_asset} → {to_asset} (${amount_usd:.2f})")
        print("=" * 60)
        
        result = {
            'from_asset': from_asset,
            'to_asset': to_asset,
            'amount_usd': amount_usd,
            'price_api_success': False,
            'tx_api_success': False,
            'price_response': None,
            'tx_response': None,
            'error': None
        }
        
        try:
            # Debt swap reverse routing
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
            
            # STEP 1: Test ParaSwap Price API
            print(f"\n📡 STEP 1: ParaSwap Price API")
            print("-" * 40)
            
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
            
            print(f"URL: {price_url}")
            print(f"Parameters:")
            for key, value in price_params.items():
                print(f"  {key}: {value}")
            
            price_response = requests.get(price_url, params=price_params, timeout=20)
            
            print(f"\nPrice API Response:")
            print(f"  Status Code: {price_response.status_code}")
            print(f"  Headers: {dict(price_response.headers)}")
            
            if price_response.status_code == 200:
                price_data = price_response.json()
                result['price_response'] = price_data
                result['price_api_success'] = True
                
                print(f"✅ Price API SUCCESS")
                print(f"  Response keys: {list(price_data.keys())}")
                
                if 'priceRoute' in price_data:
                    pr = price_data['priceRoute']
                    print(f"  Price Route:")
                    print(f"    srcAmount: {pr.get('srcAmount', 'N/A')}")
                    print(f"    destAmount: {pr.get('destAmount', 'N/A')}")
                    print(f"    srcToken: {pr.get('srcToken', 'N/A')}")
                    print(f"    destToken: {pr.get('destToken', 'N/A')}")
                
            else:
                print(f"❌ Price API FAILED")
                print(f"  Error body: {price_response.text[:500]}...")
                result['error'] = f"Price API {price_response.status_code}: {price_response.text[:200]}"
                return result
            
            # STEP 2: Test ParaSwap Transaction API
            print(f"\n📡 STEP 2: ParaSwap Transaction API")
            print("-" * 40)
            
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
                'userAddress': self.paraswap_debt_swap_adapter,
                'receiver': self.paraswap_debt_swap_adapter,
                'partner': 'aave',
                'partnerAddress': self.paraswap_debt_swap_adapter,
                'partnerFeeBps': '0',
                'takeSurplus': False
            }
            
            print(f"URL: {tx_url}")
            print(f"Query Parameters:")
            for key, value in tx_params.items():
                print(f"  {key}: {value}")
            print(f"JSON Payload keys: {list(tx_payload.keys())}")
            
            tx_response = requests.post(
                tx_url, 
                params=tx_params, 
                json=tx_payload, 
                timeout=20,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"\nTransaction API Response:")
            print(f"  Status Code: {tx_response.status_code}")
            print(f"  Headers: {dict(tx_response.headers)}")
            
            if tx_response.status_code == 200:
                tx_data = tx_response.json()
                result['tx_response'] = tx_data
                result['tx_api_success'] = True
                
                print(f"✅ Transaction API SUCCESS")
                print(f"  Response keys: {list(tx_data.keys())}")
                
                if 'data' in tx_data:
                    print(f"  Calldata length: {len(tx_data['data'])} chars")
                    print(f"  Calldata preview: {tx_data['data'][:100]}...")
                
            else:
                print(f"❌ Transaction API FAILED")
                print(f"  Error body: {tx_response.text[:500]}...")
                result['error'] = f"Transaction API {tx_response.status_code}: {tx_response.text[:200]}"
                return result
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ ParaSwap API test failed: {e}")
            print(f"🔍 Full error trace:")
            traceback.print_exc()
            
        return result

    def test_credit_delegation_permit(self, private_key_str: str, debt_token_address: str) -> Dict:
        """Test credit delegation permit creation with detailed logging"""
        print(f"\n📝 TESTING CREDIT DELEGATION PERMIT")
        print("=" * 60)
        print(f"Debt Token: {debt_token_address}")
        print(f"Delegatee: {self.paraswap_debt_swap_adapter}")
        
        result = {
            'debt_token_address': debt_token_address,
            'success': False,
            'permit_data': None,
            'error': None
        }
        
        try:
            # Get user account
            user_account = self.w3.eth.account.from_key(private_key_str)
            user_address = user_account.address
            
            print(f"User address: {user_address}")
            
            # Get debt token contract info
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
            
            # Get token name and nonce
            print(f"\n📋 Contract Data:")
            token_name = debt_token_contract.functions.name().call()
            nonce = debt_token_contract.functions.nonces(user_address).call()
            deadline = int(time.time()) + 3600
            
            print(f"  Token Name: {token_name}")
            print(f"  User: {user_address}")
            print(f"  Nonce: {nonce}")
            print(f"  Deadline: {deadline}")
            
            # EIP-712 domain
            domain = {
                'name': token_name,
                'version': '1',
                'chainId': 42161,
                'verifyingContract': debt_token_address
            }
            
            # EIP-712 types
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
            
            # Message
            message = {
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'nonce': nonce,
                'deadline': deadline
            }
            
            print(f"\n📝 EIP-712 Data:")
            print(f"  Domain: {domain}")
            print(f"  Message: {message}")
            
            # Create structured data
            full_message = {
                'types': types,
                'primaryType': 'DelegationWithSig',
                'domain': domain,
                'message': message
            }
            
            print(f"\n🔐 Signing permit...")
            encoded_data = encode_typed_data(full_message)
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
            
            result['permit_data'] = permit_data
            result['success'] = True
            
            print(f"✅ Credit delegation permit created successfully")
            print(f"  v: {permit_data['v']}")
            print(f"  r: {permit_data['r'].hex()}")
            print(f"  s: {permit_data['s'].hex()}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Credit delegation permit failed: {e}")
            print(f"🔍 Full error trace:")
            traceback.print_exc()
            
        return result

    def test_full_component_generation(self, private_key_str: str, from_asset: str, 
                                     to_asset: str, amount_usd: float) -> Dict:
        """Test complete component generation process"""
        print(f"\n🔄 TESTING FULL COMPONENT GENERATION")
        print("=" * 80)
        print(f"Operation: {from_asset} debt → {to_asset} debt")
        print(f"Amount: ${amount_usd:.2f}")
        print("=" * 80)
        
        result = {
            'operation': f'{from_asset}_to_{to_asset}_debt_swap',
            'amount_usd': amount_usd,
            'components': {},
            'overall_success': False,
            'error': None
        }
        
        try:
            # Component 1: Debt token address
            print(f"\n🏦 COMPONENT 1: Debt Token Address")
            debt_token_result = self.test_debt_token_resolution(to_asset)
            result['components']['debt_token'] = debt_token_result
            
            if not debt_token_result['success']:
                raise Exception(f"Debt token resolution failed: {debt_token_result['error']}")
            
            # Component 2: ParaSwap calldata
            print(f"\n🌐 COMPONENT 2: ParaSwap Calldata")
            paraswap_result = self.test_paraswap_api_detailed(from_asset, to_asset, amount_usd)
            result['components']['paraswap'] = paraswap_result
            
            if not (paraswap_result['price_api_success'] and paraswap_result['tx_api_success']):
                raise Exception(f"ParaSwap API failed: {paraswap_result['error']}")
            
            # Component 3: Credit delegation permit
            print(f"\n📝 COMPONENT 3: Credit Delegation Permit")
            permit_result = self.test_credit_delegation_permit(
                private_key_str, debt_token_result['debt_token_address']
            )
            result['components']['credit_permit'] = permit_result
            
            if not permit_result['success']:
                raise Exception(f"Credit delegation permit failed: {permit_result['error']}")
            
            # SUCCESS - All components generated
            result['overall_success'] = True
            
            print(f"\n✅ ALL COMPONENTS GENERATED SUCCESSFULLY!")
            print("=" * 80)
            print(f"✅ Debt Token: {debt_token_result['debt_token_address']}")
            print(f"✅ ParaSwap: {len(paraswap_result['tx_response']['data'])} char calldata")
            print(f"✅ Credit Permit: v={permit_result['permit_data']['v']}")
            print("=" * 80)
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n❌ COMPONENT GENERATION FAILED: {e}")
            print("=" * 80)
            
        return result

def main():
    """Main debugging function"""
    print(f"🔧 COMPONENT GENERATION DEBUG HARNESS")
    print("=" * 80)
    
    # Mock agent setup for testing (replace with real agent)
    class MockAgent:
        def __init__(self):
            # Use environment variables or provide test values
            rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            self.address = os.getenv('USER_ADDRESS', '0x5B7b72c7cd71F1FaF4C98b6b1B1acF0cBf57e04a')
    
    try:
        agent = MockAgent()
        debugger = ComponentGenerationDebugger(agent)
        
        # Test environment setup
        env_results = debugger.test_environment_setup()
        
        if not env_results.get('private_key_available'):
            print(f"\n❌ Cannot proceed - Private key not available")
            print(f"   Set PRIVATE_KEY environment variable")
            return
        
        private_key = os.getenv('PRIVATE_KEY')
        
        # Test full component generation for both swap directions
        test_cases = [
            ('DAI', 'ARB', 10.0),
            ('ARB', 'DAI', 10.0)
        ]
        
        for from_asset, to_asset, amount in test_cases:
            print(f"\n{'='*80}")
            print(f"TESTING: {from_asset} → {to_asset} (${amount:.2f})")
            print(f"{'='*80}")
            
            component_result = debugger.test_full_component_generation(
                private_key, from_asset, to_asset, amount
            )
            
            if component_result['overall_success']:
                print(f"✅ {from_asset} → {to_asset} component generation: SUCCESS")
            else:
                print(f"❌ {from_asset} → {to_asset} component generation: FAILED")
                print(f"   Error: {component_result['error']}")
                
        print(f"\n🔧 COMPONENT GENERATION DEBUG COMPLETE")
        
    except Exception as e:
        print(f"❌ Debug harness failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()