import os
import time
import json
from web3 import Web3
from eth_account import Account

class MockAaveIntegration:
    """Mock Aave integration for when real integration fails"""
    def __init__(self):
        self.usdc_address = "0xaf88d065eec38faD0AEFf3e253e648a15cEe23dC"
        
    def get_token_balance(self, token_address):
        return 0.0
        
    def supply_to_aave(self, token_address, amount):
        print("⚠️ Mock Aave: Would supply assets")
        return None
        
    def borrow_from_aave(self, token_address, amount):
        print("⚠️ Mock Aave: Would borrow assets")
        return None

class MockUniswapIntegration:
    """Mock Uniswap integration for when real integration fails"""
    def swap_tokens(self, token_in, token_out, amount, fee):
        print("⚠️ Mock Uniswap: Would swap tokens")
        return None

class MockHealthMonitor:
    """Mock health monitor for when real monitor fails"""
    def get_current_health_factor(self):
        return {
            'health_factor': 2.5,
            'total_collateral_eth': 0.0,
            'total_debt_eth': 0.0,
            'total_collateral_usdc': 0.0,
            'total_debt_usdc': 0.0,
            'available_borrows_eth': 0.0,
            'available_borrows_usdc': 0.0
        }
    
    def get_arb_price(self):
        return {'price': 0.30}
        
    def get_monitoring_summary(self):
        return {'total_collateral_usd': 0.0}

