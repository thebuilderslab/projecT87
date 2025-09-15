#!/usr/bin/env python3
"""
PRODUCTION DEBT SWAP CYCLE EXECUTOR
Consolidated implementation with deterministic validation and comprehensive PNL tracking.
Verifiable execution: DAI debt → ARB debt → wait 5min → ARB debt → DAI debt.
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

class ProductionDebtSwapExecutor:
    """Production-ready consolidated debt swap executor with comprehensive validation"""
    
    def __init__(self, private_key: str = None):
        """Initialize with comprehensive setup and validation"""
        # Load private key from parameter or environment
        self.private_key = private_key or os.getenv('PRIVATE_KEY')
        if not self.private_key:
            raise ValueError("Private key not provided and no PRIVATE_KEY environment variable set")
        
        # Initialize Web3 connection
        rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to Arbitrum RPC: {rpc_url}")
        
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
        
        # Initialize PNL tracking
        self.cycle_data = {
            'cycle_id': f"debt_swap_cycle_{int(time.time())}",
            'start_time': None,
            'end_time': None,
            'phase1_execution': {},
            'phase2_execution': {},
            'initial_positions': {},
            'intermediate_positions': {},
            'final_positions': {},
            'price_snapshots': {},
            'gas_costs_total': Decimal('0'),
            'pnl_analysis': {},
            'transaction_receipts': [],
            'verification_links': []
        }
        
        print(f"🔧 PRODUCTION Debt Swap Cycle Executor Initialized")
        print(f"   User: {self.user_address}")
        print(f"   RPC: {rpc_url}")
        print(f"   Cycle ID: {self.cycle_data['cycle_id']}")
        print(f"   All verification components active")

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
            prices = self.get_current_prices()
            
            position = {
                'total_collateral_usd': float(account_data[0]) / (10**8),
                'total_debt_usd': float(account_data[1]) / (10**8),
                'available_borrows_usd': float(account_data[2]) / (10**8),
                'health_factor': float(account_data[5]) / (10**18) if account_data[5] > 0 else float('inf'),
                'debt_balances': debt_balances,
                'debt_values_usd': {
                    'DAI': debt_balances['DAI'] * prices['DAI'],
                    'ARB': debt_balances['ARB'] * prices['ARB']
                },
                'prices': prices,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ POSITION SNAPSHOT:")
            print(f"   Total Collateral: ${position['total_collateral_usd']:.2f}")
            print(f"   Total Debt: ${position['total_debt_usd']:.2f}")
            print(f"   Available Borrows: ${position['available_borrows_usd']:.2f}")
            print(f"   Health Factor: {position['health_factor']:.6f}")
            print(f"   DAI Debt: {debt_balances['DAI']:.6f} (${position['debt_values_usd']['DAI']:.2f})")
            print(f"   ARB Debt: {debt_balances['ARB']:.6f} (${position['debt_values_usd']['ARB']:.2f})")
            
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
            print(f"   Expected Amount: {result['expected_amount']}")
            print(f"   Calldata Length: {len(result['calldata'])} chars")
            
            return result
            
        except Exception as e:
            print(f"❌ ParaSwap error: {e}")
            import traceback
            print(f"🔍 Full error: {traceback.format_exc()}")
            return {}

    def create_credit_delegation_permit(self, debt_token_address: str) -> Dict:
        """Create CORRECT EIP-712 credit delegation permit per Aave V3 specification"""
        try:
            print(f"📝 Creating CORRECT credit delegation permit")
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
            token_name = debt_token_contract.functions.name().call()
            nonce = debt_token_contract.functions.nonces(self.user_address).call()
            deadline = int(time.time()) + 3600  # 1 hour
            
            print(f"   Token Name: {token_name}")
            print(f"   User: {self.user_address}")
            print(f"   Nonce: {nonce}")
            
            # CORRECT EIP-712 domain (Aave V3 standard)
            domain = {
                'name': token_name,
                'version': '1',  # Aave V3 uses version 1
                'chainId': 42161,
                'verifyingContract': debt_token_address
            }
            
            # CORRECT Aave V3 EIP-712 types
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
            
            # Correct Aave V3 message (owner recovered from signature)
            message = {
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,  # Max approval
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
                'value': 2**256 - 1,
                'deadline': deadline,
                'v': signature.v,
                'r': signature.r.to_bytes(32, 'big'),  # Convert to bytes32
                's': signature.s.to_bytes(32, 'big')   # Convert to bytes32
            }
            
            print(f"✅ CORRECT credit delegation permit created")
            
            return permit_data
            
        except Exception as e:
            print(f"❌ Error creating credit delegation permit: {e}")
            return {}

    def decode_revert_reason(self, revert_data: str) -> str:
        """Decode revert reason from contract call failure"""
        try:
            if not revert_data or revert_data == '0x':
                return "No revert data available"
            
            # Remove 0x prefix
            if revert_data.startswith('0x'):
                revert_data = revert_data[2:]
            
            # Standard Error(string) selector: 0x08c379a0
            error_selector = revert_data[:8]
            
            if error_selector == '08c379a0':  # Error(string)
                try:
                    # Decode as ABI-encoded string
                    from web3 import Web3
                    decoded = Web3.to_text(hexstr='0x' + revert_data[8:])
                    return f"Error(string): {decoded}"
                except:
                    try:
                        # Fallback: direct hex decode
                        string_data = revert_data[8+64:]  # Skip selector and offset
                        length = int(revert_data[8+64:8+128], 16) * 2  # Length in chars
                        message_hex = string_data[:length]
                        message = bytes.fromhex(message_hex).decode('utf-8', errors='ignore')
                        return f"Error(string): {message}"
                    except:
                        return f"Error(string): Unable to decode - {revert_data[:100]}..."
            
            # Custom error selectors (common Aave/ParaSwap errors)
            custom_errors = {
                '579952fc': 'INVALID_AMOUNT',
                'cd4e6167': 'INVALID_TOKEN', 
                'f4d678b8': 'INSUFFICIENT_LIQUIDITY',
                '48f5c3ed': 'INVALID_SIGNATURE',
                'eb7e8b22': 'EXPIRED_PERMIT',
                '3774c25c': 'INVALID_DELEGATEE',
                '08c379a0': 'GENERIC_ERROR',
                '4e487b71': 'PANIC_ERROR',
                'aa7d5d0a': 'INSUFFICIENT_COLLATERAL',
                '70f4a398': 'INVALID_CREDIT_DELEGATION'
            }
            
            if error_selector in custom_errors:
                return f"Custom Error: {custom_errors[error_selector]} (0x{error_selector})"
            
            # Unknown custom error
            return f"Unknown Custom Error: 0x{error_selector} (data: {revert_data[:100]}...)"
            
        except Exception as e:
            return f"Revert reason decode failed: {str(e)} (raw: {revert_data[:100]}...)"

    def eth_call_preflight(self, transaction_data: Dict) -> Tuple[bool, str]:
        """Perform eth_call preflight to capture revert reasons before on-chain execution"""
        try:
            print(f"\n🔍 ETH_CALL PREFLIGHT TEST")
            print("=" * 50)
            print(f"Testing transaction before on-chain execution...")
            
            # Prepare eth_call parameters
            call_params = {
                'to': transaction_data['to'],
                'from': transaction_data['from'],
                'data': transaction_data['data'],
                'gas': transaction_data.get('gas', 1000000),  # Use provided gas or 1M for testing
                'gasPrice': transaction_data.get('gasPrice', 0),
                'value': transaction_data.get('value', 0)
            }
            
            print(f"📋 Call Parameters:")
            print(f"   To: {call_params['to']}")
            print(f"   From: {call_params['from']}")
            print(f"   Gas: {call_params['gas']:,}")
            print(f"   Data Length: {len(call_params['data'])} chars")
            
            # Execute eth_call (static call)
            try:
                result = self.w3.eth.call(call_params, 'latest')
                print(f"✅ ETH_CALL SUCCESS")
                print(f"   Return Data: {result.hex() if result else '0x'}")
                print(f"   Transaction would succeed on-chain")
                return True, "ETH_CALL successful - transaction should execute"
                
            except ContractLogicError as cle:
                # Web3.py detected a revert with decoded reason
                revert_reason = str(cle)
                print(f"❌ ETH_CALL REVERT (ContractLogicError)")
                print(f"   Decoded Reason: {revert_reason}")
                return False, f"Contract Logic Error: {revert_reason}"
                
            except Exception as call_error:
                # Raw revert data or other error
                error_str = str(call_error)
                print(f"❌ ETH_CALL FAILED")
                print(f"   Raw Error: {error_str}")
                
                # Try to extract revert data from error message
                revert_data = None
                if 'revert' in error_str.lower():
                    import re
                    hex_pattern = r'0x[a-fA-F0-9]+'
                    matches = re.findall(hex_pattern, error_str)
                    for match in matches:
                        if len(match) > 10:  # Skip short hex values
                            revert_data = match
                            break
                
                if revert_data:
                    decoded_reason = self.decode_revert_reason(revert_data)
                    print(f"   Decoded Revert: {decoded_reason}")
                    return False, f"ETH_CALL reverted: {decoded_reason}"
                else:
                    return False, f"ETH_CALL failed: {error_str}"
                    
        except Exception as e:
            error_msg = f"ETH_CALL preflight failed: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
        
        finally:
            print("=" * 50)

    def validate_position_for_swap(self, swap_amount_usd: float) -> Tuple[bool, str]:
        """Validate that position has adequate DAI debt for swapping"""
        try:
            position = self.get_aave_position()
            
            if not position:
                return False, "Could not fetch Aave position"
            
            dai_debt_usd = position['debt_values_usd']['DAI']
            health_factor = position['health_factor']
            
            # Minimum requirements
            min_dai_debt = swap_amount_usd * 1.1  # 10% buffer
            min_health_factor = 1.5  # Safety margin
            
            if dai_debt_usd < min_dai_debt:
                return False, f"Insufficient DAI debt: ${dai_debt_usd:.2f} < ${min_dai_debt:.2f} required"
            
            if health_factor < min_health_factor:
                return False, f"Health factor too low: {health_factor:.3f} < {min_health_factor} required"
            
            print(f"✅ Position validation passed:")
            print(f"   DAI debt: ${dai_debt_usd:.2f} (${min_dai_debt:.2f} required)")
            print(f"   Health factor: {health_factor:.3f} (>{min_health_factor} required)")
            
            return True, "Position validation successful"
            
        except Exception as e:
            return False, f"Position validation failed: {e}"

    def execute_debt_swap(self, from_asset: str, to_asset: str, swap_amount_usd: float) -> Dict:
        """Execute single debt swap with comprehensive validation and artifact persistence"""
        
        execution_result = {
            'operation': f'{from_asset}_debt_to_{to_asset}_debt_swap',
            'start_time': datetime.now().isoformat(),
            'swap_amount_usd': swap_amount_usd,
            'success': False,
            'preflight_validation': {},
            'transaction_hash': None,
            'transaction_receipt': None,
            'gas_used': 0,
            'gas_cost_eth': 0,
            'position_before': {},
            'position_after': {}
        }
        
        try:
            print(f"\n🔄 EXECUTING DEBT SWAP")
            print("=" * 60)
            print(f"Operation: {from_asset} debt → {to_asset} debt")
            print(f"Amount: ${swap_amount_usd:.2f}")
            print(f"User: {self.user_address}")
            print("=" * 60)
            
            # 1. Position validation
            execution_result['position_before'] = self.get_aave_position()
            
            valid, validation_msg = self.validate_position_for_swap(swap_amount_usd)
            if not valid:
                execution_result['error'] = validation_msg
                return execution_result
            
            # 2. Get debt token addresses
            new_debt_token = self.get_debt_token_address(to_asset)
            if not new_debt_token:
                execution_result['error'] = f"Failed to get {to_asset} debt token address"
                return execution_result
            
            # 3. Calculate swap amount in wei
            if from_asset.upper() == 'DAI':
                amount_wei = int(swap_amount_usd * 1e18)  # DAI = $1
            elif from_asset.upper() == 'ARB':
                arb_price = execution_result['position_before']['prices']['ARB']
                amount_wei = int(swap_amount_usd / arb_price * 1e18)
            else:
                execution_result['error'] = f"Unsupported asset: {from_asset}"
                return execution_result
            
            # 4. Get ParaSwap calldata
            paraswap_data = self.get_paraswap_calldata(from_asset, to_asset, amount_wei)
            if not paraswap_data:
                execution_result['error'] = "Failed to get ParaSwap calldata"
                return execution_result
            
            # Use exact amount from ParaSwap
            if 'expected_amount' in paraswap_data:
                amount_to_swap = int(paraswap_data['expected_amount'])
            else:
                amount_to_swap = amount_wei
            
            # 5. Create credit delegation permit
            credit_permit = self.create_credit_delegation_permit(new_debt_token)
            if not credit_permit:
                execution_result['error'] = "Failed to create credit delegation permit"
                return execution_result
            
            # 6. Build swapDebt transaction
            debt_swap_contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter,
                abi=self.debt_swap_abi
            )
            
            function_call = debt_swap_contract.functions.swapDebt(
                self.tokens[from_asset.upper()],  # assetToSwapFrom
                self.tokens[to_asset.upper()],    # assetToSwapTo  
                amount_to_swap,                   # amountToSwap
                bytes.fromhex(paraswap_data['calldata'][2:]),  # paraswapData
                (
                    credit_permit['token'],       # token
                    credit_permit['delegatee'],   # delegatee
                    credit_permit['value'],       # value
                    credit_permit['deadline'],    # deadline
                    credit_permit['v'],           # v
                    credit_permit['r'],           # r
                    credit_permit['s']            # s
                )
            )
            
            # 7. Gas estimation and preflight
            try:
                gas_estimate = function_call.estimate_gas({'from': self.user_address})
                gas_limit = int(gas_estimate * 1.2)
                
                print(f"✅ Gas estimation: {gas_estimate:,} (limit: {gas_limit:,})")
            except Exception as gas_error:
                execution_result['error'] = f"Gas estimation failed: {gas_error}"
                return execution_result
            
            # Build transaction data for preflight
            tx_data = function_call.build_transaction({
                'from': self.user_address,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            # 8. ETH_CALL preflight test
            preflight_success, preflight_msg = self.eth_call_preflight(tx_data)
            execution_result['preflight_validation'] = {
                'success': preflight_success,
                'message': preflight_msg
            }
            
            if not preflight_success:
                execution_result['error'] = f"Preflight failed: {preflight_msg}"
                return execution_result
            
            # 9. Execute transaction
            print(f"\n🚀 EXECUTING ON-CHAIN TRANSACTION")
            print("=" * 50)
            
            signed_tx = self.account.sign_transaction(tx_data)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            execution_result['transaction_hash'] = tx_hash.hex()
            
            print(f"📡 Transaction sent: {execution_result['transaction_hash']}")
            print(f"⏳ Waiting for confirmation...")
            
            # 10. Wait for receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            execution_result['transaction_receipt'] = dict(tx_receipt)
            execution_result['gas_used'] = tx_receipt['gasUsed']
            execution_result['gas_cost_eth'] = float(tx_receipt['gasUsed'] * tx_receipt['effectiveGasPrice']) / 1e18
            
            if tx_receipt['status'] == 1:
                print(f"✅ TRANSACTION SUCCESSFUL")
                print(f"   Gas Used: {tx_receipt['gasUsed']:,}")
                print(f"   Gas Cost: {execution_result['gas_cost_eth']:.6f} ETH")
                
                execution_result['success'] = True
                
                # Get post-swap position
                time.sleep(2)  # Brief delay for state to update
                execution_result['position_after'] = self.get_aave_position()
                
            else:
                execution_result['error'] = "Transaction failed on-chain"
                
            return execution_result
            
        except Exception as e:
            execution_result['error'] = f"Execution failed: {str(e)}"
            import traceback
            print(f"❌ Execution error: {traceback.format_exc()}")
            return execution_result

    def execute_full_cycle(self, swap_amount_usd: float = 2.0) -> Dict:
        """Execute complete DAI→ARB→wait 5min→ARB→DAI cycle with comprehensive tracking"""
        
        print(f"\n🎯 STARTING COMPLETE DEBT SWAP CYCLE")
        print("=" * 80)
        print(f"Cycle ID: {self.cycle_data['cycle_id']}")
        print(f"Amount: ${swap_amount_usd:.2f} per swap")
        print("=" * 80)
        
        self.cycle_data['start_time'] = datetime.now().isoformat()
        self.cycle_data['initial_positions'] = self.get_aave_position()
        self.cycle_data['price_snapshots']['start'] = self.get_current_prices()
        
        # Phase 1: DAI debt → ARB debt
        print(f"\n📍 PHASE 1: DAI DEBT → ARB DEBT")
        phase1_result = self.execute_debt_swap('DAI', 'ARB', swap_amount_usd)
        self.cycle_data['phase1_execution'] = phase1_result
        
        if not phase1_result['success']:
            print(f"❌ Phase 1 failed: {phase1_result.get('error', 'Unknown error')}")
            return self.cycle_data
        
        # Add transaction receipt to artifacts
        if phase1_result.get('transaction_receipt'):
            self.cycle_data['transaction_receipts'].append({
                'phase': 'phase1',
                'receipt': phase1_result['transaction_receipt']
            })
        
        self.cycle_data['intermediate_positions'] = self.get_aave_position()
        self.cycle_data['gas_costs_total'] += Decimal(str(phase1_result['gas_cost_eth']))
        
        print(f"✅ Phase 1 complete! Gas cost: {phase1_result['gas_cost_eth']:.6f} ETH")
        
        # 5-minute wait
        print(f"\n⏰ WAITING 5 MINUTES BETWEEN PHASES...")
        wait_start = time.time()
        for i in range(300):  # 5 minutes = 300 seconds
            remaining = 300 - i
            if remaining % 60 == 0:  # Print every minute
                print(f"⏳ {remaining // 60} minutes remaining...")
            time.sleep(1)
        
        wait_duration = time.time() - wait_start
        print(f"✅ Wait complete: {wait_duration:.1f} seconds")
        
        # Phase 2: ARB debt → DAI debt
        print(f"\n📍 PHASE 2: ARB DEBT → DAI DEBT")
        phase2_result = self.execute_debt_swap('ARB', 'DAI', swap_amount_usd)
        self.cycle_data['phase2_execution'] = phase2_result
        
        if not phase2_result['success']:
            print(f"❌ Phase 2 failed: {phase2_result.get('error', 'Unknown error')}")
            return self.cycle_data
        
        # Add transaction receipt to artifacts
        if phase2_result.get('transaction_receipt'):
            self.cycle_data['transaction_receipts'].append({
                'phase': 'phase2',
                'receipt': phase2_result['transaction_receipt']
            })
        
        self.cycle_data['final_positions'] = self.get_aave_position()
        self.cycle_data['gas_costs_total'] += Decimal(str(phase2_result['gas_cost_eth']))
        self.cycle_data['end_time'] = datetime.now().isoformat()
        self.cycle_data['price_snapshots']['end'] = self.get_current_prices()
        
        print(f"✅ Phase 2 complete! Gas cost: {phase2_result['gas_cost_eth']:.6f} ETH")
        
        # Generate PNL analysis
        self.cycle_data['pnl_analysis'] = self.calculate_cycle_pnl()
        
        # Generate verification links
        for receipt in self.cycle_data['transaction_receipts']:
            tx_hash = receipt['receipt']['transactionHash'].hex()
            arbiscan_link = f"https://arbiscan.io/tx/{tx_hash}"
            self.cycle_data['verification_links'].append({
                'phase': receipt['phase'],
                'transaction_hash': tx_hash,
                'arbiscan_url': arbiscan_link
            })
        
        print(f"\n🎉 CYCLE COMPLETE!")
        print(f"   Total Gas Cost: {float(self.cycle_data['gas_costs_total']):.6f} ETH")
        print(f"   Duration: {self.cycle_data['end_time']} - {self.cycle_data['start_time']}")
        
        return self.cycle_data

    def calculate_cycle_pnl(self) -> Dict:
        """Calculate comprehensive PNL analysis for the complete cycle"""
        try:
            initial = self.cycle_data['initial_positions']
            final = self.cycle_data['final_positions']
            
            if not initial or not final:
                return {'error': 'Missing position data for PNL calculation'}
            
            # Calculate debt changes
            dai_debt_change = final['debt_balances']['DAI'] - initial['debt_balances']['DAI']
            arb_debt_change = final['debt_balances']['ARB'] - initial['debt_balances']['ARB']
            
            # Calculate USD values
            end_prices = self.cycle_data['price_snapshots']['end']
            dai_debt_change_usd = dai_debt_change * end_prices['DAI']
            arb_debt_change_usd = arb_debt_change * end_prices['ARB']
            
            total_debt_change_usd = final['total_debt_usd'] - initial['total_debt_usd']
            
            # Gas costs
            gas_cost_eth = float(self.cycle_data['gas_costs_total'])
            eth_price = 3000  # Approximate ETH price for USD calculation
            gas_cost_usd = gas_cost_eth * eth_price
            
            # Net PNL
            gross_pnl_usd = -total_debt_change_usd  # Negative debt change is profit
            net_pnl_usd = gross_pnl_usd - gas_cost_usd
            
            pnl_analysis = {
                'debt_changes': {
                    'DAI': {
                        'tokens': dai_debt_change,
                        'usd': dai_debt_change_usd
                    },
                    'ARB': {
                        'tokens': arb_debt_change,
                        'usd': arb_debt_change_usd
                    }
                },
                'total_debt_change_usd': total_debt_change_usd,
                'gas_costs': {
                    'eth': gas_cost_eth,
                    'usd': gas_cost_usd
                },
                'pnl': {
                    'gross_usd': gross_pnl_usd,
                    'net_usd': net_pnl_usd,
                    'net_percentage': (net_pnl_usd / (initial['total_debt_usd'] or 1)) * 100
                },
                'health_factor_change': final['health_factor'] - initial['health_factor'],
                'efficiency_metrics': {
                    'gas_cost_percentage': (gas_cost_usd / abs(gross_pnl_usd or 1)) * 100,
                    'cycle_duration_minutes': self.get_cycle_duration_minutes()
                }
            }
            
            return pnl_analysis
            
        except Exception as e:
            return {'error': f'PNL calculation failed: {e}'}

    def get_cycle_duration_minutes(self) -> float:
        """Calculate cycle duration in minutes"""
        try:
            start = datetime.fromisoformat(self.cycle_data['start_time'])
            end = datetime.fromisoformat(self.cycle_data['end_time'])
            duration = (end - start).total_seconds() / 60
            return duration
        except:
            return 0.0

    def save_cycle_artifacts(self, filename: str = None) -> str:
        """Save complete cycle artifacts to JSON file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"debt_swap_cycle_{timestamp}.json"
            
            # Convert any Decimal objects to float for JSON serialization
            def decimal_converter(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                return obj
            
            # Create a copy and convert decimals
            cycle_data_copy = json.loads(json.dumps(self.cycle_data, default=decimal_converter))
            
            with open(filename, 'w') as f:
                json.dump(cycle_data_copy, f, indent=2, default=str)
            
            print(f"📄 Cycle artifacts saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving artifacts: {e}")
            return ""

if __name__ == "__main__":
    # Quick test execution
    try:
        executor = ProductionDebtSwapExecutor()
        
        # Test minimal position validation
        position = executor.get_aave_position()
        if position:
            print("✅ Executor initialized successfully")
            
            # Test components
            dai_debt_token = executor.get_debt_token_address('ARB')
            if dai_debt_token:
                print("✅ Debt token retrieval working")
            
            print("\n🎯 Ready for debt swap cycle execution")
        else:
            print("❌ Could not fetch position data")
            
    except Exception as e:
        print(f"❌ Initialization failed: {e}")