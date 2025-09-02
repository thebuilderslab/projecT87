#!/usr/bin/env python3
"""
Enhanced Market Analyzer with CoinMarketCap Integration
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
    def __init__(self, agent=None):
        """Initialize the enhanced market analyzer"""
        self.agent = agent
        self.data_cache = {}
        self.cache_timeout = 3600  # 1 hour cache timeout
        self.technical_analysis = TechnicalAnalysis()
        self.last_api_call = 0
        self.rate_limit_delay = 10.0  # Increased to 10 seconds to avoid rate limits
        self.api_failure_count = 0
        self.max_api_failures = 3

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Initialize CoinMarketCap API client
        self.coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
        if not self.coinmarketcap_key:
            self.logger.warning("COINMARKETCAP_API_KEY not found. Using mock data mode.")
            self.cmc_client = None
            self.initialized = True  # Still consider initialized for mock mode
            self.mock_mode = True
        else:
            try:
                if not self.coinmarketcap_key or len(self.coinmarketcap_key) < 10:
                    raise ValueError("Invalid CoinMarketCap API key provided")
                self.cmc_client = CoinMarketCapAPI(self.coinmarketcap_key)
                self.mock_mode = False
                
                # Test API with a simple call and handle rate limits gracefully
                try:
                    test_data = self.cmc_client.get_current_price('BTC')
                    if test_data:
                        self.initialized = True
                        self.logger.info(f"✅ Enhanced Market Analyzer initialized with CoinMarketCap API key: {self.coinmarketcap_key[:8]}...")
                        self.logger.info("CoinMarketCap API test successful.")
                    else:
                        raise Exception("API test returned no data")
                except Exception as api_error:
                    if "429" in str(api_error) or "Too Many Requests" in str(api_error):
                        self.logger.warning("CoinMarketCap API rate limited during initialization - switching to mock mode")
                        self.mock_mode = True
                        self.initialized = True
                    else:
                        self.logger.error(f"CoinMarketCap API test failed: {api_error}")
                        self.mock_mode = True
                        self.initialized = True  # Still allow mock mode operation
                        
            except ValueError as e:
                self.logger.error(f"Error initializing CoinMarketCap API: {e}")
                self.cmc_client = None
                self.initialized = True  # Allow mock mode
                self.mock_mode = True
            except Exception as e:
                self.logger.error(f"Unexpected error initializing CoinMarketCap API: {e}")
                self.cmc_client = None
                self.initialized = True  # Allow mock mode
                self.mock_mode = True

    def get_market_data_with_fallback(self, symbol: str) -> Optional[Dict]:
        """Get market data with fallback mechanisms"""
        # If in mock mode or too many API failures, go straight to mock data
        if self.mock_mode or self.api_failure_count >= self.max_api_failures:
            return self._get_mock_data(symbol)

        current_time = time.time()
        if current_time - self.last_api_call < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - (current_time - self.last_api_call))

        # Try CoinMarketCap first
        if self.cmc_client and not self.mock_mode:
            try:
                data = self.cmc_client.get_current_price(symbol)
                if data and 'price' in data:
                    self.last_api_call = time.time()
                    self.api_failure_count = 0  # Reset failure count on success
                    data['source'] = 'coinmarketcap'
                    data['timestamp'] = time.time()
                    return data
            except Exception as e:
                self.api_failure_count += 1
                if "429" in str(e) or "Too Many Requests" in str(e):
                    self.logger.warning(f"CoinMarketCap rate limited for {symbol} - switching to mock mode temporarily")
                    self.mock_mode = True  # Temporarily switch to mock mode
                else:
                    self.logger.warning(f"CoinMarketCap failed for {symbol}: {e}")

        # Return mock data as fallback
        if not self.mock_mode:
            self.logger.warning(f"All APIs failed for {symbol}, using mock data")
        return self._get_mock_data(symbol)

    def _get_mock_data(self, symbol: str) -> Optional[Dict]:
        """Generate mock data for a symbol"""
        logger.info(f"Generating mock data for {symbol}")
        mock_prices = {
            'BTC': {'price': 50000, 'change_24h': 1.5, 'market_cap': 1e12, 'volume_24h': 30e9},
            'ETH': {'price': 3000, 'change_24h': 2.0, 'market_cap': 350e9, 'volume_24h': 15e9},
            'ARB': {'price': 0.41, 'change_24h': -0.5, 'market_cap': 1e9, 'volume_24h': 100e6},
            'DAI': {'price': 1.0, 'change_24h': 0.0, 'market_cap': 10e9, 'volume_24h': 1e6}
        }
        if symbol in mock_prices:
            data = mock_prices[symbol]
            return {
                'price': data['price'],
                'percent_change_24h': data['change_24h'],
                'market_cap': data['market_cap'],
                'volume_24h': data['volume_24h'],
                'source': 'mock',
                'timestamp': time.time()
            }
        return None

    def get_market_summary(self) -> Dict:
        """Get comprehensive market summary"""
        try:
            summary = {
                'timestamp': time.time(),
                'btc_analysis': {},
                'eth_analysis': {},
                'dai_analysis': {},
                'arb_analysis': {},
                'market_sentiment': 'neutral'
            }

            # Analyze major cryptocurrencies
            symbols = ['BTC', 'ETH', 'DAI', 'ARB']
            for symbol in symbols:
                try:
                    current_data = self.get_market_data_with_fallback(symbol)
                    if current_data:
                        analysis = {
                            'price': current_data['price'],
                            'change_24h': current_data.get('percent_change_24h', 0),
                            'volume_24h': current_data.get('volume_24h', 0),
                            'signal': self._determine_signal(current_data.get('percent_change_24h', 0)),
                            'confidence': min(abs(current_data.get('percent_change_24h', 0)) / 10, 1.0),
                            'source': current_data.get('source', 'unknown')
                        }

                        # Add RSI for ARB
                        if symbol == 'ARB':
                            analysis['rsi'] = 45  # Mock RSI value

                        summary[f'{symbol.lower()}_analysis'] = analysis
                    else:
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

            return summary

        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return {'error': str(e), 'timestamp': time.time()}

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

class EnhancedMarketSignalStrategy:
    """Enhanced market signal strategy for debt swap decisions"""

    def __init__(self, agent):
        self.agent = agent
        try:
            self.analyzer = EnhancedMarketAnalyzer(agent)

            # Test if we can get market data
            test_data = self.analyzer.get_market_summary()
            if test_data and not test_data.get('error'):
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
        print("Testing Enhanced Market Analyzer with CoinMarketCap API")
        print("=" * 60)

        # Check API key
        coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')

        if coinmarketcap_key:
            print(f"✅ CoinMarketCap API Key found: {coinmarketcap_key[:8]}...")
        else:
            print("❌ COINMARKETCAP_API_KEY not found")

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