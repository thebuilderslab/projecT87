
"""
Configuration constants for the DeFi agent system
"""

# Minimum ETH requirements for operations
MIN_ETH_FOR_OPERATIONS = 0.001  # Minimum ETH needed for any operation
MIN_ETH_FOR_GAS_BUFFER = 0.0005  # Additional ETH buffer for gas

# Gas price constants
DEFAULT_GAS_PRICE = 100000000  # 0.1 gwei in wei
MAX_GAS_PRICE = 1000000000     # 1 gwei in wei

# Health factor thresholds
MIN_HEALTH_FACTOR = 1.5        # Minimum safe health factor
TARGET_HEALTH_FACTOR = 2.0     # Target health factor for operations

# Operation limits
MAX_BORROW_AMOUNT_USD = 50.0   # Maximum borrow amount per operation
MIN_BORROW_AMOUNT_USD = 0.5    # Minimum borrow amount per operation

# Cooldown periods (in seconds)
OPERATION_COOLDOWN = 60        # Standard operation cooldown
EMERGENCY_COOLDOWN = 300       # Emergency operation cooldown

print("✅ Configuration constants loaded successfully")
