#!/usr/bin/env python3
"""
Enhanced Borrow Manager
Provides multiple mechanisms for reliable borrowing operations
"""

import time
import json
import os
from decimal import Decimal
from web3 import Web3

class EnhancedBorrowManager:
    def __init__(self, agent):
        self.agent = agent
        self.max_retries = 5
        self.retry_delay = 2

    def execute_enhanced_borrow_with_retry(self, amount_usd):
        """Execute enhanced borrow with comprehensive retry mechanisms"""
        # Default to USDC for borrowing
        token_address = self.agent.usdc_address
        return self.safe_borrow_with_fallbacks(amount_usd, token_address)

    def safe_borrow_with_fallbacks(self, amount_usd, token_address):
        """
        Execute borrowing with multiple fallback mechanisms and cooldown management
        """
        print(f"🏦 Enhanced Borrow Manager: Borrowing ${amount_usd:.2f}")

        # Enhanced input validation with override support
        if amount_usd <= 0:
            # Check if manual override is active and we can use fallback amount
            if hasattr(self.agent, 'detect_manual_override') and self.agent.detect_manual_override():
                print(f"🔧 Manual override active - calculating fallback borrow amount")
                try:
                    # Get available borrowing capacity
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

                    pool_contract = self.agent.w3.eth.contract(address=self.agent.aave_pool_address, abi=pool_abi)
                    account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
                    available_borrows_usd = account_data[2] / (10**8)

                    # Use the agent's calculation logic
                    amount_usd = self.calculate_safe_borrow_amount(0.0, available_borrows_usd)
                    print(f"🔧 Override borrow amount: ${amount_usd:.2f}")

                    if amount_usd <= 0:
                        print(f"❌ Even override calculation resulted in invalid amount: ${amount_usd}")
                        return None

                except Exception as e:
                    print(f"❌ Failed to calculate override amount: {e}")
                    return None
            else:
                print(f"⚠️ Invalid borrow amount: ${amount_usd}, operation cancelled")
                return None

        # Check cooldown first
        if hasattr(self.agent, 'is_operation_in_cooldown'):
            try:
                in_cooldown, remaining_time = self.agent.is_operation_in_cooldown('borrow')
                if in_cooldown:
                    print(f"⏰ Borrow operation in cooldown for {remaining_time:.0f}s")
                    return None
            except Exception as cooldown_error:
                print(f"⚠️ Cooldown check failed: {cooldown_error}, proceeding with operation")

        # Mechanism 1: Direct Aave integration
        result = self._try_direct_aave_borrow(amount_usd, token_address)
        if result:
            return self._record_success(result)

        # Mechanism 2: Alternative parameter order
        result = self._try_alternative_parameter_order(amount_usd, token_address)
        if result:
            return result

        # Mechanism 3: Step-by-step manual borrow
        result = self._try_manual_step_borrow(amount_usd, token_address)
        if result:
            return result

        # Mechanism 4: Contract direct call
        result = self._try_direct_contract_call(amount_usd, token_address)
        if result:
            return result

        # Mechanism 5: Aave API Fallback
        result = self._try_aave_api_fallback(amount_usd, token_address)
        if result:
            return result

        # Mechanism 6: Compound V3 Fallback (USDC only)
        if token_address.lower() == self.agent.usdc_address.lower():
            result = self._try_compound_fallback(amount_usd)
            if result:
                return result

        # Mechanism 7: DeFi Pulse API Integration
        result = self._try_defi_pulse_api(amount_usd, token_address)
        if result:
            return result

        print("❌ All borrowing mechanisms failed")
        return None

    def _record_success(self, result):
        """Record successful operation and return result"""
        if result and hasattr(self.agent, 'record_successful_operation'):
            self.agent.record_successful_operation('borrow')
        return result

    def _try_aave_api_fallback(self, amount_usd, token_address):
        """Try Aave API fallback mechanism"""
        try:
            print("🔄 Mechanism 5: Aave API fallback")
            from aave_api_fallback import AaveAPIFallback

            api_fallback = AaveAPIFallback(self.agent)
            result = api_fallback.execute_borrow_via_flashloan(amount_usd, token_address)

            if result:
                print(f"✅ Mechanism 5 success: {result}")
                return result

        except Exception as e:
            print(f"❌ Mechanism 5 failed: {e}")

        return None

    def _try_compound_fallback(self, amount_usd):
        """Try Compound V3 as fallback for USDC"""
        try:
            print("🔄 Mechanism 6: Compound V3 fallback")
            from compound_v3_integration import CompoundV3Fallback

            compound_fallback = CompoundV3Fallback(self.agent)
            result = compound_fallback.borrow_from_compound(amount_usd)

            if result:
                print(f"✅ Mechanism 6 success: {result}")
                return result

        except Exception as e:
            print(f"❌ Mechanism 6 failed: {e}")

        return None

    def _try_defi_pulse_api(self, amount_usd, token_address):
        """Try DeFi Pulse API for lending operations"""
        try:
            print("🔄 Mechanism 7: DeFi Pulse API")

            # Use DeFi Pulse API for borrow operations
            import requests

            # Get current lending rates
            response = requests.get(f"https://api.defipulse.com/v1/lending/rates")
            if response.status_code == 200:
                rates_data = response.json()

                # Find best borrowing rate for the token
                best_rate = None
                for protocol in rates_data.get('protocols', []):
                    if protocol.get('name') == 'Aave':
                        best_rate = protocol.get('borrow_rate')
                        break

                if best_rate:
                    print(f"✅ Found borrowing rate: {best_rate}%")
                    # Execute borrow via direct contract call with optimized parameters
                    return self._execute_optimized_borrow(amount_usd, token_address, best_rate)

        except Exception as e:
            print(f"❌ Mechanism 7 failed: {e}")

        return None

    def _execute_optimized_borrow(self, amount_usd, token_address, rate):
        """Execute borrow with optimized parameters"""
        try:
            # Convert to wei with proper decimals
            decimals = self._get_token_decimals(token_address)
            amount_wei = int(amount_usd * (10 ** decimals))

            # Use rate to optimize gas price
            gas_multiplier = 1.5 if rate > 5.0 else 1.2

            # Execute with optimized gas
            tx = self.agent.aave.pool_contract.functions.borrow(
                Web3.to_checksum_address(token_address),
                amount_wei,
                2,  # Variable rate
                0,  # Referral code
                Web3.to_checksum_address(self.agent.address)
            ).build_transaction({
                'chainId': self.agent.w3.eth.chain_id,
                'gas': 400000,
                'gasPrice': int(self.agent.w3.eth.gas_price * gas_multiplier),
                'nonce': self.agent.w3.eth.get_transaction_count(self.agent.address, 'pending'),
                'from': self.agent.address
            })

            signed_tx = self.agent.w3.eth.account.sign_transaction(tx, self.agent.account.key)
            tx_hash = self.agent.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            return tx_hash.hex()

        except Exception as e:
            print(f"❌ Optimized borrow failed: {e}")
            return None

    def _try_direct_aave_borrow(self, amount_usd, token_address):
        """Try the standard Aave integration borrow method with proper USD to wei conversion"""
        try:
            print("🔄 Mechanism 1: Direct Aave integration with enhanced conversion")

            # Use the Aave integration's conversion method
            if hasattr(self.agent.aave, '_convert_usd_to_wei'):
                amount_wei = self.agent.aave._convert_usd_to_wei(amount_usd, token_address)
            else:
                # Fallback conversion
                decimals = self._get_token_decimals(token_address)
                if token_address.lower() == self.agent.usdc_address.lower():
                    amount_wei = int(amount_usd * (10 ** decimals))
                else:
                    print(f"❌ Unsupported token for borrowing: {token_address}")
                    return None

            if amount_wei <= 0:
                print(f"❌ Invalid wei amount: {amount_wei}")
                return None

            print(f"💱 Converted ${amount_usd} to {amount_wei} wei")

            # Get optimized gas parameters
            try:
                gas_params = self.get_optimized_gas_params('aave_borrow', 'market')
                print(f"✅ Got gas parameters: {gas_params}")
            except Exception as gas_error:
                print(f"⚠️ Gas parameter error: {gas_error}")
                gas_params = {'gas': 400000, 'gasPrice': self.agent.w3.to_wei(1, 'gwei')}

            # Use the borrow method with wei amount
            if hasattr(self.agent.aave, 'borrow_from_aave'):
                try:
                    borrow_result = self.agent.aave.borrow_from_aave(amount_wei, token_address)
                    if borrow_result:
                        print(f"✅ Mechanism 1 success with wei: {borrow_result}")
                        return borrow_result
                except Exception as wei_error:
                    print(f"⚠️ Wei borrow failed: {wei_error}")

            # Fallback to USD amount if available
            if hasattr(self.agent.aave, 'borrow'):
                try:
                    borrow_result = self.agent.aave.borrow(amount_usd, token_address)
                    if borrow_result:
                        print(f"✅ Mechanism 1 success with USD: {borrow_result}")
                        return borrow_result
                except Exception as usd_error:
                    print(f"❌ USD borrow failed: {usd_error}")

            raise Exception("No working borrow method found in Aave integration")

        except Exception as e:
            print(f"❌ Mechanism 1 failed: {e}")

        return None

    def _try_alternative_parameter_order(self, amount_usd, token_address):
        """Try with different parameter arrangements"""
        try:
            print("🔄 Mechanism 2: Alternative parameter order")

            # Try the simple borrow method with correct signature
            tx_hash = self.agent.aave.borrow(amount_usd, token_address)

            if tx_hash:
                print(f"✅ Mechanism 2 success: {tx_hash}")
                return tx_hash

        except Exception as e:
            print(f"❌ Mechanism 2 failed: {e}")

        return None

    def _try_manual_step_borrow(self, amount_usd, token_address):
        """Manual step-by-step borrowing with enhanced retry logic"""
        try:
            print("🔄 Mechanism 3: Manual step-by-step borrow with retry logic")

            # Enhanced pre-validation before attempting borrow
            print(f"🔍 Enhanced pre-borrow validation...")

            # Check current account data from Aave
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

            pool_contract = self.agent.w3.eth.contract(
                address=self.agent.aave_pool_address,
                abi=pool_abi
            )

            user_address = Web3.to_checksum_address(self.agent.address)
            account_data = pool_contract.functions.getUserAccountData(user_address).call()

            available_borrows_usd = account_data[2] / (10**8)
            current_hf = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')

            print(f"   Available borrows: ${available_borrows_usd:.2f}")
            print(f"   Current HF: {current_hf:.4f}")
            print(f"   Requested: ${amount_usd:.2f}")

            # Validate borrowing capacity with safety margin
            if amount_usd > available_borrows_usd * 0.9:  # Use 90% of available
                safe_amount = available_borrows_usd * 0.8  # Reduce to 80%
                print(f"⚠️ Reducing borrow amount for safety: ${safe_amount:.2f}")
                amount_usd = safe_amount

            if amount_usd < 0.5:
                print(f"❌ Amount too small after safety reduction: ${amount_usd:.2f}")
                return None

            # Get token decimals and convert amount
            decimals = self._get_token_decimals(token_address)
            if token_address.lower() == self.agent.usdc_address.lower():
                amount_wei = int(amount_usd * (10 ** decimals))
            else:
                print(f"❌ Unsupported token: {token_address}")
                return None

            print(f"💱 Amount: ${amount_usd} = {amount_wei} wei")
            print(f"👤 User: {user_address}")

            # Progressive retry with increasing gas prices
            gas_multipliers = [1.2, 1.5, 1.8, 2.0, 2.5]

            for attempt, multiplier in enumerate(gas_multipliers):
                try:
                    print(f"🔄 Attempt {attempt + 1}/5 with gas multiplier {multiplier}")

                    # Get fresh nonce for each attempt
                    nonce = self.agent.w3.eth.get_transaction_count(user_address, 'pending')

                    # Get optimized gas parameters
                    gas_params = self.get_optimized_gas_params('aave_borrow', 'urgent' if attempt > 2 else 'market')

                    # Apply progressive multiplier
                    if 'gasPrice' in gas_params:
                        gas_params['gasPrice'] = int(gas_params['gasPrice'] * multiplier)
                    elif 'maxFeePerGas' in gas_params:
                        gas_params['maxFeePerGas'] = int(gas_params['maxFeePerGas'] * multiplier)
                        gas_params['maxPriorityFeePerGas'] = int(gas_params['maxPriorityFeePerGas'] * multiplier)

                    print(f"⛽ Gas params for attempt {attempt + 1}: {gas_params}")

                    # Build transaction
                    transaction = self.agent.aave.pool_contract.functions.borrow(
                        Web3.to_checksum_address(token_address),
                        amount_wei,
                        2,  # Variable interest rate mode
                        0,  # referralCode
                        user_address
                    ).build_transaction({
                        'chainId': self.agent.w3.eth.chain_id,
                        'gas': gas_params.get('gas', 400000),
                        'nonce': nonce,
                        'from': user_address,
                        **{k: v for k, v in gas_params.items() if k in ['gasPrice', 'maxFeePerGas', 'maxPriorityFeePerGas']}
                    })

                    # Sign and send
                    signed_txn = self.agent.w3.eth.account.sign_transaction(
                        transaction, self.agent.account.key
                    )
                    tx_hash = self.agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

                    tx_hash_hex = tx_hash.hex()
                    print(f"✅ Borrow successful: {tx_hash_hex}")

                    # Wait for confirmation with detailed error analysis
                    try:
                        receipt = self.agent.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                        if receipt.status == 1:
                            print(f"🎉 BORROW CONFIRMED: {tx_hash_hex}")
                            return tx_hash_hex
                        else:
                            print(f"❌ Borrow reverted: {tx_hash_hex}")

                            # Enhanced revert reason analysis
                            revert_analysis = self._analyze_transaction_revert(tx_hash_hex, transaction, receipt)
                            print(f"   🔍 Detailed revert analysis: {revert_analysis['summary']}")

                            # Handle specific revert reasons
                            if revert_analysis['retry_recommended']:
                                if revert_analysis['suggested_action'] == 'reduce_amount':
                                    smaller_amount = amount_usd * 0.6
                                    print(f"   🔄 Retrying with reduced amount: ${smaller_amount:.2f}")
                                    return self._try_manual_step_borrow(smaller_amount, token_address)
                                elif revert_analysis['suggested_action'] == 'increase_gas':
                                    print(f"   🔄 Retrying with higher gas...")
                                    continue
                            else:
                                print(f"   ❌ No retry recommended: {revert_analysis['reason']}")
                                return None
                    except Exception as wait_error:
                        print(f"⚠️ Confirmation timeout: {wait_error}")
                        return tx_hash_hex  # Return hash even if confirmation times out

                except Exception as attempt_error:
                    error_msg = str(attempt_error).lower()
                    print(f"❌ Attempt {attempt + 1} failed: {attempt_error}")

                    # Specific error handling
                    if "nonce too low" in error_msg:
                        print(f"🔄 Nonce conflict, will retry with fresh nonce")
                        time.sleep(1)
                        continue
                    elif "gas" in error_msg and "low" in error_msg:
                        print(f"⛽ Gas too low, increasing multiplier")
                        continue
                    elif "insufficient funds" in error_msg:
                        print(f"💰 Insufficient ETH for gas fees")
                        break
                    else:
                        if attempt == len(gas_multipliers) - 1:
                            print(f"🚨 All retry attempts failed")
                            break
                        continue

        except Exception as e:
            print(f"❌ Mechanism 3 failed: {e}")

        return None

    def _try_direct_contract_call(self, amount_usd, token_address):
        """Direct contract call with enhanced error handling"""
        try:
            print("🔄 Mechanism 4: Direct contract call")

            # Enhanced contract interaction
            pool_contract = self.agent.w3.eth.contract(
                address=self.agent.aave_pool_address,
                abi=self._get_minimal_pool_abi()
            )

            decimals = self._get_token_decimals(token_address)
            amount_wei = int(amount_usd * (10 ** decimals))
            user_address = Web3.to_checksum_address(self.agent.address)

            # Enhanced gas estimation
            gas_estimate = pool_contract.functions.borrow(
                Web3.to_checksum_address(token_address),
                amount_wei,
                2,
                0,
                user_address
            ).estimate_gas({'from': user_address})

            # Execute with retry logic
            for attempt in range(self.max_retries):
                try:
                    nonce = self.agent.w3.eth.get_transaction_count(user_address, 'pending')

                    transaction = pool_contract.functions.borrow(
                        Web3.to_checksum_address(token_address),
                        amount_wei,
                        2,
                        0,
                        user_address
                    ).build_transaction({
                        'chainId': self.agent.w3.eth.chain_id,
                        'gas': int(gas_estimate * 1.3),
                        'gasPrice': int(self.agent.w3.eth.gas_price * 1.2),
                        'nonce': nonce,
                        'from': user_address
                    })

                    signed_txn = self.agent.w3.eth.account.sign_transaction(
                        transaction, self.agent.account.key
                    )
                    tx_hash = self.agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

                    tx_hash_hex = tx_hash.hex()
                    print(f"✅ Mechanism 4 success (attempt {attempt + 1}): {tx_hash_hex}")
                    return tx_hash_hex

                except Exception as retry_error:
                    if attempt < self.max_retries - 1:
                        print(f"🔄 Retrying mechanism 4 (attempt {attempt + 2})")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise retry_error

        except Exception as e:
            print(f"❌ Mechanism 4 failed: {e}")

        return None

    def _get_token_decimals(self, token_address):
        """Get token decimals with fallbacks"""
        try:
            # Try direct contract call first
            token_contract = self.agent.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=[{
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
            )
            return token_contract.functions.decimals().call()
        except:
            # Use known decimals as fallback
            known_decimals = {
                self.agent.usdc_address.lower(): 6,
                self.agent.wbtc_address.lower(): 8,
                self.agent.weth_address.lower(): 18,
                self.agent.dai_address.lower(): 18
            }
            return known_decimals.get(token_address.lower(), 18)

    def _get_minimal_pool_abi(self):
        """Get minimal ABI for borrow function"""
        return [{
            "inputs": [
                {"name": "asset", "type": "address"},
                {"name": "amount", "type": "uint256"},
                {"name": "interestRateMode", "type": "uint256"},
                {"name": "referralCode", "type": "uint16"},
                {"name": "onBehalfOf", "type": "address"}
            ],
            "name": "borrow",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

    def detect_manual_override(self):
        """
        Detect when manual override is active through multiple indicators
        """
        # Check for manual trigger files
        manual_files = ['trigger_test.flag', 'manual_override.flag', 'force_borrow.flag']
        for file_path in manual_files:
            if os.path.exists(file_path):
                print(f"🔧 Manual override detected: {file_path} exists")
                return True

        # Check if manual_override_active attribute is set
        if hasattr(self, 'manual_override_active') and self.manual_override_active:
            print(f"🔧 Manual override detected: manual_override_active = True")
            return True

        # Check for test mode
        if os.path.exists('test_mode.flag'):
            print(f"🧪 Test mode detected - treating as manual override")
            return True

        # Check environment variable
        if os.getenv('MANUAL_OVERRIDE', '').lower() in ['true', '1', 'yes']:
            print(f"🔧 Manual override detected: MANUAL_OVERRIDE environment variable")
            return True

        return False

    def calculate_safe_borrow_amount(self, growth_amount, available_borrows_usd):
        """
        Calculate a safe borrow amount based on growth and available capacity
        """
        try:
            # Use agent's calculation logic if available
            if hasattr(self.agent, 'calculate_safe_borrow_amount'):
                return self.agent.calculate_safe_borrow_amount(growth_amount, available_borrows_usd)

            # Fallback calculation logic
            if available_borrows_usd <= 0:
                return 0.0

            # Conservative approach: use 15% of available capacity or $10, whichever is smaller
            safe_amount = min(available_borrows_usd * 0.15, 10.0)

            # Ensure minimum of $0.5 if there's any capacity
            if safe_amount > 0:
                safe_amount = max(safe_amount, 0.5)

            return safe_amount

        except Exception as e:
            print(f"❌ Safe borrow calculation failed: {e}")
            return 0.0

    def get_optimized_gas_params(self, operation_type='default', market_condition='normal'):
        """
        Calculate gas parameters based on market conditions
        """
        try:
            # Use agent's aave integration if available
            if hasattr(self.agent, 'aave') and hasattr(self.agent.aave, 'get_optimized_gas_params'):
                return self.agent.aave.get_optimized_gas_params(operation_type, market_condition)

            # Fallback gas parameters
            base_gas_price = self.agent.w3.eth.gas_price if hasattr(self.agent, 'w3') else self.agent.w3.to_wei(1, 'gwei')

            # Gas limits for different operations
            gas_limits = {
                'aave_borrow': 400000,
                'aave_supply': 300000,
                'uniswap_swap': 350000,
                'default': 250000
            }

            # Market condition multipliers
            multipliers = {
                'normal': 1.2,
                'volatile': 1.5,
                'urgent': 2.0,
                'market': 1.3
            }

            gas_limit = gas_limits.get(operation_type, gas_limits['default'])
            multiplier = multipliers.get(market_condition, 1.2)

            return {
                'gas': gas_limit,
                'gasPrice': int(base_gas_price * multiplier)
            }

        except Exception as e:
            print(f"⚠️ Gas parameter calculation failed: {e}")
            return {
                'gas': 400000,
                'gasPrice': self.agent.w3.to_wei(1, 'gwei') if hasattr(self.agent, 'w3') else 1000000000
            }

    def _execute_borrow_transaction(self, w3_instance, pool_contract, token_address, 
                                   amount_wei, interest_rate_mode, user_address):
        """Execute borrow transaction with enhanced error handling and higher gas limits"""

        # Get fresh nonce and gas data
        nonce = w3_instance.eth.get_transaction_count(user_address, 'pending')

        # CRITICAL: Use much higher gas limits for Aave borrowing
        try:
            estimated_gas = pool_contract.functions.borrow(
                token_address, amount_wei, interest_rate_mode, 0, user_address
            ).estimate_gas({'from': user_address})

            gas_limit = max(int(estimated_gas * 1.5), 600000)  # At least 600k gas
            print(f"⛽ Estimated gas: {estimated_gas}, using: {gas_limit}")
        except Exception as gas_est_error:
            gas_limit = 800000  # Much higher fallback for complex operations
            print(f"⚠️ Gas estimation failed ({gas_est_error}), using high fallback: {gas_limit}")

        # Enhanced gas price with network conditions
        try:
            current_gas_price = w3_instance.eth.gas_price
            gas_price = int(current_gas_price * 2.0)  # Much higher premium for reliability
        except:
            gas_price = int(1.0 * 1e9)  # 1.0 gwei fallback (higher)

        print(f"⛽ Gas price: {gas_price} wei ({gas_price / 1e9:.2f} gwei)")

        # Pre-transaction validation
        try:
            print(f"🔍 Pre-transaction validation:")

            # Check current account data
            account_data = pool_contract.functions.getUserAccountData(user_address).call()
            available_borrows = account_data[2] / (10**8)
            health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')

            print(f"   Available borrows: ${available_borrows:.2f}")
            print(f"   Health factor: {health_factor:.4f}")
            print(f"   Requested amount: ${amount_wei / (10**6):.2f}")

            if available_borrows < (amount_wei / (10**6)):
                print(f"❌ CRITICAL: Insufficient borrowing capacity!")
                return None

            if health_factor < 1.2:
                print(f"❌ CRITICAL: Health factor too low for borrowing!")
                return None

        except Exception as validation_error:
            print(f"⚠️ Pre-transaction validation failed: {validation_error}")

        # Multiple transaction attempts with increasing gas
        gas_multipliers = [1.0, 1.5, 2.0, 2.5]  # More aggressive gas increases
        gas_limit_multipliers = [1.0, 1.2, 1.5, 2.0]  # Also increase gas limits

        for attempt, (gas_mult, limit_mult) in enumerate(zip(gas_multipliers, gas_limit_multipliers)):
            try:
                adjusted_gas_price = int(gas_price * gas_mult)
                adjusted_gas_limit = int(gas_limit * limit_mult)
                current_nonce = nonce + attempt

                print(f"🔄 Enhanced attempt {attempt + 1}:")
                print(f"   Nonce: {current_nonce}")
                print(f"   Gas limit: {adjusted_gas_limit:,}")
                print(f"   Gas price: {adjusted_gas_price:,} wei ({adjusted_gas_price / 1e9:.3f} gwei)")

                # Build borrow transaction with enhanced parameters
                transaction = pool_contract.functions.borrow(
                    Web3.to_checksum_address(token_address),  # address
                    int(amount_wei),                          # uint256
                    int(interest_rate_mode),                  # uint256 
                    int(0),                                   # uint16 referralCode
                    Web3.to_checksum_address(user_address)    # address onBehalfOf
                ).build_transaction({
                    'chainId': w3_instance.eth.chain_id,
                    'gas': adjusted_gas_limit,
                    'gasPrice': adjusted_gas_price,
                    'nonce': current_nonce,
                    'from': user_address
                })

                # Sign and send
                signed_txn = w3_instance.eth.account.sign_transaction(transaction, self.agent.account.key)
                tx_hash = w3_instance.eth.send_raw_transaction(signed_txn.rawTransaction)

                tx_hash_hex = tx_hash.hex()
                print(f"✅ Transaction sent: {tx_hash_hex}")

                # Wait for confirmation with timeout
                try:
                    print(f"⏳ Waiting for confirmation...")
                    receipt = w3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

                    if receipt.status == 1:
                        print(f"🎉 BORROW SUCCESS! Transaction confirmed: {tx_hash_hex}")
                        explorer_url = f"https://arbiscan.io/tx/{tx_hash_hex}"
                        print(f"📊 View on Arbiscan: {explorer_url}")
                        return tx_hash_hex
                    else:
                        print(f"❌ Transaction reverted (status=0): {tx_hash_hex}")

                        # Enhanced revert reason analysis
                        revert_analysis = self._analyze_transaction_revert(tx_hash_hex, transaction, receipt)
                        print(f"   🔍 Detailed revert analysis: {revert_analysis['summary']}")

                        # Handle specific revert reasons
                        if revert_analysis['retry_recommended']:
                            if revert_analysis['suggested_action'] == 'reduce_amount':
                                smaller_amount = amount_usd * 0.6
                                print(f"   🔄 Retrying with reduced amount: ${smaller_amount:.2f}")
                                return self._try_manual_step_borrow(smaller_amount, token_address)
                            elif revert_analysis['suggested_action'] == 'increase_gas':
                                print(f"   🔄 Retrying with higher gas...")
                                continue
                        else:
                            print(f"   ❌ No retry recommended: {revert_analysis['reason']}")
                            return None
                except Exception as get_tx_e:
                            print(f"    Could not fetch transaction details: {get_tx_e}")
                        raise Exception(f"Transaction {tx_hash_hex} reverted with status 0.")

                except Exception as retry_error:
                    print(f"❌ Enhanced attempt {attempt + 1} failed: {retry_error}")
                    if attempt == len(gas_multipliers) - 1:
                        print(f"🚨 All enhanced attempts failed")
                        break
                    continue

            return None

        except Exception as e:
            print(f"❌ Enhanced borrow transaction failed: {e}")
            return None

    def _analyze_transaction_revert(self, tx_hash, transaction, receipt):
        """Analyze why a transaction reverted and suggest actions"""
        try:
            print(f"🔍 Analyzing transaction revert: {tx_hash}")

            # Try to get detailed revert reason
            revert_data = None
            try:
                # Replay the transaction to get revert reason
                self.agent.w3.eth.call(transaction, receipt.blockNumber)
            except Exception as revert_error:
                revert_data = str(revert_error)

            # Analyze common Aave revert reasons
            analysis = {
                'revert_data': revert_data,
                'retry_recommended': False,
                'suggested_action': None,
                'summary': 'Unknown revert reason',
                'reason': 'Transaction failed without clear reason'
            }

            if revert_data:
                error_lower = revert_data.lower()

                if "health factor" in error_lower or "liquidation" in error_lower:
                    analysis.update({
                        'summary': 'Health factor would drop below liquidation threshold',
                        'retry_recommended': True,
                        'suggested_action': 'reduce_amount',
                        'reason': 'Borrow amount too large for current collateral'
                    })

                elif "borrowing not enabled" in error_lower:
                    analysis.update({
                        'summary': 'Borrowing disabled for this asset',
                        'retry_recommended': False,
                        'reason': 'Asset borrowing is disabled by protocol'
                    })

                elif "collateral balance" in error_lower or "no collateral" in error_lower:
                    analysis.update({
                        'summary': 'Insufficient or no collateral',
                        'retry_recommended': False,
                        'reason': 'Need to supply collateral before borrowing'
                    })

                elif "gas" in error_lower and ("low" in error_lower or "insufficient" in error_lower):
                    analysis.update({
                        'summary': 'Insufficient gas for transaction',
                        'retry_recommended': True,
                        'suggested_action': 'increase_gas',
                        'reason': 'Transaction ran out of gas'
                    })

                elif "allowance" in error_lower:
                    analysis.update({
                        'summary': 'Token allowance issue',
                        'retry_recommended': True,
                        'suggested_action': 'check_allowance',
                        'reason': 'Need to approve token spending'
                    })

                elif "paused" in error_lower:
                    analysis.update({
                        'summary': 'Protocol is paused',
                        'retry_recommended': False,
                        'reason': 'Aave protocol temporarily paused'
                    })

                else:
                    analysis.update({
                        'summary': f'Unknown error: {revert_data[:100]}...',
                        'retry_recommended': False,
                        'reason': 'Unrecognized error pattern'
                    })

            # Log analysis for debugging
            print(f"   Revert analysis: {analysis['summary']}")
            if analysis['retry_recommended']:
                print(f"   Suggested action: {analysis['suggested_action']}")
            else:
                print(f"   No retry: {analysis['reason']}")

            return analysis

        except Exception as e:
            print(f"⚠️ Revert analysis failed: {e}")
            return {
                'summary': 'Analysis failed',
                'retry_recommended': False,
                'reason': 'Could not analyze revert reason'
            }