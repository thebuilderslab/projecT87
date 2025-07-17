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
        Execute borrowing with multiple fallback mechanisms
        """
        print(f"🏦 Enhanced Borrow Manager: Borrowing ${amount_usd:.2f}")

        # Mechanism 1: Direct Aave integration
        result = self._try_direct_aave_borrow(amount_usd, token_address)
        if result:
            return result

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

        print("❌ All borrowing mechanisms failed")
        return None

    def _try_direct_aave_borrow(self, amount_usd, token_address):
        """Try the standard Aave integration borrow method"""
        try:
            print("🔄 Mechanism 1: Direct Aave integration")

            # Use the Aave integration's borrow method with correct parameters
            # Convert USD amount to proper token amount with decimals
            usdc_amount_proper = amount_usd  # Keep as USD amount for borrow method

            borrow_result = self.agent.aave.borrow(
                usdc_amount_proper,   # amount in USD
                token_address  # token address
            )

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

            # Try the simple borrow method
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