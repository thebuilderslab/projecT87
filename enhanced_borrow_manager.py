"""Fix gas multipliers variable name"""
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

            # Comprehensive pre-validation
            validation_result = self._validate_borrow_conditions(amount_usd, token_address)
            if not validation_result:
                return False

            # Check ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            min_eth_required = 0.001  # Minimum ETH for gas
            if eth_balance < min_eth_required:
                print(f"❌ Insufficient ETH for gas: {eth_balance:.6f} ETH (need {min_eth_required:.3f})")
                return False

            # Execute borrow with enhanced retry logic
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    print(f"🔄 Enhanced borrow attempt {attempt + 1}/{max_attempts}")

                    # Get optimized gas parameters
                    gas_params = self.agent.get_optimized_gas_params('aave_borrow', 'market')
                    print(f"   Gas limit: {gas_params.get('gas', 'N/A')}")
                    print(f"   Gas price: {self.w3.from_wei(gas_params.get('gasPrice', 0), 'gwei'):.2f} gwei")

                    # Use the agent's Aave integration with gas params
                    result = self.aave.borrow(amount_usd, token_address)

                    if result:
                        print(f"✅ Enhanced borrow successful: {result}")
                        return result
                    else:
                        print(f"❌ Borrow attempt {attempt + 1} failed")

                except Exception as e:
                    print(f"❌ Borrow attempt {attempt + 1} error: {e}")

                    # Enhanced error handling
                    if "insufficient funds" in str(e).lower():
                        print(f"💡 Try: Add more ETH for gas fees")
                        break
                    elif "execution reverted" in str(e).lower():
                        print(f"💡 Try: Check health factor and borrowing capacity")
                        break
                    elif "nonce too low" in str(e).lower():
                        print(f"💡 RPC sync issue - trying next attempt")

                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt
                        print(f"⏱️ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)

            print(f"❌ All {max_attempts} enhanced borrow attempts failed")
            return False

        except Exception as e:
            print(f"❌ Enhanced borrow manager failed: {e}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            return False

    def _validate_borrow_conditions(self, amount_usd, token_address):
        """Validate conditions for safe borrowing with comprehensive checks"""
        try:
            print(f"🔍 Enhanced validation for ${amount_usd:.2f} borrow...")

            # Check basic parameters
            if not amount_usd or amount_usd <= 0:
                print(f"❌ Invalid borrow amount: ${amount_usd}")
                return False

            if not token_address or len(token_address) != 42:
                print(f"❌ Invalid token address: {token_address}")
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
`