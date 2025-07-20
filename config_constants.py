# Configuration Constants for Arbitrum Agent
MIN_ETH_FOR_OPERATIONS = 0.01  # Minimum ETH needed for operations
MIN_ETH_FOR_GAS_BUFFER = 0.005  # Minimum ETH buffer for gas fees
DEFAULT_GAS_LIMIT = 300000
DEFAULT_GAS_PRICE_GWEI = 0.1
HEALTH_FACTOR_THRESHOLD = 1.5
TARGET_HEALTH_FACTOR = 2.5
MAX_SLIPPAGE_PERCENT = 2.0
OPERATION_COOLDOWN_SECONDS = 60
"""
Configuration Constants for Arbitrum Agent
"""

# Minimum ETH requirements for operations
MIN_ETH_FOR_OPERATIONS = 0.001  # 0.001 ETH minimum for gas operations
MIN_ETH_FOR_GAS_BUFFER = 0.0005  # 0.0005 ETH buffer for gas fees

# Health factor thresholds
MIN_HEALTH_FACTOR = 1.05  # Emergency threshold
TARGET_HEALTH_FACTOR = 1.25  # Conservative target

# Operational limits
MAX_CONSECUTIVE_FAILURES = 3
OPERATION_COOLDOWN_SECONDS = 60

# Gas optimization settings
DEFAULT_GAS_MULTIPLIER = 1.2
EMERGENCY_GAS_MULTIPLIER = 2.0

# Borrowing parameters
MIN_BORROW_AMOUNT_USD = 0.5
MAX_BORROW_AMOUNT_USD = 1000.0
GROWTH_TRIGGER_THRESHOLD_USD = 12.0

# RPC settings
RPC_TIMEOUT_SECONDS = 30
MAX_RPC_RETRIES = 3

# Price data settings
PRICE_CACHE_DURATION = 300  # 5 minutes
"""
Configuration Constants for Arbitrum DeFi Agent
Centralized configuration management
"""

# Minimum ETH requirements for operations
MIN_ETH_FOR_OPERATIONS = 0.002  # Minimum ETH for gas operations
MIN_ETH_FOR_GAS_BUFFER = 0.001  # Additional buffer for safety

# Health factor thresholds
MIN_HEALTH_FACTOR = 1.05  # Emergency threshold
TARGET_HEALTH_FACTOR = 1.25  # Conservative target
SAFE_HEALTH_FACTOR = 2.0  # Safe borrowing threshold

# Borrowing configuration
MAX_BORROW_PERCENTAGE = 0.8  # Max 80% of available capacity
MIN_BORROW_AMOUNT = 0.5  # Minimum borrow amount in USD
MAX_BORROW_AMOUNT = 100.0  # Maximum single borrow amount in USD

# Autonomous trigger configuration
GROWTH_TRIGGER_THRESHOLD = 12.0  # USD growth to trigger operations
MANUAL_OVERRIDE_THRESHOLD = 1.0  # Lower threshold for testing
COOLDOWN_PERIOD = 60  # Seconds between operations

# Gas configuration
DEFAULT_GAS_LIMIT = 200000
DEFAULT_GAS_PRICE = 100000000  # 0.1 gwei in wei
GAS_PRICE_MULTIPLIER = 1.2  # 20% premium for reliability

# Network configuration
ARBITRUM_MAINNET_CHAIN_ID = 42161
ARBITRUM_SEPOLIA_CHAIN_ID = 421614

# Token allocation for swaps (percentages)
WBTC_ALLOCATION = 0.30  # 30% to WBTC
WETH_ALLOCATION = 0.20  # 20% to WETH
DAI_ALLOCATION = 0.10   # 10% to DAI
RESERVE_ALLOCATION = 0.40  # 40% kept as reserves

# Validation thresholds
MIN_COLLATERAL_USD = 10.0  # Minimum collateral for operations
MAX_DEBT_RATIO = 0.75  # Maximum debt to collateral ratio

# API configuration
REQUEST_TIMEOUT = 10  # Seconds for external API calls
MAX_RETRIES = 3  # Maximum retry attempts
RETRY_DELAY = 2  # Seconds between retries

print("✅ Configuration constants loaded successfully")
