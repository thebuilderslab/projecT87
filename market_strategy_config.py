
#!/usr/bin/env python3
"""
Market Strategy Configuration
Enhanced configuration for BTC/ARB correlation-based debt swapping
"""

import os
from datetime import datetime

# Market Signal Strategy Configuration
MARKET_SIGNAL_ENABLED = os.getenv('MARKET_SIGNAL_ENABLED', 'true').lower() == 'true'

# BTC Market Conditions (Primary Signal)
BTC_DROP_THRESHOLD = float(os.getenv('BTC_DROP_THRESHOLD', '0.015'))  # 1.5% drop threshold
BTC_RECOVERY_THRESHOLD = float(os.getenv('BTC_RECOVERY_THRESHOLD', '0.02'))  # 2% recovery threshold
BTC_VOLATILITY_THRESHOLD = float(os.getenv('BTC_VOLATILITY_THRESHOLD', '0.05'))  # 5% volatility

# ARB Technical Analysis Parameters
ARB_RSI_OVERSOLD = float(os.getenv('ARB_RSI_OVERSOLD', '25'))  # More aggressive oversold
ARB_RSI_OVERBOUGHT = float(os.getenv('ARB_RSI_OVERBOUGHT', '75'))  # More aggressive overbought
ARB_MOMENTUM_THRESHOLD = float(os.getenv('ARB_MOMENTUM_THRESHOLD', '0.03'))  # 3% momentum

# Confidence Thresholds for Strategy Execution
DAI_TO_ARB_CONFIDENCE = float(os.getenv('DAI_TO_ARB_THRESHOLD', '0.65'))  # 65% confidence for DAI→ARB
ARB_TO_DAI_CONFIDENCE = float(os.getenv('ARB_TO_DAI_THRESHOLD', '0.60'))  # 60% confidence for ARB→DAI

# Operation Limits and Safety
MAX_MARKET_OPERATION_AMOUNT = float(os.getenv('MAX_MARKET_OPERATION_AMOUNT', '8.0'))  # $8 max per operation
MIN_OPERATION_AMOUNT = float(os.getenv('MIN_OPERATION_AMOUNT', '1.0'))  # $1 minimum
MARKET_OPERATION_PERCENTAGE = float(os.getenv('MARKET_OPERATION_PERCENTAGE', '0.04'))  # 4% of available

# Health Factor Requirements for Market Operations
MIN_HEALTH_FACTOR_FOR_MARKET_OPS = float(os.getenv('MIN_HEALTH_FACTOR_FOR_MARKET_OPS', '2.2'))  # Higher safety
TARGET_HEALTH_FACTOR_POST_OP = float(os.getenv('TARGET_HEALTH_FACTOR_POST_OP', '2.0'))  # Target after operation

# Timing and Cooldown Configuration
SIGNAL_COOLDOWN = int(os.getenv('SIGNAL_COOLDOWN', '1800'))  # 30 minutes between signals
MARKET_ANALYSIS_INTERVAL = int(os.getenv('MARKET_ANALYSIS_INTERVAL', '3600'))  # 1 hour analysis cycle
OPERATION_RETRY_DELAY = int(os.getenv('OPERATION_RETRY_DELAY', '300'))  # 5 minutes retry delay

# API Configuration
COINMARKETCAP_RATE_LIMIT = int(os.getenv('COINMARKETCAP_RATE_LIMIT', '100'))  # Calls per day
API_TIMEOUT_SECONDS = int(os.getenv('API_TIMEOUT_SECONDS', '10'))  # API timeout

# Market Correlation Analysis
BTC_ARB_CORRELATION_WINDOW = int(os.getenv('BTC_ARB_CORRELATION_WINDOW', '24'))  # Hours to analyze
CORRELATION_STRENGTH_THRESHOLD = float(os.getenv('CORRELATION_STRENGTH_THRESHOLD', '0.3'))  # Min correlation

# Risk Management
MAX_DAILY_OPERATIONS = int(os.getenv('MAX_DAILY_OPERATIONS', '6'))  # Max 6 operations per day
MAX_WEEKLY_VOLUME = float(os.getenv('MAX_WEEKLY_VOLUME', '40.0'))  # Max $40 weekly volume
POSITION_SIZE_LIMIT = float(os.getenv('POSITION_SIZE_LIMIT', '0.15'))  # 15% of total position

