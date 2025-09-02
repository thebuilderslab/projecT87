#!/usr/bin/env python3
"""
Market Signal Strategy with CoinMarketCap Integration
Enhanced market analysis for debt swap decisions
"""

import os
import time
import logging
from typing import Dict, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketSignalStrategy:
    """Market signal strategy for autonomous trading decisions"""

    def __init__(self, agent):
        self.agent = agent

        # Market signal enablement (set by environment variable)
        self.market_signal_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
        
        # Enhanced API rate limiting
        self.last_api_call = 0
        self.api_call_interval = 60  # Minimum 60 seconds between API calls
        self.api_call_count = 0
        self.max_api_calls_per_hour = 100  # Conservative limit

        # Debt reduction optimization parameters
        self.arb_depreciation_threshold = -0.02  # 2% drop triggers debt reduction
        self.debt_reduction_cooldown = 300  # 5 minutes between debt reduction attempts
        self.last_debt_reduction = 0

        # Enhanced confidence thresholds with market conditions
        self.base_dai_to_arb_threshold = 0.92  # 92% base confidence
        self.base_arb_to_dai_threshold = 0.88  # 88% base confidence
        self.market_volatility_modifier = 0.0  # Adjusts thresholds based on volatility

        # ARB price tracking for debt reduction
        self.arb_price_history = []
        self.arb_entry_prices = {}  # Track entry prices for debt swaps

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
                    synthetic_count = 0

                    for key in ['btc_analysis', 'eth_analysis', 'arb_analysis', 'dai_analysis']:
                        if key in analysis:
                            if analysis[key].get('source') == 'synthetic_fallback' or analysis[key].get('synthetic'):
                                using_synthetic = True
                                synthetic_count += 1

                    # Allow limited trading if only some data is synthetic
                    if synthetic_count >= 3:  # If 3+ sources are synthetic, disable trading
                        logger.warning("🔄 Too much synthetic market data - trading disabled for safety")
                        return False
                    elif using_synthetic:
                        logger.info("🔄 Some synthetic data detected - using conservative trading")
                        # Still allow trading but be more conservative
                        return self.enhanced_strategy.should_execute_trade() if hasattr(self.enhanced_strategy, 'should_execute_trade') else False

                return self.enhanced_strategy.should_execute_trade() if hasattr(self.enhanced_strategy, 'should_execute_trade') else False
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

    def detect_bearish_reversal_patterns(self, price_data) -> List[str]:
        """Detect bearish reversal patterns indicating potential trend change"""
        patterns_detected = []
        
        try:
            if not price_data or len(price_data) < 20:
                return patterns_detected
            
            # Convert to price list for analysis
            prices = [float(p.get('price', 0)) for p in price_data[-20:]]
            if not prices or all(p == 0 for p in prices):
                return patterns_detected
            
            # Head and Shoulders Pattern
            if self._detect_head_and_shoulders(prices):
                patterns_detected.append("Head and Shoulders")
            
            # Double Top Pattern
            if self._detect_double_top(prices):
                patterns_detected.append("Double Top")
            
            # Triple Top Pattern
            if self._detect_triple_top(prices):
                patterns_detected.append("Triple Top")
            
            # Rounding Top Pattern
            if self._detect_rounding_top(prices):
                patterns_detected.append("Rounding Top")
                
        except Exception as e:
            logger.error(f"Error detecting bearish reversal patterns: {e}")
            
        return patterns_detected
    
    def detect_bearish_continuation_patterns(self, price_data) -> List[str]:
        """Detect bearish continuation patterns indicating downtrend continuation"""
        patterns_detected = []
        
        try:
            if not price_data or len(price_data) < 15:
                return patterns_detected
            
            prices = [float(p.get('price', 0)) for p in price_data[-15:]]
            if not prices or all(p == 0 for p in prices):
                return patterns_detected
            
            # Bearish Flag Pattern
            if self._detect_bearish_flag(prices):
                patterns_detected.append("Bearish Flag")
            
            # Bearish Pennant Pattern
            if self._detect_bearish_pennant(prices):
                patterns_detected.append("Bearish Pennant")
            
            # Falling Wedge Pattern
            if self._detect_falling_wedge(prices):
                patterns_detected.append("Falling Wedge")
            
            # Descending Triangle Pattern
            if self._detect_descending_triangle(prices):
                patterns_detected.append("Descending Triangle")
                
        except Exception as e:
            logger.error(f"Error detecting bearish continuation patterns: {e}")
            
        return patterns_detected
    
    def _detect_head_and_shoulders(self, prices) -> bool:
        """Detect Head and Shoulders pattern"""
        if len(prices) < 15:
            return False
        
        # Find potential peaks
        peaks = []
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                peaks.append((i, prices[i]))
        
        if len(peaks) < 3:
            return False
        
        # Check if we have a head and shoulders formation
        # Head should be higher than both shoulders
        for i in range(len(peaks) - 2):
            left_shoulder = peaks[i][1]
            head = peaks[i + 1][1]
            right_shoulder = peaks[i + 2][1]
            
            if (head > left_shoulder and head > right_shoulder and
                abs(left_shoulder - right_shoulder) / max(left_shoulder, right_shoulder) < 0.05):
                return True
        
        return False
    
    def _detect_double_top(self, prices) -> bool:
        """Detect Double Top pattern"""
        if len(prices) < 10:
            return False
        
        peaks = []
        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                peaks.append((i, prices[i]))
        
        if len(peaks) < 2:
            return False
        
        # Check for double top - two peaks at similar levels
        for i in range(len(peaks) - 1):
            peak1 = peaks[i][1]
            peak2 = peaks[i + 1][1]
            
            if abs(peak1 - peak2) / max(peak1, peak2) < 0.03:  # Within 3%
                return True
        
        return False
    
    def _detect_triple_top(self, prices) -> bool:
        """Detect Triple Top pattern"""
        if len(prices) < 15:
            return False
        
        peaks = []
        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                peaks.append((i, prices[i]))
        
        if len(peaks) < 3:
            return False
        
        # Check for triple top - three peaks at similar levels
        for i in range(len(peaks) - 2):
            peak1 = peaks[i][1]
            peak2 = peaks[i + 1][1]
            peak3 = peaks[i + 2][1]
            
            avg_peak = (peak1 + peak2 + peak3) / 3
            if all(abs(p - avg_peak) / avg_peak < 0.04 for p in [peak1, peak2, peak3]):
                return True
        
        return False
    
    def _detect_rounding_top(self, prices) -> bool:
        """Detect Rounding Top pattern"""
        if len(prices) < 12:
            return False
        
        # Check for gradual rise followed by gradual decline
        mid_point = len(prices) // 2
        first_half = prices[:mid_point]
        second_half = prices[mid_point:]
        
        # First half should generally trend up
        first_trend = sum(1 for i in range(1, len(first_half)) if first_half[i] > first_half[i-1])
        # Second half should generally trend down
        second_trend = sum(1 for i in range(1, len(second_half)) if second_half[i] < second_half[i-1])
        
        return (first_trend > len(first_half) * 0.6 and 
                second_trend > len(second_half) * 0.6)
    
    def _detect_bearish_flag(self, prices) -> bool:
        """Detect Bearish Flag pattern"""
        if len(prices) < 10:
            return False
        
        # Look for small upward consolidation after downtrend
        recent_trend = prices[-5:]
        if len(recent_trend) < 5:
            return False
        
        # Check if recent prices are consolidating slightly upward
        slope = (recent_trend[-1] - recent_trend[0]) / len(recent_trend)
        range_size = max(recent_trend) - min(recent_trend)
        avg_price = sum(recent_trend) / len(recent_trend)
        
        return (slope > 0 and range_size / avg_price < 0.02)  # Small upward movement
    
    def _detect_bearish_pennant(self, prices) -> bool:
        """Detect Bearish Pennant pattern"""
        if len(prices) < 8:
            return False
        
        recent_prices = prices[-8:]
        highs = []
        lows = []
        
        for i in range(1, len(recent_prices) - 1):
            if (recent_prices[i] > recent_prices[i-1] and 
                recent_prices[i] > recent_prices[i+1]):
                highs.append(recent_prices[i])
            if (recent_prices[i] < recent_prices[i-1] and 
                recent_prices[i] < recent_prices[i+1]):
                lows.append(recent_prices[i])
        
        # Pennant has converging trend lines
        if len(highs) >= 2 and len(lows) >= 2:
            high_trend = highs[-1] < highs[0]  # Descending highs
            low_trend = lows[-1] > lows[0]    # Ascending lows
            return high_trend and low_trend
        
        return False
    
    def _detect_falling_wedge(self, prices) -> bool:
        """Detect Falling Wedge pattern"""
        if len(prices) < 10:
            return False
        
        # Both highs and lows should be declining but converging
        highs = []
        lows = []
        
        for i in range(1, len(prices) - 1):
            if (prices[i] > prices[i-1] and prices[i] > prices[i+1]):
                highs.append((i, prices[i]))
            if (prices[i] < prices[i-1] and prices[i] < prices[i+1]):
                lows.append((i, prices[i]))
        
        if len(highs) >= 2 and len(lows) >= 2:
            # Check if both trend lines are declining and converging
            high_slope = (highs[-1][1] - highs[0][1]) / (highs[-1][0] - highs[0][0])
            low_slope = (lows[-1][1] - lows[0][1]) / (lows[-1][0] - lows[0][0])
            
            return (high_slope < 0 and low_slope < 0 and abs(high_slope) > abs(low_slope))
        
        return False
    
    def _detect_descending_triangle(self, prices) -> bool:
        """Detect Descending Triangle pattern"""
        if len(prices) < 10:
            return False
        
        lows = []
        highs = []
        
        for i in range(1, len(prices) - 1):
            if (prices[i] < prices[i-1] and prices[i] < prices[i+1]):
                lows.append(prices[i])
            if (prices[i] > prices[i-1] and prices[i] > prices[i+1]):
                highs.append(prices[i])
        
        if len(lows) >= 2 and len(highs) >= 2:
            # Lows should be roughly horizontal, highs should be descending
            low_range = max(lows) - min(lows)
            avg_low = sum(lows) / len(lows)
            high_trend = highs[-1] < highs[0]  # Descending highs
            
            return (low_range / avg_low < 0.02 and high_trend)  # Flat support, descending resistance
        
        return False

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
                    dai_analysis = analysis.get('dai_analysis', {}) # Assuming DAI analysis might be relevant

                    # Update ARB price history for depreciation tracking
                    if 'price' in arb_analysis:
                        self.arb_price_history.append(arb_analysis['price'])
                        if len(self.arb_price_history) > 10: # Keep last 10 prices
                            self.arb_price_history.pop(0)

                    # Check ARB depreciation for debt reduction
                    self.check_arb_depreciation_for_debt_reduction(arb_analysis)

                    # ENHANCED: Detect bearish chart patterns
                    bearish_reversal_patterns = []
                    bearish_continuation_patterns = []
                    
                    # Use price history for pattern detection
                    if hasattr(self, 'arb_price_history') and len(self.arb_price_history) > 10:
                        price_data = [{'price': p} for p in self.arb_price_history]
                        bearish_reversal_patterns = self.detect_bearish_reversal_patterns(price_data)
                        bearish_continuation_patterns = self.detect_bearish_continuation_patterns(price_data)

                    # Calculate adjusted confidence thresholds
                    volatility = abs(analysis.get('market_volatility', 0)) # Example: use a market volatility metric
                    adjusted_dai_to_arb_threshold = self.base_dai_to_arb_threshold + self.market_volatility_modifier * volatility
                    adjusted_arb_to_dai_threshold = self.base_arb_to_dai_threshold + self.market_volatility_modifier * volatility

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

                    # ARB signal analysis (RSI conditions for swaps)
                    arb_rsi = arb_analysis.get('rsi')
                    arb_confidence = arb_analysis.get('confidence', 0)
                    if arb_rsi is not None:
                        if arb_rsi < 30: # Oversold ARB
                            # DAI -> ARB swap condition
                            if arb_confidence >= self.base_dai_to_arb_threshold:
                                signal_strength += arb_confidence * 0.3 # 30% weight for DAI->ARB
                                signals_detected.append(f"DAI->ARB (ARB oversold, conf: {arb_confidence:.2f})")
                        elif arb_rsi > 70: # Overbought ARB
                            # ARB -> DAI swap condition
                            if arb_confidence >= self.base_arb_to_dai_threshold:
                                signal_strength -= arb_confidence * 0.3 # 30% weight for ARB->DAI
                                signals_detected.append(f"ARB->DAI (ARB overbought, conf: {arb_confidence:.2f})")

                    # Apply bearish pattern influence
                    if bearish_reversal_patterns or bearish_continuation_patterns:
                        pattern_weight = len(bearish_reversal_patterns) * 0.15 + len(bearish_continuation_patterns) * 0.10
                        signal_strength -= pattern_weight  # Bearish patterns reduce signal strength

                    # Apply overall sentiment to signal strength
                    market_sentiment = analysis.get('market_sentiment', 'neutral')
                    if market_sentiment == 'bearish':
                        signal_strength *= 0.8 # Reduce signal strength in bearish market
                    elif market_sentiment == 'bullish':
                        signal_strength *= 1.2 # Increase signal strength in bullish market

                    # Determine overall recommendation and action
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
                        'market_sentiment': market_sentiment,
                        'confidence_level': abs(signal_strength),
                        'bearish_reversal_patterns': bearish_reversal_patterns,
                        'bearish_continuation_patterns': bearish_continuation_patterns,
                        'timestamp': time.time(),
                        'status': 'success'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Market analysis failed',
                        'recommendation': 'HOLD',
                        'action': 'hold',
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

    def check_arb_depreciation_for_debt_reduction(self, arb_analysis: Dict):
        """Checks for ARB depreciation and triggers debt reduction if conditions are met."""
        current_time = time.time()
        if current_time - self.last_debt_reduction < self.debt_reduction_cooldown:
            return # Cooldown period active

        if not self.agent or not hasattr(self.agent, 'get_health_factor') or not hasattr(self.agent, 'swap_dai_for_arb'):
            logger.warning("Agent not properly initialized for debt reduction.")
            return

        health_factor = self.agent.get_health_factor()
        if health_factor is None or health_factor <= 2.0:
            logger.info(f"Health factor ({health_factor}) too low for debt reduction. Required > 2.0")
            return # Health factor gate

        if not self.arb_price_history or len(self.arb_price_history) < 2:
            logger.info("Not enough ARB price history to determine depreciation.")
            return # Need at least two data points to check depreciation

        # Check for significant ARB depreciation
        latest_arb_price = arb_analysis.get('price')
        if latest_arb_price is None:
            logger.warning("Could not retrieve latest ARB price for depreciation check.")
            return

        # Calculate depreciation over the last recorded interval
        previous_arb_price = self.arb_price_history[-2] # Get the second to last price
        if previous_arb_price == 0: return # Avoid division by zero

        depreciation = (latest_arb_price - previous_arb_price) / previous_arb_price

        if depreciation <= self.arb_depreciation_threshold:
            logger.info(f"ARB depreciated by {depreciation:.2%}. Triggering DAI -> ARB swap for debt reduction.")
            # Execute swap to reduce DAI debt by acquiring ARB
            try:
                # Placeholder for actual swap logic - needs agent method
                # self.agent.swap_dai_for_arb(amount_dai, token_arb)
                logger.info("Executing DAI -> ARB swap for debt reduction.")
                self.last_debt_reduction = current_time # Update cooldown
                # Optionally store entry price for ARB
                self.arb_entry_prices[time.time()] = latest_arb_price
                return True
            except Exception as e:
                logger.error(f"Error executing DAI -> ARB swap: {e}")
                return False
        return False


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