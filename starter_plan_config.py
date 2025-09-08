
#!/usr/bin/env python3
"""
Starter Plan Configuration
Optimized settings for budget-conscious operation
"""

# API Rate Limiting (Credits per day: ~833)
API_CALL_INTERVAL = 300  # 5 minutes between calls
MAX_API_CALLS_PER_HOUR = 12  # 288 calls per day max
MAX_API_CALLS_PER_DAY = 250  # Buffer below limit

# Debt Swap Operation Timing
DEBT_SWAP_COOLDOWN = 300  # 5 minutes between debt swaps
MARKET_ANALYSIS_INTERVAL = 600  # 10 minutes between market analysis

# Data Caching
CACHE_DURATION = 3600  # 1 hour cache for API data
EXTENDED_CACHE_DURATION = 7200  # 2 hours for budget preservation

# Monitoring Intervals
HEALTH_CHECK_INTERVAL = 300  # 5 minutes
BALANCE_CHECK_INTERVAL = 180  # 3 minutes
POSITION_MONITORING_INTERVAL = 240  # 4 minutes

# Conservative Thresholds
MIN_CONFIDENCE_THRESHOLD = 0.7  # Higher confidence required
MIN_SIGNAL_STRENGTH = 0.6  # Stronger signals only

# Risk Management
MAX_OPERATIONS_PER_HOUR = 6  # Conservative operation limit
EMERGENCY_STOP_ON_BUDGET_95_PERCENT = True

print("✅ Starter Plan Configuration Loaded")
print(f"   API calls limited to {MAX_API_CALLS_PER_DAY}/day")
print(f"   Debt swap cooldown: {DEBT_SWAP_COOLDOWN}s")
print(f"   Market analysis every: {MARKET_ANALYSIS_INTERVAL}s")
