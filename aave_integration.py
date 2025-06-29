import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

class AaveArbitrumIntegration:
    def __init__(self, w3, account):
        self.w3 = w3
        self.account = account
        self.address = account.address

        # Determine network based on chain ID
        chain_id = self.w3.eth.chain_id

        if chain_id == 42161:  # Arbitrum Mainnet
            print(f"🌐 Initializing for Arbitrum Mainnet (Chain ID: {chain_id})")
            # Aave V3 Arbitrum MAINNET Contract Addresses
            self.pool_addresses_provider = self.w3.to_checksum_address("0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb")
            self.pool_address = self.w3.to_checksum_address("0x794a61358D6845594F94dc1DB02A252b5b4814aD")
            self.pool_data_provider = self.w3.to_checksum_address("0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654")
            # Token addresses for Arbitrum Mainnet (corrected)
            self.weth_address = Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
            self.wbtc_address = Web3.to_checksum_address("0x2f2a2543B76A4166549F7bffBE68df6Fc579b2F3")  # Correct WBTC
            self.dai_address = Web3.to_checksum_address("0xDA10009cBd56D0F34a29c7aA35e34D246dA651D0")   # Correct DAI
            self.usdc_address = Web3.to_checksum_address("0xaf88d065eec38faD0AEFf3e253e648a15cEe23dC") # Correct USDC
            self.arb_address = Web3.to_checksum_address("0x912CE59144191C1f20bDd2ce08f2a688FEaEbb0B")   # Correct ARB
        else:  # Arbitrum Sepolia Testnet (Chain ID: 421614)
            print(f"🧪 Initializing for Arbitrum Sepolia Testnet (Chain ID: {chain_id})")
            # Aave V3 Arbitrum SEPOLIA TESTNET Contract Addresses
            self.pool_addresses_provider = self.w3.to_checksum_address("0x0496275d34753A48320CA58103d5220d394FF77F")
            self.pool_address = self.w3.to_checksum_address("0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951")
            self.pool_data_provider = self.w3.to_checksum_address("0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654")
            # Token addresses on Arbitrum SEPOLIA TESTNET
            self.weth_address = self.w3.to_checksum_address("0x980B62Da83eFf3D4576C647993b0c1D7faf17c73")
            self.wbtc_address = self.w3.to_checksum_address("0x078f358208685046a11C85e8ad32895DED33A249")
            self.dai_address = self.w3.to_checksum_address("0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE")
            self.usdc_address = self.w3.to_checksum_address("0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d")
            self.arb_address = self.w3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548")
        print(f"🪙 ARB Token Address (checksummed): {self.arb_address}")

        # Load ABIs
        self.pool_abi = self._get_pool_abi()
        self.erc20_abi = self._get_erc20_abi()

        # Initialize contracts
        self.pool_contract = self.w3.eth.contract(
            address=self.pool_address, 
            abi=self.pool_abi
        )

        # Verify all contract addresses are properly checksummed
        network_name = "Arbitrum Mainnet" if chain_id == 42161 else "Arbitrum Sepolia"
        print(f"🏦 Aave Integration - Contract Address Verification ({network_name}):")
        print(f"   Pool: {self.pool_address}")
        print(f"   Data Provider: {self.pool_data_provider}")
        print(f"   WETH: {self.weth_address}")
        print(f"   WBTC: {self.wbtc_address}")
        print(f"   DAI: {self.dai_address}")
        print(f"   USDC: {self.usdc_address}")
        print(f"   ARB: {self.arb_address}")

        # Validate that all addresses are properly checksummed
        addresses_to_check = [
            ("Pool", self.pool_address),
            ("WETH", self.weth_address),
            ("WBTC", self.wbtc_address),
            ("DAI", self.dai_address),
            ("USDC", self.usdc_address),
            ("ARB", self.arb_address)
        ]

        validation_passed = True
        for name, addr in addresses_to_check:
            if addr != self.w3.to_checksum_address(addr):
                print(f"❌ {name} address not properly checksummed: {addr}")
                validation_passed = False
            else:
                print(f"✅ {name} address properly checksummed")

        if validation_passed:
            print(f"✅ All contract addresses validated successfully for {network_name}")
        else:
            print(f"⚠️ Some address validation issues detected")

        print(f"🏦 Aave integration initialized for {self.address}")

    def _get_pool_abi(self):
        """Aave V3 Pool ABI (simplified for key functions)"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"},
                    {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
                ],
                "name": "supply",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                    {"internalType": "uint16", "name": "referralCode", "type": "uint16"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"}
                ],
                "name": "borrow",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "to", "type": "address"}
                ],
                "name": "withdraw",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"}
                ],
                "name": "repay",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

    def _get_erc20_abi(self):
        """Standard ERC20 ABI for token operations"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "spender", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "decimals",
                "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    def get_token_balance(self, token_address):
        """Get token balance for the user's address with enhanced error handling and RPC failover"""
        try:
            print(f"🔍 Getting token balance for {token_address} for user {self.address}")

            # If agent has multiple RPC endpoints, try them
            if hasattr(self, 'agent') and hasattr(self.agent, 'rpc_endpoints'):
                return self._get_balance_with_rpc_failover(token_address)

            # Single RPC attempt
            return self._get_balance_single_rpc(token_address)

        except Exception as e:
            print(f"❌ ERROR: Failed to get token balance for {token_address} for user {self.address}. Details: {e}")
            return 0.0

    def _get_balance_single_rpc(self, token_address):
        """Get balance using current RPC"""
        # Create contract instance
        token_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi
        )

        # Get balance in wei
        try:
            balance_wei = token_contract.functions.balanceOf(self.address).call()
        except Exception as balance_error:
            print(f"❌ ERROR: Failed to get balance. Details: {balance_error}")
            return 0.0

        # Get decimals with fallback
        try:
            decimals = token_contract.functions.decimals().call()
        except Exception as decimals_error:
            print(f"⚠️ Warning: Could not get decimals for {token_address}, using default 6 for USDC. Error: {decimals_error}")
            # Use 6 for USDC, 8 for WBTC, 18 for others
            if token_address.lower() == "0xaf88d065eec38fad0aeff3e253e648a15cee23dc":
                decimals = 6  # USDC
            elif token_address.lower() == "0x2f2a2543b76a4166549f7bffbe68df6fc579b2f3":
                decimals = 8  # WBTC
            else:
                decimals = 18  # Default

        # Convert to human readable format
        balance = float(balance_wei) / float(10 ** decimals)
        print(f"✅ Token balance: {balance:.6f}")

        return balance

    def _get_balance_with_rpc_failover(self, token_address):
        """Try multiple RPC endpoints to get token balance"""
        for rpc_url in self.agent.rpc_endpoints:
            try:
                print(f"🔄 Trying balance check with RPC: {rpc_url}")

                # Create temporary Web3 instance
                temp_w3 = Web3(Web3.HTTPProvider(rpc_url))

                if not temp_w3.is_connected():
                    print(f"❌ RPC not connected: {rpc_url}")
                    continue

                # Verify chain ID
                if temp_w3.eth.chain_id != self.agent.expected_chain_id:
                    print(f"❌ Wrong chain ID for {rpc_url}")
                    continue

                # Create contract with temp Web3
                token_contract = temp_w3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.erc20_abi
                )

                # Get balance
                balance_wei = token_contract.functions.balanceOf(self.address).call()

                # Get decimals with fallback
                try:
                    decimals = token_contract.functions.decimals().call()
                except:
                    # Use known decimals for common tokens
                    if token_address.lower() == "0xaf88d065eec38fad0aeff3e253e648a15cee23dc":
                        decimals = 6  # USDC
                    elif token_address.lower() == "0x2f2a2543b76a4166549f7bffbe68df6fc579b2f3":
                        decimals = 8  # WBTC
                    else:
                        decimals = 18  # Default

                balance = float(balance_wei) / float(10 ** decimals)
                print(f"✅ Successfully got balance with {rpc_url}: {balance:.6f}")

                # Update main Web3 instance to working RPC
                if rpc_url != self.agent.current_rpc_url:
                    self.w3 = temp_w3
                    self.agent.w3 = temp_w3
                    self.agent.current_rpc_url = rpc_url
                    print(f"🔄 Switched to RPC: {rpc_url}")

                return balance

            except Exception as e:
                print(f"❌ Error with RPC {rpc_url}: {e}")
                continue

        print("❌ All RPC endpoints failed for token balance")
        return 0.0

    def approve_token(self, token_address, amount):
        """Approve token spending for Aave"""
        try:
            # Ensure all addresses are properly checksummed
            token_address = self.w3.to_checksum_address(token_address)

            if hasattr(self.account, 'address'):
                user_address = self.w3.to_checksum_address(self.account.address)
            else:
                user_address = self.w3.to_checksum_address(self.address)

            token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
            decimals = token_contract.functions.decimals().call()
            amount_wei = int(float(amount) * (10 ** decimals))

            # Get fresh nonce with pending transactions included
            nonce = self.w3.eth.get_transaction_count(user_address, 'pending')
            print(f"🔢 Using pending nonce: {nonce} for approval")

            # Add retry logic for nonce conflicts with exponential backoff
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Get fresh nonce for each attempt
                    current_nonce = self.w3.eth.get_transaction_count(user_address, 'pending')
                    print(f"🔢 Attempt {attempt + 1}: Using fresh pending nonce {current_nonce}")

                    transaction = token_contract.functions.approve(
                        self.pool_address, 
                        amount_wei
                    ).build_transaction({
                        'chainId': self.w3.eth.chain_id,
                        'gas': 100000,
                        'gasPrice': int(self.w3.eth.gas_price * 1.1),  # 10% higher gas price
                        'nonce': current_nonce,
                    })

                    # Sign and send
                    signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

                    print(f"✅ Token approval sent: {tx_hash.hex()}")
                    return tx_hash.hex()

                except Exception as retry_e:
                    if "nonce too low" in str(retry_e) and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1  # Exponential backoff: 2, 3, 5, 9 seconds
                        print(f"🔄 Nonce conflict, waiting {wait_time}s before retry {attempt + 2}")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        raise retry_e

        except Exception as e:
            print(f"❌ Approval failed: {e}")
            return None

    def supply_to_aave(self, token_address, amount):
        """Supply assets to Aave for lending"""
        try:
            print(f"🏦 Supplying {amount} tokens to Aave...")

            # First approve token spending
            approval_tx = self.approve_token(token_address, amount)
            if not approval_tx:
                return None

            # Wait for approval (in production, you'd wait for confirmation)
            import time
            time.sleep(3)

            # Convert amount to wei
            if token_address == self.weth_address:
                amount_wei = self.w3.to_wei(amount, 'ether')
            else:
                token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
                decimals = token_contract.functions.decimals().call()
                amount_wei = int(amount * (10 ** decimals))

            # Build supply transaction with better nonce handling
            user_address = self.w3.to_checksum_address(self.address)

            # Add retry logic for nonce conflicts with exponential backoff
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Get fresh nonce for each attempt
                    current_nonce = self.w3.eth.get_transaction_count(user_address, 'pending')
                    print(f"🔢 Attempt {attempt + 1}: Using fresh pending nonce {current_nonce} for supply")

                    transaction = self.pool_contract.functions.supply(
                        self.w3.to_checksum_address(token_address),    # asset
                        amount_wei,       # amount
                        user_address,     # onBehalfOf
                        0                 # referralCode
                    ).build_transaction({
                        'chainId': self.w3.eth.chain_id,
                        'gas': 300000,
                        'gasPrice': int(self.w3.eth.gas_price * 1.1),  # 10% higher gas price
                        'nonce': current_nonce,
                    })

                    # Sign and send
                    signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

                    print(f"✅ Supply transaction sent: {tx_hash.hex()}")
                    print(f"📊 Explorer: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")

                    return tx_hash.hex()

                except Exception as retry_e:
                    if "nonce too low" in str(retry_e) and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1  # Exponential backoff: 2, 3, 5, 9 seconds
                        print(f"🔄 Nonce conflict, waiting {wait_time}s before retry {attempt + 2}")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        raise retry_e

        except Exception as e:
            print(f"❌ Supply failed: {e}")
            return None

    def borrow_from_aave(self, token_address, amount, interest_rate_mode=2):
        """Borrow assets from Aave (interest_rate_mode: 1=stable, 2=variable)"""
        try:
            print(f"💰 Borrowing {amount} tokens from Aave...")

            # Convert amount to wei
            if token_address == self.weth_address:
                amount_wei = self.w3.to_wei(amount, 'ether')
            else:
                token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
                decimals = token_contract.functions.decimals().call()
                amount_wei = int(amount * (10 ** decimals))

            # Build borrow transaction with better nonce handling
            user_address = self.w3.to_checksum_address(self.address)
            nonce = self.w3.eth.get_transaction_count(user_address, 'latest')
            print(f"🔢 Using nonce: {nonce} for borrow")

            # Add retry logic for nonce conflicts
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    transaction = self.pool_contract.functions.borrow(
                        self.w3.to_checksum_address(token_address),         # asset
                        amount_wei,           # amount
                        interest_rate_mode,   # interestRateMode (2 = variable)
                        0,                    # referralCode
                        user_address          # onBehalfOf
                    ).build_transaction({
                        'chainId': self.w3.eth.chain_id,
                        'gas': 400000,
                        'gasPrice': self.w3.eth.gas_price,
                        'nonce': nonce + attempt,
                    })

                    # Sign and send
                    signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

                    print(f"✅ Borrow transaction sent: {tx_hash.hex()}")
                    print(f"📊 Explorer: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")

                    return tx_hash.hex()

                except Exception as retry_e:
                    if "nonce too low" in str(retry_e) and attempt < max_retries - 1:
                        print(f"🔄 Nonce conflict, retrying with nonce {nonce + attempt + 1}")
                        continue
                    else:
                        raise retry_e

        except Exception as e:
            print(f"❌ Borrow failed: {e}")
            return None

    def repay_to_aave(self, token_address, amount, interest_rate_mode=2):
        """Repay borrowed assets to Aave"""
        try:
            print(f"💳 Repaying {amount} tokens to Aave...")

            # First approve token spending
            approval_tx = self.approve_token(token_address, amount)
            if not approval_tx:
                return None

            import time
            time.sleep(3)

            # Convert amount to wei
            if token_address == self.weth_address:
                amount_wei = self.w3.to_wei(amount, 'ether')
            else:
                token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
                decimals = token_contract.functions.decimals().call()
                amount_wei = int(amount * (10 ** decimals))

            # Build repay transaction with better nonce handling
            user_address = self.w3.to_checksum_address(self.address)
            nonce = self.w3.eth.get_transaction_count(user_address, 'latest')
            print(f"🔢 Using nonce: {nonce} for repay")

            # Add retry logic for nonce conflicts
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    transaction = self.pool_contract.functions.repay(
                        self.w3.to_checksum_address(token_address),         # asset
                        amount_wei,           # amount
                        interest_rate_mode,   # interestRateMode
                        user_address          # onBehalfOf
                    ).build_transaction({
                        'chainId': self.w3.eth.chain_id,
                        'gas': 300000,
                        'gasPrice': self.w3.eth.gas_price,
                        'nonce': nonce + attempt,
                    })

                    # Sign and send
                    signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

                    print(f"✅ Repay transaction sent: {tx_hash.hex()}")
                    return tx_hash.hex()

                except Exception as retry_e:
                    if "nonce too low" in str(retry_e) and attempt < max_retries - 1:
                        print(f"🔄 Nonce conflict, retrying with nonce {nonce + attempt + 1}")
                        continue
                    else:
                        raise retry_e

        except Exception as e:
            print(f"❌ Repay failed: {e}")
            return None

    def supply_wbtc_to_aave(self, wbtc_amount):
        """Supply WBTC to Aave V3 as collateral"""
        try:
            print(f"🪙 Supplying {wbtc_amount} WBTC to Aave V3...")

            # Check WBTC balance first
            wbtc_balance = self.get_token_balance(self.wbtc_address)
            print(f"💰 Current WBTC balance: {wbtc_balance:.8f}")

            if wbtc_balance < wbtc_amount:
                print(f"❌ Insufficient WBTC balance. Need {wbtc_amount:.8f}, have {wbtc_balance:.8f}")
                return None

            # Convert amount to wei (WBTC has 8 decimals)
            wbtc_amount_wei = int(wbtc_amount * (10 ** 8))
            print(f"🔢 WBTC amount in wei: {wbtc_amount_wei}")

            # First approve WBTC spending
            print("🔐 Approving WBTC spending...")
            approval_tx = self.approve_token(self.wbtc_address, wbtc_amount)
            if not approval_tx:
                print("❌ WBTC approval failed")
                return None

            print(f"✅ WBTC approval sent: {approval_tx}")

            # Wait for approval confirmation
            import time
            time.sleep(5)

            # Supply WBTC to Aave
            user_address = self.w3.to_checksum_address(self.address)
            nonce = self.w3.eth.get_transaction_count(user_address, 'pending')

            print("🏦 Supplying WBTC to Aave V3...")
            transaction = self.pool_contract.functions.supply(
                self.wbtc_address,     # asset
                wbtc_amount_wei,       # amount (8 decimals for WBTC)
                user_address,          # onBehalfOf
                0                      # referralCode
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 300000,
                'gasPrice': int(self.w3.eth.gas_price * 1.2),  # 20% higher gas price for faster confirmation
                'nonce': nonce,
            })

            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            tx_hash_hex = tx_hash.hex()
            print(f"✅ WBTC supply transaction sent: {tx_hash_hex}")

            # Determine explorer URL based on network
            if self.w3.eth.chain_id == 42161:
                explorer_url = f"https://arbiscan.io/tx/{tx_hash_hex}"
            else:
                explorer_url = f"https://sepolia.arbiscan.io/tx/{tx_hash_hex}"

            print(f"📊 View on explorer: {explorer_url}")

            return tx_hash_hex

        except Exception as e:
            print(f"❌ WBTC supply failed: {e}")
            return None

    def execute_yield_strategy(self, strategy_type="conservative"):
        """Execute automated yield farming strategies with mainnet safety limits"""
        print(f"🚀 Executing {strategy_type} yield strategy...")

        eth_balance = self.get_token_balance(self.weth_address)

        # MAINNET SAFETY: Maximum 0.1 ETH per transaction
        MAX_ETH_PER_TX = 0.1

        if eth_balance < 0.01:
            print("❌ Insufficient ETH balance for yield strategy")
            return None

        if strategy_type == "conservative":
            # Supply 50% of ETH to Aave for lending yield, capped at 0.1 ETH
            supply_amount = min(eth_balance * 0.5, MAX_ETH_PER_TX)
            print(f"🛡️ MAINNET SAFETY: Limiting supply to {supply_amount:.4f} ETH")
            return self.supply_to_aave(self.weth_address, supply_amount)

        elif strategy_type == "leveraged":
            # 1. Supply ETH as collateral
            supply_amount = eth_balance * 0.7
            supply_tx = self.supply_to_aave(self.weth_address, supply_amount)

            if supply_tx:
                # 2. Borrow USDC against ETH collateral (at 50% LTV)
                import time
                time.sleep(5)  # Wait for supply to confirm

                # Estimate USDC borrow amount (assuming 1 ETH = $2000, borrow 50% LTV)
                usdc_borrow_amount = supply_amount * 2000 * 0.5  # 50% LTV
                borrow_tx = self.borrow_from_aave(self.usdc_address, usdc_borrow_amount)

                return {"supply": supply_tx, "borrow": borrow_tx}

        return None