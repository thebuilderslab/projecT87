
# Configuration constants for Arbitrum DeFi Agent
# This module provides centralized configuration management

# Minimum ETH requirements for operations
MIN_ETH_FOR_OPERATIONS = 0.001  # Minimum ETH needed for gas fees
MIN_ETH_FOR_GAS_BUFFER = 0.0005  # Buffer amount for gas fee fluctuations

# Health factor thresholds - Universal minimum: 1.5
MIN_HEALTH_FACTOR = 1.5  # Minimum safe health factor (universal threshold)
TARGET_HEALTH_FACTOR = 1.5  # Target health factor for operations
EMERGENCY_HEALTH_FACTOR = 1.5  # Emergency threshold (universal minimum)

# Autonomous trigger thresholds
COLLATERAL_GROWTH_TRIGGER_USD = 13.0  # USD growth trigger for autonomous sequence
MAIN_TRIGGER_THRESHOLD = 13.0  # Main trigger threshold (same as above for compatibility)

# Operation limits
MAX_BORROW_PERCENTAGE = 0.8  # Maximum percentage of available borrows to use
MAX_RETRY_ATTEMPTS = 3  # Maximum retry attempts for failed operations

# Gas price settings
DEFAULT_GAS_PRICE_GWEI = 0.1  # Default gas price in gwei
GAS_PRICE_MULTIPLIER = 1.2  # Multiplier for gas price to ensure inclusion

# ETH balance thresholds for strategy execution
MIN_ETH_GAS_THRESHOLD = 0.005  # Minimum ETH balance required for gas operations
                               # This covers multiple transactions to prevent running out of gas

# Cooldown periods (in seconds)
OPERATION_COOLDOWN = 60  # Cooldown between operations
EMERGENCY_COOLDOWN = 300  # Extended cooldown after emergencies

# API settings
DEFAULT_TIMEOUT = 30  # Default timeout for API calls
MAX_RETRIES = 3  # Maximum retries for API calls

print("✅ Config module loaded successfully")
