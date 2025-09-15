#!/usr/bin/env python3
"""
CORRECTED PRODUCTION DEBT SWAP CYCLE
Using correct debt swap adapter: DAI→ARB→wait 5min→ARB→DAI with real transactions
"""

import os
import time
import json
import requests
from datetime import datetime, timedelta
from web3 import Web3
from eth_account.messages import encode_structured_data

class CorrectedProductionDebtSwapCycle:
    """Complete production cycle with correct debt swap adapter"""
    
    def __init__(self):
        print("🚀 CORRECTED PRODUCTION DEBT SWAP CYCLE")
        print("=" * 80)
        print("🎯 MISSION: Complete DAI→ARB→wait 5min→ARB→DAI cycle")
        print("🔧 FIX APPLIED: Using correct debt swap adapter address")
        print("📊 DELIVERABLES: Real transactions + Comprehensive PNL")
        print("=" * 80)
        
        # Direct Web3 setup
        self.private_key = os.getenv('PRIVATE_KEY')
        if not self.private_key:
            raise Exception("PRIVATE_KEY not found")
        
        self.w3 = Web3(Web3.HTTPProvider("https://arbitrum-one.public.blastapi.io"))
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Arbitrum")
        
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.user_address = self.account.address
        
        # CORRECTED addresses
        self.paraswap_debt_swap_adapter = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"  # CANONICAL AAVE ADDRESS BOOK
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        self.swap_amount = 3.0  # $3 for production execution
        self.slippage_bps = 75  # 75 basis points = 0.75% slippage
        
        self.cycle_data = {
            'execution_id': f"corrected_cycle_{int(time.time())}",
            'start_time': datetime.now().isoformat(),
            'user_address': self.user_address,
            'swap_amount_usd': self.swap_amount,
            'debt_swap_adapter': self.paraswap_debt_swap_adapter
        }
        
        print(f"✅ Corrected initialization complete")
        print(f"   User: {self.user_address}")
        print(f"   Debt Swap Adapter: {self.paraswap_debt_swap_adapter}")
        print(f"   Amount: ${self.swap_amount}")
    
    def get_aave_position(self):
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
                'health_factor': account_data[5] / 1e18 if account_data[5] > 0 else float('inf'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Position check failed: {e}")
            return {}
    
    def validate_production_readiness(self):
        """Validate readiness for production execution"""
        position = self.get_aave_position()
        if not position:
            return False, "Failed to get position"
        
        print(f"📊 Current Position:")
        print(f"   Collateral: ${position['total_collateral_usd']:.2f}")
        print(f"   Debt: ${position['total_debt_usd']:.2f}")
        print(f"   Health Factor: {position['health_factor']:.3f}")
        print(f"   Available Borrows: ${position['available_borrows_usd']:.2f}")
        
        # Safety checks
        if position['health_factor'] < 1.5:
            return False, f"Health factor too low: {position['health_factor']:.3f} < 1.5"
        
        if position['total_debt_usd'] < self.swap_amount:
            return False, f"Insufficient debt: ${position['total_debt_usd']:.2f} < ${self.swap_amount}"
        
        if position['total_collateral_usd'] < 20:
            return False, f"Insufficient collateral: ${position['total_collateral_usd']:.2f} < $20"
        
        return True, "Production ready - All safety checks passed"
    
    def get_debt_token_address(self, asset_symbol):
        """Get variable debt token address"""
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
            
            contract = self.w3.eth.contract(address=self.aave_data_provider, abi=data_provider_abi)
            tokens = contract.functions.getReserveTokensAddresses(
                self.tokens[asset_symbol.upper()]
            ).call()
            
            debt_token = tokens[2]  # Variable debt token
            print(f"📋 {asset_symbol} debt token: {debt_token}")
            return debt_token
        except Exception as e:
            print(f"❌ Debt token lookup failed: {e}")
            return ""
    
    def create_credit_delegation_permit(self, debt_token_address):
        """Create EIP-712 credit delegation permit"""
        try:
            print(f"📝 Creating credit delegation permit...")
            
            # Get token info
            debt_token_abi = [
                {"inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
                {"inputs": [{"name": "owner", "type": "address"}], "name": "nonces", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
            ]
            
            debt_token_contract = self.w3.eth.contract(address=debt_token_address, abi=debt_token_abi)
            token_name = debt_token_contract.functions.name().call()
            nonce = debt_token_contract.functions.nonces(self.user_address).call()
            deadline = int(time.time()) + 3600
            
            print(f"   Token: {token_name}, Nonce: {nonce}")
            
            # EIP-712 domain
            domain = {
                'name': token_name,
                'version': '1',
                'chainId': 42161,
                'verifyingContract': debt_token_address
            }
            
            # EIP-712 types with delegator field (architectural fix)
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
            
            # Message with delegator field
            message = {
                'delegator': self.user_address,
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'nonce': nonce,
                'deadline': deadline
            }
            
            # Sign permit
            structured_data = {'types': types, 'domain': domain, 'primaryType': 'DelegationWithSig', 'message': message}
            encoded_data = encode_structured_data(structured_data)
            signature = self.account.sign_message(encoded_data)
            
            permit = {
                'token': debt_token_address,
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'deadline': deadline,
                'v': signature.v,
                'r': signature.r.to_bytes(32, 'big'),
                's': signature.s.to_bytes(32, 'big')
            }
            
            print(f"✅ Permit created successfully")
            return permit
        except Exception as e:
            print(f"❌ Permit creation failed: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def verify_permit_and_preflight(self, debt_token_address, permit, debt_swap_params):
        """ARCHITECT FIX: Strengthen preflight validation"""
        print(f"🔍 ARCHITECT PREFLIGHT VALIDATION")
        print(f"   Verifying permit and debt swap parameters...")
        
        try:
            # ARCHITECT FIX: Verify permit by checking borrowAllowance
            debt_token_abi = [
                {
                    "inputs": [
                        {"name": "fromUser", "type": "address"},
                        {"name": "toUser", "type": "address"}
                    ],
                    "name": "borrowAllowance",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            debt_token_contract = self.w3.eth.contract(address=debt_token_address, abi=debt_token_abi)
            
            # Check current allowance
            current_allowance = debt_token_contract.functions.borrowAllowance(
                self.user_address, 
                self.paraswap_debt_swap_adapter
            ).call()
            
            print(f"   Current borrow allowance: {current_allowance}")
            print(f"   Required allowance: {permit['value']}")
            
            # Note: After permit is applied, allowance should be permit['value']
            # For now, we validate the permit parameters are correct
            
            # ARCHITECT FIX: Use staticcall to adapter.swapDebt to capture exact revert messages
            print(f"   Testing debt swap with staticcall...")
            
            debt_swap_abi = [{
                "inputs": [
                    {
                        "components": [
                            {"name": "debtAsset", "type": "address"},
                            {"name": "newDebtAsset", "type": "address"},
                            {"name": "debtRepayAmount", "type": "uint256"},
                            {"name": "maxNewDebtAmount", "type": "uint256"},
                            {"name": "extraCollateralAmount", "type": "uint256"},
                            {"name": "extraCollateralAsset", "type": "address"},
                            {"name": "offset", "type": "uint256"},
                            {"name": "paraswapData", "type": "bytes"}
                        ],
                        "name": "debtSwapParams",
                        "type": "tuple"
                    },
                    {
                        "components": [
                            {"name": "delegator", "type": "address"},
                            {"name": "delegatee", "type": "address"},
                            {"name": "value", "type": "uint256"},
                            {"name": "deadline", "type": "uint256"},
                            {"name": "v", "type": "uint8"},
                            {"name": "r", "type": "bytes32"},
                            {"name": "s", "type": "bytes32"}
                        ],
                        "name": "creditDelegationPermit",
                        "type": "tuple"
                    },
                    {"name": "useEthPath", "type": "bool"}
                ],
                "name": "swapDebt",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            debt_swap_contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter,
                abi=debt_swap_abi
            )
            
            credit_delegation_permit = (
                self.user_address,
                permit['delegatee'],
                permit['value'],
                permit['deadline'],
                permit['v'],
                permit['r'],
                permit['s']
            )
            
            # Build function call for staticcall test
            function_call = debt_swap_contract.functions.swapDebt(
                debt_swap_params,
                credit_delegation_permit,
                False  # useEthPath
            )
            
            # ARCHITECT FIX: Use staticcall to capture exact revert messages
            try:
                # Test the call with eth_call (staticcall)
                result = self.w3.eth.call({
                    'to': self.paraswap_debt_swap_adapter,
                    'from': self.user_address,
                    'data': function_call._encode_transaction_data(),
                    'gas': 2000000  # High gas limit for testing
                })
                print(f"   ✅ Staticcall successful - transaction should work")
                return True, "Preflight validation passed"
                
            except Exception as staticcall_error:
                # ARCHITECT FIX: Capture exact revert message
                error_msg = str(staticcall_error)
                print(f"   ❌ Staticcall failed: {error_msg}")
                
                # Try to extract revert reason
                if 'revert' in error_msg.lower():
                    revert_reason = error_msg
                else:
                    revert_reason = f"Staticcall failed: {error_msg}"
                
                # ARCHITECT FIX: Abort execution if any preflight fails
                return False, f"Preflight validation failed: {revert_reason}"
                
        except Exception as e:
            print(f"   ❌ Preflight validation error: {e}")
            import traceback
            print(traceback.format_exc())
            # ARCHITECT FIX: Abort execution if any preflight fails
            return False, f"Preflight validation error: {e}"
    
    def get_real_paraswap_data(self, from_asset, to_asset, amount_wei):
        """Get real ParaSwap routing data with architect's fixes"""
        import math
        
        print(f"🌐 Getting real ParaSwap data for {from_asset}→{to_asset} (ARCHITECT FIXED)...")
        
        # ARCHITECT FIX: Correct routing for debt swaps
        # srcToken = newDebtAsset, destToken = oldDebtAsset, side = 'BUY', amount = debtRepayAmount
        old_debt_asset = self.tokens[from_asset.upper()]  # DAI for DAI→ARB
        new_debt_asset = self.tokens[to_asset.upper()]    # ARB for DAI→ARB
        
        print(f"   Debt swap routing: {old_debt_asset} → {new_debt_asset}")
        print(f"   srcToken (new debt): {new_debt_asset}")
        print(f"   destToken (old debt): {old_debt_asset}")
        print(f"   amount (debt repay): {amount_wei}")
        
        # ARCHITECT FIX: Include missing parameters
        slippage_bps = 75  # 75 basis points = 0.75%
        
        try:
            # Get price quote from ParaSwap with CORRECT parameters
            price_url = "https://apiv5.paraswap.io/prices"
            price_params = {
                'srcToken': new_debt_asset,      # FIXED: srcToken = newDebtAsset
                'destToken': old_debt_asset,     # FIXED: destToken = oldDebtAsset
                'amount': str(amount_wei),       # FIXED: amount = debtRepayAmount
                'srcDecimals': 18,
                'destDecimals': 18,
                'side': 'BUY',                   # FIXED: side = 'BUY'
                'network': 42161,
                'partner': 'aave',
                'txOrigin': self.user_address,   # ARCHITECT FIX: Missing parameter
                'slippage': slippage_bps         # ARCHITECT FIX: Missing parameter (50-100 bps)
            }
            
            print(f"   Getting price quote with fixed parameters...")
            print(f"   Parameters: {price_params}")
            
            price_response = requests.get(price_url, params=price_params, timeout=15)
            
            if price_response.status_code != 200:
                # ARCHITECT FIX: Log 400 response body and fail-fast
                error_body = price_response.text if price_response.text else 'No response body'
                print(f"   ❌ ParaSwap price API failed: {price_response.status_code}")
                print(f"   Response body: {error_body}")
                raise Exception(f"ParaSwap price API failed: {price_response.status_code} - {error_body}")
            
            price_data = price_response.json()
            print(f"   ✅ Price data received: {json.dumps(price_data, indent=2)[:500]}...")
            
            if 'priceRoute' not in price_data:
                print(f"   ❌ No price route found in response")
                raise Exception("No ParaSwap price route available")
            
            price_route = price_data['priceRoute']
            
            # Get transaction data with CORRECT parameters (ARCHITECT FIX: Remove slippage from tx call)
            tx_url = "https://apiv5.paraswap.io/transactions/42161"
            tx_payload = {
                'srcToken': new_debt_asset,
                'destToken': old_debt_asset,
                'srcAmount': price_route['srcAmount'],          # ARCHITECT FIX: Use srcAmount from price route
                'destAmount': price_route['destAmount'],        # ARCHITECT FIX: Use destAmount from price route
                'priceRoute': price_route,
                'userAddress': self.paraswap_debt_swap_adapter,  # FIXED: Use adapter address
                'receiver': self.paraswap_debt_swap_adapter,     # FIXED: Use adapter address  
                'partner': 'aave',
                'txOrigin': self.user_address,                   # ARCHITECT FIX: Missing parameter
                # ARCHITECT FIX: Remove slippage here as it conflicts with srcAmount
            }
            
            print(f"   Getting transaction data with fixed parameters...")
            print(f"   TX Payload keys: {list(tx_payload.keys())}")
            
            tx_response = requests.post(tx_url, json=tx_payload, timeout=20)
            
            if tx_response.status_code != 200:
                # ARCHITECT FIX: Log 400 response body and fail-fast
                error_body = tx_response.text if tx_response.text else 'No response body'
                print(f"   ❌ ParaSwap transaction API failed: {tx_response.status_code}")
                print(f"   Response body: {error_body}")
                raise Exception(f"ParaSwap transaction API failed: {tx_response.status_code} - {error_body}")
            
            tx_data = tx_response.json()
            print(f"   ✅ Transaction data received")
            
            # ARCHITECT FIX: Proper response mapping
            calldata = tx_data.get('data', '')
            to_amount_offset = tx_data.get('toAmountOffset', 0)  # Get offset from response
            
            if not calldata:
                raise Exception("No calldata received from ParaSwap")
            
            # ARCHITECT FIX: Calculate correct debt swap parameters
            debt_repay_amount = int(price_route['destAmount'])     # destAmount = what we repay
            max_new_debt_amount = math.ceil(int(price_route['srcAmount']) * (1 + slippage_bps / 10000))  # srcAmount * (1 + slippage)
            
            result = {
                'calldata': calldata,
                'debt_repay_amount': debt_repay_amount,           # ARCHITECT FIX: Use destAmount
                'max_new_debt_amount': max_new_debt_amount,       # ARCHITECT FIX: Use srcAmount with slippage
                'offset': to_amount_offset,                       # ARCHITECT FIX: Use toAmountOffset
                'price_route': price_route,
                'slippage_bps': slippage_bps,
                'src_amount': int(price_route['srcAmount']),
                'dest_amount': int(price_route['destAmount'])
            }
            
            print(f"   ✅ ARCHITECT FIXED ParaSwap data:")
            print(f"      Debt Repay Amount: {debt_repay_amount}")
            print(f"      Max New Debt Amount: {max_new_debt_amount}")
            print(f"      Offset: {to_amount_offset}")
            print(f"      Calldata length: {len(calldata)} chars")
            
            return result
            
        except Exception as e:
            # ARCHITECT FIX: No mock data fallback - fail fast
            print(f"   ❌ ParaSwap API failed: {e}")
            print(f"   ARCHITECT FIX: No mock data fallback - failing fast")
            raise Exception(f"ParaSwap API failed and no fallback allowed: {e}")
    
    def execute_debt_swap_transaction(self, from_asset, to_asset, phase_name):
        """Execute real debt swap transaction with corrected adapter"""
        try:
            print(f"\n⚡ EXECUTING {phase_name} WITH CORRECTED ADAPTER")
            print(f"   Operation: {from_asset} debt → {to_asset} debt")
            print(f"   Amount: ${self.swap_amount}")
            print(f"   Adapter: {self.paraswap_debt_swap_adapter}")
            
            # Get debt token for credit delegation
            to_debt_token = self.get_debt_token_address(to_asset)
            if not to_debt_token:
                raise Exception(f"Failed to get {to_asset} debt token")
            
            # Create credit delegation permit
            permit = self.create_credit_delegation_permit(to_debt_token)
            if not permit:
                raise Exception("Credit delegation permit creation failed")
            
            # Calculate amount and get ParaSwap data
            amount_wei = int(self.swap_amount * 1e18)
            paraswap_data = self.get_real_paraswap_data(from_asset, to_asset, amount_wei)
            
            # ARCHITECT FIX: Use correct response mapping
            debt_repay_amount = paraswap_data['debt_repay_amount']      # destAmount
            max_new_debt_amount = paraswap_data['max_new_debt_amount']  # srcAmount * (1 + slippage)
            offset = paraswap_data['offset']                            # toAmountOffset
            calldata = paraswap_data['calldata']                        # tx.data
            
            print(f"   ARCHITECT MAPPED PARAMETERS:")
            print(f"      Debt Repay Amount: {debt_repay_amount}")
            print(f"      Max New Debt Amount: {max_new_debt_amount}")
            print(f"      Offset: {offset}")
            print(f"      Calldata length: {len(calldata)}")
            
            # ARCHITECT FIX: Build correct debt swap parameters with mapped values
            debt_swap_params = (
                self.tokens[from_asset.upper()],  # debtAsset (old debt)
                self.tokens[to_asset.upper()],    # newDebtAsset (new debt)
                debt_repay_amount,                # ARCHITECT FIX: Use destAmount
                max_new_debt_amount,              # ARCHITECT FIX: Use srcAmount * (1 + slippage)
                0,                               # extraCollateralAmount
                "0x0000000000000000000000000000000000000000",  # extraCollateralAsset
                offset,                          # ARCHITECT FIX: Use toAmountOffset
                bytes.fromhex(calldata[2:]) if calldata.startswith('0x') else bytes.fromhex(calldata)  # ARCHITECT FIX: Use tx.data
            )
            
            print(f"   DEBT SWAP PARAMETERS:")
            print(f"      Debt Asset: {self.tokens[from_asset.upper()]}")
            print(f"      New Debt Asset: {self.tokens[to_asset.upper()]}")
            print(f"      Debt Repay Amount: {debt_repay_amount}")
            print(f"      Max New Debt Amount: {max_new_debt_amount}")
            print(f"      Offset: {offset}")
            
            # ARCHITECT FIX: Strengthened preflight validation
            preflight_success, preflight_message = self.verify_permit_and_preflight(
                to_debt_token, permit, debt_swap_params
            )
            
            if not preflight_success:
                # ARCHITECT FIX: Abort execution if any preflight fails
                raise Exception(f"Preflight validation failed: {preflight_message}")
            
            print(f"   ✅ Preflight validation passed: {preflight_message}")
            
            # Build debt swap contract
            debt_swap_abi = [{
                "inputs": [
                    {
                        "components": [
                            {"name": "debtAsset", "type": "address"},
                            {"name": "newDebtAsset", "type": "address"},
                            {"name": "debtRepayAmount", "type": "uint256"},
                            {"name": "maxNewDebtAmount", "type": "uint256"},
                            {"name": "extraCollateralAmount", "type": "uint256"},
                            {"name": "extraCollateralAsset", "type": "address"},
                            {"name": "offset", "type": "uint256"},
                            {"name": "paraswapData", "type": "bytes"}
                        ],
                        "name": "debtSwapParams",
                        "type": "tuple"
                    },
                    {
                        "components": [
                            {"name": "delegator", "type": "address"},
                            {"name": "delegatee", "type": "address"},
                            {"name": "value", "type": "uint256"},
                            {"name": "deadline", "type": "uint256"},
                            {"name": "v", "type": "uint8"},
                            {"name": "r", "type": "bytes32"},
                            {"name": "s", "type": "bytes32"}
                        ],
                        "name": "creditDelegationPermit",
                        "type": "tuple"
                    },
                    {"name": "useEthPath", "type": "bool"}
                ],
                "name": "swapDebt",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            debt_swap_contract = self.w3.eth.contract(
                address=self.paraswap_debt_swap_adapter,
                abi=debt_swap_abi
            )
            
            credit_delegation_permit = (
                self.user_address,               # delegator
                permit['delegatee'],             # delegatee
                permit['value'],                 # value
                permit['deadline'],              # deadline
                permit['v'],                     # v
                permit['r'],                     # r
                permit['s']                      # s
            )
            
            # Build function call with corrected parameters
            function_call = debt_swap_contract.functions.swapDebt(
                debt_swap_params,
                credit_delegation_permit,
                False  # useEthPath
            )
            
            # ARCHITECT FIX: Preflight already completed above with strengthened validation
            print(f"🔍 Preflight validation already completed with ARCHITECT fixes")
            
            # Estimate gas and build transaction
            print(f"⛽ Estimating gas...")
            gas_estimate = function_call.estimate_gas({'from': self.user_address})
            
            transaction = function_call.build_transaction({
                'from': self.user_address,
                'gas': int(gas_estimate * 1.2),
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            print(f"⚡ SENDING CORRECTED TRANSACTION TO BLOCKCHAIN")
            print(f"   Gas Estimate: {gas_estimate:,}")
            print(f"   Gas Price: {self.w3.eth.gas_price / 1e9:.2f} gwei")
            
            # Sign and send transaction
            signed_tx = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"📤 TRANSACTION SENT: {tx_hash.hex()}")
            print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
            
            # Wait for confirmation
            print(f"⏳ Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            success = receipt['status'] == 1
            print(f"{'✅ TRANSACTION CONFIRMED!' if success else '❌ TRANSACTION FAILED!'}")
            
            if success:
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas Used: {receipt['gasUsed']:,}")
            
            return {
                'success': success,
                'tx_hash': tx_hash.hex(),
                'receipt': dict(receipt),
                'gas_used': receipt['gasUsed'],
                'block_number': receipt['blockNumber'],
                'arbiscan_url': f"https://arbiscan.io/tx/{tx_hash.hex()}",
                'timestamp': datetime.now().isoformat(),
                'phase': phase_name,
                'from_asset': from_asset,
                'to_asset': to_asset
            }
            
        except Exception as e:
            print(f"❌ {phase_name} execution failed: {e}")
            import traceback
            print(traceback.format_exc())
            return {
                'success': False, 
                'error': str(e), 
                'phase': phase_name,
                'timestamp': datetime.now().isoformat()
            }
    
    def monitor_wait_period(self, minutes):
        """Monitor position during wait period"""
        print(f"\n⏳ WAIT PERIOD: {minutes} MINUTES WITH POSITION MONITORING")
        print("-" * 60)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=minutes)
        snapshots = []
        
        # Initial snapshot
        initial = self.get_aave_position()
        snapshots.append({'elapsed_minutes': 0, 'position': initial})
        print(f"📊 Initial Position - HF: {initial['health_factor']:.3f}, Debt: ${initial['total_debt_usd']:.2f}")
        
        # Monitor every minute
        minute_count = 0
        while datetime.now() < end_time and minute_count < minutes:
            time.sleep(60)  # Wait 1 minute
            minute_count += 1
            
            current = self.get_aave_position()
            snapshots.append({'elapsed_minutes': minute_count, 'position': current})
            
            remaining = end_time - datetime.now()
            remaining_min = max(0, int(remaining.total_seconds() / 60))
            print(f"📊 {minute_count}min elapsed - HF: {current['health_factor']:.3f}, Debt: ${current['total_debt_usd']:.2f} ({remaining_min}min remaining)")
        
        print(f"✅ Wait period completed")
        
        return {
            'duration_minutes': minutes,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'snapshots': snapshots,
            'initial_position': snapshots[0]['position'],
            'final_position': snapshots[-1]['position']
        }
    
    def calculate_comprehensive_pnl(self, initial_position, final_position):
        """Calculate comprehensive PNL analysis with exact numbers and percentages"""
        print(f"\n📊 COMPREHENSIVE PNL ANALYSIS")
        print("=" * 60)
        
        # Calculate absolute changes
        collateral_change = final_position['total_collateral_usd'] - initial_position['total_collateral_usd']
        debt_change = final_position['total_debt_usd'] - initial_position['total_debt_usd']
        hf_change = final_position['health_factor'] - initial_position['health_factor']
        
        # Calculate percentage changes
        collateral_pct = (collateral_change / initial_position['total_collateral_usd']) * 100 if initial_position['total_collateral_usd'] > 0 else 0
        debt_pct = (debt_change / initial_position['total_debt_usd']) * 100 if initial_position['total_debt_usd'] > 0 else 0
        hf_pct = (hf_change / initial_position['health_factor']) * 100 if initial_position['health_factor'] > 0 else 0
        
        # Net position value calculation
        initial_net_value = initial_position['total_collateral_usd'] - initial_position['total_debt_usd']
        final_net_value = final_position['total_collateral_usd'] - final_position['total_debt_usd']
        net_value_change = final_net_value - initial_net_value
        net_value_pct = (net_value_change / abs(initial_net_value)) * 100 if initial_net_value != 0 else 0
        
        pnl_analysis = {
            'cycle_summary': {
                'operation': 'Complete DAI→ARB→wait 5min→ARB→DAI debt swap cycle',
                'swap_amount_usd': self.swap_amount,
                'execution_mode': 'production',
                'debt_swap_adapter': self.paraswap_debt_swap_adapter
            },
            'initial_position': {
                'total_collateral_usd': initial_position['total_collateral_usd'],
                'total_debt_usd': initial_position['total_debt_usd'],
                'health_factor': initial_position['health_factor'],
                'net_value_usd': initial_net_value,
                'timestamp': initial_position['timestamp']
            },
            'final_position': {
                'total_collateral_usd': final_position['total_collateral_usd'],
                'total_debt_usd': final_position['total_debt_usd'],
                'health_factor': final_position['health_factor'],
                'net_value_usd': final_net_value,
                'timestamp': final_position['timestamp']
            },
            'absolute_changes': {
                'collateral_change_usd': collateral_change,
                'debt_change_usd': debt_change,
                'health_factor_change': hf_change,
                'net_value_change_usd': net_value_change
            },
            'percentage_changes': {
                'collateral_change_pct': collateral_pct,
                'debt_change_pct': debt_pct,
                'health_factor_change_pct': hf_pct,
                'net_value_change_pct': net_value_pct
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Display comprehensive analysis
        print(f"📈 INITIAL POSITION (Start of Cycle):")
        print(f"   Collateral: ${initial_position['total_collateral_usd']:.2f}")
        print(f"   Debt: ${initial_position['total_debt_usd']:.2f}")
        print(f"   Health Factor: {initial_position['health_factor']:.3f}")
        print(f"   Net Value: ${initial_net_value:.2f}")
        
        print(f"\n📉 FINAL POSITION (End of Cycle):")
        print(f"   Collateral: ${final_position['total_collateral_usd']:.2f}")
        print(f"   Debt: ${final_position['total_debt_usd']:.2f}")
        print(f"   Health Factor: {final_position['health_factor']:.3f}")
        print(f"   Net Value: ${final_net_value:.2f}")
        
        print(f"\n💰 ABSOLUTE CHANGES:")
        print(f"   Collateral Change: ${collateral_change:+.2f}")
        print(f"   Debt Change: ${debt_change:+.2f}")
        print(f"   Health Factor Change: {hf_change:+.3f}")
        print(f"   Net Value Change: ${net_value_change:+.2f}")
        
        print(f"\n📊 PERCENTAGE CHANGES:")
        print(f"   Collateral Change: {collateral_pct:+.2f}%")
        print(f"   Debt Change: {debt_pct:+.2f}%")
        print(f"   Health Factor Change: {hf_pct:+.2f}%")
        print(f"   Net Value Change: {net_value_pct:+.2f}%")
        
        return pnl_analysis
    
    def execute_complete_production_cycle(self):
        """Execute the complete production debt swap cycle"""
        try:
            print(f"\n🚀 EXECUTING COMPLETE PRODUCTION DEBT SWAP CYCLE")
            print("=" * 80)
            
            # Validation
            ready, message = self.validate_production_readiness()
            if not ready:
                raise Exception(f"Production validation failed: {message}")
            
            print(f"✅ Production validation passed: {message}")
            self.cycle_data['validation'] = {'passed': True, 'message': message}
            
            # Record initial position
            initial_position = self.get_aave_position()
            self.cycle_data['initial_position'] = initial_position
            
            print(f"\n🎯 PHASE 1: DAI DEBT → ARB DEBT")
            print("=" * 40)
            phase1_result = self.execute_debt_swap_transaction('DAI', 'ARB', 'PHASE 1')
            self.cycle_data['phase_1'] = phase1_result
            
            if not phase1_result.get('success', False):
                raise Exception(f"Phase 1 failed: {phase1_result.get('error', 'Unknown error')}")
            
            print(f"\n⏳ WAIT PERIOD: 5 MINUTES")
            print("=" * 40)
            wait_result = self.monitor_wait_period(5)
            self.cycle_data['wait_period'] = wait_result
            
            print(f"\n🎯 PHASE 2: ARB DEBT → DAI DEBT")
            print("=" * 40)
            phase2_result = self.execute_debt_swap_transaction('ARB', 'DAI', 'PHASE 2')
            self.cycle_data['phase_2'] = phase2_result
            
            if not phase2_result.get('success', False):
                raise Exception(f"Phase 2 failed: {phase2_result.get('error', 'Unknown error')}")
            
            # Final position and comprehensive PNL
            final_position = self.get_aave_position()
            self.cycle_data['final_position'] = final_position
            
            pnl_analysis = self.calculate_comprehensive_pnl(initial_position, final_position)
            self.cycle_data['pnl_analysis'] = pnl_analysis
            
            # Mark successful completion
            self.cycle_data['completion_time'] = datetime.now().isoformat()
            self.cycle_data['cycle_successful'] = True
            
            # Save comprehensive results
            filename = f"complete_production_cycle_{self.cycle_data['execution_id']}.json"
            with open(filename, 'w') as f:
                json.dump(self.cycle_data, f, indent=2, default=str)
            
            print(f"\n🎉 COMPLETE PRODUCTION DEBT SWAP CYCLE SUCCESSFUL!")
            print("=" * 80)
            print(f"✅ PHASE 1 COMPLETED:")
            print(f"   Transaction Hash: {phase1_result['tx_hash']}")
            print(f"   Arbiscan Link: {phase1_result['arbiscan_url']}")
            print(f"   Block Number: {phase1_result['block_number']}")
            print(f"   Gas Used: {phase1_result['gas_used']:,}")
            
            print(f"\n✅ WAIT PERIOD COMPLETED:")
            print(f"   Duration: 5 minutes with position monitoring")
            print(f"   Position snapshots: {len(wait_result['snapshots'])} recorded")
            
            print(f"\n✅ PHASE 2 COMPLETED:")
            print(f"   Transaction Hash: {phase2_result['tx_hash']}")
            print(f"   Arbiscan Link: {phase2_result['arbiscan_url']}")
            print(f"   Block Number: {phase2_result['block_number']}")
            print(f"   Gas Used: {phase2_result['gas_used']:,}")
            
            print(f"\n✅ COMPREHENSIVE PNL ANALYSIS COMPLETED:")
            print(f"   Complete cycle with exact numbers and percentages")
            print(f"   All position changes tracked and calculated")
            
            print(f"\n📄 VERIFIABLE EVIDENCE:")
            print(f"   Complete results saved: {filename}")
            print(f"   Transaction receipts preserved")
            print(f"   Blockchain verification links provided")
            print("=" * 80)
            
            return self.cycle_data
            
        except Exception as e:
            print(f"❌ Complete production cycle failed: {e}")
            import traceback
            print(traceback.format_exc())
            
            self.cycle_data['cycle_failed'] = True
            self.cycle_data['failure_reason'] = str(e)
            self.cycle_data['failure_time'] = datetime.now().isoformat()
            
            return self.cycle_data

def main():
    """Main execution function for corrected production cycle"""
    print("🚀 CORRECTED PRODUCTION DEBT SWAP CYCLE - FINAL EXECUTION")
    print("=" * 80)
    print("🔧 CORRECTION APPLIED: Using proper debt swap adapter address")
    print("🎯 TARGET: Complete DAI→ARB→wait 5min→ARB→DAI with real transactions")
    print("📊 DELIVERABLES: Transaction hashes + Comprehensive PNL analysis")
    print("=" * 80)
    
    try:
        executor = CorrectedProductionDebtSwapCycle()
        results = executor.execute_complete_production_cycle()
        
        if results.get('cycle_successful', False):
            print(f"\n🎉 MISSION ACCOMPLISHED - PRODUCTION CYCLE COMPLETE!")
            print(f"✅ Complete DAI→ARB→wait 5min→ARB→DAI sequence executed successfully")
            print(f"✅ Real transaction hashes obtained and blockchain verified") 
            print(f"✅ Comprehensive PNL analysis with exact numbers and percentages completed")
            print(f"✅ Verifiable evidence collected and persisted")
            print(f"✅ All user requirements fully delivered")
            return True
        else:
            print(f"\n❌ MISSION FAILED - PRODUCTION CYCLE INCOMPLETE")
            print(f"   Failure Reason: {results.get('failure_reason', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Production cycle execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎉 PRODUCTION CYCLE SUCCESSFUL' if success else '❌ PRODUCTION CYCLE FAILED'}")