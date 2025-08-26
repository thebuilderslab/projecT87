
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

class CoinGeckoAPI:
    """CoinGecko API client for fetching market data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'x-cg-pro-api-key': self.api_key,
            })
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price and basic metrics from CoinGecko"""
        try:
            # Map symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum', 
                'DAI': 'dai'
            }
            
            gecko_id = symbol_map.get(symbol.upper())
            if not gecko_id:
                logger.warning(f"Unknown symbol for CoinGecko: {symbol}")
                return None
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': gecko_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if gecko_id not in data:
                return None
            
            coin_data = data[gecko_id]
            
            return {
                'price': coin_data.get('usd', 0),
                'percent_change_1h': 0,  # CoinGecko simple API doesn't provide 1h change
                'percent_change_24h': coin_data.get('usd_24h_change', 0),
                'percent_change_7d': 0,  # Not available in simple API
                'volume_24h': coin_data.get('usd_24h_vol', 0),
                'market_cap': coin_data.get('usd_market_cap', 0)
            }
            
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                logger.warning(f"CoinGecko rate limit hit for {symbol}: {e}")
                raise requests.exceptions.HTTPError("Rate limit exceeded", response=e.response)
            logger.error(f"CoinGecko API error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected CoinGecko error for {symbol}: {e}")
            return None

