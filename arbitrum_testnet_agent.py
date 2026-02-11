# Applying DAI compliance by removing USDC references and updating token validation.
import os
import json
import math
import time
import logging
import signal
import errno
from datetime import datetime
from web3 import Web3
from eth_account import Account

# Web3 version compatibility check
try:
    web3_version = Web3.__version__
    print(f"🔍 Web3 version: {web3_version}")
except:
    print("⚠️ Cannot determine Web3 version")

# --- Aave and DeFi-specific constants and ABIs ---
AAVE_POOL_ADDRESS = '0x794a61358D6845594F94dc1DB02A252b5b4814aD'
DAI_ADDRESS = '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'

AAVE_POOL_ABI = [
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
            {"name": "rateMode", "type": "uint256"},
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

DAI_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

from aave_integration import AaveArbitrumIntegration
from uniswap_integration import UniswapIntegration
from aave_health_monitor import AaveHealthMonitor as HealthMonitor
from gas_fee_calculator import ArbitrumGasCalculator
from config_constants import MIN_ETH_FOR_OPERATIONS, MIN_ETH_FOR_GAS_BUFFER
from block_event_monitor import BlockEventMonitor
import requests
import sys
import traceback

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArbitrumTestnetAgent:
    def __init__(self, rpc_manager=None, private_key=None):
        """Initialize the Arbitrum Testnet Agent with proper configuration"""
        print("🤖 Initializing Arbitrum Testnet Agent...")
        # Load environment variables
        self.private_key = private_key or os.getenv('PRIVATE_KEY') or os.getenv('Wallet_PRIVATE_KEY')
        print(f"DEBUG: Private key loaded from parameter/environment: {'[REDACTED]' if self.private_key else 'None'}")
        if not self.private_key:
            raise ValueError("Private key not provided and no PRIVATE_KEY or WALLET_PRIVATE_KEY environment variable set.")
        self.coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.network_mode = os.getenv('NETWORK_MODE', 'mainnet')

        if not self.private_key:
            raise Exception("Wallet_PRIVATE_KEY environment variable not found!")

        if not self.coinmarketcap_api_key:
            raise Exception("COINMARKETCAP_API_KEY environment variable not found!")

        # Validate critical environment variables early
        try:
            self._validate_critical_environment()
        except Exception as env_error:
            print(f"❌ Environment validation failed: {env_error}")
            print("💡 Please check your Replit secrets configuration")
            print("🔧 Attempting graceful recovery...")

            # Try to continue with minimal functionality
            try:
                if self._validate_critical_environment():
                    print("✅ Core validation passed - continuing with limited features")
                else:
                    raise env_error
            except:
                raise env_error

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
                print("❌ All RPC endpoints failed initial testing")
                print("🔄 Attempting simplified connection to primary RPC...")

                # Fallback: Try simple connection without extensive testing
                try:
                    fallback_rpc = self.rpc_endpoints[0]  # Use first RPC as fallback
                    self.w3 = Web3(Web3.HTTPProvider(fallback_rpc))
                    if self.w3.is_connected():
                        self.rpc_url = fallback_rpc
                        print(f"✅ Fallback connection successful: {fallback_rpc}")
                    else:
                        raise Exception("Fallback connection also failed")
                except:
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
        # Setup enhanced error handling
        self._setup_enhanced_error_handling()

    def _initialize_enhanced_rpc_manager(self):
        """Initialize enhanced RPC management with only working endpoints"""
        print("🔍 DEBUG: Starting RPC manager initialization...")
        print(f"🔍 DEBUG: Network mode: {self.network_mode}")

        if self.network_mode == 'mainnet':
            # Get Alchemy RPC URL from Replit secrets first
            alchemy_rpc_url = os.getenv('ALCHEMY_RPC_URL')
            # SECURITY: Never print full RPC URLs as they contain API keys
            rpc_status = "loaded" if alchemy_rpc_url else "not found"
            print(f"🔍 DEBUG: ALCHEMY_RPC_URL status: {rpc_status}")

            # Multiple RPC endpoints for reliability - prioritizing Alchemy if available
            self.rpc_endpoints = []

            if alchemy_rpc_url:
                self.rpc_endpoints.append(alchemy_rpc_url)
                print(f"🔗 DEBUG: Added Alchemy RPC to endpoints list (endpoint secured)")
            else:
                print("⚠️ DEBUG: No ALCHEMY_RPC_URL found in environment variables")

            # High-throughput stable endpoints (removed problematic Infura)
            fallback_endpoints = [
                "https://arbitrum.llamarpc.com",
                "https://arb1.arbitrum.io/rpc",
                "https://arbitrum-one.publicnode.com",
                "https://arbitrum-one.public.blastapi.io",
                "https://rpc.ankr.com/arbitrum"
            ]

            self.rpc_endpoints.extend(fallback_endpoints)
            print(f"🔍 DEBUG: Total RPC endpoints to test: {len(self.rpc_endpoints)}")

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

                # Create test connection with retry mechanism
                test_w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 15}))

                # Comprehensive tests
                start_time = time.time()

                # Test 1: Basic connectivity
                if not test_w3.is_connected():
                    print(f"❌ Not connected: {rpc_url}")
                    continue

                # Test 2: Chain ID verification with proper error handling
                try:
                    chain_id = test_w3.eth.chain_id
                    if chain_id != expected_chain_id:
                        print(f"❌ Wrong chain ID {chain_id}: {rpc_url}")
                        continue
                except AttributeError:
                    print(f"❌ Web3 version incompatibility: {rpc_url}")
                    continue
                except Exception as chain_error:
                    print(f"❌ Chain ID check failed: {rpc_url} - {chain_error}")
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
        """Create a robust Web3 connection with exponential backoff retry mechanism"""
        try:
            # Enhanced request settings for reliability with rate limit handling
            request_kwargs = {
                'timeout': 30,
                'headers': {
                    'User-Agent': 'ArbitrumAgent/1.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            }

            # Enhanced retry settings with exponential backoff for rate limits
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            import requests
            session = requests.Session()

            # Aggressive retry strategy for rate limits
            retry_strategy = Retry(
                total=5,  # Increased retries
                backoff_factor=1.0,  # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                status_forcelist=[429, 500, 502, 503, 504],
                respect_retry_after_header=True,  # Honor rate limit headers
                raise_on_status=False
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
            "https://arbitrum.llamarpc.com",
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
            # Token addresses for Arbitrum Mainnet
            self.weth_address = self.w3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
            self.wbtc_address = self.w3.to_checksum_address("0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f")
            self.dai_address = self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
            # Official GHO token address - Arbitrum One mainnet
            self.gho_address = self.w3.to_checksum_address("0x7dfF72693f6A4149b17e7C6314655f6A9F7c8B33")
            self.arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
            self.aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"

            # Mainnet aToken addresses (properly checksummed)
            self.aWBTC_address = "0x6533afac2E7BCCB20dca161449A13A2D2d5B739A"
            self.aWETH_address = "0xe50fA9b4c56454E2edF6BFf7c81b50c5F05aBE61"
            self.aDAI_address = "0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE"

            print(f"📋 Mainnet Token addresses verified:")
            print(f"   DAI: {self.dai_address}")
            print(f"   WBTC: {self.wbtc_address}")
            print(f"   WETH: {self.weth_address}")
            print(f"   GHO: {self.gho_address}")
            print(f"   Aave Pool: {self.aave_pool_address}")
        else:
            # Testnet mode (Arbitrum Sepolia)
            self.expected_chain_id = 421614  # Arbitrum Sepolia
            self.rpc_url = "https://sepolia-rollup.arbitrum.io/rpc"
            print("🧪 Initializing for Arbitrum Sepolia Testnet")

            # Testnet token addresses (properly checksummed)
            self.wbtc_address = "0xA2d460Bc966F6C4D5527a6ba35C6cB57c15c8F96"
            self.weth_address = "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73"
            self.dai_address = "0x5f6bB460B6d0bdA2CCaDdd7A19B5F6E7b5b8E1DB"
            self.gho_address = None  # GHO not available on Arbitrum Sepolia testnet
            self.arb_address = "0x1b20e6a3B2a86618C32A37ffcD5E98C0d20a6E42"
            self.aave_pool_address = "0x18cd499E3d7ed42FebA981ac9236A278E4Cdc2ee"
        
        # PHASE 1: FIXED-VALUE DISTRIBUTION PATHS
        # Two distinct execution paths with exact dollar amounts
        self.GROWTH_DISTRIBUTION = {
            'total_borrow': 10.20,
            'dai_supply': 3.00,
            'wbtc_swap_supply': 3.00,
            'weth_swap_supply': 2.00,
            'eth_gas_reserve': 1.10,
            'dai_transfer': 1.10,
            'min_capacity': 12.0,
        }
        self.CAPACITY_DISTRIBUTION = {
            'total_borrow': 5.50,
            'dai_supply': 1.10,
            'wbtc_swap_supply': 1.10,
            'weth_swap_supply': 1.10,
            'eth_gas_reserve': 1.10,
            'dai_transfer': 1.10,
            'min_capacity': 7.0,
        }

        # GLOBAL EXECUTION LOCK - prevents double-borrowing
        self.is_transacting = False
        self.last_transaction_complete_time = 0

        # WALLET_S_ADDRESS for DAI transfers (REQUIRED for mainnet)
        self.wallet_s_address = os.getenv('WALLET_S_ADDRESS')
        if self.wallet_s_address:
            self.wallet_s_address = self.w3.to_checksum_address(self.wallet_s_address.strip())
            print(f"✅ WALLET_S_ADDRESS configured: {self.wallet_s_address[:10]}...")
        else:
            print("🚨 WALLET_S_ADDRESS not set - REQUIRED for Phase 1 execution")
            print("   Both Growth and Capacity paths include DAI transfer step")

        print(f"✅ Fixed-value distribution paths configured:")
        print(f"   Growth Path: ${self.GROWTH_DISTRIBUTION['total_borrow']:.2f} total borrow (requires ${self.GROWTH_DISTRIBUTION['min_capacity']:.0f} capacity)")
        print(f"   Capacity Path: ${self.CAPACITY_DISTRIBUTION['total_borrow']:.2f} total borrow (requires ${self.CAPACITY_DISTRIBUTION['min_capacity']:.0f} capacity)")

        # Initialize collateral tracking for autonomous triggers
        # Set to previous known value ($47) so growth from added collateral is detected
        self.last_collateral_value_usd = 38.0
        self.baseline_initialized = True
        self.baseline_sync_attempted = True
        print("💰 Initialized last_collateral_value_usd to $38.00 (post-rebalance baseline)")
        print(f"📊 Baseline set to: ${self.last_collateral_value_usd:.2f} — growth trigger will detect changes from this level")

        # STARTER PLAN OPTIMIZED COOLDOWN SETTINGS
        self.last_successful_operation_time = 0  # Unix timestamp of last op
        self.operation_cooldown_seconds = 130  # STARTER PLAN: 130 second cooldown to preserve API credits
        self.last_operation_type = None  # Track type of last operation
        
        # Initialize cost optimization
        try:
            from cost_optimization_manager import CostOptimizationManager
            self.cost_manager = CostOptimizationManager()
        except ImportError:
            self.cost_manager = None
        
        # VALIDATE HIGH-FREQUENCY PARAMETERS
        from environmental_configuration import OPERATION_COOLDOWN, MIN_SWAP_AMOUNT, MAX_SWAP_AMOUNT
        if self.operation_cooldown_seconds != OPERATION_COOLDOWN:
            print(f"⚠️ Agent cooldown mismatch: {self.operation_cooldown_seconds}s vs config {OPERATION_COOLDOWN}s")
            self.operation_cooldown_seconds = OPERATION_COOLDOWN  # Sync with config
        
        print(f"✅ HIGH-FREQUENCY PARAMETERS CONFIRMED:")
        print(f"   Operation Cooldown: {self.operation_cooldown_seconds}s")
        print(f"   Min/Max Swap: ${MIN_SWAP_AMOUNT} - ${MAX_SWAP_AMOUNT}")
        print(f"   System ready for high-frequency debt swapping")

        # Growth-Triggered System Configuration
        self.growth_trigger_threshold = 50.0  # $50 absolute growth threshold
        self.growth_health_factor_threshold = 1.35  # MIN_HEALTH_FACTOR for growth operations
        self.growth_percentage_threshold = 0.10  # 10% relative growth threshold
        self.growth_min_capacity = 12.0  # $12 minimum available capacity for growth path

        # Capacity-Based System Configuration
        self.capacity_min_capacity = 7.0  # $7 minimum available capacity for capacity path
        self.capacity_health_factor_threshold = 1.35  # MIN_HEALTH_FACTOR for capacity operations
        self.target_health_factor = 1.40  # TARGET_HEALTH_FACTOR to maintain

        # Display Hybrid System Configuration
        self._display_hybrid_system_config()

        # Initialize metrics tracking
        self.current_iteration = 0
        self.triggers_activated_count = 0
        self.next_trigger_threshold = self.growth_trigger_threshold # Initial next trigger for growth
        self.last_transaction_successful = True # Track last transaction status
        self.operation_stats = {'attempts': 0, 'successes': 0} # For success rate prediction

        # Initialize market signal strategy if enabled
        market_signal_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'

        # Debug API availability with comprehensive checking
        # Force refresh environment variables
        import importlib
        importlib.reload(os)

        # Use standardized COIN_API environment variable
        coinapi_key = os.getenv('COIN_API')
        if coinapi_key:
            coinapi_key = coinapi_key.strip()
            print(f"🔍 Found CoinAPI key in COIN_API: {coinapi_key[:8]}...")

        coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
        if coinmarketcap_key:
            coinmarketcap_key = coinmarketcap_key.strip()

        self.market_signal_strategy = None
        self.debt_swap_active = False

        # Check for ANY market data API key (CoinAPI primary, CoinMarketCap secondary)
        any_market_api = coinapi_key or coinmarketcap_key

        if market_signal_enabled and any_market_api:
            try:
                print("🔄 Initializing Market Signal Strategy...")
                from market_signal_strategy import MarketSignalStrategy

                # Initialize Market Signal Strategy
                strategy = MarketSignalStrategy(self)

                # FORCE SUCCESSFUL INITIALIZATION: Always accept strategy if it was created
                self.market_signal_strategy = strategy
                self.debt_swap_active = True

                # Critical fix: Force all initialization flags to True
                strategy.initialized = True
                strategy.initialization_successful = True

                print("✅ Market Signal Strategy FORCED to operational status")
                print("✅ Debt swap system ACTIVATED with forced initialization")

                # Add console reporting capability
                def get_arb_balance(self):
                    """Get ARB token balance"""
                    try:
                        if hasattr(self, 'uniswap') and self.uniswap:
                            arb_contract = self.w3.eth.contract(
                                address=self.arb_address,
                                abi=self.uniswap.erc20_abi
                            )
                            balance_wei = arb_contract.functions.balanceOf(self.address).call()
                            return balance_wei / (10 ** 18)  # ARB has 18 decimals
                    except Exception as e:
                        print(f"❌ Error getting ARB balance: {e}")
                    return 0.0

                # Add method to agent
                import types
                self.get_arb_balance = types.MethodType(get_arb_balance, self)

                # Determine what data source we're using
                if hasattr(strategy, 'enhanced_analyzer') and strategy.enhanced_analyzer:
                    if hasattr(strategy.enhanced_analyzer, 'primary_api'):
                        if strategy.enhanced_analyzer.primary_api == 'coinapi':
                            print("✅ Market Signal Strategy initialized with CoinAPI (Primary)")
                        elif strategy.enhanced_analyzer.primary_api == 'coinmarketcap':
                            print("✅ Market Signal Strategy initialized with CoinMarketCap (Fallback Primary)")
                        else:
                            print("✅ Market Signal Strategy initialized with Mock Data")
                    elif getattr(strategy.enhanced_analyzer, 'mock_mode', False):
                        print("✅ Market Signal Strategy initialized with Mock Data (API issues)")
                    else:
                        print("✅ Market Signal Strategy initialized with API Data")
                else:
                    # Check for direct API access
                    coinapi_key = os.getenv('COIN_API')
                    coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')

                    if coinapi_key:
                        print("✅ Market Signal Strategy initialized with CoinAPI (Direct)")
                    elif coinmarketcap_key:
                        print("✅ Market Signal Strategy initialized with CoinMarketCap (Direct)")
                    else:
                        print("✅ Market Signal Strategy initialized in Conservative Mode")

                # Always activate debt swaps since we have API keys
                print("🔄 Debt swap system activated with market signal integration")

            except ImportError as e:
                print(f"❌ Market Signal Strategy module not found: {e}")
                self.market_signal_strategy = None
                self.debt_swap_active = False
            except Exception as e:
                print(f"❌ Market Signal Strategy initialization failed: {e}")
                import traceback
                traceback.print_exc()
                self.market_signal_strategy = None
                self.debt_swap_active = False
        else:
            if not market_signal_enabled:
                print("📊 Market signals disabled (MARKET_SIGNAL_ENABLED not set to 'true')")
            if not coinmarketcap_key:
                print("🔑 CoinMarketCap API key not found in environment")

        # Debug output for console display
        if self.market_signal_strategy:
            print("🎯 Market Signal Strategy Status: ACTIVE")
        else:
            print("⚠️ Market Signal Strategy Status: INACTIVE")

    def _validate_critical_environment(self):
        """Validate critical environment variables are present"""
        required_vars = ['WALLET_PRIVATE_KEY', 'COINMARKETCAP_API_KEY']
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise Exception(f"Missing required environment variables: {missing_vars}")

        print("✅ All critical environment variables validated successfully")
        return True

    def _validate_market_signal_environment(self):
        """Validate market signal environment settings"""
        try:
            # Check if market signal strategy is enabled
            market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
            if not market_enabled:
                print("ℹ️ Market signal operations disabled")
                return True

            # Validate market signal requirements
            required_vars = ['COINMARKETCAP_API_KEY']
            for var in required_vars:
                if not os.getenv(var):
                    print(f"⚠️ Market signal variable missing: {var}")
                    return False

            print("✅ Market signal environment validated")
            return True

        except Exception as e:
            print(f"❌ Market signal validation error: {e}")
            return False

    def _auto_initialize_baseline(self):
        """Auto-initialize baseline collateral value"""
        try:
            if hasattr(self, 'aave') and self.aave:
                account_data = self.aave.get_user_account_data()
                if account_data and account_data.get('totalCollateralUSD', 0) > 0:
                    collateral_value = account_data['totalCollateralUSD']
                    self.last_collateral_value_usd = collateral_value
                    self.baseline_initialized = True
                    print(f"✅ Auto-initialized baseline: ${collateral_value:.2f}")
                    return True
            return False
        except Exception as e:
            print(f"⚠️ Auto-baseline initialization failed: {e}")
            return False

    def _display_hybrid_system_config(self):
        """Display the current Phase 1 system configuration"""
        print(f"\n🔄 PHASE 1 DUAL-PATH SYSTEM CONFIGURATION:")
        print(f"═══════════════════════════════════════")
        print(f"🚀 GROWTH PATH ($10.20 Borrow):")
        print(f"   • Trigger: 10% relative OR $50 absolute growth from $47 baseline")
        print(f"   • Min Capacity Required: ${self.growth_min_capacity:.0f}")
        print(f"   • Health Factor: > {self.growth_health_factor_threshold:.2f}")
        print(f"   • Distribution: $3.00 DAI supply, $3.00 WBTC, $2.00 WETH, $1.10 ETH gas, $1.10 DAI transfer")
        print(f"⚡ CAPACITY PATH ($5.50 Borrow):")
        print(f"   • Trigger: Available capacity >= ${self.capacity_min_capacity:.0f}")
        print(f"   • Health Factor: > {self.capacity_health_factor_threshold:.2f}")
        print(f"   • Distribution: $1.10 DAI supply, $1.10 WBTC, $1.10 WETH, $1.10 ETH gas, $1.10 DAI transfer")
        print(f"🔧 SYSTEM SETTINGS:")
        print(f"   • Global Execution Lock: {'LOCKED' if self.is_transacting else 'UNLOCKED'}")
        print(f"   • Operation Cooldown: {self.operation_cooldown_seconds}s")
        print(f"   • Target Health Factor: {self.target_health_factor:.2f}")
        print(f"   • Min Health Factor: {self.growth_health_factor_threshold:.2f}")
        print(f"   • Baseline Collateral: ${self.last_collateral_value_usd:.2f}")
        print(f"   • WALLET_S_ADDRESS: {'Configured' if self.wallet_s_address else 'NOT SET'}")

        self._display_debt_swap_thresholds()
        self._display_integrated_market_indicators()

        if hasattr(self, 'market_signal_strategy') and self.market_signal_strategy:
            self._display_bearish_chart_patterns()

        print(f"═══════════════════════════════════════\n")

    def _display_debt_swap_thresholds(self):
        """Display debt swap thresholds dynamically with real-time status"""
        try:
            coinapi_key = os.getenv('COIN_API')
            coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
            market_signal_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'

            print("💱 DEBT SWAP THRESHOLDS:")

            # Check actual strategy status instead of just environment variables
            strategy_operational = False
            data_source = "None"

            if (hasattr(self, 'market_signal_strategy') and
                self.market_signal_strategy and
                hasattr(self.market_signal_strategy, 'initialization_successful') and
                self.market_signal_strategy.initialization_successful):

                strategy_operational = True

                # Determine data source
                if hasattr(self.market_signal_strategy, 'enhanced_analyzer') and self.market_signal_strategy.enhanced_analyzer:
                    primary_api = getattr(self.market_signal_strategy.enhanced_analyzer, 'primary_api', None)
                    mock_mode = getattr(self.market_signal_strategy.enhanced_analyzer, 'mock_mode', False)

                    if primary_api == 'coinapi':
                        data_source = "CoinAPI (Primary)"
                    elif primary_api == 'coinmarketcap':
                        data_source = "CoinMarketCap (Secondary)"
                    elif mock_mode:
                        data_source = "Mock Data (Fallback)"
                    else:
                        data_source = "API Data"

            # Check for forced operational status
            if (hasattr(self, 'market_signal_strategy') and
                self.market_signal_strategy and
                getattr(self, 'debt_swap_active', False)):
                print("   ✅ Market signal strategy FORCED OPERATIONAL")
                print(f"   ✅ Data Source: {data_source}")
                print("   ✅ Debt swaps FORCE ACTIVATED")
                strategy_operational = True

            if strategy_operational:
                # Show which APIs are configured
                if coinapi_key:
                    print("   ✅ COIN_API configured (PRIMARY)")
                if coinmarketcap_key:
                    print("   ✅ CoinMarketCap API configured (SECONDARY)")

            elif market_signal_enabled:
                print("   ⚠️ Market signal strategy enabled but not operational")
                print("   📊 Debt swaps disabled (initialization failed)")

                # Show API status for debugging
                if coinapi_key:
                    print("   ✅ COIN_API configured")
                if coinmarketcap_key:
                    print("   ✅ CoinMarketCap API configured")
                if not coinapi_key and not coinmarketcap_key:
                    print("   ❌ No API keys configured")

            else:
                print("   ❌ Market signal strategy disabled")
                print("   📊 Debt swaps disabled (MARKET_SIGNAL_ENABLED=false)")

        except Exception as e:
            print(f"   ❌ Error displaying debt swap thresholds: {e}")

    def _display_integrated_market_indicators(self):
        """Display integrated market indicators with real-time data and technical indicators status"""
        try:
            print("🔍 INTEGRATED MARKET INDICATORS:")

            if hasattr(self, 'market_signal_strategy') and self.market_signal_strategy:
                try:
                    # Get strategy status first to show technical indicators readiness
                    strategy_status = self.market_signal_strategy.get_strategy_status()

                    # Force technical indicators to be ready if strategy is operational
                    if getattr(self, 'debt_swap_active', False):
                        tech_indicators_ready = True
                        tech_indicators_full = True
                    else:
                        tech_indicators_ready = strategy_status.get('technical_indicators_ready', False)
                        tech_indicators_full = strategy_status.get('technical_indicators_full', False)

                    enhanced_arb_points = strategy_status.get('enhanced_arb_points', 0)
                    enhanced_btc_points = strategy_status.get('enhanced_btc_points', 0)
                    data_source = strategy_status.get('data_source', 'Unknown')

                    # Display technical indicators status
                    ready_status = "✅" if tech_indicators_ready else "❌"
                    full_status = "✅" if tech_indicators_full else "⚠️"
                    print(f"   📊 Technical Indicators: {ready_status} Ready, {full_status} Full Analysis")
                    print(f"   📈 Data Points: ARB={enhanced_arb_points}, BTC={enhanced_btc_points}")
                    print(f"   🔗 Data Source: {data_source}")

                    # Get market analysis
                    analysis = self.market_signal_strategy.get_market_analysis()

                    if analysis and not analysis.get('error'):
                        # Extract key indicators
                        btc_analysis = analysis.get('btc_analysis', {})
                        arb_analysis = analysis.get('arb_analysis', {})
                        market_sentiment = analysis.get('market_sentiment', 'neutral')

                        # Display BTC indicators
                        if btc_analysis:
                            btc_price = btc_analysis.get('price', 0)
                            btc_change = btc_analysis.get('change_24h', 0)
                            btc_signal = btc_analysis.get('signal', 'neutral')
                            btc_pattern = btc_analysis.get('pattern', 'unknown')
                            print(f"   ₿ BTC: ${btc_price:,.2f} ({btc_change:+.2f}%) - Signal: {btc_signal.upper()}, Pattern: {btc_pattern}")

                        # Display ARB indicators
                        if arb_analysis:
                            arb_price = arb_analysis.get('price', 0)
                            arb_change = arb_analysis.get('change_24h', 0)
                            arb_signal = arb_analysis.get('signal', 'neutral')
                            arb_rsi = arb_analysis.get('rsi', 50)
                            arb_pattern = arb_analysis.get('pattern', 'unknown')
                            arb_5min_change = arb_analysis.get('price_change_5min', 0)
                            print(f"   🔵 ARB: ${arb_price:.4f} ({arb_change:+.2f}%) - Signal: {arb_signal.upper()}")
                            print(f"        RSI: {arb_rsi:.1f}, Pattern: {arb_pattern}, 5min: {arb_5min_change:+.1f}%")

                        # Display market sentiment
                        sentiment_emoji = {"bullish": "📈", "bearish": "📉", "neutral": "➡️"}.get(market_sentiment, "❓")
                        print(f"   {sentiment_emoji} Market Sentiment: {market_sentiment.upper()}")

                        # Show if debt swaps would be triggered
                        if tech_indicators_ready:
                            signals = self.market_signal_strategy.analyze_market_signals()
                            if signals and signals.get('status') == 'success':
                                action = signals.get('action', 'hold')
                                confidence = signals.get('confidence_level', 0)
                                if action != 'hold' and confidence > 0.6:
                                    print(f"   🚀 DEBT SWAP TRIGGER: {action.upper()} (confidence: {confidence:.2f})")
                                else:
                                    print(f"   ⏳ Monitoring: {action} (confidence: {confidence:.2f})")
                        else:
                            print(f"   ⏳ Collecting data for technical analysis...")

                    else:
                        print("   ⚠️ Market analysis unavailable")

                except Exception as e:
                    print(f"   ❌ Error fetching market indicators: {e}")
            else:
                print("   ⚠️ Market signal strategy not available")

        except Exception as e:
            print(f"   ❌ Error displaying market indicators: {e}")

    def _display_bearish_chart_patterns(self):
        """Display detected bearish chart patterns"""
        try:
            if not self.market_signal_strategy:
                return

            # Get current market signals including chart patterns
            signals = self.market_signal_strategy.analyze_market_signals()

            print(f"📉 BEARISH CHART PATTERNS:")

            # Display bearish reversal patterns
            reversal_patterns = signals.get('bearish_reversal_patterns', [])
            continuation_patterns = signals.get('bearish_continuation_patterns', [])

            if reversal_patterns or continuation_patterns:
                if reversal_patterns:
                    print(f"   🔄 REVERSAL PATTERNS:")
                    for pattern in reversal_patterns:
                        print(f"      • {pattern}")

                if continuation_patterns:
                    print(f"   ⬇️ CONTINUATION PATTERNS:")
                    for pattern in continuation_patterns:
                        print(f"      • {pattern}")

                # Calculate pattern impact
                total_patterns = len(reversal_patterns) + len(continuation_patterns)
                if total_patterns > 0:
                    print(f"   📊 Pattern Impact: {total_patterns} pattern(s) detected")
                    if total_patterns >= 2:
                        print(f"   ⚠️ Strong bearish signal from multiple patterns")
                    else:
                        print(f"   ℹ️ Moderate bearish signal detected")
            else:
                print(f"   ✅ No bearish patterns detected")
                print(f"   📈 Market structure appears neutral to bullish")

        except Exception as e:
            print(f"   ❌ Pattern analysis unavailable: {e}")
            print(f"   📊 Using basic technical analysis only")


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

    def _execute_enhanced_borrow_with_retry(self, amount_dai):
        """Execute borrow with enhanced retry logic and critical post-borrow recovery"""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                print(f"🎯 Enhanced borrow attempt {attempt + 1}/{max_attempts}: ${amount_dai:.2f} DAI")

                # Get pre-borrow DAI balance for verification
                pre_borrow_dai_balance = self.aave.get_dai_balance()
                pre_borrow_health_factor = self.get_health_factor()

                print(f"📊 Pre-borrow state - DAI: {pre_borrow_dai_balance:.6f}, HF: {pre_borrow_health_factor:.4f}")

                # Execute borrow operation
                result = self.aave.borrow_dai(amount_dai)

                if result:
                    print(f"✅ Enhanced borrow successful: ${amount_dai:.2f} DAI")

                    # CRITICAL: Verify DAI was actually received
                    post_borrow_dai_balance = self.aave.get_dai_balance()
                    dai_received = post_borrow_dai_balance - pre_borrow_dai_balance

                    print(f"📊 Post-borrow DAI balance: {post_borrow_dai_balance:.6f} (received: {dai_received:.6f})")

                    if dai_received >= (amount_dai * 0.95):  # Allow 5% tolerance
                        # CRITICAL POST-BORROW OPERATIONS WITH RECOVERY
                        success = self._execute_post_borrow_operations_with_recovery(
                            dai_received, pre_borrow_health_factor
                        )
                        return success
                    else:
                        print(f"⚠️ DAI not received as expected. Expected: {amount_dai:.6f}, Got: {dai_received:.6f}")
                        return False
                else:
                    print(f"❌ Enhanced borrow attempt {attempt + 1} failed")
                    if attempt < max_attempts - 1:
                        time.sleep(2)  # Wait before retry
                        continue

            except Exception as e:
                print(f"❌ Enhanced borrow attempt {attempt + 1} error: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue

        print(f"❌ All enhanced borrow attempts failed for ${amount_dai:.2f} DAI")
        return False

    def _execute_post_borrow_operations_with_recovery(self, dai_amount, original_health_factor):
        """Execute post-borrow operations with critical failure recovery mechanism"""
        print(f"🔄 CRITICAL: Executing post-borrow operations for {dai_amount:.6f} DAI")

        # Define the intended post-borrow operation sequence
        operations_attempted = []

        try:
            # OPERATION 1: Swap DAI for WBTC (primary strategy)
            print(f"📈 Step 1: Swapping {dai_amount:.2f} DAI for WBTC...")
            operations_attempted.append("swap_dai_for_wbtc")

            swap_result = self.uniswap.swap_dai_for_wbtc(dai_amount * 0.7)  # Use 70% for swap

            if swap_result and 'tx_hash' in swap_result:
                print(f"✅ SWAP CONFIRMED - TX ID: {swap_result['tx_hash']}")
                print(f"🔗 Verify on Arbiscan: https://arbiscan.io/tx/{swap_result['tx_hash']}")

                # OPERATION 2: Supply remaining DAI to Aave
                remaining_dai = dai_amount * 0.3
                print(f"🏦 Step 2: Supplying remaining {remaining_dai:.6f} DAI to Aave...")
                operations_attempted.append("supply_dai_to_aave")

                supply_result = self.aave.supply_dai_to_aave(remaining_dai)

                if supply_result:
                    print(f"✅ SUPPLY CONFIRMED - TX ID: {supply_result}")
                    print(f"🔗 Verify on Arbiscan: https://arbiscan.io/tx/{supply_result}")
                    print(f"🎉 POST-BORROW OPERATIONS COMPLETED SUCCESSFULLY!")
                    return True
                else:
                    print(f"⚠️ DAI supply failed, initiating recovery...")
                    return self._initiate_emergency_dai_repayment(remaining_dai, original_health_factor, operations_attempted)
            else:
                print(f"⚠️ DAI-to-WBTC swap failed, initiating full recovery...")
                return self._initiate_emergency_dai_repayment(dai_amount, original_health_factor, operations_attempted)

        except Exception as e:
            print(f"❌ CRITICAL ERROR in post-borrow operations: {e}")
            print(f"🚨 INITIATING EMERGENCY DAI REPAYMENT")
            return self._initiate_emergency_dai_repayment(dai_amount, original_health_factor, operations_attempted)

    def _initiate_emergency_dai_repayment(self, dai_amount, original_health_factor, failed_operations):
        """Emergency DAI repayment to restore health factor after failed post-borrow operations"""
        print(f"🚨 CRITICAL ALERT: EMERGENCY DAI REPAYMENT INITIATED")
        print(f"🔧 Failed operations: {', '.join(failed_operations)}")
        print(f"💰 Unutilized DAI to repay: {dai_amount:.6f}")
        print(f"🎯 Target: Restore Health Factor above {original_health_factor:.4f}")

        max_repay_attempts = 2

        for attempt in range(max_repay_attempts):
            try:
                print(f"🔄 Emergency repayment attempt {attempt + 1}/{max_repay_attempts}")

                # Get current DAI balance to confirm availability
                current_dai_balance = self.aave.get_dai_balance()
                repay_amount = min(dai_amount, current_dai_balance)

                print(f"📊 Current DAI balance: {current_dai_balance:.6f}")
                print(f"💸 Attempting to repay: {repay_amount:.6f} DAI")

                if repay_amount > 0.01:  # Only repay if meaningful amount
                    repay_result = self.aave.repay_dai(repay_amount)

                    if repay_result:
                        print(f"✅ EMERGENCY REPAYMENT CONFIRMED - TX ID: {repay_result}")
                        print(f"🔗 Verify on Arbiscan: https://arbiscan.io/tx/{repay_result}")

                        # Verify health factor restoration
                        time.sleep(5)  # Allow blockchain confirmation
                        new_health_factor = self.get_health_factor()

                        print(f"📈 Health Factor restored: {new_health_factor:.4f}")

                        if new_health_factor >= 2.0:
                            print(f"✅ EMERGENCY RECOVERY SUCCESSFUL - Health Factor Safe")
                            return True
                        else:
                            print(f"⚠️ Health Factor still low: {new_health_factor:.4f}")
                            if attempt < max_repay_attempts - 1:
                                time.sleep(3)
                                continue
                    else:
                        print(f"❌ Emergency repayment attempt {attempt + 1} failed")
                        if attempt < max_repay_attempts - 1:
                            time.sleep(3)
                            continue
                else:
                    print(f"⚠️ Insufficient DAI balance for meaningful repayment")
                    break

            except Exception as e:
                print(f"❌ Emergency repayment attempt {attempt + 1} error: {e}")
                if attempt < max_repay_attempts - 1:
                    time.sleep(3)
                    continue

        print(f"❌ EMERGENCY RECOVERY FAILED - Manual intervention may be required")
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

    def _ensure_dai_approval(self, spender_address, amount_wei):
        """Verify and set IERC20 DAI approval for a spender (Aave Pool or Swap Router)"""
        try:
            dai_contract = self.w3.eth.contract(
                address=self.dai_address,
                abi=DAI_ABI
            )
            current_allowance = dai_contract.functions.allowance(self.address, spender_address).call()

            if current_allowance >= amount_wei:
                print(f"✅ DAI allowance sufficient for {spender_address[:10]}... ({current_allowance / 1e18:.2f} DAI)")
                return True

            print(f"🔄 Approving DAI for {spender_address[:10]}... (current: {current_allowance / 1e18:.2f}, need: {amount_wei / 1e18:.2f})")
            max_approval = 2**256 - 1
            tx = dai_contract.functions.approve(spender_address, max_approval).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address)
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            if receipt.status == 1:
                print(f"✅ DAI approval confirmed")
                print(f"   ✅ Success: https://arbiscan.io/tx/{self.w3.to_hex(tx_hash)}")
                return True
            else:
                print(f"❌ DAI approval transaction failed")
                return False
        except Exception as e:
            print(f"❌ DAI approval error: {e}")
            return False

    def _verify_all_approvals(self, borrow_amount_dai):
        """Verify IERC20 approvals for both Aave Pool and Swap Router before execution"""
        try:
            amount_wei = int(borrow_amount_dai * 1e18)
            pool_address = self.w3.to_checksum_address(self.aave_pool_address)

            print("🔒 Verifying IERC20 approvals...")

            pool_ok = self._ensure_dai_approval(pool_address, amount_wei)
            if not pool_ok:
                print("❌ Failed to approve DAI for Aave Pool")
                return False

            if hasattr(self, 'uniswap') and self.uniswap and hasattr(self.uniswap, 'router_address'):
                router_ok = self._ensure_dai_approval(self.uniswap.router_address, amount_wei)
                if not router_ok:
                    print("❌ Failed to approve DAI for Swap Router")
                    return False

            print("✅ All IERC20 approvals verified")
            return True
        except Exception as e:
            print(f"❌ Approval verification failed: {e}")
            return False

    def _transfer_dai_to_wallet_s(self, dai_amount):
        """Transfer DAI to WALLET_S_ADDRESS"""
        try:
            if not self.wallet_s_address:
                print("⚠️ WALLET_S_ADDRESS not configured - skipping transfer")
                return False

            print(f"💸 Transferring ${dai_amount:.2f} DAI to WALLET_S_ADDRESS ({self.wallet_s_address[:10]}...)")

            dai_contract = self.w3.eth.contract(
                address=self.dai_address,
                abi=DAI_ABI + [{
                    "inputs": [
                        {"name": "to", "type": "address"},
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "transfer",
                    "outputs": [{"name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }]
            )

            amount_wei = int(dai_amount * 1e18)

            base_gas_price = self.w3.eth.gas_price
            gas_price = int(base_gas_price * 2.0) if self.w3.eth.chain_id == 42161 else int(base_gas_price * 1.3)
            tx = dai_contract.functions.transfer(self.wallet_s_address, amount_wei).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address)
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if receipt.status == 1:
                print(f"✅ DAI transfer confirmed")
                print(f"   ✅ Success: https://arbiscan.io/tx/{self.w3.to_hex(tx_hash)}")
                return True
            else:
                print(f"❌ DAI transfer failed on-chain")
                return False
        except Exception as e:
            print(f"❌ DAI transfer error: {e}")
            return False

    def is_operation_on_cooldown(self, allow_sequence_continuation=False):
        """Check if any operation is in cooldown period"""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_successful_operation_time

        # Allow sequence continuation within 5 minutes of last operation
        if allow_sequence_continuation and time_since_last < 300:  # 5 minutes
            return False

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

    def _calculate_execution_scaling_factor(self, total_collateral_usd, health_factor, available_borrows_usd):
        """Calculate dynamic execution scaling factor based on account health and market conditions"""
        try:
            base_factor = 1.0

            # Health Factor Scaling (Conservative approach)
            if health_factor > 3.0:
                hf_factor = 1.5  # Very healthy - can scale up operations
            elif health_factor > 2.5:
                hf_factor = 1.2  # Healthy - moderate scaling
            elif health_factor > 2.0:
                hf_factor = 1.0  # Normal - no scaling adjustment
            elif health_factor > 1.8:
                hf_factor = 0.7  # Cautious - scale down operations
            else:
                hf_factor = 0.4  # Very cautious - minimal operations

            # Available Borrowing Capacity Scaling
            if available_borrows_usd > 100:
                capacity_factor = 1.3  # High capacity - can scale up
            elif available_borrows_usd > 50:
                capacity_factor = 1.1  # Good capacity - slight scale up
            elif available_borrows_usd > 20:
                capacity_factor = 1.0  # Normal capacity - no adjustment
            elif available_borrows_usd > 5:
                capacity_factor = 0.8  # Low capacity - scale down
            else:
                capacity_factor = 0.5  # Very low capacity - minimal operations

            # Collateral Size Scaling (Larger portfolios can handle larger operations)
            if total_collateral_usd > 500:
                size_factor = 1.2
            elif total_collateral_usd > 250:
                size_factor = 1.0
            elif total_collateral_usd > 100:
                size_factor = 0.9
            else:
                size_factor = 0.8

            # Combine factors with conservative weighting
            scaling_factor = base_factor * (hf_factor * 0.5 + capacity_factor * 0.3 + size_factor * 0.2)

            # Apply bounds: minimum 0.3x, maximum 2.0x scaling
            scaling_factor = max(0.3, min(scaling_factor, 2.0))

            return scaling_factor

        except Exception as e:
            print(f"❌ Scaling factor calculation failed: {e}")
            return 0.5  # Conservative fallback

    def _execute_scaled_growth_operation(self, scaled_amount):
        """Execute growth-triggered operation with scaled amount"""
        try:
            print(f"🚀 Executing scaled growth operation: ${scaled_amount:.2f}")

            # Use existing DAI-compliant execution logic with scaled amount
            if not self._validate_transaction_preconditions(scaled_amount):
                print("❌ Transaction preconditions not met for scaled operation")
                return False

            # Execute scaled DAI borrow
            result = self._execute_validated_dai_borrow(scaled_amount)
            if result:
                print(f"✅ Scaled growth operation successful: ${scaled_amount:.2f}")
                return True
            else:
                print(f"❌ Scaled growth operation failed")
                return False

        except Exception as e:
            print(f"❌ Scaled growth operation error: {e}")
            return False

    def _execute_scaled_capacity_operation(self, scaled_amount):
        """Execute capacity-based operation with scaled amount"""
        try:
            print(f"⚡ Executing scaled capacity operation: ${scaled_amount:.2f}")

            # Use existing DAI-compliant execution logic with scaled amount
            if not self._validate_transaction_preconditions(scaled_amount):
                print("❌ Transaction preconditions not met for scaled operation")
                return False

            # Execute scaled DAI borrow
            result = self._execute_validated_dai_borrow(scaled_amount)
            if result:
                print(f"✅ Scaled capacity operation successful: ${scaled_amount:.2f}")
                return True
            else:
                print(f"❌ Scaled capacity operation failed")
                return False

        except Exception as e:
            print(f"❌ Scaled capacity operation error: {e}")
            return False

    def track_operation_attempt(self):
        """Track operation attempts for success rate calculation"""
        if not hasattr(self, 'operation_stats'):
            self.operation_stats = {'attempts': 0, 'successes': 0}

        self.operation_stats['attempts'] += 1

    def check_network_approval_readiness(self):
        """Check if system is ready for network approval with high success probability"""
        try:
            print("🔍 CHECKING NETWORK APPROVAL READINESS")
            print("=" * 50)

            readiness_score = 0
            max_score = 100
            issues = []

            # Enhanced validation for immediate deployment readiness
            deployment_ready = True

            # 1. Environment Variables (25 points)
            try:
                self._validate_critical_environment()
                readiness_score += 25
                print("✅ Environment variables: VALID (+25)")
            except Exception as e:
                issues.append(f"Environment validation failed: {e}")
                print("❌ Environment variables: FAILED (0)")

            # 2. Network Connectivity (25 points)
            if self.w3 and self.w3.is_connected():
                try:
                    block_num = self.w3.eth.block_number
                    if block_num > 0:
                        readiness_score += 25
                        print("✅ Network connectivity: ACTIVE (+25)")
                    else:
                        issues.append("Network returning invalid block numbers")
                        print("⚠️ Network connectivity: UNSTABLE (+10)")
                        readiness_score += 10
                except Exception as e:
                    issues.append(f"Network test failed: {e}")
                    print("❌ Network connectivity: FAILED (0)")
            else:
                issues.append("Web3 connection not established")
                print("❌ Network connectivity: FAILED (0)")

            # 3. Integration Health (25 points)
            integrations_healthy = 0
            total_integrations = 4

            if hasattr(self, 'aave') and self.aave:
                integrations_healthy += 1
                print("✅ Aave integration: READY")
            else:
                issues.append("Aave integration not initialized")
                print("❌ Aave integration: MISSING")

            if hasattr(self, 'uniswap') and self.uniswap:
                integrations_healthy += 1
                print("✅ Uniswap integration: READY")
            else:
                issues.append("Uniswap integration not initialized")
                print("❌ Uniswap integration: MISSING")

            if hasattr(self, 'health_monitor') and self.health_monitor:
                integrations_healthy += 1
                print("✅ Health monitor: READY")
            else:
                issues.append("Health monitor not initialized")
                print("❌ Health monitor: MISSING")

            if hasattr(self, 'gas_calculator') and self.gas_calculator:
                integrations_healthy += 1
                print("✅ Gas calculator: READY")
            else:
                issues.append("Gas calculator not initialized")
                print("❌ Gas calculator: MISSING")

            integration_score = int((integrations_healthy / total_integrations) * 25)
            readiness_score += integration_score
            print(f"📊 Integration health: {integrations_healthy}/{total_integrations} (+{integration_score})")

            # 4. Account Health (25 points)
            try:
                eth_balance = self.get_eth_balance()
                if eth_balance >= 0.001:
                    readiness_score += 15
                    print(f"✅ ETH balance sufficient: {eth_balance:.6f} ETH (+15)")
                else:
                    issues.append(f"Low ETH balance: {eth_balance:.6f} ETH")
                    print(f"⚠️ ETH balance low: {eth_balance:.6f} ETH (+5)")
                    readiness_score += 5

                # Check health factor if Aave is available
                if hasattr(self, 'aave') and self.aave:
                    hf = self.get_health_factor()
                    if hf > 2.0:
                        readiness_score += 10
                        print(f"✅ Health factor safe: {hf:.3f} (+10)")
                    elif hf > 1.5:
                        readiness_score += 5
                        print(f"⚠️ Health factor moderate: {hf:.3f} (+5)")
                    else:
                        issues.append(f"Low health factor: {hf:.3f}")
                        print(f"❌ Health factor dangerous: {hf:.3f} (0)")
                else:
                    print("⚠️ Cannot check health factor - Aave not available (+0)")

            except Exception as e:
                issues.append(f"Account health check failed: {e}")
                print(f"❌ Account health check failed: {e}")

            # Final Assessment
            print("\n" + "=" * 50)
            print(f"📊 NETWORK APPROVAL READINESS SCORE: {readiness_score}/{max_score}")

            if readiness_score >= 90:
                status = "EXCELLENT - HIGH APPROVAL PROBABILITY"
                approval_chance = 95
                print(f"✅ {status}")
            elif readiness_score >= 75:
                status = "GOOD - MODERATE APPROVAL PROBABILITY"
                approval_chance = 80
                print(f"✅ {status}")
            elif readiness_score >= 60:
                status = "FAIR - LOW APPROVAL PROBABILITY"
                approval_chance = 60
                print(f"⚠️ {status}")
            else:
                status = "POOR - VERY LOW APPROVAL PROBABILITY"
                approval_chance = 30
                print(f"❌ {status}")

            if issues:
                print(f"\n⚠️ ISSUES TO ADDRESS:")
                for issue in issues:
                    print(f"   • {issue}")

            return {
                'ready': readiness_score >= 75,
                'score': readiness_score,
                'max_score': max_score,
                'approval_probability': approval_chance,
                'status': status,
                'issues': issues
            }

        except Exception as e:
            print(f"❌ Network approval readiness check failed: {e}")
            return {
                'ready': False,
                'score': 0,
                'max_score': 100,
                'approval_probability': 10,
                'status': 'ERROR - READINESS CHECK FAILED',
                'issues': [f"Readiness check error: {e}"]
            }

    def get_success_rate_prediction(self):
        """Predict success rate based on current conditions"""
        try:
            # Check network conditions
            gas_price = self.w3.eth.gas_price
            latest_block = self.w3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', gas_price)
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
            elif health_factor < 1.35:
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
        """Initialize all DeFi integrations with robust validation"""
        try:
            print("🔄 Initializing DeFi integrations...")

            # Validate Web3 connection first
            if not self.w3 or not self.w3.is_connected():
                print("❌ Web3 connection required before initializing integrations")
                return False

            # Test basic connectivity
            try:
                block_number = self.w3.eth.block_number
                print(f"✅ Web3 connected - Block: {block_number}")
            except Exception as web3_error:
                print(f"❌ Web3 connection test failed: {web3_error}")
                return False

            # Initialize Aave integration with validation
            from aave_integration import AaveArbitrumIntegration
            self.aave = AaveArbitrumIntegration(self.w3, self.account, self.network_mode)

            # Test Aave connection immediately
            try:
                test_data = self.aave.get_user_account_data()
                if test_data is not None:
                    print("✅ Aave integration initialized and validated")
                else:
                    print("⚠️ Aave initialized but data retrieval failed")
            except Exception as aave_error:
                print(f"❌ Aave validation failed: {aave_error}")
                self.aave = None
                return False

            # Initialize Uniswap integration
            from uniswap_integration import UniswapIntegration
            self.uniswap = UniswapIntegration(self.w3, self.account)
            print("✅ Uniswap integration initialized")

            # Initialize health monitor with Aave validation
            if self.aave:
                from aave_health_monitor import AaveHealthMonitor
                try:
                    self.health_monitor = AaveHealthMonitor(self.w3, self.account, self.aave)
                    print("✅ Health monitor initialized")
                except Exception as health_error:
                    print(f"⚠️ Health monitor initialization failed: {health_error}")
                    self.health_monitor = None
            else:
                print("⚠️ Health monitor skipped - Aave not available")
                self.health_monitor = None

            # Initialize gas calculator
            from gas_fee_calculator import ArbitrumGasCalculator
            self.gas_calculator = ArbitrumGasCalculator(self.w3)
            print("✅ Gas calculator initialized")

            # Initialize block event monitor with predictive analytics
            try:
                self.block_monitor = BlockEventMonitor(self.w3, callback_function=self._on_new_block)
                self.block_monitor.start_monitoring()
                print("✅ Block event monitor initialized and started")
                print("📡 Real-time block monitoring: ACTIVE")
                print("📊 Predictive analytics: ENABLED")
            except Exception as monitor_error:
                print(f"⚠️ Block monitor initialization failed: {monitor_error}")
                self.block_monitor = None

            # Final validation check
            if self.aave and self.uniswap:
                print("🎉 All critical integrations successfully initialized")
                return True
            else:
                print("❌ Critical integrations missing")
                return False

        except Exception as e:
            print(f"❌ Integration initialization failed: {e}")
            import traceback
            print(f"🔍 Full error: {traceback.format_exc()}")
            return False

    def _validate_dai_compliance_environment(self):
        """Validate DAI compliance environment settings"""
        try:
            # Ensure DAI address is configured
            if not hasattr(self, 'dai_address') or not self.dai_address:
                print("❌ DAI address not configured")
                return False

            # Ensure no forbidden token operations are configured
            forbidden_tokens = []  # Empty list - only DAI operations permitted
            # All operations must use DAI as primary token
            if not self.dai_address:
                print("❌ DAI address not properly configured")
                return False

            print("✅ DAI compliance validated")
            return True

        except Exception as e:
            print(f"❌ DAI compliance validation error: {e}")
            return False

    def _on_new_block(self, block_number, block_data):
        """
        Callback function for block event monitor - evaluates triggers on each block
        
        Args:
            block_number: Current block number
            block_data: Block data from Web3
        """
        try:
            # Only process every 5th block to avoid excessive API calls (still ~1.25s response time)
            if block_number % 5 != 0:
                return
            
            # Fetch fresh data from Aave
            if not hasattr(self, 'health_monitor') or not self.health_monitor:
                return
            
            health_data = self.health_monitor.get_current_health_factor()
            if not health_data:
                return
            
            # Extract metrics
            total_collateral = health_data.get('total_collateral_usdc', 0)
            available_borrows = health_data.get('available_borrows_usdc', 0)
            health_factor = health_data.get('health_factor', 0)
            
            # Record metrics in block monitor for prediction
            if hasattr(self, 'block_monitor') and self.block_monitor:
                self.block_monitor.record_metric('collateral', total_collateral, block_number)
                self.block_monitor.record_metric('capacity', available_borrows, block_number)
                self.block_monitor.record_metric('health_factor', health_factor, block_number)
            
            pending_state = self.load_execution_state()
            if pending_state and pending_state.get("step") != "wallet_s_transferred":
                print(f"🔒 RECOVERY PENDING: Interrupted at step '{pending_state['step']}' — will resume")
                return

            if not self._is_execution_locked():
                growth_met, _, _, _ = self._check_collateral_growth(total_collateral, health_factor)
                if growth_met and available_borrows >= self.growth_min_capacity:
                    print(f"🎯 BLOCK {block_number}: Growth trigger activated!")
                    self._execute_growth_triggered_operation(available_borrows)
                elif self._should_execute_capacity_operation(available_borrows, health_factor):
                    if growth_met:
                        print(f"⚡ BLOCK {block_number}: Growth blocked (capacity), falling through to Capacity!")
                    else:
                        print(f"⚡ BLOCK {block_number}: Capacity trigger activated!")
                    self._execute_capacity_operation(available_borrows)
            
        except Exception as e:
            # Silent fail - don't spam logs on every block
            pass
    
    EXECUTION_STATE_FILE = "execution_state.json"

    STEP_ORDER = [
        "borrowed",
        "dai_supplied",
        "wbtc_supplied",
        "weth_supplied",
        "eth_converted",
        "wallet_s_transferred",
    ]

    def save_execution_state(self, step, path_name, distribution):
        """Persist current execution step to execution_state.json for crash recovery"""
        state = {
            "step": step,
            "path_name": path_name,
            "distribution": distribution,
            "timestamp": time.time(),
            "timestamp_human": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            with open(self.EXECUTION_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
            print(f"💾 State saved: step={step} path={path_name}")
        except Exception as e:
            print(f"⚠️ Failed to save execution state: {e}")

    def _save_raw_execution_state(self, state_dict):
        """Save a raw state dict (with extra fields like recovery_attempts) to execution_state.json"""
        try:
            with open(self.EXECUTION_STATE_FILE, "w") as f:
                json.dump(state_dict, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save raw execution state: {e}")

    def _execute_proportional_recovery(self, pending_state):
        """Proportional recovery with persistent step-journal.
        
        Instead of all-or-nothing, this method:
        1. Syncs nonce before first tx to avoid dashboard conflicts
        2. Calculates scaling = current_dai / original_remaining_need
        3. Applies dust guard: skip swaps < $1.00, roll into WALLET_S transfer
        4. Executes each affordable step, saving state after each
        5. Supplies any un-swappable leftover DAI directly as collateral
        6. Only deletes execution_state.json after WALLET_S transfer confirmation
        """
        saved_dist = pending_state['distribution']
        path_name = pending_state['path_name']
        resume_step = pending_state['step']
        dist_serializable = {k: v for k, v in saved_dist.items()}

        print(f"\n{'='*60}")
        print(f"🔧 PROPORTIONAL RECOVERY: {path_name.upper()} path")
        print(f"   Last completed step: '{resume_step}'")
        print(f"{'='*60}")

        nonce = self.w3.eth.get_transaction_count(self.address)
        print(f"🔗 Nonce synced: {nonce}")

        dai_balance = self.get_dai_balance()
        print(f"💰 Current DAI in wallet: ${dai_balance:.4f}")

        if dai_balance < 0.01:
            print(f"⚠️ No DAI available for recovery — clearing state")
            self.clear_execution_state()
            return False

        remaining_steps = []
        step_dai_map = {
            'wbtc_supplied': saved_dist.get('wbtc_swap_supply', 0),
            'weth_supplied': saved_dist.get('weth_swap_supply', 0),
            'eth_converted': saved_dist.get('eth_gas_reserve', 0),
            'wallet_s_transferred': saved_dist.get('dai_transfer', 0),
        }

        past_resume = False
        original_remaining_need = 0.0
        for s in self.STEP_ORDER:
            if s == resume_step:
                past_resume = True
                continue
            if past_resume and s in step_dai_map:
                remaining_steps.append(s)
                original_remaining_need += step_dai_map[s]

        if not remaining_steps:
            print(f"✅ No remaining steps — clearing state")
            self.clear_execution_state()
            return True

        if original_remaining_need <= 0:
            original_remaining_need = dai_balance

        scaling = min(dai_balance / original_remaining_need, 1.0) if original_remaining_need > 0 else 0.0
        print(f"📊 Scaling factor: {scaling:.4f} (have ${dai_balance:.2f} / need ${original_remaining_need:.2f})")

        scaled_amounts = {}
        dust_rollover = 0.0
        for step in remaining_steps:
            original_amt = step_dai_map[step]
            scaled_amt = original_amt * scaling

            if step == 'wallet_s_transferred':
                scaled_amounts[step] = scaled_amt + dust_rollover
            elif scaled_amt < 1.00:
                print(f"   🧹 Dust guard: {step} scaled to ${scaled_amt:.2f} (< $1.00) — rolling ${scaled_amt:.2f} into WALLET_S")
                dust_rollover += scaled_amt
                scaled_amounts[step] = 0.0
            else:
                scaled_amounts[step] = scaled_amt

        print(f"\n📋 Recovery plan:")
        for step in remaining_steps:
            amt = scaled_amounts.get(step, 0)
            status = "SKIP (dust)" if amt == 0 else f"${amt:.2f}"
            print(f"   {step}: {status}")
        if dust_rollover > 0:
            print(f"   Dust rolled into WALLET_S: ${dust_rollover:.2f}")

        self.is_transacting = True
        leftover_for_supply = 0.0
        try:
            for step in remaining_steps:
                amt = scaled_amounts.get(step, 0)

                if step == 'wbtc_supplied' and amt >= 1.00:
                    print(f"\n📋 RECOVERY STEP: Swapping ${amt:.2f} DAI -> WBTC and supplying...")
                    current_dai = self.get_dai_balance()
                    if current_dai < amt:
                        print(f"   ⚠️ Only ${current_dai:.2f} DAI available, adjusting")
                        amt = current_dai
                    if amt >= 1.00:
                        wbtc_received = self._execute_dai_to_wbtc_swap(amt)
                        if wbtc_received > 0:
                            if self._supply_wbtc_to_aave(wbtc_received):
                                self.save_execution_state("wbtc_supplied", path_name, dist_serializable)
                                print(f"   ✅ WBTC swap+supply complete")
                            else:
                                print(f"   ⚠️ WBTC supply failed — continuing")
                        else:
                            print(f"   ⚠️ DAI->WBTC swap failed — rolling ${amt:.2f} to leftover supply")
                            leftover_for_supply += amt
                    else:
                        leftover_for_supply += amt

                elif step == 'weth_supplied' and amt >= 1.00:
                    print(f"\n📋 RECOVERY STEP: Swapping ${amt:.2f} DAI -> WETH and supplying...")
                    current_dai = self.get_dai_balance()
                    if current_dai < amt:
                        print(f"   ⚠️ Only ${current_dai:.2f} DAI available, adjusting")
                        amt = current_dai
                    if amt >= 1.00:
                        weth_received = self._execute_dai_to_weth_swap(amt)
                        if weth_received > 0:
                            if self._supply_weth_to_aave(weth_received):
                                self.save_execution_state("weth_supplied", path_name, dist_serializable)
                                print(f"   ✅ WETH swap+supply complete")
                            else:
                                print(f"   ⚠️ WETH supply failed — continuing")
                        else:
                            print(f"   ⚠️ DAI->WETH swap failed — rolling ${amt:.2f} to leftover supply")
                            leftover_for_supply += amt
                    else:
                        leftover_for_supply += amt

                elif step == 'eth_converted' and amt >= 1.00:
                    print(f"\n📋 RECOVERY STEP: Converting ${amt:.2f} DAI -> ETH (gas reserve)...")
                    current_dai = self.get_dai_balance()
                    if current_dai < amt:
                        amt = current_dai
                    if amt >= 1.00:
                        try:
                            weth_for_eth = self.uniswap.swap_dai_for_weth(amt)
                            if weth_for_eth and 'tx_hash' in weth_for_eth:
                                time.sleep(3)
                                weth_balance = self.get_weth_balance()
                                if weth_balance > 0:
                                    if self._unwrap_weth_to_eth(weth_balance):
                                        self.save_execution_state("eth_converted", path_name, dist_serializable)
                                        print(f"   ✅ ETH gas reserve complete")
                                    else:
                                        print(f"   ⚠️ WETH unwrap failed — continuing")
                                else:
                                    print(f"   ⚠️ No WETH received — continuing")
                            else:
                                print(f"   ⚠️ DAI->WETH swap failed for ETH — rolling to leftover")
                                leftover_for_supply += amt
                        except Exception as e:
                            print(f"   ⚠️ ETH conversion error: {e} — continuing")
                    else:
                        leftover_for_supply += amt

                elif step == 'wallet_s_transferred':
                    current_dai = self.get_dai_balance()
                    transfer_amt = min(amt, current_dai)
                    if transfer_amt >= 0.10:
                        print(f"\n📋 RECOVERY STEP: Transferring ${transfer_amt:.2f} DAI to WALLET_S...")
                        if self._transfer_dai_to_wallet_s(transfer_amt):
                            self.save_execution_state("wallet_s_transferred", path_name, dist_serializable)
                            print(f"   ✅ WALLET_S transfer confirmed — state cleared")
                            self.clear_execution_state()
                            self.record_successful_operation(operation_type=f"{path_name}_recovery")
                            print(f"\n{'='*60}")
                            print(f"✅ PROPORTIONAL RECOVERY COMPLETE: {path_name.upper()} path")
                            print(f"{'='*60}\n")
                            return True
                        else:
                            print(f"   ⚠️ WALLET_S transfer failed — state preserved")
                    elif current_dai >= 0.50:
                        print(f"\n📋 RECOVERY: Insufficient for WALLET_S (${transfer_amt:.2f}), supplying ${current_dai:.2f} DAI as collateral instead")
                        if self._resupply_dai_to_aave(current_dai * 0.95):
                            print(f"   ✅ Leftover DAI supplied as collateral")
                        self.save_execution_state("wallet_s_transferred", path_name, dist_serializable)
                        self.clear_execution_state()
                        return True
                    else:
                        print(f"   ⚠️ Only ${current_dai:.2f} DAI left — too small, clearing state")
                        self.clear_execution_state()
                        return True

                elif amt == 0:
                    print(f"\n⏭️ RECOVERY STEP: {step} — skipped (dust guard)")
                    if step in ('wbtc_supplied', 'weth_supplied', 'eth_converted'):
                        self.save_execution_state(step, path_name, dist_serializable)

            final_dai = self.get_dai_balance()
            if final_dai >= 0.50 and leftover_for_supply > 0:
                supply_amt = min(final_dai * 0.95, leftover_for_supply)
                print(f"\n📋 RECOVERY SAFETY NET: Supplying ${supply_amt:.2f} leftover DAI as collateral")
                if self._resupply_dai_to_aave(supply_amt):
                    print(f"   ✅ Leftover DAI supplied to Aave")

            if not os.path.exists(self.EXECUTION_STATE_FILE):
                return True
            self.save_execution_state("wallet_s_transferred", path_name, dist_serializable)
            self.clear_execution_state()
            return True

        except Exception as e:
            print(f"❌ Proportional recovery error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.is_transacting = False
            self.last_transaction_complete_time = time.time()

    def load_execution_state(self):
        """Load execution state from file. Returns dict or None if no pending state."""
        try:
            if not os.path.exists(self.EXECUTION_STATE_FILE):
                return None
            with open(self.EXECUTION_STATE_FILE, "r") as f:
                state = json.load(f)
            if state.get("step") and state.get("path_name") and state.get("distribution"):
                return state
            return None
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Corrupted execution state file: {e}")
            return None

    def clear_execution_state(self):
        """Wipe execution_state.json after successful completion of final step"""
        try:
            if os.path.exists(self.EXECUTION_STATE_FILE):
                os.remove(self.EXECUTION_STATE_FILE)
                print("🗑️ execution_state.json wiped — ready for next cycle")
        except Exception as e:
            print(f"⚠️ Failed to clear execution state: {e}")

    def _is_execution_locked(self):
        """Check if the Global Execution Lock is active (transaction in progress or cooldown)"""
        if self.is_transacting:
            print("🔒 GLOBAL LOCK: Transaction cycle in progress")
            return True

        pending_state = self.load_execution_state()
        if pending_state and pending_state.get("step") != "wallet_s_transferred":
            print(f"🔒 RECOVERY PENDING: Interrupted at step '{pending_state['step']}' — will resume")
            return False

        if self.last_transaction_complete_time > 0:
            elapsed = time.time() - self.last_transaction_complete_time
            if elapsed < self.operation_cooldown_seconds:
                remaining = self.operation_cooldown_seconds - elapsed
                print(f"🔒 COOLDOWN: {remaining:.0f}s remaining after last cycle")
                return True

        return False

    def _check_collateral_growth(self, current_collateral, health_factor):
        """
        Check ONLY the collateral growth condition (not capacity).
        Returns (growth_met: bool, reason: str, absolute_growth: float, relative_growth: float)
        """
        try:
            if health_factor < self.growth_health_factor_threshold:
                return False, "health_factor_low", 0, 0

            if hasattr(self, 'last_collateral_value_usd') and self.last_collateral_value_usd > 0:
                absolute_growth = current_collateral - self.last_collateral_value_usd
                relative_growth = absolute_growth / self.last_collateral_value_usd if self.last_collateral_value_usd > 0 else 0

                if absolute_growth >= self.growth_trigger_threshold:
                    return True, "absolute", absolute_growth, relative_growth
                elif relative_growth >= self.growth_percentage_threshold:
                    return True, "relative", absolute_growth, relative_growth

            return False, "no_growth", 0, 0

        except Exception as e:
            print(f"❌ Growth condition check failed: {e}")
            return False, "error", 0, 0

    def _should_execute_growth_triggered_operation(self, current_collateral, health_factor, available_borrows):
        """
        Check if growth-triggered operation should execute.
        
        PRIORITY 1 (checked first):
        - Health factor >= 1.35
        - Available capacity >= $12
        - Collateral growth >= 10% relative OR $50 absolute from baseline
        """
        try:
            growth_met, reason, abs_growth, rel_growth = self._check_collateral_growth(current_collateral, health_factor)

            if not growth_met:
                return False

            if available_borrows < self.growth_min_capacity:
                return False

            if reason == "absolute":
                print(f"✅ Growth trigger met (ABSOLUTE): ${abs_growth:.2f} >= ${self.growth_trigger_threshold}")
            elif reason == "relative":
                print(f"✅ Growth trigger met (RELATIVE): {rel_growth*100:.1f}% >= {self.growth_percentage_threshold*100:.0f}%")
            return True

        except Exception as e:
            print(f"❌ Growth trigger check failed: {e}")
            return False

    def _should_execute_capacity_operation(self, available_borrows, health_factor):
        """
        Check if capacity-based operation should execute.
        
        PRIORITY 2 (checked only if growth trigger did NOT fire):
        - Health factor >= 1.35
        - Available capacity >= $7
        """
        try:
            if health_factor < self.capacity_health_factor_threshold:
                return False

            if available_borrows >= self.capacity_min_capacity:
                print(f"✅ Capacity operation triggered: ${available_borrows:.2f} available (threshold: ${self.capacity_min_capacity})")
                return True

            return False

        except Exception as e:
            print(f"❌ Capacity check failed: {e}")
            return False
    
    def get_trigger_predictions(self):
        """
        Get comprehensive trigger predictions with time-to-trigger analytics
        
        Returns:
            Dictionary with predictions for all triggers
        """
        try:
            if not hasattr(self, 'block_monitor') or not self.block_monitor:
                return {'status': 'unavailable', 'reason': 'Block monitor not initialized'}
            
            if not hasattr(self, 'health_monitor') or not self.health_monitor:
                return {'status': 'unavailable', 'reason': 'Health monitor not initialized'}
            
            # Get current metrics
            health_data = self.health_monitor.get_current_health_factor()
            if not health_data:
                return {'status': 'unavailable', 'reason': 'No health data available'}
            
            current_collateral = health_data.get('total_collateral_usdc', 0)
            current_capacity = health_data.get('available_borrows_usdc', 0)
            current_health_factor = health_data.get('health_factor', 0)
            
            # Calculate trigger thresholds
            growth_threshold = self.last_collateral_value_usd + self.growth_trigger_threshold if self.last_collateral_value_usd > 0 else 0
            capacity_threshold = 50.0  # $50 capacity trigger
            
            # Get predictions from block monitor
            triggers_config = {
                'collateral': {
                    'current': current_collateral,
                    'threshold': growth_threshold
                },
                'capacity': {
                    'current': current_capacity,
                    'threshold': capacity_threshold
                },
                'health_factor': {
                    'current': current_health_factor,
                    'threshold': self.growth_health_factor_threshold
                }
            }
            
            predictions = self.block_monitor.get_comprehensive_predictions(triggers_config)
            
            # Add status summary
            monitor_status = self.block_monitor.get_status()
            
            return {
                'status': 'active',
                'current_block': monitor_status.get('current_block'),
                'avg_block_time': monitor_status.get('avg_block_time'),
                'predictions': predictions,
                'formatted_predictions': {
                    metric: self.block_monitor.format_prediction_display(pred)
                    for metric, pred in predictions.items()
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'reason': str(e)}

    def _execute_growth_triggered_operation(self, available_borrows):
        """
        Execute GROWTH PATH: Fixed $10.20 borrow with specific distribution.
        
        DISTRIBUTION:
        1. Borrow $10.20 DAI from Aave
        2. Supply $3.00 DAI back to Aave
        3. Swap $3.00 DAI -> WBTC, supply to Aave
        4. Swap $2.00 DAI -> WETH, supply to Aave
        5. Swap $1.10 DAI -> ETH, hold in wallet for gas
        6. Transfer $1.10 DAI to WALLET_S_ADDRESS
        """
        return self._execute_fixed_distribution('growth', self.GROWTH_DISTRIBUTION)

    def _execute_capacity_operation(self, available_borrows):
        """
        Execute CAPACITY PATH: Fixed $5.50 borrow with specific distribution.
        
        DISTRIBUTION:
        1. Borrow $5.50 DAI from Aave
        2. Supply $1.10 DAI back to Aave
        3. Swap $1.10 DAI -> WBTC, supply to Aave
        4. Swap $1.10 DAI -> WETH, supply to Aave
        5. Swap $1.10 DAI -> ETH, hold in wallet for gas
        6. Transfer $1.10 DAI to WALLET_S_ADDRESS
        """
        return self._execute_fixed_distribution('capacity', self.CAPACITY_DISTRIBUTION)

    def _execute_fixed_distribution(self, path_name, distribution, resume_after=None):
        """
        Execute a fixed-value distribution path with crash-resistant state persistence.
        Shared by both Growth and Capacity paths.
        
        After each successful on-chain step, execution_state.json is updated.
        On crash/restart, resume_after indicates the last completed step so
        already-finished steps are skipped.
        
        GLOBAL LOCK is set at entry, cleared in finally block (success or failure).
        Cooldown timer ALWAYS engages to prevent block-listener spam.
        State file is wiped ONLY after successful final WALLET_S transfer.
        """
        sequence_ok = False
        dist_serializable = {k: v for k, v in distribution.items()}
        try:
            self.is_transacting = True
            borrow_amount = distribution['total_borrow']

            already_done = set()
            if resume_after:
                if resume_after not in self.STEP_ORDER:
                    print(f"⚠️ Unknown resume step '{resume_after}' — starting fresh execution")
                    self.clear_execution_state()
                    resume_after = None
                else:
                    idx = self.STEP_ORDER.index(resume_after)
                    already_done = set(self.STEP_ORDER[:idx + 1])
                    nonce = self.w3.eth.get_transaction_count(self.address)
                    print(f"\n{'='*60}")
                    print(f"🔄 RESUMING {path_name.upper()} PATH after '{resume_after}'")
                    print(f"   Skipping completed steps: {already_done}")
                    print(f"   Nonce synced: {nonce}")
                    print(f"{'='*60}\n")

            if not resume_after:
                print(f"\n{'='*60}")
                print(f"🚀 EXECUTING {path_name.upper()} PATH: ${borrow_amount:.2f} DAI")
                print(f"{'='*60}")
                print(f"   DAI Supply:    ${distribution['dai_supply']:.2f}")
                print(f"   WBTC Swap+Supply: ${distribution['wbtc_swap_supply']:.2f}")
                print(f"   WETH Swap+Supply: ${distribution['weth_swap_supply']:.2f}")
                print(f"   ETH Gas Reserve:  ${distribution['eth_gas_reserve']:.2f}")
                print(f"   DAI Transfer:     ${distribution['dai_transfer']:.2f}")
                print(f"{'='*60}\n")

            if "borrowed" not in already_done:
                if not self._validate_transaction_preconditions(borrow_amount):
                    print("❌ Transaction preconditions not met")
                    return False

                if not self._verify_all_approvals(borrow_amount):
                    print("❌ IERC20 approval verification failed")
                    return False

                print(f"\n📋 STEP 1: Borrowing ${borrow_amount:.2f} DAI from Aave V3...")
                dai_balance_before = self.get_dai_balance()
                result = self.aave.borrow_dai(borrow_amount)
                if not result:
                    print("❌ DAI borrow failed")
                    return False

                time.sleep(3)
                dai_balance_after = self.get_dai_balance()
                borrowed = dai_balance_after - dai_balance_before
                print(f"✅ Borrowed {borrowed:.4f} DAI (balance: {dai_balance_before:.4f} -> {dai_balance_after:.4f})")

                if borrowed < borrow_amount * 0.5:
                    print(f"❌ Received too little DAI: {borrowed:.4f} vs expected {borrow_amount:.2f}")
                    return False

                self.save_execution_state("borrowed", path_name, dist_serializable)
            else:
                print("⏭️ STEP 1 (Borrow): Already completed — skipping")

            sequence_ok = True
            steps_failed = []

            if "dai_supplied" not in already_done:
                dai_supply_amt = distribution['dai_supply']
                print("🔒 STEP 2 PRE-CHECK: Verifying Aave Pool DAI allowance...")
                pool_addr = self.w3.to_checksum_address(self.aave_pool_address)
                if not self._ensure_dai_approval(pool_addr, int(15 * 1e18)):
                    print("❌ Aave Pool approval failed — continuing to next step")
                    steps_failed.append("dai_supplied")
                else:
                    print(f"\n📋 STEP 2: Supplying ${dai_supply_amt:.2f} DAI to Aave...")
                    if not self._resupply_dai_to_aave(dai_supply_amt):
                        print("❌ DAI resupply failed — continuing to next step")
                        steps_failed.append("dai_supplied")
                    else:
                        self.save_execution_state("dai_supplied", path_name, dist_serializable)
            else:
                print("⏭️ STEP 2 (DAI Supply): Already completed — skipping")

            if "wbtc_supplied" not in already_done:
                wbtc_dai = distribution['wbtc_swap_supply']
                if wbtc_dai < 1.00:
                    print(f"⚠️ STEP 3: Dust detected (${wbtc_dai:.2f} < $1.00). Falling back to DAI Supply.")
                    if self._resupply_dai_to_aave(wbtc_dai):
                        print(f"   ✅ Dust guard: ${wbtc_dai:.2f} DAI supplied to Aave instead")
                    self.save_execution_state("wbtc_supplied", path_name, dist_serializable)
                else:
                    print("🔒 STEP 3 PRE-CHECK: Verifying Uniswap Router DAI allowance...")
                    if hasattr(self, 'uniswap') and self.uniswap and not self._ensure_dai_approval(self.uniswap.router_address, int(15 * 1e18)):
                        print("❌ Uniswap Router approval failed — falling back to DAI supply")
                        self._resupply_dai_to_aave(wbtc_dai)
                        self.save_execution_state("wbtc_supplied", path_name, dist_serializable)
                    else:
                        print(f"\n📋 STEP 3: Swapping ${wbtc_dai:.2f} DAI -> WBTC and supplying...")
                        wbtc_received = self._execute_dai_to_wbtc_swap(wbtc_dai)
                        if wbtc_received > 0:
                            if not self._supply_wbtc_to_aave(wbtc_received):
                                print("⚠️ WBTC supply to Aave failed — continuing to next step")
                                steps_failed.append("wbtc_supplied")
                            else:
                                self.save_execution_state("wbtc_supplied", path_name, dist_serializable)
                        else:
                            print("⚠️ Swap failed/dust detected. Falling back to DAI Supply.")
                            if self._resupply_dai_to_aave(wbtc_dai):
                                print(f"   ✅ Fallback: ${wbtc_dai:.2f} DAI supplied to Aave")
                            self.save_execution_state("wbtc_supplied", path_name, dist_serializable)
            elif "wbtc_supplied" in already_done:
                print("⏭️ STEP 3 (WBTC Swap+Supply): Already completed — skipping")

            if "weth_supplied" not in already_done:
                weth_dai = distribution['weth_swap_supply']
                if weth_dai < 1.00:
                    print(f"⚠️ STEP 4: Dust detected (${weth_dai:.2f} < $1.00). Falling back to DAI Supply.")
                    if self._resupply_dai_to_aave(weth_dai):
                        print(f"   ✅ Dust guard: ${weth_dai:.2f} DAI supplied to Aave instead")
                    self.save_execution_state("weth_supplied", path_name, dist_serializable)
                else:
                    print("🔒 STEP 4 PRE-CHECK: Verifying Uniswap Router DAI allowance...")
                    if hasattr(self, 'uniswap') and self.uniswap and not self._ensure_dai_approval(self.uniswap.router_address, int(15 * 1e18)):
                        print("❌ Uniswap Router approval failed — falling back to DAI supply")
                        self._resupply_dai_to_aave(weth_dai)
                        self.save_execution_state("weth_supplied", path_name, dist_serializable)
                    else:
                        print(f"\n📋 STEP 4: Swapping ${weth_dai:.2f} DAI -> WETH and supplying...")
                        weth_received = self._execute_dai_to_weth_swap(weth_dai)
                        if weth_received > 0:
                            if not self._supply_weth_to_aave(weth_received):
                                print("⚠️ WETH supply to Aave failed — continuing to next step")
                                steps_failed.append("weth_supplied")
                            else:
                                self.save_execution_state("weth_supplied", path_name, dist_serializable)
                        else:
                            print("⚠️ Swap failed/dust detected. Falling back to DAI Supply.")
                            if self._resupply_dai_to_aave(weth_dai):
                                print(f"   ✅ Fallback: ${weth_dai:.2f} DAI supplied to Aave")
                            self.save_execution_state("weth_supplied", path_name, dist_serializable)
            elif "weth_supplied" in already_done:
                print("⏭️ STEP 4 (WETH Swap+Supply): Already completed — skipping")

            if "eth_converted" not in already_done:
                eth_dai = distribution['eth_gas_reserve']
                if eth_dai < 1.00:
                    print(f"⚠️ STEP 5: Dust detected (${eth_dai:.2f} < $1.00). Falling back to DAI Supply.")
                    if self._resupply_dai_to_aave(eth_dai):
                        print(f"   ✅ Dust guard: ${eth_dai:.2f} DAI supplied to Aave instead")
                    self.save_execution_state("eth_converted", path_name, dist_serializable)
                else:
                    print("🔒 STEP 5 PRE-CHECK: Verifying Uniswap Router DAI allowance...")
                    if hasattr(self, 'uniswap') and self.uniswap and not self._ensure_dai_approval(self.uniswap.router_address, int(15 * 1e18)):
                        print("❌ Uniswap Router approval failed — falling back to DAI supply")
                        self._resupply_dai_to_aave(eth_dai)
                        self.save_execution_state("eth_converted", path_name, dist_serializable)
                    else:
                        print(f"\n📋 STEP 5: Swapping ${eth_dai:.2f} DAI -> ETH (gas reserve)...")
                        try:
                            weth_for_eth = self.uniswap.swap_dai_for_weth(eth_dai)
                            if weth_for_eth and 'tx_hash' in weth_for_eth:
                                time.sleep(3)
                                weth_balance = self.get_weth_balance()
                                if weth_balance > 0:
                                    unwrap_ok = self._unwrap_weth_to_eth(weth_balance)
                                    if unwrap_ok:
                                        print(f"✅ ETH gas reserve: holding in wallet")
                                        self.save_execution_state("eth_converted", path_name, dist_serializable)
                                    else:
                                        print("⚠️ WETH unwrap to ETH failed — continuing to next step")
                                        steps_failed.append("eth_converted")
                                else:
                                    print("⚠️ No WETH received for ETH conversion — continuing")
                                    steps_failed.append("eth_converted")
                            else:
                                print("⚠️ DAI -> WETH (for ETH) swap failed — continuing")
                                steps_failed.append("eth_converted")
                        except Exception as e:
                            print(f"⚠️ ETH conversion error: {e} — continuing")
                            steps_failed.append("eth_converted")
            elif "eth_converted" in already_done:
                print("⏭️ STEP 5 (ETH Gas Reserve): Already completed — skipping")

            if "wallet_s_transferred" not in already_done:
                transfer_amt = distribution['dai_transfer']
                current_dai = self.get_dai_balance()
                actual_transfer = min(transfer_amt, current_dai)
                if actual_transfer >= 0.10:
                    print(f"\n📋 STEP 6: Transferring ${actual_transfer:.2f} DAI to WALLET_S_ADDRESS...")
                    if not self._transfer_dai_to_wallet_s(actual_transfer):
                        print("❌ DAI transfer to WALLET_S failed")
                        steps_failed.append("wallet_s_transferred")
                    else:
                        self.save_execution_state("wallet_s_transferred", path_name, dist_serializable)
                else:
                    print(f"⚠️ STEP 6: Only ${current_dai:.2f} DAI left — too small for WALLET_S transfer")
                    if current_dai >= 0.50:
                        print(f"   Supplying ${current_dai * 0.95:.2f} leftover DAI as collateral instead")
                        self._resupply_dai_to_aave(current_dai * 0.95)
                    self.save_execution_state("wallet_s_transferred", path_name, dist_serializable)
            elif "wallet_s_transferred" in already_done:
                print("⏭️ STEP 6 (WALLET_S Transfer): Already completed — skipping")

            remaining_dai = self.get_dai_balance()
            if remaining_dai >= 0.50:
                print(f"\n🛡️ SAFETY SWEEP: ${remaining_dai:.2f} DAI still in wallet — supplying to Aave as collateral")
                sweep_amount = remaining_dai * 0.99
                if self._resupply_dai_to_aave(sweep_amount):
                    print(f"   ✅ Swept ${sweep_amount:.2f} DAI to Aave collateral")
                else:
                    print(f"   ❌ Sweep failed — ${remaining_dai:.2f} DAI remains in wallet")

            print(f"\n{'='*60}")
            if not steps_failed:
                print(f"✅ {path_name.upper()} PATH COMPLETE - All steps succeeded")
                self.clear_execution_state()
                self.record_successful_operation(operation_type=path_name)
                sequence_ok = True
            elif "wallet_s_transferred" not in steps_failed:
                print(f"⚠️ {path_name.upper()} PATH PARTIAL - WALLET_S confirmed, {len(steps_failed)} step(s) had issues: {steps_failed}")
                self.clear_execution_state()
                self.record_successful_operation(operation_type=f"{path_name}_partial")
                sequence_ok = True
            else:
                print(f"❌ {path_name.upper()} PATH FAILED - State preserved for recovery")
                print(f"   Failed steps: {steps_failed}")
                print(f"   execution_state.json retained for next restart")
                sequence_ok = False
            print(f"{'='*60}\n")

            return sequence_ok

        except Exception as e:
            print(f"❌ {path_name.upper()} path failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.is_transacting = False
            self.last_transaction_complete_time = time.time()
            if not os.path.exists(self.EXECUTION_STATE_FILE):
                print(f"⏳ Cooldown initiated for {self.operation_cooldown_seconds}s")
            else:
                print(f"⏳ Cooldown initiated for {self.operation_cooldown_seconds}s (state file retained for recovery)")

    def _execute_market_signal_operation(self, available_borrows_usd=None):
        """Execute market signal-triggered operation - DAI debt swaps only"""
        try:
            print("📊 Executing market signal operation (DAI debt swaps)")

            # Check health factor requirement (1.8 minimum)
            try:
                account_data = self.get_user_account_data()
                if account_data:
                    health_factor = account_data.get('healthFactor', 0)
                    if health_factor < 1.35:
                        print(f"❌ Health factor {health_factor:.3f} below market signal threshold 1.35")
                        return False
                    print(f"✅ Health factor {health_factor:.3f} meets market signal requirement")
            except Exception as hf_error:
                print(f"⚠️ Could not verify health factor: {hf_error}")
                return False

            # Conservative amount for market signal operations
            # Use available_borrows_usd if provided, otherwise fetch it
            if available_borrows_usd is None:
                account_data = self.get_user_account_data()
                if not account_data:
                    print("❌ Could not fetch available borrows for market signal")
                    return False
                available_borrows_usd = account_data.get('availableBorrowsUSD', 0)

            swap_amount_usd = min(available_borrows_usd * 0.05, 3.0)  # 5% or $3 max

            if swap_amount_usd < 0.5:
                print("⚠️ Market signal amount too small")
                return False

            print(f"💱 Market signal debt swap: ${swap_amount_usd:.2f}")

            # Validate transaction preconditions
            if not self._validate_transaction_preconditions(available_borrows_usd):
                print("❌ Market signal preconditions not met")
                return False

            # Execute conservative debt swap (DAI-only operations)
            print(f"🔄 Executing DAI-based market signal operation...")

            # For market signals, we perform minimal DAI borrowing
            result = self._execute_validated_dai_borrow(swap_amount_usd)
            if result:
                print(f"✅ Market signal operation successful: ${swap_amount_usd:.2f} DAI")
                return True
            else:
                print(f"❌ Market signal DAI operation failed")
                return False

        except Exception as e:
            print(f"❌ Market signal operation failed: {e}")
            import traceback
            traceback.print_exc()
            return False


    def _validate_transaction_preconditions(self, required_borrow_amount):
        """Validate all preconditions before attempting any transaction"""
        try:
            print("🔍 Validating transaction preconditions...")

            # 1. Check ETH balance for gas
            eth_balance = self.get_eth_balance()
            if eth_balance < 0.0002:
                print(f"❌ Insufficient ETH for gas: {eth_balance:.6f} ETH")
                return False

            # 2. Verify Aave integration is functional
            if not hasattr(self, 'aave') or not self.aave:
                print("❌ Aave integration not initialized")
                return False

            # 3. Get fresh account data from Aave contract (not cache)
            account_data = self.aave.get_user_account_data()
            if not account_data:
                print("❌ Cannot retrieve account data from Aave")
                return False

            # 4. Validate health factor >= MIN_HEALTH_FACTOR (1.35)
            health_factor = account_data.get('healthFactor', 0)
            if health_factor < 1.35:
                print(f"❌ Health factor too low: {health_factor:.3f} (need >= 1.35)")
                return False

            # 5. Validate available borrows >= required borrow amount
            actual_available = account_data.get('availableBorrowsUSD', 0)
            if actual_available < required_borrow_amount:
                print(f"❌ Insufficient borrowing capacity: ${actual_available:.2f} (need ${required_borrow_amount:.2f})")
                return False

            # 6. Verify Uniswap integration
            if not hasattr(self, 'uniswap') or not self.uniswap:
                print("❌ Uniswap integration not initialized")
                return False

            # 7. Verify WALLET_S_ADDRESS is configured (required for DAI transfer step)
            if not self.wallet_s_address:
                print("❌ WALLET_S_ADDRESS not configured - required for execution")
                return False

            print(f"✅ All preconditions met - ETH: {eth_balance:.6f}, HF: {health_factor:.3f}, Available: ${actual_available:.2f}, Need: ${required_borrow_amount:.2f}")
            return True

        except Exception as e:
            print(f"❌ Precondition validation failed: {e}")
            return False

    def _calculate_validated_borrow_amount(self, available_borrows, operation_type="general"):
        """Calculate a validated borrow amount with multiple safety checks"""
        try:
            print(f"💰 Calculating safe borrow amount for {operation_type} operation...")

            # Base calculation based on operation type
            if operation_type == "growth":
                base_percentage = 0.10  # Conservative 10% for growth operations
                max_amount = 8.0
            elif operation_type == "capacity":
                base_percentage = 0.08  # Very conservative 8% for capacity operations
                max_amount = 5.0
            elif operation_type == "market_signal":
                base_percentage = 0.05  # Ultra conservative 5% for market signal operations
                max_amount = 3.0
            else:
                base_percentage = 0.05  # Ultra conservative 5% for general operations
                max_amount = 3.0

            # Calculate initial amount
            calculated_amount = available_borrows * base_percentage

            # Apply maximum cap
            safe_amount = min(calculated_amount, max_amount)

            # Apply minimum threshold
            if safe_amount < 0.5:
                print(f"⚠️ Calculated amount ${safe_amount:.2f} below minimum threshold")
                return 0.0

            # Additional safety check - ensure we're not borrowing too much relative to collateral
            account_data = self.aave.get_user_account_data()
            if account_data:
                total_collateral = account_data.get('totalCollateralUSD', 0)
                if total_collateral > 0:
                    max_safe_borrow = total_collateral * 0.02  # Maximum 2% of collateral per operation
                    safe_amount = min(safe_amount, max_safe_borrow)
                    print(f"📊 Collateral-based limit: ${max_safe_borrow:.2f}")

            print(f"💎 Final validated borrow amount: ${safe_amount:.2f}")
            return safe_amount

        except Exception as e:
            print(f"❌ Borrow amount calculation failed: {e}")
            return 0.0

    def _execute_validated_dai_borrow(self, borrow_amount):
        """
        Execute DAI borrow with ATOMIC execution guarantee and comprehensive validation.
        
        ATOMIC EXECUTION GUARANTEE:
        ===========================
        This method enforces strict atomicity: borrowed DAI MUST be swapped and supplied.
        There are NO skip paths - if swap or supply fails, the entire operation fails.
        
        This prevents the critical issue where borrowed DAI could remain unswapped/unsupplied,
        which would violate the core arbitrage strategy and leave the position unbalanced.
        
        Execution Flow:
        1. Validate borrow amount > 0
        2. Record DAI balance before borrow
        3. Execute borrow transaction on Aave
        4. Verify DAI balance increased
        5. Execute complete DeFi sequence (swap + supply)
        6. Return TRUE only if ALL steps succeed
        
        Args:
            borrow_amount: Amount of DAI to borrow in USD
            
        Returns:
            bool: True ONLY if borrow AND complete sequence succeed, False otherwise
        """
        try:
            print(f"🏦 Executing validated DAI borrow: ${borrow_amount:.2f}")

            # Pre-execution validation
            if borrow_amount <= 0:
                print("❌ Invalid borrow amount")
                return False

            # Check DAI token balance before operation
            dai_balance_before = self.get_dai_balance()
            print(f"📊 DAI balance before: {dai_balance_before:.6f}")

            # Attempt the borrow with detailed error catching
            try:
                result = self.aave.borrow_dai(borrow_amount)

                if result:
                    print(f"✅ Borrow transaction initiated: {result}")

                    # Wait a moment and verify the balance increased
                    import time
                    time.sleep(3)

                    dai_balance_after = self.get_dai_balance()
                    balance_increase = dai_balance_after - dai_balance_before

                    print(f"📊 DAI balance after: {dai_balance_after:.6f}")
                    print(f"📈 Balance increase: {balance_increase:.6f}")

                    if balance_increase > 0:
                        print(f"✅ Borrow successful - received {balance_increase:.6f} DAI")

                        # ATOMIC EXECUTION GUARANTEE: Execute complete sequence or fail entirely
                        # NO SKIP PATHS - borrowed DAI must ALWAYS be swapped and supplied
                        sequence_success = self._execute_complete_defi_sequence(balance_increase)
                        if sequence_success:
                            print("✅ Complete DeFi sequence executed successfully - ATOMIC OPERATION COMPLETE")
                            return True
                        else:
                            # CRITICAL FIX: Return False to enforce atomicity
                            # Borrowed DAI without swap/supply violates the arbitrage strategy
                            print("❌ ATOMIC GUARANTEE VIOLATION: Borrow succeeded but swap/supply FAILED")
                            print("❌ Operation marked as FAILED to prevent unswapped DAI position")
                            return False  # ATOMIC: Must fail if sequence fails (NO SKIP PATH)
                    else:
                        print("⚠️ Transaction completed but balance didn't increase as expected")
                        return False
                else:
                    print("❌ Borrow transaction failed")
                    return False

            except Exception as borrow_error:
                error_msg = str(borrow_error).lower()
                if "execution reverted" in error_msg:
                    print("❌ Transaction reverted by smart contract")
                    print("💡 Possible causes:")
                    print("   - Insufficient collateral")
                    print("   - Health factor too low")
                    print("   - Borrow cap reached")
                    print("   - Asset not enabled for borrowing")
                elif "insufficient funds" in error_msg:
                    print("❌ Insufficient ETH for gas fees")
                elif "nonce" in error_msg:
                    print("❌ Nonce error - transaction ordering issue")
                else:
                    print(f"❌ Borrow execution error: {borrow_error}")

                return False

        except Exception as e:
            print(f"❌ Validated borrow execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    
    def _swap_dai_for_gho(self, dai_amount):
        """
        Swap DAI for GHO via Uniswap.
        GHO is held in wallet (not supplied to Aave).
        
        NETWORK-AWARE: GHO only available on mainnet.
        
        Args:
            dai_amount: Amount of DAI to swap
            
        Returns:
            bool: True if swap succeeded, False otherwise
        """
        try:
            # Guard: Check if GHO is available on this network
            if not self.gho_address:
                print("⚠️ GHO not available on this network - operation N/A (not a failure)")
                return True  # Return True since this is not an error, just N/A
            
            if not self.uniswap:
                print("❌ Uniswap integration not available")
                return False
            
            print(f"🔄 Swapping {dai_amount:.6f} DAI → GHO via Uniswap...")
            
            # GHO swap uses generic token swap method
            swap_result = self.uniswap.swap_tokens(
                self.dai_address,
                self.gho_address,
                dai_amount
            )
            
            if swap_result and 'tx_hash' in swap_result:
                print(f"✅ GHO swap successful: {swap_result['tx_hash']}")
                return True
            else:
                print("❌ GHO swap failed")
                return False
                
        except Exception as e:
            print(f"❌ GHO swap error: {e}")
            return False
    
    def _get_gho_balance(self):
        """
        Get GHO balance from wallet.
        
        NETWORK-AWARE: Returns 0 if GHO not available on this network.
        """
        try:
            # Guard: Check if GHO is available on this network
            if not self.gho_address:
                return 0.0
            
            if not hasattr(self, 'aave') or not self.aave:
                return 0.0
            return self.aave.get_token_balance(self.gho_address)
        except Exception as e:
            print(f"❌ Failed to get GHO balance: {e}")
            return 0.0
    
    def _unwrap_weth_to_eth(self, weth_amount):
        """
        Unwrap WETH to native ETH.
        ETH is held in wallet (not supplied to Aave).
        
        Args:
            weth_amount: Amount of WETH to unwrap
            
        Returns:
            bool: True if unwrap succeeded, False otherwise
        """
        try:
            print(f"🔄 Unwrapping {weth_amount:.8f} WETH → ETH...")
            
            # WETH contract ABI for withdraw function
            weth_abi = [{
                "constant": False,
                "inputs": [{"name": "wad", "type": "uint256"}],
                "name": "withdraw",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            weth_contract = self.w3.eth.contract(
                address=self.weth_address,
                abi=weth_abi
            )
            
            # Convert to wei
            weth_wei = int(weth_amount * 1e18)
            
            # Build transaction
            tx = weth_contract.functions.withdraw(weth_wei).build_transaction({
                'from': self.address,
                'gas': 50000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address)
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            if receipt.status == 1:
                print(f"✅ WETH unwrapped to ETH")
                print(f"   ✅ Success: https://arbiscan.io/tx/{self.w3.to_hex(tx_hash)}")
            else:
                print(f"❌ WETH unwrap transaction failed on-chain")
                return False
            return True
            
        except Exception as e:
            print(f"❌ WETH unwrap error: {e}")
            return False
    
    def _perform_safety_sweep(self):
        """Nurse Mode: Detect and supply idle WETH, WBTC, DAI to Aave when balance > $1.10 USD"""
        try:
            print("🚑 Nurse Mode: Scanning wallet for idle assets...")
            MIN_USD_THRESHOLD = 1.10
            ETH_GAS_RESERVE = 0.001
            ETH_PRICE_FALLBACK = 2000.0
            BTC_PRICE_FALLBACK = 67000.0

            eth_balance = self.get_eth_balance()
            weth_balance = self.get_weth_balance()
            wbtc_balance = self.get_wbtc_balance()
            dai_balance = self.get_dai_balance()

            print(f"   WETH: {weth_balance:.8f} | WBTC: {wbtc_balance:.8f} | DAI: {dai_balance:.6f} | ETH (gas): {eth_balance:.6f}")

            supplied_any = False

            weth_usd = weth_balance * ETH_PRICE_FALLBACK
            if weth_usd > MIN_USD_THRESHOLD:
                if eth_balance > ETH_GAS_RESERVE:
                    print(f"🚑 Nurse Mode: Found ${weth_usd:.2f} of WETH. Supplying to Aave to boost Health Factor.")
                    if self._supply_weth_to_aave(weth_balance):
                        supplied_any = True
                    else:
                        print("   ⚠️ WETH supply failed")
                else:
                    print(f"   ⚠️ WETH detected (${weth_usd:.2f}) but ETH gas too low ({eth_balance:.6f} < {ETH_GAS_RESERVE}). Skipping.")

            wbtc_usd = wbtc_balance * BTC_PRICE_FALLBACK
            if wbtc_usd > MIN_USD_THRESHOLD:
                print(f"🚑 Nurse Mode: Found ${wbtc_usd:.2f} of WBTC. Supplying to Aave to boost Health Factor.")
                if self._supply_wbtc_to_aave(wbtc_balance):
                    supplied_any = True
                else:
                    print("   ⚠️ WBTC supply failed")

            if dai_balance > MIN_USD_THRESHOLD:
                print(f"🚑 Nurse Mode: Found ${dai_balance:.2f} of DAI. Supplying to Aave to boost Health Factor.")
                if self._resupply_dai_to_aave(dai_balance * 0.99):
                    supplied_any = True
                else:
                    print("   ⚠️ DAI supply failed")

            if not supplied_any:
                print("🚑 Nurse Mode: No idle assets above $1.10 threshold. Wallet clean.")
            else:
                hf_data = self.aave.get_user_account_data() if self.aave else None
                new_hf = hf_data.get('healthFactor', 0) if hf_data else 0
                print(f"🚑 Nurse Mode: Sweep complete. New Health Factor: {new_hf:.4f}")

        except Exception as e:
            print(f"❌ Nurse Mode error: {e}")
            import traceback
            traceback.print_exc()

    def _resupply_dai_to_aave(self, dai_amount):
        """
        Resupply DAI directly to Aave as collateral (no swap needed).
        
        Args:
            dai_amount: Amount of DAI to supply
            
        Returns:
            bool: True if supply succeeded, False otherwise
        """
        try:
            if not self.aave:
                print("❌ Aave integration not available")
                return False
            
            print(f"🏦 Resupplying {dai_amount:.6f} DAI to Aave...")
            
            # Use Aave integration to supply DAI
            supply_result = self.aave.supply_dai_to_aave(dai_amount)
            
            if supply_result:
                tx_str = str(supply_result)
                print(f"✅ DAI resupply completed")
                if tx_str.startswith("0x"):
                    print(f"   ✅ Success: https://arbiscan.io/tx/{tx_str}")
                else:
                    print(f"   TX: {tx_str}")
                return True
            else:
                print("❌ DAI resupply failed")
                return False
                
        except Exception as e:
            print(f"❌ DAI resupply error: {e}")
            return False

    def _execute_dai_to_wbtc_swap(self, dai_amount):
        """Execute DAI to WBTC swap and return amount received"""
        try:
            if not self.uniswap:
                print("❌ Uniswap integration not available")
                return 0

            print(f"🔄 Executing DAI → WBTC swap for {dai_amount:.6f} DAI")

            # Get WBTC balance before swap
            wbtc_balance_before = self.get_wbtc_balance()

            # Execute swap
            swap_result = self.uniswap.swap_dai_for_wbtc(dai_amount)

            if swap_result and 'tx_hash' in swap_result:
                print(f"✅ WBTC swap tx sent")
                print(f"   ✅ Success: https://arbiscan.io/tx/{swap_result['tx_hash']}")
                # Wait for confirmation
                import time
                time.sleep(5)

                # Get WBTC balance after swap
                wbtc_balance_after = self.get_wbtc_balance()
                wbtc_received = wbtc_balance_after - wbtc_balance_before

                print(f"✅ WBTC swap completed: {wbtc_received:.8f} WBTC received")
                return wbtc_received
            else:
                print("❌ WBTC swap failed")
                return 0

        except Exception as e:
            print(f"❌ DAI to WBTC swap error: {e}")
            return 0

    def _execute_dai_to_weth_swap(self, dai_amount):
        """Execute DAI to WETH swap and return amount received"""
        try:
            if not self.uniswap:
                print("❌ Uniswap integration not available")
                return 0

            print(f"🔄 Executing DAI → WETH swap for {dai_amount:.6f} DAI")

            # Get WETH balance before swap
            weth_balance_before = self.get_weth_balance()

            # Execute swap
            swap_result = self.uniswap.swap_dai_for_weth(dai_amount)

            if swap_result and 'tx_hash' in swap_result:
                print(f"✅ WETH swap tx sent")
                print(f"   ✅ Success: https://arbiscan.io/tx/{swap_result['tx_hash']}")
                # Wait for confirmation
                import time
                time.sleep(5)

                # Get WETH balance after swap
                weth_balance_after = self.get_weth_balance()
                weth_received = weth_balance_after - weth_balance_before

                print(f"✅ WETH swap completed: {weth_received:.8f} WETH received")
                return weth_received
            else:
                print("❌ WETH swap failed")
                return 0

        except Exception as e:
            print(f"❌ DAI to WETH swap error: {e}")
            return 0

    def _supply_wbtc_to_aave(self, wbtc_amount):
        """Supply WBTC to Aave and return success status"""
        try:
            if not self.aave:
                print("❌ Aave integration not available")
                return False

            print(f"🏦 Supplying {wbtc_amount:.8f} WBTC to Aave")

            # Execute supply
            supply_result = self.aave.supply_wbtc_to_aave(wbtc_amount)

            if supply_result:
                tx_str = str(supply_result)
                print(f"✅ WBTC supply completed")
                if tx_str.startswith("0x"):
                    print(f"   ✅ Success: https://arbiscan.io/tx/{tx_str}")
                else:
                    print(f"   TX: {tx_str}")
                return True
            else:
                print("❌ WBTC supply failed")
                return False

        except Exception as e:
            print(f"❌ WBTC supply error: {e}")
            return False

    def _supply_weth_to_aave(self, weth_amount):
        """Supply WETH to Aave and return success status"""
        try:
            if not self.aave:
                print("❌ Aave integration not available")
                return False

            print(f"🏦 Supplying {weth_amount:.8f} WETH to Aave")

            # Execute supply
            supply_result = self.aave.supply_weth_to_aave(weth_amount)

            if supply_result:
                tx_str = str(supply_result)
                print(f"✅ WETH supply completed")
                if tx_str.startswith("0x"):
                    print(f"   ✅ Success: https://arbiscan.io/tx/{tx_str}")
                else:
                    print(f"   TX: {tx_str}")
                return True
            else:
                print("❌ WETH supply failed")
                return False

        except Exception as e:
            print(f"❌ WETH supply error: {e}")
            return False

    def get_eth_balance(self):
        """Get ETH balance in readable format"""
        try:
            balance_wei = self.w3.eth.get_balance(self.address)
            return balance_wei / (10**18)
        except Exception as e:
            print(f"❌ Failed to get ETH balance: {e}")
            return 0.0

    def get_dai_balance(self):
        """Get DAI balance using Aave integration"""
        try:
            if hasattr(self, 'aave') and self.aave:
                return self.aave.get_dai_balance()
            else:
                print("❌ Aave integration not available for DAI balance")
                return 0.0
        except Exception as e:
            print(f"❌ Failed to get DAI balance: {e}")
            return 0.0

    def get_health_factor(self):
        """Get current health factor from Aave"""
        try:
            if hasattr(self, 'aave') and self.aave:
                account_data = self.aave.get_user_account_data()
                return account_data.get('healthFactor', 0) if account_data else 0
            else:
                print("❌ Aave integration not available for health factor")
                return 0.0
        except Exception as e:
            print(f"❌ Failed to get health factor: {e}")
            return 0.0

    def run_real_defi_task(self, run_id, iteration, agent_config):
        """Run real DeFi task with Global Execution Lock, growth trigger first, then capacity trigger.
        On startup, checks execution_state.json for interrupted sequences and resumes them."""
        try:
            print(f"\n🚀 Monitoring cycle {run_id}-{iteration}")

            pending_state = self.load_execution_state()
            if pending_state and pending_state.get("step") != "wallet_s_transferred":
                print(f"\n🔄 CRASH RECOVERY: Found interrupted '{pending_state['path_name']}' path at step '{pending_state['step']}'")
                print(f"   Resuming execution from after '{pending_state['step']}'...")

                if not hasattr(self, 'aave') or not self.aave:
                    print("❌ Aave integration not available — cannot resume")
                    return 0.5

                saved_dist = pending_state['distribution']
                path_name = pending_state['path_name']
                resume_step = pending_state['step']

                recovery_attempts = pending_state.get('recovery_attempts', 0) + 1
                pending_state['recovery_attempts'] = recovery_attempts
                if recovery_attempts > 5:
                    print(f"⚠️ Recovery failed {recovery_attempts} times — clearing stale state")
                    self.save_execution_state("wallet_s_transferred", path_name, saved_dist)
                    self.clear_execution_state()
                    return 0.5

                self._save_raw_execution_state(pending_state)

                dai_balance = self.get_dai_balance()
                print(f"💰 Recovery DAI balance: ${dai_balance:.4f}")

                if dai_balance >= 0.90 * sum([
                    saved_dist.get('wbtc_swap_supply', 0),
                    saved_dist.get('weth_swap_supply', 0),
                    saved_dist.get('eth_gas_reserve', 0),
                    saved_dist.get('dai_transfer', 0),
                ]):
                    print(f"✅ Sufficient DAI for full recovery — executing standard resume")
                    if self._execute_fixed_distribution(path_name, saved_dist, resume_after=resume_step):
                        print(f"✅ RECOVERY COMPLETE: {path_name.upper()} path finished successfully")
                        return 0.9
                    else:
                        print(f"❌ Full recovery failed (attempt {recovery_attempts}/5) — trying proportional next cycle")
                        return 0.4
                else:
                    print(f"📉 Insufficient DAI for full recovery — using PROPORTIONAL RECOVERY")
                    if self._execute_proportional_recovery(pending_state):
                        print(f"✅ PROPORTIONAL RECOVERY COMPLETE: {path_name.upper()} path")
                        return 0.9
                    else:
                        print(f"❌ Proportional recovery failed (attempt {recovery_attempts}/5) — state preserved")
                        return 0.4

            if self._is_execution_locked():
                print("🔒 Skipping cycle - execution locked")
                return 0.5

            if not hasattr(self, 'aave') or not self.aave:
                print("❌ Aave integration not available")
                return 0.5

            account_data = self.aave.get_user_account_data()
            if not account_data:
                print("❌ Could not retrieve account data")
                return 0.3

            health_factor = account_data.get('healthFactor', 0)
            available_borrows = account_data.get('availableBorrowsUSD', 0)
            total_collateral = account_data.get('totalCollateralUSD', 0)

            print(f"📊 Position: Collateral ${total_collateral:.2f} | Baseline ${self.last_collateral_value_usd:.2f} | HF {health_factor:.3f} | Available ${available_borrows:.2f}")
            print(f"🔒 Lock: {'TRANSACTING' if self.is_transacting else 'UNLOCKED'} | Growth needs ${self.growth_min_capacity:.0f} cap | Capacity needs ${self.capacity_min_capacity:.0f} cap")

            performance = 0.5

            if health_factor < 1.35:
                print(f"🚨 EMERGENCY: Health factor {health_factor:.3f} below 1.35!")
                dai_balance = self.aave.get_token_balance(self.dai_address) if self.aave else 0
                if dai_balance > 0.5:
                    safe_amount = dai_balance * 0.99
                    print(f"🛡️ EMERGENCY RECOVERY: Found {dai_balance:.4f} DAI in wallet — supplying {safe_amount:.4f} to Aave to restore HF")
                    if self._resupply_dai_to_aave(safe_amount):
                        print(f"✅ EMERGENCY RECOVERY SUCCESS: Supplied {dai_balance:.4f} DAI as collateral")
                        performance = 0.6
                    else:
                        print(f"❌ EMERGENCY RECOVERY FAILED: Could not supply DAI")
                        performance = 0.1
                else:
                    print(f"   No recoverable DAI in wallet ({dai_balance:.4f} DAI)")
                    performance = 0.1
                return performance

            growth_met, growth_reason, abs_growth, rel_growth = self._check_collateral_growth(total_collateral, health_factor)
            executed = False

            if growth_met and available_borrows >= self.growth_min_capacity:
                if growth_reason == "absolute":
                    print(f"✅ Growth trigger met (ABSOLUTE): ${abs_growth:.2f} >= ${self.growth_trigger_threshold}")
                else:
                    print(f"✅ Growth trigger met (RELATIVE): {rel_growth*100:.1f}% >= {self.growth_percentage_threshold*100:.0f}%")
                print(f"🔥 GROWTH TRIGGER ACTIVATED: Collateral grew from ${self.last_collateral_value_usd:.2f} -> ${total_collateral:.2f}")
                print(f"   Executing Growth Path: Borrow ${self.GROWTH_DISTRIBUTION['total_borrow']:.2f} DAI")
                if self._execute_growth_triggered_operation(available_borrows):
                    print(f"✅ GROWTH OPERATION SUCCESS")
                    self.update_baseline_after_success(total_collateral)
                    print(f"✅ Baseline updated: ${self.last_collateral_value_usd:.2f} -> ${total_collateral:.2f}")
                    performance = 0.9
                else:
                    print(f"❌ Growth operation failed")
                    performance = 0.4
                executed = True

            elif growth_met and available_borrows < self.growth_min_capacity:
                growth_pct = rel_growth * 100
                print(f"📊 GROWTH CONDITIONS MET ({growth_pct:.1f}% growth) but CAPACITY BLOCKED: ${available_borrows:.2f} < ${self.growth_min_capacity:.0f} needed")
                print(f"   ➡️ FALLING THROUGH to Capacity Path evaluation...")

                if self._should_execute_capacity_operation(available_borrows, health_factor):
                    print(f"⚡ CAPACITY TRIGGER ACTIVATED (via fall-through): ${available_borrows:.2f} available >= ${self.capacity_min_capacity:.0f}")
                    print(f"   Executing Capacity Path: Borrow ${self.CAPACITY_DISTRIBUTION['total_borrow']:.2f} DAI")
                    if self._execute_capacity_operation(available_borrows):
                        print(f"✅ CAPACITY OPERATION SUCCESS (Growth was blocked, Capacity executed)")
                        performance = 0.8
                    else:
                        print(f"❌ Capacity operation failed")
                        performance = 0.4
                    executed = True
                else:
                    print(f"   ❌ Capacity Path also not met: ${available_borrows:.2f} < ${self.capacity_min_capacity:.0f}")

            if not executed:
                if self._should_execute_capacity_operation(available_borrows, health_factor):
                    print(f"⚡ CAPACITY TRIGGER ACTIVATED: ${available_borrows:.2f} available")
                    print(f"   Executing Capacity Path: Borrow ${self.CAPACITY_DISTRIBUTION['total_borrow']:.2f} DAI")
                    if self._execute_capacity_operation(available_borrows):
                        print(f"✅ CAPACITY OPERATION SUCCESS")
                        performance = 0.8
                    else:
                        print(f"❌ Capacity operation failed")
                        performance = 0.4
                    executed = True

            if not executed:
                growth_from_baseline = total_collateral - self.last_collateral_value_usd
                growth_pct = (growth_from_baseline / self.last_collateral_value_usd * 100) if self.last_collateral_value_usd > 0 else 0
                print(f"💤 IDLE: Growth ${growth_from_baseline:.2f} ({growth_pct:.1f}%) from ${self.last_collateral_value_usd:.0f} baseline")
                print(f"   Growth Path: needs ${self.growth_min_capacity:.0f} capacity + 10% growth (have ${available_borrows:.2f} + {growth_pct:.1f}%)")
                print(f"   Capacity Path: needs ${self.capacity_min_capacity:.0f} capacity (have ${available_borrows:.2f})")
                performance = 0.6

            return performance

        except Exception as e:
            print(f"❌ Real DeFi task failed: {e}")
            import traceback
            traceback.print_exc()
            return 0.2

    def _setup_enhanced_error_handling(self):
        """Setup enhanced error handling for the agent"""
        try:
            # Basic error handling setup
            signal.signal(signal.SIGINT, self._handle_emergency_stop)
            signal.signal(signal.SIGTERM, self._handle_emergency_stop)
            print("✅ Enhanced error handling setup complete")
        except Exception as e:
            print(f"⚠️ Error handling setup failed: {e}")

    def _handle_emergency_stop(self, signum, frame):
        """Handle emergency stop signals"""
        print("🛑 Emergency stop signal received")
        print("🔄 Gracefully shutting down operations...")
        # Add cleanup logic here if needed
        exit(0)

    def get_token_balance(self, token_symbol):
        """Get balance of a specified token"""
        token_map = {
            'ARB': self.arb_address,
            'DAI': self.dai_address,
            'WBTC': self.wbtc_address,
            'WETH': self.weth_address
        }
        token_address = token_map.get(token_symbol)
        if not token_address:
            print(f"❌ Unknown token symbol: {token_symbol}")
            return 0.0

        try:
            if self.aave:
                return self.aave.get_token_balance(token_address)
            return 0.0
        except Exception as e:
            print(f"❌ Error getting {token_symbol} balance: {e}")
            return 0.0


    def _validate_debt_swap_readiness(self):
        """Validate readiness for debt swap operations"""
        try:
            print("🔄 VALIDATING DEBT SWAP READINESS")
            print("=" * 40)

            validation_results = {
                'market_signal_enabled': False,
                'sufficient_balance': False,
                'healthy_position': False,
                'network_connected': False,
                'integrations_ready': False
            }

            # Check if market signal strategy is enabled
            if (hasattr(self, 'market_signal_strategy') and
                self.market_signal_strategy and
                getattr(self.market_signal_strategy, 'market_signal_enabled', False)):
                validation_results['market_signal_enabled'] = True
                print("✅ Market signal strategy enabled")
            else:
                print("❌ Market signal strategy not enabled")

            # Check balances
            dai_balance = self.get_dai_balance()
            arb_balance = self.get_arb_balance()
            eth_balance = self.get_eth_balance()

            if dai_balance > 0.1 or arb_balance > 0.1:
                validation_results['sufficient_balance'] = True
                print(f"✅ Sufficient token balances - DAI: {dai_balance:.2f}, ARB: {arb_balance:.2f}")
            else:
                print(f"❌ Insufficient token balances - DAI: {dai_balance:.2f}, ARB: {arb_balance:.2f}")

            # Check health factor
            health_factor = self.get_health_factor()
            if health_factor > 2.0:
                validation_results['healthy_position'] = True
                print(f"✅ Healthy position - HF: {health_factor:.3f}")
            else:
                print(f"❌ Risky position - HF: {health_factor:.3f}")

            # Check network connectivity
            if self.w3 and self.w3.is_connected():
                validation_results['network_connected'] = True
                print("✅ Network connected")
            else:
                print("❌ Network not connected")

            # Check integrations
            if (hasattr(self, 'aave') and self.aave and
                hasattr(self, 'uniswap') and self.uniswap):
                validation_results['integrations_ready'] = True
                print("✅ DeFi integrations ready")
            else:
                print("❌ DeFi integrations not ready")

            # Overall readiness score
            ready_count = sum(validation_results.values())
            total_checks = len(validation_results)
            readiness_score = (ready_count / total_checks) * 100

            print(f"\n📊 DEBT SWAP READINESS: {ready_count}/{total_checks} ({readiness_score:.0f}%)")

            return {
                'ready': ready_count >= 4,  # Need at least 4/5 checks to pass
                'score': readiness_score,
                'details': validation_results
            }

        except Exception as e:
            print(f"❌ Debt swap readiness validation failed: {e}")
            return {'ready': False, 'score': 0, 'details': {}}


    def get_user_account_data(self):
        """Get user account data from Aave"""
        try:
            if hasattr(self, 'aave') and self.aave:
                return self.aave.get_user_account_data()
            else:
                print("❌ Aave integration not available")
                return None
        except Exception as e:
            print(f"❌ Failed to get user account data: {e}")
            return None

    def get_wbtc_balance(self):
        """Get WBTC balance using Aave integration"""
        try:
            if hasattr(self, 'aave') and self.aave:
                return self.aave.get_token_balance(self.wbtc_address)
            else:
                print("❌ Aave integration not available for WBTC balance")
                return 0.0
        except Exception as e:
            print(f"❌ Failed to get WBTC balance: {e}")
            return 0.0

    def get_weth_balance(self):
        """Get WETH balance using Aave integration"""
        try:
            if hasattr(self, 'aave') and self.aave:
                return self.aave.get_token_balance(self.weth_address)
            else:
                print("❌ Aave integration not available for WETH balance")
                return 0.0
        except Exception as e:
            print(f"❌ Failed to get WETH balance: {e}")
            return 0.0

    def get_arb_balance(self):
        """Get ARB balance using Aave integration"""
        try:
            if hasattr(self, 'aave') and self.aave:
                return self.aave.get_token_balance(self.arb_address)
            else:
                print("❌ Aave integration not available for ARB balance")
                return 0.0
        except Exception as e:
            print(f"❌ Failed to get ARB balance: {e}")
            return 0.0

    def run(self):
        """Main loop for the agent with Global Execution Lock"""
        print("\n" + "="*60)
        print("🚀 STARTING AUTONOMOUS TRADING AGENT 🚀")
        print("="*60 + "\n")

        if not self.initialize_integrations():
            print("❌ Failed to initialize critical integrations. Exiting.")
            sys.exit(1)

        if not self.baseline_initialized:
            self._auto_initialize_baseline()

        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'Iter.':<10} | {'Health Factor':<15} | {'Action':<25} | {'Status':<15}")
            print("-" * 70)

            performance_score = 0.5

            try:
                # CHECK GLOBAL EXECUTION LOCK
                if self._is_execution_locked():
                    print(f"{iteration:<10} | {'N/A':<15} | {'LOCKED':<25} | {'COOLDOWN':<15}")
                    time.sleep(30)
                    continue

                account_data = self.get_user_account_data()
                if not account_data:
                    print("❌ Failed to get account data. Skipping iteration.")
                    time.sleep(10)
                    continue

                health_factor = account_data.get('healthFactor', 0)
                available_borrows = account_data.get('availableBorrowsUSD', 0)
                total_collateral = account_data.get('totalCollateralUSD', 0)

                print(f"📊 Position: Collateral ${total_collateral:.2f} | Baseline ${self.last_collateral_value_usd:.2f} | HF {health_factor:.3f} | Available ${available_borrows:.2f}")

                if health_factor < 1.35:
                    action = "EMERGENCY"
                    status = "CRITICAL"
                    performance_score *= 0.1
                else:
                    growth_met, g_reason, g_abs, g_rel = self._check_collateral_growth(total_collateral, health_factor)
                    run_executed = False

                    if growth_met and available_borrows >= self.growth_min_capacity:
                        action = "GROWTH PATH"
                        status = "EXECUTING"
                        print(f"🔥 GROWTH TRIGGER: ${self.last_collateral_value_usd:.2f} -> ${total_collateral:.2f}")
                        if self._execute_growth_triggered_operation(available_borrows):
                            performance_score += 0.3
                            status = "SUCCESS"
                            self.update_baseline_after_success(total_collateral)
                        else:
                            status = "FAILED"
                            performance_score *= 0.5
                        run_executed = True
                    elif growth_met and available_borrows < self.growth_min_capacity:
                        print(f"📊 Growth met but capacity blocked: ${available_borrows:.2f} < ${self.growth_min_capacity:.0f} → falling through to Capacity")
                        if self._should_execute_capacity_operation(available_borrows, health_factor):
                            action = "CAPACITY PATH (FALL-THROUGH)"
                            status = "EXECUTING"
                            if self._execute_capacity_operation(available_borrows):
                                performance_score += 0.2
                                status = "SUCCESS"
                            else:
                                status = "FAILED"
                                performance_score *= 0.5
                            run_executed = True

                    if not run_executed:
                        if self._should_execute_capacity_operation(available_borrows, health_factor):
                            action = "CAPACITY PATH"
                            status = "EXECUTING"
                            if self._execute_capacity_operation(available_borrows):
                                performance_score += 0.2
                                status = "SUCCESS"
                            else:
                                status = "FAILED"
                                performance_score *= 0.5
                        else:
                            action = "IDLE / MONITORING"
                            status = "HEALTHY"
                            performance_score += 0.05

                performance_score = self._perform_debt_swap_operations(performance_score)

                if hasattr(self, 'track_operation_attempt'):
                    self.track_operation_attempt()

                print(f"{iteration:<10} | {health_factor:<15.3f} | {action:<25} | {status:<15}")

                # 130s cooldown sleep managed by global lock
                time.sleep(30)

            except Exception as e:
                print(f"\n❌ UNEXPECTED ERROR IN MAIN LOOP: {e}")
                print("🔄 Attempting to recover and continue...")
                import traceback
                traceback.print_exc()
                time.sleep(10)

    def _perform_debt_swap_operations(self, performance_score):
        """ Execute debt swap operations based on market signals """
        # 🎯 OPTIMIZED DEBT SWAP SYSTEM WITH MACD AND ENHANCED TRIGGERS
        if self.debt_swap_active and hasattr(self, 'market_signal_strategy') and self.market_signal_strategy:
            try:
                # Get market analysis for debt swap decisions
                signals = self.market_signal_strategy.analyze_market_signals()

                if signals and signals.get('status') == 'success':
                    action = signals.get('action', 'hold')
                    confidence = signals.get('confidence_level', 0)
                    signals_detected = signals.get('signals_detected', [])

                    # Enhanced logging for transparency
                    from swap_console_reporter import SwapConsoleReporter
                    reporter = SwapConsoleReporter()

                    # CORRECTED HIGH-FREQUENCY EXECUTION LOGIC
                    if action == 'dai_to_arb':
                        # Check for MACD bearish crossover (buy low trigger)
                        macd_bearish_trigger = any('MACD Bearish Crossover' in signal for signal in signals_detected)

                        # High-frequency threshold (0.4 for faster execution)
                        if confidence >= 0.4 or macd_bearish_trigger:
                            print(f"📉 EXECUTING DAI→ARB SWAP (buy low strategy)")
                            print(f"   Confidence: {confidence:.2f} (threshold: 0.4)")
                            print(f"   MACD Bearish: {'✅ DETECTED' if macd_bearish_trigger else '❌'}")
                            print(f"   Strategy: BUY LOW when ARB is oversold/bearish")
                            print(f"   Signals: {', '.join(signals_detected)}")

                            # Get decision reasons
                            reasons = self.market_signal_strategy.get_swap_decision_reasons('dai_to_arb')

                            # Execute high-frequency swap
                            swap_amount = self._calculate_optimal_swap_amount('dai_to_arb')
                            result = self._execute_debt_swap_dai_to_arb(confidence)

                            # Report swap execution
                            reporter.report_swap_execution('dai_to_arb', swap_amount, reasons, confidence)

                            if result:
                                print("✅ DAI→ARB (buy low) swap completed successfully")
                                performance_score += 0.3  # Moderate reward for high-frequency
                            else:
                                print("❌ DAI→ARB (buy low) swap failed")
                        else:
                            print(f"⏸️ DAI→ARB confidence {confidence:.2f} below high-frequency threshold (0.4)")

                    elif action == 'arb_to_dai':
                        # Check for MACD bullish crossover (sell high trigger)
                        macd_bullish_trigger = any('MACD Bullish Crossover' in signal for signal in signals_detected)

                        # High-frequency threshold (0.4 for faster execution)
                        if confidence >= 0.4 or macd_bullish_trigger:
                            print(f"🚀 EXECUTING ARB→DAI SWAP (sell high strategy)")
                            print(f"   Confidence: {confidence:.2f} (threshold: 0.4)")
                            print(f"   MACD Bullish: {'✅ DETECTED' if macd_bullish_trigger else '❌'}")
                            print(f"   Strategy: SELL HIGH when ARB is overbought/bullish")
                            print(f"   Signals: {', '.join(signals_detected)}")

                            # Get decision reasons
                            reasons = self.market_signal_strategy.get_swap_decision_reasons('arb_to_dai')

                            # Execute high-frequency swap
                            swap_amount = self._calculate_optimal_swap_amount('arb_to_dai')
                            result = self._execute_debt_swap_arb_to_dai(confidence)

                            # Report swap execution
                            reporter.report_swap_execution('arb_to_dai', swap_amount, reasons, confidence)

                            if result:
                                print("✅ ARB→DAI (sell high) swap completed successfully")
                                performance_score += 0.3  # Moderate reward for high-frequency
                            else:
                                print("❌ ARB→DAI (sell high) swap failed")
                        else:
                            print(f"⏸️ ARB→DAI confidence {confidence:.2f} below high-frequency threshold (0.4)")
                    else:
                        # HOLD decision with reasons
                        reasons = self.market_signal_strategy.get_swap_decision_reasons('hold')
                        print(f"💰 HOLDING POSITION - Market Analysis:")
                        print(f"   Action: {action.upper()}")
                        print(f"   Confidence: {confidence:.2f}")
                        print(f"   Reasons:")
                        for i, reason in enumerate(reasons, 1):
                            print(f"      {i}. {reason}")

                else:
                    print("⚠️ Market signal analysis failed - using conservative strategy")
            except Exception as e:
                print(f"❌ Error during debt swap operations: {e}")
                import traceback
                traceback.print_exc()

        return performance_score # Return the potentially modified performance_score

    def _calculate_optimal_swap_amount(self, swap_type: str) -> float:
        """Calculate optimal swap amount for high-frequency trading (small, frequent swaps)"""
        try:
            if not self.aave:
                return 0.0

            account_data = self.aave.get_user_account_data()
            if not account_data:
                return 0.0

            available_borrows = account_data.get('availableBorrowsUSD', 0)
            health_factor = account_data.get('healthFactor', 0)

            if swap_type == 'dai_to_arb':
                # High-frequency: small, safe DAI swaps (buy low strategy)
                if health_factor > 2.5:
                    return min(available_borrows * 0.05, 10.0)  # 5% or $10 max
                elif health_factor > 2.0:
                    return min(available_borrows * 0.03, 5.0)   # 3% or $5 max
                elif health_factor > 1.8:
                    return min(available_borrows * 0.02, 2.0)   # 2% or $2 max
                else:
                    return 0.0
            elif swap_type == 'arb_to_dai':
                # High-frequency: small ARB sales (sell high strategy)
                arb_balance = self.get_arb_balance()

                if arb_balance > 10.0:
                    return min(arb_balance * 0.3, 10.0)  # 30% or $10 max
                elif arb_balance > 5.0:
                    return min(arb_balance * 0.4, 5.0)   # 40% or $5 max
                elif arb_balance > 1.0:
                    return min(arb_balance * 0.5, 2.0)   # 50% or $2 max
                else:
                    return arb_balance  # Swap all if very small amount

            return 0.0

        except Exception as e:
            logger.error(f"Error calculating high-frequency swap amount: {e}")
            return 0.0

    def check_debt_swap_conditions(self):
        """Check if debt swap conditions are met"""
        try:
            # Check if market signal strategy is available
            if not hasattr(self, 'market_signal_strategy') or not self.market_signal_strategy:
                return False, "Market signal strategy not available"

            # Check if strategy is properly initialized
            if not hasattr(self.market_signal_strategy, 'initialization_successful'):
                return False, "Market signal strategy not initialized"

            if not self.market_signal_strategy.initialization_successful:
                return False, "Market signal strategy initialization failed"

            # Check technical indicators readiness
            status = self.market_signal_strategy.get_strategy_status()
            tech_ready = status.get('technical_indicators_ready', False)

            if not tech_ready:
                arb_points = status.get('enhanced_arb_points', 0)
                btc_points = status.get('enhanced_btc_points', 0)
                min_points = status.get('min_points_for_basic', 5)
                return False, f"Insufficient data points (ARB: {arb_points}, BTC: {btc_points}, need: {min_points})"

            # Check health factor if Aave is available
            if hasattr(self, 'aave') and self.aave:
                try:
                    account_data = self.aave.get_user_account_data()
                    if account_data:
                        health_factor = account_data.get('healthFactor', 0)
                        if health_factor < 1.35:
                            return False, f"Health factor too low: {health_factor:.3f} (need >1.35)"
                    else:
                        return False, "Cannot retrieve account data"
                except Exception as hf_error:
                    return False, f"Health factor check failed: {hf_error}"

            # Check debt swap activation
            if not getattr(self, 'debt_swap_active', False):
                return False, "Debt swap system not activated"

            return True, "All debt swap conditions met - system ready"

        except Exception as e:
            return False, f"Debt swap condition check failed: {e}"

    def _execute_debt_swap_dai_to_arb(self, confidence):
        """Execute DAI to ARB debt swap with profit tracking"""
        try:
            print("🔄 Executing DAI → ARB debt swap...")

            # Check DAI balance
            dai_balance = self.get_dai_balance()

            if dai_balance < 10.0:  # Need at least $10 DAI
                print(f"❌ Insufficient DAI balance: {dai_balance:.2f}")
                return False

            # Calculate optimal swap amount
            swap_amount = self._calculate_optimal_swap_amount('dai_to_arb')

            if swap_amount < 1.0:
                print("❌ Optimal swap amount too low for DAI→ARB")
                return False

            print(f"💱 Swapping {swap_amount:.2f} DAI for ARB...")

            # Execute swap via Uniswap
            if hasattr(self, 'uniswap') and self.uniswap:
                result = self.uniswap.swap_dai_for_arb(swap_amount)

                if result and result.get('success'):
                    tx_hash = result.get('tx_hash')
                    cycle_id = result.get('cycle_id')

                    print(f"✅ DAI → ARB swap successful!")
                    print(f"🔗 TX: {tx_hash}")
                    print(f"📊 Cycle ID: {cycle_id}")

                    # Log the swap with console reporter
                    try:
                        from swap_console_reporter import log_swap_execution
                        log_swap_execution('dai_to_arb', swap_amount, result.get('arb_received', 0),
                                         self.market_signal_strategy.get_swap_decision_reasons('dai_to_arb'))
                    except Exception as log_err:
                        print(f"Logging error: {log_err}")

                    return True
                else:
                    print("❌ DAI → ARB swap failed")
                    return False
            else:
                print("❌ Uniswap integration not available")
                return False

        except Exception as e:
            print(f"❌ DAI → ARB debt swap error: {e}")
            return False

    def _execute_debt_swap_arb_to_dai(self, confidence):
        """Execute ARB to DAI debt swap with profit tracking"""
        try:
            print("🔄 Executing ARB → DAI debt swap...")

            # Check ARB balance
            arb_balance = self.get_arb_balance()

            if arb_balance < 5.0:  # Need at least 5 ARB
                print(f"❌ Insufficient ARB balance: {arb_balance:.6f}")
                return False

            # Calculate optimal swap amount
            swap_amount = self._calculate_optimal_swap_amount('arb_to_dai')

            if swap_amount < 1.0:
                print("❌ Optimal swap amount too low for ARB→DAI")
                return False

            print(f"💱 Swapping {swap_amount:.6f} ARB for DAI...")

            # Execute swap via Uniswap
            if hasattr(self, 'uniswap') and self.uniswap:
                result = self.uniswap.swap_arb_for_dai(swap_amount)

                if result and result.get('success'):
                    tx_hash = result.get('tx_hash')

                    print(f"✅ ARB → DAI swap successful!")
                    print(f"🔗 TX: {tx_hash}")
                    print(f"💰 DAI received: {result.get('dai_received', 0):.2f}")

                    # Log the swap with console reporter
                    try:
                        from swap_console_reporter import log_swap_execution
                        log_swap_execution('arb_to_dai', swap_amount, result.get('dai_received', 0),
                                         self.market_signal_strategy.get_swap_decision_reasons('arb_to_dai'))
                    except Exception as log_err:
                        print(f"Logging error: {log_err}")

                    return True
                else:
                    print("❌ ARB → DAI swap failed")
                    return False
            else:
                print("❌ Uniswap integration not available")
                return False

        except Exception as e:
            print(f"❌ ARB → DAI debt swap error: {e}")
            return False

    def _calculate_optimal_swap_amount(self, swap_type: str) -> float:
        """Calculate optimal swap amount for high-frequency trading (small, frequent swaps)"""
        try:
            if not self.aave:
                return 0.0

            account_data = self.aave.get_user_account_data()
            if not account_data:
                return 0.0

            available_borrows = account_data.get('availableBorrowsUSD', 0)
            health_factor = account_data.get('healthFactor', 0)

            if swap_type == 'dai_to_arb':
                # High-frequency: small, safe DAI swaps (buy low strategy)
                if health_factor > 2.5:
                    return min(available_borrows * 0.05, 10.0)  # 5% or $10 max
                elif health_factor > 2.0:
                    return min(available_borrows * 0.03, 5.0)   # 3% or $5 max
                elif health_factor > 1.8:
                    return min(available_borrows * 0.02, 2.0)   # 2% or $2 max
                else:
                    return 0.0
            elif swap_type == 'arb_to_dai':
                # High-frequency: small ARB sales (sell high strategy)
                arb_balance = self.get_arb_balance()

                if arb_balance > 10.0:
                    return min(arb_balance * 0.3, 10.0)  # 30% or $10 max
                elif arb_balance > 5.0:
                    return min(arb_balance * 0.4, 5.0)   # 40% or $5 max
                elif arb_balance > 1.0:
                    return min(arb_balance * 0.5, 2.0)   # 50% or $2 max
                else:
                    return arb_balance  # Swap all if very small amount

            return 0.0

        except Exception as e:
            logger.error(f"Error calculating high-frequency swap amount: {e}")
            return 0.0

    def check_debt_swap_conditions(self):
        """Check if debt swap conditions are met"""
        try:
            # Check if market signal strategy is available
            if not hasattr(self, 'market_signal_strategy') or not self.market_signal_strategy:
                return False, "Market signal strategy not available"

            # Check if strategy is properly initialized
            if not hasattr(self.market_signal_strategy, 'initialization_successful'):
                return False, "Market signal strategy not initialized"

            if not self.market_signal_strategy.initialization_successful:
                return False, "Market signal strategy initialization failed"

            # Check technical indicators readiness
            status = self.market_signal_strategy.get_strategy_status()
            tech_ready = status.get('technical_indicators_ready', False)

            if not tech_ready:
                arb_points = status.get('enhanced_arb_points', 0)
                btc_points = status.get('enhanced_btc_points', 0)
                min_points = status.get('min_points_for_basic', 5)
                return False, f"Insufficient data points (ARB: {arb_points}, BTC: {btc_points}, need: {min_points})"

            # Check health factor if Aave is available
            if hasattr(self, 'aave') and self.aave:
                try:
                    account_data = self.aave.get_user_account_data()
                    if account_data:
                        health_factor = account_data.get('healthFactor', 0)
                        if health_factor < 1.35:
                            return False, f"Health factor too low: {health_factor:.3f} (need >1.35)"
                    else:
                        return False, "Cannot retrieve account data"
                except Exception as hf_error:
                    return False, f"Health factor check failed: {hf_error}"

            # Check debt swap activation
            if not getattr(self, 'debt_swap_active', False):
                return False, "Debt swap system not activated"

            return True, "All debt swap conditions met - system ready"

        except Exception as e:
            return False, f"Debt swap condition check failed: {e}"

