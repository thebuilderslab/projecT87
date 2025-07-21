import os
import json
import math
import time
import logging
from datetime import datetime
from web3 import Web3
from eth_account import Account
from aave_integration import AaveArbitrumIntegration
from uniswap_integration import UniswapArbitrumIntegration as UniswapIntegration
from aave_health_monitor import AaveHealthMonitor as HealthMonitor
from gas_fee_calculator import ArbitrumGasCalculator
from config_constants import MIN_ETH_FOR_OPERATIONS, MIN_ETH_FOR_GAS_BUFFER
import requests
import sys

class ArbitrumTestnetAgent:
    def __init__(self):
        print("🤖 Initializing Arbitrum Testnet Agent...")

        # Load environment variables
        self.private_key = os.getenv('WALLET_PRIVATE_KEY')
        # Ensure the wallet address is derived from the private key or explicitly set
        # This is where your wallet's private key will be loaded from Replit secrets
        wallet_private_key = os.environ.get("WALLET_PRIVATE_KEY")
        print(f"DEBUG: WALLET_PRIVATE_KEY loaded from environment: {'[REDACTED]' if wallet_private_key else 'None'}") # ADD THIS LINE
        if not wallet_private_key:
            raise ValueError("WALLET_PRIVATE_KEY environment variable not set.")
            # Ensure the wallet address is derived from the private key or explicitly set
            # This is where your wallet's private key will be loaded from Replit secrets
            wallet_private_key = os.environ.get("WALLET_PRIVATE_KEY")
            print(f"DEBUG: WALLET_PRIVATE_KEY loaded from environment: {'[REDACTED]' if wallet_private_key else 'None'}") # ADD THIS LINE
            if not wallet_private_key:
                raise ValueError("WALLET_PRIVATE_KEY environment variable not set.")
        self.coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.network_mode = os.getenv('NETWORK_MODE', 'testnet')

        if not self.private_key:
            raise Exception("WALLET_PRIVATE_KEY environment variable not found!")

        if not self.coinmarketcap_api_key:
            raise Exception("COINMARKETCAP_API_KEY environment variable not found!")

        # Enhanced RPC management with automatic failover
        self.rpc_manager = self._initialize_enhanced_rpc_manager()
        self.rpc_url = self.rpc_manager['primary_rpc']
        self.alternative_rpcs = self.rpc_manager['fallback_rpcs']

        print(f"🚨 NETWORK_MODE from environment: '{self.network_mode}'")
        print(f"🔗 Primary RPC: {self.rpc_url}")
        print(f"🔄 Fallback RPCs: {len(self.alternative_rpcs)} available")

        # Initialize Web3 with enhanced connection handling
        print(f"🔍 DEBUG: Attempting to create Web3 connection with primary RPC: {self.rpc_url}")
        self.w3 = self._create_robust_web3_connection(self.rpc_url)

        if not self.w3 or not self.w3.is_connected():
            # Try fallback RPCs
            print("⚠️ Primary RPC failed, trying fallbacks...")
            for i, fallback_rpc in enumerate(self.alternative_rpcs):
                try:
                    print(f"🔍 DEBUG: Trying fallback RPC {i+1}/{len(self.alternative_rpcs)}: {fallback_rpc}")
                    self.w3 = self._create_robust_web3_connection(fallback_rpc)
                    if self.w3 and self.w3.is_connected():
                        self.rpc_url = fallback_rpc
                        print(f"✅ Connected via fallback RPC: {fallback_rpc}")
                        break
                except Exception as e:
                    print(f"❌ Fallback RPC {fallback_rpc} failed: {e}")
                    continue
            else:
                raise Exception("Failed to connect to any available RPC endpoint")
        else:
            print(f"✅ Successfully connected to primary RPC: {self.rpc_url}")

        # Final verification of Web3 connection
        try:
            chain_id = self.w3.eth.chain_id
            block_number = self.w3.eth.block_number
            print(f"🔍 DEBUG: Web3 connection verified - Chain ID: {chain_id}, Latest Block: {block_number}")
        except Exception as e:
            print(f"❌ Web3 connection verification failed: {e}")
            raise Exception(f"Web3 connection not functional: {e}")

        # Initialize account after successful RPC connection
        self._initialize_account()

    def _initialize_enhanced_rpc_manager(self):
        """Initialize enhanced RPC management with only working endpoints"""
        print("🔍 DEBUG: Starting RPC manager initialization...")
        print(f"🔍 DEBUG: Network mode: {self.network_mode}")

        if self.network_mode == 'mainnet':
            # Get Alchemy RPC URL from Replit secrets first
            alchemy_rpc_url = os.getenv('ALCHEMY_RPC_URL')
            print(f"DEBUG: ALCHEMY_RPC_URL loaded from environment: {alchemy_rpc_url}")
            print(f"🔍 DEBUG: ALCHEMY_RPC_URL from env: {alchemy_rpc_url}")

            # Multiple RPC endpoints for reliability - prioritizing Alchemy if available
            self.rpc_endpoints = []

            if alchemy_rpc_url:
                self.rpc_endpoints.append(alchemy_rpc_url)
                print(f"🔗 DEBUG: Added Alchemy RPC to endpoints list: {alchemy_rpc_url[:50]}...")
            else:
                print("⚠️ DEBUG: No ALCHEMY_RPC_URL found in environment variables")

            # Add fallback endpoints (removed unauthorized Ankr endpoint)
            fallback_endpoints = [
                "https://arbitrum-mainnet.infura.io/v3/5d36f0061cbc4dda980f938ff891c141",
                "https://arb1.arbitrum.io/rpc", 
                "https://arbitrum-one.public.blastapi.io",
                "https://arbitrum-one.publicnode.com"
            ]

            self.rpc_endpoints.extend(fallback_endpoints)
            print(f"🔍 DEBUG: Total RPC endpoints to test: {len(self.rpc_endpoints)}")
            for i, rpc in enumerate(self.rpc_endpoints):
                print(f"   {i+1}. {rpc[:60]}...")

            # Test and rank only the working RPCs for performance
            tested_rpcs = self._test_and_rank_rpcs(self.rpc_endpoints, 42161)

            self.chain_id = 42161
            print("🌐 Operating on Arbitrum Mainnet")

        else:
            # Testnet RPCs
            testnet_rpcs = [
                "https://sepolia-rollup.arbitrum.io/rpc",
                "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
            ]

            tested_rpcs = self._test_and_rank_rpcs(testnet_rpcs, 421614)

            self.chain_id = 421614
            print("🧪 Operating on Arbitrum Sepolia Testnet")

        if not tested_rpcs:
            raise Exception("No working RPC endpoints found")

        print(f"🔍 DEBUG: Final RPC selection results:")
        print(f"   Primary RPC: {tested_rpcs[0]}")
        print(f"   Fallback RPCs: {len(tested_rpcs[1:])} available")

        return {
            'primary_rpc': tested_rpcs[0],
            'fallback_rpcs': tested_rpcs[1:],
            'total_available': len(tested_rpcs)
        }

    def _test_and_rank_rpcs(self, rpc_list, expected_chain_id):
        """Test RPC endpoints and rank by performance"""
        working_rpcs = []

        for rpc_url in rpc_list:
            try:
                print(f"🔍 Testing RPC: {rpc_url}")

                # Create test connection
                test_w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))

                # Comprehensive tests
                start_time = time.time()

                # Test 1: Basic connectivity
                if not test_w3.is_connected():
                    print(f"❌ Not connected: {rpc_url}")
                    continue

                # Test 2: Chain ID verification
                chain_id = test_w3.eth.chain_id
                if chain_id != expected_chain_id:
                    print(f"❌ Wrong chain ID {chain_id}: {rpc_url}")
                    continue

                # Test 3: Latest block (freshness test)
                latest_block = test_w3.eth.get_block('latest')
                if not latest_block or latest_block.number < 1000000:
                    print(f"❌ Invalid block data: {rpc_url}")
                    continue

                # Test 4: Gas price (network responsiveness)
                gas_price = test_w3.eth.gas_price
                if not gas_price or gas_price <= 0:
                    print(f"❌ Invalid gas price: {rpc_url}")
                    continue

                response_time = time.time() - start_time

                working_rpcs.append({
                    'url': rpc_url,
                    'response_time': response_time,
                    'block_number': latest_block.number,
                    'gas_price': gas_price
                })

                print(f"✅ RPC passed tests: {rpc_url} ({response_time:.2f}s)")

            except Exception as e:
                print(f"❌ RPC test failed: {rpc_url} - {e}")
                continue

        # Sort by response time (fastest first)
        working_rpcs.sort(key=lambda x: x['response_time'])

        print(f"📊 RPC Test Results: {len(working_rpcs)}/{len(rpc_list)} endpoints working")

        return [rpc['url'] for rpc in working_rpcs]

    def _create_robust_web3_connection(self, rpc_url):
        """Create a robust Web3 connection with optimized settings"""
        try:
            # Enhanced request settings for reliability
            request_kwargs = {
                'timeout': 30,
                'headers': {
                    'User-Agent': 'ArbitrumAgent/1.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            }

            # Add retry settings for better reliability
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            import requests
            session = requests.Session()

            retry_strategy = Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[429, 500, 502, 503, 504],
            )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            # Create Web3 instance
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs=request_kwargs, session=session))

            # Add middleware for PoA networks if needed
            if hasattr(Web3, 'middleware_onion'):
                from web3.middleware import geth_poa_middleware
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            return w3

        except Exception as e:
            print(f"❌ Failed to create Web3 connection to {rpc_url}: {e}")
            return None

    def switch_to_fallback_rpc(self):
        """Switch to next available working RPC endpoint"""
        if not self.alternative_rpcs:
            print("⚠️ No fallback RPCs available")
            return False

        current_rpc = self.rpc_url
        working_rpcs = [
            "https://arbitrum-mainnet.infura.io/v3/5d36f0061cbc4dda980f938ff891c141",
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.publicnode.com",
            "https://arbitrum-one.public.blastapi.io"
        ]

        # Only try working RPCs that are different from current
        available_rpcs = [rpc for rpc in working_rpcs if rpc != current_rpc]

        for fallback_rpc in available_rpcs:
            try:
                print(f"🔄 Switching to working RPC: {fallback_rpc}")

                # Test connection directly
                new_w3 = self._create_robust_web3_connection(fallback_rpc)
                if new_w3 and new_w3.is_connected():
                    # Test with a simple call
                    block_num = new_w3.eth.block_number
                    if block_num > 0:
                        # Switch to new RPC
                        self.w3 = new_w3
                        self.rpc_url = fallback_rpc

                        # Re-initialize contracts with new w3
                        if hasattr(self, 'aave') and self.aave:
                            self.aave.w3 = new_w3
                            if hasattr(self.aave, 'pool_contract'):
                                self.aave.pool_contract = new_w3.eth.contract(
                                    address=self.aave.pool_address,
                                    abi=self.aave.pool_abi
                                )

                        print(f"✅ Successfully switched to: {fallback_rpc}")
                        return True

            except Exception as e:
                print(f"❌ Working RPC {fallback_rpc} failed: {e}")
                continue

        print("❌ All working RPC fallbacks failed")
        return False

    def _initialize_account(self):
        """Initialize account after RPC setup"""
        # Validate and clean private key format
        private_key = self.private_key.strip()

        # Ensure proper format - remove 0x prefix if present for validation
        if private_key.startswith('0x'):
            hex_part = private_key[2:]
        else:
            hex_part = private_key

        # Validate hex format and length
        if len(hex_part) != 64:
            raise Exception(f"Invalid private key length: {len(hex_part)} (expected 64)")

        try:
            int(hex_part, 16)  # Test if valid hex
        except ValueError:
            raise Exception("Invalid private key format: contains non-hex characters")

        # Ensure 0x prefix for Account.from_key()
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key

        # Initialize account
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        print(f"🔑 Wallet Address: {self.address}")
        print(f"💰 AGENT INITIALIZED WITH WALLET: {self.address}")
        print(f"✅ Private key format validated and normalized")

        # Contract addresses based on network
        if self.network_mode == 'mainnet':
            # Arbitrum Mainnet addresses - Use properly checksummed addresses
            self.usdc_address = "0xAF88D065e8c38FAD0AEff3E253e648A15ceE23DC"  # Native USDC (Aave V3 supported)
            self.usdc_native_address = "0xAF88D065e8c38FAD0AEff3E253e648A15ceE23DC"  # Native USDC
            self.wbtc_address = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
            self.weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
            self.dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
            self.arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
            self.aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"

            # Mainnet aToken addresses (properly checksummed)
            self.aWBTC_address = "0x6533afac2E7BCCB20dca161449A13A2D2d5B739A"
            self.aWETH_address = "0xe50fA9b4c56454E2edF6BFf7c81b50c5F05aBE61"
            self.aUSDC_address = "0x724dc807b04555b71ed48a6896b6F41593b8C637"

            print(f"📋 Mainnet Token addresses verified:")
            print(f"   USDC: {self.usdc_address}")
            print(f"   WBTC: {self.wbtc_address}")
            print(f"   WETH: {self.weth_address}")
            print(f"   DAI: {self.dai_address}")
            print(f"   Aave Pool: {self.aave_pool_address}")
        else:
            # Testnet mode (Arbitrum Sepolia)
            self.expected_chain_id = 421614  # Arbitrum Sepolia
            self.rpc_url = "https://sepolia-rollup.arbitrum.io/rpc"
            print("🧪 Initializing for Arbitrum Sepolia Testnet")

            # Testnet token addresses (properly checksummed)
            self.usdc_address = "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"
            self.wbtc_address = "0xA2d460Bc966F6C4D5527a6ba35C6cB57c15c8F96"
            self.weth_address = "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73"
            self.dai_address = "0x5f6bB460B6d0bdA2CCaDdd7A19B5F6E7b5b8E1DB"
            self.arb_address = "0x1b20e6a3B2a86618C32A37ffcD5E98C0d20a6E42"
            self.aave_pool_address = "0x18cd499E3d7ed42FebA981ac9236A278E4Cdc2ee"

        # Initialize real blockchain integrations
        self.aave = None
        self.uniswap = None
        self.health_monitor = None
        self.gas_calculator = None
        self.enhanced_borrow_manager = None

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
        # Start with 0.0 but will sync with actual position on first run
        self.last_collateral_value_usd = 0.0
        self.baseline_initialized = False
        self.baseline_sync_attempted = False
        print("💰 Initialized last_collateral_value_usd to 0.0 (will sync with actual position)")
        print(f"📊 Initialized last_collateral_value_usd to: {self.last_collateral_value_usd}")

        # Cooldown settings
        self.last_successful_operation_time = 0  # Unix timestamp of last op
        self.operation_cooldown_seconds = 60 # 1 minute cooldown
        self.last_operation_type = None  # Track type of last operation
        return True

    def update_baseline_after_success(self, new_collateral_value=None):
        """Update baseline collateral value after successful operation"""
        try:
            if new_collateral_value is not None:
                self.last_collateral_value_usd = new_collateral_value
                print(f"✅ Updated baseline collateral: ${new_collateral_value:.2f}")

                # Save to agent baseline file
                baseline_data = {
                    'timestamp': time.time(),
                    'collateral_value_usd': new_collateral_value,
                    'updated_by': 'successful_operation'
                }

                from fix_json_serialization import safe_json_dump
                safe_json_dump(baseline_data, 'agent_baseline.json')

                return True
            else:
                print("⚠️ No collateral value provided for baseline update")
                return False

        except Exception as e:
            print(f"❌ Failed to update baseline: {e}")
            return False

    def execute_enhanced_borrow_with_retry(self, amount_usd):
        """Execute borrow with enhanced retry mechanism"""
        try:
            if hasattr(self, 'enhanced_borrow_manager') and self.enhanced_borrow_manager:
                return self.enhanced_borrow_manager.execute_enhanced_borrow_with_retry(amount_usd)
            else:
                print("❌ Enhanced borrow manager not available")
                return False
        except Exception as e:
            print(f"❌ Enhanced borrow execution failed: {e}")
            return False

    def calculate_safe_borrow_amount(self, growth_amount, available_borrows_usd):
        """Calculate a safe borrow amount based on growth and available capacity"""
        try:
            if available_borrows_usd <= 0:
                return 0.0

            # Conservative approach: use 15% of available capacity or $10, whichever is smaller
            safe_amount = min(available_borrows_usd * 0.15, 10.0)

            # Ensure minimum of $0.5 if there's any capacity
            if safe_amount > 0:
                safe_amount = max(safe_amount, 0.5)

            print(f"💰 Safe borrow calculation:")
            print(f"   Available: ${available_borrows_usd:.2f}")
            print(f"   Safe amount (15%): ${safe_amount:.2f}")

            return safe_amount

        except Exception as e:
            print(f"❌ Safe borrow calculation failed: {e}")
            return 0.0

    def detect_manual_override(self):
        """
        Detect when manual override is active through multiple indicators
        """
        import os

        # Check for manual trigger files
        manual_files = ['trigger_test.flag', 'manual_override.flag', 'force_borrow.flag']
        for file_path in manual_files:
            if os.path.exists(file_path):
                print(f"🔧 Manual override detected: {file_path} exists")
                return True

        # Check if manual_override_active attribute is set
        if hasattr(self, 'manual_override_active') and self.manual_override_active:
            print(f"🔧 Manual override detected: manual_override_active = True")
            return True

        # Check for test mode
        if os.path.exists('test_mode.flag'):
            print(f"🧪 Test mode detected - treating as manual override")
            return True

        # Check environment variable
        if os.getenv('MANUAL_OVERRIDE', '').lower() in ['true', '1', 'yes']:
            print(f"🔧 Manual override detected: MANUAL_OVERRIDE environment variable")
            return True

        return False

    def is_operation_on_cooldown(self):
        """Check if any operation is in cooldown period"""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_successful_operation_time

        if time_since_last < self.operation_cooldown_seconds:
            remaining_time = self.operation_cooldown_seconds - time_since_last
            print(f"⏰ Operation in cooldown. {remaining_time:.0f}s remaining")
            return True

        return False

    def is_operation_in_cooldown(self, operation_type="general"):
        """Check if operation is in cooldown period"""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_successful_operation_time

        # Different cooldown periods for different operations
        cooldown_periods = {
            'borrow': 60,  # 1 minute for borrow operations
            'supply': 60,  # 1 minute for supply operations  
            'swap': 60,    # 1 minute for swap operations
            'general': 60  # 1 minute for general operations
        }

        required_cooldown = cooldown_periods.get(operation_type, self.operation_cooldown_seconds)

        if time_since_last < required_cooldown:
            remaining_time = required_cooldown - time_since_last
            print(f"⏰ Operation '{operation_type}' in cooldown. {remaining_time:.0f}s remaining")
            return True, remaining_time

        return False, 0

    def record_successful_operation(self, operation_type="general"):
        """Record successful operation for cooldown tracking"""
        import time
        self.last_successful_operation_time = time.time()
        self.last_operation_type = operation_type
        
        # Track success rates
        if not hasattr(self, 'operation_stats'):
            self.operation_stats = {'attempts': 0, 'successes': 0}
        
        self.operation_stats['successes'] += 1
        success_rate = (self.operation_stats['successes'] / max(self.operation_stats['attempts'], 1)) * 100
        
        print(f"✅ Operation '{operation_type}' recorded. Success rate: {success_rate:.1f}%")
        print(f"   Next operation available in {self.operation_cooldown_seconds}s")
        
    def track_operation_attempt(self):
        """Track operation attempts for success rate calculation"""
        if not hasattr(self, 'operation_stats'):
            self.operation_stats = {'attempts': 0, 'successes': 0}
        
        self.operation_stats['attempts'] += 1
        
    def get_success_rate_prediction(self):
        """Predict success rate based on current conditions"""
        try:
            # Check network conditions
            gas_price = self.w3.eth.gas_price
            base_fee = self.w3.eth.get_block('latest').get('baseFeePerGas', gas_price)
            congestion_ratio = gas_price / base_fee if base_fee > 0 else 1.0
            
            # Check account health
            account_data = self.aave.get_user_account_data()
            health_factor = account_data.get('healthFactor', 0) if account_data else 0
            available_borrows = account_data.get('availableBorrowsUSD', 0) if account_data else 0
            
            # Calculate base success rate
            base_rate = 75  # Starting assumption
            
            # Adjust for health factor
            if health_factor > 3.0:
                base_rate += 15
            elif health_factor > 2.0:
                base_rate += 5
            elif health_factor < 1.5:
                base_rate -= 30
                
            # Adjust for network congestion
            if congestion_ratio > 3.0:
                base_rate -= 20
            elif congestion_ratio > 1.5:
                base_rate -= 10
                
            # Adjust for borrowing capacity
            if available_borrows > 50:
                base_rate += 10
            elif available_borrows < 5:
                base_rate -= 15
                
            # Historical success rate influence
            if hasattr(self, 'operation_stats') and self.operation_stats['attempts'] > 5:
                historical_rate = (self.operation_stats['successes'] / self.operation_stats['attempts']) * 100
                base_rate = (base_rate * 0.7) + (historical_rate * 0.3)  # Weighted average
                
            return max(10, min(95, base_rate))  # Cap between 10-95%
            
        except Exception as e:
            print(f"⚠️ Success rate prediction failed: {e}")
            return 60  # Conservative default

    def get_recent_performance(self, num_entries=20):
        """Get recent performance data for analysis"""
        try:
            if not hasattr(self, 'operation_stats'):
                return []
            
            # Return basic performance metrics
            recent_data = []
            if self.operation_stats.get('attempts', 0) > 0:
                success_rate = (self.operation_stats['successes'] / self.operation_stats['attempts']) * 100
                recent_data.append({
                    'performance_metric': success_rate / 100,
                    'timestamp': time.time(),
                    'operation_type': 'recent_operations'
                })
            
            return recent_data[-num_entries:]
            
        except Exception as e:
            print(f"⚠️ Failed to get recent performance: {e}")
            return []

    def initialize_integrations(self):
        """Initialize all real DeFi integrations with strict error handling"""
        try:
            # Check if already initialized to prevent multiple initializations
            if hasattr(self, 'aave') and self.aave is not None:
                print("✅ DeFi integrations already initialized, skipping...")
                return True

            print("🚀 Initializing Real DeFi Integrations...")

            # Initialize Real Aave, Uniswap, and Health Monitor Integrations
            self.aave = AaveArbitrumIntegration(self.w3, self.account)
            self.uniswap = UniswapIntegration(self.w3, self.account)
            self.health_monitor = HealthMonitor(self.w3, self.account, self.aave)
            print("✅ Initialized Real Aave, Uniswap, and Health Monitor Integrations.")

            # Initialize Gas Calculator
            self.gas_calculator = ArbitrumGasCalculator()
            print("⛽ Initialized Gas Calculator.")

            # Initialize Enhanced Borrow Manager
            try:
                from enhanced_borrow_manager import EnhancedBorrowManager
                self.enhanced_borrow_manager = EnhancedBorrowManager(self)
                print("🏦 Initialized Enhanced Borrow Manager.")
            except ImportError as e:
                print(f"⚠️ Enhanced Borrow Manager not available: {e}")
                self.enhanced_borrow_manager = None

            # Token approvals with gas optimization
            tokens_to_approve = [
                ("USDC", self.usdc_address),
                ("WBTC", self.wbtc_address),
                ("WETH", self.weth_address),
                ("DAI", self.dai_address)
            ]

            for token_name, token_address in tokens_to_approve:
                print(f"🚀 Approving {token_name} for Aave Pool...")

                try:
                    # Approve token with a very large but finite amount instead of infinity
                    max_approval_amount = 2**256 - 1  # Maximum uint256 value

                    # The approve_token method handles gas optimization internally
                    self.aave.approve_token(
                        token_address,
                        max_approval_amount
                    )
                    print(f"✅ {token_name} approved for Aave with optimized gas")
                    time.sleep(2)

                except Exception as e:
                    print(f"⚠️ {token_name} approval failed: {e}")
                    print(f"   Continuing with next token...")
                    continue

            print("✅ All DeFi integrations initialized successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize DeFi integrations: {e}")
            return False

    def check_network_status(self):
        """Checks the network status with comprehensive validation."""
        try:
            if not self.w3.is_connected():
                return False, "Not connected to Web3 provider."

            # Get network info
            latest_block = self.w3.eth.block_number
            gas_price = self.w3.eth.gas_price
            actual_chain_id = self.w3.eth.chain_id

            # Enhanced network congestion detection
            base_fee = self.w3.eth.get_block('latest').get('baseFeePerGas', gas_price)
            congestion_ratio = gas_price / base_fee if base_fee > 0 else 1.0

            print(f"🌐 Network Congestion Analysis:")
            print(f"   Base Fee: {self.w3.from_wei(base_fee, 'gwei'):.2f} gwei")
            print(f"   Current Gas: {self.w3.from_wei(gas_price, 'gwei'):.2f} gwei") 
            print(f"   Congestion Ratio: {congestion_ratio:.2f}x")

            # Warn if network is congested (>3x base fee)
            if congestion_ratio > 3.0:
                print(f"⚠️ HIGH NETWORK CONGESTION - Transactions may be rejected or delayed")
                print(f"💡 Consider waiting for lower congestion or using higher gas prices")

            print(f"🌐 Network Connected: Block {latest_block}, Gas Price: {Web3.from_wei(gas_price, 'gwei')} Gwei")
            print(f"🔗 RPC Endpoint: {self.rpc_url}")
            print(f"⛓️ Chain ID: {actual_chain_id} (Expected: {self.chain_id})")

            # Validate chain ID matches expected
            if actual_chain_id != self.chain_id:
                return False, f"Chain ID mismatch: got {actual_chain_id}, expected {self.chain_id}"

            # Test Aave pool contract accessibility
            try:
                pool_contract = self.w3.eth.contract(
                    address=self.aave_pool_address,
                    abi=[{
                        "inputs": [],
                        "name": "POOL_REVISION",
                        "outputs": [{"name": "", "type": "uint256"}],
                        "stateMutability": "view",
                        "type": "function"
                    }]
                )
                revision = pool_contract.functions.POOL_REVISION().call()
                print(f"✅ Aave Pool accessible: Revision {revision}")
            except Exception as e:
                print(f"⚠️ Aave Pool access issue: {e}")

            return True, "Connected and validated"
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
        #    return 0.0 # Return 0 if unable toretrieve # Original Code
        return 0.0  # Returning 0.0 directly because the function is not being used.

    def analyze_borrow_failure(self):
        """Analyze borrow failure and provide diagnostics"""
        try:
            print(f"\n🔍 BORROW FAILURE ANALYSIS:")

            # Get current Aave account data
            pool_abi = [{
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
            }]

            pool_contract = self.w3.eth.contract(address=self.aave_pool_address, abi=pool_abi)
            account_data = pool_contract.functions.getUserAccountData(self.address).call()

            collateral_usd = account_data[0] / (10**8)
            debt_usd = account_data[1] / (10**8)
            available_borrows_usd = account_data[2] / (10**8)
            health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')

            print(f"   💰 Collateral: ${collateral_usd:.2f}")
            print(f"   💳 Debt: ${debt_usd:.2f}")
            print(f"   📊 Available Borrows: ${available_borrows_usd:.2f}")
            print(f"   ❤️ Health Factor: {health_factor:.4f}")

            # Enhanced analysis based on specific failure patterns
            if health_factor < 1.5:
                print(f"   ⚠️ ISSUE: Health factor too low for borrowing")
                print(f"   💡 SUGGESTION: Add more collateral to improve health factor")
            elif available_borrows_usd < 1.0:
                print(f"   ⚠️ ISSUE: Insufficient borrowing capacity")
                print(f"   💡 SUGGESTION: Add more collateral or repay existing debt")
            else:
                print(f"   ⚠️ ISSUE: Transaction simulation failed - likely gas or contract interaction issue")
                print(f"   💡 SUGGESTIONS:")
                print(f"      - Check if USDC borrowing is enabled on this market")
                print(f"      - Verify gas settings and network connectivity")
                print(f"      - Try smaller borrow amount ($1-5 USDC)")
                print(f"      - Check for any Aave protocol restrictions")

        except Exception as analysis_error:
            print(f"   ❌ Borrow failure analysis error: {analysis_error}")
            import traceback
            print(f"   🔍 Traceback: {traceback.format_exc()}")

    def execute_leveraged_supply_strategy(self, amount_to_borrow_usdc=10):
        """Execute REVISED DAI-based leveraged supply strategy with conditional ETH acquisition and dedicated WBTC allocation"""
        # This strategy is extremely sensitive to gas costs and slippage.

        # STEP 1: Determine borrow amount based on available capacity
        try:
            print("\n💰 Determining borrow amount...")
            account_data = self.aave.get_user_account_data()
            if not account_data:
                print("❌ Could not retrieve account data. Aborting strategy.")
                return False

            available_borrows_usdc = account_data['availableBorrowsUSD']
            print(f"📊 Available borrows: ${available_borrows_usdc:.2f}")

            # Limit borrow amount to a conservative value (e.g., 10% of available)
            amount_to_borrow_usdc = min(available_borrows_usdc * 0.10, 10.0)
            print(f"   Safe amount (10%): ${amount_to_borrow_usdc:.2f}")

            if amount_to_borrow_usdc < 1.0:
                print(f"   Not enough borrow capacity: ${amount_to_borrow_usdc:.2f} < $1.0")
                print("Aborting leveraged supply strategy.")
                return False

        except Exception as e:
            print(f"❌ Error determining borrow amount: {e}")
            return False

        # STEP 2: Borrow USDC
        # Borrow USDC
        try:
            # Use DAI borrowing instead of USDC
            print(f"🔄 Converting USDC borrow to DAI borrow: ${amount_to_borrow_usdc:.2f}")
            success_borrow = self.aave.borrow(amount_to_borrow_usdc, self.dai_address)
            if not success_borrow:
                print("❌ Failed to borrow DAI. Aborting strategy.")
                return False
            print(f"✅ Borrowed {amount_to_borrow_usdc} DAI successfully.")
        except Exception as e:
            print(f"❌ Error during DAI borrow: {e}")
            import traceback
            traceback.print_exc()
            return False

        # STEP 3: Swap 3 USDC for WBTC and supply
        # Swap 3 DAI for WBTC and supply
        try:
            print("  Swapping 3 DAI for WBTC and supplying to Aave...")
            # First swap DAI to WBTC
            wbtc_swap_success = self.uniswap.swap_tokens(self.dai_address, self.wbtc_address, 3, 500)

            if wbtc_swap_success:
                print("  ✅ Successfully swapped DAI for WBTC.")
                # Then supply WBTC to Aave
                wbtc_supply_success = self.aave.supply_to_aave(self.wbtc_address, wbtc_swap_success)

                if wbtc_supply_success:
                    print("  ✅ Successfully supplied WBTC to Aave.")
                else:
                    print("  ❌ Failed to supply WBTC to Aave.")
            else:
                print("  ❌ Failed to swap DAI for WBTC.")

        except Exception as e:
            print(f"  ❌ Error during WBTC swap and supply: {e}")
            return False

        # STEP 4: Swap 2 USDC for WETH and supply
        # Swap 2 DAI for WETH and supply
        try:
            print("  Swapping 2 DAI for WETH and supplying to Aave...")
            # First swap DAI to WETH
            weth_swap_success = self.uniswap.swap_tokens(self.dai_address, self.weth_address, 2, 500)

            if weth_swap_success:
                print("  ✅ Successfully swapped DAI for WETH.")
                # Then supply WETH to Aave
                weth_supply_success = self.aave.supply_to_aave(self.weth_address, weth_swap_success)

                if weth_supply_success:
                    print("  ✅ Successfully supplied WETH to Aave.")
                else:
                    print("  ❌ Failed to supply WETH to Aave.")
            else:
                print("  ❌ Failed to swap DAI for WETH.")

        except Exception as e:
            print(f"  ❌ Error during WETH swap and supply: {e}")
            return False

        # STEP 5: ETH Gas Buffer Management
        try:
            print("\n⛽ ETH Gas Buffer Management...")
            current_eth_balance = self.get_eth_balance()

            MIN_ETH_GAS_THRESHOLD = 0.02  # Slightly lower threshold
            MIN_ETH_GAS_BUFFER = 0.05
            print(f"💰 Current ETH Balance: {current_eth_balance:.4f} ETH")
            print(f"   Threshold: {MIN_ETH_GAS_THRESHOLD:.4f} ETH,  Buffer: {MIN_ETH_GAS_BUFFER:.4f} ETH")

            if current_eth_balance < MIN_ETH_GAS_THRESHOLD:
                print(f"  Wallet ETH is below threshold. Swapping 1 DAI for ETH.")
                # Swap 1 DAI for WETH (then unwrap to ETH)
                success_eth_swap = self.uniswap.swap_tokens(self.dai_address, self.weth_address, 1, 500)
                if not success_eth_swap:
                    print("  ⚠️ Failed to swap 1 DAI for ETH. This might impact future transactions if gas runs out.")
                else:
                    print("  ✅ Successfully swapped 1 DAI for ETH to maintain gas buffer.")
            else:
                print(f"  Wallet ETH is sufficient. Supplying 1 DAI to Aave as collateral instead of swapping for ETH.")
                # Supply the 1 DAI directly to Aave
                success_supply_eth_dai_yield = self.aave.supply_to_aave(self.dai_address, 1)

        except Exception as e:
            print(f"  ❌ Error during ETH gas management: {e}")
            return False

        # STEP 6: Remaining balance supply
        # Supply remaining 4 DAI directly (2 + 2 allocation)
        try:
            print("  Supplying remaining 4 DAI directly to Aave...")
            # Check current DAI balance
            dai_balance = self.aave.get_token_balance(self.dai_address)
            supply_amount = min(4, dai_balance)  # Supply up to 4 DAI or available balance

            if supply_amount > 0:
                # Approve and supply DAI
                if self.aave.approve_token(self.dai_address, supply_amount):
                    success_dai_supply = self.aave.supply_to_aave(self.dai_address, supply_amount)
                    if success_dai_supply:
                        print(f"  ✅ Successfully supplied {supply_amount:.6f} DAI directly to Aave.")
                    else:
                        print("  ❌ Failed to supply DAI directly to Aave.")
                else:
                    print("  ❌ Failed to approve DAI for Aave.")
            else:
                print("  ❌ No DAI balance available for direct supply.")

        except Exception as e:
            print(f"  ❌ Error during remaining balance supply: {e}")
            return False

        # Final Report
        print("\n📊 Leveraged Supply Strategy Execution Report:")
        print("  ✅ Strategy completed without fatal errors.")
        print("  ⚠️ Check individual steps for potential minor issues.")

        return True

    def run_real_defi_task(self, run_id, iteration, config):
        """Main DeFi task execution method for autonomous operation"""
        try:
            print(f"\n🚀 STARTING AUTONOMOUS RUN: {run_id}, ITERATION: {iteration}")
            print("=" * 60)

            # Performance tracking
            performance_score = 0.0
            operations_completed = 0
            
            # Step 1: Network and wallet validation
            print("📋 Step 1: Network and wallet validation...")
            network_ok, network_msg = self.check_network_status()
            if not network_ok:
                print(f"❌ Network validation failed: {network_msg}")
                return 0.1
            
            print(f"✅ Network validation passed: {network_msg}")
            operations_completed += 1

            # Step 2: Check emergency stop
            if self.check_emergency_stop():
                print("🛑 Emergency stop activated - halting operations")
                return 0.0

            # Step 3: Wallet readiness check
            eth_balance = self.get_eth_balance()
            print(f"💰 Current ETH balance: {eth_balance:.6f} ETH")
            
            if eth_balance < MIN_ETH_FOR_OPERATIONS:
                print(f"❌ Insufficient ETH for operations: {eth_balance:.6f} < {MIN_ETH_FOR_OPERATIONS}")
                return 0.2
            
            operations_completed += 1

            # Step 4: Get Aave account data and health factor
            print("📊 Step 4: Checking Aave account status...")
            try:
                account_data = self.aave.get_user_account_data()
                if account_data:
                    health_factor = account_data.get('healthFactor', 0)
                    available_borrows = account_data.get('availableBorrowsUSD', 0)
                    total_collateral = account_data.get('totalCollateralUSD', 0)
                    
                    print(f"   Health Factor: {health_factor:.4f}")
                    print(f"   Collateral: ${total_collateral:.2f}")
                    print(f"   Available Borrows: ${available_borrows:.2f}")
                    
                    operations_completed += 1
                    performance_score += 0.2
                    
                    # Step 5: Safe operation execution based on conditions
                    if health_factor > 1.5 and available_borrows > 1.0:
                        print("✅ Health and capacity conditions met for DAI borrowing")
                        
                        # Check for collateral growth trigger
                        current_collateral = total_collateral
                        collateral_growth = current_collateral - self.last_collateral_value_usd
                        growth_threshold = self.growth_trigger_threshold  # Default $40 from config
                        
                        print(f"📊 Collateral Growth Analysis:")
                        print(f"   Current: ${current_collateral:.2f}")
                        print(f"   Baseline: ${self.last_collateral_value_usd:.2f}")
                        print(f"   Growth: ${collateral_growth:.2f}")
                        print(f"   Threshold: ${growth_threshold:.2f}")
                        
                        # HYBRID APPROACH: Growth-triggered OR capacity optimization
                        manual_override = self.detect_manual_override()
                        growth_triggered = collateral_growth >= growth_threshold
                        
                        # New: Capacity optimization trigger
                        capacity_utilization = available_borrows / max(total_collateral * 0.8, 1)  # 80% max LTV assumption
                        capacity_optimization_enabled = self._should_optimize_capacity(available_borrows, capacity_utilization)
                        
                        print(f"🎯 Trigger Analysis:")
                        print(f"   Growth triggered: {growth_triggered} (${collateral_growth:.2f} >= ${growth_threshold:.2f})")
                        print(f"   Capacity optimization: {capacity_optimization_enabled} ({capacity_utilization:.1%} utilization)")
                        print(f"   Manual override: {manual_override}")
                        
                        if growth_triggered or capacity_optimization_enabled or manual_override:
                            trigger_reason = []
                            if growth_triggered:
                                trigger_reason.append(f"🚀 GROWTH TRIGGERED: ${collateral_growth:.2f}")
                            if capacity_optimization_enabled:
                                trigger_reason.append(f"⚡ CAPACITY OPTIMIZATION: {capacity_utilization:.1%} utilization")
                            if manual_override:
                                trigger_reason.append(f"🔧 MANUAL OVERRIDE")
                            
                            print(" | ".join(trigger_reason))
                            
                            # Predict success rate
                            predicted_success = self.get_success_rate_prediction()
                            print(f"📊 Predicted success rate: {predicted_success:.1f}%")
                            
                            # Check cooldown
                            if self.is_operation_on_cooldown():
                                print("⏰ Operations in cooldown period")
                                performance_score += 0.1
                            else:
                                # Calculate safe borrow amount using hybrid logic
                                if growth_triggered:
                                    safe_amount = self.calculate_safe_borrow_amount(collateral_growth, available_borrows)
                                else:
                                    # Capacity-based: smaller, more frequent amounts
                                    safe_amount = self._calculate_capacity_optimized_amount(available_borrows, capacity_utilization)
                        else:
                            print(f"⏸️ NO TRIGGERS ACTIVATED")
                            print(f"   Growth needed: ${max(0, growth_threshold - collateral_growth):.2f}")
                            print(f"   Capacity utilization: {capacity_utilization:.1%} (threshold: 20%)")
                            performance_score += 0.2
                            safe_amount = 0
                            
                            # Track this attempt
                            self.track_operation_attempt()
                            
                            if safe_amount > 0:
                                print(f"🎯 Attempting safe DAI borrow: ${safe_amount:.2f}")
                                
                                # Execute enhanced DAI-only borrow
                                if hasattr(self, 'enhanced_borrow_manager') and self.enhanced_borrow_manager:
                                    borrow_success = self.enhanced_borrow_manager.execute_enhanced_borrow_with_retry(safe_amount)
                                    if borrow_success:
                                        print(f"✅ DAI borrow successful!")
                                        self.record_successful_operation('borrow')
                                        
                                        # Update baseline collateral after successful operation
                                        self.update_baseline_after_success(current_collateral)
                                        
                                        performance_score += 0.4
                                        operations_completed += 2
                                        
                                        # Execute swap and supply sequence after successful borrow
                                        self._execute_post_borrow_operations(safe_amount)
                                        
                                    else:
                                        print(f"❌ DAI borrow failed")
                                        performance_score += 0.1
                                else:
                                    # Fallback to direct DAI borrow
                                    borrow_success = self.aave.borrow(safe_amount, self.dai_address)
                                    if borrow_success:
                                        print(f"✅ Direct DAI borrow successful!")
                                        self.record_successful_operation('borrow')
                                        performance_score += 0.3
                                        operations_completed += 2
                                        
                                        # Execute swap and supply sequence after successful borrow
                                        self._execute_post_borrow_operations(safe_amount)
                                        
                                    else:
                                        print(f"❌ Direct DAI borrow failed")
                                        self.analyze_borrow_failure()
                                        performance_score += 0.1
                    else:
                        print(f"⚠️ Conditions not favorable for borrowing:")
                        print(f"   Health Factor: {health_factor:.4f} (need > 1.5)")
                        print(f"   Available Borrows: ${available_borrows:.2f} (need > $1.0)")
                        performance_score += 0.2
                else:
                    print("❌ Could not retrieve Aave account data")
                    performance_score += 0.1
                    
            except Exception as aave_error:
                print(f"❌ Aave interaction error: {aave_error}")
                performance_score += 0.1

            # Step 6: Final status report
            print(f"\n📊 AUTONOMOUS TASK SUMMARY:")
            print(f"   Operations completed: {operations_completed}")
            print(f"   Performance score: {performance_score:.3f}")
            print(f"   Run: {run_id}, Iteration: {iteration}")
            
            # Ensure minimum performance score
            performance_score = max(performance_score, 0.1)
            
            return performance_score

        except Exception as e:
            print(f"❌ Critical error in autonomous task: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return 0.1


    def _execute_post_borrow_operations(self, borrowed_amount):
        """Execute swap and supply operations after successful DAI borrow"""
        try:
            print(f"\n🔄 EXECUTING POST-BORROW OPERATIONS")
            print(f"💰 Borrowed amount: ${borrowed_amount:.2f} DAI")
            
            # Wait for borrow confirmation
            print("⏳ Waiting for DAI borrow confirmation...")
            import time
            time.sleep(10)
            
            # Get current DAI balance
            dai_balance = self.aave.get_token_balance(self.dai_address)
            print(f"💰 Current DAI balance: {dai_balance:.6f} DAI")
            
            if dai_balance < 1.0:
                print("⚠️ Insufficient DAI balance for swaps and supplies")
                return False
            
            # Allocate DAI for different operations
            allocation = self._calculate_dai_allocation(dai_balance)
            
            # Step 1: Swap DAI for WBTC and supply
            if allocation['wbtc_swap'] > 0:
                print(f"\n🔄 Step 1: Swapping ${allocation['wbtc_swap']:.2f} DAI for WBTC...")
                wbtc_swap_result = self.uniswap.swap_tokens(
                    self.dai_address, 
                    self.wbtc_address, 
                    allocation['wbtc_swap'], 
                    500
                )
                
                if wbtc_swap_result:
                    print("✅ DAI → WBTC swap successful!")
                    time.sleep(10)  # Wait for swap confirmation
                    
                    # Supply WBTC to Aave
                    wbtc_balance = self.aave.get_token_balance(self.wbtc_address)
                    if wbtc_balance > 0:
                        supply_result = self.aave.supply_wbtc_to_aave(wbtc_balance)
                        if supply_result:
                            print("✅ WBTC supplied to Aave!")
                        else:
                            print("❌ WBTC supply failed")
                else:
                    print("❌ DAI → WBTC swap failed")
            
            # Step 2: Swap DAI for WETH and supply
            if allocation['weth_swap'] > 0:
                print(f"\n🔄 Step 2: Swapping ${allocation['weth_swap']:.2f} DAI for WETH...")
                weth_swap_result = self.uniswap.swap_tokens(
                    self.dai_address, 
                    self.weth_address, 
                    allocation['weth_swap'], 
                    500
                )
                
                if weth_swap_result:
                    print("✅ DAI → WETH swap successful!")
                    time.sleep(10)  # Wait for swap confirmation
                    
                    # Supply WETH to Aave
                    weth_balance = self.aave.get_token_balance(self.weth_address)
                    if weth_balance > 0:
                        supply_result = self.aave.supply_to_aave(self.weth_address, weth_balance)
                        if supply_result:
                            print("✅ WETH supplied to Aave!")
                        else:
                            print("❌ WETH supply failed")
                else:
                    print("❌ DAI → WETH swap failed")
            
            # Step 3: Supply remaining DAI directly
            if allocation['direct_supply'] > 0:
                print(f"\n🔄 Step 3: Supplying ${allocation['direct_supply']:.2f} DAI directly to Aave...")
                dai_supply_result = self.aave.supply_to_aave(self.dai_address, allocation['direct_supply'])
                if dai_supply_result:
                    print("✅ DAI supplied to Aave!")
                else:
                    print("❌ DAI supply failed")
            
            print("\n✅ Post-borrow operations completed!")
            return True
            
        except Exception as e:
            print(f"❌ Post-borrow operations failed: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return False

    def _calculate_dai_allocation(self, total_dai):
        """Calculate DAI allocation for different operations"""
        try:
            print(f"📊 Calculating DAI allocation for {total_dai:.6f} DAI")
            
            # Conservative allocation strategy
            allocation = {
                'wbtc_swap': 0,
                'weth_swap': 0, 
                'direct_supply': 0
            }
            
            if total_dai >= 8.0:
                # If we have enough DAI, allocate for swaps and supply
                allocation['wbtc_swap'] = 3.0  # $3 for WBTC
                allocation['weth_swap'] = 2.0  # $2 for WETH
                allocation['direct_supply'] = total_dai - 5.0  # Rest for direct supply
            elif total_dai >= 5.0:
                # Medium allocation
                allocation['wbtc_swap'] = 2.0
                allocation['weth_swap'] = 1.0
                allocation['direct_supply'] = total_dai - 3.0
            else:
                # Small allocation - just supply directly
                allocation['direct_supply'] = total_dai
            
            print(f"📋 DAI Allocation:")
            print(f"   WBTC Swap: ${allocation['wbtc_swap']:.2f}")
            print(f"   WETH Swap: ${allocation['weth_swap']:.2f}")
            print(f"   Direct Supply: ${allocation['direct_supply']:.2f}")
            
            return allocation
            
        except Exception as e:
            print(f"❌ Allocation calculation failed: {e}")
            return {'wbtc_swap': 0, 'weth_swap': 0, 'direct_supply': total_dai}

import os
import json
import math
import time
import logging
from datetime import datetime
from web3 import Web3
from eth_account import Account
from aave_integration import AaveArbitrumIntegration
from uniswap_integration import UniswapArbitrumIntegration as UniswapIntegration
from aave_health_monitor import AaveHealthMonitor as HealthMonitor
from gas_fee_calculator import ArbitrumGasCalculator
from config_constants import MIN_ETH_FOR_OPERATIONS, MIN_ETH_FOR_GAS_BUFFER
import requests
import sys

class ArbitrumTestnetAgent:
    def __init__(self):
        # ... existing initialization code ...
        
        # Hybrid system configuration
        self.capacity_optimization_threshold = float(os.getenv('CAPACITY_OPTIMIZATION_THRESHOLD', '0.20'))  # 20% utilization threshold
        self.capacity_optimization_cooldown = 300  # 5 minutes between capacity optimizations
        self.last_capacity_optimization = 0
        
    def _should_optimize_capacity(self, available_borrows, capacity_utilization):
        """Determine if capacity optimization should trigger"""
        try:
            # Conditions for capacity optimization:
            # 1. Available borrows > $10 (meaningful amount)
            # 2. Capacity utilization < 20% (underutilized)
            # 3. Not in capacity optimization cooldown
            # 4. Market conditions favorable
            
            current_time = time.time()
            
            # Check basic thresholds
            if available_borrows < 10.0:
                return False
                
            if capacity_utilization >= self.capacity_optimization_threshold:
                return False
                
            # Check cooldown for capacity optimizations
            if current_time - self.last_capacity_optimization < self.capacity_optimization_cooldown:
                return False
                
            # Check market conditions (gas prices, network congestion)
            gas_price = self.w3.eth.gas_price
            base_fee = self.w3.eth.get_block('latest').get('baseFeePerGas', gas_price)
            network_congestion = gas_price / base_fee if base_fee > 0 else 1.0
            
            # Skip capacity optimization during high network congestion
            if network_congestion > 2.0:
                print(f"⏸️ Skipping capacity optimization due to network congestion: {network_congestion:.2f}x")
                return False
                
            print(f"✅ Capacity optimization conditions met:")
            print(f"   Available: ${available_borrows:.2f} > $10")
            print(f"   Utilization: {capacity_utilization:.1%} < {self.capacity_optimization_threshold:.1%}")
            print(f"   Network congestion: {network_congestion:.2f}x < 2.0x")
            
            return True
            
        except Exception as e:
            print(f"❌ Capacity optimization check failed: {e}")
            return False
            
    def _calculate_capacity_optimized_amount(self, available_borrows, capacity_utilization):
        """Calculate optimal borrow amount for capacity optimization"""
        try:
            # For capacity optimization, use smaller amounts more frequently
            # This reduces risk while maintaining capital efficiency
            
            # Base amount: 5-15% of available capacity
            base_percentage = 0.05 + (0.10 * (1 - capacity_utilization))  # 5-15% based on current utilization
            base_amount = available_borrows * base_percentage
            
            # Apply constraints
            min_amount = 1.0   # Minimum $1
            max_amount = 25.0  # Maximum $25 for capacity optimization
            
            optimal_amount = max(min_amount, min(base_amount, max_amount))
            
            print(f"💡 Capacity optimization calculation:")
            print(f"   Base percentage: {base_percentage:.1%}")
            print(f"   Base amount: ${base_amount:.2f}")
            print(f"   Constrained amount: ${optimal_amount:.2f}")
            
            # Update last optimization time
            self.last_capacity_optimization = time.time()
            
            return optimal_amount
            
        except Exception as e:
            print(f"❌ Capacity optimization calculation failed: {e}")
            return 0.0
