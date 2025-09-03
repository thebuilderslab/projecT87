
#!/usr/bin/env python3
"""
Environmental Configuration for Optimized Market Signal Strategy
Less conservative parameters for improved opportunity capture
"""

import os

# OPTIMIZED MARKET SIGNAL PARAMETERS (Less Conservative)
BTC_DROP_THRESHOLD = float(os.getenv('BTC_DROP_THRESHOLD', '0.005'))  # 0.5% (was 1%)
BTC_RECOVERY_THRESHOLD = float(os.getenv('BTC_RECOVERY_THRESHOLD', '0.015'))  # 1.5%
BTC_VOLATILITY_THRESHOLD = float(os.getenv('BTC_VOLATILITY_THRESHOLD', '0.03'))  # 3%

# OPTIMIZED ARB TECHNICAL PARAMETERS
ARB_RSI_OVERSOLD = float(os.getenv('ARB_RSI_OVERSOLD', '40'))  # 40 (was 35)
ARB_RSI_OVERBOUGHT = float(os.getenv('ARB_RSI_OVERBOUGHT', '70'))  # 70
ARB_MOMENTUM_THRESHOLD = float(os.getenv('ARB_MOMENTUM_THRESHOLD', '0.02'))  # 2%

# OPTIMIZED CONFIDENCE THRESHOLDS
DAI_TO_ARB_THRESHOLD = float(os.getenv('DAI_TO_ARB_THRESHOLD', '0.5'))  # 50% (was 70%)
ARB_TO_DAI_THRESHOLD = float(os.getenv('ARB_TO_DAI_THRESHOLD', '0.6'))  # 60%

# MACD PARAMETERS
MACD_FAST_PERIOD = int(os.getenv('MACD_FAST_PERIOD', '12'))
MACD_SLOW_PERIOD = int(os.getenv('MACD_SLOW_PERIOD', '26'))
MACD_SIGNAL_PERIOD = int(os.getenv('MACD_SIGNAL_PERIOD', '9'))

# OPTIMIZED STRATEGY SETTINGS
PATTERN_CONFIRMATION_REQUIRED = os.getenv('PATTERN_CONFIRMATION_REQUIRED', 'false').lower() == 'true'
MULTI_VALIDATION_REQUIRED = os.getenv('MULTI_VALIDATION_REQUIRED', 'false').lower() == 'true'
MINIMUM_CONFIDENCE_THRESHOLD = float(os.getenv('MINIMUM_CONFIDENCE_THRESHOLD', '0.5'))  # 50%

print("📊 OPTIMIZED MARKET PARAMETERS LOADED:")
print(f"   BTC Drop Threshold: {BTC_DROP_THRESHOLD*100:.1f}%")
print(f"   ARB RSI Oversold: {ARB_RSI_OVERSOLD}")
print(f"   DAI→ARB Confidence: {DAI_TO_ARB_THRESHOLD*100:.0f}%")
print("✅ Less conservative parameters for improved opportunity capture")
