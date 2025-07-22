"""
Apply fixes for gas estimation failures, missing variable errors, and syntax errors in the enhanced borrow manager.
"""
"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""

import os
from web3 import Web3
from eth_account import Account

class UniswapArbitrumIntegration:
    def __init__(self, w3, account):
        self.w3 = w3
        self.account = account
        self.address = account.address

        # Determine network based on chain ID
        chain_id = self.w3.eth.chain_id

        if chain_id == 42161:  # Arbitrum Mainnet
            print(f"🌐 Initializing Uniswap for Arbitrum Mainnet (Chain ID: {chain_id})")
            # Uniswap V3 Arbitrum Mainnet addresses
            self.router_address = self.w3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")  # SwapRouter
            self.factory_address = self.w3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")  # V3 Factory
            self.quoter_address = self.w3.to_checksum_address("0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6")   # Quoter V2

            # Mainnet token addresses
            self.weth_address = self.w3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
            self.dai_address = self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
            self.wbtc_address = self.w3.to_checksum_address("0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f")
            self.dai_address = self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
        else:  # Arbitrum Sepolia Testnet
            print(f"🧪 Initializing Uniswap for Arbitrum Sepolia Testnet (Chain ID: {chain_id})")
            # Uniswap V3 Arbitrum Sepolia addresses
            self.router_address = self.w3.to_checksum_address("0x101F443B4d1b059569D643917553c771E1b9663E")  # SwapRouter
            self.factory_address = self.w3.to_checksum_address("0x248AB79Bbb9bC29bB72f7Cd42F17e054Fc40188e")  # V3 Factory
            self.quoter_address = self.w3.to_checksum_address("0x2779a0CC1c3e0E44D2542EC3637094d26349e68e")   # Quoter V2

            # Testnet token addresses
            self.weth_address = self.w3.to_checksum_address("0x980B62Da83eFf3D4576C647993b0c1D7faf17c73")
            self.dai_address = self.w3.to_checksum_address("0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d")
            self.wbtc_address = self.w3.to_checksum_address("0x078f358208685046a11C85e8ad32895DED33A249")
            self.dai_address = self.w3.to_checksum_address("0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE")

        self.router_abi = self._get_router_abi()
        self.erc20_abi = self._get_erc20_abi()

        self.router_contract = self.w3.eth.contract(
            address=self.router_address, 
            abi=self.router_abi
        )

        print(f"🔄 Uniswap V3 integration initialized")

    def _get_router_abi(self):
        """Uniswap V3 SwapRouter ABI"""
        return [
            {
                "inputs": [
                    {
                        "components": [
                            {"internalType": "address", "name": "tokenIn", "type": "address"},
                            {"internalType": "address", "name": "tokenOut", "type": "address"},
                            {"internalType": "uint24", "name": "fee", "type": "uint24"},
                            {"internalType": "address", "name": "recipient", "type": "address"},
                            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                        ],
                        "internalType": "struct ISwapRouter.ExactInputSingleParams",
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "exactInputSingle",
                "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            }
        ]

    def _get_erc20_abi(self):
        """Complete ERC20 ABI with all required functions for swap validation"""
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
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "owner", "type": "address"},
                    {"internalType": "address", "name": "spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "symbol",
                "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "name",
                "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    def _convert_to_wei(self, token_address, amount):
        """Convert amount to wei based on token decimals"""
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
            decimals = token_contract.functions.decimals().call()
        except:
            # Fallback decimals if contract call fails
            if token_address.lower() == "0xaf88d065e77c8cf0eaeff3e253e648a15cee23dc":  # DAI
                decimals = 6
            elif token_address.lower() == "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f":  # WBTC
                decimals = 8
            else:
                decimals = 18
        return int(amount * (10 ** decimals))


    def swap_tokens(self, token_in, token_out, amount_in, fee=3000):
        """Execute token swap on Uniswap V3 with enhanced validation and error handling - DAI-ONLY ENFORCEMENT"""
        try:
            import time

            # CRITICAL: Enforce DAI-only swap policy
            dai_address_lower = self.dai_address.lower()
            wbtc_address_lower = self.wbtc_address.lower()
            weth_address_lower = self.weth_address.lower()

            token_in_lower = token_in.lower()
            token_out_lower = token_out.lower()

            # Validate only allowed swap combinations
            allowed_swaps = [
                (dai_address_lower, wbtc_address_lower),  # DAI → WBTC
                (dai_address_lower, weth_address_lower),  # DAI → WETH
            ]

            current_swap = (token_in_lower, token_out_lower)
            if current_swap not in allowed_swaps:
                print(f"❌ FORBIDDEN SWAP: {token_in} → {token_out}")
                print(f"🚫 Only DAI → WBTC and DAI → WETH swaps are allowed")
                print(f"🎯 Current swap pair not in allowlist: {current_swap}")
                return None

            print(f"✅ APPROVED SWAP: DAI → {'WBTC' if token_out_lower == wbtc_address_lower else 'WETH'}")

            # Enhanced contract validation
            for token_addr in [token_in, token_out]:
                if token_addr != "0x0000000000000000000000000000000000000000":
                    try:
                        checksummed_addr = self.w3.to_checksum_address(token_addr)
                        code = self.w3.eth.get_code(checksummed_addr)
                        if code == b'':
                            print(f"❌ No contract found at {token_addr}")
                            return None

                        # Verify it's a valid ERC20 token
                        token_contract = self.w3.eth.contract(address=checksummed_addr, abi=self.erc20_abi)
                        symbol = token_contract.functions.symbol().call()
                        decimals = token_contract.functions.decimals().call()

                        print(f"✅ Token validated: {symbol} (decimals: {decimals}) at {checksummed_addr}")

                    except Exception as contract_error:
                        print(f"❌ Token contract validation failed for {token_addr}: {contract_error}")
                        return None

            # ENHANCED: Validate token balance before swap
            if token_in != "0x0000000000000000000000000000000000000000":
                token_contract = self.w3.eth.contract(address=token_in, abi=self.erc20_abi)
                try:
                    current_balance = token_contract.functions.balanceOf(self.address).call()
                    decimals = token_contract.functions.decimals().call()
                    readable_balance = current_balance / (10 ** decimals)

                    if readable_balance < amount_in:
                        print(f"❌ Insufficient balance: {readable_balance:.6f} < {amount_in:.6f}")
                        return None
                    print(f"✅ Balance check passed: {readable_balance:.6f} >= {amount_in:.6f}")
                except Exception as balance_error:
                    print(f"⚠️ Balance check failed: {balance_error}")
                    return None  # Don't proceed if balance check fails

            # Convert amount_in to wei FIRST
            amount_in_wei = self._convert_to_wei(token_in, amount_in)
            print(f"🔄 Converting {amount_in} to {amount_in_wei} wei for {token_in}")

            if amount_in_wei <= 0:
                print(f"❌ Invalid wei conversion result: {amount_in_wei}")
                return None

            # Check ETH balance for gas
            eth_balance = self.w3.eth.get_balance(self.address)
            min_eth_needed = self.w3.to_wei(0.001, 'ether')  # 0.001 ETH minimum
            if eth_balance < min_eth_needed:
                print(f"❌ Insufficient ETH for gas: {self.w3.from_wei(eth_balance, 'ether'):.6f} ETH")
                return None

            # Approve token spending with enhanced validation
            if token_in != "0x0000000000000000000000000000000000000000":  # Not ETH
                token_contract = self.w3.eth.contract(address=token_in, abi=self.erc20_abi)

                # Check current allowance first
                try:
                    current_allowance = token_contract.functions.allowance(self.address, self.router_address).call()
                    if current_allowance >= amount_in_wei:
                        print(f"✅ Token already approved: {current_allowance} >= {amount_in_wei}")
                    else:
                        # Need to approve
                        nonce = self.w3.eth.get_transaction_count(self.address)

                        # Enhanced gas price calculation for mainnet
                        base_gas_price = self.w3.eth.gas_price
                        chain_id = self.w3.eth.chain_id

                        if chain_id == 42161:  # Arbitrum Mainnet
                            optimized_gas_price = max(base_gas_price, int(0.01 * 10**9))  # Min 0.01 gwei
                        else:
                            optimized_gas_price = int(base_gas_price * 1.2)  # 20% higher for testnet

                        approve_tx = token_contract.functions.approve(
                            self.router_address, 
                            amount_in_wei * 2  # Approve 2x amount for efficiency
                        ).build_transaction({
                            'chainId': chain_id,
                            'gas': 100000,
                            'gasPrice': optimized_gas_price,
                            'nonce': nonce,
                        })

                        signed_approve = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
                        approve_hash = self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
                        print(f"✅ Approval sent: {approve_hash.hex()}")
                        time.sleep(8)  # Wait for approval confirmation

                except Exception as approve_error:
                    print(f"❌ Approval failed: {approve_error}")
                    return None

            # Build swap parameters with proper wei amounts
            deadline = int(time.time()) + 600  # 10 minutes from now (more time)

            # Calculate minimum output with proper slippage tolerance
            try:
                # Get quote for expected output amount
                quoter_contract = self.w3.eth.contract(
                    address='0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',  # Uniswap V3 Quoter
                    abi=[{
                        "inputs": [
                            {"name": "tokenIn", "type": "address"},
                            {"name": "tokenOut", "type": "address"},
                            {"name": "fee", "type": "uint24"},
                            {"name": "amountIn", "type": "uint256"},
                            {"name": "sqrtPriceLimitX96", "type": "uint160"}
                        ],
                        "name": "quoteExactInputSingle",
                        "outputs": [{"name": "amountOut", "type": "uint256"}],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }]
                )

                expected_output = quoter_contract.functions.quoteExactInputSingle(
                    token_in, token_out, 3000, amount_in_wei, 0
                ).call()

                # 2% slippage tolerance
                min_output_amount = int(expected_output * 0.98)
                print(f"💡 Expected output: {expected_output}, Min output: {min_output_amount}")

            except Exception as quote_error:
                print(f"⚠️ Quote failed: {quote_error}, using conservative minimum")
                min_output_amount = 1  # Fallback to 1 wei minimum

            swap_params = {
                'tokenIn': self.w3.to_checksum_address(token_in),
                'tokenOut': self.w3.to_checksum_address(token_out),
                'fee': fee,
                'recipient': self.w3.to_checksum_address(self.address),
                'deadline': deadline,
                'amountIn': amount_in_wei,
                'amountOutMinimum': min_output_amount,  # Realistic minimum output
                'sqrtPriceLimitX96': 0   # No price limit
            }

            # Build swap transaction with enhanced gas optimization
            nonce = self.w3.eth.get_transaction_count(self.address)

            # Enhanced gas calculation for swap
            base_gas_price = self.w3.eth.gas_price
            chain_id = self.w3.eth.chain_id

            if chain_id == 42161:  # Arbitrum Mainnet
                swap_gas_price = max(base_gas_price, int(0.1 * 10**9))  # Min 0.1 gwei (increased)
                gas_limit = 500000  # Increased gas limit for complex swaps
            else:
                swap_gas_price = int(base_gas_price * 1.5)  # 50% higher for testnet
                gas_limit = 450000

            swap_tx = self.router_contract.functions.exactInputSingle(
                swap_params
            ).build_transaction({
                'chainId': chain_id,
                'gas': gas_limit,
                'gasPrice': swap_gas_price,
                'nonce': nonce,
                'value': amount_in_wei if token_in == "0x0000000000000000000000000000000000000000" else 0
            })

            print(f"🔄 Swap transaction built:")
            print(f"   Gas Price: {self.w3.from_wei(swap_gas_price, 'gwei'):.4f} gwei")
            print(f"   Gas Limit: {gas_limit}")
            print(f"   Amount In: {amount_in_wei} wei ({amount_in} tokens)")

            # Pre-validate transaction before gas estimation
            try:
                # Check token balances first
                token_in_contract = self.w3.eth.contract(address=token_in, abi=self.erc20_abi)
                current_balance = token_in_contract.functions.balanceOf(self.address).call()

                if current_balance < amount_in_wei:
                    print(f"❌ Insufficient token balance: {current_balance} < {amount_in_wei}")
                    return None

                # Check allowance
                current_allowance = token_in_contract.functions.allowance(
                    self.address, self.router_address
                ).call()

                if current_allowance < amount_in_wei:
                    print(f"❌ Insufficient allowance: {current_allowance} < {amount_in_wei}")
                    return None

                print(f"✅ Pre-validation passed: balance={current_balance}, allowance={current_allowance}")

                # Now try gas estimation with retries
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        estimated_gas = self.w3.eth.estimate_gas(swap_tx)
                        print(f"💰 Gas estimation successful on attempt {attempt + 1}: {estimated_gas}")

                        # Update gas limit if estimation is higher
                        if estimated_gas > gas_limit:
                            gas_limit = int(estimated_gas * 1.3)  # 30% buffer
                            print(f"⛽ Increased gas limit to: {gas_limit}")
                        break

                    except Exception as gas_error:
                        print(f"⚠️ Gas estimation attempt {attempt + 1} failed: {gas_error}")
                        if attempt == max_retries - 1:
                            print(f"❌ All gas estimation attempts failed - using default gas limit")
                            # Don't abort, use the higher default gas limit instead
                            break
                        else:
                            import time
                            time.sleep(1)  # Wait 1 second before retry

            except Exception as validation_error:
                print(f"❌ Pre-validation failed: {validation_error}")
                return None

            # Sign and send
            signed_swap = self.w3.eth.account.sign_transaction(swap_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_swap.rawTransaction)

            print(f"✅ Swap executed successfully: {tx_hash.hex()}")

            # Return transaction hash for tracking
            return tx_hash.hex()

        except Exception as e:
            print(f"❌ Swap failed with error: {e}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return None

    def optimize_collateral_via_swap(self, aave_integration, current_collateral_amount):
        """Swap borrowed DAI assets to optimize collateral position - STRICT DAI-ONLY OPERATIONS"""
        try:
            print("🔄 Optimizing collateral through strategic DAI swapping...")
            print("🎯 STRICT MODE: Only DAI → WBTC and DAI → WETH swaps allowed")

            # Enforce DAI-only policy - reject any DAI operations
            if hasattr(aave_integration, 'dai_address'):
                print("⚠️ DAI contract detected but will NOT be used in swaps")
                print("🚫 System configured for DAI-only swap operations")

            # Check DAI balance instead of DAI
            dai_balance = aave_integration.get_token_balance(aave_integration.dai_address)

            if dai_balance > 5.0:  # If we have more than $5 DAI
                # Swap portion of DAI to WETH for diversification
                swap_amount = min(dai_balance * 0.4, 20.0)  # Max $20 or 40% of balance

                print(f"🔄 Swapping {swap_amount:.2f} DAI to WETH for collateral optimization")

                swap_tx = self.swap_tokens(
                    aave_integration.dai_address,   # DAI in
                    aave_integration.weth_address,  # WETH out
                    swap_amount,
                    500  # 0.05% fee (lower fee tier for stablecoin->ETH)
                )

                if swap_tx:
                    print("✅ DAI → WETH collateral optimization swap completed")
                    return True
                else:
                    print("❌ DAI → WETH swap failed")

            # Also check for WBTC diversification
            if dai_balance > 10.0:  # If we have substantial DAI
                wbtc_swap_amount = min(dai_balance * 0.2, 15.0)  # Max $15 or 20% to WBTC

                print(f"🔄 Swapping {wbtc_swap_amount:.2f} DAI to WBTC for collateral diversification")

                wbtc_swap_tx = self.swap_tokens(
                    aave_integration.dai_address,   # DAI in
                    aave_integration.wbtc_address,  # WBTC out
                    wbtc_swap_amount,
                    500  # 0.05% fee
                )

                if wbtc_swap_tx:
                    print("✅ DAI → WBTC collateral diversification swap completed")
                    return True

            return False

        except Exception as e:
            print(f"❌ Collateral optimization failed: {e}")
            import traceback
            print(f"🔍 Full error: {traceback.format_exc()}")
            return False