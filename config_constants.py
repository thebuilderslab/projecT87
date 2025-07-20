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
