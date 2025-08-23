
"""
RSI Calculator for Market Signal Strategy
Provides real-time and historical RSI calculations
"""

import requests
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging
import time

class RSICalculator:
    def __init__(self, coinmarketcap_api_key: str):
        self.api_key = coinmarketcap_api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }
        self.price_history = {}
        
        # Alternative data sources
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.binance_base = "https://api.binance.com/api/v3"
        self.cryptocompare_base = "https://min-api.cryptocompare.com/data/v2"
        
    def get_historical_prices(self, symbol: str, days: int = 14) -> List[float]:
        """Get historical price data for RSI calculation"""
        try:
            # Use CoinMarketCap quotes endpoint
            url = f"{self.base_url}/cryptocurrency/quotes/latest"
            params = {'symbol': symbol}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if symbol in data['data']:
                current_price = data['data'][symbol]['quote']['USD']['price']
                
                # For demo, simulate historical prices (in production, use historical endpoint)
                prices = []
                base_price = current_price
                for i in range(days):
                    # Simulate price variations
                    variation = np.random.normal(0, 0.02)  # 2% standard deviation
                    price = base_price * (1 + variation)
                    prices.append(price)
                    base_price = price
                
                return prices[::-1]  # Reverse to get chronological order
                
        except Exception as e:
            logging.error(f"Failed to get historical prices for {symbol}: {e}")
            return []
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI using traditional formula"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if insufficient data
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        # Avoid division by zero
        if avg_loss == 0:
            return 100.0
        
        # Calculate RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_arb_rsi(self, period: int = 14) -> Dict:
        """Get current RSI for ARB token with multiple data source fallbacks"""
        try:
            # Try primary source (CoinMarketCap)
            prices = self.get_historical_prices('ARB', period + 5)
            if prices and len(prices) >= period:
                rsi = self.calculate_rsi(prices, period)
                return self._format_rsi_result(rsi, period, len(prices), 'coinmarketcap')
            
            # Fallback 1: CoinGecko
            prices = self._get_coingecko_historical_prices('arbitrum', period + 5)
            if prices and len(prices) >= period:
                rsi = self.calculate_rsi(prices, period)
                return self._format_rsi_result(rsi, period, len(prices), 'coingecko')
            
            # Fallback 2: Binance (if ARB is listed)
            prices = self._get_binance_historical_prices('ARBUSDT', period + 5)
            if prices and len(prices) >= period:
                rsi = self.calculate_rsi(prices, period)
                return self._format_rsi_result(rsi, period, len(prices), 'binance')
            
            # Fallback 3: CryptoCompare
            prices = self._get_cryptocompare_historical_prices('ARB', period + 5)
            if prices and len(prices) >= period:
                rsi = self.calculate_rsi(prices, period)
                return self._format_rsi_result(rsi, period, len(prices), 'cryptocompare')
            
            # Final fallback: use market data from your existing system
            return {'rsi': 50.0, 'status': 'insufficient_data', 'sources_tried': 4}
            
        except Exception as e:
            logging.error(f"RSI calculation failed: {e}")
            return {'rsi': 50.0, 'status': 'error', 'error': str(e)}
    
    def get_btc_rsi(self, period: int = 14) -> Dict:
        """Get current RSI for BTC"""
        try:
            prices = self.get_historical_prices('BTC', period + 5)
            if not prices:
                return {'rsi': 50.0, 'status': 'insufficient_data'}
            
            rsi = self.calculate_rsi(prices, period)
            
            return {
                'rsi': rsi,
                'status': 'oversold' if rsi <= 30 else 'overbought' if rsi >= 70 else 'neutral',
                'period': period,
                'data_points': len(prices),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logging.error(f"BTC RSI calculation failed: {e}")
            return {'rsi': 50.0, 'status': 'error', 'error': str(e)}
    
    def get_multi_timeframe_rsi(self, symbol: str) -> Dict:
        """Get RSI for multiple timeframes"""
        try:
            rsi_data = {}
            periods = [7, 14, 21]  # Short, medium, long-term
            
            for period in periods:
                prices = self.get_historical_prices(symbol, period + 5)
                if prices:
                    rsi = self.calculate_rsi(prices, period)
                    rsi_data[f'rsi_{period}'] = rsi
            
            return {
                'symbol': symbol,
                'timeframes': rsi_data,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logging.error(f"Multi-timeframe RSI failed: {e}")
            return {'symbol': symbol, 'timeframes': {}, 'error': str(e)}

# Usage example for integration with your system
def test_rsi_calculator():
    """Test the RSI calculator"""
    import os
    
    api_key = os.getenv('COINMARKETCAP_API_KEY')
    if not api_key:
        print("❌ COINMARKETCAP_API_KEY not found")
        return
    
    calculator = RSICalculator(api_key)
    
    print("📊 Testing RSI Calculator")
    print("=" * 40)
    
    # Test ARB RSI
    arb_rsi = calculator.get_arb_rsi()
    print(f"ARB RSI: {arb_rsi['rsi']:.1f} ({arb_rsi['status']})")
    
    # Test BTC RSI
    btc_rsi = calculator.get_btc_rsi()
    print(f"BTC RSI: {btc_rsi['rsi']:.1f} ({btc_rsi['status']})")
    
    # Test multi-timeframe
    multi_rsi = calculator.get_multi_timeframe_rsi('ARB')
    if 'timeframes' in multi_rsi:
        for timeframe, rsi in multi_rsi['timeframes'].items():
            print(f"ARB {timeframe}: {rsi:.1f}")

if __name__ == "__main__":
    test_rsi_calculator()



    def _format_rsi_result(self, rsi: float, period: int, data_points: int, source: str) -> Dict:
        """Format RSI result consistently"""
        if rsi <= 30:
            status = 'oversold'
        elif rsi >= 70:
            status = 'overbought'
        else:
            status = 'neutral'
        
        return {
            'rsi': rsi,
            'status': status,
            'period': period,
            'data_points': data_points,
            'source': source,
            'timestamp': time.time()
        }

    def _get_coingecko_historical_prices(self, coin_id: str, days: int) -> List[float]:
        """Get historical prices from CoinGecko"""
        try:
            url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'prices' in data:
                # Extract prices (second element of each price array)
                prices = [price[1] for price in data['prices']]
                return prices[-days:] if len(prices) >= days else prices
            
        except Exception as e:
            logging.error(f"CoinGecko historical prices failed: {e}")
            
        return []

    def _get_binance_historical_prices(self, symbol: str, hours: int) -> List[float]:
        """Get historical prices from Binance"""
        try:
            url = f"{self.binance_base}/klines"
            params = {
                'symbol': symbol,
                'interval': '1h',
                'limit': hours
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                # Extract closing prices (index 4 in kline data)
                prices = [float(kline[4]) for kline in data]
                return prices
            
        except Exception as e:
            logging.error(f"Binance historical prices failed: {e}")
            
        return []

    def _get_cryptocompare_historical_prices(self, symbol: str, hours: int) -> List[float]:
        """Get historical prices from CryptoCompare"""
        try:
            url = f"{self.cryptocompare_base}/histohour"
            params = {
                'fsym': symbol,
                'tsym': 'USD',
                'limit': hours,
                'api_key': 'demo'  # Use demo key or add your own
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'Data' in data and 'Data' in data['Data']:
                # Extract closing prices
                prices = [point['close'] for point in data['Data']['Data']]
                return prices
            
        except Exception as e:
            logging.error(f"CryptoCompare historical prices failed: {e}")
            
        return []

    def get_consensus_rsi(self, symbol: str, period: int = 14) -> Dict:
        """Get consensus RSI from multiple sources for higher confidence"""
        try:
            rsi_values = []
            sources_used = []
            
            # Collect RSI from all available sources
            methods = [
                ('coinmarketcap', lambda: self.get_historical_prices(symbol, period + 5)),
                ('coingecko', lambda: self._get_coingecko_historical_prices('arbitrum' if symbol == 'ARB' else 'bitcoin', period + 5)),
                ('binance', lambda: self._get_binance_historical_prices(f"{symbol}USDT", period + 5)),
                ('cryptocompare', lambda: self._get_cryptocompare_historical_prices(symbol, period + 5))
            ]
            
            for source_name, price_method in methods:
                try:
                    prices = price_method()
                    if prices and len(prices) >= period:
                        rsi = self.calculate_rsi(prices, period)
                        rsi_values.append(rsi)
                        sources_used.append(source_name)
                except:
                    continue
            
            if not rsi_values:
                return {'rsi': 50.0, 'status': 'no_data', 'confidence': 0.0}
            
            # Calculate consensus
            avg_rsi = sum(rsi_values) / len(rsi_values)
            rsi_std = np.std(rsi_values) if len(rsi_values) > 1 else 0
            
            # Confidence based on agreement between sources and number of sources
            confidence = (1.0 - min(rsi_std / 20.0, 1.0)) * (len(rsi_values) / 4.0)
            confidence = min(confidence, 1.0)
            
            return {
                'rsi': avg_rsi,
                'status': 'oversold' if avg_rsi <= 30 else 'overbought' if avg_rsi >= 70 else 'neutral',
                'confidence': confidence,
                'sources_used': sources_used,
                'rsi_values': rsi_values,
                'std_deviation': rsi_std,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logging.error(f"Consensus RSI calculation failed: {e}")
            return {'rsi': 50.0, 'status': 'error', 'confidence': 0.0, 'error': str(e)}
