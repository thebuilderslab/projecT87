
```python
#!/usr/bin/env python3
"""
Enhanced Market Analyzer with CoinMarketCap API Integration
Provides comprehensive trading analysis for debt swap decisions
"""

import os
import time
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TechnicalIndicators:
    """Container for technical indicator values"""
    rsi: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    sma_9: float
    sma_50: float
    sma_100: float
    sma_200: float
    bollinger_upper: float
    bollinger_lower: float
    volume_sma: float

@dataclass
class MarketSignal:
    """Enhanced market signal with technical analysis"""
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0.0 to 1.0
    strength: str  # 'weak', 'moderate', 'strong'
    indicators: TechnicalIndicators
    recommendation: str
    timestamp: float

class CoinMarketCapAPI:
    """CoinMarketCap API client for fetching market data"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        })
        
    def get_historical_data(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data for a given symbol"""
        try:
            # Get symbol ID first
            url = f"{self.base_url}/v1/cryptocurrency/map"
            params = {'symbol': symbol}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data['data']:
                logger.warning(f"No data found for symbol {symbol}")
                return None
                
            crypto_id = data['data'][0]['id']
            
            # Get historical quotes
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            quotes_url = f"{self.base_url}/v2/cryptocurrency/quotes/historical"
            quotes_params = {
                'id': crypto_id,
                'time_start': start_date.strftime('%Y-%m-%d'),
                'time_end': end_date.strftime('%Y-%m-%d'),
                'interval': 'daily',
                'count': days
            }
            
            quotes_response = self.session.get(quotes_url, params=quotes_params, timeout=30)
            quotes_response.raise_for_status()
            
            quotes_data = quotes_response.json()
            
            if 'data' not in quotes_data or not quotes_data['data']:
                logger.warning(f"No historical data found for {symbol}")
                return None
                
            # Convert to DataFrame
            historical_data = []
            for entry in quotes_data['data']:
                timestamp = pd.to_datetime(entry['timestamp'])
                quote = entry['quote']['USD']
                
                historical_data.append({
                    'timestamp': timestamp,
                    'open': quote.get('open', quote['price']),
                    'high': quote.get('high', quote['price']),
                    'low': quote.get('low', quote['price']),
                    'close': quote['price'],
                    'volume': quote.get('volume_24h', 0),
                    'market_cap': quote.get('market_cap', 0)
                })
            
            df = pd.DataFrame(historical_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"Successfully fetched {len(df)} days of data for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price and 24h data for a symbol"""
        try:
            url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if symbol in data['data']:
                quote = data['data'][symbol]['quote']['USD']
                return {
                    'price': quote['price'],
                    'percent_change_1h': quote.get('percent_change_1h', 0),
                    'percent_change_24h': quote.get('percent_change_24h', 0),
                    'percent_change_7d': quote.get('percent_change_7d', 0),
                    'volume_24h': quote.get('volume_24h', 0),
                    'market_cap': quote.get('market_cap', 0)
                }
            return None
            
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None

class TechnicalAnalysis:
    """Technical analysis calculations for trading indicators"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD line, signal line, and histogram"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        """Calculate volume Simple Moving Average"""
        return volume.rolling(window=period).mean()

class EnhancedMarketAnalyzer:
    """Enhanced market analyzer with comprehensive technical analysis"""
    
    def __init__(self, agent):
        self.agent = agent
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        if not self.api_key:
            raise ValueError("COINMARKETCAP_API_KEY not found in environment variables")
        
        self.cmc_client = CoinMarketCapAPI(self.api_key)
        self.technical_analysis = TechnicalAnalysis()
        
        # Cache for historical data
        self.data_cache = {}
        self.cache_timeout = 3600  # 1 hour
        
        logger.info("Enhanced Market Analyzer initialized successfully")
    
    def get_cached_data(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Get cached historical data or fetch new data"""
        cache_key = f"{symbol}_{days}"
        current_time = time.time()
        
        if cache_key in self.data_cache:
            cached_data, timestamp = self.data_cache[cache_key]
            if current_time - timestamp < self.cache_timeout:
                return cached_data
        
        # Fetch new data
        data = self.cmc_client.get_historical_data(symbol, days)
        if data is not None:
            self.data_cache[cache_key] = (data, current_time)
        
        return data
    
    def calculate_indicators(self, data: pd.DataFrame) -> Optional[TechnicalIndicators]:
        """Calculate all technical indicators for the given data"""
        try:
            if len(data) < 200:  # Need enough data for 200-day MA
                logger.warning("Insufficient data for complete technical analysis")
                return None
            
            close_prices = data['close']
            volume = data['volume']
            
            # Calculate indicators
            rsi = self.technical_analysis.calculate_rsi(close_prices).iloc[-1]
            macd_line, signal_line, histogram = self.technical_analysis.calculate_macd(close_prices)
            
            sma_9 = self.technical_analysis.calculate_sma(close_prices, 9).iloc[-1]
            sma_50 = self.technical_analysis.calculate_sma(close_prices, 50).iloc[-1]
            sma_100 = self.technical_analysis.calculate_sma(close_prices, 100).iloc[-1]
            sma_200 = self.technical_analysis.calculate_sma(close_prices, 200).iloc[-1]
            
            upper_bb, middle_bb, lower_bb = self.technical_analysis.calculate_bollinger_bands(close_prices)
            volume_sma = self.technical_analysis.calculate_volume_sma(volume).iloc[-1]
            
            return TechnicalIndicators(
                rsi=rsi,
                macd_line=macd_line.iloc[-1],
                macd_signal=signal_line.iloc[-1],
                macd_histogram=histogram.iloc[-1],
                sma_9=sma_9,
                sma_50=sma_50,
                sma_100=sma_100,
                sma_200=sma_200,
                bollinger_upper=upper_bb.iloc[-1],
                bollinger_lower=lower_bb.iloc[-1],
                volume_sma=volume_sma
            )
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None
    
    def analyze_signal_strength(self, indicators: TechnicalIndicators, current_price: float) -> Tuple[str, float, str]:
        """Analyze signal strength based on technical indicators"""
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        # RSI Analysis
        if indicators.rsi < 30:
            bullish_signals += 2  # Oversold - strong bullish
        elif indicators.rsi < 40:
            bullish_signals += 1  # Moderately oversold
        elif indicators.rsi > 70:
            bearish_signals += 2  # Overbought - strong bearish
        elif indicators.rsi > 60:
            bearish_signals += 1  # Moderately overbought
        total_signals += 2
        
        # MACD Analysis
        if indicators.macd_line > indicators.macd_signal and indicators.macd_histogram > 0:
            bullish_signals += 2  # MACD bullish crossover
        elif indicators.macd_line < indicators.macd_signal and indicators.macd_histogram < 0:
            bearish_signals += 2  # MACD bearish crossover
        total_signals += 2
        
        # Moving Average Analysis
        if indicators.sma_9 > indicators.sma_50 > indicators.sma_100 > indicators.sma_200:
            bullish_signals += 3  # Strong uptrend
        elif indicators.sma_9 < indicators.sma_50 < indicators.sma_100 < indicators.sma_200:
            bearish_signals += 3  # Strong downtrend
        elif indicators.sma_9 > indicators.sma_50:
            bullish_signals += 1  # Short-term bullish
        elif indicators.sma_9 < indicators.sma_50:
            bearish_signals += 1  # Short-term bearish
        total_signals += 3
        
        # Bollinger Bands Analysis
        if current_price < indicators.bollinger_lower:
            bullish_signals += 1  # Price below lower band - potential bounce
        elif current_price > indicators.bollinger_upper:
            bearish_signals += 1  # Price above upper band - potential reversal
        total_signals += 1
        
        # Calculate confidence and determine signal
        net_bullish = bullish_signals - bearish_signals
        confidence = abs(net_bullish) / total_signals
        
        if net_bullish > 2:
            signal_type = "bullish"
            strength = "strong" if confidence > 0.6 else "moderate"
        elif net_bullish < -2:
            signal_type = "bearish"
            strength = "strong" if confidence > 0.6 else "moderate"
        else:
            signal_type = "neutral"
            strength = "weak"
            confidence = max(0.1, confidence)  # Minimum confidence for neutral
        
        return signal_type, confidence, strength
    
    def should_execute_trade(self) -> bool:
        """Enhanced trade execution decision based on comprehensive analysis"""
        try:
            logger.info("🔍 ENHANCED MARKET ANALYSIS - Comprehensive Technical Analysis")
            logger.info("=" * 70)
            
            # Fetch data for multiple assets
            btc_data = self.get_cached_data('BTC', 365)
            eth_data = self.get_cached_data('ETH', 365)
            
            # Get current prices
            btc_current = self.cmc_client.get_current_price('BTC')
            eth_current = self.cmc_client.get_current_price('ETH')
            
            if not all([btc_data is not None, eth_data is not None, btc_current, eth_current]):
                logger.warning("⚠️ Insufficient market data for analysis")
                return False
            
            # Calculate indicators for BTC and ETH
            btc_indicators = self.calculate_indicators(btc_data)
            eth_indicators = self.calculate_indicators(eth_data)
            
            if not btc_indicators or not eth_indicators:
                logger.warning("⚠️ Failed to calculate technical indicators")
                return False
            
            # Analyze signals
            btc_signal, btc_confidence, btc_strength = self.analyze_signal_strength(
                btc_indicators, btc_current['price']
            )
            eth_signal, eth_confidence, eth_strength = self.analyze_signal_strength(
                eth_indicators, eth_current['price']
            )
            
            logger.info(f"📊 BTC Analysis:")
            logger.info(f"   Signal: {btc_signal.upper()} ({btc_strength})")
            logger.info(f"   Confidence: {btc_confidence:.2f}")
            logger.info(f"   RSI: {btc_indicators.rsi:.1f}")
            logger.info(f"   MACD: {btc_indicators.macd_line:.2f} / {btc_indicators.macd_signal:.2f}")
            logger.info(f"   Price vs SMA50: {((btc_current['price'] / btc_indicators.sma_50 - 1) * 100):+.1f}%")
            
            logger.info(f"📊 ETH Analysis:")
            logger.info(f"   Signal: {eth_signal.upper()} ({eth_strength})")
            logger.info(f"   Confidence: {eth_confidence:.2f}")
            logger.info(f"   RSI: {eth_indicators.rsi:.1f}")
            logger.info(f"   MACD: {eth_indicators.macd_line:.2f} / {eth_indicators.macd_signal:.2f}")
            logger.info(f"   Price vs SMA50: {((eth_current['price'] / eth_indicators.sma_50 - 1) * 100):+.1f}%")
            
            # Market momentum analysis
            btc_momentum = btc_current['percent_change_24h']
            eth_momentum = eth_current['percent_change_24h']
            
            logger.info(f"📈 Market Momentum:")
            logger.info(f"   BTC 24h: {btc_momentum:+.2f}%")
            logger.info(f"   ETH 24h: {eth_momentum:+.2f}%")
            
            # Enhanced decision logic
            should_trade = False
            trade_reason = ""
            
            # Strong bullish conditions for debt swap (DAI → ARB)
            if (btc_signal == "bullish" and eth_signal == "bullish" and 
                btc_confidence > 0.6 and eth_confidence > 0.6):
                should_trade = True
                trade_reason = "Strong bullish signals across major assets"
                
            # Oversold conditions with momentum
            elif (btc_indicators.rsi < 30 or eth_indicators.rsi < 30) and (btc_momentum > -5):
                should_trade = True
                trade_reason = "Oversold conditions with limited downside momentum"
                
            # MACD bullish crossover with confirming signals
            elif (btc_indicators.macd_histogram > 0 and eth_indicators.macd_histogram > 0 and
                  btc_confidence > 0.4 and eth_confidence > 0.4):
                should_trade = True
                trade_reason = "MACD bullish crossover with confirmation"
                
            # Moving average golden cross
            elif (btc_indicators.sma_50 > btc_indicators.sma_200 and 
                  eth_indicators.sma_50 > eth_indicators.sma_200 and
                  btc_current['price'] > btc_indicators.sma_50):
                should_trade = True
                trade_reason = "Golden cross pattern with price above key MA"
            
            logger.info(f"🎯 TRADE DECISION:")
            if should_trade:
                logger.info(f"   ✅ EXECUTE TRADE")
                logger.info(f"   📝 Reason: {trade_reason}")
                logger.info(f"   💪 Combined Confidence: {(btc_confidence + eth_confidence) / 2:.2f}")
            else:
                logger.info(f"   ❌ HOLD POSITION")
                logger.info(f"   📝 Reason: Market conditions not favorable for debt swap")
                logger.info(f"   ⚠️ Recommendation: Wait for stronger technical signals")
            
            return should_trade
            
        except Exception as e:
            logger.error(f"❌ Enhanced market analysis failed: {e}")
            return False
    
    def get_market_summary(self) -> Dict:
        """Get comprehensive market summary for dashboard display"""
        try:
            summary = {
                'btc_analysis': {},
                'eth_analysis': {},
                'market_sentiment': 'neutral',
                'recommendation': 'hold',
                'confidence': 0.0,
                'last_updated': time.time()
            }
            
            # Get current market data
            btc_current = self.cmc_client.get_current_price('BTC')
            eth_current = self.cmc_client.get_current_price('ETH')
            
            if btc_current:
                summary['btc_analysis'] = {
                    'price': btc_current['price'],
                    'change_24h': btc_current['percent_change_24h'],
                    'volume_24h': btc_current['volume_24h']
                }
            
            if eth_current:
                summary['eth_analysis'] = {
                    'price': eth_current['price'],
                    'change_24h': eth_current['percent_change_24h'],
                    'volume_24h': eth_current['volume_24h']
                }
            
            # Determine overall market sentiment
            if btc_current and eth_current:
                avg_change = (btc_current['percent_change_24h'] + eth_current['percent_change_24h']) / 2
                if avg_change > 5:
                    summary['market_sentiment'] = 'very_bullish'
                elif avg_change > 2:
                    summary['market_sentiment'] = 'bullish'
                elif avg_change < -5:
                    summary['market_sentiment'] = 'very_bearish'
                elif avg_change < -2:
                    summary['market_sentiment'] = 'bearish'
                else:
                    summary['market_sentiment'] = 'neutral'
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return {'error': str(e), 'last_updated': time.time()}

# Integration with existing market signal strategy
class EnhancedMarketSignalStrategy:
    """Enhanced market signal strategy with comprehensive technical analysis"""
    
    def __init__(self, agent):
        self.agent = agent
        self.analyzer = EnhancedMarketAnalyzer(agent)
        self.last_analysis_time = 0
        self.analysis_cooldown = 300  # 5 minutes
        
        logger.info("Enhanced Market Signal Strategy initialized")
    
    def should_execute_trade(self) -> bool:
        """Enhanced trade execution with comprehensive market analysis"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_analysis_time < self.analysis_cooldown:
            logger.info(f"⏰ Analysis in cooldown: {self.analysis_cooldown - (current_time - self.last_analysis_time):.0f}s remaining")
            return False
        
        try:
            should_trade = self.analyzer.should_execute_trade()
            self.last_analysis_time = current_time
            return should_trade
            
        except Exception as e:
            logger.error(f"Enhanced trade analysis failed: {e}")
            return False
    
    def get_market_status(self) -> Dict:
        """Get current market analysis status"""
        return self.analyzer.get_market_summary()

if __name__ == "__main__":
    # Test the enhanced analyzer
    class MockAgent:
        pass
    
    try:
        analyzer = EnhancedMarketAnalyzer(MockAgent())
        print("✅ Enhanced Market Analyzer initialized successfully")
        
        # Test market summary
        summary = analyzer.get_market_summary()
        print(f"📊 Market Summary: {summary}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
```
