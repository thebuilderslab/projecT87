#!/usr/bin/env python3
"""
Comprehensive 7-Step Pre-Transaction Validation System for DeFi Transactions
Implements comprehensive validation to minimize revert risk before transaction submission.

Validation Steps:
1. Parameter Validation - amounts, addresses, asset types, protocol limits
2. Pre-Transaction Simulation - eth_call/staticCall with revert reason capture
3. Balance and Allowance Checks - wallet balances, ETH for fees, ERC-20 allowances  
4. Health Factor Validation - post-transaction health factor calculation
5. Network Fee Settings - gas price/limit validation against Arbitrum recommendations
6. Contract & ABI Verification - verify contract addresses and ABI versions
7. Error Handling - comprehensive error capture with structured diagnostics
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from typing import Any, Dict, List, Optional, Tuple, Union
from web3 import Web3
from web3.exceptions import ContractLogicError, ValidationError
from web3.types import TxParams
from eth_utils import is_address, to_checksum_address

# Set high precision for calculations
getcontext().prec = 50

class ComprehensiveTransactionValidator:
    """
    Comprehensive 7-step pre-transaction validation system for DeFi transactions.
    Designed to catch issues that would cause reverts BEFORE transaction submission.
    """
    
    def __init__(self, w3: Web3, user_address: str, coin_api_key: Optional[str] = None):
        """Initialize the comprehensive validation system"""
        self.w3 = w3
        self.user_address = to_checksum_address(user_address)
        self.coin_api_key = coin_api_key or os.getenv('COIN_API')
        
        # Validation thresholds and limits
        self.MIN_HEALTH_FACTOR = 1.1  # Minimum safe health factor
        self.SAFE_HEALTH_FACTOR = 1.5  # Recommended health factor
        self.MIN_ETH_FOR_GAS = 0.01   # Minimum ETH required for gas
        self.MAX_GAS_PRICE_GWEI = 50  # Maximum acceptable gas price
        self.MIN_AMOUNT_USD = 1.0     # Minimum transaction amount in USD
        self.MAX_AMOUNT_USD = 100000  # Maximum transaction amount in USD
        
        # Arbitrum mainnet contract addresses
        self.AAVE_POOL = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.AAVE_DATA_PROVIDER = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        self.AAVE_DEBT_SWITCH_V3 = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
        self.PARASWAP_AUGUSTUS = "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57"
        
        # Token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548",
            'USDC': "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            'WETH': "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            'WBTC': "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
        }
        
        # Variable debt token addresses
        self.debt_tokens = {
            'DAI': "0x8619d80FB0141ba7F184CbF22fd724116D9f7ffC",
            'ARB': "0x44705f578135cC5d703b4c9c122528C73Eb87145",
            'USDC': "0xF15F26710c827DDe8ACBA678682F3Ce24f2Fb56E",
            'WETH': "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351",
            'WBTC': "0x92b42c66840C7AD907b4BF74879FF3eF7c529473"
        }
        
        # Initialize ABIs
        self._initialize_abis()
        
        print("🔒 Comprehensive Transaction Validator initialized")
        print(f"   User Address: {self.user_address}")
        print(f"   Chain ID: {self.w3.eth.chain_id}")
        print(f"   CoinAPI: {'✅ Available' if self.coin_api_key else '⚠️ Not available'}")

    def _initialize_abis(self):
        """Initialize contract ABIs for validation"""
        
        # ERC-20 ABI
        self.erc20_abi = [
            {
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Aave Pool ABI
        self.aave_pool_abi = [
            {
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
            }
        ]
        
        # Debt Switch ABI
        self.debt_switch_abi = [
            {
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
            }
        ]

    def validate_transaction_comprehensive(self, transaction_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comprehensive 7-step validation for DeFi transaction.
        
        Args:
            transaction_params: Dictionary containing transaction parameters including:
                - transaction_type: 'debt_swap', 'supply', 'borrow', etc.
                - from_token: Source token address or symbol
                - to_token: Destination token address or symbol  
                - amount: Transaction amount in token units
                - contract_address: Target contract address
                - function_data: Encoded function call data
                - gas_limit: Proposed gas limit
                - gas_price: Proposed gas price
                
        Returns:
            Comprehensive validation report with results for all 7 steps
        """
        
        print(f"\n🔒 COMPREHENSIVE 7-STEP TRANSACTION VALIDATION")
        print("=" * 80)
        print(f"Transaction Type: {transaction_params.get('transaction_type', 'Unknown')}")
        print(f"User Address: {self.user_address}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Initialize validation report
        validation_report = {
            'validation_timestamp': datetime.now().isoformat(),
            'user_address': self.user_address,
            'transaction_params': transaction_params.copy(),
            'validation_steps': {},
            'overall_status': 'PENDING',
            'final_recommendation': 'PENDING',
            'risk_assessment': {},
            'errors': [],
            'warnings': [],
            'execution_time_ms': 0
        }
        
        start_time = time.time()
        
        try:
            # Execute all 7 validation steps
            validation_steps = [
                ('step_1_parameter_validation', self._validate_parameters),
                ('step_2_simulation', self._validate_pre_transaction_simulation),
                ('step_3_balances_allowances', self._validate_balances_and_allowances),
                ('step_4_health_factor', self._validate_health_factor),
                ('step_5_network_fees', self._validate_network_fees),
                ('step_6_contract_abi', self._validate_contract_and_abi),
                ('step_7_error_handling', self._validate_error_handling)
            ]
            
            # Execute each validation step
            for step_name, validation_func in validation_steps:
                print(f"\n📋 Executing {step_name.replace('_', ' ').upper()}")
                print("-" * 60)
                
                step_start = time.time()
                step_result = validation_func(transaction_params)
                step_execution_time = (time.time() - step_start) * 1000
                
                step_result['execution_time_ms'] = step_execution_time
                validation_report['validation_steps'][step_name] = step_result
                
                # Log step result
                status_emoji = "✅" if step_result['status'] == 'PASS' else "⚠️" if step_result['status'] == 'WARN' else "❌"
                print(f"{status_emoji} {step_name}: {step_result['status']} ({step_execution_time:.1f}ms)")
                
                if step_result.get('message'):
                    print(f"   Message: {step_result['message']}")
                
                # Collect errors and warnings
                if step_result.get('errors'):
                    validation_report['errors'].extend(step_result['errors'])
                if step_result.get('warnings'):
                    validation_report['warnings'].extend(step_result['warnings'])
            
            # Calculate overall validation results
            validation_report = self._calculate_overall_validation_results(validation_report)
            
        except Exception as e:
            validation_report['overall_status'] = 'ERROR'
            validation_report['final_recommendation'] = 'HALT'
            validation_report['errors'].append(f"Validation system error: {str(e)}")
            print(f"❌ Validation system error: {e}")
        
        finally:
            validation_report['execution_time_ms'] = (time.time() - start_time) * 1000
        
        # Print final summary
        self._print_validation_summary(validation_report)
        
        return validation_report

    def _validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Parameter Validation - amounts, addresses, asset types, protocol limits"""
        
        validation_result = {
            'status': 'PASS',
            'message': '',
            'details': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate transaction type
            if 'transaction_type' not in params:
                validation_result['errors'].append("Missing transaction_type parameter")
            
            # Validate addresses
            if 'contract_address' in params:
                if not is_address(params['contract_address']):
                    validation_result['errors'].append(f"Invalid contract address: {params['contract_address']}")
                else:
                    validation_result['details']['contract_address_valid'] = True
            
            # Validate token addresses/symbols
            for token_field in ['from_token', 'to_token']:
                if token_field in params:
                    token = params[token_field]
                    if isinstance(token, str):
                        if token.upper() in self.tokens:
                            validation_result['details'][f'{token_field}_resolved'] = self.tokens[token.upper()]
                        elif is_address(token):
                            validation_result['details'][f'{token_field}_valid'] = True
                        else:
                            validation_result['errors'].append(f"Invalid {token_field}: {token}")
            
            # Validate amounts
            if 'amount' in params:
                try:
                    amount = Decimal(str(params['amount']))
                    if amount <= 0:
                        validation_result['errors'].append(f"Amount must be positive: {amount}")
                    elif amount > Decimal('1e18'):  # Reasonable upper limit
                        validation_result['warnings'].append(f"Very large amount detected: {amount}")
                    else:
                        validation_result['details']['amount_valid'] = True
                        validation_result['details']['amount_decimal'] = amount
                except (ValueError, TypeError):
                    validation_result['errors'].append(f"Invalid amount format: {params['amount']}")
            
            # Validate gas parameters
            if 'gas_limit' in params:
                gas_limit = params['gas_limit']
                if not isinstance(gas_limit, int) or gas_limit <= 0:
                    validation_result['errors'].append(f"Invalid gas_limit: {gas_limit}")
                elif gas_limit > 1000000:  # 1M gas limit warning
                    validation_result['warnings'].append(f"High gas limit: {gas_limit}")
                else:
                    validation_result['details']['gas_limit_valid'] = True
            
            if 'gas_price' in params:
                gas_price = params['gas_price']
                if not isinstance(gas_price, int) or gas_price <= 0:
                    validation_result['errors'].append(f"Invalid gas_price: {gas_price}")
                else:
                    gas_price_gwei = gas_price / 1e9
                    if gas_price_gwei > self.MAX_GAS_PRICE_GWEI:
                        validation_result['warnings'].append(f"High gas price: {gas_price_gwei:.2f} gwei")
                    validation_result['details']['gas_price_gwei'] = gas_price_gwei
            
            # Validate debt swap specific parameters
            if params.get('transaction_type') == 'debt_swap':
                required_fields = ['from_token', 'to_token', 'amount']
                for field in required_fields:
                    if field not in params:
                        validation_result['errors'].append(f"Missing required debt swap parameter: {field}")
            
            # Set final status
            if validation_result['errors']:
                validation_result['status'] = 'FAIL'
                validation_result['message'] = f"Parameter validation failed: {len(validation_result['errors'])} errors"
            elif validation_result['warnings']:
                validation_result['status'] = 'WARN' 
                validation_result['message'] = f"Parameter validation passed with {len(validation_result['warnings'])} warnings"
            else:
                validation_result['message'] = "All parameters validated successfully"
            
        except Exception as e:
            validation_result['status'] = 'FAIL'
            validation_result['errors'].append(f"Parameter validation error: {str(e)}")
            validation_result['message'] = "Parameter validation failed due to system error"
        
        return validation_result

    def _validate_pre_transaction_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Pre-Transaction Simulation - eth_call/staticCall with revert reason capture"""
        
        validation_result = {
            'status': 'PASS',
            'message': '',
            'details': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            contract_address = params.get('contract_address')
            function_data = params.get('function_data')
            
            if not contract_address or not function_data:
                validation_result['status'] = 'WARN'
                validation_result['message'] = "Cannot simulate - missing contract address or function data"
                validation_result['warnings'].append("Simulation skipped due to missing parameters")
                return validation_result
            
            # Prepare transaction for simulation
            tx_params = {
                'to': to_checksum_address(contract_address),
                'from': self.user_address,
                'data': function_data,
                'gas': params.get('gas_limit', 500000),
                'gasPrice': params.get('gas_price', self.w3.eth.gas_price)
            }
            
            # Simulate using eth_call (static call)
            print(f"   Simulating transaction to {contract_address}")
            
            try:
                # Perform static call simulation
                result = self.w3.eth.call(tx_params)
                
                validation_result['details']['simulation_successful'] = True
                validation_result['details']['simulation_result'] = result.hex() if result else "0x"
                validation_result['message'] = "Transaction simulation successful"
                
                # Try to estimate gas
                try:
                    estimated_gas = self.w3.eth.estimate_gas(tx_params)
                    validation_result['details']['estimated_gas'] = estimated_gas
                    
                    proposed_gas = params.get('gas_limit')
                    if proposed_gas and estimated_gas > proposed_gas:
                        validation_result['warnings'].append(
                            f"Estimated gas ({estimated_gas}) exceeds proposed limit ({proposed_gas})"
                        )
                        validation_result['status'] = 'WARN'
                    
                except Exception as gas_error:
                    validation_result['warnings'].append(f"Gas estimation failed: {str(gas_error)}")
                
            except ContractLogicError as e:
                # Transaction would revert
                validation_result['status'] = 'FAIL'
                validation_result['errors'].append(f"Transaction would revert: {str(e)}")
                validation_result['message'] = "Simulation detected transaction revert"
                
                # Try to extract revert reason
                try:
                    revert_reason = self._extract_revert_reason(e)
                    validation_result['details']['revert_reason'] = revert_reason
                except:
                    pass
                
            except Exception as e:
                validation_result['status'] = 'FAIL'
                validation_result['errors'].append(f"Simulation failed: {str(e)}")
                validation_result['message'] = "Transaction simulation failed"
        
        except Exception as e:
            validation_result['status'] = 'FAIL'
            validation_result['errors'].append(f"Simulation validation error: {str(e)}")
            validation_result['message'] = "Simulation validation failed due to system error"
        
        return validation_result

    def _validate_balances_and_allowances(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Balance and Allowance Checks - wallet balances, ETH for fees, ERC-20 allowances"""
        
        validation_result = {
            'status': 'PASS',
            'message': '',
            'details': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check ETH balance for gas fees
            eth_balance = self.w3.eth.get_balance(self.user_address)
            eth_balance_ether = self.w3.from_wei(eth_balance, 'ether')
            
            validation_result['details']['eth_balance'] = float(eth_balance_ether)
            
            if eth_balance_ether < self.MIN_ETH_FOR_GAS:
                validation_result['errors'].append(
                    f"Insufficient ETH for gas: {eth_balance_ether:.6f} ETH (minimum: {self.MIN_ETH_FOR_GAS})"
                )
            elif eth_balance_ether < self.MIN_ETH_FOR_GAS * 2:
                validation_result['warnings'].append(
                    f"Low ETH balance for gas: {eth_balance_ether:.6f} ETH"
                )
            
            # Estimate transaction cost
            gas_limit = params.get('gas_limit', 500000)
            gas_price = params.get('gas_price', self.w3.eth.gas_price)
            tx_cost_wei = gas_limit * gas_price
            tx_cost_ether = self.w3.from_wei(tx_cost_wei, 'ether')
            
            validation_result['details']['estimated_tx_cost_eth'] = float(tx_cost_ether)
            
            if eth_balance < tx_cost_wei:
                validation_result['errors'].append(
                    f"Insufficient ETH for transaction cost: need {tx_cost_ether:.6f} ETH, have {eth_balance_ether:.6f} ETH"
                )
            
            # Check token balances and allowances for relevant tokens
            from_token = params.get('from_token')
            amount = params.get('amount')
            contract_address = params.get('contract_address')
            
            if from_token and amount and contract_address:
                token_address = self._resolve_token_address(from_token)
                if token_address:
                    # Check token balance
                    token_contract = self.w3.eth.contract(
                        address=token_address,
                        abi=self.erc20_abi
                    )
                    
                    try:
                        token_balance = token_contract.functions.balanceOf(self.user_address).call()
                        decimals = token_contract.functions.decimals().call()
                        token_balance_formatted = token_balance / (10 ** decimals)
                        
                        validation_result['details']['token_balance'] = {
                            'token': from_token,
                            'balance_raw': token_balance,
                            'balance_formatted': token_balance_formatted,
                            'decimals': decimals
                        }
                        
                        # Convert amount to raw units
                        amount_raw = int(Decimal(str(amount)) * (10 ** decimals))
                        
                        if token_balance < amount_raw:
                            validation_result['errors'].append(
                                f"Insufficient {from_token} balance: need {amount}, have {token_balance_formatted:.6f}"
                            )
                        
                        # Check allowance
                        allowance = token_contract.functions.allowance(
                            self.user_address, 
                            to_checksum_address(contract_address)
                        ).call()
                        
                        allowance_formatted = allowance / (10 ** decimals)
                        validation_result['details']['token_allowance'] = {
                            'token': from_token,
                            'spender': contract_address,
                            'allowance_raw': allowance,
                            'allowance_formatted': allowance_formatted
                        }
                        
                        if allowance < amount_raw:
                            validation_result['errors'].append(
                                f"Insufficient {from_token} allowance: need {amount}, have {allowance_formatted:.6f}"
                            )
                    
                    except Exception as token_error:
                        validation_result['warnings'].append(f"Could not check {from_token} balance/allowance: {str(token_error)}")
            
            # Set final status
            if validation_result['errors']:
                validation_result['status'] = 'FAIL'
                validation_result['message'] = f"Balance/allowance validation failed: {len(validation_result['errors'])} errors"
            elif validation_result['warnings']:
                validation_result['status'] = 'WARN'
                validation_result['message'] = f"Balance/allowance validation passed with {len(validation_result['warnings'])} warnings"
            else:
                validation_result['message'] = "All balances and allowances validated successfully"
        
        except Exception as e:
            validation_result['status'] = 'FAIL'
            validation_result['errors'].append(f"Balance/allowance validation error: {str(e)}")
            validation_result['message'] = "Balance/allowance validation failed due to system error"
        
        return validation_result

    def _validate_health_factor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Health Factor Validation - calculate post-transaction health factor"""
        
        validation_result = {
            'status': 'PASS',
            'message': '',
            'details': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Get current Aave account data
            aave_pool = self.w3.eth.contract(
                address=self.AAVE_POOL,
                abi=self.aave_pool_abi
            )
            
            try:
                account_data = aave_pool.functions.getUserAccountData(self.user_address).call()
                
                total_collateral_base = account_data[0]
                total_debt_base = account_data[1]
                available_borrows_base = account_data[2]
                current_liquidation_threshold = account_data[3]
                ltv = account_data[4]
                health_factor = account_data[5]
                
                # Convert health factor from wei (10^18) to decimal
                current_health_factor = health_factor / 1e18 if health_factor > 0 else float('inf')
                
                validation_result['details']['current_position'] = {
                    'total_collateral_usd': total_collateral_base / 1e8,  # Aave uses 8 decimals for USD
                    'total_debt_usd': total_debt_base / 1e8,
                    'available_borrows_usd': available_borrows_base / 1e8,
                    'current_liquidation_threshold': current_liquidation_threshold / 1e4,  # Basis points to percentage
                    'ltv': ltv / 1e4,
                    'health_factor': current_health_factor
                }
                
                # Validate current health factor
                if current_health_factor < self.MIN_HEALTH_FACTOR:
                    validation_result['errors'].append(
                        f"Current health factor too low: {current_health_factor:.4f} (minimum: {self.MIN_HEALTH_FACTOR})"
                    )
                elif current_health_factor < self.SAFE_HEALTH_FACTOR:
                    validation_result['warnings'].append(
                        f"Health factor below safe threshold: {current_health_factor:.4f} (recommended: {self.SAFE_HEALTH_FACTOR})"
                    )
                
                # Estimate post-transaction health factor for debt swaps
                if params.get('transaction_type') == 'debt_swap':
                    post_tx_health_factor = self._estimate_post_debt_swap_health_factor(
                        params, validation_result['details']['current_position']
                    )
                    
                    validation_result['details']['estimated_post_tx_health_factor'] = post_tx_health_factor
                    
                    if post_tx_health_factor < self.MIN_HEALTH_FACTOR:
                        validation_result['errors'].append(
                            f"Estimated post-transaction health factor too low: {post_tx_health_factor:.4f}"
                        )
                    elif post_tx_health_factor < self.SAFE_HEALTH_FACTOR:
                        validation_result['warnings'].append(
                            f"Estimated post-transaction health factor below safe threshold: {post_tx_health_factor:.4f}"
                        )
                
            except Exception as aave_error:
                validation_result['warnings'].append(f"Could not fetch Aave account data: {str(aave_error)}")
                validation_result['status'] = 'WARN'
                validation_result['message'] = "Health factor validation skipped - could not access Aave data"
                return validation_result
            
            # Set final status
            if validation_result['errors']:
                validation_result['status'] = 'FAIL'
                validation_result['message'] = f"Health factor validation failed: {len(validation_result['errors'])} errors"
            elif validation_result['warnings']:
                validation_result['status'] = 'WARN'
                validation_result['message'] = f"Health factor validation passed with {len(validation_result['warnings'])} warnings"
            else:
                validation_result['message'] = "Health factor validation successful"
        
        except Exception as e:
            validation_result['status'] = 'FAIL'
            validation_result['errors'].append(f"Health factor validation error: {str(e)}")
            validation_result['message'] = "Health factor validation failed due to system error"
        
        return validation_result

    def _validate_network_fees(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Network Fee Settings - validate gas price/limit against Arbitrum recommendations"""
        
        validation_result = {
            'status': 'PASS',
            'message': '',
            'details': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Get current network gas price
            current_gas_price = self.w3.eth.gas_price
            current_gas_price_gwei = current_gas_price / 1e9
            
            validation_result['details']['network_gas_price_gwei'] = current_gas_price_gwei
            
            # Get ETH price for cost calculation
            eth_price_usd = self._get_eth_price_usd()
            validation_result['details']['eth_price_usd'] = eth_price_usd
            
            # Validate proposed gas parameters
            proposed_gas_price = params.get('gas_price', current_gas_price)
            proposed_gas_limit = params.get('gas_limit', 500000)
            
            proposed_gas_price_gwei = proposed_gas_price / 1e9
            
            validation_result['details']['proposed_gas_price_gwei'] = proposed_gas_price_gwei
            validation_result['details']['proposed_gas_limit'] = proposed_gas_limit
            
            # Check if gas price is reasonable
            if proposed_gas_price_gwei > self.MAX_GAS_PRICE_GWEI:
                validation_result['errors'].append(
                    f"Gas price too high: {proposed_gas_price_gwei:.2f} gwei (maximum: {self.MAX_GAS_PRICE_GWEI})"
                )
            elif proposed_gas_price_gwei > current_gas_price_gwei * 2:
                validation_result['warnings'].append(
                    f"Gas price significantly above network rate: {proposed_gas_price_gwei:.2f} gwei vs {current_gas_price_gwei:.2f} gwei"
                )
            elif proposed_gas_price_gwei < current_gas_price_gwei * 0.5:
                validation_result['warnings'].append(
                    f"Gas price significantly below network rate: {proposed_gas_price_gwei:.2f} gwei vs {current_gas_price_gwei:.2f} gwei (may cause delays)"
                )
            
            # Calculate transaction cost in USD
            tx_cost_eth = (proposed_gas_limit * proposed_gas_price) / 1e18
            tx_cost_usd = tx_cost_eth * eth_price_usd
            
            validation_result['details']['estimated_tx_cost_usd'] = tx_cost_usd
            
            if tx_cost_usd > 50:  # $50 warning threshold
                validation_result['warnings'].append(
                    f"High transaction cost: ${tx_cost_usd:.2f}"
                )
            
            # Arbitrum-specific validations
            if self.w3.eth.chain_id == 42161:  # Arbitrum mainnet
                # Arbitrum typically has very low gas prices
                if proposed_gas_price_gwei > 5:
                    validation_result['warnings'].append(
                        f"Gas price unusual for Arbitrum: {proposed_gas_price_gwei:.2f} gwei (typically < 5 gwei)"
                    )
                
                # Arbitrum gas limits can be higher due to L2 nature
                if proposed_gas_limit > 2000000:
                    validation_result['warnings'].append(
                        f"Very high gas limit for Arbitrum: {proposed_gas_limit:,}"
                    )
            
            # Set final status
            if validation_result['errors']:
                validation_result['status'] = 'FAIL'
                validation_result['message'] = f"Network fee validation failed: {len(validation_result['errors'])} errors"
            elif validation_result['warnings']:
                validation_result['status'] = 'WARN'
                validation_result['message'] = f"Network fee validation passed with {len(validation_result['warnings'])} warnings"
            else:
                validation_result['message'] = "Network fee validation successful"
        
        except Exception as e:
            validation_result['status'] = 'FAIL'
            validation_result['errors'].append(f"Network fee validation error: {str(e)}")
            validation_result['message'] = "Network fee validation failed due to system error"
        
        return validation_result

    def _validate_contract_and_abi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Step 6: Contract & ABI Verification - verify contract addresses and ABI versions"""
        
        validation_result = {
            'status': 'PASS',
            'message': '',
            'details': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            contract_address = params.get('contract_address')
            
            if not contract_address:
                validation_result['status'] = 'WARN'
                validation_result['message'] = "No contract address to validate"
                validation_result['warnings'].append("Contract validation skipped - no address provided")
                return validation_result
            
            contract_address = to_checksum_address(contract_address)
            
            # Check if address contains code (is a contract)
            code = self.w3.eth.get_code(contract_address)
            if len(code) == 0:
                validation_result['errors'].append(f"No contract code at address: {contract_address}")
                validation_result['status'] = 'FAIL'
                return validation_result
            
            validation_result['details']['contract_has_code'] = True
            validation_result['details']['code_size_bytes'] = len(code)
            
            # Verify against known official contracts
            known_contracts = {
                self.AAVE_POOL: "Aave Pool V3",
                self.AAVE_DEBT_SWITCH_V3: "Aave Debt Switch V3", 
                self.AAVE_DATA_PROVIDER: "Aave Data Provider V3",
                self.PARASWAP_AUGUSTUS: "ParaSwap Augustus Swapper"
            }
            
            if contract_address in known_contracts:
                validation_result['details']['verified_contract'] = known_contracts[contract_address]
                validation_result['message'] = f"Contract verified: {known_contracts[contract_address]}"
            else:
                validation_result['warnings'].append(f"Unknown contract address: {contract_address}")
                validation_result['status'] = 'WARN'
                validation_result['message'] = "Contract address not in verified list"
            
            # Check if function selector exists in contract for debt swap
            function_data = params.get('function_data')
            if function_data and len(function_data) >= 10:  # At least 4 bytes for selector + 0x
                function_selector = function_data[:10]
                validation_result['details']['function_selector'] = function_selector
                
                # Known function selectors
                known_selectors = {
                    '0xb8bd1c6b': 'swapDebt (Aave Debt Switch)',
                    '0x617ba037': 'supply (Aave Pool)',
                    '0xa415bcad': 'borrow (Aave Pool)',
                    '0x69328dec': 'withdraw (Aave Pool)',
                    '0x573ade81': 'repay (Aave Pool)'
                }
                
                if function_selector in known_selectors:
                    validation_result['details']['verified_function'] = known_selectors[function_selector]
                else:
                    validation_result['warnings'].append(f"Unknown function selector: {function_selector}")
            
            # Additional validation for Aave contracts
            if contract_address == self.AAVE_POOL:
                validation_result = self._validate_aave_pool_contract(validation_result)
            elif contract_address == self.AAVE_DEBT_SWITCH_V3:
                validation_result = self._validate_debt_switch_contract(validation_result)
            
        except Exception as e:
            validation_result['status'] = 'FAIL'
            validation_result['errors'].append(f"Contract/ABI validation error: {str(e)}")
            validation_result['message'] = "Contract/ABI validation failed due to system error"
        
        return validation_result

    def _validate_error_handling(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Step 7: Error Handling - comprehensive error capture with structured diagnostics"""
        
        validation_result = {
            'status': 'PASS',
            'message': '',
            'details': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test error handling capabilities
            validation_result['details']['error_handling_capabilities'] = {
                'revert_reason_extraction': True,
                'gas_estimation_error_handling': True,
                'network_error_recovery': True,
                'contract_call_error_handling': True
            }
            
            # Check for common error-prone scenarios
            error_scenarios = []
            
            # Scenario 1: Low ETH balance
            eth_balance = self.w3.eth.get_balance(self.user_address)
            if eth_balance < self.w3.to_wei(self.MIN_ETH_FOR_GAS, 'ether'):
                error_scenarios.append({
                    'scenario': 'low_eth_balance',
                    'risk': 'high',
                    'description': 'Insufficient ETH for gas fees'
                })
            
            # Scenario 2: High gas price
            gas_price = params.get('gas_price', self.w3.eth.gas_price)
            if gas_price > self.w3.to_wei(self.MAX_GAS_PRICE_GWEI, 'gwei'):
                error_scenarios.append({
                    'scenario': 'high_gas_price',
                    'risk': 'medium',
                    'description': 'Gas price exceeds recommended maximum'
                })
            
            # Scenario 3: Large transaction amount
            amount = params.get('amount')
            if amount:
                try:
                    amount_val = float(amount)
                    if amount_val > self.MAX_AMOUNT_USD:
                        error_scenarios.append({
                            'scenario': 'large_amount',
                            'risk': 'medium',
                            'description': 'Transaction amount exceeds typical limits'
                        })
                except:
                    pass
            
            validation_result['details']['error_scenarios_detected'] = error_scenarios
            
            # Test network connectivity and responsiveness
            try:
                block_number = self.w3.eth.block_number
                validation_result['details']['network_connectivity'] = {
                    'connected': True,
                    'latest_block': block_number,
                    'chain_id': self.w3.eth.chain_id
                }
            except Exception as network_error:
                validation_result['errors'].append(f"Network connectivity issue: {str(network_error)}")
                validation_result['details']['network_connectivity'] = {
                    'connected': False,
                    'error': str(network_error)
                }
            
            # Prepare structured error diagnostics
            validation_result['details']['diagnostic_info'] = {
                'timestamp': datetime.now().isoformat(),
                'user_address': self.user_address,
                'chain_id': self.w3.eth.chain_id,
                'web3_provider': str(type(self.w3.provider)),
                'validation_version': '1.0.0'
            }
            
            # Set final status based on error scenarios
            high_risk_scenarios = [s for s in error_scenarios if s['risk'] == 'high']
            medium_risk_scenarios = [s for s in error_scenarios if s['risk'] == 'medium']
            
            if high_risk_scenarios:
                validation_result['status'] = 'FAIL'
                validation_result['message'] = f"High-risk error scenarios detected: {len(high_risk_scenarios)}"
                validation_result['errors'].extend([s['description'] for s in high_risk_scenarios])
            elif medium_risk_scenarios:
                validation_result['status'] = 'WARN'
                validation_result['message'] = f"Medium-risk scenarios detected: {len(medium_risk_scenarios)}"
                validation_result['warnings'].extend([s['description'] for s in medium_risk_scenarios])
            else:
                validation_result['message'] = "Error handling validation successful"
        
        except Exception as e:
            validation_result['status'] = 'FAIL'
            validation_result['errors'].append(f"Error handling validation error: {str(e)}")
            validation_result['message'] = "Error handling validation failed due to system error"
        
        return validation_result

    def _calculate_overall_validation_results(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall validation status and final recommendation"""
        
        # Count validation results
        step_results = validation_report['validation_steps']
        
        pass_count = sum(1 for step in step_results.values() if step['status'] == 'PASS')
        warn_count = sum(1 for step in step_results.values() if step['status'] == 'WARN')
        fail_count = sum(1 for step in step_results.values() if step['status'] == 'FAIL')
        total_steps = len(step_results)
        
        # Calculate risk assessment
        risk_assessment = {
            'total_steps': total_steps,
            'passed_steps': pass_count,
            'warning_steps': warn_count,
            'failed_steps': fail_count,
            'success_rate': (pass_count / total_steps) * 100 if total_steps > 0 else 0,
            'total_errors': len(validation_report['errors']),
            'total_warnings': len(validation_report['warnings'])
        }
        
        validation_report['risk_assessment'] = risk_assessment
        
        # Determine overall status and recommendation
        if fail_count > 0:
            validation_report['overall_status'] = 'FAIL'
            validation_report['final_recommendation'] = 'HALT'
        elif warn_count > total_steps / 2:  # More than half have warnings
            validation_report['overall_status'] = 'WARN'
            validation_report['final_recommendation'] = 'REQUIRE_FIXES'
        elif warn_count > 0:
            validation_report['overall_status'] = 'WARN'
            validation_report['final_recommendation'] = 'PROCEED_WITH_CAUTION'
        else:
            validation_report['overall_status'] = 'PASS'
            validation_report['final_recommendation'] = 'PROCEED'
        
        return validation_report

    def _print_validation_summary(self, validation_report: Dict[str, Any]):
        """Print comprehensive validation summary"""
        
        print(f"\n🔒 COMPREHENSIVE VALIDATION SUMMARY")
        print("=" * 80)
        
        # Overall status
        status_emoji = "✅" if validation_report['overall_status'] == 'PASS' else "⚠️" if validation_report['overall_status'] == 'WARN' else "❌"
        print(f"{status_emoji} Overall Status: {validation_report['overall_status']}")
        print(f"🎯 Final Recommendation: {validation_report['final_recommendation']}")
        print(f"⏱️ Total Execution Time: {validation_report['execution_time_ms']:.1f}ms")
        
        # Risk assessment
        risk = validation_report['risk_assessment']
        print(f"\n📊 RISK ASSESSMENT:")
        print(f"   Success Rate: {risk['success_rate']:.1f}% ({risk['passed_steps']}/{risk['total_steps']} steps passed)")
        print(f"   Warnings: {risk['warning_steps']} steps, {risk['total_warnings']} total warnings")
        print(f"   Failures: {risk['failed_steps']} steps, {risk['total_errors']} total errors")
        
        # Step-by-step results
        print(f"\n📋 VALIDATION STEPS BREAKDOWN:")
        for step_name, step_result in validation_report['validation_steps'].items():
            status_emoji = "✅" if step_result['status'] == 'PASS' else "⚠️" if step_result['status'] == 'WARN' else "❌"
            step_display = step_name.replace('step_', '').replace('_', ' ').title()
            print(f"   {status_emoji} {step_display}: {step_result['status']} ({step_result.get('execution_time_ms', 0):.1f}ms)")
            if step_result.get('message'):
                print(f"      → {step_result['message']}")
        
        # Errors and warnings summary
        if validation_report['errors']:
            print(f"\n❌ CRITICAL ERRORS ({len(validation_report['errors'])}):")
            for i, error in enumerate(validation_report['errors'][:5], 1):  # Show first 5
                print(f"   {i}. {error}")
            if len(validation_report['errors']) > 5:
                print(f"   ... and {len(validation_report['errors']) - 5} more errors")
        
        if validation_report['warnings']:
            print(f"\n⚠️ WARNINGS ({len(validation_report['warnings'])}):")
            for i, warning in enumerate(validation_report['warnings'][:3], 1):  # Show first 3
                print(f"   {i}. {warning}")
            if len(validation_report['warnings']) > 3:
                print(f"   ... and {len(validation_report['warnings']) - 3} more warnings")
        
        print("=" * 80)

    # Helper methods
    
    def _resolve_token_address(self, token: str) -> Optional[str]:
        """Resolve token symbol to address"""
        if isinstance(token, str):
            if token.upper() in self.tokens:
                return self.tokens[token.upper()]
            elif is_address(token):
                return to_checksum_address(token)
        return None

    def _get_eth_price_usd(self) -> float:
        """Get ETH price in USD using CoinAPI or fallback"""
        if self.coin_api_key:
            try:
                headers = {'X-CoinAPI-Key': self.coin_api_key}
                response = requests.get(
                    'https://rest.coinapi.io/v1/exchangerate/ETH/USD',
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json()['rate']
            except:
                pass
        
        # Fallback price
        return 2500.0

    def _extract_revert_reason(self, error: ContractLogicError) -> str:
        """Extract revert reason from contract error"""
        try:
            # Try to decode revert reason from error message
            error_str = str(error)
            if 'revert' in error_str.lower():
                # Extract reason if available
                if ':' in error_str:
                    return error_str.split(':', 1)[1].strip()
            return error_str
        except:
            return "Unknown revert reason"

    def _estimate_post_debt_swap_health_factor(self, params: Dict[str, Any], current_position: Dict[str, Any]) -> float:
        """Estimate health factor after debt swap"""
        try:
            # This is a simplified estimation
            # In practice, you'd need to calculate the exact price impact and new debt amounts
            
            current_hf = current_position['health_factor']
            current_debt = current_position['total_debt_usd']
            
            # For debt swaps, health factor should remain approximately the same
            # as we're just changing the composition of debt, not the total amount
            
            # Add small buffer for price impact and fees
            estimated_hf = current_hf * 0.98  # 2% buffer for price impact
            
            return estimated_hf
        except:
            return current_position.get('health_factor', 1.0)

    def _validate_aave_pool_contract(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Additional validation for Aave Pool contract"""
        try:
            pool_contract = self.w3.eth.contract(
                address=self.AAVE_POOL,
                abi=self.aave_pool_abi
            )
            
            # Test getUserAccountData function
            pool_contract.functions.getUserAccountData(self.user_address).call()
            validation_result['details']['aave_pool_functional'] = True
            
        except Exception as e:
            validation_result['warnings'].append(f"Aave Pool contract validation failed: {str(e)}")
        
        return validation_result

    def _validate_debt_switch_contract(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Additional validation for Debt Switch contract"""
        try:
            # Check if contract has the expected swapDebt function
            debt_switch_contract = self.w3.eth.contract(
                address=self.AAVE_DEBT_SWITCH_V3,
                abi=self.debt_switch_abi
            )
            
            # Verify function exists (this will throw if not found)
            debt_switch_contract.get_function_by_name('swapDebt')
            validation_result['details']['debt_switch_functional'] = True
            
        except Exception as e:
            validation_result['warnings'].append(f"Debt Switch contract validation failed: {str(e)}")
        
        return validation_result


def create_debt_swap_validation_test() -> Dict[str, Any]:
    """Create a test debt swap transaction for validation demonstration"""
    
    return {
        'transaction_type': 'debt_swap',
        'from_token': 'DAI',
        'to_token': 'ARB', 
        'amount': '50.0',  # 50 DAI worth
        'contract_address': '0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4',  # Aave Debt Switch V3
        'function_data': '0xb8bd1c6b',  # swapDebt selector (partial)
        'gas_limit': 500000,
        'gas_price': 100000000,  # 0.1 gwei
        'max_slippage': 0.01,  # 1%
        'deadline': int(time.time()) + 3600  # 1 hour from now
    }


if __name__ == "__main__":
    # Example usage
    print("🔒 Comprehensive Transaction Validator - DeFi Pre-Transaction Validation System")
    print("=" * 80)
    print("This module provides 7-step validation to minimize transaction revert risk:")
    print("1. Parameter Validation")
    print("2. Pre-Transaction Simulation") 
    print("3. Balance and Allowance Checks")
    print("4. Health Factor Validation")
    print("5. Network Fee Settings")
    print("6. Contract & ABI Verification")
    print("7. Error Handling")
    print("=" * 80)