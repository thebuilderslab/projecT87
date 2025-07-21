import os
from web3 import Web3
from eth_account import Account

class UniswapArbitrumIntegration:
    def __init__(self, w3, account):
        self.w3 = w3
        self.account = account
        self.address = account.address

        # Uniswap V3 Arbitrum Sepolia addresses (ensure proper EIP-55 checksum)
        self.router_address = self.w3.to_checksum_address("0x101F443B4d1b059569D643917553c771E1b9663E")  # SwapRouter
        self.factory_address = self.w3.to_checksum_address("0x248AB79Bbb9bC29bB72f7Cd42F17e054Fc40188e")  # V3 Factory
        self.quoter_address = self.w3.to_checksum_address("0x2779a0CC1c3e0E44D2542EC3637094d26349e68e")   # Quoter V2

        # Token addresses
        self.weth_address = self.w3.to_checksum_address("0x980B62Da83eFf3D4576C647993b0c1D7faf17c73")
        # Arbitrum Mainnet token addresses
        self.usdc_address = "0xAF88D065e8c38FAD0AEff3E253e648A15ceE23DC"

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
        """Standard ERC20 ABI"""
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
            }
        ]

    def _convert_to_wei(self, token_address, amount):
        """Convert amount to wei based on token decimals"""
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
            decimals = token_contract.functions.decimals().call()
        except:
            # Fallback decimals if contract call fails
            if token_address.lower() == "0xaf88d065e77c8cf0eaeff3e253e648a15cee23dc":  # USDC
                decimals = 6
            elif token_address.lower() == "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f":  # WBTC
                decimals = 8
            else:
                decimals = 18
        return int(amount * (10 ** decimals))


    def swap_tokens(self, token_in, token_out, amount_in, fee=3000):
        """Execute token swap on Uniswap V3"""
        try:
            import time

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
                    print(f"⚠️ Balance check failed, proceeding with swap: {balance_error}")

            # Convert amount_in to wei FIRST
            amount_in_wei = self._convert_to_wei(token_in, amount_in)
            print(f"🔄 Converting {amount_in} to {amount_in_wei} wei for {token_in}")

            # Approve token spending
            if token_in != "0x0000000000000000000000000000000000000000":  # Not ETH
                token_contract = self.w3.eth.contract(address=token_in, abi=self.erc20_abi)
                nonce = self.w3.eth.get_transaction_count(self.address)

                # Enhanced gas price calculation
                base_gas_price = self.w3.eth.gas_price
                optimized_gas_price = int(base_gas_price * 1.2)  # 20% higher than base

                approve_tx = token_contract.functions.approve(
                    self.router_address, 
                    amount_in_wei  # Use properly converted wei amount
                ).build_transaction({
                    'chainId': self.w3.eth.chain_id,
                    'gas': 100000,
                    'gasPrice': optimized_gas_price,  # Use optimized gas price
                    'nonce': nonce,
                })

                signed_approve = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
                self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
                print(f"✅ Approval transaction sent with gas price: {optimized_gas_price}")
                time.sleep(5)  # Wait longer for approval confirmation

            # Build swap parameters with proper wei amounts
            deadline = int(time.time()) + 300  # 5 minutes from now

            swap_params = {
                'tokenIn': token_in,
                'tokenOut': token_out,
                'fee': fee,
                'recipient': self.address,
                'deadline': deadline,
                'amountIn': amount_in_wei,  # Use wei amount here
                'amountOutMinimum': 0,
                'sqrtPriceLimitX96': 0
            }

            # Build swap transaction with enhanced gas optimization
            nonce = self.w3.eth.get_transaction_count(self.address)

            # Enhanced gas calculation for swap
            base_gas_price = self.w3.eth.gas_price
            swap_gas_price = int(base_gas_price * 1.3)  # 30% higher for swap operations

            swap_tx = self.router_contract.functions.exactInputSingle(
                swap_params
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 350000,  # Higher gas limit for complex swaps
                'gasPrice': swap_gas_price,  # Use optimized gas price
                'nonce': nonce,
                'value': amount_in_wei if token_in == "0x0000000000000000000000000000000000000000" else 0
            })

            print(f"🔄 Swap transaction built with gas price: {swap_gas_price} ({self.w3.from_wei(swap_gas_price, 'gwei'):.2f} gwei)")

            # Sign and send
            signed_swap = self.w3.eth.account.sign_transaction(swap_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_swap.rawTransaction)

            print(f"✅ Swap executed: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            print(f"❌ Swap failed: {e}")
            return None

    def optimize_collateral_via_swap(self, aave_integration, current_collateral_amount):
        """Swap borrowed assets to optimize collateral position"""
        try:
            print("🔄 Optimizing collateral through strategic swapping...")

            # Example: If we borrowed USDC, swap some to ETH to rebalance
            usdc_balance = aave_integration.get_token_balance(aave_integration.usdc_address)

            if usdc_balance > 100:  # If we have more than $100 USDC
                # Swap 50% of USDC to ETH for rebalancing
                swap_amount = int(usdc_balance * 0.5)  # Remove (10 ** 6), handled in swap_tokens

                swap_tx = self.swap_tokens(
                    aave_integration.usdc_address,  # USDC in
                    aave_integration.weth_address,  # WETH out
                    swap_amount,
                    3000  # 0.3% fee
                )

                if swap_tx:
                    print("✅ Collateral optimization swap completed")
                    return True

            return False

        except Exception as e:
            print(f"❌ Collateral optimization failed: {e}")
            return False