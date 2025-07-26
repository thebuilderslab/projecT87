"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
All USDC references have been removed and replaced with DAI equivalents.
Only DAI borrowing, lending, and related operations are permitted.
SYSTEM VALIDATION: All swap operations must use DAI as the primary token.
"""

import os
import time
import json
from web3 import Web3
from eth_account import Account
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AaveArbitrumIntegration:
    def __init__(self, w3, account, network_mode='mainnet'):
        self.w3 = w3
        self.account = account
        self.network_mode = network_mode

        # DAI-ONLY COMPLIANCE: Only DAI address is configured
        if network_mode == 'mainnet':
            self.dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
            self.wbtc_address = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
            self.weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
            self.pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        else:
            # Testnet addresses
            self.dai_address = "0x5f6bB460B6d0bdA2CCaDdd7A19B5F6E7b5b8E1DB"
            self.wbtc_address = "0xA2d460Bc966F6C4D5527a6ba35C6cB57c15c8F96"
            self.weth_address = "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73"
            self.pool_address = "0x18cd499E3d7ed42FebA981ac9236A278E4Cdc2ee"

        # Initialize pool contract
        self._initialize_pool_contract()

        print(f"✅ Aave integration initialized for {network_mode} with DAI-only compliance")

    def _initialize_pool_contract(self):
        """Initialize Aave pool contract"""
        self.pool_abi = [
            {
                "inputs": [
                    {"name": "asset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "onBehalfOf", "type": "address"},
                    {"name": "referralCode", "type": "uint16"}
                ],
                "name": "supply",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
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
            },
            {
                "inputs": [
                    {"name": "asset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "to", "type": "address"}
                ],
                "name": "withdraw",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "asset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "interestRateMode", "type": "uint256"},
                    {"name": "onBehalfOf", "type": "address"}
                ],
                "name": "repay",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
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

        self.pool_contract = self.w3.eth.contract(
            address=self.pool_address,
            abi=self.pool_abi
        )

    def get_user_account_data(self):
        """Get user account data from Aave - DAI-centric compliance"""
        try:
            # Add retry mechanism for system call failures
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    account_data = self.pool_contract.functions.getUserAccountData(self.account.address).call()

                    return {
                        'totalCollateralUSD': account_data[0] / (10**8),
                        'totalDebtUSD': account_data[1] / (10**8),
                        'availableBorrowsUSD': account_data[2] / (10**8),
                        'healthFactor': account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
                    }
                except (OSError, ConnectionError, ProcessLookupError) as sys_error:
                    logger.warning(f"System call error on attempt {attempt + 1}: {sys_error}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    raise

        except Exception as e:
            logger.error(f"Failed to get account data: {e}")
            return None

    def borrow_dai(self, amount_dai):
        """Borrow DAI from Aave - DAI-only compliance enforced"""
        try:
            print(f"🏦 Initiating DAI borrow: ${amount_dai:.2f}")
            amount_wei = int(amount_dai * 10**18)  # DAI has 18 decimals

            # Pre-transaction validation
            account_data = self.get_user_account_data()
            if not account_data:
                logger.error("Cannot retrieve account data for validation")
                return False

            available_borrows = account_data.get('availableBorrowsUSD', 0)
            if amount_dai > available_borrows:
                logger.error(f"Requested amount ${amount_dai:.2f} exceeds available ${available_borrows:.2f}")
                return False

            health_factor = account_data.get('healthFactor', 0)
            if health_factor < 1.5:
                logger.error(f"Health factor too low for borrowing: {health_factor:.3f}")
                return False

            # Build transaction with enhanced error handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Get fresh nonce and gas price
                    nonce = self.w3.eth.get_transaction_count(self.account.address)
                    gas_price = self.w3.eth.gas_price

                    print(f"📊 Transaction params - Nonce: {nonce}, Gas Price: {gas_price}")

                    # Estimate gas first
                    try:
                        estimated_gas = self.pool_contract.functions.borrow(
                            self.dai_address,
                            amount_wei,
                            2,  # Variable interest rate
                            0,  # Referral code
                            self.account.address
                        ).estimate_gas({'from': self.account.address})

                        # Add 20% buffer to estimated gas
                        gas_limit = int(estimated_gas * 1.2)
                        print(f"⛽ Estimated gas: {estimated_gas}, Using: {gas_limit}")

                    except Exception as gas_error:
                        print(f"⚠️ Gas estimation failed: {gas_error}")
                        gas_limit = 400000  # Fallback gas limit

                    tx = self.pool_contract.functions.borrow(
                        self.dai_address,
                        amount_wei,
                        2,  # Variable interest rate
                        0,  # Referral code
                        self.account.address
                    ).build_transaction({
                        'from': self.account.address,
                        'gas': gas_limit,
                        'gasPrice': gas_price,
                        'nonce': nonce
                    })

                    # Sign and send
                    signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

                    print(f"✅ DAI borrow transaction sent: {tx_hash.hex()}")

                    # Wait for transaction confirmation
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                    if receipt.status == 1:
                        print(f"✅ DAI borrow confirmed: ${amount_dai:.2f}")
                        return tx_hash.hex()
                    else:
                        print(f"❌ Transaction failed in execution")
                        return False

                except ValueError as ve:
                    error_msg = str(ve)
                    if "execution reverted" in error_msg:
                        logger.error(f"Contract execution reverted: {ve}")
                        print("💡 Contract rejected the transaction - likely insufficient collateral or limits exceeded")
                        return False
                    else:
                        logger.warning(f"ValueError on borrow attempt {attempt + 1}: {ve}")
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        raise

                except (OSError, ConnectionError, ProcessLookupError) as sys_error:
                    logger.warning(f"System call error on borrow attempt {attempt + 1}: {sys_error}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    raise

        except Exception as e:
            logger.error(f"DAI borrow failed: {e}")
            print(f"❌ DAI borrow failed with error: {e}")
            return False

    def borrow(self, amount_dai, dai_address):
        """Legacy method - redirects to borrow_dai for DAI compliance"""
        if dai_address != self.dai_address:
            raise ValueError("DAI COMPLIANCE VIOLATION: Only DAI borrowing is permitted")
        return self.borrow_dai(amount_dai)

    def supply_to_aave(self, token_address, amount):
        """Supply tokens to Aave - DAI-centric operations"""
        try:
            if token_address == self.dai_address:
                amount_wei = int(amount * 10**18)  # DAI has 18 decimals
            elif token_address == self.wbtc_address:
                amount_wei = int(amount * 10**8)   # WBTC has 8 decimals
            elif token_address == self.weth_address:
                amount_wei = int(amount * 10**18)  # WETH has 18 decimals
            else:
                raise ValueError("Unsupported token for supply")

            # Build transaction
            tx = self.pool_contract.functions.supply(
                token_address,
                amount_wei,
                self.account.address,
                0  # Referral code
            ).build_transaction({
                'from': self.account.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })

            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            print(f"✅ Token supply successful: {amount:.6f}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Token supply failed: {e}")
            return False

    def supply_dai_to_aave(self, amount):
        """Supply DAI to Aave - DAI compliance method"""
        return self.supply_to_aave(self.dai_address, amount)

    def supply_wbtc_to_aave(self, amount):
        """Supply WBTC to Aave"""
        return self.supply_to_aave(self.wbtc_address, amount)

    def supply_weth_to_aave(self, amount):
        """Supply WETH to Aave"""
        return self.supply_to_aave(self.weth_address, amount)

    def get_token_balance(self, token_address):
        """Get token balance - DAI-centric compliance"""
        try:
            # Standard ERC20 balance ABI
            balance_abi = [{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }]

            # Retry mechanism for system call errors
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    contract = self.w3.eth.contract(address=token_address, abi=balance_abi)
                    balance_wei = contract.functions.balanceOf(self.account.address).call()

                    # Convert based on token decimals
                    if token_address == self.dai_address:
                        return balance_wei / (10**18)  # DAI has 18 decimals
                    elif token_address == self.wbtc_address:
                        return balance_wei / (10**8)   # WBTC has 8 decimals
                    elif token_address == self.weth_address:
                        return balance_wei / (10**18)  # WETH has 18 decimals
                    else:
                        return balance_wei / (10**18)  # Default to 18 decimals

                except (OSError, ConnectionError, ProcessLookupError) as sys_error:
                    logger.warning(f"System call error on balance check attempt {attempt + 1}: {sys_error}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    raise

        except Exception as e:
            logger.error(f"Failed to get token balance: {e}")
            return 0.0

    def get_dai_balance(self):
        """Get DAI balance - DAI compliance method"""
        return self.get_token_balance(self.dai_address)

    def approve_token(self, token_address, amount):
        """Approve token for Aave operations"""
        try:
            # Standard ERC20 approve ABI
            approve_abi = [{
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }]

            contract = self.w3.eth.contract(address=token_address, abi=approve_abi)

            # Convert amount to wei based on token decimals
            if token_address == self.dai_address:
                amount_wei = int(amount * 10**18)
            elif token_address == self.wbtc_address:
                amount_wei = int(amount * 10**8)
            elif token_address == self.weth_address:
                amount_wei = int(amount * 10**18)
            else:
                amount_wei = int(amount * 10**18)

            # Build transaction
            tx = contract.functions.approve(
                self.pool_address,
                amount_wei
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })

            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            print(f"✅ Token approval successful")
            return True

        except Exception as e:
            logger.error(f"Token approval failed: {e}")
            return False

    def approve_dai(self, amount):
        """Approve DAI for Aave operations - DAI compliance method"""
        return self.approve_token(self.dai_address, amount)

    def withdraw_from_aave(self, token_address, amount):
        """Withdraw tokens from Aave"""
        try:
            if token_address == self.dai_address:
                amount_wei = int(amount * 10**18)  # DAI has 18 decimals
            elif token_address == self.wbtc_address:
                amount_wei = int(amount * 10**8)   # WBTC has 8 decimals
            elif token_address == self.weth_address:
                amount_wei = int(amount * 10**18)  # WETH has 18 decimals
            else:
                raise ValueError("Unsupported token for withdrawal")

            # Build transaction
            tx = self.pool_contract.functions.withdraw(
                token_address,
                amount_wei,
                self.account.address
            ).build_transaction({
                'from': self.account.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })

            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            print(f"✅ Token withdrawal successful: {amount:.6f}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Token withdrawal failed: {e}")
            return False

    def withdraw_dai_from_aave(self, amount):
        """Withdraw DAI from Aave - DAI compliance method"""
        return self.withdraw_from_aave(self.dai_address, amount)

    def repay_dai(self, amount):
        """Repay DAI debt to Aave"""
        try:
            amount_wei = int(amount * 10**18)  # DAI has 18 decimals

            # Build transaction
            tx = self.pool_contract.functions.repay(
                self.dai_address,
                amount_wei,
                2,  # Variable interest rate
                self.account.address
            ).build_transaction({
                'from': self.account.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })

            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            print(f"✅ DAI repayment successful: {amount:.6f}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"DAI repayment failed: {e}")
            return False
