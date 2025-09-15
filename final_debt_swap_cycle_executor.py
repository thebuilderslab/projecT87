#!/usr/bin/env python3
"""
Final Debt Swap Cycle Executor - Complete Implementation
Fixed ParaSwap API issue + Comprehensive PNL Tracking + Full Cycle Execution
DAI debt → ARB debt → wait 5 minutes → ARB debt → DAI debt
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
from eth_account.messages import encode_typed_data

# Set high precision for PNL calculations
getcontext().prec = 50

class DebtPosition:
    """Track debt position with detailed metrics"""
    def __init__(self, timestamp: str, dai_debt: float, arb_debt: float, 
                 dai_price: float, arb_price: float):
        self.timestamp = timestamp
        self.dai_debt = float(dai_debt)
        self.arb_debt = float(arb_debt)
        self.dai_price = float(dai_price)
        self.arb_price = float(arb_price)
        self.total_debt_usd = (self.dai_debt * self.dai_price) + (self.arb_debt * self.arb_price)

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'dai_debt': self.dai_debt,
            'arb_debt': self.arb_debt,
            'dai_price': self.dai_price,
            'arb_price': self.arb_price,
            'total_debt_usd': self.total_debt_usd
        }

class ComprehensivePNLTracker:
    """Comprehensive PNL tracking for debt swap cycles"""
    
    def __init__(self, agent):
        self.agent = agent
        self.positions: List[DebtPosition] = []
        self.swap_events = []
        
        # Contract addresses
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        self.token_addresses = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        print(f"📊 Comprehensive PNL Tracker initialized")

    def get_current_prices(self) -> Dict[str, float]:
        """Get current token prices"""
        try:
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            if not api_key:
                return {'DAI': 1.00, 'ARB': 0.80}  # Fallback
            
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
                print(f"💰 Prices: DAI ${prices['DAI']:.4f}, ARB ${prices['ARB']:.4f}")
                return prices
            else:
                return {'DAI': 1.00, 'ARB': 0.80}
                
        except:
            return {'DAI': 1.00, 'ARB': 0.80}

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
            
            data_provider = self.agent.w3.eth.contract(address=self.aave_data_provider, abi=data_provider_abi)
            debt_balances = {}
            
            for symbol, token_address in self.token_addresses.items():
                addresses = data_provider.functions.getReserveTokensAddresses(token_address).call()
                variable_debt_token = addresses[2]
                
                debt_contract = self.agent.w3.eth.contract(address=variable_debt_token, abi=erc20_abi)
                balance_wei = debt_contract.functions.balanceOf(self.agent.address).call()
                balance = float(balance_wei) / 1e18
                
                debt_balances[symbol] = balance
                print(f"📋 {symbol} debt: {balance:.6f}")
            
            return debt_balances
            
        except Exception as e:
            print(f"❌ Error getting debt balances: {e}")
            return {'DAI': 0.0, 'ARB': 0.0}

    def capture_position(self, event_name: str) -> DebtPosition:
        """Capture current debt position"""
        print(f"\n📸 CAPTURING POSITION: {event_name}")
        print("=" * 50)
        
        prices = self.get_current_prices()
        debt_balances = self.get_debt_balances()
        
        position = DebtPosition(
            timestamp=datetime.now().isoformat(),
            dai_debt=debt_balances['DAI'],
            arb_debt=debt_balances['ARB'],
            dai_price=prices['DAI'],
            arb_price=prices['ARB']
        )
        
        self.positions.append(position)
        
        print(f"📊 POSITION CAPTURED:")
        print(f"   DAI Debt: {position.dai_debt:.6f} DAI (${position.dai_debt * position.dai_price:.2f})")
        print(f"   ARB Debt: {position.arb_debt:.6f} ARB (${position.arb_debt * position.arb_price:.2f})")
        print(f"   Total USD: ${position.total_debt_usd:.2f}")
        print("=" * 50)
        
        return position

    def calculate_pnl(self, pos1: DebtPosition, pos2: DebtPosition) -> Dict:
        """Calculate detailed PNL between positions"""
        dai_debt_change = pos2.dai_debt - pos1.dai_debt
        dai_usd_change = dai_debt_change * pos2.dai_price
        
        arb_debt_change = pos2.arb_debt - pos1.arb_debt
        arb_usd_change = arb_debt_change * pos2.arb_price
        
        total_debt_change_usd = pos2.total_debt_usd - pos1.total_debt_usd
        
        # Percentage changes
        dai_percentage = ((pos2.dai_debt / pos1.dai_debt) - 1) * 100 if pos1.dai_debt > 0 else 0
        arb_percentage = ((pos2.arb_debt / pos1.arb_debt) - 1) * 100 if pos1.arb_debt > 0 else 0
        total_percentage = ((pos2.total_debt_usd / pos1.total_debt_usd) - 1) * 100 if pos1.total_debt_usd > 0 else 0
        
        # Time difference
        dt1 = datetime.fromisoformat(pos1.timestamp.replace('Z', '+00:00'))
        dt2 = datetime.fromisoformat(pos2.timestamp.replace('Z', '+00:00'))
        time_diff_minutes = (dt2 - dt1).total_seconds() / 60
        
        return {
            'dai_debt_change': dai_debt_change,
            'dai_usd_change': dai_usd_change,
            'dai_percentage': dai_percentage,
            'arb_debt_change': arb_debt_change,
            'arb_usd_change': arb_usd_change,
            'arb_percentage': arb_percentage,
            'total_debt_change_usd': total_debt_change_usd,
            'total_percentage': total_percentage,
            'timespan_minutes': time_diff_minutes
        }

    def print_pnl_analysis(self, pnl: Dict, title: str):
        """Print detailed PNL analysis"""
        print(f"\n💹 {title}")
        print("=" * 60)
        print(f"📊 DEBT CHANGES:")
        print(f"   DAI: {pnl['dai_debt_change']:+.6f} DAI (${pnl['dai_usd_change']:+.2f}) [{pnl['dai_percentage']:+.2f}%]")
        print(f"   ARB: {pnl['arb_debt_change']:+.6f} ARB (${pnl['arb_usd_change']:+.2f}) [{pnl['arb_percentage']:+.2f}%]")
        print(f"💰 TOTAL USD CHANGE: ${pnl['total_debt_change_usd']:+.2f} [{pnl['total_percentage']:+.2f}%]")
        print(f"⏱️  TIMESPAN: {pnl['timespan_minutes']:.1f} minutes")
        print("=" * 60)

class FinalDebtSwapExecutor:
    """Final debt swap executor with fixed ParaSwap integration"""
    
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
        
        print(f"🔧 Final Debt Swap Executor initialized")

    def get_fixed_paraswap_calldata(self, from_asset: str, to_asset: str, amount_usd: float) -> Dict:
        """Get ParaSwap calldata with FIXED API parameters"""
        try:
            print(f"\n🌐 FIXED PARASWAP INTEGRATION")
            print("=" * 50)
            
            # Debt swap reverse routing
            if from_asset.upper() == 'DAI' and to_asset.upper() == 'ARB':
                src_token = self.tokens['ARB']
                dest_token = self.tokens['DAI']
                print(f"🔄 Reverse routing: ARB → DAI (for DAI debt → ARB debt)")
            else:
                src_token = self.tokens['DAI']
                dest_token = self.tokens['ARB']
                print(f"🔄 Reverse routing: DAI → ARB (for ARB debt → DAI debt)")
            
            amount_wei = int(amount_usd * 1e18)
            
            # Get ParaSwap price
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
            price_response = requests.get(price_url, params=price_params, timeout=15)
            
            if price_response.status_code != 200:
                raise Exception(f"Price API error: {price_response.status_code}")
            
            price_data = price_response.json()
            if 'priceRoute' not in price_data:
                raise Exception("No price route found")
            
            price_route = price_data['priceRoute']
            print(f"✅ Price route: {int(price_route['srcAmount']) / 1e18:.6f} → {int(price_route['destAmount']) / 1e18:.6f}")
            
            # FIXED: Transaction payload without deprecated parameter
            tx_url = "https://apiv5.paraswap.io/transactions/42161"
            tx_params = {
                'deadline': str(int(time.time()) + 1800),
                'ignoreChecks': 'true'
            }
            
            # CRITICAL FIX: Remove deprecated 'positiveSlippageToUser' parameter
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
                'takeSurplus': False  # Keep this one, remove positiveSlippageToUser
                # 'positiveSlippageToUser': False  # REMOVED - this was causing the error
            }
            
            print(f"📡 ParaSwap transaction API (FIXED)...")
            tx_response = requests.post(tx_url, params=tx_params, json=tx_payload, timeout=20)
            
            if tx_response.status_code != 200:
                error_detail = tx_response.text[:200]
                raise Exception(f"Transaction API error {tx_response.status_code}: {error_detail}")
            
            tx_data = tx_response.json()
            if 'data' not in tx_data:
                raise Exception("No transaction data in response")
            
            result = {
                'calldata': tx_data['data'],
                'expected_amount': price_route['destAmount'],
                'src_amount': price_route['srcAmount']
            }
            
            print(f"✅ FIXED PARASWAP SUCCESS!")
            print(f"   Calldata: {len(result['calldata'])} chars")
            print(f"   Expected: {int(result['expected_amount']) / 1e18:.6f}")
            print("=" * 50)
            
            return result
            
        except Exception as e:
            print(f"❌ ParaSwap integration failed: {e}")
            return {}

    def get_debt_token_address(self, asset_symbol: str) -> str:
        """Get debt token address"""
        try:
            asset_address = self.tokens[asset_symbol.upper()]
            
            abi = [{
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
            
            contract = self.w3.eth.contract(address=self.aave_data_provider, abi=abi)
            addresses = contract.functions.getReserveTokensAddresses(asset_address).call()
            return addresses[2]  # Variable debt token
            
        except Exception as e:
            print(f"❌ Error getting debt token: {e}")
            return ""

    def create_credit_delegation_permit(self, private_key: str, debt_token_address: str) -> Dict:
        """Create credit delegation permit"""
        try:
            user_account = self.w3.eth.account.from_key(private_key)
            
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
            deadline = int(time.time()) + 3600
            
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
            
            message = {
                'delegatee': self.paraswap_debt_swap_adapter,
                'value': 2**256 - 1,
                'nonce': nonce,
                'deadline': deadline
            }
            
            # FIXED: Use correct encode_typed_data format (newer library version)
            full_message = {
                'types': types,
                'primaryType': 'DelegationWithSig',
                'domain': domain,
                'message': message
            }
            encoded_data = encode_typed_data(full_message)
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

    def execute_single_debt_swap(self, private_key: str, from_asset: str, to_asset: str, amount_usd: float) -> Dict:
        """Execute single debt swap with fixed integration"""
        result = {
            'operation': f'{from_asset}_to_{to_asset}_debt_swap',
            'start_time': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            print(f"\n🚀 EXECUTING: {from_asset} debt → {to_asset} debt (${amount_usd:.2f})")
            print("=" * 60)
            
            # Get components
            debt_token = self.get_debt_token_address(to_asset)
            paraswap_data = self.get_fixed_paraswap_calldata(from_asset, to_asset, amount_usd)
            credit_permit = self.create_credit_delegation_permit(private_key, debt_token)
            
            if not all([debt_token, paraswap_data, credit_permit]):
                raise Exception("Failed to generate required components")
            
            # Build contract call
            contract = self.w3.eth.contract(address=self.paraswap_debt_swap_adapter, abi=self.debt_swap_abi)
            amount_to_swap = int(paraswap_data['expected_amount'])
            
            function_call = contract.functions.swapDebt(
                self.tokens[from_asset.upper()],
                self.tokens[to_asset.upper()],
                amount_to_swap,
                bytes.fromhex(paraswap_data['calldata'][2:]),
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
            
            # Gas estimation
            try:
                gas_estimate = function_call.estimate_gas({'from': self.user_address})
                gas_limit = int(gas_estimate * 1.3)
                print(f"✅ Gas estimated: {gas_estimate:,}")
            except:
                gas_limit = 1000000
                print(f"⚠️ Gas estimation failed, using {gas_limit:,}")
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.user_address,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            # Preflight test
            print(f"🔍 Preflight test...")
            try:
                self.w3.eth.call(transaction, 'latest')
                print(f"✅ Preflight passed")
            except Exception as call_error:
                raise Exception(f"Preflight failed: {call_error}")
            
            # Execute transaction
            print(f"🚀 Executing on-chain...")
            user_account = self.w3.eth.account.from_key(private_key)
            signed_tx = user_account.sign_transaction(transaction)
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"✅ Transaction sent: {tx_hash_hex}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                print(f"✅ CONFIRMED! Block: {receipt['blockNumber']}, Gas: {receipt['gasUsed']:,}")
                print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
                
                result['success'] = True
                result['tx_hash'] = tx_hash_hex
                result['block_number'] = receipt['blockNumber']
                result['gas_used'] = receipt['gasUsed']
            else:
                raise Exception("Transaction reverted")
            
            return result
            
        except Exception as e:
            print(f"❌ Debt swap failed: {e}")
            result['error'] = str(e)
            return result
        
        finally:
            result['end_time'] = datetime.now().isoformat()

class CompleteDebtSwapCycle:
    """Complete debt swap cycle executor with comprehensive PNL tracking"""
    
    def __init__(self, agent):
        self.agent = agent
        self.executor = FinalDebtSwapExecutor(agent)
        self.pnl_tracker = ComprehensivePNLTracker(agent)
        
        print(f"🎯 Complete Debt Swap Cycle initialized")
        print(f"   Cycle: DAI debt → ARB debt → wait 5 min → ARB debt → DAI debt")

    def execute_complete_cycle(self, private_key: str, swap_amount_usd: float = 5.0, wait_minutes: int = 5) -> Dict:
        """Execute complete debt swap cycle with comprehensive tracking"""
        
        cycle_result = {
            'cycle_name': 'complete_debt_swap_cycle',
            'start_time': datetime.now().isoformat(),
            'swap_amount_usd': swap_amount_usd,
            'wait_minutes': wait_minutes,
            'phases': {},
            'pnl_analysis': {},
            'overall_success': False
        }
        
        try:
            print(f"\n🎯 COMPLETE DEBT SWAP CYCLE EXECUTION")
            print("=" * 80)
            print(f"Cycle: DAI debt → ARB debt → wait {wait_minutes} min → ARB debt → DAI debt")
            print(f"Amount: ${swap_amount_usd:.2f} per swap")
            print(f"Real execution: ENABLED")
            print("=" * 80)
            
            # INITIAL POSITION
            initial_position = self.pnl_tracker.capture_position("CYCLE_START")
            
            # PHASE 1: DAI debt → ARB debt
            print(f"\n🚀 PHASE 1: DAI DEBT → ARB DEBT")
            phase1_result = self.executor.execute_single_debt_swap(
                private_key, 'DAI', 'ARB', swap_amount_usd
            )
            
            cycle_result['phases']['phase_1'] = phase1_result
            
            if not phase1_result.get('success'):
                raise Exception(f"Phase 1 failed: {phase1_result.get('error')}")
            
            # Position after Phase 1
            post_phase1_position = self.pnl_tracker.capture_position("AFTER_PHASE_1")
            phase1_pnl = self.pnl_tracker.calculate_pnl(initial_position, post_phase1_position)
            self.pnl_tracker.print_pnl_analysis(phase1_pnl, "PHASE 1 PNL ANALYSIS")
            cycle_result['pnl_analysis']['phase_1'] = phase1_pnl
            
            # WAIT PERIOD
            print(f"\n⏳ WAIT PERIOD: {wait_minutes} MINUTES")
            print("-" * 50)
            
            wait_start = datetime.now()
            for minute in range(wait_minutes):
                remaining = wait_minutes - minute
                print(f"   ⏱️  {remaining} minutes remaining...")
                time.sleep(60)
            
            wait_end = datetime.now()
            actual_wait = (wait_end - wait_start).total_seconds() / 60
            
            print(f"✅ Wait completed: {actual_wait:.1f} minutes")
            
            # Position after wait
            post_wait_position = self.pnl_tracker.capture_position("AFTER_WAIT")
            wait_pnl = self.pnl_tracker.calculate_pnl(post_phase1_position, post_wait_position)
            self.pnl_tracker.print_pnl_analysis(wait_pnl, "WAIT PERIOD PNL (Price Impact)")
            cycle_result['pnl_analysis']['wait_period'] = wait_pnl
            
            # PHASE 2: ARB debt → DAI debt
            print(f"\n🚀 PHASE 2: ARB DEBT → DAI DEBT")
            phase2_result = self.executor.execute_single_debt_swap(
                private_key, 'ARB', 'DAI', swap_amount_usd
            )
            
            cycle_result['phases']['phase_2'] = phase2_result
            
            if not phase2_result.get('success'):
                raise Exception(f"Phase 2 failed: {phase2_result.get('error')}")
            
            # Final position
            final_position = self.pnl_tracker.capture_position("CYCLE_END")
            phase2_pnl = self.pnl_tracker.calculate_pnl(post_wait_position, final_position)
            self.pnl_tracker.print_pnl_analysis(phase2_pnl, "PHASE 2 PNL ANALYSIS")
            cycle_result['pnl_analysis']['phase_2'] = phase2_pnl
            
            # OVERALL CYCLE PNL
            overall_pnl = self.pnl_tracker.calculate_pnl(initial_position, final_position)
            self.pnl_tracker.print_pnl_analysis(overall_pnl, "OVERALL CYCLE PNL ANALYSIS")
            cycle_result['pnl_analysis']['overall_cycle'] = overall_pnl
            
            cycle_result['overall_success'] = True
            
            # SUCCESS SUMMARY
            print(f"\n🎉 COMPLETE DEBT SWAP CYCLE: SUCCESS!")
            print("=" * 80)
            print(f"✅ Phase 1: DAI → ARB debt swap executed ({phase1_result['tx_hash']})")
            print(f"✅ Wait Period: {actual_wait:.1f} minutes completed")
            print(f"✅ Phase 2: ARB → DAI debt swap executed ({phase2_result['tx_hash']})")
            print(f"✅ Comprehensive PNL tracking completed")
            print(f"💰 Overall P&L: ${overall_pnl['total_debt_change_usd']:+.2f} ({overall_pnl['total_percentage']:+.2f}%)")
            print("=" * 80)
            
            return cycle_result
            
        except Exception as e:
            print(f"\n❌ CYCLE FAILED: {e}")
            cycle_result['error'] = str(e)
            return cycle_result
        
        finally:
            cycle_result['end_time'] = datetime.now().isoformat()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"complete_debt_swap_cycle_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(cycle_result, f, indent=2, default=str)
            
            print(f"\n📁 Results saved: {filename}")

def main():
    """Execute complete debt swap cycle"""
    print("🎯 COMPLETE DEBT SWAP CYCLE EXECUTOR")
    print("=" * 80)
    print("Fixed ParaSwap API + Comprehensive PNL Tracking + Real Execution")
    print("=" * 80)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        agent = ArbitrumTestnetAgent()
        private_key = os.getenv('PRIVATE_KEY')
        
        if not agent or not private_key:
            raise Exception("Agent or private key initialization failed")
        
        # Execute complete cycle
        cycle_executor = CompleteDebtSwapCycle(agent)
        result = cycle_executor.execute_complete_cycle(
            private_key=private_key,
            swap_amount_usd=5.0,  # $5 per swap
            wait_minutes=5  # 5 minute wait
        )
        
        if result.get('overall_success'):
            print(f"\n🎉 MISSION ACCOMPLISHED!")
            print(f"✅ Complete debt swap cycle executed successfully")
            print(f"✅ All requirements fulfilled with comprehensive PNL tracking")
        else:
            print(f"\n❌ MISSION FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    main()