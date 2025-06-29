import os
import time
import json # Added for potential config file, but primarily for os.getenv
from web3 import Web3
from aave_integration import AaveArbitrumIntegration
from uniswap_integration import UniswapArbitrumIntegration
from aave_health_monitor import AaveHealthMonitor

class ArbitrumTestnetAgent:
    def __init__(self):
        # Load environment variables from Replit Secrets
        self.arb_rpc_url = os.getenv('ARB_RPC_URL')
        self.private_key = os.getenv('PRIVATE_KEY')
        self.address = os.getenv('WALLET_ADDRESS')

        # Configuration parameters loaded from environment variables (Replit Secrets)
        # Defaults are provided if the environment variable is not set
        self.target_health_factor = float(os.getenv('TARGET_HEALTH_FACTOR', '3.5')) # Target HF for general management
        self.growth_trigger_threshold = float(os.getenv('GROWTH_TRIGGER_THRESHOLD', '40.0')) # USDC growth to trigger re-leverage
        self.re_leverage_percentage = float(os.getenv('RE_LEVERAGE_PERCENTAGE', '0.50')) # Percentage of growth to re-leverage
        self.min_borrow_releverage = float(os.getenv('MIN_BORROW_RELEVERAGE', '10.0')) # Minimum borrow amount for re-leverage
        self.max_borrow_releverage = float(os.getenv('MAX_BORROW_RELEVERAGE', '200.0')) # Maximum borrow amount for re-leverage
        self.safe_releverage_hf_threshold = float(os.getenv('SAFE_RELEVERAGE_HF_THRESHOLD', '2.5')) # Minimum HF to safely re-leverage

        self.previous_leveraged_value_usd = None # Initialize for tracking growth

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.arb_rpc_url))
        if not self.w3.is_connected():
            print("Failed to connect to Arbitrum RPC.")
            exit()

        # Token addresses (ensure these are correct for Arbitrum mainnet/testnet)
        self.weth_address = Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1") # WETH on Arbitrum
        self.usdc_address = Web3.to_checksum_address("0xaf88d065eec38faD0AEFf3e253e648a15cEe23dC") # USDC on Arbitrum
        self.dai_address = Web3.to_checksum_address("0xDA10009cBd56d0F34a29c7aA35e34D246dA651D0")  # DAI on Arbitrum
        self.arb_address = Web3.to_checksum_address("0x912CE59144191C1f20bDd2ce08f2a688FEaEbb0B")  # ARB on Arbitrum
        self.wbtc_address = Web3.to_checksum_address("0x2f2a2543B76A4166549F7bffBE68df6Fc579b2F3") # WBTC on Arbitrum

        # Integration instances - these will be initialized later
        self.aave = None
        self.uniswap = None
        self.health_monitor = None

    def initialize_integrations(self):
        """Initializes Aave, Uniswap, and Health Monitor integrations."""
        try:
            self.aave = AaveArbitrumIntegration(self.w3, self.private_key, self.address, self.weth_address, self.usdc_address, self.dai_address)
            self.uniswap = UniswapArbitrumIntegration(self.w3, self.private_key, self.address)
            self.health_monitor = AaveHealthMonitor(self.w3, self.address, self.aave)
            print("✅ DeFi integrations initialized.")
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

    def get_eth_balance(self, address):
        """Get ETH balance of an address."""
        try:
            balance_wei = self.w3.eth.get_balance(address)
            return self.w3.from_wei(balance_wei, 'ether')
        except Exception as e:
            print(f"Error getting ETH balance: {e}")
            return 0.0

    def get_leveraged_tokens_usd_value(self):
        """
        Calculates the total USD value of supplied collateral tokens on Aave.
        NOTE: This needs to get the *supplied* balance from Aave, not just wallet balance.
        AaveHealthMonitor.get_monitoring_summary should be able to provide this via 'total_collateral_usd'.
        """
        # Rely on the health monitor's total collateral USD value for accuracy
        monitoring_summary = self.health_monitor.get_monitoring_summary()
        if monitoring_summary and 'total_collateral_usd' in monitoring_summary:
            return monitoring_summary['total_collateral_usd']
        else:
            print("❌ Could not get total collateral USD value from health monitor.")
            return 0.0 # Return 0 if unable to retrieve

    def execute_leveraged_supply_strategy(self, usdc_borrow_amount):
        """
        Executes a strategy of borrowing USDC, swapping it for other assets,
        and supplying them as collateral to increase leverage.
        Revised to supply ALL remaining USDC as DAI collateral.
        """
        print(f"\n⚙️ Executing Leveraged Supply Strategy with {usdc_borrow_amount:.2f} USDC...")

        if not self.aave.borrow_from_aave(usdc_borrow_amount, self.usdc_address):
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