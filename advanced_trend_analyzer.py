
#!/usr/bin/env python3
"""
Advanced Trend Analyzer - Minute-by-Minute and 1-Hour Analysis
Optimized system for real-time market trend detection and prediction
"""

import time
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import statistics

@dataclass
class TrendPoint:
    timestamp: float
    btc_price: float
    btc_change_1m: float
    btc_change_5m: float
    btc_change_15m: float
    btc_change_1h: float
    arb_price: float
    arb_change_1m: float
    arb_change_5m: float
    arb_change_15m: float
    arb_change_1h: float
    volume_btc: float
    volume_arb: float

@dataclass
class TrendAnalysis:
    trend_direction: str  # 'bullish', 'bearish', 'sideways'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    momentum_1m: float
    momentum_5m: float
    momentum_15m: float
    momentum_1h: float
    volatility_score: float
    prediction_1h: Dict
    signals: List[str]

class AdvancedTrendAnalyzer:
    def __init__(self, agent):
        self.agent = agent
        self.coinmarketcap_api_key = agent.coinmarketcap_api_key
        
        # Data storage - keep last 24 hours of minute data
        self.max_data_points = 1440  # 24 hours * 60 minutes
        self.price_history = deque(maxlen=self.max_data_points)
        self.trend_history = deque(maxlen=60)  # Last hour of trend analyses
        
        # Analysis parameters
        self.volatility_threshold = 0.02  # 2% volatility threshold
        self.trend_strength_threshold = 0.7  # 70% strength for strong trends
        self.momentum_decay_factor = 0.95  # How quickly momentum decays
        
        # Optimization flags
        self.enable_minute_analysis = True
        self.enable_1h_prediction = True
        self.enable_volume_analysis = True
        self.enable_volatility_filtering = True
        
        logging.info("Advanced Trend Analyzer initialized with minute-by-minute analysis")

    def collect_real_time_data(self) -> Optional[TrendPoint]:
        """Collect real-time price data for trend analysis"""
        try:
            # Get current market data
            btc_data = self._get_btc_data_with_history()
            arb_data = self._get_arb_data_with_history()
            
            if not btc_data or not arb_data:
                return None
            
            current_time = time.time()
            
            # Calculate multi-timeframe changes
            btc_changes = self._calculate_timeframe_changes(btc_data, 'btc')
            arb_changes = self._calculate_timeframe_changes(arb_data, 'arb')
            
            trend_point = TrendPoint(
                timestamp=current_time,
                btc_price=btc_data.get('price', 0),
                btc_change_1m=btc_changes.get('1m', 0),
                btc_change_5m=btc_changes.get('5m', 0),
                btc_change_15m=btc_changes.get('15m', 0),
                btc_change_1h=btc_data.get('percent_change_1h', 0),
                arb_price=arb_data.get('price', 0),
                arb_change_1m=arb_changes.get('1m', 0),
                arb_change_5m=arb_changes.get('5m', 0),
                arb_change_15m=arb_changes.get('15m', 0),
                arb_change_1h=arb_data.get('percent_change_1h', 0),
                volume_btc=btc_data.get('volume_24h', 0),
                volume_arb=arb_data.get('volume_24h', 0)
            )
            
            # Store in history
            self.price_history.append(trend_point)
            
            return trend_point
            
        except Exception as e:
            logging.error(f"Failed to collect real-time data: {e}")
            return None

    def analyze_minute_trends(self) -> Optional[TrendAnalysis]:
        """Analyze minute-by-minute trends with 1-hour prediction"""
        try:
            if len(self.price_history) < 15:  # Need at least 15 minutes of data
                logging.warning("Insufficient data for trend analysis")
                return None
            
            current_point = self.price_history[-1]
            
            # Calculate trend direction and strength
            trend_direction, strength = self._calculate_trend_direction()
            
            # Calculate momentum across timeframes
            momentum_1m = self._calculate_momentum('1m', 1)
            momentum_5m = self._calculate_momentum('5m', 5)
            momentum_15m = self._calculate_momentum('15m', 15)
            momentum_1h = self._calculate_momentum('1h', 60)
            
            # Calculate volatility
            volatility_score = self._calculate_volatility()
            
            # Generate 1-hour prediction
            prediction_1h = self._generate_1hour_prediction()
            
            # Calculate confidence based on data quality and consistency
            confidence = self._calculate_trend_confidence(
                strength, volatility_score, momentum_1h
            )
            
            # Generate actionable signals
            signals = self._generate_trend_signals(
                trend_direction, strength, confidence, prediction_1h
            )
            
            analysis = TrendAnalysis(
                trend_direction=trend_direction,
                strength=strength,
                confidence=confidence,
                momentum_1m=momentum_1m,
                momentum_5m=momentum_5m,
                momentum_15m=momentum_15m,
                momentum_1h=momentum_1h,
                volatility_score=volatility_score,
                prediction_1h=prediction_1h,
                signals=signals
            )
            
            # Store analysis
            self.trend_history.append(analysis)
            
            return analysis
            
        except Exception as e:
            logging.error(f"Minute trend analysis failed: {e}")
            return None

    def _calculate_trend_direction(self) -> Tuple[str, float]:
        """Calculate overall trend direction and strength"""
        if len(self.price_history) < 10:
            return 'sideways', 0.0
        
        # Use multiple timeframes for trend determination
        recent_points = list(self.price_history)[-10:]
        
        # BTC trend analysis
        btc_prices = [p.btc_price for p in recent_points]
        btc_trend = (btc_prices[-1] - btc_prices[0]) / btc_prices[0]
        
        # ARB trend analysis
        arb_prices = [p.arb_price for p in recent_points]
        arb_trend = (arb_prices[-1] - arb_prices[0]) / arb_prices[0]
        
        # Combined trend score
        combined_trend = (btc_trend * 0.6 + arb_trend * 0.4)  # BTC weighted more
        
        # Determine direction
        if combined_trend > 0.002:  # > 0.2%
            direction = 'bullish'
        elif combined_trend < -0.002:  # < -0.2%
            direction = 'bearish'
        else:
            direction = 'sideways'
        
        # Calculate strength
        strength = min(1.0, abs(combined_trend) * 100)  # Convert to 0-1 scale
        
        return direction, strength

    def _calculate_momentum(self, timeframe: str, minutes: int) -> float:
        """Calculate momentum for specific timeframe"""
        if len(self.price_history) < minutes:
            return 0.0
        
        recent_points = list(self.price_history)[-minutes:]
        
        # Calculate price momentum
        btc_momentum = sum(p.btc_change_1m for p in recent_points) / len(recent_points)
        arb_momentum = sum(p.arb_change_1m for p in recent_points) / len(recent_points)
        
        # Weighted average
        combined_momentum = (btc_momentum * 0.6 + arb_momentum * 0.4)
        
        return combined_momentum

    def _calculate_volatility(self) -> float:
        """Calculate market volatility score"""
        if len(self.price_history) < 30:
            return 0.5  # Default moderate volatility
        
        recent_points = list(self.price_history)[-30:]  # Last 30 minutes
        
        # BTC volatility
        btc_changes = [p.btc_change_1m for p in recent_points]
        btc_volatility = statistics.stdev(btc_changes) if len(btc_changes) > 1 else 0
        
        # ARB volatility
        arb_changes = [p.arb_change_1m for p in recent_points]
        arb_volatility = statistics.stdev(arb_changes) if len(arb_changes) > 1 else 0
        
        # Combined volatility score (0-1 scale)
        combined_volatility = min(1.0, (btc_volatility + arb_volatility) / 2)
        
        return combined_volatility

    def _generate_1hour_prediction(self) -> Dict:
        """Generate 1-hour price prediction based on trends"""
        if len(self.price_history) < 60:
            return {'confidence': 0.0, 'direction': 'unknown', 'magnitude': 0.0}
        
        # Use last hour of data for prediction
        hour_data = list(self.price_history)[-60:]
        
        # Linear regression on price movements
        btc_trend = self._simple_linear_regression([p.btc_price for p in hour_data])
        arb_trend = self._simple_linear_regression([p.arb_price for p in hour_data])
        
        # Predict next hour movement
        btc_prediction = btc_trend * 60  # Extrapolate for 60 minutes
        arb_prediction = arb_trend * 60
        
        # Combined prediction
        combined_prediction = (btc_prediction * 0.6 + arb_prediction * 0.4)
        
        # Determine direction and magnitude
        if combined_prediction > 0.005:  # > 0.5%
            direction = 'bullish'
        elif combined_prediction < -0.005:  # < -0.5%
            direction = 'bearish'
        else:
            direction = 'sideways'
        
        magnitude = abs(combined_prediction)
        confidence = min(0.95, max(0.1, magnitude * 20))  # Scale confidence
        
        return {
            'confidence': confidence,
            'direction': direction,
            'magnitude': magnitude,
            'btc_prediction': btc_prediction,
            'arb_prediction': arb_prediction
        }

    def _simple_linear_regression(self, prices: List[float]) -> float:
        """Simple linear regression to find trend slope"""
        if len(prices) < 2:
            return 0.0
        
        n = len(prices)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = sum(x_values) / n
        y_mean = sum(prices) / n
        
        numerator = sum((x_values[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope

    def _calculate_trend_confidence(self, strength: float, volatility: float, momentum: float) -> float:
        """Calculate confidence in trend analysis"""
        # Base confidence from trend strength
        base_confidence = strength
        
        # Adjust for volatility (high volatility reduces confidence)
        volatility_adjustment = max(0.5, 1.0 - volatility)
        
        # Momentum consistency bonus
        momentum_bonus = min(0.2, abs(momentum) * 10)
        
        # Data quality bonus (more data = higher confidence)
        data_bonus = min(0.1, len(self.price_history) / 1440)  # Up to 10% bonus for full day
        
        confidence = base_confidence * volatility_adjustment + momentum_bonus + data_bonus
        return min(0.98, max(0.1, confidence))

    def _generate_trend_signals(self, direction: str, strength: float, confidence: float, prediction: Dict) -> List[str]:
        """Generate actionable trading signals"""
        signals = []
        
        # Strong trend signals
        if strength > 0.7 and confidence > 0.8:
            if direction == 'bearish':
                signals.append('STRONG_BEARISH_TREND')
                if prediction['direction'] == 'bearish' and prediction['confidence'] > 0.7:
                    signals.append('DAI_TO_ARB_OPPORTUNITY')
            elif direction == 'bullish':
                signals.append('STRONG_BULLISH_TREND')
                signals.append('ARB_TO_DAI_OPPORTUNITY')
        
        # Momentum signals
        if abs(prediction.get('magnitude', 0)) > 0.01:  # > 1% predicted movement
            if prediction['direction'] == 'bearish':
                signals.append('BEARISH_MOMENTUM_BUILDING')
            else:
                signals.append('BULLISH_MOMENTUM_BUILDING')
        
        # Volatility signals
        volatility = self._calculate_volatility()
        if volatility > 0.05:
            signals.append('HIGH_VOLATILITY_DETECTED')
        elif volatility < 0.01:
            signals.append('LOW_VOLATILITY_CONSOLIDATION')
        
        return signals

    def _get_btc_data_with_history(self) -> Optional[Dict]:
        """Get BTC data with historical context"""
        try:
            if not hasattr(self, 'market_data_api'):
                from market_data_api_fix import MarketDataAPIFix
                self.market_data_api = MarketDataAPIFix(self.coinmarketcap_api_key)
            
            return self.market_data_api.get_btc_price_data_fixed()
        except Exception as e:
            logging.error(f"BTC data error: {e}")
            return None

    def _get_arb_data_with_history(self) -> Optional[Dict]:
        """Get ARB data with historical context"""
        try:
            if not hasattr(self, 'market_data_api'):
                from market_data_api_fix import MarketDataAPIFix
                self.market_data_api = MarketDataAPIFix(self.coinmarketcap_api_key)
            
            return self.market_data_api.get_arb_price_data_fixed()
        except Exception as e:
            logging.error(f"ARB data error: {e}")
            return None

    def _calculate_timeframe_changes(self, data: Dict, asset: str) -> Dict:
        """Calculate price changes for multiple timeframes"""
        try:
            current_price = data.get('price', 0)
            
            # For minute changes, we need to track our own history
            # Use percentage changes from API as approximation
            return {
                '1m': data.get('percent_change_1h', 0) / 60,  # Approximate 1-minute change
                '5m': data.get('percent_change_1h', 0) / 12,  # Approximate 5-minute change
                '15m': data.get('percent_change_1h', 0) / 4,  # Approximate 15-minute change
            }
        except Exception:
            return {'1m': 0, '5m': 0, '15m': 0}

    def get_current_trend_summary(self) -> Dict:
        """Get current trend analysis summary"""
        if not self.trend_history:
            return {'status': 'insufficient_data'}
        
        latest_analysis = self.trend_history[-1]
        
        return {
            'trend_direction': latest_analysis.trend_direction,
            'strength': latest_analysis.strength,
            'confidence': latest_analysis.confidence,
            'momentum_1h': latest_analysis.momentum_1h,
            'volatility': latest_analysis.volatility_score,
            'prediction_1h': latest_analysis.prediction_1h,
            'active_signals': latest_analysis.signals,
            'data_points': len(self.price_history),
            'analysis_count': len(self.trend_history)
        }

    def should_trigger_trade_based_on_trends(self) -> Tuple[bool, str, Dict]:
        """Determine if trends indicate a trade opportunity"""
        if not self.trend_history:
            return False, 'no_data', {}
        
        latest = self.trend_history[-1]
        
        # Strong bearish trend with high confidence
        if (latest.trend_direction == 'bearish' and 
            latest.strength > 0.7 and 
            latest.confidence > 0.85 and
            'DAI_TO_ARB_OPPORTUNITY' in latest.signals):
            
            return True, 'dai_to_arb', {
                'confidence': latest.confidence,
                'strength': latest.strength,
                'prediction': latest.prediction_1h
            }
        
        # Strong bullish trend for profit taking
        if (latest.trend_direction == 'bullish' and 
            latest.strength > 0.6 and 
            latest.confidence > 0.8 and
            'ARB_TO_DAI_OPPORTUNITY' in latest.signals):
            
            return True, 'arb_to_dai', {
                'confidence': latest.confidence,
                'strength': latest.strength,
                'prediction': latest.prediction_1h
            }
        
        return False, 'hold', {'reason': 'conditions_not_met'}
