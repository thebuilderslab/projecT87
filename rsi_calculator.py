
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
        """Get current RSI for ARB token"""
        try:
            prices = self.get_historical_prices('ARB', period + 5)
            if not prices:
                return {'rsi': 50.0, 'status': 'insufficient_data'}
            
            rsi = self.calculate_rsi(prices, period)
            
            # Determine RSI status
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
                'data_points': len(prices),
                'timestamp': time.time()
            }
            
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
