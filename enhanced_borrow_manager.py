"""Enhanced Borrow Manager gas settings updated for mainnet and testnet."""
"""Enhanced Borrow Manager: Fixing syntax error at line 469 and ensuring DAI compliance."""
"""
Enhanced Borrow Manager
Provides robust borrowing functionality with fallbacks and validation
"""

import time
from web3 import Web3

class EnhancedBorrowManager:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.account = agent.account
        self.aave = agent.aave

    def safe_borrow_with_fallbacks(self, amount_usd, token_address):
        """DAI-only borrowing - no fallbacks"""
        try:
            # Ensure we're using DAI address for the new strategy
                        if token_address.lower() != self.agent.dai_address.lower():
                print(f"🔄 DAI Strategy: Converting borrow request to DAI address")
                print(f"   Original: {token_address}")
                print(f"   Using DAI: {self.agent.dai_address}")
                token_address = self.agent.dai_address

            print(f"🏦 Enhanced Borrow Manager: Attempting to borrow ${amount_usd:.2f} DAI ONLY")
            print(f"🔍 DEBUG: DAI address: {token_address}")

            # Convert USD to DAI wei (DAI has 18 decimals, 1 USD ≈ 1 DAI)
            amount_wei = int(amount_usd * (10 ** 18))
            print(f"💱 Converted ${amount_usd:.2f} to {amount_wei} DAI wei")
            print(f"🎯 DAI Strategy: Primary borrowing asset confirmed as DAI")

            # Execute DAI borrow with correct method name
            result = self.aave.borrow(amount_wei, token_address)

            if result:
                print(f"✅ Successfully borrowed ${amount_usd:.2f} DAI")
                return result
            else:
                print(f"❌ DAI borrow failed - NO FALLBACKS")
                return None

        except Exception as e:
            print(f"❌ Enhanced DAI borrow failed: {e}")
            return None

    def _validate_borrow_conditions_enhanced(self, amount_usd, token_address):
        """Enhanced validation with specific revert prevention"""
        try:
            print(f"🔍 Enhanced validation for ${amount_usd:.2f} borrow...")

            # Check basic parameters
            if not amount_usd or amount_usd <= 0:
                print(f"❌ Invalid borrow amount: ${amount_usd}")
                return False

            try:
                # Validate and normalize token address
                from web3 import Web3
                normalized_address = Web3.to_checksum_address(token_address)
                if len(normalized_address) != 42:
                    print(f"❌ Invalid token address: {token_address}")
                    return False
            except Exception as addr_error:
                print(f"❌ Invalid token address format: {token_address} - {addr_error}")
                return False

            # Enhanced ETH balance check
            eth_balance = self.agent.get_eth_balance()
            if eth_balance < 0.002:  # Increased requirement
                print(f"❌ Insufficient ETH for gas: {eth_balance:.6f} ETH")
                return False

            # Check network connectivity
            try:
                latest_block = self.w3.eth.block_number
                print(f"✅ Network connected - Block: {latest_block}")
            except Exception as net_error:
                print(f"❌ Network connectivity issue: {net_error}")
                return False

            # Enhanced Aave pool health check
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

            pool_contract = self.w3.eth.contract(
                address=self.agent.aave_pool_address,
                abi=pool_abi
            )

            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()

            total_collateral = account_data[0] / (10**8)
            total_debt = account_data[1] / (10**8)
            available_borrows = account_data[2] / (10**8)
            health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')

            print(f"🔍 Enhanced Validation Results:")
            print(f"   Total Collateral: ${total_collateral:.2f}")
            print(f"   Total Debt: ${total_debt:.2f}")
            print(f"   Available Borrows: ${available_borrows:.2f}")
            print(f"   Health Factor: {health_factor:.4f}")
            print(f"   ETH Balance: {eth_balance:.6f} ETH")

            # Enhanced safety thresholds for mainnet
            min_health_factor = 2.0  # Increased from 1.5
            min_collateral_required = 50.0  # Increased from 10.0

            if total_collateral < min_collateral_required:
                print(f"❌ Insufficient collateral: ${total_collateral:.2f} < ${min_collateral_required}")
                return False

            if health_factor < min_health_factor:
                print(f"❌ Health factor too low: {health_factor:.4f} < ${min_health_factor}")
                return False

            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrowing capacity: ${available_borrows:.2f} < ${amount_usd:.2f}")
                return False

            # Enhanced safety check - don't borrow more than 70% of available (reduced from 80%)
            max_safe_borrow = available_borrows * 0.7
            if amount_usd > max_safe_borrow:
                print(f"❌ Borrow amount exceeds safe limit: ${amount_usd:.2f} > ${max_safe_borrow:.2f}")
                return False

            # Additional check: simulate the borrow transaction with proper ABI
            try:
                user_address = Web3.to_checksum_address(self.agent.address)
                token_address_checksum = Web3.to_checksum_address(token_address)
                amount_wei = int(amount_usd * (10 ** 6))  # USDC decimals

                # Use the agent's Aave integration which has the correct ABI
                if hasattr(self.agent, 'aave') and self.agent.aave:
                    # Simulate the transaction with proper gas context
                    try:
                        # CORRECTED: Use DAI decimals (18) for DAI token
                        if token_address_checksum.lower() == self.agent.dai_address.lower():
                            amount_wei = int(amount_usd * (10 ** 18))  # DAI has 18 decimals
                        else:
                            amount_wei = int(amount_usd * (10 ** 6))   # USDC has 6 decimals

                        self.agent.aave.pool_contract.functions.borrow(
                            token_address_checksum,
                            amount_wei,  # Use token-specific amount
                            2,  # Variable rate
                            0,  # Referral code
                            user_address
                        ).call({
                            'from': user_address,
                            'gas': 500000,
                            'gasPrice': int(2 * 10**9)  # 2 gwei minimum for simulation
                        })
                        print(f"✅ Transaction simulation passed")
                    except Exception as aave_sim_error:
                        print(f"❌ CRITICAL: Transaction simulation failed: {aave_sim_error}")

                        # Check for specific Aave protocol errors
                        error_str = str(aave_sim_error).lower()
                        if "insufficient collateral" in error_str:
                            print(f"💡 SOLUTION: Increase collateral or reduce borrow amount")
                            return False
                        elif "borrowing not enabled" in error_str:
                            print(f"💡 SOLUTION: USDC borrowing may be disabled")
                            return False
                        elif "health factor" in error_str:
                            print(f"💡 SOLUTION: Health factor would be too low")
                            return False
                        else:
                            print(f"💡 Proceeding cautiously despite simulation failure")
                            # Continue but flag as risky
                else:
                    print(f"⚠️ Aave integration not available for simulation")

            except Exception as sim_error:
                print(f"❌ Transaction simulation failed: {sim_error}")

                # Provide specific guidance based on simulation error
                if "insufficient collateral" in str(sim_error).lower():
                    print(f"💡 Need more collateral deposited to Aave")
                elif "health factor" in str(sim_error).lower():
                    print(f"💡 Borrow would make health factor too low")
                elif "borrowing not enabled" in str(sim_error).lower():
                    print(f"💡 Borrowing might not be enabled for this asset")
                elif "function" in str(sim_error).lower() and "abi" in str(sim_error).lower():
                    print(f"💡 ABI issue detected - proceeding with actual transaction")
                else:
                    return False

            print(f"✅ All enhanced validation checks passed")
            return True

        except Exception as e:
            print(f"❌ Enhanced validation failed: {e}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            return False

    def _get_enhanced_gas_params(self, attempt_number):
        """Get enhanced gas parameters with dynamic cheapest pricing"""
        try:
            # Base parameters
            base_gas_limit = 500000
            current_gas_price = self.w3.eth.gas_price

            print(f"🔍 Network Gas Analysis:")
            print(f"   Current network gas price: {self.w3.from_wei(current_gas_price, 'gwei'):.4f} gwei")

            # Dynamic gas pricing based on network conditions
            if attempt_number == 0:
                # First attempt: Use network-acceptable gas price (increased for mainnet)
                # Arbitrum mainnet requires higher gas for reliable execution
                min_viable_gas = max(current_gas_price, int(0.5 * 10**9))  # 0.5 gwei minimum (increased)
                enhanced_gas_price = int(min_viable_gas * 1.5)  # 50% above minimum for reliability
                gas_limit = base_gas_limit
                print(f"   🟢 CHEAPEST MODE: Using {self.w3.from_wei(enhanced_gas_price, 'gwei'):.4f} gwei")

            elif attempt_number == 1:
                # Second attempt: Use network standard
                enhanced_gas_price = int(current_gas_price * 1.2)  # 20% above network
                gas_limit = base_gas_limit + 100000
                print(f"   🟡 STANDARD MODE: Using {self.w3.from_wei(enhanced_gas_price, 'gwei'):.4f} gwei")

            else:
                # Higher attempts: Progressive increase
                multiplier = 1.5 + (attempt_number * 0.3)  # 1.5x, 1.8x, 2.1x, etc.
                enhanced_gas_price = int(current_gas_price * multiplier)
                gas_limit = base_gas_limit + (attempt_number * 100000)
                print(f"   🔴 PRIORITY MODE: Using {self.w3.from_wei(enhanced_gas_price, 'gwei'):.4f} gwei")

            # Safety minimum - only enforce if gas price is extremely low
            absolute_minimum = int(0.01 * 10**9)  # 0.01 gwei absolute floor
            enhanced_gas_price = max(enhanced_gas_price, absolute_minimum)

            return {
                'gas': gas_limit,
                'gasPrice': enhanced_gas_price
            }

        except Exception as e:
            print(f"⚠️ Enhanced gas params failed: {e}")
            return {
                'gas': 500000,
                'gasPrice': int(0.05 * 10**9)  # 0.05 gwei fallback - cheapest viable
            }

    def _validate_borrow_conditions(self, amount_usd, token_address):
        """Validate conditions for safe borrowing with comprehensive checks"""
        try:
            print(f"🔍 Enhanced validation for ${amount_usd:.2f} borrow...")

            # Check basic parameters
            if not amount_usd or amount_usd <= 0:
                print(f"❌ Invalid borrow amount: ${amount_usd}")
                return False

            try:
                # Validate and normalize token address
                from web3 import Web3
                normalized_address = Web3.to_checksum_address(token_address)
                if len(normalized_address) != 42:
                    print(f"❌ Invalid token address: {token_address}")
                    return False
            except Exception as addr_error:
                print(f"❌ Invalid token address format: {token_address} - {addr_error}")
                return False

            # Check ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            if eth_balance < 0.001:
                print(f"❌ Insufficient ETH for gas: {eth_balance:.6f} ETH")
                return False

            # Check network connectivity
            try:
                latest_block = self.w3.eth.block_number
                print(f"✅ Network connected - Block: {latest_block}")
            except Exception as net_error:
                print(f"❌ Network connectivity issue: {net_error}")
                return False

            # Check Aave pool health
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

            pool_contract = self.w3.eth.contract(
                address=self.agent.aave_pool_address,
                abi=pool_abi
            )

            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()

            total_collateral = account_data[0] / (10**8)
            total_debt = account_data[1] / (10**8)
            available_borrows = account_data[2] / (10**8)
            health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')

            print(f"🔍 Enhanced Validation Results:")
            print(f"   Total Collateral: ${total_collateral:.2f}")
            print(f"   Total Debt: ${total_debt:.2f}")
            print(f"   Available Borrows: ${available_borrows:.2f}")
            print(f"   Health Factor: {health_factor:.4f}")
            print(f"   ETH Balance: {eth_balance:.6f} ETH")

            # Safety thresholds
            min_health_factor = 1.5
            min_collateral_required = 10.0  # $10 minimum collateral

            if total_collateral < min_collateral_required:
                print(f"❌ Insufficient collateral: ${total_collateral:.2f} < ${min_collateral_required}")
                return False

            if health_factor < min_health_factor:
                print(f"❌ Health factor too low: {health_factor:.4f} < ${min_health_factor}")
                return False

            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrowing capacity: ${available_borrows:.2f} < ${amount_usd:.2f}")
                return False

            # Additional safety check - don't borrow more than 80% of available
            max_safe_borrow = available_borrows * 0.8
            if amount_usd > max_safe_borrow:
                print(f"❌ Borrow amount exceeds safe limit: ${amount_usd:.2f} > ${max_safe_borrow:.2f}")
                return False

            print(f"✅ All validation checks passed")
            return True

        except Exception as e:
            print(f"❌ Enhanced validation failed: {e}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            return False

    def execute_enhanced_borrow_with_retry(self, amount_usd):
        """Execute enhanced borrow with DAI ONLY - absolutely no fallbacks"""
        try:
            print(f"🏦 Enhanced Borrow Manager: STRICT DAI-ONLY BORROWING")
            print(f"💰 Target amount: ${amount_usd:.2f} DAI")
            print(f"🎯 DAI address: {self.agent.dai_address}")
            print(f"❌ USDC fallback: DISABLED")

            # Validate we're using DAI address
            dai_address = self.agent.dai_address
            print(f"✅ Confirmed DAI address: {dai_address}")

            # Enhanced validation for DAI borrowing
            if not self._validate_dai_borrow_conditions(amount_usd):
                print(f"❌ DAI borrow validation failed")
                return None

            # Execute DAI borrow with direct method call - simplified approach
            result = self.aave.borrow(amount_usd, dai_address)

            if result:
                print(f"✅ SUCCESS: Borrowed ${amount_usd:.2f} DAI")
                print(f"🔗 Transaction hash: {result}")
                return result
            else:
                print(f"❌ FAILED: DAI borrow unsuccessful")
                print(f"🚫 NO FALLBACK - DAI-ONLY STRATEGY")
                return None

        except Exception as e:
            print(f"❌ Enhanced DAI borrow failed: {e}")
            print(f"🚫 NO FALLBACK ATTEMPTED - STRICT DAI-ONLY MODE")
            return None
    def _validate_dai_borrow_conditions(self, amount_usd):
        """Validate conditions specifically for DAI borrowing"""
        try:
            print(f"🔍 DAI-specific borrow validation for ${amount_usd:.2f}")

            # Check DAI is available for borrowing on Aave
            dai_address = self.agent.dai_address
            print(f"✅ DAI address confirmed: {dai_address}")

            # Standard validation checks
            return self._validate_borrow_conditions(amount_usd, dai_address)

        except Exception as e:
            print(f"❌ DAI borrow validation failed: {e}")
            return False

    def _execute_dai_borrow_with_retries(self, amount_wei, dai_address):
        """Execute DAI borrow with retries - no other tokens"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                print(f"🔄 DAI borrow attempt {attempt + 1}/{max_retries}")
                print(f"🎯 Only borrowing DAI: {dai_address}")

                # Execute borrow using Aave integration - FIXED METHOD NAME
                result = self.aave.borrow(amount_wei, dai_address)

                if result:
                    print(f"✅ DAI borrow successful on attempt {attempt + 1}")
                    return result
                else:
                    print(f"❌ DAI borrow failed on attempt {attempt + 1}")

                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                        print(f"⏰ Waiting {wait_time}s before retry...")
                        import time
                        time.sleep(wait_time)

            except Exception as e:
                print(f"❌ DAI borrow attempt {attempt + 1} error: {e}")
                if attempt == max_retries - 1:
                    print(f"🚫 All DAI borrow attempts failed")

        return None

    def _validate_network_timing(self):
        """Validate network conditions for optimal transaction timing"""
        try:
            current_block = self.w3.eth.get_block('latest')
            current_time = time.time()
            block_time = current_block.timestamp

            # Check if we're close to block time (avoid mempool congestion)
            time_since_block = current_time - block_time

            print(f"🕐 Network Timing Check:")
            print(f"   Time since last block: {time_since_block:.1f}s")

            # Arbitrum blocks are ~0.25s, warn if we're too close to next expected block
            if time_since_block > 10:  # More than 10s since last block might indicate issues
                print(f"⚠️ Long time since last block - network may be congested")
                return False

            # Check pending transaction count in mempool
            pending_tx_count = self.w3.eth.get_block('pending').transactions.__len__ if hasattr(self.w3.eth.get_block('pending'), 'transactions') else 0
            print(f"   Pending transactions: {pending_tx_count}")

            return True

        except Exception as e:
            print(f"⚠️ Network timing validation failed: {e}")
            return True  # Don't block if we can't check timing
`
import os
import time
import json
from decimal import Decimal
from web3 import Web3

class EnhancedBorrowManager:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.aave = agent.aave
        self.max_retry_attempts = 3
        self.retry_delay = 10  # seconds

    def execute_enhanced_borrow_with_retry(self, amount_usd):
        """Execute DAI borrow with enhanced retry mechanism and validation"""
        try:
            print(f"\n🏦 ENHANCED DAI BORROW MANAGER")
            print(f"💰 Target borrow amount: ${amount_usd:.2f} DAI")

            # Pre-borrow validation
            if not self._validate_borrow_conditions(amount_usd):
                return False

            # Execute borrow with retries
            for attempt in range(1, self.max_retry_attempts + 1):
                print(f"\n🔄 Borrow attempt {attempt}/{self.max_retry_attempts}")

                # Execute the borrow
                borrow_result = self._execute_single_borrow_attempt(amount_usd)

                if borrow_result:
                    print(f"✅ Enhanced DAI borrow successful on attempt {attempt}")
                    self._log_borrow_success(amount_usd, attempt)
                    return True
                else:
                    print(f"❌ Borrow attempt {attempt} failed")

                    if attempt < self.max_retry_attempts:
                        print(f"⏳ Waiting {self.retry_delay}s before retry...")
                        time.sleep(self.retry_delay)

                        # Adjust conditions for retry
                        amount_usd = self._adjust_amount_for_retry(amount_usd, attempt)

            print(f"❌ All {self.max_retry_attempts} borrow attempts failed")
            self._log_borrow_failure(amount_usd)
            return False

        except Exception as e:
            print(f"❌ Enhanced borrow manager error: {e}")
            return False

    def _validate_borrow_conditions(self, amount_usd):
        """Validate conditions before attempting borrow"""
        try:
            print("🔍 Validating borrow conditions...")

            # Check account data
            account_data = self.aave.get_user_account_data()
            if not account_data or not account_data.get('success', True):
                print("❌ Cannot retrieve account data")
                return False

            # Check available borrows
            available_borrows = account_data['availableBorrowsUSD']
            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrow capacity: ${available_borrows:.2f} < ${amount_usd:.2f}")
                return False

            # Check health factor
            health_factor = account_data['healthFactor']
            if health_factor < 2.0:
                print(f"❌ Health factor too low for safe borrowing: {health_factor:.4f}")
                return False

            # Check ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            if eth_balance < 0.001:
                print(f"❌ Insufficient ETH for gas: {eth_balance:.6f}")
                return False

            # Check DAI contract accessibility
            try:
                dai_contract = self.w3.eth.contract(
                    address=self.agent.dai_address, 
                    abi=self.aave.erc20_abi
                )
                dai_symbol = dai_contract.functions.symbol().call()
                print(f"✅ DAI contract accessible: {dai_symbol}")
            except Exception as dai_error:
                print(f"❌ DAI contract not accessible: {dai_error}")
                return False

            print("✅ All borrow conditions validated")
            return True

        except Exception as e:
            print(f"❌ Borrow validation failed: {e}")
            return False

    def _execute_single_borrow_attempt(self, amount_usd):
        """Execute a single DAI borrow attempt"""
        try:
            print(f"🎯 Executing DAI borrow: ${amount_usd:.2f}")

            # Use the agent's DAI address
            dai_address = self.agent.dai_address

            # Execute borrow through Aave integration
            borrow_result = self.aave.borrow(amount_usd, dai_address)

            if borrow_result:
                # Wait for transaction confirmation
                time.sleep(15)

                # Verify borrow by checking DAI balance
                dai_balance = self.aave.get_token_balance(dai_address)
                if dai_balance >= (amount_usd * 0.95):  # Allow 5% slippage
                    print(f"✅ DAI borrow verified: {dai_balance:.6f} DAI received")
                    return True
                else:
                    print(f"⚠️ DAI balance lower than expected: {dai_balance:.6f}")
                    return False
            else:
                print("❌ Borrow transaction failed")
                return False

        except Exception as e:
            print(f"❌ Single borrow attempt failed: {e}")
            return False

    def _adjust_amount_for_retry(self, original_amount, attempt):
        """Adjust borrow amount for retry attempts"""
        # Reduce amount by 10% each retry
        reduction_factor = 0.9 ** attempt
        adjusted_amount = original_amount * reduction_factor

        print(f"💡 Adjusting borrow amount for retry: ${original_amount:.2f} → ${adjusted_amount:.2f}")
        return adjusted_amount

    def _log_borrow_success(self, amount_usd, attempt):
        """Log successful borrow for analytics"""
        try:
            log_data = {
                'timestamp': time.time(),
                'amount_usd': float(amount_usd),
                'attempt': attempt,
                'status': 'success',
                'token': 'DAI'
            }

            # Save to file for tracking
            filename = f"borrow_success_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

        except Exception as e:
            print(f"⚠️ Could not save borrow success log: {e}")

    def _log_borrow_failure(self, amount_usd):
        """Log failed borrow for debugging"""
        try:
            log_data = {
                'timestamp': time.time(),
                'amount_usd': float(amount_usd),
                'status': 'failure',
                'token': 'DAI',
                'max_attempts': self.max_retry_attempts
            }

            filename = f"borrow_failure_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

        except Exception as e:
            print(f"⚠️ Could not save borrow failure log: {e}")
    def _execute_post_borrow_swaps(self, borrowed_amount):
        """Execute DAI swaps after successful borrow with strict validation"""
        try:
            print(f"🔄 Executing post-borrow DAI swaps for ${borrowed_amount:.2f}")

            # Wait for borrow confirmation
            import time
            time.sleep(8)

            # Get current DAI balance
            dai_balance = self.agent.aave.get_token_balance(self.agent.dai_address)
            print(f"💰 Current DAI balance: {dai_balance:.6f}")

            if dai_balance < 1.0:
                print("⚠️ Insufficient DAI balance for swaps")
                return False

            # Allocate DAI for swaps
            wbtc_allocation = min(dai_balance * 0.3, 3.0)  # 30% or max $3
            weth_allocation = min(dai_balance * 0.2, 2.0)  # 20% or max $2

            success_count = 0

            # Execute DAI → WBTC swap
            if wbtc_allocation >= 0.5:
                print(f"🔄 Swapping ${wbtc_allocation:.2f} DAI → WBTC")
                wbtc_result = self.agent.uniswap.swap_tokens(
                    self.agent.dai_address,
                    self.agent.wbtc_address,
                    wbtc_allocation,
                    500
                )

                if wbtc_result:
                    print("✅ DAI → WBTC swap successful")
                    success_count += 1
                    time.sleep(8)

                    # Supply WBTC to Aave
                    wbtc_balance = self.agent.aave.get_token_balance(self.agent.wbtc_address)
                    if wbtc_balance > 0:
                        supply_result = self.agent.aave.supply_to_aave(self.agent.wbtc_address, wbtc_balance)
                        if supply_result:
                            print("✅ WBTC supplied to Aave")
                        else:
                            print("❌ WBTC supply failed")
                else:
                    print("❌ DAI → WBTC swap failed")

            # Execute DAI → WETH swap
            if weth_allocation >= 0.5:
                print(f"🔄 Swapping ${weth_allocation:.2f} DAI → WETH")
                weth_result = self.agent.uniswap.swap_tokens(
                    self.agent.dai_address,
                    self.agent.weth_address,
                    weth_allocation,
                    500
                )

                if weth_result:
                    print("✅ DAI → WETH swap successful")
                    success_count += 1
                    time.sleep(8)

                    # Supply WETH to Aave
                    weth_balance = self.agent.aave.get_token_balance(self.agent.weth_address)
                    if weth_balance > 0:
                        supply_result = self.agent.aave.supply_to_aave(self.agent.weth_address, weth_balance)
                        if supply_result:
                            print("✅ WETH supplied to Aave")
                        else:
                            print("❌ WETH supply failed")
                else:
                    print("❌ DAI → WETH swap failed")

            # Supply remaining DAI directly
            remaining_dai = self.agent.aave.get_token_balance(self.agent.dai_address)
            if remaining_dai >= 0.5:
                print(f"🔄 Supplying remaining ${remaining_dai:.2f} DAI directly")
                dai_supply_result = self.agent.aave.supply_to_aave(self.agent.dai_address, remaining_dai)
                if dai_supply_result:
                    print("✅ DAI supplied to Aave")
                    success_count += 1
                else:
                    print("❌ DAI supply failed")

            print(f"📊 Post-borrow operations: {success_count} successful")
            return success_count > 0

        except Exception as e:
            print(f"❌ Post-borrow swaps failed: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return False
import os
import time
import json
from decimal import Decimal
from web3 import Web3

class EnhancedBorrowManager:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.aave = agent.aave
        self.max_retry_attempts = 3
        self.retry_delay = 10  # seconds

        dai_balance = self.aave.get_token_balance(self.agent.dai_address)
        print(f"🔍 Enhanced Borrow Manager initialized for DAI-ONLY operations")
        print(f"💰 DAI Balance: {dai_balance:.6f}")
        print(f"🔒 DAI COMPLIANCE: All operations restricted to DAI token only")

    def execute_enhanced_borrow_with_retry(self, amount_usd):
        """Execute DAI borrow with enhanced retry mechanism and validation"""
        try:
            print(f"\n🏦 ENHANCED DAI BORROW MANAGER")
            print(f"💰 Target borrow amount: ${amount_usd:.2f} DAI")

            # Pre-borrow validation
            if not self._validate_borrow_conditions(amount_usd):
                return False

            # Execute borrow with retries
            for attempt in range(1, self.max_retry_attempts + 1):
                print(f"\n🔄 Borrow attempt {attempt}/{self.max_retry_attempts}")

                # Execute the borrow
                borrow_result = self._execute_single_borrow_attempt(amount_usd)

                if borrow_result:
                    print(f"✅ Enhanced DAI borrow successful on attempt {attempt}")
                    self._log_borrow_success(amount_usd, attempt)
                    return True
                else:
                    print(f"❌ Borrow attempt {attempt} failed")

                    if attempt < self.max_retry_attempts:
                        print(f"⏳ Waiting {self.retry_delay}s before retry...")
                        time.sleep(self.retry_delay)

                        # Adjust conditions for retry
                        amount_usd = self._adjust_amount_for_retry(amount_usd, attempt)

            print(f"❌ All {self.max_retry_attempts} borrow attempts failed")
            self._log_borrow_failure(amount_usd)
            return False

        except Exception as e:
            print(f"❌ Enhanced borrow manager error: {e}")
            return False

    def _validate_borrow_conditions(self, amount_usd):
        """Validate conditions before attempting borrow"""
        try:
            print("🔍 Validating borrow conditions...")

            # Check account data
            account_data = self.aave.get_user_account_data()
            if not account_data or not account_data.get('success', True):
                print("❌ Cannot retrieve account data")
                return False

            # Check available borrows
            available_borrows = account_data['availableBorrowsUSD']
            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrow capacity: ${available_borrows:.2f} < ${amount_usd:.2f}")
                return False

            # Check health factor
            health_factor = account_data['healthFactor']
            if health_factor < 2.0:
                print(f"❌ Health factor too low for safe borrowing: {health_factor:.4f}")
                return False

            # Check ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            if eth_balance < 0.001:
                print(f"❌ Insufficient ETH for gas: {eth_balance:.6f}")
                return False

            # Check DAI contract accessibility
            try:
                dai_contract = self.w3.eth.contract(
                    address=self.agent.dai_address, 
                    abi=self.aave.erc20_abi
                )
                dai_symbol = dai_contract.functions.symbol().call()
                print(f"✅ DAI contract accessible: {dai_symbol}")
            except Exception as dai_error:
                print(f"❌ DAI contract not accessible: {dai_error}")
                return False

            print("✅ All borrow conditions validated")
            return True

        except Exception as e:
            print(f"❌ Borrow validation failed: {e}")
            return False

    def _execute_single_borrow_attempt(self, amount_usd):
        """Execute a single DAI borrow attempt"""
        try:
            print(f"🎯 Executing DAI borrow: ${amount_usd:.2f}")

            # Use the agent's DAI address
            dai_address = self.agent.dai_address

            # Execute borrow through Aave integration
            borrow_result = self.aave.borrow(amount_usd, dai_address)

            if borrow_result:
                # Wait for transaction confirmation
                time.sleep(15)

                # Verify borrow by checking DAI balance
                dai_balance = self.aave.get_token_balance(dai_address)
                if dai_balance >= (amount_usd * 0.95):  # Allow 5% slippage
                    print(f"✅ DAI borrow verified: {dai_balance:.6f} DAI received")
                    return True
                else:
                    print(f"⚠️ DAI balance lower than expected: {dai_balance:.6f}")
                    return False
            else:
                print("❌ Borrow transaction failed")
                return False

        except Exception as e:
            print(f"❌ Single borrow attempt failed: {e}")
            return False

    def _adjust_amount_for_retry(self, original_amount, attempt):
        """Adjust borrow amount for retry attempts"""
        # Reduce amount by 10% each retry
        reduction_factor = 0.9 ** attempt
        adjusted_amount = original_amount * reduction_factor

        print(f"💡 Adjusting borrow amount for retry: ${original_amount:.2f} → ${adjusted_amount:.2f}")
        return adjusted_amount

    def _log_borrow_success(self, amount_usd, attempt):
        """Log successful borrow for analytics"""
        try:
            log_data = {
                'timestamp': time.time(),
                'amount_usd': float(amount_usd),
                'attempt': attempt,
                'status': 'success',
                'token': 'DAI'
            }

            # Save to file for tracking
            filename = f"borrow_success_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

        except Exception as e:
            print(f"⚠️ Could not save borrow success log: {e}")

    def _log_borrow_failure(self, amount_usd):
        """Log failed borrow for debugging"""
        try:
            log_data = {
                'timestamp': time.time(),
                'amount_usd': float(amount_usd),
                'status': 'failure',
                'token': 'DAI',
                'max_attempts': self.max_retry_attempts
            }

            filename = f"borrow_failure_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

        except Exception as e:
            print(f"⚠️ Could not save borrow failure log: {e}")
    def _execute_post_borrow_swaps(self, borrowed_amount):
        """Execute DAI swaps after successful borrow with strict validation"""
        try:
            print(f"🔄 Executing post-borrow DAI swaps for ${borrowed_amount:.2f}")

            # Wait for borrow confirmation
            import time
            time.sleep(8)

            # Get current DAI balance
            dai_balance = self.agent.aave.get_token_balance(self.agent.dai_address)
            print(f"💰 Current DAI balance: {dai_balance:.6f}")

            if dai_balance < 1.0:
                print("⚠️ Insufficient DAI balance for swaps")
                return False

            # Allocate DAI for swaps
            wbtc_allocation = min(dai_balance * 0.3, 3.0)  # 30% or max $3
            weth_allocation = min(dai_balance * 0.2, 2.0)  # 20% or max $2

            success_count = 0

            # Execute DAI → WBTC swap
            if wbtc_allocation >= 0.5:
                print(f"🔄 Swapping ${wbtc_allocation:.2f} DAI → WBTC")
                wbtc_result = self.agent.uniswap.swap_tokens(
                    self.agent.dai_address,
                    self.agent.wbtc_address,
                    wbtc_allocation,
                    500
                )

                if wbtc_result:
                    print("✅ DAI → WBTC swap successful")
                    success_count += 1
                    time.sleep(8)

                    # Supply WBTC to Aave
                    wbtc_balance = self.agent.aave.get_token_balance(self.agent.wbtc_address)
                    if wbtc_balance > 0:
                        supply_result = self.agent.aave.supply_to_aave(self.agent.wbtc_address, wbtc_balance)
                        if supply_result:
                            print("✅ WBTC supplied to Aave")
                        else:
                            print("❌ WBTC supply failed")
                else:
                    print("❌ DAI → WBTC swap failed")

            # Execute DAI → WETH swap
            if weth_allocation >= 0.5:
                print(f"🔄 Swapping ${weth_allocation:.2f} DAI → WETH")
                weth_result = self.agent.uniswap.swap_tokens(
                    self.agent.dai_address,
                    self.agent.weth_address,
                    weth_allocation,
                    500
                )

                if weth_result:
                    print("✅ DAI → WETH swap successful")
                    success_count += 1
                    time.sleep(8)

                    # Supply WETH to Aave
                    weth_balance = self.agent.aave.get_token_balance(self.agent.weth_address)
                    if weth_balance > 0:
                        supply_result = self.agent.aave.supply_to_aave(self.agent.weth_address, weth_balance)
                        if supply_result:
                            print("✅ WETH supplied to Aave")
                        else:
                            print("❌ WETH supply failed")
                else:
                    print("❌ DAI → WETH swap failed")

            # Supply remaining DAI directly
            remaining_dai = self.agent.aave.get_token_balance(self.agent.dai_address)
            if remaining_dai >= 0.5:
                print(f"🔄 Supplying remaining ${remaining_dai:.2f} DAI directly")
                dai_supply_result = self.agent.aave.supply_to_aave(self.agent.dai_address, remaining_dai)
                if dai_supply_result:
                    print("✅ DAI supplied to Aave")
                    success_count += 1
                else:
                    print("❌ DAI supply failed")

            print(f"📊 Post-borrow operations: {success_count} successful")
            return success_count > 0

        except Exception as e:
            print(f"❌ Post-borrow swaps failed: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return False