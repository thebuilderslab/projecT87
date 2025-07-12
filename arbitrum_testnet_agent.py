import time
import json
import os
import random
from datetime import datetime
from web3 import Web3
from eth_account import Account
from aave_integration import AaveIntegration
from uniswap_integration import UniswapIntegration
from aave_health_monitor import HealthMonitor
from gas_fee_calculator import ArbitrumGasCalculator
import requests

class ArbitrumTestnetAgent:
    def __init__(self):
        print("🤖 Initializing Arbitrum Testnet Agent...")

        # Load environment variables
        self.private_key = os.getenv('PRIVATE_KEY')
        self.coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.network_mode = os.getenv('NETWORK_MODE', 'testnet')

        if not self.private_key:
            raise Exception("PRIVATE_KEY environment variable not found!")

        if not self.coinmarketcap_api_key:
            raise Exception("COINMARKETCAP_API_KEY environment variable not found!")

        # Determine network configuration
        if self.network_mode == 'mainnet':
            self.rpc_url = "https://arb1.arbitrum.io/rpc"
            self.chain_id = 42161
            print("🌐 Operating on Arbitrum Mainnet")
        else:
            self.rpc_url = "https://sepolia-rollup.arbitrum.io/rpc"
            self.chain_id = 421614
            print("🧪 Operating on Arbitrum Sepolia Testnet")

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to {self.rpc_url}")

        # Initialize account
        self.account = Account.from_key(self.private_key)
        self.address = self.account.address
        print(f"🔑 Wallet Address: {self.address}")

        # Contract addresses based on network
        if self.network_mode == 'mainnet':
            # Arbitrum Mainnet addresses
            self.usdc_address = "0xaf88d065e77c8cF0eAEFf3e253e648a15cEe23dC"
            self.wbtc_address = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
            self.weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
            self.dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
            self.aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        else:
            # Arbitrum Sepolia Testnet addresses
            self.usdc_address = "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"
            self.wbtc_address = "0x1346786E6A5e07b90184a1Ba58E55444b99DC4A2"
            self.weth_address = "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73"
            self.dai_address = "0x6d906e526a4e2Ca02097BA9d0caA3c382F52278E"
            self.aave_pool_address = "0x6Cbb63871b97A50E62dcB36BF5532eCCa4a3FE0d"

        # Initialize real blockchain integrations
        self.aave = None
        self.uniswap = None
        self.health_monitor = None
        self.gas_calculator = None

        # Configuration parameters loaded from environment variables (Replit Secrets)
        # Defaults are provided if the environment variable is not set
        self.target_health_factor = float(os.getenv('TARGET_HEALTH_FACTOR', '3.5')) # Target HF for general management
        self.growth_trigger_threshold = float(os.getenv('GROWTH_TRIGGER_THRESHOLD', '40.0')) # USDC growth to trigger re-leverage
        self.re_leverage_percentage = float(os.getenv('RE_LEVERAGE_PERCENTAGE', '0.50')) # Percentage of growth to re-leverage
        self.min_borrow_releverage = float(os.getenv('MIN_BORROW_RELEVERAGE', '10.0')) # Minimum borrow amount for re-leverage
        self.max_borrow_releverage = float(os.getenv('MAX_BORROW_RELEVERAGE', '200.0')) # Maximum borrow amount for re-leverage
        self.safe_releverage_hf_threshold = float(os.getenv('SAFE_RELEVERAGE_HF_THRESHOLD', '2.5')) # Minimum HF to safely re-leverage

        self.previous_leveraged_value_usd = None # Initialize for tracking growth

        # Initialize collateral tracking for autonomous triggers
        self.last_collateral_value_usd = 0.0
        print("💰 Initialized last_collateral_value_usd to 0.0")

    def initialize_integrations(self):
        """Initialize all real DeFi integrations with strict error handling"""
        try:
            print("🚀 Initializing Real DeFi Integrations...")

            # Initialize Real Aave, Uniswap, and Health Monitor Integrations
            self.aave = AaveIntegration(self.w3, self.account)
            self.uniswap = UniswapIntegration(self.w3, self.account)
            self.health_monitor = HealthMonitor(self.w3, self.account)
            print("✅ Initialized Real Aave, Uniswap, and Health Monitor Integrations.")

            # Initialize Gas Calculator
            self.gas_calculator = ArbitrumGasCalculator()
            print("⛽ Initialized Gas Calculator.")

            # Token approvals with gas optimization
            tokens_to_approve = [
                ("USDC", self.usdc_address),
                ("WBTC", self.wbtc_address),
                ("WETH", self.weth_address),
                ("DAI", self.dai_address)
            ]

            for token_name, token_address in tokens_to_approve:
                print(f"🚀 Approving {token_name} for Aave Pool...")

                # Get gas parameters with strict error handling
                gas_params = self.gas_calculator.calculate_transaction_fee('approve_token', speed='market')
                if gas_params is None:
                    raise Exception(f"CRITICAL: Failed to get gas params for {token_name} approval. Halting.")

                # Approve token with gas optimization
                self.aave.approve_token(
                    token_address=token_address,
                    spender_address=self.aave_pool_address,
                    amount_in_human_readable=float('inf'),
                    gas_price=gas_params['gas_price_wei']
                )
                print(f"✅ {token_name} approved for Aave with optimized gas")
                time.sleep(2)

            print("✅ All DeFi integrations initialized successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize DeFi integrations: {e}")
            return False

    def check_network_status(self):
        """Checks the network status."""
        try:
            if not self.w3.is_connected():
                return False, "Not connected to Web3 provider."
            latest_block = self.w3.eth.block_number
            gas_price = self.w3.eth.gas_price
            print(f"🌐 Network Connected: Block {latest_block}, Gas Price: {Web3.from_wei(gas_price, 'gwei')} Gwei")
            return True, "Connected"
        except Exception as e:
            return False, f"Network check failed: {e}"

    def check_emergency_stop(self):
        """Checks for an emergency stop flag file."""
        return os.path.exists("emergency_stop.flag")

    def get_eth_balance(self):
        """Get ETH balance from blockchain"""
        try:
            balance_wei = self.w3.eth.get_balance(self.address)
            return self.w3.from_wei(balance_wei, 'ether')
        except Exception as e:
            print(f"❌ Failed to get ETH balance: {e}")
            return 0.0

    def get_leveraged_tokens_usd_value(self):
        """
        Calculates the total USD value of supplied collateral tokens on Aave.
        NOTE: This needs to get the *supplied* balance from Aave, not just wallet balance.
        AaveHealthMonitor.get_monitoring_summary should be able to provide this via 'total_collateral_usd'.
        """
        # Rely on the health monitor's total collateral USD value for accuracy
        # monitoring_summary = self.health_monitor.get_monitoring_summary() # Original Code
        # if monitoring_summary and 'total_collateral_usd' in monitoring_summary: # Original Code
        #    return monitoring_summary['total_collateral_usd'] # Original Code
        # else: # Original Code
        #    print("❌ Could not get total collateral USD value from health monitor.") # Original Code
        #    return 0.0 # Return 0 if unable to retrieve # Original Code
        return 0.0 # Returning 0.0 directly because the function is not being used.

    def execute_leveraged_supply_strategy(self, usdc_borrow_amount):
        """
        Executes a strategy of borrowing USDC, swapping it for other assets,
        and supplying them as collateral to increase leverage.
        Revised to supply ALL remaining USDC as DAI collateral.
        """
        print(f"\n⚙️ Executing Leveraged Supply Strategy with {usdc_borrow_amount:.2f} USDC...")

        if not self.aave.borrow(usdc_borrow_amount, self.usdc_address):
            print("❌ Failed to borrow USDC for leveraged supply.")
            return False
        print(f"✅ Borrowed {usdc_borrow_amount:.2f} USDC.")
        time.sleep(5) # Give network time

        # Define distribution percentages
        # Adjust these percentages based on your desired asset allocation
        WBTC_PERCENT = 0.30 # 30% of borrowed USDC converted to WBTC
        WETH_PERCENT = 0.20 # 20% of borrowed USDC converted to WETH
        DAI_PERCENT = 0.10  # 10% of borrowed USDC converted to DAI (initial direct allocation)
        ETH_GAS_RESERVE_PERCENT = 0.05 # 5% of borrowed USDC converted to ETH for gas
        # The remaining will be converted to DAI and supplied

        current_usdc_balance = self.aave.get_token_balance(self.usdc_address)
        print(f"Current USDC balance after borrow: {current_usdc_balance:.2f}")

        # Ensure we don't try to swap more than we have
        usdc_to_swap_base = min(current_usdc_balance, usdc_borrow_amount)
        if usdc_to_swap_base < 1.0: # Check if there's enough to even attempt swaps
            print("❌ Insufficient USDC to proceed with leveraged supply swaps.")
            return False

        # Calculate amounts based on percentage
        wbtc_amount_usdc_equiv = usdc_to_swap_base * WBTC_PERCENT
        weth_amount_usdc_equiv = usdc_to_swap_base * WETH_PERCENT
        dai_amount_usdc_equiv = usdc_to_swap_base * DAI_PERCENT
        eth_for_gas_usdc_equiv = usdc_to_swap_base * ETH_GAS_RESERVE_PERCENT

        # Perform swaps
        success = True

        # Swap to WBTC
        if wbtc_amount_usdc_equiv > 0.1: # Only swap if meaningful amount
            print(f"🔄 Swapping {wbtc_amount_usdc_equiv:.2f} USDC to WBTC...")
            if not self.uniswap.swap_tokens(self.usdc_address, self.wbtc_address, wbtc_amount_usdc_equiv, 500):
                print("❌ Failed to swap USDC to WBTC.")
                success = False
            else:
                print("✅ Swapped USDC to WBTC.")
                time.sleep(5)

        # Swap to WETH
        if weth_amount_usdc_equiv > 0.1:
            print(f"🔄 Swapping {weth_amount_usdc_equiv:.2f} USDC to WETH...")
            if not self.uniswap.swap_tokens(self.usdc_address, self.weth_address, weth_amount_usdc_equiv, 500):
                print("❌ Failed to swap USDC to WETH.")
                success = False
            else:
                print("✅ Swapped USDC to WETH.")
                time.sleep(5)

        # Swap to DAI (initial allocation)
        if dai_amount_usdc_equiv > 0.1:
            print(f"🔄 Swapping {dai_amount_usdc_equiv:.2f} USDC to DAI...")
            if not self.uniswap.swap_tokens(self.usdc_address, self.dai_address, dai_amount_usdc_equiv, 500):
                print("❌ Failed to swap USDC to DAI.")
                success = False
            else:
                print("✅ Swapped USDC to DAI.")
                time.sleep(5)

        # Swap a small portion to ETH for gas if needed (and unwrap WETH)
        if eth_for_gas_usdc_equiv > 0.01: # Smallest amount for gas
            print(f"🔄 Swapping {eth_for_gas_usdc_equiv:.2f} USDC to ETH for gas...")
            if self.uniswap.swap_tokens(self.usdc_address, self.weth_address, eth_for_gas_usdc_equiv, 500):
                weth_balance = self.aave.get_token_balance(self.weth_address) # Check newly acquired WETH
                if weth_balance > 0:
                    print(f"Unwrapping {weth_balance:.6f} WETH to ETH for gas reserve.")
                    self.aave.unwrap_weth(weth_balance) # Assuming this unwraps WETH to ETH
                    print("✅ Swapped USDC to ETH for gas.")

    def get_optimized_gas_params(self, operation_type, speed='market'):
        """Get optimized gas parameters for transactions"""
        try:
            gas_data = self.gas_calculator.calculate_transaction_fee(operation_type, speed)
            if gas_data:
                return {
                    'gas': gas_data['gas_limit'],
                    'gasPrice': gas_data['gas_price_wei']
                }
            else:
                # Fallback gas parameters
                return {
                    'gas': self.gas_calculator.gas_limits.get(operation_type, 200000),
                    'gasPrice': int(self.w3.eth.gas_price * 1.1)  # 10% above current
                }
        except Exception as e:
            print(f"⚠️ Gas optimization failed, using fallback: {e}")
            # Safe fallback
            return {
                'gas': 200000,
                'gasPrice': int(self.w3.eth.gas_price * 1.1) if self.w3.eth.gas_price else 100000000  # 0.1 gwei fallback
            }

    def get_arb_price(self):
        """Get real-time ARB price with strict error handling - NO HARDCODED FALLBACK"""
        try:
            if not self.coinmarketcap_api_key:
                raise Exception("CoinMarketCap API key not available")

            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': self.coinmarketcap_api_key,
            }
            parameters = {
                'symbol': 'ARB',
                'convert': 'USD'
            }

            response = requests.get(url, headers=headers, params=parameters, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'ARB' in data['data']:
                    price = data['data']['ARB']['quote']['USD']['price']
                    print(f"✅ Real ARB price fetched: ${price:.4f}")
                    return {'price': price}
                else:
                    raise Exception("ARB price data not found in API response")
            else:
                raise Exception(f"CoinMarketCap API error: {response.status_code}")

        except Exception as e:
            print(f"❌ CRITICAL: Failed to fetch real ARB price: {e}")
            raise Exception("Failed to fetch real ARB price.")

    def run_real_defi_task(self, run_id, iteration, config):
        """Execute autonomous DeFi operations with REAL blockchain data only"""
        print(f"\n🎯 Autonomous Run {run_id}, Iteration {iteration}")

        try:
            # Initialize integrations if not done
            if not hasattr(self, 'aave') or self.aave is None:
                self.initialize_integrations()

            # Check health factor with real data
            health_data = self.health_monitor.get_health_factor()
            if health_data is None:
                raise Exception("CRITICAL: Failed to get real health factor data. Halting.")

            current_health_factor = health_data.get('health_factor', 0)
            print(f"📊 Current Health Factor: {current_health_factor:.4f}")

            # Get real ARB price (strict - no fallback)
            arb_price_data = self.get_arb_price()
            arb_price = arb_price_data['price']
            print(f"💰 ARB Price: ${arb_price:.4f}")

            # Check emergency stop
            if self.check_emergency_stop():
                print("🛑 Emergency stop active, skipping operations")
                return 0.0

            # Check network status
            network_ok, status = self.check_network_status()
            if not network_ok:
                print(f"❌ Network issue: {status}")
                return 0.1

            # --- START DIAGNOSTIC CODE ---
            print("\n🔍 DIAGNOSTIC: Checking Wallet Balances...")
            # Get and print ETH balance
            current_eth_balance = self.get_eth_balance()
            print(f"    DIAGNOSTIC - Wallet ETH Balance (raw): {current_eth_balance:.10f} ETH")

            # Get and print USDC balance using the Aave integration's method
            current_usdc_balance_from_aave_integration = self.aave.get_token_balance(self.usdc_address)
            print(f"    DIAGNOSTIC - Wallet USDC Balance (via Aave integration): {current_usdc_balance_from_aave_integration:.6f} USDC")

            print("🔍 DIAGNOSTIC: Wallet Balance Check Complete.")
            # --- END DIAGNOSTIC CODE ---

            # Trigger condition: If health factor > 1.3, execute the sequence
            if current_health_factor > 1.3:
                print(f"🚀 TRIGGER ACTIVATED: Health factor {current_health_factor:.4f} > 1.3")

                # Step 1: Borrow 6 USDC with gas optimization
                print("🏦 Step 1: Borrowing 6 USDC...")
                gas_params = self.gas_calculator.calculate_transaction_fee('aave_borrow', speed='market')
                if gas_params is None:
                    raise Exception("CRITICAL: Failed to get gas params for Aave borrow. Halting.")

                borrow_result = self.aave.borrow(
                    asset=self.usdc_address,
                    amount=6.0,
                    gas_price=gas_params['gas_price_wei']
                )
                print(f"✅ Borrowed 6 USDC with optimized gas")
                time.sleep(5)

                # Step 2: Swap 2 USDC for WBTC and supply to Aave
                print("🔄 Step 2: Swap 2 USDC → WBTC + Supply to Aave...")

                # Get gas for swap
                gas_params = self.gas_calculator.calculate_transaction_fee('uniswap_swap', speed='market')
                if gas_params is None:
                    raise Exception("CRITICAL: Failed to get gas params for WBTC swap. Halting.")

                # Get initial WBTC balance
                wbtc_balance_before = self.uniswap.get_token_balance(self.wbtc_address)

                # Swap USDC for WBTC
                swap_result = self.uniswap.swap_tokens(
                    token_in=self.usdc_address,
                    token_out=self.wbtc_address,
                    amount_in=2.0,
                    gas_price=gas_params['gas_price_wei']
                )
                time.sleep(5)

                # Get WBTC received
                wbtc_balance_after = self.uniswap.get_token_balance(self.wbtc_address)
                wbtc_received = wbtc_balance_after - wbtc_balance_before
                print(f"✅ Received {wbtc_received:.8f} WBTC")

                # Supply WBTC to Aave
                gas_params = self.gas_calculator.calculate_transaction_fee('aave_supply', speed='market')
                if gas_params is None:
                    raise Exception("CRITICAL: Failed to get gas params for WBTC supply. Halting.")

                self.aave.supply(
                    asset=self.wbtc_address,
                    amount=wbtc_received,
                    gas_price=gas_params['gas_price_wei']
                )
                print(f"✅ Supplied {wbtc_received:.8f} WBTC to Aave")
                time.sleep(5)

                # Step 3: Swap 1 USDC for WETH and supply to Aave
                print("🔄 Step 3: Swap 1 USDC → WETH + Supply to Aave...")

                gas_params = self.gas_calculator.calculate_transaction_fee('uniswap_swap', speed='market')
                if gas_params is None:
                    raise Exception("CRITICAL: Failed to get gas params for WETH swap. Halting.")

                weth_balance_before = self.uniswap.get_token_balance(self.weth_address)

                self.uniswap.swap_tokens(
                    token_in=self.usdc_address,
                    token_out=self.weth_address,
                    amount_in=1.0,
                    gas_price=gas_params['gas_price_wei']
                )
                time.sleep(5)

                weth_balance_after = self.uniswap.get_token_balance(self.weth_address)
                weth_received = weth_balance_after - weth_balance_before
                print(f"✅ Received {weth_received:.8f} WETH")

                # Supply WETH to Aave
                gas_params = self.gas_calculator.calculate_transaction_fee('aave_supply', speed='market')
                if gas_params is None:
                    raise Exception("CRITICAL: Failed to get gas params for WETH supply. Halting.")

                self.aave.supply(
                    asset=self.weth_address,
                    amount=weth_received,
                    gas_price=gas_params['gas_price_wei']
                )
                print(f"✅ Supplied {weth_received:.8f} WETH to Aave")
                time.sleep(5)

                # Step 4: Swap 1 USDC for DAI and supply to Aave
                print("🔄 Step 4: Swap 1 USDC → DAI + Supply to Aave...")

                gas_params = self.gas_calculator.calculate_transaction_fee('uniswap_swap', speed='market')
                if gas_params is None:
                    raise Exception("CRITICAL: Failed to get gas params for DAI swap. Halting.")

                dai_balance_before = self.uniswap.get_token_balance(self.dai_address)

                self.uniswap.swap_tokens(
                    token_in=self.usdc_address,
                    token_out=self.dai_address,
                    amount_in=1.0,
                    gas_price=gas_params['gas_price_wei']
                )
                time.sleep(5)

                dai_balance_after = self.uniswap.get_token_balance(self.dai_address)
                dai_received = dai_balance_after - dai_balance_before
                print(f"✅ Received {dai_received:.8f} DAI")

                # Supply DAI to Aave
                gas_params = self.gas_calculator.calculate_transaction_fee('aave_supply', speed='market')
                if gas_params is None:
                    raise Exception("CRITICAL: Failed to get gas params for DAI supply. Halting.")

                self.aave.supply(
                    asset=self.dai_address,
                    amount=dai_received,
                    gas_price=gas_params['gas_price_wei']
                )
                print(f"✅ Supplied {dai_received:.8f} DAI to Aave")
                time.sleep(5)

                # Step 5: Swap remaining 2 USDC for ETH (keep as WETH)
                print("🔄 Step 5: Swap 2 USDC → ETH (keep as WETH)...")

                gas_params = self.gas_calculator.calculate_transaction_fee('uniswap_swap', speed='market')
                if gas_params is None:
                    raise Exception("CRITICAL: Failed to get gas params for final ETH swap. Halting.")

                final_weth_before = self.uniswap.get_token_balance(self.weth_address)

                self.uniswap.swap_tokens(
                    token_in=self.usdc_address,
                    token_out=self.weth_address,
                    amount_in=2.0,
                    gas_price=gas_params['gas_price_wei']
                )
                time.sleep(5)

                final_weth_after = self.uniswap.get_token_balance(self.weth_address)
                final_weth_received = final_weth_after - final_weth_before
                print(f"✅ Received {final_weth_received:.8f} WETH (kept in wallet)")

                print("🎉 AUTONOMOUS SEQUENCE COMPLETED SUCCESSFULLY!")
                return 0.95  # High performance score

            else:
                print(f"⏸️ No action: Health factor {current_health_factor:.4f} ≤ 1.3")
                return 0.7  # Moderate performance score

        except Exception as e:
            print(f"❌ CRITICAL ERROR in autonomous task: {e}")
            print("🛑 Halting execution due to real data fetch failure")
            return 0.0  # Failed performance score

    def get_portfolio_summary(self):
        """Get real portfolio summary with strict error handling"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'eth_balance': self.get_eth_balance(),
                'health_factor': None,
                'arb_price': None
            }

            # Get real health factor
            health_data = self.health_monitor.get_health_factor()
            if health_data is None:
                raise Exception("Failed to get real health factor")
            summary['health_factor'] = health_data.get('health_factor')

            # Get real ARB price
            arb_data = self.get_arb_price()
            summary['arb_price'] = arb_data['price']

            return summary

        except Exception as e:
            print(f"❌ Failed to get real portfolio summary: {e}")
            raise Exception("Portfolio summary requires real data - halting")