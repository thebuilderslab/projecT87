
"""
Enhanced Market Analyzer with Advanced Pattern Recognition
Incorporates multi-timeframe analysis, pattern recognition, and success rate optimization
"""

import numpy as np
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class MarketPattern:
    pattern_type: str
    confidence: float
    timeframe: str
    success_probability: float
    risk_score: float

@dataclass
class EnhancedMarketSignal:
    signal_type: str
    confidence: float
    btc_analysis: Dict
    arb_analysis: Dict
    pattern_analysis: Dict
    gas_efficiency_score: float
    success_probability: float
    recommended_amount: float
    timestamp: float

class EnhancedMarketAnalyzer:
    def __init__(self, agent):
        self.agent = agent
        self.coinmarketcap_api_key = agent.coinmarketcap_api_key
        self.price_history = {'BTC': [], 'ARB': []}
        self.pattern_success_rates = {}
        
        # Enhanced configuration
        self.btc_narrow_threshold = 0.003  # 0.3% threshold
        self.analysis_window_hours = 4
        self.hourly_average_weight = 0.6
        self.pattern_confidence_threshold = 0.75
        
        # Load historical success rates
        self._load_pattern_success_rates()
        
    def _load_pattern_success_rates(self):
        """Load historical pattern success rates from data"""
        try:
            with open('pattern_success_rates.json', 'r') as f:
                self.pattern_success_rates = json.load(f)
        except FileNotFoundError:
            # Initialize with default success rates
            self.pattern_success_rates = {
                'btc_dip_arb_oversold': 0.78,
                'btc_recovery_arb_momentum': 0.71,
                'divergence_pattern': 0.65,
                'volume_spike_pattern': 0.69,
                'consolidation_breakout': 0.73
            }
    
    def get_historical_price_data(self, symbol: str, hours: int = 4) -> List[Dict]:
        """Get historical price data for pattern analysis"""
        try:
            # Using CoinMarketCap historical data endpoint
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': self.coinmarketcap_api_key,
            }
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            parameters = {
                'symbol': symbol,
                'time_start': start_time.isoformat(),
                'time_end': end_time.isoformat(),
                'interval': '1h',
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=headers, params=parameters, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                return data['data']['quotes']
            return []
            
        except Exception as e:
            logging.error(f"Failed to get historical data for {symbol}: {e}")
            return []
    
    def calculate_advanced_indicators(self, price_data: List[Dict]) -> Dict:
        """Calculate advanced technical indicators from price history"""
        if len(price_data) < 4:
            return {'rsi': 50, 'macd': 0, 'bb_bands': {'upper': 0, 'lower': 0}}
        
        prices = [float(candle['quote']['USD']['close']) for candle in price_data]
        
        # Enhanced RSI calculation
        rsi = self._calculate_rsi(prices, period=min(14, len(prices)))
        
        # MACD calculation
        macd_line, macd_signal = self._calculate_macd(prices)
        
        # Bollinger Bands
        bb_upper, bb_lower = self._calculate_bollinger_bands(prices)
        
        # Volume analysis
        volumes = [float(candle['quote']['USD']['volume']) for candle in price_data]
        volume_trend = self._analyze_volume_trend(volumes)
        
        return {
            'rsi': rsi,
            'macd': {'line': macd_line, 'signal': macd_signal, 'histogram': macd_line - macd_signal},
            'bb_bands': {'upper': bb_upper, 'lower': bb_lower},
            'volume_trend': volume_trend,
            'price_momentum': self._calculate_momentum(prices),
            'volatility': np.std(prices) if len(prices) > 1 else 0
        }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI with proper price change analysis"""
        if len(prices) < period + 1:
            return 50.0
        
        price_changes = np.diff(prices)
        gains = np.where(price_changes > 0, price_changes, 0)
        losses = np.where(price_changes < 0, -price_changes, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> Tuple[float, float]:
        """Calculate MACD line and signal line"""
        if len(prices) < 26:
            return 0.0, 0.0
        
        # EMA calculation
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        signal_line = self._calculate_ema([macd_line], 9)
        
        return macd_line, signal_line
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if not prices:
            return 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return 0.0, 0.0
        
        recent_prices = prices[-period:]
        mean_price = np.mean(recent_prices)
        std_dev = np.std(recent_prices)
        
        upper_band = mean_price + (2 * std_dev)
        lower_band = mean_price - (2 * std_dev)
        
        return upper_band, lower_band
    
    def _analyze_volume_trend(self, volumes: List[float]) -> Dict:
        """Analyze volume trends"""
        if len(volumes) < 2:
            return {'trend': 'neutral', 'strength': 0}
        
        recent_avg = np.mean(volumes[-2:])
        historical_avg = np.mean(volumes[:-2]) if len(volumes) > 2 else recent_avg
        
        if recent_avg > historical_avg * 1.5:
            return {'trend': 'increasing', 'strength': 0.8}
        elif recent_avg < historical_avg * 0.7:
            return {'trend': 'decreasing', 'strength': 0.6}
        else:
            return {'trend': 'stable', 'strength': 0.4}
    
    def _calculate_momentum(self, prices: List[float]) -> float:
        """Calculate price momentum"""
        if len(prices) < 2:
            return 0.0
        
        return (prices[-1] - prices[0]) / prices[0] * 100
    
    def detect_chart_patterns(self, btc_data: List[Dict], arb_data: List[Dict]) -> List[MarketPattern]:
        """Detect negative chart patterns for bearish signals"""
        patterns = []
        
        if len(btc_data) < 4 or len(arb_data) < 4:
            return patterns
        
        btc_prices = [float(candle['quote']['USD']['close']) for candle in btc_data]
        arb_prices = [float(candle['quote']['USD']['close']) for candle in arb_data]
        
        # Pattern 1: BTC Declining with ARB Oversold
        btc_decline = (btc_prices[-1] - btc_prices[0]) / btc_prices[0]
        if btc_decline <= -self.btc_narrow_threshold:
            arb_indicators = self.calculate_advanced_indicators(arb_data)
            if arb_indicators['rsi'] <= 30:
                patterns.append(MarketPattern(
                    pattern_type='btc_dip_arb_oversold',
                    confidence=0.85,
                    timeframe='4h',
                    success_probability=self.pattern_success_rates.get('btc_dip_arb_oversold', 0.78),
                    risk_score=0.3
                ))
        
        # Pattern 2: Divergence Pattern
        btc_momentum = self._calculate_momentum(btc_prices)
        arb_momentum = self._calculate_momentum(arb_prices)
        
        if abs(btc_momentum - arb_momentum) > 2.0:  # 2% divergence
            patterns.append(MarketPattern(
                pattern_type='divergence_pattern',
                confidence=0.7,
                timeframe='4h',
                success_probability=self.pattern_success_rates.get('divergence_pattern', 0.65),
                risk_score=0.4
            ))
        
        # Pattern 3: Volume Spike with Price Drop
        btc_volumes = [float(candle['quote']['USD']['volume']) for candle in btc_data]
        volume_analysis = self._analyze_volume_trend(btc_volumes)
        
        if volume_analysis['trend'] == 'increasing' and btc_decline < -0.005:
            patterns.append(MarketPattern(
                pattern_type='volume_spike_pattern',
                confidence=0.75,
                timeframe='4h',
                success_probability=self.pattern_success_rates.get('volume_spike_pattern', 0.69),
                risk_score=0.35
            ))
        
        return patterns
    
    def calculate_gas_efficiency_score(self) -> float:
        """Calculate current gas efficiency for operations"""
        try:
            # Get current gas price
            current_gas = self.agent.get_current_gas_price()
            
            # Historical average (you can track this over time)
            avg_gas = 0.1  # Gwei, adjust based on your tracking
            
            # Lower gas = higher efficiency score
            if current_gas <= avg_gas * 0.8:
                return 0.9  # Excellent gas conditions
            elif current_gas <= avg_gas * 1.2:
                return 0.7  # Good gas conditions
            elif current_gas <= avg_gas * 1.5:
                return 0.5  # Average gas conditions
            else:
                return 0.3  # Poor gas conditions
        except:
            return 0.5  # Default moderate score
    
    def generate_enhanced_signal(self) -> Optional[EnhancedMarketSignal]:
        """Generate enhanced market signal with pattern analysis"""
        try:
            # Get 4-hour historical data
            btc_historical = self.get_historical_price_data('BTC', self.analysis_window_hours)
            arb_historical = self.get_historical_price_data('ARB', self.analysis_window_hours)
            
            if not btc_historical or not arb_historical:
                logging.warning("Insufficient historical data for enhanced analysis")
                return None
            
            # Calculate indicators
            btc_indicators = self.calculate_advanced_indicators(btc_historical)
            arb_indicators = self.calculate_advanced_indicators(arb_historical)
            
            # Detect patterns
            patterns = self.detect_chart_patterns(btc_historical, arb_historical)
            
            # Calculate weighted success probability
            pattern_success = 0.5  # Default
            if patterns:
                pattern_success = max(p.success_probability for p in patterns)
            
            # Gas efficiency
            gas_score = self.calculate_gas_efficiency_score()
            
            # Determine signal based on patterns and indicators
            signal_type = 'neutral'
            confidence = 0.0
            
            # Check for bearish signal (DAI → ARB opportunity)
            bearish_patterns = [p for p in patterns if 'dip' in p.pattern_type or 'oversold' in p.pattern_type]
            if bearish_patterns and arb_indicators['rsi'] <= 30:
                signal_type = 'bearish'
                confidence = min(0.9, max(p.confidence for p in bearish_patterns) * gas_score)
            
            # Check for bullish signal (ARB → DAI opportunity)
            elif arb_indicators['rsi'] >= 70 and btc_indicators['momentum'] > 1.0:
                signal_type = 'bullish'
                confidence = 0.75 * gas_score
            
            # Calculate recommended amount based on success probability and gas costs
            base_amount = 5.0  # Base $5 operation
            risk_adjusted_amount = base_amount * pattern_success * gas_score
            recommended_amount = min(10.0, max(1.0, risk_adjusted_amount))  # Clamp between $1-$10
            
            return EnhancedMarketSignal(
                signal_type=signal_type,
                confidence=confidence,
                btc_analysis=btc_indicators,
                arb_analysis=arb_indicators,
                pattern_analysis={'patterns': [p.__dict__ for p in patterns], 'count': len(patterns)},
                gas_efficiency_score=gas_score,
                success_probability=pattern_success,
                recommended_amount=recommended_amount,
                timestamp=time.time()
            )
            
        except Exception as e:
            logging.error(f"Enhanced signal generation failed: {e}")
            return None
    
    def update_pattern_success_rate(self, pattern_type: str, success: bool):
        """Update pattern success rates based on actual results"""
        if pattern_type not in self.pattern_success_rates:
            self.pattern_success_rates[pattern_type] = 0.5
        
        # Simple learning rate adjustment
        learning_rate = 0.1
        current_rate = self.pattern_success_rates[pattern_type]
        
        if success:
            self.pattern_success_rates[pattern_type] = current_rate + (learning_rate * (1 - current_rate))
        else:
            self.pattern_success_rates[pattern_type] = current_rate - (learning_rate * current_rate)
        
        # Save updated rates
        try:
            with open('pattern_success_rates.json', 'w') as f:
                json.dump(self.pattern_success_rates, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save pattern success rates: {e}")
