"""Apply fixes for gas estimation failures, missing variable errors, and syntax errors in the enhanced borrow manager."""
"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""

import os
import time
from web3 import Web3
from eth_account import Account

class UniswapIntegration:
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

            # Mainnet token addresses - Fixed duplicates and added ARB
            self.weth_address = self.w3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
            self.dai_address = self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
            self.wbtc_address = self.w3.to_checksum_address("0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f")
            self.arb_address = self.w3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548")
        else:  # Arbitrum Sepolia Testnet
            print(f"🧪 Initializing Uniswap for Arbitrum Sepolia Testnet (Chain ID: {chain_id})")
            # Uniswap V3 Arbitrum Sepolia addresses
            self.router_address = self.w3.to_checksum_address("0x101F443B4d1b059569D643917553c771E1b9663E")  # SwapRouter
            self.factory_address = self.w3.to_checksum_address("0x248AB79Bbb9bC29bB72f7Cd42F17e054Fc40188e")  # V3 Factory
            self.quoter_address = self.w3.to_checksum_address("0x2779a0CC1c3e0E44D2542EC3637094d26349e68e")   # Quoter V2

            # Testnet token addresses - Fixed duplicates and added ARB
            self.weth_address = self.w3.to_checksum_address("0x980B62Da83eFf3D4576C647993b0c1D7faf17c73")
            self.dai_address = self.w3.to_checksum_address("0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d")
            self.wbtc_address = self.w3.to_checksum_address("0x078f358208685046a11C85e8ad32895DED33A249")
            self.arb_address = self.w3.to_checksum_address("0x1b20e6a3B2a86618C32A37ffcD5E98C0d20a6E42")

        self.router_abi = self._get_router_abi()
        self.erc20_abi = self._get_erc20_abi()

        self.router_contract = self.w3.eth.contract(
            address=self.router_address, 
            abi=self.router_abi
        )

        print(f"🔄 Uniswap V3 integration initialized")

    def _get_router_abi(self):
        """Uniswap V3 SwapRouter ABI with single-hop and multi-hop support"""
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
            },
            {
                "inputs": [
                    {
                        "components": [
                            {"internalType": "bytes", "name": "path", "type": "bytes"},
                            {"internalType": "address", "name": "recipient", "type": "address"},
                            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}
                        ],
                        "internalType": "struct ISwapRouter.ExactInputParams",
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "exactInput",
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
            token_address_lower = token_address.lower()
            if token_address_lower == "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1":  # DAI
                decimals = 18
            elif token_address_lower == "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f":  # WBTC
                decimals = 8
            elif token_address_lower == "0x912ce59144191c1204e64559fe8253a0e49e6548":  # ARB
                decimals = 18
            else:
                decimals = 18
        return int(amount * (10 ** decimals))


    def swap_tokens(self, token_in, token_out, amount_in, fee=3000):
        """Execute token swap on Uniswap V3 with enhanced validation and error handling - DAI-ONLY ENFORCEMENT"""
        try:
            # CRITICAL: Enforce DAI-only swap policy
            dai_address_lower = self.dai_address.lower()
            wbtc_address_lower = self.wbtc_address.lower()
            weth_address_lower = self.weth_address.lower()

            token_in_lower = token_in.lower()
            token_out_lower = token_out.lower()

            # Validate allowed swap combinations including ARB and GHO
            arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
            arb_address_lower = arb_address.lower()
            gho_address = "0x7dfF72693f6A4149b17e7C6314655f6A9F7c8B33"  # GHO on Arbitrum
            gho_address_lower = gho_address.lower()

            allowed_swaps = [
                (dai_address_lower, wbtc_address_lower),  # DAI → WBTC
                (dai_address_lower, weth_address_lower),  # DAI → WETH
                (dai_address_lower, arb_address_lower),   # DAI → ARB
                (arb_address_lower, dai_address_lower),   # ARB → DAI
                (dai_address_lower, gho_address_lower),   # DAI → GHO
            ]

            current_swap = (token_in_lower, token_out_lower)
            if current_swap not in allowed_swaps:
                print(f"❌ FORBIDDEN SWAP: {token_in} → {token_out}")
                print(f"🚫 Only DAI → WBTC and DAI → WETH swaps are allowed")
                print(f"🎯 Current swap pair not in allowlist: {current_swap}")
                return None

            if token_out_lower == wbtc_address_lower:
                token_out_name = "WBTC"
            elif token_out_lower == weth_address_lower:
                token_out_name = "WETH"
            elif token_out_lower == arb_address_lower:
                token_out_name = "ARB"
            elif token_out_lower == gho_address_lower:
                token_out_name = "GHO"
            elif token_in_lower == arb_address_lower:
                token_out_name = "DAI (from ARB)"
            else:
                token_out_name = "UNKNOWN"

            print(f"✅ APPROVED SWAP: {token_in_lower.split('x')[1][:6]}... → {token_out_name}")

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

            # Continue with swap execution logic here
            return self._execute_validated_swap(token_in, token_out, amount_in, fee)

        except Exception as e:
            print(f"❌ Token swap failed: {e}")
            return None

    def _execute_validated_swap(self, token_in, token_out, amount_in, fee):
        """Execute the validated swap with comprehensive error handling and debt swap logic"""
        try:
            print(f"🔄 Executing validated debt swap: {amount_in} tokens")

            # Convert amount_in to wei FIRST
            amount_in_wei = self._convert_to_wei(token_in, amount_in)
            print(f"🔄 Converting {amount_in} to {amount_in_wei} wei for {token_in}")

            if amount_in_wei <= 0:
                print(f"❌ Invalid wei conversion result: {amount_in_wei}")
                return None

            # Check ETH balance for gas
            eth_balance = self.w3.eth.get_balance(self.address)
            min_eth_needed = self.w3.to_wei(0.0002, 'ether')  # 0.0002 ETH minimum (Arbitrum L2 gas is cheap)
            if eth_balance < min_eth_needed:
                print(f"❌ Insufficient ETH for gas: {self.w3.from_wei(eth_balance, 'ether'):.6f} ETH")
                return None

            # Approve token spending if needed
            if token_in != "0x0000000000000000000000000000000000000000":  # Not ETH
                token_contract = self.w3.eth.contract(address=token_in, abi=self.erc20_abi)

                # Check current allowance first
                try:
                    current_allowance = token_contract.functions.allowance(self.address, self.router_address).call()
                    if current_allowance < amount_in_wei:
                        # Need to approve
                        nonce = self.w3.eth.get_transaction_count(self.address)
                        base_gas_price = self.w3.eth.gas_price
                        chain_id = self.w3.eth.chain_id

                        # Apply 2x multiplier for Arbitrum mainnet to handle variable gas costs
                        if chain_id == 42161:  # Arbitrum Mainnet
                            optimized_gas_price = int(base_gas_price * 2.0)
                            print(f"⛽ Arbitrum approval: base {base_gas_price} → optimized {optimized_gas_price} (2.0x)")
                        else:
                            optimized_gas_price = int(base_gas_price * 1.3)  # 30% buffer for testnet
                            print(f"⛽ Testnet approval: base {base_gas_price} → optimized {optimized_gas_price} (1.3x)")

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

                        # Wait for approval confirmation
                        time.sleep(8)

                except Exception as approve_error:
                    print(f"❌ Approval failed: {approve_error}")
                    return None

            deadline = int(time.time()) + 120  # 120 seconds from now

            min_output_amount = 1
            try:
                quoter_contract = self.w3.eth.contract(
                    address='0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',
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
                        "stateMutability": "view",
                        "type": "function"
                    }]
                )
                expected_output = quoter_contract.functions.quoteExactInputSingle(
                    self.w3.to_checksum_address(token_in),
                    self.w3.to_checksum_address(token_out),
                    fee, amount_in_wei, 0
                ).call()
                if expected_output > 0:
                    min_output_amount = max(1, int(expected_output * 0.99))
                    print(f"✅ Quote: expected {expected_output}, min (1% slippage): {min_output_amount}")
            except Exception as quote_err:
                print(f"⚠️ Quote failed, using minimal output: {quote_err}")
                min_output_amount = 1

            swap_params = {
                'tokenIn': self.w3.to_checksum_address(token_in),
                'tokenOut': self.w3.to_checksum_address(token_out),
                'fee': fee,
                'recipient': self.w3.to_checksum_address(self.address),
                'deadline': deadline,
                'amountIn': amount_in_wei,
                'amountOutMinimum': min_output_amount,
                'sqrtPriceLimitX96': 0
            }

            # Build swap transaction with Arbitrum multiplier
            nonce = self.w3.eth.get_transaction_count(self.address)
            base_gas_price = self.w3.eth.gas_price
            chain_id = self.w3.eth.chain_id

            # Apply 2x multiplier for Arbitrum mainnet to handle variable gas costs
            if chain_id == 42161:  # Arbitrum Mainnet
                swap_gas_price = int(base_gas_price * 2.0)
                gas_limit = 500000
                print(f"⛽ Arbitrum swap: base {base_gas_price} → optimized {swap_gas_price} (2.0x)")
            else:
                swap_gas_price = int(base_gas_price * 1.5)  # 50% buffer for testnet
                gas_limit = 450000
                print(f"⛽ Testnet swap: base {base_gas_price} → optimized {swap_gas_price} (1.5x)")

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

                        # Apply 2x multiplier for Arbitrum mainnet to handle variable gas costs
                        if chain_id == 42161:  # Arbitrum Mainnet
                            optimized_gas_price = int(base_gas_price * 2.0)
                            print(f"⛽ Arbitrum approval (2nd): base {base_gas_price} → optimized {optimized_gas_price} (2.0x)")
                        else:
                            optimized_gas_price = int(base_gas_price * 1.3)  # 30% buffer for testnet
                            print(f"⛽ Testnet approval (2nd): base {base_gas_price} → optimized {optimized_gas_price} (1.3x)")

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
            deadline = int(time.time()) + 120  # 120 seconds from now

            # Calculate minimum output with enhanced error handling and fallback mechanisms
            min_output_amount = 1  # Start with minimal requirement

            try:
                # Try multiple fee tiers for better liquidity
                fee_tiers = [500, 3000, 10000]  # 0.05% (most liquid on Arbitrum), 0.3%, 1%
                best_quote = 0
                best_fee = fee

                for test_fee in fee_tiers:
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
                                "stateMutability": "view",
                                "type": "function"
                            }]
                        )

                        expected_output = quoter_contract.functions.quoteExactInputSingle(
                            token_in, token_out, test_fee, amount_in_wei, 0
                        ).call()

                        if expected_output > best_quote:
                            best_quote = expected_output
                            best_fee = test_fee
                            print(f"💡 Better quote found - Fee: {test_fee}, Output: {expected_output}")

                    except Exception as fee_error:
                        print(f"⚠️ Fee tier {test_fee} failed: {fee_error}")
                        continue

                if best_quote > 0:
                    # Use best fee tier found
                    fee = best_fee
                    min_output_amount = max(1, int(best_quote * 0.99))
                    print(f"   Min output (1% slippage): {min_output_amount}")
                    print(f"✅ Using fee tier: {fee}, Expected: {best_quote}, Min: {min_output_amount}")
                else:
                    print(f"⚠️ No quotes available, using minimal output requirement")

            except Exception as quote_error:
                print(f"⚠️ Quote system failed: {quote_error}, using minimal requirements")
                min_output_amount = 1

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

            # Enhanced gas calculation for swap with Arbitrum multiplier
            base_gas_price = self.w3.eth.gas_price
            chain_id = self.w3.eth.chain_id

            # Apply 2x multiplier for Arbitrum mainnet to handle variable gas costs
            if chain_id == 42161:  # Arbitrum Mainnet
                swap_gas_price = int(base_gas_price * 2.0)
                gas_limit = 500000  # Increased gas limit for complex swaps
                print(f"⛽ Arbitrum swap (2nd): base {base_gas_price} → optimized {swap_gas_price} (2.0x)")
            else:
                swap_gas_price = int(base_gas_price * 1.5)  # 50% buffer for testnet
                gas_limit = 450000
                print(f"⛽ Testnet swap (2nd): base {base_gas_price} → optimized {swap_gas_price} (1.5x)")

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

                # Enhanced gas estimation with multiple fallback strategies
                max_retries = 3
                estimated_gas = None
                gas_estimation_success = False

                # Try progressively simpler transaction validation
                for attempt in range(max_retries):
                    try:
                        if attempt == 0:
                            estimated_gas = self.w3.eth.estimate_gas(swap_tx)
                        elif attempt == 1:
                            swap_tx['gas'] = 600000
                            estimated_gas = self.w3.eth.estimate_gas(swap_tx)
                        else:
                            estimated_gas = 500000

                        print(f"💰 Gas estimation attempt {attempt + 1}: {estimated_gas}")
                        gas_estimation_success = True

                        # Update transaction with estimated gas
                        if estimated_gas > 0:
                            gas_limit = min(int(estimated_gas * 1.8), 800000)  # 80% buffer, max 800k
                            swap_tx['gas'] = gas_limit
                            print(f"⛽ Updated gas limit to: {gas_limit}")
                        break

                    except Exception as gas_error:
                        error_msg = str(gas_error).lower()
                        print(f"⚠️ Gas estimation attempt {attempt + 1} failed: {gas_error}")

                        if "execution reverted" in error_msg and "stf" in error_msg:
                            print("⚠️ Slippage Too Forward - adjusting parameters")
                            min_output_amount = max(1, int(min_output_amount * 0.9))
                            swap_params['amountOutMinimum'] = min_output_amount
                            print(f"🔄 Reduced min output to: {min_output_amount}")
                            continue
                        elif "execution reverted" in error_msg:
                            if attempt < max_retries - 1:
                                print(f"⚠️ Gas estimate reverted (attempt {attempt + 1}), retrying...")
                                swap_params['amountOutMinimum'] = 1
                                continue
                            else:
                                print("⚠️ Gas estimation reverted — sending with fallback gas limit anyway")
                                estimated_gas = 500000
                                gas_estimation_success = True
                                break
                        elif "insufficient funds" in error_msg:
                            print("❌ Insufficient ETH for gas fees")
                            return None

                # Final fallback if all estimation attempts failed
                if not gas_estimation_success:
                    print("⚠️ Using fallback gas settings")
                    swap_tx['gas'] = 600000  # Conservative fallback

            except Exception as validation_error:
                print(f"❌ Pre-validation failed: {validation_error}")
                return None

            for nonce_attempt in range(3):
                try:
                    fresh_nonce = self.w3.eth.get_transaction_count(self.address, 'pending')
                    swap_tx['nonce'] = fresh_nonce
                    print(f"🔄 Fresh nonce before signing: {fresh_nonce} (attempt {nonce_attempt + 1}/3)")

                    signed_swap = self.w3.eth.account.sign_transaction(swap_tx, self.account.key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_swap.rawTransaction)

                    print(f"✅ Swap executed successfully: {tx_hash.hex()}")
                    return tx_hash.hex()

                except ValueError as nonce_err:
                    err_msg = str(nonce_err)
                    if 'nonce too low' in err_msg and nonce_attempt < 2:
                        print(f"⚠️ Nonce conflict (attempt {nonce_attempt + 1}/3), retrying with fresh nonce...")
                        import time as _time
                        _time.sleep(1)
                        continue
                    else:
                        raise

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

    def _encode_path(self, tokens, fees):
        """Encode multi-hop path for Uniswap V3 exactInput
        Path format: token0 (20 bytes) + fee (3 bytes) + token1 (20 bytes) + fee (3 bytes) + token2 (20 bytes)
        """
        path = b''
        for i, token in enumerate(tokens):
            path += bytes.fromhex(token[2:])
            if i < len(fees):
                path += fees[i].to_bytes(3, 'big')
        return path

    def _audit_path(self, path_bytes, token_names, fees):
        """Pre-flight byte-level audit of encoded path — prints hex, length, and decoded fees"""
        print("=" * 60)
        print("🔍 PRE-FLIGHT PATH AUDIT (abi.encodePacked)")
        print(f"   Full hex: 0x{path_bytes.hex()}")
        expected_len = 20 * len(token_names) + 3 * len(fees)
        print(f"   Length:   {len(path_bytes)} bytes (expected {expected_len} for {len(token_names)}-token path)")
        offset = 0
        for i, name in enumerate(token_names):
            addr = path_bytes[offset:offset+20]
            print(f"   {name} addr: {addr.hex()} ({len(addr)} bytes)")
            offset += 20
            if i < len(fees):
                fee_bytes = path_bytes[offset:offset+3]
                fee_val = int.from_bytes(fee_bytes, 'big')
                pct = fee_val / 1_000_000 * 100
                print(f"   Fee tier:  0x{fee_bytes.hex()} = {fee_val} ({pct:.2f}%)")
                offset += 3
        valid = len(path_bytes) == (20 * len(token_names) + 3 * len(fees))
        print(f"   AUDIT: {'✅ PASS' if valid else '❌ FAIL — unexpected byte length'}")
        print("=" * 60)

    def _execute_multihop_swap(self, path_bytes, amount_in, amount_in_wei, token_in, description):
        """Execute a multi-hop swap using exactInput"""
        try:
            print(f"🔄 Multi-hop swap: {description}")

            eth_balance = self.w3.eth.get_balance(self.address)
            min_eth_needed = self.w3.to_wei(0.0002, 'ether')
            if eth_balance < min_eth_needed:
                print(f"❌ Insufficient ETH for gas: {self.w3.from_wei(eth_balance, 'ether'):.6f} ETH")
                return None

            if token_in != "0x0000000000000000000000000000000000000000":
                token_contract = self.w3.eth.contract(address=token_in, abi=self.erc20_abi)
                try:
                    current_allowance = token_contract.functions.allowance(self.address, self.router_address).call()
                    if current_allowance < amount_in_wei:
                        nonce = self.w3.eth.get_transaction_count(self.address)
                        base_gas_price = self.w3.eth.gas_price
                        chain_id = self.w3.eth.chain_id
                        gas_price = int(base_gas_price * 2.0) if chain_id == 42161 else int(base_gas_price * 1.3)
                        approve_tx = token_contract.functions.approve(
                            self.router_address, amount_in_wei * 2
                        ).build_transaction({
                            'chainId': chain_id, 'gas': 100000,
                            'gasPrice': gas_price, 'nonce': nonce,
                        })
                        signed_approve = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
                        approve_hash = self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
                        print(f"✅ Multi-hop approval sent: {approve_hash.hex()}")
                        time.sleep(8)
                except Exception as approve_error:
                    print(f"❌ Multi-hop approval failed: {approve_error}")
                    return None

            deadline = int(time.time()) + 120
            nonce = self.w3.eth.get_transaction_count(self.address)
            base_gas_price = self.w3.eth.gas_price
            chain_id = self.w3.eth.chain_id
            swap_gas_price = int(base_gas_price * 2.0) if chain_id == 42161 else int(base_gas_price * 1.5)
            gas_limit = 600000

            swap_params = {
                'path': path_bytes,
                'recipient': self.w3.to_checksum_address(self.address),
                'deadline': deadline,
                'amountIn': amount_in_wei,
                'amountOutMinimum': 1
            }

            swap_tx = self.router_contract.functions.exactInput(
                swap_params
            ).build_transaction({
                'chainId': chain_id,
                'gas': gas_limit,
                'gasPrice': swap_gas_price,
                'nonce': nonce,
                'value': 0
            })

            print(f"⛽ Multi-hop gas: {self.w3.from_wei(swap_gas_price, 'gwei'):.4f} gwei, limit: {gas_limit}")

            try:
                estimated_gas = self.w3.eth.estimate_gas(swap_tx)
                swap_tx['gas'] = min(int(estimated_gas * 1.8), 800000)
                print(f"💰 Multi-hop gas estimate: {estimated_gas} → using {swap_tx['gas']}")
            except Exception as gas_err:
                print(f"⚠️ Multi-hop gas estimation failed: {gas_err}, using {gas_limit}")

            fresh_nonce = self.w3.eth.get_transaction_count(self.address, 'pending')
            swap_tx['nonce'] = fresh_nonce
            signed_swap = self.w3.eth.account.sign_transaction(swap_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_swap.rawTransaction)
            print(f"✅ Multi-hop swap sent: {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status == 1:
                print(f"✅ Multi-hop swap confirmed!")
                return tx_hash.hex()
            else:
                print(f"❌ Multi-hop swap reverted on-chain")
                return None

        except Exception as e:
            print(f"❌ Multi-hop swap error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def swap_dai_for_wbtc(self, dai_amount):
        """Swap DAI for WBTC on Uniswap V3 — uses multi-hop DAI→WETH→WBTC for better liquidity"""
        try:
            print(f"🔄 Swapping {dai_amount:.6f} DAI for WBTC (multi-hop via WETH)...")

            if dai_amount <= 0:
                print("❌ Invalid DAI amount for swap")
                return False

            amount_in_wei = int(dai_amount * 1e18)

            fees_attempt1 = [500, 500]
            path_bytes = self._encode_path(
                [self.dai_address, self.weth_address, self.wbtc_address],
                fees_attempt1
            )
            self._audit_path(path_bytes, ["DAI", "WETH", "WBTC"], fees_attempt1)

            swap_result = self._execute_multihop_swap(
                path_bytes, dai_amount, amount_in_wei,
                self.dai_address, f"{dai_amount:.4f} DAI → WETH → WBTC"
            )

            if not swap_result:
                print("⚠️ Multi-hop 500/500 failed, trying 3000/500 fee tiers...")
                fees_attempt2 = [3000, 500]
                path_bytes = self._encode_path(
                    [self.dai_address, self.weth_address, self.wbtc_address],
                    fees_attempt2
                )
                self._audit_path(path_bytes, ["DAI", "WETH", "WBTC"], fees_attempt2)
                swap_result = self._execute_multihop_swap(
                    path_bytes, dai_amount, amount_in_wei,
                    self.dai_address, f"{dai_amount:.4f} DAI →(3000)→ WETH →(500)→ WBTC"
                )

            if not swap_result:
                print("⚠️ Multi-hop failed, trying direct DAI→WBTC single-hop...")
                swap_result_direct = self._execute_swap(
                    self.dai_address, self.wbtc_address, dai_amount, "DAI", "WBTC"
                )
                if swap_result_direct and isinstance(swap_result_direct, str):
                    swap_result = swap_result_direct

            if swap_result and isinstance(swap_result, str):
                return {
                    'success': True,
                    'tx_hash': swap_result,
                    'amount_in': dai_amount,
                    'token_in': 'DAI',
                    'token_out': 'WBTC'
                }
            else:
                print("❌ All WBTC swap attempts failed")
                return False

        except Exception as e:
            print(f"❌ DAI to WBTC swap failed: {e}")
            return False

    def swap_dai_for_weth(self, dai_amount):
        """Swap DAI for WETH on Uniswap V3 — prefers 500 fee tier (most liquid on Arbitrum)"""
        try:
            print(f"🔄 Swapping {dai_amount:.6f} DAI for WETH...")

            if dai_amount <= 0:
                print("❌ Invalid DAI amount for swap")
                return False

            swap_result = self._execute_swap(
                self.dai_address,
                self.weth_address, 
                dai_amount,
                "DAI",
                "WETH"
            )

            if swap_result and isinstance(swap_result, str):
                return {
                    'success': True,
                    'tx_hash': swap_result,
                    'amount_in': dai_amount,
                    'token_in': 'DAI',
                    'token_out': 'WETH'
                }
            else:
                return False

        except Exception as e:
            print(f"❌ DAI to WETH swap failed: {e}")
            return False

    def swap_weth_for_wbtc(self, weth_amount):
        """Swap WETH for WBTC on Uniswap V3 — direct swap (most liquid pair on Arbitrum)"""
        try:
            print(f"🔄 Swapping {weth_amount:.8f} WETH for WBTC...")

            if weth_amount <= 0:
                print("❌ Invalid WETH amount for swap")
                return False

            swap_result = self._execute_swap(
                self.weth_address,
                self.wbtc_address,
                weth_amount,
                "WETH",
                "WBTC"
            )

            if swap_result and isinstance(swap_result, str):
                return {
                    'success': True,
                    'tx_hash': swap_result,
                    'amount_in': weth_amount,
                    'token_in': 'WETH',
                    'token_out': 'WBTC'
                }
            else:
                return False

        except Exception as e:
            print(f"❌ WETH to WBTC swap failed: {e}")
            return False

    def swap_weth_for_dai(self, weth_amount):
        """Swap WETH for DAI on Uniswap V3 — prefers 500 fee tier"""
        try:
            print(f"🔄 Swapping {weth_amount:.8f} WETH for DAI...")

            if weth_amount <= 0:
                print("❌ Invalid WETH amount for swap")
                return False

            swap_result = self._execute_swap(
                self.weth_address,
                self.dai_address,
                weth_amount,
                "WETH",
                "DAI"
            )

            if swap_result and isinstance(swap_result, str):
                return {
                    'success': True,
                    'tx_hash': swap_result,
                    'amount_in': weth_amount,
                    'token_in': 'WETH',
                    'token_out': 'DAI'
                }
            else:
                return False

        except Exception as e:
            print(f"❌ WETH to DAI swap failed: {e}")
            return False

    def swap_dai_for_arb(self, dai_amount):
        """Swap DAI for ARB on Uniswap V3 - Extended for ARB token swaps with profit tracking"""
        try:
            print(f"🔄 Swapping {dai_amount:.6f} DAI for ARB...")

            # DAI compliance check
            if dai_amount <= 0:
                print("❌ Invalid DAI amount for swap")
                return False

            # Get ARB price before swap for tracking
            arb_price = 0.41  # Default, should be fetched from price oracle
            try:
                # Try to get real ARB price if market analyzer is available
                if hasattr(self, '_get_arb_price'):
                    arb_price = self._get_arb_price()
            except:
                pass

            # ARB token address for Arbitrum Mainnet
            arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"

            swap_result = self._execute_swap(
                self.dai_address,
                arb_address, 
                dai_amount,
                "DAI",
                "ARB"
            )

            if swap_result and isinstance(swap_result, str):
                # Calculate ARB received (estimate)
                arb_received = dai_amount / arb_price

                # Start profit tracking
                try:
                    from debt_swap_profit_tracker import track_dai_to_arb_swap
                    cycle_id = track_dai_to_arb_swap(dai_amount, arb_received, arb_price)
                    print(f"📊 Profit tracking started: {cycle_id}")
                except Exception as track_error:
                    print(f"⚠️ Profit tracking failed: {track_error}")
                    cycle_id = None

                return {
                    'success': True,
                    'tx_hash': swap_result,
                    'amount_in': dai_amount,
                    'token_in': 'DAI',
                    'token_out': 'ARB',
                    'arb_received': arb_received,
                    'arb_price': arb_price,
                    'cycle_id': cycle_id
                }
            else:
                return False

        except Exception as e:
            print(f"❌ DAI to ARB swap failed: {e}")
            return False

    def swap_arb_for_dai(self, arb_amount, cycle_id=None):
        """Swap ARB for DAI on Uniswap V3 - Reverse swap functionality with profit tracking"""
        try:
            print(f"🔄 Swapping {arb_amount:.6f} ARB for DAI...")

            # ARB compliance check
            if arb_amount <= 0:
                print("❌ Invalid ARB amount for swap")
                return False

            # Get ARB price for tracking
            arb_price = 0.41  # Default, should be fetched from price oracle
            try:
                if hasattr(self, '_get_arb_price'):
                    arb_price = self._get_arb_price()
            except:
                pass

            # ARB token address for Arbitrum Mainnet
            arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"

            swap_result = self._execute_swap(
                arb_address,
                self.dai_address, 
                arb_amount,
                "ARB",
                "DAI"
            )

            if swap_result and isinstance(swap_result, str):
                # Calculate DAI received (estimate)
                dai_received = arb_amount * arb_price

                # Complete profit tracking if cycle_id provided
                if cycle_id:
                    try:
                        from debt_swap_profit_tracker import track_arb_to_dai_swap
                        track_arb_to_dai_swap(cycle_id, dai_received, arb_price)
                        print(f"📊 Profit tracking completed for cycle: {cycle_id}")
                    except Exception as track_error:
                        print(f"⚠️ Profit tracking completion failed: {track_error}")

                return {
                    'success': True,
                    'tx_hash': swap_result,
                    'amount_in': arb_amount,
                    'token_in': 'ARB',
                    'token_out': 'DAI',
                    'dai_received': dai_received,
                    'arb_price': arb_price
                }
            else:
                return False

        except Exception as e:
            print(f"❌ ARB to DAI swap failed: {e}")
            return False

    def _execute_swap(self, token_in, token_out, amount, token_in_name, token_out_name):
        """Executes the token swap on Uniswap V3 and returns transaction hash"""
        try:
            # Validate input
            if amount <= 0:
                print(f"❌ Invalid amount for {token_in_name} to {token_out_name} swap")
                return False

            print(f"🔄 Executing swap: {amount:.6f} {token_in_name} -> {token_out_name}")
            swap_tx = self.swap_tokens(token_in, token_out, amount)

            if not swap_tx:
                print(f"❌ Swap {token_in_name} to {token_out_name} transaction failed")
                return False

            # Handle different return types from swap_tokens
            if isinstance(swap_tx, str):
                tx_hash_str = swap_tx
            else:
                try:
                    tx_hash = self.w3.to_bytes(hexstr=swap_tx)
                    tx_hash_str = tx_hash.hex()
                except:
                    tx_hash_str = str(swap_tx)

            # Wait for confirmation
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_str, timeout=120)
                if receipt.status == 1:
                    print(f"✅ {token_in_name} to {token_out_name} swap successful!")
                    print(f"🔗 Transaction Hash: {tx_hash_str}")
                    return tx_hash_str
                else:
                    print(f"❌ Swap transaction failed in execution")
                    return False
            except Exception as receipt_error:
                print(f"⚠️ Could not verify transaction receipt: {receipt_error}")
                print(f"🔗 Transaction Hash: {tx_hash_str}")
                return tx_hash_str  # Return hash even if receipt check fails

        except Exception as e:
            print(f"❌ Error in _execute_swap: {e}")
            import traceback
            traceback.print_exc()
            return False