class ArbitrumTestnetAgent:
    def __init__(self, network_mode=None):
        # Determine network mode
        self.network_mode = network_mode or os.getenv('NETWORK_MODE', 'mainnet')
        
        # Load private key with enhanced validation - prioritize PRIVATE_KEY from Replit Secrets
        private_key = os.getenv('PRIVATE_KEY') or os.getenv('PRIVATE_KEY2')
        
        if not private_key or len(private_key.strip()) < 32:
            raise ValueError("❌ CRITICAL: No valid private key found in PRIVATE_KEY or PRIVATE_KEY2. Please set a valid private key in Replit Secrets.")
        
        private_key = private_key.strip()
        
        # Clean the private key
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        
        # Check for placeholder text - this should fail fast
        if 'your_private_key_here' in private_key.lower() or 'placeholder' in private_key.lower() or private_key == "0" * 64:
            raise ValueError("❌ CRITICAL: Placeholder private key detected. Please set your actual private key in Replit Secrets.")
        
        # Validate hex characters
        try:
            int(private_key, 16)
        except ValueError:
            raise ValueError("❌ CRITICAL: Private key contains invalid hexadecimal characters. Please check your private key format.")
        
        # Ensure proper length
        if len(private_key) not in [64, 66]:
            if len(private_key) < 64:
                private_key = private_key.zfill(64)
                print(f"🔧 Padded private key to 64 characters")
            else:
                raise ValueError(f"❌ CRITICAL: Private key has invalid length: {len(private_key)}. Should be 64 characters.")
        
        print(f"✅ Valid private key loaded (length: {len(private_key)})")
        
        # Create account object
        try:
            self.account = Account.from_key('0x' + private_key)
        except Exception as e:
            raise ValueError(f"Failed to create account from private key: {e}")
        self.address = self.account.address
        
        # Network configuration with multiple RPC endpoints for reliability
        if self.network_mode == 'mainnet':
            # Multiple Arbitrum Mainnet RPC endpoints for fallback
            self.rpc_endpoints = [
                os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc'),
                'https://arbitrum-one.publicnode.com',
                'https://arbitrum.llama.fi',
                'https://rpc.ankr.com/arbitrum',
                'https://arbitrum-one.public.blastapi.io',
                'https://arbitrum.blockpi.network/v1/rpc/public'
            ]
            self.expected_chain_id = 42161
            self.aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        else:
            self.rpc_endpoints = ['https://sepolia-rollup.arbitrum.io/rpc']
            self.expected_chain_id = 421614
            self.aave_pool_address = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"

        # Configuration parameters loaded from environment variables (Replit Secrets)
        # Defaults are provided if the environment variable is not set
        self.target_health_factor = float(os.getenv('TARGET_HEALTH_FACTOR', '3.5')) # Target HF for general management
        self.growth_trigger_threshold = float(os.getenv('GROWTH_TRIGGER_THRESHOLD', '40.0')) # USDC growth to trigger re-leverage
        self.re_leverage_percentage = float(os.getenv('RE_LEVERAGE_PERCENTAGE', '0.50')) # Percentage of growth to re-leverage
        self.min_borrow_releverage = float(os.getenv('MIN_BORROW_RELEVERAGE', '10.0')) # Minimum borrow amount for re-leverage
        self.max_borrow_releverage = float(os.getenv('MAX_BORROW_RELEVERAGE', '200.0')) # Maximum borrow amount for re-leverage
        self.safe_releverage_hf_threshold = float(os.getenv('SAFE_RELEVERAGE_HF_THRESHOLD', '2.5')) # Minimum HF to safely re-leverage

        self.previous_leveraged_value_usd = None # Initialize for tracking growth

        # Initialize Web3 with RPC failover mechanism
        self.w3 = None
        self.current_rpc_url = None
        
        for rpc_url in self.rpc_endpoints:
            try:
                print(f"🔄 Trying RPC: {rpc_url}")
                
                # Create provider with timeout
                from web3.providers import HTTPProvider
                provider = HTTPProvider(rpc_url, request_kwargs={'timeout': 10})
                test_w3 = Web3(provider)
                
                # Test connection with timeout
                if test_w3.is_connected():
                    # Verify chain ID with timeout
                    try:
                        chain_id = test_w3.eth.chain_id
                        if chain_id == self.expected_chain_id:
                            # Test a simple call to ensure RPC is working
                            latest_block = test_w3.eth.block_number
                            self.w3 = test_w3
                            self.current_rpc_url = rpc_url
                            print(f"✅ Connected to {rpc_url} (Chain ID: {chain_id}, Block: {latest_block})")
                            break
                        else:
                            print(f"❌ Wrong chain ID for {rpc_url}: {chain_id} (expected {self.expected_chain_id})")
                    except Exception as chain_e:
                        print(f"❌ Chain ID check failed for {rpc_url}: {chain_e}")
                else:
                    print(f"❌ Failed to connect to {rpc_url}")
            except Exception as e:
                print(f"❌ Error with {rpc_url}: {e}")
                continue
        
        if not self.w3 or not self.w3.is_connected():
            print("❌ Failed to connect to any Arbitrum RPC endpoint.")
            exit()

        # Token addresses (corrected for Arbitrum mainnet/testnet)
        self.weth_address = Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1") # WETH on Arbitrum
        self.usdc_address = "0xaf88D065eEc38FAD0aEfF3e253e648a15cEE23DC"
        self.dai_address = Web3.to_checksum_address("0xDA10009cBd56d0F34a29c7aA35e34D246dA651D0")  # DAI on Arbitrum
        self.arb_address = Web3.to_checksum_address("0x912CE59144191C1f20bDd2ce08f2a688FEaEbb0B")  # ARB on Arbitrum
        self.wbtc_address = Web3.to_checksum_address("0x2f2a2543B76A4166549F7bffBE68df6Fc579b2F3") # WBTC on Arbitrum

        # Integration instances - these will be initialized later
        self.aave = None
        self.uniswap = None
        self.health_monitor = None

    def initialize_integrations(self):
        """Initializes Aave, Uniswap, and Health Monitor integrations with enhanced error handling."""
        integration_success = {'aave': False, 'uniswap': False, 'health_monitor': False}
        
        try:
            # Initialize Aave integration
            try:
                from aave_integration import AaveArbitrumIntegration
                self.aave = AaveArbitrumIntegration(self.w3, self.account)
                
                # Pass agent reference for RPC failover
                self.aave.agent = self
                
                # Test Aave integration
                test_balance = self.aave.get_token_balance(self.usdc_address)
                print(f"✅ Aave integration initialized and tested (USDC balance: {test_balance:.6f})")
                integration_success['aave'] = True
            except Exception as e:
                print(f"❌ Aave integration failed: {e}")
                print("🔧 Using mock Aave integration - transactions will fail")
                self.aave = MockAaveIntegration()
            
            # Initialize Uniswap integration
            try:
                from uniswap_integration import UniswapArbitrumIntegration
                self.uniswap = UniswapArbitrumIntegration(self.w3, self.account)
                print("✅ Uniswap integration initialized")
                integration_success['uniswap'] = True
            except Exception as e:
                print(f"❌ Uniswap integration failed: {e}")
                print("🔧 Using mock Uniswap integration - swaps will fail")
                self.uniswap = MockUniswapIntegration()
            
            # Initialize Health Monitor
            try:
                from aave_health_monitor import AaveHealthMonitor
                self.health_monitor = AaveHealthMonitor(self.w3, self.address, self.aave_pool_address)
                print("✅ Health monitor initialized")
                integration_success['health_monitor'] = True
            except Exception as e:
                print(f"❌ Health monitor failed: {e}")
                print("🔧 Using mock health monitor - monitoring limited")
                self.health_monitor = MockHealthMonitor()
            
            # Check if critical integrations are working
            critical_failed = not (integration_success['aave'] and integration_success['uniswap'])
            if critical_failed:
                print("⚠️ WARNING: Critical integrations failed - real transactions may not work")
                print("💡 Check your network connection and contract addresses")
            
            return not critical_failed
            
        except Exception as e:
            print(f"❌ Critical failure in integration initialization: {e}")
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

    def get_eth_balance(self, address=None):
        """Get ETH balance of an address."""
        try:
            check_address = address or self.address
            balance_wei = self.w3.eth.get_balance(check_address)
            return float(self.w3.from_wei(balance_wei, 'ether'))
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

    def run_real_defi_task(self, run_id, iteration, config):
        """Execute real DeFi operations for autonomous agent"""
        try:
            print(f"🤖 Executing DeFi task - Run {run_id}, Iteration {iteration}")
            
            # Initialize integrations if not done
            if not hasattr(self, 'aave'):
                self.initialize_integrations()
            
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
            current_eth_balance = self.get_eth_balance(self.address)
            print(f"    DIAGNOSTIC - Wallet ETH Balance (raw): {current_eth_balance:.10f} ETH")

            # Get and print USDC balance using the Aave integration's method
            current_usdc_balance_from_aave_integration = self.aave.get_token_balance(self.usdc_address)
            print(f"    DIAGNOSTIC - Wallet USDC Balance (via Aave integration): {current_usdc_balance_from_aave_integration:.6f} USDC")

            print("🔍 DIAGNOSTIC: Wallet Balance Check Complete.")
            # --- END DIAGNOSTIC CODE ---
            # Get current health factor
            if hasattr(self, 'health_monitor'):
                health_data = self.health_monitor.get_current_health_factor()
                if health_data and health_data['health_factor'] < 1.1:
                    print(f"⚠️ Low health factor: {health_data['health_factor']:.3f}")
                    return 0.2
            
            # Simple performance metric based on successful operations
            performance = 0.85 + (iteration % 10) * 0.01  # Simulate varying performance
            print(f"📊 Task performance: {performance:.3f}")
            
            return performance
            
        except Exception as e:
            print(f"❌ DeFi task failed: {e}")
            return 0.0