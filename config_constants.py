
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
