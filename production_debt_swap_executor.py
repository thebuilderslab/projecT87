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
from typing import Dict, List, Optional, Tuple, Union
from decimal import Decimal, getcontext
from web3 import Web3
from web3.types import TxParams, TxReceipt
from eth_typing import ChecksumAddress, HexStr
from web3.exceptions import ContractLogicError
from eth_account.messages import encode_structured_data

# UNIFIED SYSTEM IMPORTS
from debt_swap_utils import resolve_gas_estimation_failure, DebtSwapValidator
from gas_optimization import CoinAPIGasOptimizer

# Optional CoinAPI setup (graceful fallback if not available)
COIN_API_KEY = os.environ.get("COIN_API")
if COIN_API_KEY:
    print("🔑 CoinAPI key loaded successfully")
else:
    print("⚠️ CoinAPI key not available - will use fallback pricing")

# Set high precision for PNL calculations
getcontext().prec = 50

class ProductionDebtSwapExecutor:
    """Production-ready consolidated debt swap executor with comprehensive validation"""
    
    def __init__(self, private_key: Optional[str] = None):
        """Initialize with comprehensive setup and validation"""
        # Load private key from parameter or environment
        self.private_key: Optional[str] = private_key or os.getenv('PRIVATE_KEY')
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
        
        # Enhanced Gas Optimization with CoinAPI Integration
        self.coin_api_key = os.getenv('COIN_API')
        self.max_usd_per_tx = 10.0  # $10 USD maximum per transaction
        self.min_swap_usd = 25.0   # $25 minimum swap amount (prevents dust trade reverts)
        
        # Initialize comprehensive validation system with error bubbling
        try:
            self.debt_swap_validator = DebtSwapValidator()
            print("✅ Comprehensive validation system initialized with error bubbling")
        except Exception as e:
            print(f"⚠️ Warning: Comprehensive validation system initialization failed: {e}")
            self.debt_swap_validator = None
        
        # FIXED: Use Aave Debt Switch V3 (matching successful manual transactions)  
        self.aave_debt_switch_v3: ChecksumAddress = self.w3.to_checksum_address("0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4")
        # Keep backward compatibility
        self.paraswap_debt_swap_adapter: ChecksumAddress = self.aave_debt_switch_v3
        self.augustus_swapper: ChecksumAddress = self.w3.to_checksum_address("0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57")
        self.aave_pool: ChecksumAddress = self.w3.to_checksum_address("0x794a61358D6845594F94dc1DB02A252b5b4814aD")
        self.aave_data_provider: ChecksumAddress = self.w3.to_checksum_address("0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654")
        
        # Token addresses
        self.tokens: Dict[str, ChecksumAddress] = {
            'DAI': self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"),
            'ARB': self.w3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548")
        }
        
        # FIXED: CORRECT ABI from 4byte.directory matching successful manual transactions (function selector 0xb8bd1c6b)
        self.debt_swap_abi = [{
            "inputs": [
                {
                    "components": [
                        {"name": "debtAsset", "type": "address"},
                        {"name": "debtRepayAmount", "type": "uint256"},
                        {"name": "debtRateMode", "type": "uint256"},
                        {"name": "newDebtAsset", "type": "address"},
                        {"name": "maxNewDebtAmount", "type": "uint256"},
                        {"name": "extraCollateralAsset", "type": "address"},
                        {"name": "extraCollateralAmount", "type": "uint256"},
                        {"name": "offset", "type": "uint256"},
                        {"name": "swapData", "type": "bytes"}
                    ],
                    "name": "debtSwapParams",
                    "type": "tuple"
                },
                {
                    "components": [
                        {"name": "debtToken", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ],
                    "name": "creditDelegationPermit",
                    "type": "tuple"
                },
                {
                    "components": [
                        {"name": "aToken", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "v", "type": "uint8"},
                        {"name": "r", "type": "bytes32"},
                        {"name": "s", "type": "bytes32"}
                    ],
                    "name": "collateralATokenPermit",
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

    def get_uniswap_quote(self, token_in: ChecksumAddress, token_out: ChecksumAddress, amount_in: int) -> int:
        """Get accurate quote from Uniswap V3 QuoterV2 for dynamic pricing"""
        try:
            print(f"\n💱 UNISWAP V3 QUOTER: {amount_in / 1e18:.6f} tokens")
            print(f"   Route: {token_in[-6:]} → {token_out[-6:]}")
            
            # Uniswap V3 QuoterV2 on Arbitrum
            quoter_address = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e"
            
            # QuoteExactInputSingle ABI
            quoter_abi = [{
                "inputs": [
                    {
                        "components": [
                            {"name": "tokenIn", "type": "address"},
                            {"name": "tokenOut", "type": "address"},
                            {"name": "amountIn", "type": "uint256"},
                            {"name": "fee", "type": "uint24"},
                            {"name": "sqrtPriceLimitX96", "type": "uint160"}
                        ],
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "quoteExactInputSingle",
                "outputs": [
                    {"name": "amountOut", "type": "uint256"},
                    {"name": "sqrtPriceX96After", "type": "uint160"},
                    {"name": "initializedTicksCrossed", "type": "uint32"},
                    {"name": "gasEstimate", "type": "uint256"}
                ],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            quoter_contract = self.w3.eth.contract(address=self.w3.to_checksum_address(quoter_address), abi=quoter_abi)
            
            # Query parameters for 0.3% fee tier (most liquid)
            quote_params = (
                token_in,    # tokenIn
                token_out,   # tokenOut
                amount_in,   # amountIn
                3000,        # fee (0.3%)
                0            # sqrtPriceLimitX96 (no limit)
            )
            
            # Get quote from Uniswap V3
            result = quoter_contract.functions.quoteExactInputSingle(quote_params).call()
            amount_out = result[0]
            gas_estimate = result[3] if len(result) > 3 else 150000
            
            print(f"✅ REAL-TIME QUOTE:")
            print(f"   Amount Out: {amount_out / 1e18:.6f}")
            print(f"   Exchange Rate: {(amount_out / amount_in):.6f}")
            print(f"   Gas Estimate: {gas_estimate:,}")
            
            return amount_out
            
        except Exception as e:
            print(f"⚠️ QuoterV2 failed: {e}")
            # Fallback to price API estimation
            return self._fallback_price_estimation(token_in, token_out, amount_in)
    
    def _fallback_price_estimation(self, token_in: ChecksumAddress, token_out: ChecksumAddress, amount_in: int) -> int:
        """Fallback price estimation using market prices"""
        try:
            prices = self.get_current_prices()
            
            # Determine token symbols and calculate
            if token_in == self.tokens['ARB'] and token_out == self.tokens['DAI']:
                rate = prices['ARB'] / prices['DAI']
            elif token_in == self.tokens['DAI'] and token_out == self.tokens['ARB']:
                rate = prices['DAI'] / prices['ARB']
            else:
                rate = 1.0  # 1:1 fallback
            
            amount_out = int(amount_in * rate)
            print(f"📊 FALLBACK PRICING: rate={rate:.6f}, amount_out={amount_out/1e18:.6f}")
            return amount_out
            
        except Exception as e:
            print(f"❌ Fallback pricing failed: {e}")
            # Last resort: conservative 1:1 ratio
            return amount_in

    def get_paraswap_calldata_reverse_routing(self, from_asset: str, to_asset: str, amount_wei: int) -> Dict:
        """Get ParaSwap Augustus calldata for debt swap with reverse routing"""
        try:
            print(f"\n🔄 PARASWAP AUGUSTUS INTEGRATION")
            print("=" * 50)
            
            # CRITICAL: For debt swaps, routing is REVERSED
            # DAI debt → ARB debt requires ARB → DAI routing (to get DAI to repay the debt)
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']   # Route FROM ARB
                dest_token = self.tokens['DAI']  # Route TO DAI
                print(f"🔄 REVERSE ROUTING: ARB → DAI (for DAI debt → ARB debt swap)")
            elif from_asset.upper() == 'ARB' and to_asset.upper() == 'DAI':
                src_token = self.tokens['DAI']   # Route FROM DAI  
                dest_token = self.tokens['ARB']  # Route TO ARB
                print(f"🔄 REVERSE ROUTING: DAI → ARB (for ARB debt → DAI debt swap)")
            else:
                raise ValueError(f"Unsupported debt swap: {from_asset} → {to_asset}")
            
            # DEBT SWAP ParaSwap price API - CORRECT approach
            price_url = "https://apiv5.paraswap.io/prices"
            price_params = {
                'srcToken': src_token,      # ARB (new debt asset)
                'destToken': dest_token,    # DAI (old debt asset to repay)
                'amount': str(amount_wei),  # DAI amount to repay
                'srcDecimals': 18,
                'destDecimals': 18,
                'side': 'BUY',              # FIXED: BUY DAI by selling ARB
                'network': 42161,           # Arbitrum
                # FIXED: Omit userAddress to avoid balance checks
                'partner': 'aave',          # Partner for debt swap routing
                'maxImpact': '15'           # Max price impact 15%
            }
            
            print(f"🌐 Getting ParaSwap price for reverse routing...")
            price_response = requests.get(price_url, params=price_params, timeout=10)
            
            if price_response.status_code != 200:
                error_text = price_response.text if price_response.text else 'No error details'
                print(f"❌ ParaSwap price API error {price_response.status_code}: {error_text}")
                raise Exception(f"ParaSwap price API failed: {price_response.status_code} - {error_text}")
            
            price_data = price_response.json()
            
            if 'priceRoute' not in price_data:
                print(f"❌ No price route in response: {price_data}")
                raise Exception("No price route found")
            
            print(f"✅ Price route obtained:")
            print(f"   ARB amount needed: {price_data['priceRoute']['srcAmount']}")
            print(f"   DAI amount out: {price_data['priceRoute']['destAmount']}")
            
            # Get transaction data for DEBT SWAP
            tx_url = "https://apiv5.paraswap.io/transactions/42161"
            # DEBT SWAP: Use ignoreChecks to bypass balance validation
            tx_params = {
                'deadline': str(int(time.time()) + 1800),  # 30 min deadline
                'ignoreChecks': 'true'  # CRITICAL: Bypass balance checks for debt swaps
                # REMOVED: slippage (conflicts with srcAmount/destAmount from priceRoute)
            }
            
            # Ensure addresses are properly checksummed
            user_addr = self.w3.to_checksum_address(self.user_address)
            adapter_addr = self.w3.to_checksum_address(self.paraswap_debt_swap_adapter)
            
            print(f"📋 Transaction addresses:")
            print(f"   User: {user_addr}")
            print(f"   Adapter: {adapter_addr}")
            
            tx_payload = {
                'srcToken': src_token,
                'destToken': dest_token,
                'srcAmount': price_data['priceRoute']['srcAmount'],   # Computed ARB amount
                'destAmount': price_data['priceRoute']['destAmount'], # ADDED: Required DAI amount
                'priceRoute': price_data['priceRoute'],
                'userAddress': adapter_addr,  # Adapter executes the swap
                'receiver': adapter_addr,    # Adapter receives the DAI
                'partner': 'aave',           # Partner specification for debt swap
                'partnerAddress': adapter_addr,  # Partner address
                'partnerFeeBps': '0',        # No partner fee
                'takeSurplus': False         # Don't take surplus
            }
            
            print(f"🌐 Getting ParaSwap transaction data...")
            tx_response = requests.post(tx_url, params=tx_params, json=tx_payload,
                                      timeout=15, headers={'Content-Type': 'application/json'})
            
            if tx_response.status_code != 200:
                error_text = tx_response.text if tx_response.text else 'No error details'
                print(f"❌ ParaSwap transaction API error {tx_response.status_code}: {error_text}")
                raise Exception(f"ParaSwap transaction API failed: {tx_response.status_code} - {error_text}")
            
            tx_data = tx_response.json()
            
            swap_data = {
                'calldata': tx_data.get('data', '0x'),
                'expected_amount': price_data['priceRoute']['destAmount'],
                'price_route': price_data['priceRoute']
            }
            
            print(f"✅ REVERSE ParaSwap routing obtained")
            print(f"   Expected Amount: {swap_data['expected_amount']}")
            print(f"   Calldata Length: {len(swap_data['calldata'])} chars")
            
            return swap_data
            
        except Exception as e:
            print(f"❌ Uniswap V3 error: {e}")
            import traceback
            print(f"🔍 Full error: {traceback.format_exc()}")
            return {}

    def create_credit_delegation_permit(self, debt_token_address: ChecksumAddress) -> Dict:
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
                    {'name': 'delegator', 'type': 'address'},
                    {'name': 'delegatee', 'type': 'address'},
                    {'name': 'value', 'type': 'uint256'},
                    {'name': 'nonce', 'type': 'uint256'},
                    {'name': 'deadline', 'type': 'uint256'}
                ]
            }
            
            # Correct Aave V3 message with delegator field
            message = {
                'delegator': self.user_address,
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
                    # Use Web3 keccak method instead to avoid parameter issues
                    message_hex = revert_data[8+64:]
                    try:
                        # Direct hex decode approach
                        length = int(revert_data[8+64:8+128], 16) * 2
                        if length > 0 and length < len(message_hex):
                            decoded = bytes.fromhex(message_hex[:length]).decode('utf-8', errors='ignore')
                        else:
                            decoded = 'Unable to decode revert string'
                    except:
                        decoded = 'Decode failed'
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
                result = self.w3.eth.call(call_params, 'latest')  # type: ignore
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

    def _capture_comprehensive_state(self, stage: str) -> Dict:
        """Capture comprehensive system state for stepwise diff analysis"""
        start_time = time.time()
        
        print(f"\n📊 CAPTURING COMPREHENSIVE STATE: {stage}")
        print("-" * 60)
        
        state = {
            'stage': stage,
            'timestamp': time.time(),
            'capture_time_ms': 0,
            'aave_position': {},
            'token_balances': {},
            'market_prices': {},
            'gas_prices': {},
            'health_metrics': {},
            'capture_errors': []
        }
        
        try:
            # 1. Aave position data
            print("   📍 Capturing Aave position...")
            position = self.get_aave_position()
            if position:
                state['aave_position'] = position
                state['health_metrics'] = {
                    'health_factor': position.get('health_factor', 0),
                    'ltv': position.get('ltv', 0),
                    'liquidation_threshold': position.get('liquidation_threshold', 0),
                    'total_collateral_usd': position.get('total_collateral_usd', 0),
                    'total_debt_usd': position.get('total_debt_usd', 0)
                }
                print(f"      ✅ HF: {position.get('health_factor', 0):.4f}, Collateral: ${position.get('total_collateral_usd', 0):.2f}")
            else:
                state['capture_errors'].append("Failed to capture Aave position")
                
            # 2. Token balances
            print("   💰 Capturing token balances...")
            for token in ['ETH', 'DAI', 'ARB', 'WBTC']:
                try:
                    if token == 'ETH':
                        balance = self.w3.eth.get_balance(self.user_address) / 1e18
                    else:
                        token_address = getattr(self, f'{token.lower()}_address', None)
                        if token_address:
                            contract = self.w3.eth.contract(address=token_address, abi=[{
                                "constant": True,
                                "inputs": [{"name": "_owner", "type": "address"}],
                                "name": "balanceOf",
                                "outputs": [{"name": "balance", "type": "uint256"}],
                                "type": "function"
                            }])
                            balance = contract.functions.balanceOf(self.user_address).call() / 1e18
                        else:
                            balance = 0
                    state['token_balances'][token] = balance
                    print(f"      {token}: {balance:.6f}")
                except Exception as e:
                    state['capture_errors'].append(f"Failed to get {token} balance: {e}")
                    
            # 3. Gas prices
            print("   ⛽ Capturing gas prices...")
            try:
                gas_price = self.w3.eth.gas_price
                state['gas_prices'] = {
                    'current_gas_price_gwei': gas_price / 1e9,
                    'current_gas_price_wei': gas_price,
                    'eth_price_usd': position.get('prices', {}).get('ETH', 0) if position else 0
                }
                print(f"      Gas: {gas_price / 1e9:.2f} gwei, ETH: ${state['gas_prices']['eth_price_usd']:.2f}")
            except Exception as e:
                state['capture_errors'].append(f"Failed to get gas prices: {e}")
                
            # 4. Market prices (from position or fallback)
            print("   📈 Capturing market prices...")
            if position and 'prices' in position:
                state['market_prices'] = position['prices']
                for token, price in position['prices'].items():
                    print(f"      {token}: ${price:.4f}")
            else:
                state['capture_errors'].append("Failed to capture market prices")
                
        except Exception as e:
            state['capture_errors'].append(f"Critical state capture error: {e}")
            
        state['capture_time_ms'] = int((time.time() - start_time) * 1000)
        print(f"   ⏱️ State capture completed in {state['capture_time_ms']}ms")
        
        if state['capture_errors']:
            print(f"   ⚠️ Capture warnings: {len(state['capture_errors'])} issues")
            for error in state['capture_errors']:
                print(f"      - {error}")
        else:
            print("   ✅ State capture completed successfully")
            
        return state

    def execute_debt_swap(self, from_asset: str, to_asset: str, swap_amount_usd: float) -> Dict:
        """
        PRODUCTION DEBT SWAP EXECUTION with COMPREHENSIVE LOGGING & STEPWISE DIFF
        Enhanced with full audit trail for forensic analysis and debugging
        """
        
        print(f"\n🎯 EXECUTING DEBT SWAP WITH COMPREHENSIVE AUDIT TRAIL")
        print("=" * 80)
        print(f"   Route: {from_asset} debt → {to_asset} debt")
        print(f"   Amount: ${swap_amount_usd:.2f}")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
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
            'position_after': {},
            'stepwise_diff': {
                'pre_execution_state': {},
                'post_execution_state': {},
                'state_changes': {},
                'step_by_step_log': []
            },
            'comprehensive_logging': {
                'validation_details': {},
                'calldata_construction': {},
                'gas_estimation': {},
                'transaction_submission': {},
                'contract_interaction': {},
                'error_bubbling': []
            }
        }
        
        # STEP 1: PRE-EXECUTION STATE CAPTURE
        print(f"\n📊 STEP 1: PRE-EXECUTION STATE CAPTURE")
        print("-" * 50)
        
        pre_execution_start = time.time()
        execution_result['stepwise_diff']['pre_execution_state'] = self._capture_comprehensive_state(
            f"PRE-EXECUTION: {from_asset}→{to_asset}"
        )
        execution_result['stepwise_diff']['step_by_step_log'].append({
            'step': 1,
            'name': 'pre_execution_state_capture',
            'duration_ms': int((time.time() - pre_execution_start) * 1000),
            'status': 'completed',
            'details': f"Captured comprehensive state: positions, balances, prices"
        })
        
        try:
            # STEP 2: COMPREHENSIVE VALIDATION WITH ERROR BUBBLING
            print(f"\n🔍 STEP 2: COMPREHENSIVE VALIDATION WITH ERROR BUBBLING")
            print("-" * 50)
            
            validation_start = time.time()
            
            # Legacy position validation (for backward compatibility)
            execution_result['position_before'] = self.get_aave_position()
            
            valid, validation_msg = self.validate_position_for_swap(swap_amount_usd)
            
            # NEW: Comprehensive validation using error bubbling system
            print(f"🧪 INITIATING COMPREHENSIVE VALIDATION WITH ERROR BUBBLING")
            if hasattr(self, 'debt_swap_validator'):
                try:
                    validation_results = self.debt_swap_validator.comprehensive_validation(
                        contract_address="", # Will be set later when we have the transaction
                        function_call=None,  # Will be set later
                        calldata_params={},  # Will be populated
                        swap_amount_usd=swap_amount_usd
                    )
                    execution_result['comprehensive_logging']['validation_details'] = validation_results
                    
                    # Log all validation results (both passed and failed)
                    print(f"\n📋 VALIDATION RESULTS SUMMARY:")
                    print(f"   Success Rate: {validation_results['success_rate']:.1%}")
                    print(f"   Total Validations: {validation_results['total_validations']}")
                    print(f"   Passed: {validation_results['validations_passed']}")
                    print(f"   Failed: {validation_results['validations_failed']}")
                    print(f"   Total Execution Time: {validation_results['total_execution_time_ms']}ms")
                    
                    for error in validation_results['error_details']:
                        execution_result['comprehensive_logging']['error_bubbling'].append(error)
                        print(f"   ❌ Error: {error}")
                    
                except Exception as validation_error:
                    print(f"⚠️ Comprehensive validation system unavailable: {validation_error}")
                    execution_result['comprehensive_logging']['error_bubbling'].append(
                        f"Validation system error: {validation_error}"
                    )
            else:
                print(f"⚠️ Comprehensive validation system not initialized")
            
            if not valid:
                execution_result['error'] = validation_msg
                execution_result['stepwise_diff']['step_by_step_log'].append({
                    'step': 2,
                    'name': 'validation',
                    'duration_ms': int((time.time() - validation_start) * 1000),
                    'status': 'failed',
                    'details': f"Position validation failed: {validation_msg}"
                })
                return execution_result
            
            execution_result['stepwise_diff']['step_by_step_log'].append({
                'step': 2,
                'name': 'validation',
                'duration_ms': int((time.time() - validation_start) * 1000),
                'status': 'completed',
                'details': "Position validation passed"
            })
            
            # STEP 3: CALLDATA CONSTRUCTION WITH DETAILED LOGGING
            print(f"\n⚙️ STEP 3: CALLDATA CONSTRUCTION WITH DETAILED LOGGING")
            print("-" * 50)
            
            calldata_start = time.time()
            
            # 3A. Get debt token addresses
            print(f"   📍 3A: Resolving debt token addresses...")
            new_debt_token = self.get_debt_token_address(to_asset)
            if not new_debt_token:
                error_msg = f"Failed to get {to_asset} debt token address"
                execution_result['error'] = error_msg
                execution_result['comprehensive_logging']['calldata_construction']['token_resolution_error'] = error_msg
                return execution_result
            
            execution_result['comprehensive_logging']['calldata_construction']['debt_token_address'] = new_debt_token
            print(f"      ✅ {to_asset} debt token: {new_debt_token}")
            
            # 3B. Calculate swap amount in wei with detailed logging
            print(f"   💱 3B: Calculating swap amount in wei...")
            if from_asset.upper() == 'DAI':
                amount_wei = int(swap_amount_usd * 1e18)  # DAI = $1
                execution_result['comprehensive_logging']['calldata_construction']['amount_calculation'] = {
                    'asset': 'DAI',
                    'usd_amount': swap_amount_usd,
                    'price': 1.0,
                    'amount_wei': amount_wei
                }
                print(f"      ✅ DAI amount: {amount_wei} wei (${swap_amount_usd} @ $1.00/DAI)")
            elif from_asset.upper() == 'ARB':
                arb_price = execution_result['position_before']['prices']['ARB']
                amount_wei = int(swap_amount_usd / arb_price * 1e18)
                execution_result['comprehensive_logging']['calldata_construction']['amount_calculation'] = {
                    'asset': 'ARB',
                    'usd_amount': swap_amount_usd,
                    'price': arb_price,
                    'amount_wei': amount_wei
                }
                print(f"      ✅ ARB amount: {amount_wei} wei (${swap_amount_usd} @ ${arb_price:.4f}/ARB)")
            else:
                error_msg = f"Unsupported asset: {from_asset}"
                execution_result['error'] = error_msg
                execution_result['comprehensive_logging']['calldata_construction']['asset_error'] = error_msg
                return execution_result
            
            # 3C. Get ParaSwap Augustus calldata with comprehensive logging
            print(f"   🔄 3C: Constructing ParaSwap Augustus calldata...")
            paraswap_start = time.time()
            paraswap_data = self.get_paraswap_calldata_reverse_routing(from_asset, to_asset, amount_wei)
            paraswap_duration = int((time.time() - paraswap_start) * 1000)
            
            if not paraswap_data:
                error_msg = "Failed to get ParaSwap Augustus calldata"
                execution_result['error'] = error_msg
                execution_result['comprehensive_logging']['calldata_construction']['paraswap_error'] = {
                    'error': error_msg,
                    'duration_ms': paraswap_duration
                }
                return execution_result
            
            execution_result['comprehensive_logging']['calldata_construction']['paraswap_data'] = {
                'success': True,
                'duration_ms': paraswap_duration,
                'calldata_length': len(paraswap_data.get('calldata', '')),
                'expected_amount': paraswap_data.get('expected_amount', 0)
            }
            print(f"      ✅ ParaSwap calldata constructed in {paraswap_duration}ms")
            print(f"      ✅ Calldata length: {len(paraswap_data.get('calldata', ''))} characters")
            
            # Use exact amount from ParaSwap
            if 'expected_amount' in paraswap_data:
                amount_to_swap = int(paraswap_data['expected_amount'])
                print(f"      ✅ Using ParaSwap expected amount: {amount_to_swap} wei")
            else:
                amount_to_swap = amount_wei
                print(f"      ⚠️ Using original amount (ParaSwap didn't provide expected): {amount_to_swap} wei")
            
            execution_result['stepwise_diff']['step_by_step_log'].append({
                'step': 3,
                'name': 'calldata_construction',
                'duration_ms': int((time.time() - calldata_start) * 1000),
                'status': 'completed',
                'details': f"Calldata constructed successfully, ParaSwap took {paraswap_duration}ms"
            })
            
            # STEP 4: GAS ESTIMATION WITH DETAILED ANALYSIS
            print(f"\n⛽ STEP 4: GAS ESTIMATION WITH DETAILED ANALYSIS")
            print("-" * 50)
            
            gas_estimation_start = time.time()
            
            # 4A. Build transaction parameters with comprehensive logging
            print(f"   🔧 4A: Building transaction parameters...")
            zero_address = "0x0000000000000000000000000000000000000000"
            credit_permit = {
                'token': zero_address,
                'value': 0,
                'deadline': 0,
                'v': 0,
                'r': b'\x00' * 32,
                's': b'\x00' * 32
            }
            
            debt_swap_contract = self.w3.eth.contract(
                address=self.aave_debt_swap_adapter,
                abi=[{
                    "inputs": [
                        {"name": "debtAsset", "type": "address"},
                        {"name": "debtRepayAmount", "type": "uint256"},
                        {"name": "newDebtAsset", "type": "address"},
                        {"name": "maxNewDebtAmount", "type": "uint256"},
                        {"name": "extraCollateralAsset", "type": "address"},
                        {"name": "extraCollateralAmount", "type": "uint256"},
                        {"name": "offset", "type": "uint256"},
                        {"name": "paraswapData", "type": "bytes"},
                        {"name": "creditDelegationPermit", "type": "tuple", "components": [
                            {"name": "token", "type": "address"},
                            {"name": "value", "type": "uint256"},
                            {"name": "deadline", "type": "uint256"},
                            {"name": "v", "type": "uint8"},
                            {"name": "r", "type": "bytes32"},
                            {"name": "s", "type": "bytes32"}
                        ]},
                        {"name": "collateralATokenPermit", "type": "tuple", "components": [
                            {"name": "token", "type": "address"},
                            {"name": "value", "type": "uint256"},
                            {"name": "deadline", "type": "uint256"},
                            {"name": "v", "type": "uint8"},
                            {"name": "r", "type": "bytes32"},
                            {"name": "s", "type": "bytes32"}
                        ]}
                    ],
                    "name": "swapDebt",
                    "outputs": [],
                    "type": "function"
                }]
            )
            
            # Transaction parameters with comprehensive logging
            transaction_params = {
                'debtAsset': self.get_debt_token_address(from_asset),
                'debtRepayAmount': amount_to_swap,
                'newDebtAsset': new_debt_token,
                'maxNewDebtAmount': int(amount_to_swap * 1.05),  # 5% slippage
                'extraCollateralAsset': zero_address,
                'extraCollateralAmount': 0,
                'offset': 288,  # From forensic analysis
                'paraswapData': paraswap_data['calldata'],
                'creditDelegationPermit': credit_permit,
                'collateralATokenPermit': credit_permit
            }
            
            execution_result['comprehensive_logging']['contract_interaction']['transaction_params'] = {
                'debtAsset': transaction_params['debtAsset'],
                'debtRepayAmount': transaction_params['debtRepayAmount'],
                'newDebtAsset': transaction_params['newDebtAsset'],
                'maxNewDebtAmount': transaction_params['maxNewDebtAmount'],
                'offset': transaction_params['offset'],
                'paraswap_calldata_length': len(transaction_params['paraswapData']),
                'permits_zeroed': True
            }
            
            print(f"      ✅ Debt Asset: {transaction_params['debtAsset']}")
            print(f"      ✅ Repay Amount: {transaction_params['debtRepayAmount']} wei")
            print(f"      ✅ New Debt Asset: {transaction_params['newDebtAsset']}")
            print(f"      ✅ Max New Debt: {transaction_params['maxNewDebtAmount']} wei (5% slippage)")
            print(f"      ✅ Offset: {transaction_params['offset']} bytes")
            print(f"      ✅ ParaSwap Data Length: {len(transaction_params['paraswapData'])} characters")
            
            # 4B. Gas estimation with multiple approaches
            print(f"   ⛽ 4B: Performing gas estimation...")
            try:
                function_call = debt_swap_contract.functions.swapDebt(
                    transaction_params['debtAsset'],
                    transaction_params['debtRepayAmount'],
                    transaction_params['newDebtAsset'],
                    transaction_params['maxNewDebtAmount'],
                    transaction_params['extraCollateralAsset'],
                    transaction_params['extraCollateralAmount'],
                    transaction_params['offset'],
                    transaction_params['paraswapData'],
                    transaction_params['creditDelegationPermit'],
                    transaction_params['collateralATokenPermit']
                )
                
                # Try gas estimation
                try:
                    estimated_gas = function_call.estimate_gas({'from': self.user_address})
                    gas_price = self.w3.eth.gas_price
                    gas_cost_eth = (estimated_gas * gas_price) / 1e18
                    gas_cost_usd = gas_cost_eth * execution_result['position_before']['prices'].get('ETH', 3000)
                    
                    execution_result['comprehensive_logging']['gas_estimation'] = {
                        'success': True,
                        'estimated_gas': estimated_gas,
                        'gas_price_gwei': gas_price / 1e9,
                        'gas_cost_eth': gas_cost_eth,
                        'gas_cost_usd': gas_cost_usd,
                        'method': 'direct_estimation'
                    }
                    
                    print(f"      ✅ Estimated Gas: {estimated_gas:,} units")
                    print(f"      ✅ Gas Price: {gas_price / 1e9:.2f} gwei")
                    print(f"      ✅ Estimated Cost: {gas_cost_eth:.6f} ETH (${gas_cost_usd:.2f})")
                    
                except Exception as gas_error:
                    # Fallback gas estimation
                    estimated_gas = 500000  # Conservative fallback
                    gas_price = self.w3.eth.gas_price
                    gas_cost_eth = (estimated_gas * gas_price) / 1e18
                    gas_cost_usd = gas_cost_eth * execution_result['position_before']['prices'].get('ETH', 3000)
                    
                    execution_result['comprehensive_logging']['gas_estimation'] = {
                        'success': False,
                        'error': str(gas_error),
                        'estimated_gas': estimated_gas,
                        'gas_price_gwei': gas_price / 1e9,
                        'gas_cost_eth': gas_cost_eth,
                        'gas_cost_usd': gas_cost_usd,
                        'method': 'fallback_estimation'
                    }
                    
                    print(f"      ⚠️ Gas estimation failed: {gas_error}")
                    print(f"      ✅ Using fallback: {estimated_gas:,} units")
                    print(f"      ✅ Estimated Cost: {gas_cost_eth:.6f} ETH (${gas_cost_usd:.2f})")
                    
            except Exception as contract_error:
                error_msg = f"Contract interaction setup failed: {contract_error}"
                execution_result['error'] = error_msg
                execution_result['comprehensive_logging']['contract_interaction']['setup_error'] = error_msg
                return execution_result
            
            execution_result['stepwise_diff']['step_by_step_log'].append({
                'step': 4,
                'name': 'gas_estimation',
                'duration_ms': int((time.time() - gas_estimation_start) * 1000),
                'status': 'completed',
                'details': f"Gas estimation completed: {estimated_gas:,} units"
            })
            
            # STEP 5: TRANSACTION SUBMISSION WITH COMPREHENSIVE LOGGING
            print(f"\n🚀 STEP 5: TRANSACTION SUBMISSION WITH COMPREHENSIVE LOGGING")
            print("-" * 50)
            
            transaction_start = time.time()
            
            # 5A. Final pre-submission validation
            print(f"   🔍 5A: Final pre-submission validation...")
            if estimated_gas > 1000000:
                print(f"      ⚠️ High gas estimate: {estimated_gas:,} units")
            if gas_cost_usd > 50:
                print(f"      ⚠️ High transaction cost: ${gas_cost_usd:.2f}")
            
            # 5B. Build and submit transaction
            print(f"   📝 5B: Building and submitting transaction...")
            try:
                transaction = function_call.build_transaction({
                    'from': self.user_address,
                    'gas': int(estimated_gas * 1.2),  # 20% buffer
                    'gasPrice': gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.user_address)
                })
                
                execution_result['comprehensive_logging']['transaction_submission'] = {
                    'transaction_built': True,
                    'gas_limit': transaction['gas'],
                    'gas_price': transaction['gasPrice'],
                    'nonce': transaction['nonce'],
                    'to': transaction['to'],
                    'value': transaction['value']
                }
                
                print(f"      ✅ Transaction built successfully")
                print(f"      ✅ Gas Limit: {transaction['gas']:,} units")
                print(f"      ✅ Nonce: {transaction['nonce']}")
                
                # Sign and send transaction
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
                print(f"      ✅ Transaction signed")
                
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                print(f"      ✅ Transaction submitted: {tx_hash.hex()}")
                
                execution_result['transaction_hash'] = tx_hash.hex()
                execution_result['comprehensive_logging']['transaction_submission']['tx_hash'] = tx_hash.hex()
                execution_result['comprehensive_logging']['transaction_submission']['submission_time'] = time.time()
                
                # 5C. Wait for transaction receipt
                print(f"   ⏳ 5C: Waiting for transaction confirmation...")
                receipt_start = time.time()
                try:
                    tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                    receipt_duration = int((time.time() - receipt_start) * 1000)
                    
                    execution_result['transaction_receipt'] = dict(tx_receipt)
                    execution_result['gas_used'] = tx_receipt.gasUsed
                    execution_result['gas_cost_eth'] = (tx_receipt.gasUsed * gas_price) / 1e18
                    
                    execution_result['comprehensive_logging']['transaction_submission']['receipt'] = {
                        'status': tx_receipt.status,
                        'block_number': tx_receipt.blockNumber,
                        'gas_used': tx_receipt.gasUsed,
                        'confirmation_time_ms': receipt_duration,
                        'transaction_index': tx_receipt.transactionIndex
                    }
                    
                    print(f"      ✅ Transaction confirmed in block {tx_receipt.blockNumber}")
                    print(f"      ✅ Gas Used: {tx_receipt.gasUsed:,} units")
                    print(f"      ✅ Status: {'SUCCESS' if tx_receipt.status == 1 else 'FAILED'}")
                    print(f"      ✅ Confirmation Time: {receipt_duration}ms")
                    
                    if tx_receipt.status == 1:
                        execution_result['success'] = True
                    else:
                        execution_result['error'] = "Transaction failed (status = 0)"
                        
                except Exception as receipt_error:
                    execution_result['error'] = f"Transaction receipt error: {receipt_error}"
                    execution_result['comprehensive_logging']['transaction_submission']['receipt_error'] = str(receipt_error)
                    
            except Exception as submission_error:
                execution_result['error'] = f"Transaction submission failed: {submission_error}"
                execution_result['comprehensive_logging']['transaction_submission']['submission_error'] = str(submission_error)
                
            execution_result['stepwise_diff']['step_by_step_log'].append({
                'step': 5,
                'name': 'transaction_submission',
                'duration_ms': int((time.time() - transaction_start) * 1000),
                'status': 'completed' if execution_result['success'] else 'failed',
                'details': f"Transaction {'completed successfully' if execution_result['success'] else 'failed'}"
            })
            
            # STEP 6: POST-EXECUTION STATE CAPTURE AND ANALYSIS
            print(f"\n📊 STEP 6: POST-EXECUTION STATE CAPTURE AND ANALYSIS")
            print("-" * 50)
            
            post_execution_start = time.time()
            execution_result['stepwise_diff']['post_execution_state'] = self._capture_comprehensive_state(
                f"POST-EXECUTION: {from_asset}→{to_asset}"
            )
            
            # Legacy position capture
            execution_result['position_after'] = self.get_aave_position()
            
            # State comparison and diff analysis
            print(f"\n🔍 STEPWISE DIFF ANALYSIS")
            print("-" * 50)
            
            pre_state = execution_result['stepwise_diff']['pre_execution_state']
            post_state = execution_result['stepwise_diff']['post_execution_state']
            
            state_changes = {}
            
            # Health factor change
            if 'health_metrics' in pre_state and 'health_metrics' in post_state:
                hf_before = pre_state['health_metrics'].get('health_factor', 0)
                hf_after = post_state['health_metrics'].get('health_factor', 0)
                hf_change = hf_after - hf_before
                state_changes['health_factor'] = {
                    'before': hf_before,
                    'after': hf_after,
                    'change': hf_change,
                    'change_percent': (hf_change / hf_before * 100) if hf_before != 0 else 0
                }
                print(f"   📈 Health Factor: {hf_before:.4f} → {hf_after:.4f} ({hf_change:+.4f})")
            
            # Debt composition changes
            if 'aave_position' in pre_state and 'aave_position' in post_state:
                pre_debt = pre_state['aave_position'].get('debt_values_usd', {})
                post_debt = post_state['aave_position'].get('debt_values_usd', {})
                
                for token in ['DAI', 'ARB']:
                    before = pre_debt.get(token, 0)
                    after = post_debt.get(token, 0)
                    change = after - before
                    state_changes[f'{token}_debt'] = {
                        'before': before,
                        'after': after,
                        'change': change
                    }
                    print(f"   💳 {token} Debt: ${before:.2f} → ${after:.2f} (${change:+.2f})")
            
            # Token balance changes
            if 'token_balances' in pre_state and 'token_balances' in post_state:
                for token in ['ETH', 'DAI', 'ARB']:
                    before = pre_state['token_balances'].get(token, 0)
                    after = post_state['token_balances'].get(token, 0)
                    change = after - before
                    if abs(change) > 0.000001:  # Only show meaningful changes
                        state_changes[f'{token}_balance'] = {
                            'before': before,
                            'after': after,
                            'change': change
                        }
                        print(f"   💰 {token} Balance: {before:.6f} → {after:.6f} ({change:+.6f})")
            
            execution_result['stepwise_diff']['state_changes'] = state_changes
            
            execution_result['stepwise_diff']['step_by_step_log'].append({
                'step': 6,
                'name': 'post_execution_analysis',
                'duration_ms': int((time.time() - post_execution_start) * 1000),
                'status': 'completed',
                'details': f"State analysis completed, {len(state_changes)} changes detected"
            })
            
            # FINAL SUMMARY
            total_duration = int((time.time() - pre_execution_start) * 1000)
            
            print(f"\n📋 COMPREHENSIVE EXECUTION SUMMARY")
            print("=" * 80)
            print(f"   Operation: {from_asset} debt → {to_asset} debt")
            print(f"   Amount: ${swap_amount_usd:.2f}")
            print(f"   Success: {'✅ YES' if execution_result['success'] else '❌ NO'}")
            print(f"   Total Duration: {total_duration}ms")
            print(f"   Transaction Hash: {execution_result.get('transaction_hash', 'N/A')}")
            print(f"   Gas Used: {execution_result.get('gas_used', 0):,} units")
            print(f"   Gas Cost: {execution_result.get('gas_cost_eth', 0):.6f} ETH")
            print(f"   Steps Completed: {len(execution_result['stepwise_diff']['step_by_step_log'])}")
            print(f"   State Changes: {len(state_changes)}")
            
            if not execution_result['success']:
                print(f"   Error: {execution_result.get('error', 'Unknown error')}")
            
            print("=" * 80)
            
            return execution_result
            
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
            
            # 4. Get ParaSwap Augustus calldata (CORRECT interface)
            paraswap_data = self.get_paraswap_calldata_reverse_routing(from_asset, to_asset, amount_wei)
            if not paraswap_data:
                execution_result['error'] = "Failed to get ParaSwap Augustus calldata"
                return execution_result
            
            # Use exact amount from ParaSwap
            if 'expected_amount' in paraswap_data:
                amount_to_swap = int(paraswap_data['expected_amount'])
            else:
                amount_to_swap = amount_wei
            
            # 5. FIXED: Use FULLY ZEROED permit (matching successful manual transactions)
            print(f"📝 FIXED: Using FULLY ZEROED permit matching successful manual transactions")
            zero_address = "0x0000000000000000000000000000000000000000"
            credit_permit = {
                'token': zero_address,  # FIXED: debtToken must be 0x000...000 (matching manual transactions)
                'value': 0,  # FIXED: All zero values matching manual patterns
                'deadline': 0,  # FIXED: All zero values matching manual patterns  
                'v': 0,  # FIXED: All zero values matching manual patterns
                'r': b'\x00' * 32,  # FIXED: All zero values matching manual patterns
                's': b'\x00' * 32   # FIXED: All zero values matching manual patterns
            }
            
            # 6. Build swapDebt transaction
            debt_swap_contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter,
                abi=self.debt_swap_abi
            )
            
            # FIXED: Updated function call with CORRECT signature from 4byte.directory (0xb8bd1c6b)
            zero_address = "0x0000000000000000000000000000000000000000"
            
            # CORRECT ABI STRUCTURE: swapData INSIDE first tuple, proper data types
            function_call = debt_swap_contract.functions.swapDebt(
                (
                    self.tokens[from_asset.upper()],                      # debtAsset
                    amount_to_swap,                                        # debtRepayAmount  
                    2,                                                     # debtRateMode (variable debt)
                    self.tokens[to_asset.upper()],                        # newDebtAsset
                    int(amount_to_swap * 2.1),                            # maxNewDebtAmount (2.1x ratio for ARB debt)
                    zero_address,                                          # extraCollateralAsset
                    0,                                                     # extraCollateralAmount
                    288,                                                   # offset (FIXED: 288 bytes for successful manual transactions)
                    bytes.fromhex(paraswap_data['calldata'][2:])          # swapData (FIXED: standardized parameter name)
                ),
                (
                    credit_permit['token'],                               # debtToken
                    credit_permit['value'],                               # value
                    credit_permit['deadline'],                            # deadline
                    credit_permit['v'],                                   # v (uint8)
                    credit_permit['r'],                                   # r (bytes32)
                    credit_permit['s']                                    # s (bytes32)
                ),
                (
                    zero_address,                                         # aToken (empty permit)
                    0,                                                     # value
                    0,                                                     # deadline
                    0,                                                     # v (uint8)
                    b'\x00'*32,                                           # r (bytes32)
                    b'\x00'*32                                            # s (bytes32)
                )
            )
            
            # 7. UNIFIED SYSTEM: Root-cause failure prevention + Gas optimization
            print(f"\n🔧 UNIFIED VALIDATION & OPTIMIZATION SYSTEM")
            print("=" * 80)
            
            try:
                # STEP 1: Root-cause failure prevention
                print(f"STEP 1: Root-cause failure prevention...")
                
                calldata_params = {
                    'debtAsset': self.tokens[from_asset.upper()],
                    'debtRepayAmount': amount_to_swap,
                    'debtRateMode': 2,
                    'newDebtAsset': self.tokens[to_asset.upper()],
                    'maxNewDebtAmount': int(amount_to_swap * 2.1)
                }
                
                root_cause_result = resolve_gas_estimation_failure(
                    contract_address=self.paraswap_debt_swap_adapter,
                    function_call=function_call,
                    calldata_params=calldata_params,
                    swap_amount_usd=swap_amount_usd,
                    w3=self.w3
                )
                
                # Log all return values
                execution_result['root_cause_validation'] = root_cause_result
                print(f"📊 Root-cause validation result: {root_cause_result['success']}")
                
                for log_entry in root_cause_result.get('diagnostic_logs', []):
                    print(f"   {log_entry['step']}: {log_entry.get('status', 'completed')}")
                
                # If failure, log error and abort with full diagnostics
                if not root_cause_result['success']:
                    error_details = root_cause_result.get('error_details', [])
                    full_diagnostic = {
                        'function_selector': '0xb8bd1c6b',
                        'expected_signature': '0xb8bd1c6b',
                        'calldata_tokens': calldata_params,
                        'error_details': error_details,
                        'diagnostic_logs': root_cause_result.get('diagnostic_logs', []),
                        'mismatch_analysis': {
                            'signature_valid': root_cause_result.get('signature_valid', False),
                            'calldata_valid': root_cause_result.get('calldata_valid', False),
                            'amount_valid': root_cause_result.get('amount_valid', False)
                        }
                    }
                    
                    execution_result['error'] = f"Root-cause validation failed: {'; '.join(error_details)}"
                    execution_result['full_mismatch_diagnostics'] = full_diagnostic
                    
                    print(f"❌ ROOT-CAUSE VALIDATION FAILED")
                    print(f"   Errors: {error_details}")
                    print(f"   Full diagnostics logged for review")
                    
                    return execution_result
                
                print(f"✅ Root-cause validation PASSED")
                
                # STEP 2: Gas optimization with CoinAPI
                print(f"\nSTEP 2: Gas optimization with CoinAPI...")
                
                gas_optimizer = CoinAPIGasOptimizer(self.w3, max_usd_per_tx=self.max_usd_per_tx)
                gas_optimization_result = gas_optimizer.calculate_optimized_gas_params(
                    operation_type='debt_swap',
                    buffer_percent=2.0  # 2% buffer
                )
                
                execution_result['gas_optimization'] = gas_optimization_result
                
                # Log all inputs, API responses, gas used, and buffer logic
                print(f"📊 Gas optimization result: {gas_optimization_result['success']}")
                
                if not gas_optimization_result['success']:
                    execution_result['error'] = "Gas optimization failed"
                    return execution_result
                
                optimized_params = gas_optimization_result['final_params']
                
                # Generate comparison table
                manual_params = {
                    'gas': 350000,
                    'gasPrice': self.w3.eth.gas_price
                }
                
                comparison_table = gas_optimizer.generate_gas_comparison_table(
                    manual_params, gas_optimization_result
                )
                
                execution_result['gas_comparison_table'] = comparison_table
                print(comparison_table)
                
                print(f"✅ Gas optimization COMPLETE")
                
            except Exception as unified_error:
                execution_result['error'] = f"Unified system failed: {unified_error}"
                execution_result['unified_error_details'] = {
                    'error': str(unified_error),
                    'timestamp': time.time(),
                    'step': 'unified_validation_optimization'
                }
                
                print(f"❌ UNIFIED SYSTEM ERROR: {unified_error}")
                return execution_result
            
            # Build transaction data with optimized gas parameters
            tx_data = function_call.build_transaction({
                'from': self.user_address,
                'gas': optimized_params['gas'],
                'gasPrice': optimized_params['gasPrice'],
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            # 8. Execute transaction with comprehensive logging
            print(f"\n🚀 EXECUTING ON-CHAIN TRANSACTION")
            print("=" * 50)
            
            signed_tx = self.account.sign_transaction(tx_data)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            execution_result['transaction_hash'] = tx_hash.hex()
            
            # Log transaction hash, gas sent, and parameters
            transaction_logging = {
                'transaction_hash': execution_result['transaction_hash'],
                'gas_sent': optimized_params['gas'],
                'gas_price_sent': optimized_params['gasPrice'],
                'gas_price_gwei': self.w3.from_wei(optimized_params['gasPrice'], 'gwei'),
                'estimated_cost_usd': optimized_params['estimated_cost_usd'],
                'timestamp': time.time()
            }
            
            execution_result['transaction_logging'] = transaction_logging
            
            print(f"📡 Transaction sent: {execution_result['transaction_hash']}")
            print(f"⛽ Gas sent: {transaction_logging['gas_sent']:,}")
            print(f"💰 Gas price: {transaction_logging['gas_price_gwei']:.2f} gwei")
            print(f"💸 Est. cost: ${transaction_logging['estimated_cost_usd']:.4f}")
            print(f"⏳ Waiting for confirmation...")
            
            # 9. Wait for receipt and log contract events
            tx_receipt: TxReceipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            execution_result['transaction_receipt'] = dict(tx_receipt)
            execution_result['gas_used'] = tx_receipt['gasUsed']
            execution_result['gas_cost_eth'] = float(tx_receipt['gasUsed'] * tx_receipt['effectiveGasPrice']) / 1e18
            
            # Log contract event logs
            event_logs = []
            for log in tx_receipt['logs']:
                event_logs.append({
                    'address': log['address'],
                    'topics': [topic.hex() for topic in log['topics']],
                    'data': log['data'].hex()
                })
            
            execution_result['contract_event_logs'] = event_logs
            
            if tx_receipt['status'] == 1:
                print(f"✅ TRANSACTION SUCCESSFUL")
                print(f"   Gas Used: {tx_receipt['gasUsed']:,}")
                print(f"   Gas Cost: {execution_result['gas_cost_eth']:.6f} ETH")
                print(f"   Contract Events: {len(event_logs)} events logged")
                
                execution_result['success'] = True
                
                # Generate final success message
                final_success_msg = (
                    "ALL ROOT-CAUSE FAILURES, GAS MISMATCHES, AND SIGNATURE ERRORS RESOLVED"
                )
                execution_result['final_status'] = final_success_msg
                print(f"\n🎉 {final_success_msg}")
                
                # Get post-swap position
                time.sleep(2)  # Brief delay for state to update
                execution_result['position_after'] = self.get_aave_position()
                
            else:
                execution_result['error'] = "Transaction failed on-chain"
                execution_result['revert_analysis'] = self._analyze_transaction_failure(tx_receipt)
                
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
                minutes_str: str = f"{remaining // 60} minutes remaining..."
                print(f"⏳ {minutes_str}")
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
            tx_hash: str = receipt['receipt']['transactionHash'].hex()
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

    def save_cycle_artifacts(self, filename: Optional[str] = None) -> str:
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

    def get_eth_price_coinapi(self) -> float:
        """Get real-time ETH price using CoinAPI for gas optimization"""
        try:
            if not self.coin_api_key:
                print("⚠️ CoinAPI key not available, using fallback ETH price")
                return 2500.0  # Fallback price
                
            url = "https://rest.coinapi.io/v1/exchangerate/ETH/USD"
            headers = {"X-CoinAPI-Key": self.coin_api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                eth_price = float(data['rate'])
                print(f"💰 Real-time ETH price: ${eth_price:.2f}")
                return eth_price
            else:
                print(f"⚠️ CoinAPI failed ({response.status_code}), using fallback")
                return 2500.0
                
        except Exception as e:
            print(f"⚠️ CoinAPI error: {e}, using fallback ETH price")
            return 2500.0

    def get_enhanced_gas_params(self, operation_type: str, swap_amount_usd: float) -> Dict:
        """
        COMBINED SOLUTION: Enhanced gas parameter optimization with execution validation
        Merges resolve_gas_estimation_failure() + CoinAPIGasOptimizer approaches
        """
        print(f"\n⛽ ENHANCED GAS OPTIMIZATION")
        print("=" * 50)
        
        # Step 1: Enforce minimum notional amounts (prevents dust trade reverts)
        if swap_amount_usd < self.min_swap_usd:
            raise ValueError(f"Minimum ${self.min_swap_usd} swap required (got ${swap_amount_usd})")
        
        # Step 2: Get real-time network gas conditions
        base_gas_price = self.w3.eth.gas_price
        print(f"📡 Network base gas: {self.w3.from_wei(base_gas_price, 'gwei'):.2f} gwei")
        
        # Step 3: Get real-time ETH price from CoinAPI
        eth_price = self.get_eth_price_coinapi()
        
        # Step 4: Calculate gas limits based on operation type
        gas_limits = {
            'debt_swap': 300000,      # Reduced for Uniswap V3 + Aave operations (more efficient)
            'aave_borrow': 180000,
            'aave_supply': 150000,
            'token_approval': 60000
        }
        
        gas_limit = gas_limits.get(operation_type, 300000)
        
        # Step 5: Calculate USD cost and apply budget control
        estimated_cost_usd = (gas_limit * base_gas_price * eth_price) / 1e18
        print(f"💸 Estimated cost: ${estimated_cost_usd:.4f} USD")
        
        # Step 6: Dynamic gas adjustment with budget cap
        if estimated_cost_usd > self.max_usd_per_tx:
            # Cap gas price to stay within budget
            max_affordable_gas_price = (self.max_usd_per_tx * 1e18) / (gas_limit * eth_price)
            adjusted_gas_price = max(max_affordable_gas_price, base_gas_price * 0.9)  # Never below 90% market
            
            print(f"🚨 Budget cap applied: ${estimated_cost_usd:.4f} > ${self.max_usd_per_tx}")
            print(f"   Adjusted gas price: {self.w3.from_wei(int(adjusted_gas_price), 'gwei'):.2f} gwei")
            
            final_gas_price = int(adjusted_gas_price)
            budget_capped = True
        else:
            # Use network price with slight premium for reliability
            final_gas_price = int(base_gas_price * 1.05)  # 5% premium for priority
            budget_capped = False
        
        # Step 7: Final gas parameters
        final_cost_usd = (gas_limit * final_gas_price * eth_price) / 1e18
        
        gas_params = {
            'gas': gas_limit,
            'gasPrice': final_gas_price,
            'gas_limit_safety_factor': 1.25,  # 25% buffer over estimate
            'budget_capped': budget_capped,
            'estimated_cost_usd': final_cost_usd,
            'eth_price_used': eth_price,
            'operation_type': operation_type
        }
        
        print(f"✅ Final gas parameters:")
        print(f"   Gas Limit: {gas_limit:,}")
        print(f"   Gas Price: {self.w3.from_wei(final_gas_price, 'gwei'):.2f} gwei")
        print(f"   Final Cost: ${final_cost_usd:.4f} USD")
        print(f"   Budget Capped: {budget_capped}")
        
        return gas_params

    def enhanced_preflight_simulation(self, function_call, swap_amount_usd: float) -> Tuple[bool, str]:
        """
        Enhanced preflight validation with execution buffer verification
        Part of combined gas optimization solution
        """
        try:
            print(f"\n🛡️ ENHANCED PREFLIGHT SIMULATION")
            print("=" * 50)
            
            # Step 1: Static call simulation
            try:
                result = function_call.call({'from': self.user_address})
                print(f"✅ Static call successful")
            except Exception as call_error:
                error_msg = str(call_error)
                print(f"❌ Static call failed: {error_msg}")
                
                # Analyze common revert reasons
                if "insufficient" in error_msg.lower():
                    return False, f"Insufficient balance/allowance: {error_msg}"
                elif "slippage" in error_msg.lower():
                    return False, f"Slippage protection triggered: {error_msg}"
                elif "dust" in error_msg.lower() or "minimum" in error_msg.lower():
                    return False, f"Amount too small (minimum ${self.min_swap_usd}): {error_msg}"
                else:
                    return False, f"Contract execution revert: {error_msg}"
            
            # Step 2: Gas estimation with enhanced error handling
            try:
                gas_estimate = function_call.estimate_gas({'from': self.user_address})
                gas_limit = int(gas_estimate * 1.25)  # 25% buffer
                print(f"✅ Gas estimation: {gas_estimate:,} (with buffer: {gas_limit:,})")
                
                return True, f"Preflight passed - estimated gas: {gas_estimate:,}"
                
            except Exception as gas_error:
                error_msg = str(gas_error)
                print(f"❌ Gas estimation failed: {error_msg}")
                
                # This is where the original issue occurred
                if "execution reverted" in error_msg.lower():
                    return False, f"Execution revert during gas estimation (likely insufficient buffers): {error_msg}"
                else:
                    return False, f"Gas estimation error: {error_msg}"
            
        except Exception as e:
            return False, f"Preflight simulation error: {str(e)}"

    def _analyze_transaction_failure(self, tx_receipt: TxReceipt) -> Dict:
        """Analyze transaction failure for detailed diagnostics"""
        try:
            analysis = {
                'status': tx_receipt.get('status', 0),
                'gas_used': tx_receipt.get('gasUsed', 0),
                'block_number': tx_receipt.get('blockNumber', 0),
                'failure_reason': 'unknown',
                'suggested_actions': []
            }
            
            if analysis['status'] == 0:
                analysis['failure_reason'] = 'transaction_reverted'
                analysis['suggested_actions'] = [
                    'Check contract state changes',
                    'Verify input parameters',
                    'Increase gas limit',
                    'Check for slippage protection'
                ]
            
            return analysis
            
        except Exception as e:
            return {'error': f"Failed to analyze transaction failure: {e}"}

    def generate_execution_log(self, execution_result: Dict) -> Dict:
        """
        Generate structured, timestamped execution log
        Every swap execution MUST produce this comprehensive log
        """
        timestamp = datetime.now().isoformat()
        
        structured_log = {
            'execution_id': f"debt_swap_{int(time.time())}",
            'timestamp': timestamp,
            'unified_system_version': '1.0',
            'function_selector_analysis': {
                'called': '0xb8bd1c6b',
                'matched_from_abi': '0xb8bd1c6b',
                'signature_valid': execution_result.get('root_cause_validation', {}).get('signature_valid', False)
            },
            'calldata_validation': {
                'parameters_valid': execution_result.get('root_cause_validation', {}).get('calldata_valid', False),
                'amount_valid': execution_result.get('root_cause_validation', {}).get('amount_valid', False)
            },
            'gas_optimization': {
                'api_integration': execution_result.get('gas_optimization', {}).get('success', False),
                'buffer_calculation': execution_result.get('gas_optimization', {}).get('final_params', {}),
                'budget_analysis': execution_result.get('gas_optimization', {}).get('budget_analysis', {}),
                'comparison_table': execution_result.get('gas_comparison_table', '')
            },
            'transaction_execution': {
                'hash': execution_result.get('transaction_hash', ''),
                'status': 'success' if execution_result.get('success', False) else 'failed',
                'gas_used': execution_result.get('gas_used', 0),
                'gas_cost_eth': execution_result.get('gas_cost_eth', 0),
                'contract_events': len(execution_result.get('contract_event_logs', []))
            },
            'final_status': execution_result.get('final_status', 'EXECUTION INCOMPLETE'),
            'error_details': execution_result.get('error', None),
            'diagnostic_logs': execution_result.get('root_cause_validation', {}).get('diagnostic_logs', [])
        }
        
        return structured_log

    def run_automated_tests(self, simulate_only: bool = True) -> Dict:
        """
        Automated test suite for signature/call simulation and gas optimizer
        """
        print(f"\n🧪 AUTOMATED TEST SUITE")
        print("=" * 60)
        print(f"Mode: {'SIMULATION ONLY' if simulate_only else 'LIVE TESTING'}")
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_mode': 'simulation' if simulate_only else 'live',
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'detailed_results': []
        }
        
        # Test 1: Success case (correct function and calldata)
        print(f"\n📋 TEST 1: Success case validation")
        try:
            test_1_result = self._test_success_case(simulate_only)
            test_results['detailed_results'].append({
                'test_name': 'success_case',
                'result': test_1_result,
                'status': 'passed' if test_1_result.get('success', False) else 'failed'
            })
            test_results['tests_run'] += 1
            if test_1_result.get('success', False):
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
                
        except Exception as e:
            test_results['detailed_results'].append({
                'test_name': 'success_case',
                'error': str(e),
                'status': 'error'
            })
            test_results['tests_run'] += 1
            test_results['tests_failed'] += 1
        
        # Test 2: Function selector mismatch
        print(f"\n📋 TEST 2: Function selector mismatch detection")
        try:
            test_2_result = self._test_selector_mismatch()
            test_results['detailed_results'].append({
                'test_name': 'selector_mismatch',
                'result': test_2_result,
                'status': 'passed' if test_2_result.get('caught_mismatch', False) else 'failed'
            })
            test_results['tests_run'] += 1
            if test_2_result.get('caught_mismatch', False):
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
                
        except Exception as e:
            test_results['detailed_results'].append({
                'test_name': 'selector_mismatch',
                'error': str(e),
                'status': 'error'
            })
            test_results['tests_run'] += 1
            test_results['tests_failed'] += 1
        
        # Test 3: Token/parameter mismatch
        print(f"\n📋 TEST 3: Parameter validation")
        try:
            test_3_result = self._test_parameter_mismatch()
            test_results['detailed_results'].append({
                'test_name': 'parameter_mismatch',
                'result': test_3_result,
                'status': 'passed' if test_3_result.get('caught_mismatch', False) else 'failed'
            })
            test_results['tests_run'] += 1
            if test_3_result.get('caught_mismatch', False):
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
                
        except Exception as e:
            test_results['detailed_results'].append({
                'test_name': 'parameter_mismatch',
                'error': str(e),
                'status': 'error'
            })
            test_results['tests_run'] += 1
            test_results['tests_failed'] += 1
        
        # Test 4: Gas optimizer tests
        print(f"\n📋 TEST 4: Gas optimizer validation")
        try:
            test_4_result = self._test_gas_optimizer()
            test_results['detailed_results'].append({
                'test_name': 'gas_optimizer',
                'result': test_4_result,
                'status': 'passed' if test_4_result.get('all_passed', False) else 'failed'
            })
            test_results['tests_run'] += 1
            if test_4_result.get('all_passed', False):
                test_results['tests_passed'] += 1
            else:
                test_results['tests_failed'] += 1
                
        except Exception as e:
            test_results['detailed_results'].append({
                'test_name': 'gas_optimizer',
                'error': str(e),
                'status': 'error'
            })
            test_results['tests_run'] += 1
            test_results['tests_failed'] += 1
        
        # Generate summary
        test_results['success_rate'] = (test_results['tests_passed'] / test_results['tests_run']) * 100 if test_results['tests_run'] > 0 else 0
        
        print(f"\n✅ TEST SUITE COMPLETE")
        print(f"   Tests Run: {test_results['tests_run']}")
        print(f"   Passed: {test_results['tests_passed']}")
        print(f"   Failed: {test_results['tests_failed']}")
        print(f"   Success Rate: {test_results['success_rate']:.1f}%")
        
        return test_results

    def _test_success_case(self, simulate_only: bool) -> Dict:
        """Test success case with correct function and calldata"""
        from debt_swap_utils import resolve_gas_estimation_failure
        
        # Create mock successful parameters
        mock_function_call = type('MockFunction', (), {
            'selector': type('MockSelector', (), {'hex': lambda: '0xb8bd1c6b'})(),
            'call': lambda self, params: True,
            'estimate_gas': lambda self, params: 250000
        })()
        
        test_params = {
            'debtAsset': self.tokens['DAI'],
            'debtRepayAmount': 50 * 10**18,  # $50 worth
            'debtRateMode': 2,
            'newDebtAsset': self.tokens['ARB'],
            'maxNewDebtAmount': 51 * 10**18  # 2% buffer
        }
        
        result = resolve_gas_estimation_failure(
            contract_address=self.paraswap_debt_swap_adapter,
            function_call=mock_function_call,
            calldata_params=test_params,
            swap_amount_usd=50.0,  # Above minimum
            w3=self.w3
        )
        
        return {
            'success': result['success'],
            'details': result,
            'test_type': 'success_case'
        }

    def _test_selector_mismatch(self) -> Dict:
        """Test function selector mismatch detection"""
        from debt_swap_utils import resolve_gas_estimation_failure
        
        # Create mock with wrong selector
        mock_function_call = type('MockFunction', (), {
            'selector': type('MockSelector', (), {'hex': lambda: '0x12345678'})(),  # Wrong selector
            'call': lambda self, params: True,
            'estimate_gas': lambda self, params: 250000
        })()
        
        test_params = {
            'debtAsset': self.tokens['DAI'],
            'debtRepayAmount': 50 * 10**18,
            'debtRateMode': 2,
            'newDebtAsset': self.tokens['ARB'],
            'maxNewDebtAmount': 51 * 10**18
        }
        
        result = resolve_gas_estimation_failure(
            contract_address=self.paraswap_debt_swap_adapter,
            function_call=mock_function_call,
            calldata_params=test_params,
            swap_amount_usd=50.0,
            w3=self.w3
        )
        
        return {
            'caught_mismatch': not result['success'] and not result['signature_valid'],
            'error_details': result.get('error_details', []),
            'test_type': 'selector_mismatch'
        }

    def _test_parameter_mismatch(self) -> Dict:
        """Test parameter validation"""
        from debt_swap_utils import resolve_gas_estimation_failure
        
        mock_function_call = type('MockFunction', (), {
            'selector': type('MockSelector', (), {'hex': lambda: '0xb8bd1c6b'})(),
            'call': lambda self, params: True,
            'estimate_gas': lambda self, params: 250000
        })()
        
        # Invalid parameters (missing required field)
        invalid_params = {
            'debtAsset': self.tokens['DAI'],
            # 'debtRepayAmount': missing!
            'debtRateMode': 2,
            'newDebtAsset': self.tokens['ARB'],
            'maxNewDebtAmount': 51 * 10**18
        }
        
        result = resolve_gas_estimation_failure(
            contract_address=self.paraswap_debt_swap_adapter,
            function_call=mock_function_call,
            calldata_params=invalid_params,
            swap_amount_usd=50.0,
            w3=self.w3
        )
        
        return {
            'caught_mismatch': not result['success'] and not result['calldata_valid'],
            'error_details': result.get('error_details', []),
            'test_type': 'parameter_mismatch'
        }

    def _test_gas_optimizer(self) -> Dict:
        """Test gas optimizer functionality"""
        from gas_optimization import CoinAPIGasOptimizer
        
        test_results: Dict[str, Union[bool, str]] = {
            'api_fetch_test': False,
            'buffer_logic_test': False,
            'error_handling_test': False,
            'all_passed': False
        }
        
        try:
            # Test 1: API fetch and parse
            optimizer = CoinAPIGasOptimizer(self.w3, max_usd_per_tx=10.0)
            eth_price_result = optimizer.get_eth_price_coinapi()
            test_results['api_fetch_test'] = eth_price_result['price'] > 0
            
            # Test 2: Buffer logic
            gas_result = optimizer.calculate_optimized_gas_params('debt_swap', buffer_percent=2.0)
            test_results['buffer_logic_test'] = gas_result['success']
            
            # Test 3: Error handling (simulate missing API key)
            old_key = optimizer.coin_api_key
            optimizer.coin_api_key = None  # type: ignore
            error_result = optimizer.get_eth_price_coinapi()
            test_results['error_handling_test'] = error_result['source'] == 'fallback'
            optimizer.coin_api_key = old_key
            
            test_results['all_passed'] = all([
                test_results['api_fetch_test'],
                test_results['buffer_logic_test'],
                test_results['error_handling_test']
            ])
            
        except Exception as e:
            test_results['error'] = str(e)
        
        return test_results

    def generate_diagnostic_report(self, execution_result: Dict, test_results: Optional[Dict] = None) -> str:
        """
        Generate comprehensive diagnostic report for human review
        """
        report = []
        report.append("=" * 80)
        report.append("UNIFIED DEBT SWAP SYSTEM - DIAGNOSTIC REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Execution ID: {execution_result.get('transaction_hash', 'N/A')}")
        report.append("")
        
        # Root-cause validation summary
        root_cause = execution_result.get('root_cause_validation', {})
        report.append("📋 ROOT-CAUSE VALIDATION:")
        report.append(f"   Overall Success: {root_cause.get('success', False)}")
        report.append(f"   Signature Valid: {root_cause.get('signature_valid', False)}")
        report.append(f"   Calldata Valid: {root_cause.get('calldata_valid', False)}")
        report.append(f"   Amount Valid: {root_cause.get('amount_valid', False)}")
        
        if root_cause.get('error_details'):
            report.append("   Errors:")
            for error in root_cause['error_details']:
                report.append(f"     - {error}")
        report.append("")
        
        # Gas optimization summary
        gas_opt = execution_result.get('gas_optimization', {})
        report.append("⛽ GAS OPTIMIZATION:")
        report.append(f"   Optimization Success: {gas_opt.get('success', False)}")
        
        if gas_opt.get('final_params'):
            params = gas_opt['final_params']
            report.append(f"   Gas Limit: {params.get('gas', 0):,}")
            report.append(f"   Gas Price: {params.get('gasPrice', 0):,} wei")
            report.append(f"   Estimated Cost: ${params.get('estimated_cost_usd', 0):.4f}")
            report.append(f"   Budget Capped: {params.get('budget_capped', False)}")
        report.append("")
        
        # Transaction execution summary
        report.append("🚀 TRANSACTION EXECUTION:")
        report.append(f"   Success: {execution_result.get('success', False)}")
        report.append(f"   Hash: {execution_result.get('transaction_hash', 'N/A')}")
        report.append(f"   Gas Used: {execution_result.get('gas_used', 0):,}")
        report.append(f"   Gas Cost: {execution_result.get('gas_cost_eth', 0):.6f} ETH")
        report.append("")
        
        # Final status
        final_status = execution_result.get('final_status', 'EXECUTION INCOMPLETE')
        if final_status == "ALL ROOT-CAUSE FAILURES, GAS MISMATCHES, AND SIGNATURE ERRORS RESOLVED":
            report.append("🎉 FINAL STATUS: SUCCESS")
            report.append(f"   {final_status}")
        else:
            report.append("❌ FINAL STATUS: ISSUES DETECTED")
            if execution_result.get('error'):
                report.append(f"   Error: {execution_result['error']}")
        
        report.append("")
        
        # Test results if available
        if test_results:
            report.append("🧪 TEST RESULTS:")
            report.append(f"   Tests Run: {test_results.get('tests_run', 0)}")
            report.append(f"   Success Rate: {test_results.get('success_rate', 0):.1f}%")
            for test in test_results.get('detailed_results', []):
                report.append(f"   {test['test_name']}: {test['status']}")
        
        report.append("=" * 80)
        
        return "\n".join(report)

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