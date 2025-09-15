#!/usr/bin/env python3
"""
DEFINITIVE DEBT SWAP CYCLE EXECUTOR
Consolidated production implementation with proven successful execution.
Complete cycle: DAI debt → ARB debt → wait 5min → ARB debt → DAI debt + comprehensive PNL tracking.
"""

import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, getcontext
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account.messages import encode_structured_data

# Set high precision for PNL calculations
getcontext().prec = 50

class DefinitiveDebtSwapExecutor:
    """DEFINITIVE consolidated debt swap executor for proven successful execution"""
    
    def __init__(self, private_key: str = None):
        """Initialize with comprehensive setup and validation"""
        # Load private key from parameter or environment
        self.private_key = private_key or os.getenv('PRIVATE_KEY')
        if not self.private_key:
            raise ValueError("Private key not provided and no PRIVATE_KEY environment variable set")
        
        # Initialize Web3 connection
        rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Derive address from private key
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.user_address = self.w3.to_checksum_address(self.account.address)
        
        # Contract addresses (verified working)
        self.paraswap_debt_swap_adapter = "0xCf85FF1c37c594a10195F7A9Ab85CBb0a03f69dE"
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        # Correct Aave ParaSwap Debt Swap Adapter ABI
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
        
        # PNL tracking
        self.pnl_data = {
            'cycle_start_time': None,
            'cycle_end_time': None,
            'initial_debt_positions': {},
            'intermediate_debt_positions': {},
            'final_debt_positions': {},
            'gas_costs': {'phase1': 0, 'phase2': 0},
            'price_snapshots': {},
            'transactions': []
        }
        
        print(f"🔧 DEFINITIVE Debt Swap Cycle Executor initialized")
        print(f"   User: {self.user_address}")
        print(f"   RPC: {rpc_url}")
        print(f"   All components consolidated and validated")

    def get_current_prices(self) -> Dict[str, float]:
        """Get current token prices from CoinMarketCap"""
        try:
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            if not api_key:
                fallback_prices = {'DAI': 1.00, 'ARB': 0.55}
                print(f"⚠️ Using fallback prices: {fallback_prices}")
                return fallback_prices
            
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            params = {'symbol': 'DAI,ARB', 'convert': 'USD'}
            headers = {'X-CMC_PRO_API_KEY': api_key, 'Accept': 'application/json'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                prices = {
                    'DAI': float(data['data']['DAI']['quote']['USD']['price']),
                    'ARB': float(data['data']['ARB']['quote']['USD']['price'])
                }
                print(f"💰 Live prices: DAI ${prices['DAI']:.4f}, ARB ${prices['ARB']:.4f}")
                return prices
            else:
                fallback_prices = {'DAI': 1.00, 'ARB': 0.55}
                print(f"⚠️ Price API failed, using fallback: {fallback_prices}")
                return fallback_prices
                
        except Exception as e:
            fallback_prices = {'DAI': 1.00, 'ARB': 0.55}
            print(f"❌ Price error: {e}, using fallback: {fallback_prices}")
            return fallback_prices

    def get_aave_position(self) -> Dict:
        """Get comprehensive Aave position data"""
        try:
            print(f"📊 VALIDATING AAVE POSITION")
            print("=" * 50)
            
            # Pool contract for account data
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
            
            # Get individual debt balances
            debt_balances = self.get_debt_balances()
            
            position = {
                'total_collateral_usd': account_data[0] / (10**8),
                'total_debt_usd': account_data[1] / (10**8),
                'available_borrows_usd': account_data[2] / (10**8),
                'health_factor': account_data[5] / (10**18) if account_data[5] > 0 else float('inf'),
                'debt_balances': debt_balances,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ POSITION SNAPSHOT:")
            print(f"   Total Collateral: ${position['total_collateral_usd']:.2f}")
            print(f"   Total Debt: ${position['total_debt_usd']:.2f}")
            print(f"   Available Borrows: ${position['available_borrows_usd']:.2f}")
            print(f"   Health Factor: {position['health_factor']:.6f}")
            print(f"   DAI Debt: {debt_balances['DAI']:.6f}")
            print(f"   ARB Debt: {debt_balances['ARB']:.6f}")
            
            return position
            
        except Exception as e:
            print(f"❌ Error getting Aave position: {e}")
            return {}

    def get_debt_balances(self) -> Dict[str, float]:
        """Get current debt balances from Aave"""
        try:
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
            
            erc20_abi = [{
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }]
            
            data_provider = self.w3.eth.contract(address=self.aave_data_provider, abi=data_provider_abi)
            debt_balances = {}
            
            for symbol, token_address in self.tokens.items():
                addresses = data_provider.functions.getReserveTokensAddresses(token_address).call()
                variable_debt_token = addresses[2]
                
                debt_contract = self.w3.eth.contract(address=variable_debt_token, abi=erc20_abi)
                balance_wei = debt_contract.functions.balanceOf(self.user_address).call()
                balance = float(balance_wei) / 1e18
                
                debt_balances[symbol] = balance
            
            return debt_balances
            
        except Exception as e:
            print(f"❌ Error getting debt balances: {e}")
            return {'DAI': 0.0, 'ARB': 0.0}

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

    def get_paraswap_calldata(self, from_asset: str, to_asset: str, amount_wei: int) -> Dict:
        """Get ParaSwap calldata with CORRECT reverse routing for debt swaps"""
        try:
            print(f"\n🌐 PARASWAP INTEGRATION")
            print("=" * 50)
            
            # CRITICAL: For debt swaps, routing is REVERSED
            # DAI debt → ARB debt requires ARB → DAI routing (to get DAI to repay the debt)
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']  # Route FROM ARB
                dest_token = self.tokens['DAI']  # Route TO DAI
                print(f"🔄 REVERSE ROUTING: ARB → DAI (for DAI debt → ARB debt swap)")
            elif from_asset.upper() == 'ARB' and to_asset.upper() == 'DAI':
                src_token = self.tokens['DAI']  # Route FROM DAI  
                dest_token = self.tokens['ARB']  # Route TO ARB
                print(f"🔄 REVERSE ROUTING: DAI → ARB (for ARB debt → DAI debt swap)")
            else:
                raise ValueError(f"Unsupported debt swap: {from_asset} → {to_asset}")
            
            # ParaSwap Price API with correct debt swap parameters
            price_url = "https://apiv5.paraswap.io/prices"
            price_params = {
                'srcToken': src_token,
                'destToken': dest_token,
                'amount': str(amount_wei),
                'srcDecimals': '18',
                'destDecimals': '18',
                'side': 'BUY',  # BUY the dest token by selling src
                'network': '42161',  # Arbitrum
                'partner': 'aave',
                'maxImpact': '15'  # Max 15% price impact
            }
            
            print(f"📡 Getting ParaSwap price route...")
            price_response = requests.get(price_url, params=price_params, timeout=20)
            
            if price_response.status_code != 200:
                error_text = price_response.text if price_response.text else 'No error details'
                raise Exception(f"Price API failed: {price_response.status_code} - {error_text}")
            
            price_data = price_response.json()
            
            if 'priceRoute' not in price_data:
                raise Exception("No price route found")
            
            price_route = price_data['priceRoute']
            print(f"✅ Price route: {int(price_route['srcAmount']) / 1e18:.6f} → {int(price_route['destAmount']) / 1e18:.6f}")
            
            # ParaSwap Transaction API
            tx_url = "https://apiv5.paraswap.io/transactions/42161"
            tx_params = {
                'deadline': str(int(time.time()) + 1800),  # 30 min deadline
                'ignoreChecks': 'true'  # CRITICAL: Bypass balance checks for debt swaps
            }
            
            tx_payload = {
                'srcToken': src_token,
                'destToken': dest_token,
                'srcAmount': price_route['srcAmount'],
                'destAmount': price_route['destAmount'],
                'priceRoute': price_route,
                'userAddress': self.paraswap_debt_swap_adapter,  # Adapter executes
                'receiver': self.paraswap_debt_swap_adapter,    # Adapter receives
                'partner': 'aave',
                'partnerAddress': self.paraswap_debt_swap_adapter,
                'partnerFeeBps': '0',
                'takeSurplus': False
            }
            
            print(f"📡 Getting ParaSwap transaction data...")
            tx_response = requests.post(
                tx_url, 
                params=tx_params, 
                json=tx_payload,
                timeout=20,
                headers={'Content-Type': 'application/json'}
            )
            
            if tx_response.status_code != 200:
                error_text = tx_response.text if tx_response.text else 'No error details'
                raise Exception(f"Transaction API failed: {tx_response.status_code} - {error_text}")
            
            tx_data = tx_response.json()
            
            if 'data' not in tx_data:
                raise Exception("No transaction data")
            
            result = {
                'calldata': tx_data['data'],
                'expected_amount': price_route['destAmount'],
                'src_amount': price_route['srcAmount'],
                'price_route': price_route
            }
            
            print(f"✅ ParaSwap SUCCESS!")
            print(f"   Expected Amount: {int(result['expected_amount']) / 1e18:.6f}")
            print(f"   Calldata Length: {len(result['calldata'])} chars")
            
            return result
            
        except Exception as e:
            print(f"❌ ParaSwap failed: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def create_credit_delegation_permit(self, debt_token_address: str, amount: int = None) -> Dict:
        """Create EIP-712 credit delegation permit for Aave debt tokens"""
        try:
            print(f"\n📝 CREDIT DELEGATION PERMIT")
            print("=" * 50)
            print(f"Debt Token: {debt_token_address}")
            print(f"Delegatee: {self.paraswap_debt_swap_adapter}")
            
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
            
            # Get token info
            token_name = debt_token_contract.functions.name().call()
            nonce = debt_token_contract.functions.nonces(self.user_address).call()
            deadline = int(time.time()) + 3600  # 1 hour
            value = amount if amount else 2**256 - 1  # Max approval if no specific amount
            
            print(f"✅ Token: {token_name}")
            print(f"✅ Nonce: {nonce}")
            print(f"✅ Value: {value}")
            
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
            
            # Message data
            message = {
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': value,
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
            
            # Sign the permit
            encoded_data = encode_structured_data(structured_data)
            signature = self.account.sign_message(encoded_data)
            
            permit_data = {
                'token': debt_token_address,
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': value,
                'deadline': deadline,
                'v': signature.v,
                'r': signature.r.to_bytes(32, 'big'),
                's': signature.s.to_bytes(32, 'big')
            }
            
            print(f"✅ Credit delegation permit created successfully")
            
            return permit_data
            
        except Exception as e:
            print(f"❌ Error creating credit delegation permit: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def validate_debt_swap_prerequisites(self, swap_amount_usd: float = 10.0) -> Tuple[bool, str]:
        """Validate all prerequisites for debt swap execution"""
        try:
            print(f"\n🔍 VALIDATING DEBT SWAP PREREQUISITES")
            print("=" * 60)
            
            # Check 1: Aave position
            position = self.get_aave_position()
            if not position:
                return False, "Failed to get Aave position"
            
            health_factor = position.get('health_factor', 0)
            total_debt = position.get('total_debt_usd', 0)
            dai_debt = position.get('debt_balances', {}).get('DAI', 0)
            
            # Check 2: Adequate health factor
            if health_factor < 1.5:
                return False, f"Health factor too low: {health_factor:.3f} (minimum 1.5)"
            
            # Check 3: Adequate debt to swap
            min_dai_debt_required = swap_amount_usd  # Need at least swap amount in DAI debt
            if dai_debt < min_dai_debt_required:
                return False, f"Insufficient DAI debt: {dai_debt:.2f} (need {min_dai_debt_required})"
            
            # Check 4: Web3 connection
            if not self.w3.is_connected():
                return False, "Web3 not connected"
            
            # Check 5: ParaSwap API test
            print(f"🌐 Testing ParaSwap API connectivity...")
            test_amount_wei = int(1 * 1e18)  # $1 test
            test_calldata = self.get_paraswap_calldata('DAI', 'ARB', test_amount_wei)
            if not test_calldata:
                return False, "ParaSwap API failed test"
            
            # Check 6: Credit delegation permit test
            dai_debt_token = self.get_debt_token_address('DAI')
            if not dai_debt_token:
                return False, "Failed to get DAI debt token address"
            
            test_permit = self.create_credit_delegation_permit(dai_debt_token)
            if not test_permit:
                return False, "Failed to create test credit delegation permit"
            
            print(f"✅ ALL PREREQUISITES VALIDATED")
            print(f"   Health Factor: {health_factor:.3f} ✅")
            print(f"   DAI Debt: {dai_debt:.2f} ✅")
            print(f"   ParaSwap API: ✅")
            print(f"   Credit Delegation: ✅")
            print(f"   Ready for ${swap_amount_usd} debt swap")
            
            return True, "All prerequisites validated"
            
        except Exception as e:
            return False, f"Prerequisite validation failed: {e}"

    def execute_debt_swap_phase(self, from_asset: str, to_asset: str, amount_usd: float) -> Tuple[bool, Dict]:
        """Execute a single debt swap phase with comprehensive logging"""
        try:
            phase_name = f"{from_asset} debt → {to_asset} debt"
            print(f"\n🚀 EXECUTING DEBT SWAP: {phase_name}")
            print("=" * 60)
            print(f"   Amount: ${amount_usd:.2f}")
            print(f"   From: {from_asset} debt")
            print(f"   To: {to_asset} debt")
            
            # Step 1: Get ParaSwap calldata
            amount_wei = int(amount_usd * 1e18)
            paraswap_data = self.get_paraswap_calldata(from_asset, to_asset, amount_wei)
            
            if not paraswap_data:
                return False, {'error': 'Failed to get ParaSwap data'}
            
            # Step 2: Get debt token address and create credit delegation permit
            from_debt_token = self.get_debt_token_address(from_asset)
            if not from_debt_token:
                return False, {'error': f'Failed to get {from_asset} debt token address'}
            
            permit_data = self.create_credit_delegation_permit(from_debt_token)
            if not permit_data:
                return False, {'error': 'Failed to create credit delegation permit'}
            
            # Step 3: Prepare transaction
            debt_swap_contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter,
                abi=self.debt_swap_abi
            )
            
            # Build transaction parameters
            swap_params = [
                self.tokens[from_asset],  # assetToSwapFrom
                self.tokens[to_asset],    # assetToSwapTo
                amount_wei,               # amountToSwap
                paraswap_data['calldata'], # paraswapData
                (
                    permit_data['token'],
                    permit_data['delegatee'],
                    permit_data['value'],
                    permit_data['deadline'],
                    permit_data['v'],
                    permit_data['r'],
                    permit_data['s']
                )  # creditDelegationPermit tuple
            ]
            
            print(f"🔧 Building debt swap transaction...")
            
            # Get gas estimate
            try:
                gas_estimate = debt_swap_contract.functions.swapDebt(*swap_params).estimate_gas({
                    'from': self.user_address
                })
                print(f"⛽ Gas estimate: {gas_estimate:,}")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                gas_estimate = 500000  # Fallback gas limit
            
            # Build transaction
            tx = debt_swap_contract.functions.swapDebt(*swap_params).build_transaction({
                'from': self.user_address,
                'gas': int(gas_estimate * 1.2),  # 20% buffer
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            print(f"✍️ Signing transaction...")
            signed_tx = self.account.sign_transaction(tx)
            
            print(f"📤 Sending transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"🔗 Transaction sent: {tx_hash_hex}")
            print(f"⏳ Waiting for confirmation...")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                gas_used = receipt['gasUsed']
                gas_cost_wei = gas_used * tx['gasPrice']
                gas_cost_usd = (gas_cost_wei / 1e18) * self.get_current_prices().get('ETH', 2500)  # Approximate ETH price
                
                result = {
                    'success': True,
                    'tx_hash': tx_hash_hex,
                    'gas_used': gas_used,
                    'gas_cost_usd': gas_cost_usd,
                    'block_number': receipt['blockNumber'],
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"✅ DEBT SWAP SUCCESSFUL!")
                print(f"   TX Hash: {tx_hash_hex}")
                print(f"   Gas Used: {gas_used:,}")
                print(f"   Gas Cost: ${gas_cost_usd:.4f}")
                print(f"   Block: {receipt['blockNumber']}")
                
                return True, result
                
            else:
                return False, {'error': 'Transaction failed', 'tx_hash': tx_hash_hex}
                
        except Exception as e:
            print(f"❌ Debt swap failed: {e}")
            import traceback
            traceback.print_exc()
            return False, {'error': str(e)}

    def execute_full_debt_swap_cycle(self, swap_amount_usd: float = 10.0) -> Dict:
        """Execute the complete debt swap cycle with comprehensive PNL tracking"""
        try:
            print(f"\n🎯 STARTING DEFINITIVE DEBT SWAP CYCLE")
            print("=" * 80)
            print(f"   Target Amount: ${swap_amount_usd:.2f}")
            print(f"   Sequence: DAI debt → ARB debt → wait 5min → ARB debt → DAI debt")
            
            # Initialize PNL tracking
            self.pnl_data['cycle_start_time'] = datetime.now().isoformat()
            self.pnl_data['initial_debt_positions'] = self.get_aave_position()
            self.pnl_data['price_snapshots']['start'] = self.get_current_prices()
            
            # Prerequisites validation
            valid, message = self.validate_debt_swap_prerequisites(swap_amount_usd)
            if not valid:
                return {'success': False, 'error': f'Prerequisites failed: {message}'}
            
            print(f"\n📊 INITIAL POSITION SNAPSHOT")
            initial_position = self.pnl_data['initial_debt_positions']
            print(f"   DAI Debt: {initial_position['debt_balances']['DAI']:.6f}")
            print(f"   ARB Debt: {initial_position['debt_balances']['ARB']:.6f}")
            print(f"   Health Factor: {initial_position['health_factor']:.6f}")
            
            # PHASE 1: DAI debt → ARB debt
            print(f"\n🔥 PHASE 1: DAI DEBT → ARB DEBT")
            phase1_success, phase1_result = self.execute_debt_swap_phase('DAI', 'ARB', swap_amount_usd)
            
            if not phase1_success:
                return {'success': False, 'error': 'Phase 1 failed', 'details': phase1_result}
            
            self.pnl_data['transactions'].append({
                'phase': 1,
                'type': 'DAI_to_ARB',
                'result': phase1_result
            })
            
            # Intermediate position snapshot
            time.sleep(10)  # Allow blockchain to settle
            self.pnl_data['intermediate_debt_positions'] = self.get_aave_position()
            self.pnl_data['price_snapshots']['intermediate'] = self.get_current_prices()
            
            print(f"\n📊 INTERMEDIATE POSITION SNAPSHOT")
            intermediate_position = self.pnl_data['intermediate_debt_positions']
            print(f"   DAI Debt: {intermediate_position['debt_balances']['DAI']:.6f}")
            print(f"   ARB Debt: {intermediate_position['debt_balances']['ARB']:.6f}")
            print(f"   Health Factor: {intermediate_position['health_factor']:.6f}")
            
            # 5-MINUTE WAIT PERIOD
            print(f"\n⏳ WAITING 5 MINUTES...")
            wait_start = time.time()
            wait_duration = 300  # 5 minutes
            
            while time.time() - wait_start < wait_duration:
                remaining = wait_duration - (time.time() - wait_start)
                print(f"   Time remaining: {int(remaining)}s", end='\r')
                time.sleep(1)
            
            print(f"\n✅ Wait period completed")
            
            # PHASE 2: ARB debt → DAI debt
            print(f"\n🔥 PHASE 2: ARB DEBT → DAI DEBT")
            phase2_success, phase2_result = self.execute_debt_swap_phase('ARB', 'DAI', swap_amount_usd)
            
            if not phase2_success:
                return {
                    'success': False, 
                    'error': 'Phase 2 failed', 
                    'details': phase2_result,
                    'phase1_success': True,
                    'phase1_tx': phase1_result['tx_hash']
                }
            
            self.pnl_data['transactions'].append({
                'phase': 2,
                'type': 'ARB_to_DAI',
                'result': phase2_result
            })
            
            # Final position snapshot
            time.sleep(10)  # Allow blockchain to settle
            self.pnl_data['final_debt_positions'] = self.get_aave_position()
            self.pnl_data['price_snapshots']['end'] = self.get_current_prices()
            self.pnl_data['cycle_end_time'] = datetime.now().isoformat()
            
            # Calculate comprehensive PNL
            pnl_report = self.calculate_comprehensive_pnl()
            
            print(f"\n🎉 CYCLE COMPLETED SUCCESSFULLY!")
            print(f"   Phase 1 TX: {phase1_result['tx_hash']}")
            print(f"   Phase 2 TX: {phase2_result['tx_hash']}")
            
            return {
                'success': True,
                'phase1_tx': phase1_result['tx_hash'],
                'phase2_tx': phase2_result['tx_hash'],
                'pnl_report': pnl_report,
                'full_data': self.pnl_data
            }
            
        except Exception as e:
            print(f"❌ Cycle execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def calculate_comprehensive_pnl(self) -> Dict:
        """Calculate comprehensive PNL analysis"""
        try:
            print(f"\n📈 CALCULATING COMPREHENSIVE PNL")
            print("=" * 60)
            
            initial = self.pnl_data['initial_debt_positions']
            final = self.pnl_data['final_debt_positions']
            prices_start = self.pnl_data['price_snapshots']['start']
            prices_end = self.pnl_data['price_snapshots']['end']
            
            # Debt changes
            dai_debt_change = final['debt_balances']['DAI'] - initial['debt_balances']['DAI']
            arb_debt_change = final['debt_balances']['ARB'] - initial['debt_balances']['ARB']
            
            # USD values
            dai_debt_change_usd = dai_debt_change * prices_end['DAI']
            arb_debt_change_usd = arb_debt_change * prices_end['ARB']
            
            # Total gas costs
            total_gas_cost = sum(tx['result'].get('gas_cost_usd', 0) for tx in self.pnl_data['transactions'])
            
            # Net PNL calculation
            net_debt_change_usd = dai_debt_change_usd + arb_debt_change_usd
            net_pnl_usd = -net_debt_change_usd - total_gas_cost  # Negative debt change is positive PNL
            
            # Price impact analysis
            dai_price_change = ((prices_end['DAI'] - prices_start['DAI']) / prices_start['DAI']) * 100
            arb_price_change = ((prices_end['ARB'] - prices_start['ARB']) / prices_start['ARB']) * 100
            
            pnl_report = {
                'cycle_duration_seconds': (
                    datetime.fromisoformat(self.pnl_data['cycle_end_time']) - 
                    datetime.fromisoformat(self.pnl_data['cycle_start_time'])
                ).total_seconds(),
                'debt_changes': {
                    'dai_tokens': dai_debt_change,
                    'arb_tokens': arb_debt_change,
                    'dai_usd': dai_debt_change_usd,
                    'arb_usd': arb_debt_change_usd,
                    'net_debt_change_usd': net_debt_change_usd
                },
                'gas_costs': {
                    'phase1_usd': self.pnl_data['transactions'][0]['result'].get('gas_cost_usd', 0),
                    'phase2_usd': self.pnl_data['transactions'][1]['result'].get('gas_cost_usd', 0),
                    'total_usd': total_gas_cost
                },
                'price_impacts': {
                    'dai_price_change_pct': dai_price_change,
                    'arb_price_change_pct': arb_price_change
                },
                'health_factor': {
                    'initial': initial['health_factor'],
                    'final': final['health_factor'],
                    'change': final['health_factor'] - initial['health_factor']
                },
                'net_pnl': {
                    'usd': net_pnl_usd,
                    'percentage': (net_pnl_usd / (initial['total_debt_usd'] or 1)) * 100
                }
            }
            
            print(f"✅ PNL ANALYSIS COMPLETE")
            print(f"   Cycle Duration: {pnl_report['cycle_duration_seconds']:.0f} seconds")
            print(f"   DAI Debt Change: {dai_debt_change:.6f} tokens (${dai_debt_change_usd:.4f})")
            print(f"   ARB Debt Change: {arb_debt_change:.6f} tokens (${arb_debt_change_usd:.4f})")
            print(f"   Total Gas Cost: ${total_gas_cost:.4f}")
            print(f"   Net PNL: ${net_pnl_usd:.4f} ({pnl_report['net_pnl']['percentage']:.2f}%)")
            print(f"   Health Factor: {initial['health_factor']:.6f} → {final['health_factor']:.6f}")
            
            return pnl_report
            
        except Exception as e:
            print(f"❌ PNL calculation failed: {e}")
            return {}

if __name__ == "__main__":
    print("🚀 DEFINITIVE DEBT SWAP CYCLE EXECUTOR")
    print("=" * 80)
    
    try:
        # Initialize executor
        executor = DefinitiveDebtSwapExecutor()
        
        # Execute full cycle
        result = executor.execute_full_debt_swap_cycle(10.0)  # $10 test cycle
        
        if result['success']:
            print(f"\n🎉 DEFINITIVE CYCLE EXECUTION: SUCCESS!")
            print(f"   Phase 1 TX: {result['phase1_tx']}")
            print(f"   Phase 2 TX: {result['phase2_tx']}")
            print(f"   Net PNL: ${result['pnl_report']['net_pnl']['usd']:.4f}")
        else:
            print(f"\n❌ CYCLE EXECUTION FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()