class CoinAPIClient:
    """COIN_API client for fetching market data - Primary data source"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://rest.coinapi.io/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'X-CoinAPI-Key': self.api_key,
            'Accept': 'application/json'
        })
        
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price and metrics from COIN_API"""
        try:
            # Map symbols to COIN_API format
            symbol_map = {
                'BTC': 'BTC/USD',
                'ETH': 'ETH/USD',
                'DAI': 'DAI/USD',
                'ARB': 'ARB/USD'
            }
            
            coin_symbol = symbol_map.get(symbol.upper())
            if not coin_symbol:
                logger.warning(f"Unknown symbol for COIN_API: {symbol}")
                return None
            
            # Get current exchange rate
            url = f"{self.base_url}/exchangerate/{coin_symbol.replace('/', '/')}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            current_price = data.get('rate', 0)
            
            if current_price == 0:
                return None
            
            # Get historical data for percentage changes
            historical_url = f"{self.base_url}/ohlcv/{coin_symbol.replace('/', '')}/USD/history"
            params = {
                'period_id': '1DAY',
                'time_start': (datetime.now() - timedelta(days=7)).isoformat(),
                'limit': 7
            }
            
            hist_response = self.session.get(historical_url, params=params, timeout=30)
            
            # Calculate percentage changes
            percent_change_1h = 0
            percent_change_24h = 0
            percent_change_7d = 0
            volume_24h = 0
            
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                if len(hist_data) > 0:
                    latest = hist_data[-1]
                    if len(hist_data) > 1:
                        prev_24h = hist_data[-2]
                        percent_change_24h = ((current_price - prev_24h['price_close']) / prev_24h['price_close']) * 100
                    
                    if len(hist_data) >= 7:
                        prev_7d = hist_data[0]
                        percent_change_7d = ((current_price - prev_7d['price_close']) / prev_7d['price_close']) * 100
                    
                    volume_24h = latest.get('volume_traded', 0)
            
            return {
                'price': current_price,
                'percent_change_1h': percent_change_1h,
                'percent_change_24h': percent_change_24h,
                'percent_change_7d': percent_change_7d,
                'volume_24h': volume_24h,
                'market_cap': 0  # COIN_API doesn't provide market cap in basic plan
            }
            
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                logger.warning(f"COIN_API rate limit hit for {symbol}: {e}")
                raise requests.exceptions.HTTPError("Rate limit exceeded", response=e.response)
            logger.error(f"COIN_API error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected COIN_API error for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data from COIN_API"""
        try:
            symbol_map = {
                'BTC': 'BTC',
                'ETH': 'ETH', 
                'DAI': 'DAI',
                'ARB': 'ARB'
            }
            
            coin_symbol = symbol_map.get(symbol.upper())
            if not coin_symbol:
                return None
            
            url = f"{self.base_url}/ohlcv/{coin_symbol}/USD/history"
            params = {
                'period_id': '1DAY',
                'time_start': (datetime.now() - timedelta(days=days)).isoformat(),
                'limit': days
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return None
            
            # Convert to DataFrame
            df_data = []
            for item in data:
                df_data.append({
                    'timestamp': pd.to_datetime(item['time_period_start']),
                    'open': item['price_open'],
                    'high': item['price_high'],
                    'low': item['price_low'],
                    'close': item['price_close'],
                    'volume': item['volume_traded']
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Successfully fetched {len(df)} days of data for {symbol} from COIN_API")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol} from COIN_API: {e}")
            return None

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
            # Get current quote first for recent data
            url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol, 'convert': 'USD'}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'data' not in data or symbol not in data['data']:
                logger.warning(f"No data found for symbol {symbol}")
                return None
                
            quote_data = data['data'][symbol]['quote']['USD']
            
            # Create a simple DataFrame with current price
            # Note: CoinMarketCap historical API requires specific plan
            df = pd.DataFrame({
                'timestamp': [datetime.now()],
                'open': [quote_data['price']],
                'high': [quote_data['price']],
                'low': [quote_data['price']],
                'close': [quote_data['price']],
                'volume': [quote_data.get('volume_24h', 0)]
            })
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Successfully fetched current data for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price and basic metrics"""
        try:
            url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol, 'convert': 'USD'}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'data' not in data or symbol not in data['data']:
                return None
                
            quote_data = data['data'][symbol]['quote']['USD']
            
            return {
                'price': quote_data['price'],
                'percent_change_1h': quote_data.get('percent_change_1h', 0),
                'percent_change_24h': quote_data.get('percent_change_24h', 0),
                'percent_change_7d': quote_data.get('percent_change_7d', 0),
                'volume_24h': quote_data.get('volume_24h', 0),
                'market_cap': quote_data.get('market_cap', 0)
            }
            
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None

class TechnicalAnalysis:
    """Technical analysis calculations"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            if len(prices) < period + 1:
                return 50.0  # Neutral RSI if insufficient data
                
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        except:
            return 50.0
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD"""
        try:
            if len(prices) < slow + signal:
                return 0.0, 0.0, 0.0
                
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return (
                float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
                float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
                float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
            )
        except:
            return 0.0, 0.0, 0.0
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average"""
        try:
            if len(prices) < period:
                return float(prices.mean()) if len(prices) > 0 else 0.0
                
            sma = prices.rolling(window=period).mean()
            return float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else 0.0
        except:
            return 0.0
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        try:
            if len(prices) < period:
                mean_price = float(prices.mean()) if len(prices) > 0 else 0.0
                return mean_price, mean_price
                
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return (
                float(upper_band.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) else 0.0,
                float(lower_band.iloc[-1]) if not pd.isna(lower_band.iloc[-1]) else 0.0
            )
        except:
            return 0.0, 0.0

class EnhancedMarketAnalyzer:
    """Enhanced market analyzer with comprehensive technical analysis"""
    
    def __init__(self, agent):
        self.agent = agent
        
        # Initialize COIN_API (primary)
        self.coin_api_key = os.getenv('COIN_API')
        if not self.coin_api_key:
            logger.error("COIN_API key not found in environment variables")
            self.coin_api_client = None
        else:
            self.coin_api_client = CoinAPIClient(self.coin_api_key)
            logger.info("COIN_API client initialized successfully")
        
        # Initialize CoinGecko API (secondary fallback)
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        self.coingecko_client = CoinGeckoAPI(self.coingecko_api_key)
        
        # Initialize CoinMarketCap API (tertiary fallback)
        self.coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY')
        if not self.coinmarketcap_api_key:
            logger.warning("COINMARKETCAP_API_KEY not found - tertiary fallback unavailable")
            self.cmc_client = None
        else:
            self.cmc_client = CoinMarketCapAPI(self.coinmarketcap_api_key)
        
        self.technical_analysis = TechnicalAnalysis()
        
        # Cache for historical data
        self.data_cache = {}
        self.cache_timeout = 3600  # 1 hour
        
        logger.info("Enhanced Market Analyzer initialized with COIN_API primary, CoinGecko secondary, and CoinMarketCap tertiary fallback")
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """Get current prices using COIN_API primary, with CoinGecko and CoinMarketCap fallbacks"""
        results = {}
        
        for symbol in symbols:
            try:
                # Primary: Try COIN_API first
                if self.coin_api_client:
                    logger.info(f"Fetching {symbol} price from COIN_API (primary)")
                    price_data = self.coin_api_client.get_current_price(symbol)
                    
                    if price_data:
                        logger.info(f"✅ COIN_API: {symbol} = ${price_data['price']:.2f}")
                        results[symbol] = price_data
                        continue
                else:
                    logger.warning(f"⚠️ COIN_API client not available for {symbol}")
                    
            except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response.status_code == 429:
                    logger.warning(f"⚠️ COIN_API rate limit hit for {symbol}, switching to fallback")
                else:
                    logger.warning(f"⚠️ COIN_API error for {symbol}: {e}")
            except Exception as e:
                logger.warning(f"⚠️ COIN_API unexpected error for {symbol}: {e}")
            
            # Secondary Fallback: Try CoinGecko
            try:
                logger.info(f"Fetching {symbol} price from CoinGecko (secondary fallback)")
                price_data = self.coingecko_client.get_current_price(symbol)
                
                if price_data:
                    logger.info(f"✅ CoinGecko: {symbol} = ${price_data['price']:.2f}")
                    results[symbol] = price_data
                    continue
                    
            except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response.status_code == 429:
                    logger.warning(f"⚠️ CoinGecko rate limit hit for {symbol}, switching to tertiary fallback")
                else:
                    logger.warning(f"⚠️ CoinGecko API error for {symbol}: {e}")
            except Exception as e:
                logger.warning(f"⚠️ CoinGecko unexpected error for {symbol}: {e}")
            
            # Tertiary Fallback: Try CoinMarketCap
            if self.cmc_client:
                try:
                    logger.info(f"Fetching {symbol} price from CoinMarketCap (tertiary fallback)")
                    price_data = self.cmc_client.get_current_price(symbol)
                    
                    if price_data:
                        logger.info(f"✅ CoinMarketCap: {symbol} = ${price_data['price']:.2f}")
                        results[symbol] = price_data
                        continue
                        
                except Exception as e:
                    logger.error(f"❌ CoinMarketCap tertiary fallback failed for {symbol}: {e}")
            else:
                logger.error(f"❌ CoinMarketCap tertiary fallback not available for {symbol}")
            
            # All APIs failed
            logger.critical(f"🚨 CRITICAL: No market data could be fetched for {symbol} from any source")
            results[symbol] = None
        
        return results
    
    def get_cached_data(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Get cached historical data or fetch new data"""
        cache_key = f"{symbol}_{days}"
        current_time = time.time()
        
        if cache_key in self.data_cache:
            cached_data, timestamp = self.data_cache[cache_key]
            if current_time - timestamp < self.cache_timeout:
                return cached_data
        
        # Fetch new data - try COIN_API first, then CoinMarketCap fallback
        data = None
        
        # Primary: Try COIN_API
        if self.coin_api_client:
            try:
                data = self.coin_api_client.get_historical_data(symbol, days)
                if data is not None:
                    logger.info(f"Successfully fetched historical data for {symbol} from COIN_API")
            except Exception as e:
                logger.warning(f"COIN_API historical data failed for {symbol}: {e}")
        
        # Fallback: Try CoinMarketCap if COIN_API failed
        if data is None and self.cmc_client:
            try:
                data = self.cmc_client.get_historical_data(symbol, days)
                if data is not None:
                    logger.info(f"Successfully fetched historical data for {symbol} from CoinMarketCap fallback")
            except Exception as e:
                logger.warning(f"CoinMarketCap historical data fallback failed for {symbol}: {e}")
        
        if data is not None:
            self.data_cache[cache_key] = (data, current_time)
        
        return data
    
    def calculate_indicators(self, data: pd.DataFrame) -> Optional[TechnicalIndicators]:
        """Calculate all technical indicators for the given data"""
        try:
            if data is None or len(data) == 0:
                return None
                
            prices = data['close']
            volume = data['volume']
            
            # Calculate all indicators
            rsi = self.technical_analysis.calculate_rsi(prices)
            macd_line, macd_signal, macd_histogram = self.technical_analysis.calculate_macd(prices)
            
            sma_9 = self.technical_analysis.calculate_sma(prices, 9)
            sma_50 = self.technical_analysis.calculate_sma(prices, 50)
            sma_100 = self.technical_analysis.calculate_sma(prices, 100)
            sma_200 = self.technical_analysis.calculate_sma(prices, 200)
            
            bollinger_upper, bollinger_lower = self.technical_analysis.calculate_bollinger_bands(prices)
            volume_sma = self.technical_analysis.calculate_sma(volume, 20)
            
            return TechnicalIndicators(
                rsi=rsi,
                macd_line=macd_line,
                macd_signal=macd_signal,
                macd_histogram=macd_histogram,
                sma_9=sma_9,
                sma_50=sma_50,
                sma_100=sma_100,
                sma_200=sma_200,
                bollinger_upper=bollinger_upper,
                bollinger_lower=bollinger_lower,
                volume_sma=volume_sma
            )
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None
    
    def analyze_market_signal(self, symbol: str) -> Optional[MarketSignal]:
        """Analyze market signal for a given symbol"""
        try:
            # Get historical data
            data = self.get_cached_data(symbol)
            if data is None:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Calculate indicators
            indicators = self.calculate_indicators(data)
            if indicators is None:
                return None
            
            # Determine signal based on indicators
            signal_score = 0
            signals = []
            
            # RSI analysis
            if indicators.rsi < 30:
                signal_score += 1
                signals.append("RSI oversold (bullish)")
            elif indicators.rsi > 70:
                signal_score -= 1
                signals.append("RSI overbought (bearish)")
            
            # MACD analysis
            if indicators.macd_line > indicators.macd_signal:
                signal_score += 1
                signals.append("MACD bullish crossover")
            else:
                signal_score -= 1
                signals.append("MACD bearish crossover")
            
            # Moving average analysis
            current_price = data['close'].iloc[-1]
            if current_price > indicators.sma_50:
                signal_score += 1
                signals.append("Above 50-day MA (bullish)")
            else:
                signal_score -= 1
                signals.append("Below 50-day MA (bearish)")
            
            # Determine overall signal
            if signal_score >= 2:
                signal_type = "bullish"
                strength = "strong" if signal_score >= 3 else "moderate"
                recommendation = "BUY"
            elif signal_score <= -2:
                signal_type = "bearish"
                strength = "strong" if signal_score <= -3 else "moderate"
                recommendation = "SELL"
            else:
                signal_type = "neutral"
                strength = "weak"
                recommendation = "HOLD"
            
            confidence = min(abs(signal_score) / 3.0, 1.0)
            
            return MarketSignal(
                signal_type=signal_type,
                confidence=confidence,
                strength=strength,
                indicators=indicators,
                recommendation=recommendation,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market signal for {symbol}: {e}")
            return None
    
    def get_market_summary(self) -> Dict:
        """Get comprehensive market summary using dual API strategy"""
        try:
            summary = {
                'timestamp': time.time(),
                'btc_analysis': {},
                'eth_analysis': {},
                'dai_analysis': {},
                'arb_analysis': {},
                'market_sentiment': 'neutral',
                'data_source': 'coin_api_primary'  # Track which APIs were used
            }
            
            # Analyze major cryptocurrencies using COIN_API strategy
            symbols = ['BTC', 'ETH', 'DAI', 'ARB']
            current_prices = self.get_current_prices(symbols)
            
            for symbol in symbols:
                try:
                    current_data = current_prices.get(symbol)
                    if current_data:
                        signal = self.analyze_market_signal(symbol)
                        
                        analysis = {
                            'price': current_data['price'],
                            'change_1h': current_data['percent_change_1h'],
                            'change_24h': current_data['percent_change_24h'],
                            'change_7d': current_data['percent_change_7d'],
                            'volume_24h': current_data['volume_24h'],
                            'signal': signal.signal_type if signal else 'unknown',
                            'confidence': signal.confidence if signal else 0.0,
                            'recommendation': signal.recommendation if signal else 'HOLD'
                        }
                        
                        summary[f'{symbol.lower()}_analysis'] = analysis
                    else:
                        logger.error(f"No price data available for {symbol}")
                        summary[f'{symbol.lower()}_analysis'] = {'error': 'No data available'}
                        
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    summary[f'{symbol.lower()}_analysis'] = {'error': str(e)}
            
            # Determine overall market sentiment
            bullish_count = sum(1 for k, v in summary.items() 
                              if k.endswith('_analysis') and v.get('signal') == 'bullish')
            bearish_count = sum(1 for k, v in summary.items() 
                              if k.endswith('_analysis') and v.get('signal') == 'bearish')
            
            if bullish_count > bearish_count:
                summary['market_sentiment'] = 'bullish'
            elif bearish_count > bullish_count:
                summary['market_sentiment'] = 'bearish'
            else:
                summary['market_sentiment'] = 'neutral'
            
            logger.info("Market summary generated successfully with COIN_API primary strategy")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return {'error': str(e), 'timestamp': time.time()}

class EnhancedMarketSignalStrategy:
    """Enhanced market signal strategy for debt swap decisions"""
    
    def __init__(self, agent):
        self.agent = agent
        try:
            self.analyzer = EnhancedMarketAnalyzer(agent)
            self.initialized = True
            logger.info("Enhanced Market Signal Strategy initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Market Signal Strategy: {e}")
            self.initialized = False
    
    def should_execute_trade(self) -> bool:
        """Determine if a trade should be executed based on market analysis"""
        if not self.initialized:
            logger.warning("Market signal strategy not initialized, defaulting to False")
            return False
        
        try:
            # Get market summary
            summary = self.analyzer.get_market_summary()
            
            if 'error' in summary:
                logger.error(f"Market analysis error: {summary['error']}")
                return False
            
            # Conservative trading logic
            btc_signal = summary.get('btc_analysis', {}).get('signal', 'neutral')
            eth_signal = summary.get('eth_analysis', {}).get('signal', 'neutral')
            market_sentiment = summary.get('market_sentiment', 'neutral')
            
            # Only execute trades in strong bullish conditions
            if (btc_signal == 'bullish' and 
                eth_signal == 'bullish' and 
                market_sentiment == 'bullish'):
                
                btc_confidence = summary.get('btc_analysis', {}).get('confidence', 0.0)
                eth_confidence = summary.get('eth_analysis', {}).get('confidence', 0.0)
                
                # Require high confidence
                if btc_confidence > 0.7 and eth_confidence > 0.7:
                    logger.info("Strong bullish signal detected - recommending trade execution")
                    return True
            
            logger.info(f"Market conditions not favorable for trading: BTC={btc_signal}, ETH={eth_signal}, Sentiment={market_sentiment}")
            return False
            
        except Exception as e:
            logger.error(f"Error in trade decision analysis: {e}")
            return False
    
    def get_strategy_status(self) -> Dict:
        """Get current strategy status"""
        return {
            'initialized': self.initialized,
            'strategy_name': 'Enhanced CoinMarketCap Strategy',
            'last_update': time.time(),
            'api_key_present': bool(os.getenv('COINMARKETCAP_API_KEY'))
        }

# Test functionality
def test_enhanced_market_analyzer():
    """Test the enhanced market analyzer"""
    try:
        print("🧪 Testing Enhanced Market Analyzer with CoinGecko + CoinMarketCap APIs")
        print("=" * 60)
        
        # Check API keys
        coingecko_key = os.getenv('COINGECKO_API_KEY')
        coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
        
        if coingecko_key:
            print(f"✅ CoinGecko API Key found: {coingecko_key[:8]}...")
        else:
            print("⚠️ COINGECKO_API_KEY not found - using free tier")
        
        if coinmarketcap_key:
            print(f"✅ CoinMarketCap API Key found: {coinmarketcap_key[:8]}...")
        else:
            print("❌ COINMARKETCAP_API_KEY not found - fallback unavailable")
        
        # Create mock agent
        class MockAgent:
            def __init__(self):
                self.address = "0x1234...5678"
        
        # Test analyzer
        agent = MockAgent()
        analyzer = EnhancedMarketAnalyzer(agent)
        print("✅ Enhanced Market Analyzer initialized")
        
        # Test market summary
        print("📊 Testing market summary...")
        summary = analyzer.get_market_summary()
        
        if 'error' not in summary:
            print("✅ Market summary generated successfully")
            print(f"📈 Market sentiment: {summary.get('market_sentiment', 'unknown')}")
            
            if 'btc_analysis' in summary:
                btc = summary['btc_analysis']
                if 'price' in btc:
                    print(f"₿ BTC: ${btc['price']:.2f} ({btc.get('change_24h', 0):.2f}% 24h)")
                    
            if 'eth_analysis' in summary:
                eth = summary['eth_analysis']
                if 'price' in eth:
                    print(f"Ξ ETH: ${eth['price']:.2f} ({eth.get('change_24h', 0):.2f}% 24h)")
        else:
            print(f"❌ Market summary failed: {summary['error']}")
            return False
        
        # Test strategy
        strategy = EnhancedMarketSignalStrategy(agent)
        print("✅ Enhanced Market Signal Strategy initialized")
        
        trade_decision = strategy.should_execute_trade()
        print(f"🎯 Trade recommendation: {'EXECUTE' if trade_decision else 'HOLD'}")
        
        print("\n🎉 Enhanced Market Analyzer test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_enhanced_market_analyzer()