# Emergency Conditions
EMERGENCY_BTC_DROP = float(os.getenv('EMERGENCY_BTC_DROP', '0.10'))  # 10% emergency drop
EMERGENCY_ARB_DROP = float(os.getenv('EMERGENCY_ARB_DROP', '0.15'))  # 15% emergency ARB drop
EMERGENCY_HALT_DURATION = int(os.getenv('EMERGENCY_HALT_DURATION', '7200'))  # 2 hours halt

def get_market_strategy_status():
    """Get current market strategy configuration status"""
    return {
        'enabled': MARKET_SIGNAL_ENABLED,
        'btc_drop_threshold': BTC_DROP_THRESHOLD,
        'arb_rsi_oversold': ARB_RSI_OVERSOLD,
        'dai_to_arb_confidence': DAI_TO_ARB_CONFIDENCE,
        'max_operation_amount': MAX_MARKET_OPERATION_AMOUNT,
        'min_health_factor': MIN_HEALTH_FACTOR_FOR_MARKET_OPS,
        'signal_cooldown_minutes': SIGNAL_COOLDOWN / 60,
        'analysis_interval_hours': MARKET_ANALYSIS_INTERVAL / 3600,
        'max_daily_operations': MAX_DAILY_OPERATIONS,
        'last_updated': datetime.now().isoformat()
    }

def validate_configuration():
    """Validate market strategy configuration"""
    issues = []
    
    # Validate thresholds
    if BTC_DROP_THRESHOLD <= 0 or BTC_DROP_THRESHOLD > 0.2:
        issues.append(f"BTC drop threshold {BTC_DROP_THRESHOLD} outside safe range (0-0.2)")
    
    if ARB_RSI_OVERSOLD < 10 or ARB_RSI_OVERSOLD > 40:
        issues.append(f"ARB RSI oversold {ARB_RSI_OVERSOLD} outside typical range (10-40)")
    
    if DAI_TO_ARB_CONFIDENCE < 0.5 or DAI_TO_ARB_CONFIDENCE > 0.95:
        issues.append(f"DAI→ARB confidence {DAI_TO_ARB_CONFIDENCE} outside safe range (0.5-0.95)")
    
    if MIN_HEALTH_FACTOR_FOR_MARKET_OPS < 1.5:
        issues.append(f"Minimum health factor {MIN_HEALTH_FACTOR_FOR_MARKET_OPS} too low (min 1.5)")
    
    if MAX_MARKET_OPERATION_AMOUNT > 20:
        issues.append(f"Maximum operation amount ${MAX_MARKET_OPERATION_AMOUNT} too high (max $20)")
    
    # Validate timing
    if SIGNAL_COOLDOWN < 600:  # 10 minutes minimum
        issues.append(f"Signal cooldown {SIGNAL_COOLDOWN}s too short (min 600s)")
    
    return issues

def get_optimized_parameters():
    """Get optimized parameters based on current market conditions"""
    # This would analyze recent market data and suggest optimal parameters
    # For now, return conservative defaults
    return {
        'btc_drop_threshold': 0.015,  # 1.5% for balanced sensitivity
        'arb_rsi_oversold': 25,       # Aggressive but safe
        'dai_to_arb_confidence': 0.65, # Conservative confidence requirement
        'max_operation_amount': 8.0,   # Moderate position sizing
        'min_health_factor': 2.2,     # High safety margin
        'signal_cooldown': 1800,      # 30 minutes for market efficiency
        'reasoning': "Conservative parameters optimized for network approval and risk management"
    }

if __name__ == "__main__":
    print("📊 MARKET STRATEGY CONFIGURATION")
    print("=" * 50)
    
    # Display current configuration
    status = get_market_strategy_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # Validate configuration
    print(f"\n🔍 CONFIGURATION VALIDATION")
    issues = validate_configuration()
    if issues:
        print("⚠️ Configuration Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Configuration Valid")
    
    # Show optimized parameters
    print(f"\n🎯 OPTIMIZED PARAMETERS")
    optimized = get_optimized_parameters()
    for key, value in optimized.items():
        print(f"{key}: {value}")
