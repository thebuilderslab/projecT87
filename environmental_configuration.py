#!/usr/bin/env python3
"""
Environmental Configuration for Optimized Market Signal Strategy
Less conservative parameters for improved opportunity capture
"""

import os

# High-Frequency Trading Configuration (corrected logic)
BTC_DROP_THRESHOLD = float(os.getenv('BTC_DROP_THRESHOLD', '0.003'))  # 0.3% BTC drop for high-frequency
ARB_RSI_OVERSOLD = float(os.getenv('ARB_RSI_OVERSOLD', '45'))  # RSI below 45 = oversold (high-frequency)
ARB_RSI_OVERBOUGHT = float(os.getenv('ARB_RSI_OVERBOUGHT', '65'))  # RSI above 65 = overbought (high-frequency)
DAI_TO_ARB_THRESHOLD = float(os.getenv('DAI_TO_ARB_THRESHOLD', '0.4'))  # 40% confidence for DAI→ARB (buy low)
ARB_TO_DAI_THRESHOLD = float(os.getenv('ARB_TO_DAI_THRESHOLD', '0.4'))  # 40% confidence for ARB→DAI (sell high)

# High-Frequency Trading Operation Parameters
OPERATION_COOLDOWN = int(os.getenv('OPERATION_COOLDOWN', '30'))  # 30 seconds between operations
MIN_SWAP_AMOUNT = float(os.getenv('MIN_SWAP_AMOUNT', '1.0'))  # $1 minimum swap
MAX_SWAP_AMOUNT = float(os.getenv('MAX_SWAP_AMOUNT', '10.0'))  # $10 maximum swap
TARGET_HEALTH_FACTOR = float(os.getenv('TARGET_HEALTH_FACTOR', '2.0'))  # Conservative health factor

# MACD PARAMETERS
MACD_FAST_PERIOD = int(os.getenv('MACD_FAST_PERIOD', '12'))
MACD_SLOW_PERIOD = int(os.getenv('MACD_SLOW_PERIOD', '26'))
MACD_SIGNAL_PERIOD = int(os.getenv('MACD_SIGNAL_PERIOD', '9'))

# OPTIMIZED STRATEGY SETTINGS
PATTERN_CONFIRMATION_REQUIRED = os.getenv('PATTERN_CONFIRMATION_REQUIRED', 'false').lower() == 'true'
MULTI_VALIDATION_REQUIRED = os.getenv('MULTI_VALIDATION_REQUIRED', 'false').lower() == 'true'
MINIMUM_CONFIDENCE_THRESHOLD = float(os.getenv('MINIMUM_CONFIDENCE_THRESHOLD', '0.5'))  # 50%

print("📊 HIGH-FREQUENCY TRADING PARAMETERS LOADED:")
print(f"   BTC Drop Threshold: {BTC_DROP_THRESHOLD*100:.1f}%")
print(f"   ARB RSI Oversold: {ARB_RSI_OVERSOLD}")
print(f"   DAI→ARB Confidence: {DAI_TO_ARB_THRESHOLD*100:.0f}%")
print(f"   Operation Cooldown: {OPERATION_COOLDOWN}s")
print(f"   Min/Max Swap Amount: ${MIN_SWAP_AMOUNT} - ${MAX_SWAP_AMOUNT}")
print(f"   Target Health Factor: {TARGET_HEALTH_FACTOR}")
print("✅ System configured for high-frequency, small-scale trading with corrected logic.")