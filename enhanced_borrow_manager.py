#!/usr/bin/env python3
"""
Enhanced Borrow Manager
Provides multiple mechanisms for reliable borrowing operations
"""

import time
import json
from decimal import Decimal
from web3 import Web3

class EnhancedBorrowManager:
    def __init__(self, agent):
        self.agent = agent
        self.max_retries = 5
        self.retry_delay = 2

    def safe_borrow_with_fallbacks(self, amount_usd, token_address):
        """
        Execute borrowing with multiple fallback mechanisms and cooldown management
        """
        print(f"🏦 Enhanced Borrow Manager: Borrowing ${amount_usd:.2f}")
        
        # Check cooldown first
        if hasattr(self.agent, 'is_operation_in_cooldown'):
            in_cooldown, remaining_time = self.agent.is_operation_in_cooldown('borrow')
            if in_cooldown:
                print(f"⏰ Borrow operation in cooldown for {remaining_time:.0f}s")
                return None

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
        """Try the standard Aave integration borrow method"""
        try:
            print("🔄 Mechanism 1: Direct Aave integration")

            # Get optimized gas parameters first  
            gas_params = self.agent.get_optimized_gas_params('aave_borrow', 'market')
            print(f"✅ Got gas parameters: {gas_params}")

            # Try multiple borrow method signatures with correct parameter order
            if hasattr(self.agent.aave, 'borrow'):
                # Use the standard borrow method that expects USD amount
                borrow_result = self.agent.aave.borrow(amount_usd, token_address)
            else:
                raise Exception("No borrow method found in Aave integration")

            if borrow_result:
                print(f"✅ Mechanism 1 success: {borrow_result}")
                return borrow_result

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
        """Manual step-by-step borrowing process"""
        try:
            print("🔄 Mechanism 3: Manual step-by-step borrow")

            # Get token decimals
            decimals = self._get_token_decimals(token_address)
            amount_wei = int(amount_usd * (10 ** decimals))

            # Build transaction manually
            user_address = self.agent.address

            # Get fresh nonce
            nonce = self.agent.w3.eth.get_transaction_count(user_address, 'pending')

            # Build borrow transaction
            transaction = self.agent.aave.pool_contract.functions.borrow(
                Web3.to_checksum_address(token_address),
                amount_wei,
                2,  # Variable interest rate mode
                0,  # referralCode
                user_address
            ).build_transaction({
                'chainId': self.agent.w3.eth.chain_id,
                'gas': 300000,
                'gasPrice': int(self.agent.w3.eth.gas_price * 1.2),
                'nonce': nonce,
                'from': user_address
            })

            # Sign and send
            signed_txn = self.agent.w3.eth.account.sign_transaction(
                transaction, self.agent.account.key
            )
            tx_hash = self.agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            tx_hash_hex = tx_hash.hex()
            print(f"✅ Mechanism 3 success: {tx_hash_hex}")
            return tx_hash_hex

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