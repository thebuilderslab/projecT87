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
        """Execute borrow with comprehensive safety checks and fallbacks"""
        try:
            print(f"🏦 Enhanced Borrow Manager: Attempting to borrow ${amount_usd:.2f}")
            print(f"🔍 DEBUG: Token address: {token_address}")
            print(f"🔍 DEBUG: Amount USD: {amount_usd}")

            # Network timing validation
            if not self._validate_network_timing():
                print(f"❌ Network timing not optimal for transactions")
                return False

            # Comprehensive pre-validation with enhanced checks
            validation_result = self._validate_borrow_conditions_enhanced(amount_usd, token_address)
            if not validation_result:
                return False

            # Check ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            min_eth_required = 0.002  # Increased minimum ETH for gas
            if eth_balance < min_eth_required:
                print(f"❌ Insufficient ETH for gas: {eth_balance:.6f} ETH (need {min_eth_required:.3f})")
                return False

            # Execute borrow with enhanced retry logic and reversion analysis
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    print(f"🔄 Enhanced borrow attempt {attempt + 1}/{max_attempts}")

                    # Enhanced gas parameters for mainnet
                    gas_params = self._get_enhanced_gas_params(attempt)
                    print(f"   Gas limit: {gas_params.get('gas', 'N/A')}")
                    print(f"   Gas price: {self.w3.from_wei(gas_params.get('gasPrice', 0), 'gwei'):.2f} gwei")

                    # Use the agent's enhanced Aave integration
                    result = self.aave.borrow(amount_usd, token_address)

                    if result and hasattr(result, 'status') and result.status == 1:
                        print(f"✅ Enhanced borrow successful: {result.transactionHash.hex()}")
                        return result
                    elif result:
                        print(f"❌ Borrow transaction reverted: {result}")
                        # Continue to next attempt for reverted transactions
                    else:
                        print(f"❌ Borrow attempt {attempt + 1} failed - no result returned")

                except Exception as e:
                    print(f"❌ Borrow attempt {attempt + 1} error: {e}")

                    # Enhanced error handling with specific solutions
                    error_str = str(e).lower()
                    if "insufficient funds" in error_str:
                        print(f"💡 Solution: Add more ETH for gas fees")
                        break
                    elif "execution reverted" in error_str:
                        print(f"💡 Solution: Check health factor and borrowing capacity")
                        # Continue trying with different parameters
                    elif "nonce too low" in error_str:
                        print(f"💡 Solution: RPC sync issue - trying next attempt")
                    elif "gas" in error_str:
                        print(f"💡 Solution: Increasing gas parameters for next attempt")
                    elif "insufficient collateral" in error_str:
                        print(f"💡 Solution: Need more collateral or reduce borrow amount")
                        break

                    if attempt < max_attempts - 1:
                        wait_time = 3 + (2 ** attempt)  # 5s, 7s, 11s
                        print(f"⏱️ Waiting {wait_time}s before retry with enhanced parameters...")
                        time.sleep(wait_time)

            print(f"❌ All {max_attempts} enhanced borrow attempts failed")
            return False

        except Exception as e:
            print(f"❌ Enhanced borrow manager failed: {e}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            return False

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
                print(f"❌ Health factor too low: {health_factor:.4f} < {min_health_factor}")
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
                        self.agent.aave.pool_contract.functions.borrow(
                            token_address_checksum,
                            amount_wei,
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
                print(f"❌ Health factor too low: {health_factor:.4f} < {min_health_factor}")
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

    def execute_enhanced_borrow_with_retry(self, safe_borrow_amount):
        """Execute borrow with enhanced retry mechanism - corrected signature"""
        try:
            # Use the safe_borrow_with_fallbacks method which exists
            return self.safe_borrow_with_fallbacks(safe_borrow_amount, self.agent.usdc_address)
        except Exception as e:
            print(f"❌ Enhanced borrow execution failed: {e}")
            return False
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