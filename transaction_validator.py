import os
import time
from web3 import Web3

class TransactionValidator:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3

    def validate_swap_transaction(self, token_in, token_out, amount_in):
        """Validate swap transaction with strict DAI-only enforcement"""
        try:
            print(f"🔍 Validating swap: {amount_in} {token_in} → {token_out}")

            # CRITICAL: Enforce DAI-only compliance
            dai_address_lower = self.agent.dai_address.lower()
            wbtc_address_lower = self.agent.wbtc_address.lower()
            weth_address_lower = self.agent.weth_address.lower()

            token_in_lower = token_in.lower()
            token_out_lower = token_out.lower()

            # Only allow DAI → WBTC and DAI → WETH swaps
            allowed_swaps = [
                (dai_address_lower, wbtc_address_lower),  # DAI → WBTC
                (dai_address_lower, weth_address_lower),  # DAI → WETH
            ]

            current_swap = (token_in_lower, token_out_lower)
            if current_swap not in allowed_swaps:
                print(f"❌ FORBIDDEN SWAP: {token_in} → {token_out}")
                print(f"🚫 Only DAI → WBTC and DAI → WETH swaps are permitted")
                print(f"🔒 DAI COMPLIANCE VIOLATION - Transaction rejected")
                return False

            print(f"✅ DAI COMPLIANCE VERIFIED: {'DAI → WBTC' if token_out_lower == wbtc_address_lower else 'DAI → WETH'}")

            # Basic validation
            if amount_in <= 0:
                print("❌ Invalid swap amount")
                return False

            # Check token contracts exist
            if not self._validate_token_contract(token_in):
                print(f"❌ Invalid token_in contract: {token_in}")
                return False

            if not self._validate_token_contract(token_out):
                print(f"❌ Invalid token_out contract: {token_out}")
                return False

            # Check DAI balance specifically
            if not self._validate_dai_balance(amount_in):
                print(f"❌ Insufficient DAI balance for swap")
                return False

            # Validate gas requirements
            if not self._validate_gas_requirements():
                print(f"❌ Insufficient gas for swap")
                return False

            print("✅ Swap transaction validation passed with DAI compliance")
            return True

        except Exception as e:
            print(f"❌ Swap validation failed: {e}")
            return False

    def validate_borrow_transaction(self, amount_usd, token_address):
        """Validate borrow transaction before execution with enhanced checks"""
        try:
            print(f"🔍 Validating borrow: ${amount_usd:.2f} of {token_address}")

            # Check 1: Token address validation
            try:
                checksummed_token = Web3.to_checksum_address(token_address)
                token_contract = self.w3.eth.contract(
                    address=checksummed_token,
                    abi=self.agent.aave.erc20_abi
                )
                token_symbol = token_contract.functions.symbol().call()
                print(f"✅ Borrow token validated: {token_symbol}")

                # Ensure we're borrowing DAI (part of system validation)
                if token_symbol.upper() != 'DAI':
                    print(f"⚠️ Warning: Borrowing {token_symbol} instead of DAI")

            except Exception as token_error:
                print(f"❌ Invalid borrow token address: {token_error}")
                return False

            # Check 2: Get account data
            account_data = self.agent.aave.get_user_account_data()
            if not account_data or not account_data.get('success', True):
                print(f"❌ Cannot get account data")
                return False

            # Check 3: Available borrow capacity
            available_borrows = account_data['availableBorrowsUSD']
            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrow capacity: ${available_borrows:.2f} < ${amount_usd:.2f}")
                return False

            # Check 4: Ensure sufficient buffer in borrow capacity
            safe_borrow_amount = available_borrows * 0.8  # Use only 80% of available
            if amount_usd > safe_borrow_amount:
                print(f"⚠️ Borrow amount exceeds safe threshold: ${amount_usd:.2f} > ${safe_borrow_amount:.2f}")
                # Allow but warn

            # Check 5: Health factor validation
            current_debt = account_data['totalDebtUSD']
            total_collateral = account_data['totalCollateralUSD']
            new_debt = current_debt + amount_usd

            if total_collateral > 0:
                # Conservative health factor calculation
                estimated_hf = (total_collateral * 0.75) / new_debt if new_debt > 0 else float('inf')

                print(f"📊 Health factor analysis:")
                print(f"   Current debt: ${current_debt:.2f}")
                print(f"   New debt: ${new_debt:.2f}")
                print(f"   Collateral: ${total_collateral:.2f}")
                print(f"   Estimated HF after borrow: {estimated_hf:.4f}")

                if estimated_hf < 1.8:  # Conservative threshold
                    print(f"❌ Health factor would be too low: {estimated_hf:.4f} < 1.8")
                    return False
                elif estimated_hf < 2.0:
                    print(f"⚠️ Health factor approaching minimum: {estimated_hf:.4f}")

            # Check 6: ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            min_eth_needed = 0.0005  # Minimum ETH for borrow transaction
            if eth_balance < min_eth_needed:
                print(f"❌ Insufficient ETH for borrow gas: {eth_balance:.6f} < {min_eth_needed}")
                return False

            # Check 7: Validate borrow amount is reasonable
            if amount_usd < 0.5:
                print(f"❌ Borrow amount too small: ${amount_usd:.2f} < $0.5")
                return False

            if amount_usd > 500:  # Large borrow safety check
                print(f"⚠️ Large borrow amount: ${amount_usd:.2f}")
                print("💡 Consider breaking into smaller borrows")

            # Check 8: Network conditions
            try:
                gas_price = self.w3.eth.gas_price
                current_block = self.w3.eth.block_number
                print(f"🌐 Network status: Block {current_block}, Gas {self.w3.from_wei(gas_price, 'gwei'):.2f} gwei")
            except Exception as network_error:
                print(f"⚠️ Could not check network conditions: {network_error}")

            print(f"✅ Comprehensive borrow validation passed")
            return True

        except Exception as e:
            print(f"❌ Borrow validation failed: {e}")
            import traceback
            print(f"🔍 Validation error details: {traceback.format_exc()}")
            return False

    def validate_supply_transaction(self, token_address, amount):
        """Validate supply transaction before execution"""
        try:
            print(f"🔍 Validating supply: {amount:.6f} tokens to {token_address}")

            # Check token balance
            balance = self.agent.aave.get_token_balance(token_address)
            if balance < amount:
                print(f"❌ Insufficient token balance: {balance:.6f} < {amount:.6f}")
                return False

            # Check ETH for gas
            eth_balance = self.agent.get_eth_balance()
            if eth_balance < 0.0005:
                print(f"❌ Insufficient ETH for supply gas: {eth_balance:.6f}")
                return False

            print(f"✅ Supply validation passed")
            return True

        except Exception as e:
            print(f"❌ Supply validation failed: {e}")
            return False

    def _validate_token_balance(self, token_address, required_amount):
        """Validate token balance"""
        try:
            if hasattr(self.agent, 'aave') and self.agent.aave:
                balance = self.agent.aave.get_token_balance(token_address)
                return balance >= required_amount
            return False
        except Exception as e:
            print(f"❌ Balance validation failed: {e}")
            return False

    def _validate_dai_balance(self, required_amount):
        """Validate DAI balance specifically for DAI-only compliance"""
        try:
            dai_balance = self.agent.aave.get_token_balance(self.agent.dai_address)
            print(f"💰 DAI Balance Check: {dai_balance:.6f} >= {required_amount:.6f}")

            if dai_balance >= required_amount:
                print(f"✅ Sufficient DAI balance for swap")
                return True
            else:
                print(f"❌ Insufficient DAI balance: {dai_balance:.6f} < {required_amount:.6f}")
                return False

        except Exception as e:
            print(f"❌ DAI balance validation failed: {e}")
            return False

    def _validate_token_contract(self, token_address: str) -> bool:
        """Validate that token contract exists and is accessible"""
        try:
            contract = self.w3.eth.contract(
                address=token_address,
                abi=[{
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                }]
            )
            symbol = contract.functions.symbol().call()
            return len(symbol) > 0
        except Exception:
            return False