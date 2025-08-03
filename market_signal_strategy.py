
"""
Market Signal Strategy Integration for Hybrid Autonomous System
Integrates Freqtrade-style technical analysis with existing DeFi operations
"""

import os
import time
import logging
from datetime import datetime, timedelta
import requests
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class MarketSignal:
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0.0 to 1.0
    btc_price_change: float
    arb_technical_score: float
    timestamp: float

class MarketSignalStrategy:
    def __init__(self, agent):
        self.agent = agent
        self.coinmarketcap_api_key = agent.coinmarketcap_api_key
        self.signal_history = []
        self.last_signal_time = 0
        
        # Configuration parameters
        self.btc_drop_threshold = float(os.getenv('BTC_DROP_THRESHOLD', '0.01'))  # 1% drop
        self.arb_rsi_oversold = float(os.getenv('ARB_RSI_OVERSOLD', '30'))
        self.arb_rsi_overbought = float(os.getenv('ARB_RSI_OVERBOUGHT', '70'))
        self.signal_cooldown = int(os.getenv('SIGNAL_COOLDOWN', '1800'))  # 30 minutes
        
        # Market signal thresholds
        self.market_signal_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
        self.dai_to_arb_threshold = float(os.getenv('DAI_TO_ARB_THRESHOLD', '0.7'))  # Confidence needed for DAI→ARB
        self.arb_to_dai_threshold = float(os.getenv('ARB_TO_DAI_THRESHOLD', '0.6'))  # Confidence needed for ARB→DAI
        
        logging.info(f"Market Signal Strategy initialized - Enabled: {self.market_signal_enabled}")

    def get_btc_price_data(self) -> Optional[Dict]:
        """Get BTC price data from CoinMarketCap API"""
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': self.coinmarketcap_api_key,
            }
            parameters = {
                'symbol': 'BTC',
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=headers, params=parameters, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                btc_data = data['data']['BTC']
                return {
                    'price': btc_data['quote']['USD']['price'],
                    'percent_change_1h': btc_data['quote']['USD']['percent_change_1h'],
                    'percent_change_24h': btc_data['quote']['USD']['percent_change_24h'],
                    'market_cap': btc_data['quote']['USD']['market_cap']
                }
            else:
                logging.error(f"CoinMarketCap API error: {data}")
                return None
                
        except Exception as e:
            logging.error(f"Failed to get BTC price data: {e}")
            return None

    def get_arb_price_data(self) -> Optional[Dict]:
        """Get ARB price data from CoinMarketCap API"""
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': self.coinmarketcap_api_key,
            }
            parameters = {
                'symbol': 'ARB',
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=headers, params=parameters, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                arb_data = data['data']['ARB']
                return {
                    'price': arb_data['quote']['USD']['price'],
                    'percent_change_1h': arb_data['quote']['USD']['percent_change_1h'],
                    'percent_change_24h': arb_data['quote']['USD']['percent_change_24h'],
                    'volume_24h': arb_data['quote']['USD']['volume_24h']
                }
            else:
                logging.error(f"CoinMarketCap API error: {data}")
                return None
                
        except Exception as e:
            logging.error(f"Failed to get ARB price data: {e}")
            return None

    def calculate_technical_indicators(self, price_data: Dict) -> Dict:
        """Calculate simplified technical indicators for ARB"""
        try:
            # Simplified RSI calculation based on recent price changes
            price_change_1h = price_data.get('percent_change_1h', 0)
            price_change_24h = price_data.get('percent_change_24h', 0)
            
            # Simple momentum-based RSI approximation
            if price_change_1h > 2:
                rsi_estimate = 70 + (price_change_1h - 2) * 5  # Trending overbought
            elif price_change_1h < -2:
                rsi_estimate = 30 + (price_change_1h + 2) * 5  # Trending oversold
            else:
                rsi_estimate = 50 + price_change_1h * 10  # Neutral with slight bias
            
            rsi_estimate = max(0, min(100, rsi_estimate))  # Clamp to 0-100
            
            # MACD approximation using 1h vs 24h momentum
            macd_signal = "bullish" if price_change_1h > price_change_24h * 0.1 else "bearish"
            
            return {
                'rsi': rsi_estimate,
                'macd_signal': macd_signal,
                'momentum_1h': price_change_1h,
                'momentum_24h': price_change_24h
            }
            
        except Exception as e:
            logging.error(f"Technical indicator calculation failed: {e}")
            return {'rsi': 50, 'macd_signal': 'neutral', 'momentum_1h': 0, 'momentum_24h': 0}

    def analyze_market_signals(self) -> Optional[MarketSignal]:
        """Analyze market conditions and generate trading signals"""
        try:
            # Skip if disabled or in cooldown
            if not self.market_signal_enabled:
                return None
                
            current_time = time.time()
            if current_time - self.last_signal_time < self.signal_cooldown:
                return None
            
            # Get market data
            btc_data = self.get_btc_price_data()
            arb_data = self.get_arb_price_data()
            
            if not btc_data or not arb_data:
                logging.warning("Insufficient market data for signal analysis")
                return None
            
            # Calculate technical indicators
            arb_indicators = self.calculate_technical_indicators(arb_data)
            
            # Analyze BTC conditions
            btc_drop_signal = btc_data['percent_change_1h'] <= -self.btc_drop_threshold * 100
            btc_recovery_signal = btc_data['percent_change_1h'] >= self.btc_drop_threshold * 100
            
            # Analyze ARB conditions
            arb_oversold = arb_indicators['rsi'] <= self.arb_rsi_oversold
            arb_overbought = arb_indicators['rsi'] >= self.arb_rsi_overbought
            arb_macd_bullish = arb_indicators['macd_signal'] == 'bullish'
            
            # Generate signal
            signal_type = 'neutral'
            confidence = 0.0
            
            # Bearish signal (DAI → ARB opportunity)
            if btc_drop_signal and arb_oversold:
                signal_type = 'bearish'
                confidence = 0.8
            elif btc_drop_signal or arb_oversold:
                signal_type = 'bearish'
                confidence = 0.5
            
            # Bullish signal (ARB → DAI opportunity)
            elif btc_recovery_signal and (arb_overbought or arb_macd_bullish):
                signal_type = 'bullish'
                confidence = 0.7
            elif arb_overbought or (btc_recovery_signal and arb_macd_bullish):
                signal_type = 'bullish'
                confidence = 0.5
            
            signal = MarketSignal(
                signal_type=signal_type,
                confidence=confidence,
                btc_price_change=btc_data['percent_change_1h'],
                arb_technical_score=arb_indicators['rsi'],
                timestamp=current_time
            )
            
            if signal.confidence > 0.3:  # Only log significant signals
                logging.info(f"Market signal generated: {signal.signal_type} (confidence: {signal.confidence:.2f})")
                logging.info(f"BTC 1h change: {signal.btc_price_change:.2f}%, ARB RSI: {signal.arb_technical_score:.1f}")
            
            return signal
            
        except Exception as e:
            logging.error(f"Market signal analysis failed: {e}")
            return None

    def should_execute_market_strategy(self, signal: MarketSignal) -> Tuple[bool, str]:
        """Determine if market strategy should execute based on signal"""
        try:
            # Check if we should swap DAI → ARB (bearish market, ARB oversold)
            if (signal.signal_type == 'bearish' and 
                signal.confidence >= self.dai_to_arb_threshold):
                return True, 'dai_to_arb'
            
            # Check if we should swap ARB → DAI (bullish market, ARB overbought)
            elif (signal.signal_type == 'bullish' and 
                  signal.confidence >= self.arb_to_dai_threshold):
                return True, 'arb_to_dai'
            
            return False, 'hold'
            
        except Exception as e:
            logging.error(f"Strategy execution check failed: {e}")
            return False, 'hold'

    def execute_market_driven_strategy(self, strategy_type: str, amount_dai: float) -> bool:
        """Execute market-driven debt swapping strategy"""
        try:
            logging.info(f"Executing market strategy: {strategy_type} with {amount_dai:.2f} DAI")
            
            if strategy_type == 'dai_to_arb':
                # Borrow DAI and swap to ARB
                success = self._execute_dai_to_arb_swap(amount_dai)
            elif strategy_type == 'arb_to_dai':
                # Swap ARB back to DAI and repay debt
                success = self._execute_arb_to_dai_swap(amount_dai)
            else:
                logging.warning(f"Unknown strategy type: {strategy_type}")
                return False
            
            if success:
                self.last_signal_time = time.time()
                logging.info(f"Market strategy {strategy_type} executed successfully")
            else:
                logging.error(f"Market strategy {strategy_type} failed")
            
            return success
            
        except Exception as e:
            logging.error(f"Market strategy execution failed: {e}")
            return False

    def _execute_dai_to_arb_swap(self, amount_dai: float) -> bool:
        """Execute DAI → ARB swap strategy"""
        try:
            # First, borrow DAI using existing system
            borrow_success = self.agent.execute_enhanced_borrow_with_retry(amount_dai)
            if not borrow_success:
                return False
            
            # Then swap DAI for ARB using Uniswap
            if hasattr(self.agent.uniswap, 'swap_tokens'):
                swap_result = self.agent.uniswap.swap_tokens(
                    self.agent.dai_address,
                    self.agent.arb_address,
                    amount_dai,
                    3000  # 0.3% fee tier for ARB
                )
                return bool(swap_result)
            else:
                logging.error("Uniswap integration not available for ARB trading")
                return False
                
        except Exception as e:
            logging.error(f"DAI → ARB swap failed: {e}")
            return False

    def _execute_arb_to_dai_swap(self, target_dai_amount: float) -> bool:
        """Execute ARB → DAI swap strategy"""
        try:
            # Get current ARB balance
            arb_balance = self.agent.aave.get_token_balance(self.agent.arb_address)
            
            if arb_balance <= 0:
                logging.warning("No ARB balance available for swap")
                return False
            
            # Swap ARB back to DAI
            if hasattr(self.agent.uniswap, 'swap_tokens'):
                swap_result = self.agent.uniswap.swap_tokens(
                    self.agent.arb_address,
                    self.agent.dai_address,
                    arb_balance,
                    3000  # 0.3% fee tier
                )
                
                if swap_result:
                    # Optionally repay some DAI debt to maintain health factor
                    dai_balance = self.agent.aave.get_dai_balance()
                    repay_amount = min(target_dai_amount, dai_balance * 0.5)  # Repay up to 50% of received DAI
                    
                    if repay_amount > 1.0:  # Only repay if meaningful amount
                        repay_success = self.agent.aave.repay_dai(repay_amount)
                        logging.info(f"Repaid {repay_amount:.2f} DAI to maintain position health")
                
                return True
            else:
                logging.error("Uniswap integration not available for ARB trading")
                return False
                
        except Exception as e:
            logging.error(f"ARB → DAI swap failed: {e}")
            return False

    def get_strategy_status(self) -> Dict:
        """Get current market strategy status"""
        return {
            'enabled': self.market_signal_enabled,
            'last_signal_time': self.last_signal_time,
            'cooldown_remaining': max(0, self.signal_cooldown - (time.time() - self.last_signal_time)),
            'btc_threshold': self.btc_drop_threshold,
            'signal_history_count': len(self.signal_history)
        }
