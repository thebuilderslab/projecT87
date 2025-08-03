
"""
Market Strategy Configuration
Environment variables and settings for the market signal strategy
"""

import os

class MarketStrategyConfig:
    """Configuration settings for market signal strategy"""
    
    # Market Signal Settings
    MARKET_SIGNAL_ENABLED = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
    
    # Technical Analysis Thresholds
    BTC_DROP_THRESHOLD = float(os.getenv('BTC_DROP_THRESHOLD', '0.01'))  # 1% BTC drop to trigger
    ARB_RSI_OVERSOLD = float(os.getenv('ARB_RSI_OVERSOLD', '30'))
    ARB_RSI_OVERBOUGHT = float(os.getenv('ARB_RSI_OVERBOUGHT', '70'))
    
    # Signal Confidence Thresholds
    DAI_TO_ARB_CONFIDENCE = float(os.getenv('DAI_TO_ARB_THRESHOLD', '0.7'))  # 70% confidence needed
    ARB_TO_DAI_CONFIDENCE = float(os.getenv('ARB_TO_DAI_THRESHOLD', '0.6'))  # 60% confidence needed
    
    # Operational Limits
    SIGNAL_COOLDOWN_SECONDS = int(os.getenv('SIGNAL_COOLDOWN', '1800'))  # 30 minutes between signals
    MAX_MARKET_OPERATION_AMOUNT = float(os.getenv('MAX_MARKET_OPERATION', '10.0'))  # Max $10 per operation
    MARKET_OPERATION_CAPACITY_RATIO = float(os.getenv('MARKET_CAPACITY_RATIO', '0.05'))  # 5% of available capacity
    
    # Health Factor Requirements
    MIN_HEALTH_FACTOR_FOR_MARKET_OPS = float(os.getenv('MIN_HF_MARKET_OPS', '2.0'))  # Minimum HF for market operations
    MIN_AVAILABLE_BORROWS_FOR_MARKET = float(os.getenv('MIN_BORROWS_MARKET', '5.0'))  # Minimum $5 available
    
    @classmethod
    def get_config_summary(cls):
        """Get configuration summary for logging"""
        return {
            'enabled': cls.MARKET_SIGNAL_ENABLED,
            'btc_threshold': cls.BTC_DROP_THRESHOLD,
            'signal_cooldown': cls.SIGNAL_COOLDOWN_SECONDS,
            'max_operation_amount': cls.MAX_MARKET_OPERATION_AMOUNT,
            'min_health_factor': cls.MIN_HEALTH_FACTOR_FOR_MARKET_OPS
        }
