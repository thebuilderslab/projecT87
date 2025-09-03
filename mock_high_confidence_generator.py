
#!/usr/bin/env python3
"""
Mock High Confidence Signal Generator
Generates guaranteed high-confidence market signals for debt swap testing
"""

import time
import random
from typing import Dict

class MockHighConfidenceGenerator:
    """Generates mock market data with guaranteed high confidence signals"""
    
    def __init__(self):
        self.signal_type = 'bullish_for_dai_to_arb'  # Default to DAI→ARB trigger
        self.base_confidence = 0.65  # High confidence base
    
    def generate_high_confidence_arb_analysis(self) -> Dict:
        """Generate ARB analysis that triggers DAI→ARB with high confidence"""
        return {
            'price': 0.682 + random.uniform(-0.01, 0.01),  # Mock ARB price with slight variation
            'change_24h': random.uniform(-2.5, -1.0),  # Bearish 24h change (buy low signal)
            'signal': 'bearish',  # Bearish signal for buy low strategy
            'rsi': random.uniform(35, 42),  # Oversold RSI (buy opportunity)
            'pattern': 'moderate_bearish',  # Bearish pattern for buying opportunity
            'confidence': self.base_confidence + random.uniform(0, 0.15),  # 65-80% confidence
            'price_change_5min': random.uniform(-0.8, -0.4),  # Strong 5min decline (buy signal)
            'macd_line': -0.003,  # Bearish MACD for buy signal
            'macd_signal': -0.001,  # MACD signal
            'macd_histogram': -0.002,  # Negative histogram confirms bearish crossover
            'volume': random.randint(800000, 1200000)
        }
    
    def generate_high_confidence_btc_analysis(self) -> Dict:
        """Generate BTC analysis supporting the ARB signal"""
        return {
            'price': random.uniform(95000, 97000),
            'change_24h': random.uniform(-1.2, -0.4),  # Mild bearish pressure supporting ARB buy
            'signal': 'bearish',
            'pattern': 'mild_bearish',
            'confidence': random.uniform(0.5, 0.7)
        }
    
    def generate_guaranteed_market_summary(self) -> Dict:
        """Generate market summary with guaranteed high confidence for DAI→ARB"""
        return {
            'btc_analysis': self.generate_high_confidence_btc_analysis(),
            'arb_analysis': self.generate_high_confidence_arb_analysis(),
            'eth_analysis': {
                'price': random.uniform(3200, 3400),
                'change_24h': random.uniform(-1.0, 0.5),
                'signal': 'neutral',
                'pattern': 'consolidation',
                'confidence': 0.5
            },
            'market_sentiment': 'mixed_with_arb_opportunity',
            'timestamp': time.time(),
            'source': 'mock_high_confidence_generator',
            'guaranteed_confidence': True
        }

# Global instance for use in tests
mock_generator = MockHighConfidenceGenerator()
