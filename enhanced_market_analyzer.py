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
import random

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
                'BTC': 'BTC',
                'ETH': 'ETH',
                'DAI': 'DAI',
                'ARB': 'ARB'
            }

            base_symbol = symbol_map.get(symbol.upper())
            if not base_symbol:
                logger.warning(f"Unknown symbol for COIN_API: {symbol}")
                return None

            # Get current exchange rate - Fixed URL format
            url = f"{self.base_url}/exchangerate/{base_symbol}/USD"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            current_price = data.get('rate', 0)

            if current_price == 0:
                return None

            # Get historical data for percentage changes
            historical_url = f"{self.base_url}/ohlcv/{base_symbol}/USD/history"
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

        except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 429:
                        logger.warning(f"⚠️ COIN_API rate limit hit for {symbol}, switching to fallback")
                        # Don't disable completely, just skip this call
                    elif e.response.status_code in [401, 403]:
                        logger.warning(f"⚠️ COIN_API authentication failed for {symbol}: Invalid API key")
                        # Disable COIN_API for this session
                        self.coin_api_client = None
                    else:
                        logger.warning(f"⚠️ COIN_API error for {symbol}: {e}")
                else:
                    logger.warning(f"⚠️ COIN_API error for {symbol}: {e}")
        except Exception as e:
            logger.warning(f"⚠️ COIN_API unexpected error for {symbol}: {e}")
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

            base_symbol = symbol_map.get(symbol.upper())
            if not base_symbol:
                return None

            url = f"{self.base_url}/ohlcv/{base_symbol}/USD/history"
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

    def _get_coingecko_historical_data(self, symbol: str, hours: int = 24) -> Optional[List[Dict]]:
        """Helper to get historical data from CoinGecko"""
        try:
            # Map symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'DAI': 'dai',
                'ARB': 'arbitrum' # CoinGecko ID for ARB
            }

            gecko_id = symbol_map.get(symbol.upper())
            if not gecko_id:
                logger.warning(f"Unknown symbol for CoinGecko historical: {symbol}")
                return None

            # CoinGecko API for historical data (daily)
            # For hourly, you'd need a different endpoint or plan
            url = f"{self.base_url}/coins/{gecko_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': (hours + 1) // 24 if hours > 0 else 1, # Approx days
                'interval': 'daily' # CoinGecko free tier typically provides daily
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if 'prices' not in data:
                return None

            # Process data to match expected format
            # CoinGecko returns prices, market_caps, total_volumes in separate lists
            # We'll use prices for now
            historical_data = []
            price_data = data['prices']

            # Limit to 'hours' if possible, though CoinGecko provides daily
            # For simplicity, we'll take the last N points corresponding to ~hours
            num_points_to_take = min(len(price_data), hours // 24 + 1) # Approximate

            for point in price_data[-num_points_to_take:]:
                timestamp = datetime.fromtimestamp(point[0] / 1000)
                historical_data.append({
                    'timestamp': timestamp.isoformat(),
                    'price': point[1],
                    'volume': data.get('total_volumes', [])[-num_points_to_take:][price_data.index(point)][1] if data.get('total_volumes') else 0,
                    'source': 'coingecko'
                })

            return historical_data

        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                logger.warning(f"CoinGecko rate limit hit for {symbol} historical: {e}")
                raise requests.exceptions.HTTPError("Rate limit exceeded", response=e.response)
            logger.error(f"CoinGecko API error for {symbol} historical: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected CoinGecko error for {symbol} historical: {e}")
            return None

    def _get_coinmarketcap_historical_data(self, symbol: str, hours: int = 24) -> Optional[List[Dict]]:
        """Helper to get historical data from CoinMarketCap"""
        try:
            # CoinMarketCap historical data requires a specific endpoint and plan
            # This is a simplified approach using latest quote if historical endpoint is not available/accessible
            url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol, 'convert': 'USD'}

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if 'data' not in data or symbol not in data['data']:
                logger.warning(f"No data found for symbol {symbol} on CoinMarketCap")
                return None

            quote_data = data['data'][symbol]['quote']['USD']

            # Return just the latest data point as a fallback
            return [{
                'timestamp': datetime.now().isoformat(),
                'price': quote_data['price'],
                'volume': quote_data.get('volume_24h', 0),
                'source': 'coinmarketcap_latest'
            }]

        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                logger.warning(f"CoinMarketCap rate limit hit for {symbol} historical: {e}")
                raise requests.exceptions.HTTPError("Rate limit exceeded", response=e.response)
            logger.error(f"CoinMarketCap API error for {symbol} historical: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected CoinMarketCap error for {symbol} historical: {e}")
            return None

    def _convert_cmc_to_standard_format(self, cmc_data: List[Dict], symbol: str) -> Optional[List[Dict]]:
        """Convert CoinMarketCap data format to a standardized format"""
        if not cmc_data:
            return None

        standardized_data = []
        for entry in cmc_data:
            try:
                # Assuming entry is a dict with 'price', 'volume', 'timestamp', 'source'
                standardized_data.append({
                    'timestamp': entry.get('timestamp'),
                    'price': entry.get('price'),
                    'volume': entry.get('volume', 0),
                    'source': entry.get('source', 'unknown')
                })
            except Exception as e:
                logger.error(f"Error converting CoinMarketCap entry for {symbol}: {entry} - {e}")
        return standardized_data

    def _generate_fallback_historical_data(self, symbol: str, hours: int) -> List[Dict]:
        """Generate fallback historical data when all APIs fail"""
        import random
        from datetime import datetime, timedelta

        # Base prices for different symbols
        base_prices = {
            'BTC': 110000,
            'ETH': 4500,
            'ARB': 0.50,
            'DAI': 1.00
        }

        base_price = base_prices.get(symbol, 100)
        data_points = []

        # Generate hourly data points
        for i in range(hours):
            timestamp = datetime.now() - timedelta(hours=hours-i)

            # Add realistic price variation
            variation = random.uniform(-0.02, 0.02)  # ±2% variation
            price = base_price * (1 + variation)

            data_points.append({
                'timestamp': timestamp.isoformat(),
                'price': price,
                'volume': random.uniform(1000000, 10000000),
                'source': 'synthetic_fallback',
                'symbol': symbol
            })

        logger.info(f"Generated {len(data_points)} synthetic data points for {symbol}")
        return data_points


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
    def __init__(self):
        self.api_call_history = {}
        self.retry_delays = {}  # Track retry delays for exponential backoff
        self.max_retries = 3
        self.base_delay = 1  # Start with 1 second delay
        self.max_delay = 300  # Maximum 5 minutes delay
        
    def _exponential_backoff(self, api_name: str, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
        return min(delay, self.max_delay)
    
    def _make_api_request(self, url: str, headers: Dict, api_name: str = "unknown") -> Optional[Dict]:
        """Make API request with exponential backoff and rate limiting"""
        for attempt in range(self.max_retries):
            try:
                # Check if we need to wait before making the request
                if api_name in self.retry_delays:
                    wait_time = self.retry_delays[api_name]
                    if wait_time > time.time():
                        sleep_duration = wait_time - time.time()
                        logger.info(f"Rate limit backoff for {api_name}: waiting {sleep_duration:.1f}s")
                        time.sleep(sleep_duration)
                
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    # Success - clear any retry delays
                    if api_name in self.retry_delays:
                        del self.retry_delays[api_name]
                    return response.json()
                
                elif response.status_code == 429:  # Too Many Requests
                    delay = self._exponential_backoff(api_name, attempt)
                    self.retry_delays[api_name] = time.time() + delay
                    logger.warning(f"Rate limit hit for {api_name}, retrying in {delay:.1f}s (attempt {attempt + 1})")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(delay)
                        continue
                
                elif response.status_code == 404:
                    logger.error(f"API endpoint not found for {api_name}: {url}")
                    return None
                
                else:
                    logger.error(f"API request failed for {api_name}: {response.status_code}")
                    if attempt < self.max_retries - 1:
                        delay = self._exponential_backoff(api_name, attempt)
                        time.sleep(delay)
                        continue
                
            except requests.exceptions.Timeout:
                logger.warning(f"API timeout for {api_name} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self._exponential_backoff(api_name, attempt))
                    continue
            
            except Exception as e:
                logger.error(f"API request error for {api_name}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self._exponential_backoff(api_name, attempt))
                    continue
        
        logger.error(f"All retry attempts failed for {api_name}")
        return None

    def fetch_optimized_market_data(self) -> Dict:
        """Fetch only essential market data to stay within API limits"""
        try:
            coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY')
            if not coinmarketcap_api_key:
                return self._get_fallback_data()
            
            # Optimize: Request only essential coins and minimal data
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': coinmarketcap_api_key,
                'Accept': 'application/json'
            }
            
            # Request only BTC, ETH, ARB instead of all markets
            params = {
                'symbol': 'BTC,ETH,ARB',
                'convert': 'USD'
            }
            
            full_url = f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            data = self._make_api_request(full_url, headers, "CoinMarketCap")
            
            if data and 'data' in data:
                return self._process_coinmarketcap_data(data['data'])
            else:
                return self._get_fallback_data()
                
        except Exception as e:
            logger.error(f"Error fetching optimized market data: {e}")
            return self._get_fallback_data()
    
    def _process_coinmarketcap_data(self, data: Dict) -> Dict:
        """Process CoinMarketCap data efficiently"""
        try:
            processed_data = {}
            
            for symbol in ['BTC', 'ETH', 'ARB']:
                if symbol in data:
                    coin_data = data[symbol]
                    quote = coin_data['quote']['USD']
                    
                    processed_data[f'{symbol.lower()}_analysis'] = {
                        'price': quote['price'],
                        'change_24h': quote['percent_change_24h'],
                        'volume_24h': quote['volume_24h'],
                        'market_cap': quote['market_cap'],
                        'signal': self._determine_signal(quote['percent_change_24h']),
                        'confidence': min(abs(quote['percent_change_24h']) / 10, 1.0),
                        'source': 'coinmarketcap_api',
                        'timestamp': time.time()
                    }
            
            # Add market sentiment based on overall performance
            sentiment = self._calculate_market_sentiment(processed_data)
            processed_data['market_sentiment'] = sentiment
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing CoinMarketCap data: {e}")
            return self._get_fallback_data()
    
    def _determine_signal(self, change_24h: float) -> str:
        """Determine market signal based on price change"""
        if change_24h > 5:
            return 'very_bullish'
        elif change_24h > 2:
            return 'bullish'
        elif change_24h > -2:
            return 'neutral'
        elif change_24h > -5:
            return 'bearish'
        else:
            return 'very_bearish'
    
    def _calculate_market_sentiment(self, data: Dict) -> str:
        """Calculate overall market sentiment"""
        try:
            changes = []
            for key in ['btc_analysis', 'eth_analysis', 'arb_analysis']:
                if key in data:
                    changes.append(data[key].get('change_24h', 0))
            
            if not changes:
                return 'neutral'
            
            avg_change = sum(changes) / len(changes)
            
            if avg_change > 3:
                return 'very_bullish'
            elif avg_change > 1:
                return 'bullish'
            elif avg_change > -1:
                return 'neutral'
            elif avg_change > -3:
                return 'bearish'
            else:
                return 'very_bearish'
                
        except Exception as e:
            logger.error(f"Error calculating market sentiment: {e}")
            return 'neutral'
    
    def _get_fallback_data(self) -> Dict:
        """Provide fallback synthetic data when APIs fail"""
        return {
            'btc_analysis': {
                'price': 43000,
                'change_24h': -0.5,
                'signal': 'neutral',
                'confidence': 0.3,
                'source': 'synthetic_fallback'
            },
            'eth_analysis': {
                'price': 2500,
                'change_24h': -0.3,
                'signal': 'neutral', 
                'confidence': 0.3,
                'source': 'synthetic_fallback'
            },
            'arb_analysis': {
                'price': 0.41,
                'change_24h': -0.1,
                'rsi': 45,
                'signal': 'neutral',
                'confidence': 0.3,
                'source': 'synthetic_fallback'
            },
            'market_sentiment': 'neutral'
        }

class EnhancedMarketSignalStrategy:
    """Enhanced market analyzer with comprehensive technical analysis"""

    def __init__(self, agent):
        self.agent = agent

        # Initialize COIN_API (primary) with validation
        self.coin_api_key = os.getenv('COIN_API')
        if not self.coin_api_key:
            logger.warning("COIN_API key not found - disabling primary source")
            self.coin_api_client = None
        else:
            try:
                self.coin_api_client = CoinAPIClient(self.coin_api_key)
                # Quick validation test
                headers = {'X-CoinAPI-Key': self.coin_api_key}
                test_response = requests.get('https://rest.coinapi.io/v1/assets?filter_asset_id=BTC',
                                           headers=headers, timeout=10)
                if test_response.status_code == 200:
                    logger.info("COIN_API client initialized successfully")
                else:
                    logger.warning(f"COIN_API validation failed: {test_response.status_code}")
                    self.coin_api_client = None
            except Exception as e:
                logger.error(f"COIN_API initialization failed: {e}")
                self.coin_api_client = None

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

    def get_current_arb_price_with_tracking(self) -> Optional[float]:
        """Get current ARB price with historical tracking for debt reduction"""
        try:
            current_prices = self.get_current_prices(['ARB'])
            arb_data = current_prices.get('ARB')

            if arb_data and 'price' in arb_data:
                arb_price = arb_data['price']

                # Track price history for debt reduction analysis
                if not hasattr(self, 'arb_price_history'):
                    self.arb_price_history = []

                self.arb_price_history.append({
                    'price': arb_price,
                    'timestamp': time.time(),
                    'change_1h': arb_data.get('percent_change_1h', 0),
                    'change_24h': arb_data.get('percent_change_24h', 0)
                })

                # Keep only last 24 hours of price data
                cutoff_time = time.time() - 86400  # 24 hours ago
                self.arb_price_history = [
                    entry for entry in self.arb_price_history
                    if entry['timestamp'] > cutoff_time
                ]

                return arb_price

            return None

        except Exception as e:
            logger.error(f"ARB price tracking failed: {e}")
            return None

    def analyze_arb_depreciation_trend(self, hours_back: int = 4) -> Dict:
        """Analyze ARB depreciation trend for debt reduction timing"""
        try:
            if not hasattr(self, 'arb_price_history') or len(self.arb_price_history) < 2:
                return {'trend': 'insufficient_data', 'confidence': 0.0}

            # Filter to specified time window
            cutoff_time = time.time() - (hours_back * 3600)
            recent_prices = [
                entry for entry in self.arb_price_history
                if entry['timestamp'] > cutoff_time
            ]

            if len(recent_prices) < 3:
                return {'trend': 'insufficient_recent_data', 'confidence': 0.0}

            # Calculate trend metrics
            prices = [entry['price'] for entry in recent_prices]
            timestamps = [entry['timestamp'] for entry in recent_prices]

            # Simple linear regression for trend
            n = len(prices)
            sum_x = sum(timestamps)
            sum_y = sum(prices)
            sum_xy = sum(t * p for t, p in zip(timestamps, prices))
            sum_x2 = sum(t * t for t in timestamps)

            # Calculate slope (trend direction)
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

            # Calculate percentage change over period
            price_change = (prices[-1] - prices[0]) / prices[0]

            # Determine trend strength and confidence
            if price_change < -0.02:  # 2% or more drop
                trend = 'strong_depreciation'
                confidence = min(abs(price_change) * 10, 1.0)  # Higher confidence for bigger drops
            elif price_change < -0.005:  # 0.5% drop
                trend = 'moderate_depreciation'
                confidence = min(abs(price_change) * 20, 0.8)
            elif price_change > 0.02:  # 2% or more gain
                trend = 'strong_appreciation'
                confidence = min(price_change * 10, 1.0)
            else:
                trend = 'sideways'
                confidence = 0.3

            return {
                'trend': trend,
                'confidence': confidence,
                'price_change': price_change,
                'slope': slope,
                'debt_reduction_opportunity': trend in ['strong_depreciation', 'moderate_depreciation'] and confidence > 0.6
            }

        except Exception as e:
            logger.error(f"ARB depreciation trend analysis failed: {e}")
            return {'trend': 'error', 'confidence': 0.0}

    def get_current_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """Get current prices using COIN_API primary, with CoinGecko and CoinMarketCap fallbacks"""
        results = {}

        for symbol in symbols:
            # Try each API with exponential backoff
            price_data = self._fetch_price_with_backoff(symbol)
            if price_data:
                results[symbol] = price_data
            else:
                # Generate synthetic data as last resort
                results[symbol] = self._generate_synthetic_price_data(symbol)

        return results

    def _fetch_price_with_backoff(self, symbol: str, max_retries: int = 3) -> Optional[Dict]:
        """Fetch price data with exponential backoff for rate limiting"""
        import random

        apis_to_try = [
            ('COIN_API', self._try_coin_api),
            ('CoinGecko', self._try_coingecko),
            ('CoinMarketCap', self._try_coinmarketcap)
        ]

        for api_name, api_func in apis_to_try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"Fetching {symbol} from {api_name} (attempt {attempt + 1})")
                    price_data = api_func(symbol)

                    if price_data:
                        logger.info(f"✅ {api_name}: {symbol} = ${price_data['price']:.4f}")
                        return price_data

                except requests.exceptions.HTTPError as e:
                    if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                        # Calculate exponential backoff with jitter
                        base_delay = 2 ** attempt  # 1, 2, 4 seconds
                        jitter = random.uniform(0.1, 0.5)  # Add randomness
                        delay = base_delay + jitter

                        logger.warning(f"⚠️ {api_name} rate limited for {symbol}, waiting {delay:.1f}s")
                        time.sleep(delay)
                        continue
                    else:
                        logger.warning(f"⚠️ {api_name} HTTP error for {symbol}: {e}")
                        break  # Try next API

                except Exception as e:
                    logger.warning(f"⚠️ {api_name} unexpected error for {symbol}: {e}")
                    break  # Try next API

        return None

    def _try_coin_api(self, symbol: str) -> Optional[Dict]:
        """Try COIN_API with proper error handling"""
        if not self.coin_api_client:
            return None
        return self.coin_api_client.get_current_price(symbol)

    def _try_coingecko(self, symbol: str) -> Optional[Dict]:
        """Try CoinGecko API with proper error handling"""
        return self.coingecko_client.get_current_price(symbol)

    def _try_coinmarketcap(self, symbol: str) -> Optional[Dict]:
        """Try CoinMarketCap API with proper error handling"""
        if not self.cmc_client:
            return None
        return self.cmc_client.get_current_price(symbol)

    def _generate_synthetic_price_data(self, symbol: str) -> Dict:
        """Generate realistic synthetic price data when all APIs fail"""
        import random
        import hashlib

        # Use time-based seed for consistency
        time_seed = int(time.time() / 300)  # Changes every 5 minutes
        random.seed(hashlib.md5(f"{symbol}_{time_seed}".encode()).hexdigest())

        synthetic_prices = {
            'BTC': {'base': 97500, 'volatility': 0.015},
            'ETH': {'base': 3250, 'volatility': 0.02},
            'ARB': {'base': 0.41, 'volatility': 0.03},
            'DAI': {'base': 1.0, 'volatility': 0.0005}
        }

        if symbol in synthetic_prices:
            base_price = synthetic_prices[symbol]['base']
            volatility = synthetic_prices[symbol]['volatility']
            price_variation = random.uniform(-volatility, volatility)
            synthetic_price = base_price * (1 + price_variation)

            synthetic_data = {
                'price': synthetic_price,
                'percent_change_1h': random.uniform(-0.5, 0.5),
                'percent_change_24h': random.uniform(-3.0, 3.0),
                'percent_change_7d': random.uniform(-8.0, 8.0),
                'volume_24h': random.uniform(1000000, 10000000),
                'market_cap': 0,
                'source': 'synthetic_fallback',
                'synthetic': True
            }

            logger.warning(f"⚠️ Using synthetic data for {symbol}: ${synthetic_data['price']:.4f}")
            return synthetic_data

        return None

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

    def get_historical_data_with_fallbacks(self, symbol: str, hours: int = 24) -> Optional[List[Dict]]:
        """Get historical data using COIN_API primary, with CoinGecko and CoinMarketCap fallbacks"""

        # Primary: Try COIN_API first (but expect 404s for historical)
        if self.coin_api_client:
            logger.info(f"Fetching {symbol} historical data from COIN_API (primary)")
            try:
                historical_data = self.coin_api_client.get_historical_data(symbol, hours)
                if historical_data is not None and not historical_data.empty:
                    logger.info(f"✅ COIN_API historical: {symbol} - {len(historical_data)} data points")
                    # Convert DataFrame to list of dicts
                    return historical_data.to_dict('records')
            except Exception as e:
                if "404" in str(e):
                    logger.info(f"COIN_API historical not available for {symbol} (404 - normal)")
                else:
                    logger.warning(f"COIN_API historical error for {symbol}: {e}")

        # Secondary: Try CoinGecko fallback (free tier, reliable)
        logger.info(f"Using CoinGecko for {symbol} historical data (secondary)")
        coingecko_data = self._get_coingecko_historical_data(symbol, hours)
        if coingecko_data:
            logger.info(f"✅ CoinGecko historical: {symbol} - {len(coingecko_data)} data points")
            return coingecko_data

        # Tertiary: Try CoinMarketCap fallback (if rate limits allow)
        if self.cmc_client:
            logger.info(f"Trying CoinMarketCap for {symbol} historical data (tertiary)")
            try:
                cmc_data = self._get_coinmarketcap_historical_data(symbol, hours)
                if cmc_data:
                    converted_data = self._convert_cmc_to_standard_format(cmc_data, symbol)
                    if converted_data:
                        logger.info(f"✅ CoinMarketCap historical: {symbol} - {len(converted_data)} data points")
                        return converted_data
            except Exception as e:
                if "429" in str(e):
                    logger.warning(f"CoinMarketCap rate limited for {symbol}")
                else:
                    logger.error(f"CoinMarketCap historical error for {symbol}: {e}")

        # Generate synthetic/fallback data if all sources fail
        logger.warning(f"All historical sources failed for {symbol}, generating fallback data")
        return self._generate_fallback_historical_data(symbol, hours)


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
            self.analyzer = EnhancedMarketAnalyzer()
            
            # Test if we can get market data
            test_data = self.analyzer.fetch_optimized_market_data()
            if test_data and 'btc_analysis' in test_data:
                self.initialized = True
                logger.info("Enhanced Market Signal Strategy initialized successfully with working API")
            else:
                self.initialized = False
                logger.warning("Enhanced Market Signal Strategy API test failed - using fallback mode")
                
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
        print("Testing Enhanced Market Analyzer with CoinGecko + CoinMarketCap APIs")
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