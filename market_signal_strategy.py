
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
                # Check if we're using synthetic data
                analysis = self.get_market_analysis()
                if analysis and not analysis.get('error'):
                    # Check for synthetic data usage
                    using_synthetic = False
                    for key in ['btc_analysis', 'eth_analysis', 'arb_analysis']:
                        if key in analysis and analysis[key].get('source') == 'synthetic_fallback':
                            using_synthetic = True
                            break
                    
                    if using_synthetic:
                        logger.warning("🔄 Using synthetic market data - trading disabled for safety")
                        return False
                    
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
    
    def analyze_market_signals(self) -> Dict:
        """Analyze current market signals for trading decisions"""
        try:
            if self.initialized and self.enhanced_analyzer:
                # Get comprehensive market analysis
                analysis = self.enhanced_analyzer.get_market_summary()
                
                if analysis and not analysis.get('error'):
                    # Extract key signals
                    btc_analysis = analysis.get('btc_analysis', {})
                    eth_analysis = analysis.get('eth_analysis', {})
                    arb_analysis = analysis.get('arb_analysis', {})
                    
                    # Calculate overall signal strength
                    signal_strength = 0
                    signals_detected = []
                    
                    # BTC signal analysis
                    if btc_analysis.get('signal') == 'bullish':
                        signal_strength += btc_analysis.get('confidence', 0) * 0.4  # 40% weight
                        signals_detected.append(f"BTC bullish ({btc_analysis.get('confidence', 0):.2f})")
                    elif btc_analysis.get('signal') == 'bearish':
                        signal_strength -= btc_analysis.get('confidence', 0) * 0.4
                        signals_detected.append(f"BTC bearish ({btc_analysis.get('confidence', 0):.2f})")
                    
                    # ETH signal analysis
                    if eth_analysis.get('signal') == 'bullish':
                        signal_strength += eth_analysis.get('confidence', 0) * 0.3  # 30% weight
                        signals_detected.append(f"ETH bullish ({eth_analysis.get('confidence', 0):.2f})")
                    elif eth_analysis.get('signal') == 'bearish':
                        signal_strength -= eth_analysis.get('confidence', 0) * 0.3
                        signals_detected.append(f"ETH bearish ({eth_analysis.get('confidence', 0):.2f})")
                    
                    # ARB signal analysis
                    if arb_analysis.get('signal') == 'bullish':
                        signal_strength += arb_analysis.get('confidence', 0) * 0.3  # 30% weight
                        signals_detected.append(f"ARB bullish ({arb_analysis.get('confidence', 0):.2f})")
                    elif arb_analysis.get('signal') == 'bearish':
                        signal_strength -= arb_analysis.get('confidence', 0) * 0.3
                        signals_detected.append(f"ARB bearish ({arb_analysis.get('confidence', 0):.2f})")
                    
                    # Determine overall recommendation
                    if signal_strength > 0.6:
                        recommendation = "STRONG_BUY"
                        action = "dai_to_arb"
                    elif signal_strength > 0.3:
                        recommendation = "BUY"
                        action = "dai_to_arb"
                    elif signal_strength < -0.6:
                        recommendation = "STRONG_SELL"
                        action = "arb_to_dai"
                    elif signal_strength < -0.3:
                        recommendation = "SELL"
                        action = "arb_to_dai"
                    else:
                        recommendation = "HOLD"
                        action = "hold"
                    
                    return {
                        'signal_strength': signal_strength,
                        'recommendation': recommendation,
                        'action': action,
                        'signals_detected': signals_detected,
                        'market_sentiment': analysis.get('market_sentiment', 'neutral'),
                        'confidence_level': abs(signal_strength),
                        'timestamp': time.time(),
                        'status': 'success'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Market analysis failed',
                        'timestamp': time.time()
                    }
            else:
                return {
                    'status': 'fallback',
                    'message': 'Enhanced market analysis not available',
                    'recommendation': 'HOLD',
                    'action': 'hold',
                    'timestamp': time.time()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing market signals: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'recommendation': 'HOLD',
                'action': 'hold',
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
