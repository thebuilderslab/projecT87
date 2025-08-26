
#!/usr/bin/env python3
"""
Market Signal Strategy with CoinMarketCap Integration
Enhanced market analysis for debt swap decisions
"""

import os
import time
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketSignalStrategy:
    """Market signal strategy for autonomous trading decisions"""
    
    def __init__(self, agent):
        self.agent = agent
        self.initialized = False
        self.market_signal_enabled = True  # Enable market signal functionality by default
        
        try:
            # Try to import and initialize enhanced analyzer
            from enhanced_market_analyzer import EnhancedMarketAnalyzer, EnhancedMarketSignalStrategy
            
            self.enhanced_strategy = EnhancedMarketSignalStrategy(agent)
            self.enhanced_analyzer = self.enhanced_strategy.analyzer if self.enhanced_strategy.initialized else None
            self.initialized = self.enhanced_strategy.initialized
            
            if self.initialized:
                logger.info("✅ Market Signal Strategy initialized with CoinMarketCap API")
            else:
                logger.warning("⚠️ Enhanced strategy failed, using fallback mode")
                
        except Exception as e:
            logger.error(f"Failed to initialize enhanced strategy: {e}")
            self.enhanced_strategy = None
            self.enhanced_analyzer = None
            self.initialized = False
    
    def should_execute_trade(self) -> bool:
        """Determine if a trade should be executed"""
        try:
            if self.initialized and self.enhanced_strategy:
                return self.enhanced_strategy.should_execute_trade()
            else:
                # Fallback mode - very conservative
                logger.info("Using fallback trading logic (no market signals)")
                return False
                
        except Exception as e:
            logger.error(f"Error in trade decision: {e}")
            return False
    
    def get_market_analysis(self) -> Dict:
        """Get current market analysis"""
        try:
            if self.initialized and self.enhanced_analyzer:
                return self.enhanced_analyzer.get_market_summary()
            else:
                return {
                    'status': 'fallback_mode',
                    'timestamp': time.time(),
                    'message': 'Enhanced market analysis not available'
                }
                
        except Exception as e:
            logger.error(f"Error getting market analysis: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }
    
    def get_strategy_status(self) -> Dict:
        """Get strategy status"""
        return {
            'initialized': self.initialized,
            'enhanced_mode': bool(self.enhanced_strategy and self.enhanced_strategy.initialized),
            'coin_api_present': bool(os.getenv('COIN_API')),
            'coinmarketcap_api_present': bool(os.getenv('COINMARKETCAP_API_KEY')),
            'strategy_type': 'enhanced_coin_api' if self.initialized else 'fallback',
            'last_update': time.time()
        }

# Backward compatibility
def create_market_signal_strategy(agent):
    """Factory function to create market signal strategy"""
    return MarketSignalStrategy(agent)
