
# Configuration constants for Arbitrum DeFi Agent
# This module provides centralized configuration management

# Minimum ETH requirements for operations
MIN_ETH_FOR_OPERATIONS = 0.001  # Minimum ETH needed for gas fees
MIN_ETH_FOR_GAS_BUFFER = 0.0005  # Buffer amount for gas fee fluctuations

# Health factor thresholds
MIN_HEALTH_FACTOR = 1.1  # Minimum safe health factor
TARGET_HEALTH_FACTOR = 1.5  # Target health factor for operations
EMERGENCY_HEALTH_FACTOR = 1.05  # Emergency threshold

# Operation limits
MAX_BORROW_PERCENTAGE = 0.8  # Maximum percentage of available borrows to use
MAX_RETRY_ATTEMPTS = 3  # Maximum retry attempts for failed operations

# Gas price settings
DEFAULT_GAS_PRICE_GWEI = 0.1  # Default gas price in gwei
GAS_PRICE_MULTIPLIER = 1.2  # Multiplier for gas price to ensure inclusion

# Cooldown periods (in seconds)
OPERATION_COOLDOWN = 60  # Cooldown between operations
EMERGENCY_COOLDOWN = 300  # Extended cooldown after emergencies

# API settings
DEFAULT_TIMEOUT = 30  # Default timeout for API calls
MAX_RETRIES = 3  # Maximum retries for API calls

print("✅ Config module loaded successfully")
