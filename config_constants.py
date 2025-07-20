
#!/usr/bin/env python3
"""
Centralized Configuration Constants
Shared constants used across the DeFi agent system
"""

# ETH Gas and Balance Requirements
MIN_ETH_FOR_OPERATIONS = 0.00083545  # Minimum ETH required for gas operations
MIN_ETH_FOR_GAS_BUFFER = 0.00083545  # Alias for consistency with existing code

# USDC Requirements
MIN_USDC_FOR_OPERATIONS = 0.1  # Minimum USDC for operations

# Gas Estimation Constants
GAS_PRICE_BUFFER_MULTIPLIER = 1.1  # 10% buffer on gas prices
GAS_LIMIT_BUFFER_MULTIPLIER = 1.2  # 20% buffer on gas limits

# Health Factor Thresholds
MIN_HEALTH_FACTOR_FOR_OPERATIONS = 1.1
SAFE_HEALTH_FACTOR_THRESHOLD = 1.25
EMERGENCY_HEALTH_FACTOR_THRESHOLD = 1.05

# Borrowing Limits
MAX_BORROW_PERCENTAGE = 0.8  # 80% of available capacity
MIN_BORROW_AMOUNT_USD = 0.5
MAX_BORROW_AMOUNT_USD = 200.0

# Cooldown Settings
OPERATION_COOLDOWN_SECONDS = 60
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

print("✅ Config constants loaded successfully")
"""
Configuration Constants for Arbitrum Agent
"""

# Gas and ETH requirements
MIN_ETH_FOR_OPERATIONS = 0.005  # Minimum ETH needed for operations (0.005 ETH)
MIN_ETH_FOR_GAS_BUFFER = 0.002  # Additional ETH buffer for gas (0.002 ETH)

# Trading parameters
DEFAULT_SLIPPAGE_TOLERANCE = 0.005  # 0.5% slippage tolerance
MAX_GAS_PRICE_GWEI = 50  # Maximum gas price in Gwei

# Health factor thresholds
MIN_HEALTH_FACTOR = 1.1  # Minimum health factor before liquidation risk
TARGET_HEALTH_FACTOR = 2.0  # Target health factor for safe operations
EMERGENCY_HEALTH_FACTOR = 1.05  # Emergency threshold for immediate action

# Protocol addresses and constants
ARBITRUM_MAINNET_CHAIN_ID = 42161
ARBITRUM_SEPOLIA_CHAIN_ID = 421614

# Operation cooldowns (in seconds)
DEFAULT_OPERATION_COOLDOWN = 60  # 1 minute between operations
EMERGENCY_COOLDOWN = 30  # 30 seconds for emergency operations

# Retry settings
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2

# Validation thresholds
MIN_USD_AMOUNT = 0.01  # Minimum USD amount for operations
MAX_USD_AMOUNT = 10000  # Maximum USD amount for single operation
