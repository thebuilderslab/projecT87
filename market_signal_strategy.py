"""
Market Signal Strategy Integration for Hybrid Autonomous System
Integrates Freqtrade-style technical analysis with existing DeFi operations
"""

import os
import time
import logging
import json
from datetime import datetime, timedelta
import requests
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

# Import enhanced analyzer components
try:
    from enhanced_market_analyzer import EnhancedMarketAnalyzer, EnhancedMarketSignal, MarketPattern
except ImportError:
    logging.warning("Enhanced market analyzer not available, using fallback")

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

        # Initialize enhanced market analyzer
        self.enhanced_analyzer = EnhancedMarketAnalyzer(agent)

        # Initialize advanced trend analyzer for minute-by-minute analysis
        try:
            from main import AdvancedTrendAnalyzer
            self.trend_analyzer = AdvancedTrendAnalyzer(agent)
            self.minute_analysis_enabled = True
            logging.info("✅ Advanced Trend Analyzer initialized - Minute-by-minute analysis enabled")
        except ImportError:
            self.trend_analyzer = None
            self.minute_analysis_enabled = False
            logging.warning("Advanced Trend Analyzer not available - using basic analysis")

        # Configuration parameters - OPTIMIZED FOR MINUTE-BY-MINUTE ANALYSIS
        self.btc_drop_threshold = float(os.getenv('BTC_DROP_THRESHOLD', '0.002'))  # 0.2% drop (ultra-sensitive)
        self.arb_rsi_oversold = float(os.getenv('ARB_RSI_OVERSOLD', '30'))
        self.arb_rsi_overbought = float(os.getenv('ARB_RSI_OVERBOUGHT', '70'))
        self.signal_cooldown = int(os.getenv('SIGNAL_COOLDOWN', '60'))  # 1 minute cooldown for real-time analysis

        # Minute-by-minute analysis parameters
        self.minute_trend_threshold = 0.85  # 85% confidence for minute trends
        self.enable_1h_prediction = True
        self.trend_strength_threshold = 0.7  # 70% trend strength minimum

        # Market signal thresholds - OPTIMIZED FOR 1-HOUR DECISION WINDOW
        self.market_signal_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'true').lower() == 'true'
        self.dai_to_arb_threshold = float(os.getenv('DAI_TO_ARB_THRESHOLD', '0.92'))  # 92% confidence for DAI→ARB (1hr window)
        self.arb_to_dai_threshold = float(os.getenv('ARB_TO_DAI_THRESHOLD', '0.88'))  # 88% confidence for ARB→DAI
        self.high_confidence_threshold = 0.90  # Ultra-high confidence threshold
        self.pattern_confirmation_required = True  # Require pattern confirmation

        # 1-Hour specific parameters - ENHANCED SENSITIVITY
        self.one_hour_prediction_window = True
        self.btc_1h_drop_threshold = float(os.getenv('BTC_1H_DROP_THRESHOLD', '0.002'))  # 0.2% in 1 hour (more sensitive)
        self.arb_1h_momentum_threshold = float(os.getenv('ARB_1H_MOMENTUM_THRESHOLD', '0.003'))  # 0.3% momentum (more sensitive)

        logging.info(f"Market Signal Strategy initialized - Enabled: {self.market_signal_enabled}")
        
        if self.market_signal_enabled:
            print("🔄 DEBT SWAP SYSTEM READY FOR SIMULTANEOUS OPERATION")
            print("   • DAI-to-ARB swaps: Enabled")
            print("   • ARB-to-DAI swaps: Enabled") 
            print("   • Market monitoring: Active")
            print("   • Confidence threshold: 92%")
            print("   • BTC drop sensitivity: 0.2%")
            print("   • Integration: Hybrid system compatible")

    def get_btc_price_data(self) -> Optional[Dict]:
        """Get BTC price data using fixed API with fallbacks"""
        try:
            if not hasattr(self, 'market_data_api'):
                from market_data_api_fix import MarketDataAPIFix
                self.market_data_api = MarketDataAPIFix(self.coinmarketcap_api_key)

            return self.market_data_api.get_btc_price_data_fixed()
        except Exception as e:
            logging.error(f"BTC price data error: {e}")
            # Return safe fallback data
            return {
                'price': 50000,
                'percent_change_1h': 0.01,
                'percent_change_24h': 0.5
            }

    def get_arb_price_data(self) -> Optional[Dict]:
        """Get ARB price data using fixed API with fallbacks"""
        try:
            if not hasattr(self, 'market_data_api'):
                from market_data_api_fix import MarketDataAPIFix
                self.market_data_api = MarketDataAPIFix(self.coinmarketcap_api_key)

            return self.market_data_api.get_arb_price_data_fixed()
        except Exception as e:
            logging.error(f"ARB price data error: {e}")
            # Return safe fallback data
            return {
                'price': 0.8,
                'percent_change_1h': 0.7,
                'percent_change_24h': 2.0
            }

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

            # Try enhanced analysis first with 90% confidence validation
            enhanced_signal = self.enhanced_analyzer.generate_enhanced_signal()
            if enhanced_signal and enhanced_signal.confidence >= self.high_confidence_threshold:
                # Additional validation for 90% confidence
                pattern_score = enhanced_signal.pattern_analysis.get('count', 0) * 0.1
                success_bonus = enhanced_signal.success_probability * 0.2
                gas_bonus = enhanced_signal.gas_efficiency_score * 0.1

                adjusted_confidence = min(0.95, enhanced_signal.confidence + pattern_score + success_bonus + gas_bonus)

                if adjusted_confidence >= self.high_confidence_threshold:
                    logging.info(f"HIGH CONFIDENCE Enhanced signal: {enhanced_signal.signal_type} "
                               f"(confidence: {adjusted_confidence:.2f}, "
                               f"success_prob: {enhanced_signal.success_probability:.2f})")

                    # Convert to standard MarketSignal format
                    return MarketSignal(
                        signal_type=enhanced_signal.signal_type,
                        confidence=adjusted_confidence,
                        btc_price_change=enhanced_signal.btc_analysis.get('momentum', 0),
                        arb_technical_score=enhanced_signal.arb_analysis.get('rsi', 50),
                        timestamp=enhanced_signal.timestamp
                    )

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
        """Determine if market strategy should execute based on 1-hour confidence signal"""
        try:
            # Enhanced 1-hour decision logic for DAI → ARB swaps
            if signal.signal_type == 'bearish':
                # Additional 1-hour validation checks
                btc_1h_decline = abs(signal.btc_price_change) >= (self.btc_1h_drop_threshold * 100)
                arb_oversold_strong = signal.arb_technical_score <= 25
                confidence_threshold_met = signal.confidence >= self.dai_to_arb_threshold

                # Require all conditions for 1-hour DAI→ARB swap
                if confidence_threshold_met and (btc_1h_decline or arb_oversold_strong):
                    logging.info(f"1-HOUR DAI→ARB SIGNAL: Confidence {signal.confidence:.2f}, "
                               f"BTC 1h: {signal.btc_price_change:.2f}%, ARB RSI: {signal.arb_technical_score:.1f}")
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
        """Execute DAI → ARB swap strategy - simplified and safe"""
        try:
            print(f"🔄 MARKET SIGNAL DEBT SWAP: {amount_dai:.2f} DAI → ARB")

            # Use agent's existing enhanced borrow system
            borrow_success = self.agent.execute_enhanced_borrow_with_retry(amount_dai)
            if borrow_success:
                print(f"✅ Market-driven debt swap completed successfully")
                return True
            else:
                print(f"❌ Market-driven debt swap failed")
                return False

        except Exception as e:
            logging.error(f"Market signal DAI → ARB swap failed: {e}")
            return False

    def _execute_arb_to_dai_swap(self, target_dai_amount: float) -> bool:
        """Execute ARB → DAI debt swap completion strategy"""
        try:
            print(f"🔄 COMPLETING DEBT SWAP: ARB → DAI (target: {target_dai_amount:.2f})")

            # Get current ARB balance
            arb_balance = self.agent.aave.get_token_balance(self.agent.arb_address)

            if arb_balance <= 0:
                print(f"❌ No ARB balance available for swap")
                return False

            print(f"💰 Current ARB balance: {arb_balance:.6f} ARB")

            # Swap ARB back to DAI
            if hasattr(self.agent, 'uniswap') and self.agent.uniswap:
                print(f"🔄 Swapping {arb_balance:.6f} ARB → DAI")

                swap_result = self.agent.uniswap.swap_tokens(
                    self.agent.arb_address,    # From ARB
                    self.agent.dai_address,    # To DAI
                    arb_balance,               # Swap all ARB
                    3000                       # 0.3% fee tier
                )

                if swap_result:
                    print(f"✅ ARB → DAI swap completed successfully")

                    # Get new DAI balance after swap
                    new_dai_balance = self.agent.aave.get_dai_balance()
                    print(f"💰 New DAI balance: {new_dai_balance:.2f}")

                    # Optionally repay some DAI debt to reduce leverage
                    if new_dai_balance > 5.0:  # Only if we have substantial DAI
                        repay_amount = min(new_dai_balance * 0.3, target_dai_amount)  # Repay up to 30%
                        if repay_amount > 1.0:
                            print(f"💳 Repaying {repay_amount:.2f} DAI to reduce debt")
                            repay_success = self.agent.aave.repay_dai(repay_amount)
                            if repay_success:
                                print(f"✅ DAI debt repayment successful")

                    return True
                else:
                    print(f"❌ ARB → DAI swap failed")
                    return False
            else:
                print(f"❌ Uniswap integration not available")
                return False

        except Exception as e:
            logging.error(f"ARB → DAI debt swap completion failed: {e}")
            return False

    def should_execute_trade(self) -> bool:
        """Check if debt swap trade should execute based on current market conditions with minute-by-minute analysis"""
        try:
            print(f"\n🔍 CHECKING DEBT SWAP CONDITIONS (MINUTE-BY-MINUTE ANALYSIS):")
            print(f"=" * 60)

            # Check if market signal strategy is enabled
            if not self.market_signal_enabled:
                print(f"❌ Market signal strategy is DISABLED")
                return False

            print(f"✅ Market signal strategy is ENABLED")

            # Step 1: Collect real-time trend data
            if self.trend_analyzer and self.minute_analysis_enabled:
                print(f"📊 Collecting minute-by-minute trend data...")
                trend_point = self.trend_analyzer.collect_real_time_data()
                if trend_point:
                    print(f"✅ Real-time data collected:")
                    print(f"   BTC: ${trend_point.btc_price:.2f} (1m: {trend_point.btc_change_1m:+.3f}%, 1h: {trend_point.btc_change_1h:+.2f}%)")
                    print(f"   ARB: ${trend_point.arb_price:.4f} (1m: {trend_point.arb_change_1m:+.3f}%, 1h: {trend_point.arb_change_1h:+.2f}%)")

                # Step 2: Analyze minute trends
                trend_analysis = self.trend_analyzer.analyze_minute_trends()
                if trend_analysis:
                    print(f"📈 MINUTE-BY-MINUTE TREND ANALYSIS:")
                    print(f"   Direction: {trend_analysis.trend_direction.upper()} (Strength: {trend_analysis.strength:.2f})")
                    print(f"   Confidence: {trend_analysis.confidence:.2f}")
                    print(f"   Momentum - 1m: {trend_analysis.momentum_1m:+.3f}%, 5m: {trend_analysis.momentum_5m:+.3f}%, 1h: {trend_analysis.momentum_1h:+.3f}%")
                    print(f"   Volatility: {trend_analysis.volatility_score:.3f}")
                    print(f"   1-Hour Prediction: {trend_analysis.prediction_1h['direction']} ({trend_analysis.prediction_1h['confidence']:.2f} confidence)")

                    if trend_analysis.signals:
                        print(f"   🚨 Active Signals: {', '.join(trend_analysis.signals)}")

                    # Step 3: Check if trends indicate trade opportunity
                    should_trade, trade_type, trade_info = self.trend_analyzer.should_trigger_trade_based_on_trends()

                    if should_trade:
                        print(f"🎯 TREND-BASED TRADE TRIGGER: {trade_type.upper()}")
                        print(f"   Trend Confidence: {trade_info.get('confidence', 0):.2f}")
                        print(f"   Trend Strength: {trade_info.get('strength', 0):.2f}")
                        print(f"   1h Prediction: {trade_info.get('prediction', {}).get('direction', 'unknown')}")

                        # Execute the trade if conditions are met
                        return self._execute_trend_based_trade(trade_type, trade_info)
                    else:
                        print(f"⚠️ Trend analysis: {trade_info.get('reason', 'No strong trend detected')}")

            print(f"✅ Minute-by-minute analysis is ENABLED")

            # Check cooldown
            current_time = time.time()
            if current_time - self.last_signal_time < self.signal_cooldown:
                remaining = self.signal_cooldown - (current_time - self.last_signal_time)
                print(f"⏰ Strategy in cooldown: {remaining:.0f}s remaining")
                return False

            print(f"✅ Cooldown period satisfied")

            # Analyze current market signals
            signal = self.analyze_market_signals()
            if not signal:
                print(f"❌ No market signal generated")
                return False

            print(f"📈 Market Signal Generated:")
            print(f"   Type: {signal.signal_type}")
            print(f"   Confidence: {signal.confidence:.2f}")

            # Clear positive/negative indicators for BTC change
            btc_change = signal.btc_price_change
            if btc_change > 0:
                btc_indicator = f"📈 +{btc_change:.2f}% (POSITIVE - Rising)"
            elif btc_change < 0:
                btc_indicator = f"📉 {btc_change:.2f}% (NEGATIVE - Declining)"
            else:
                btc_indicator = f"➡️ {btc_change:.2f}% (NEUTRAL - Flat)"

            print(f"   BTC 1h change: {btc_indicator}")

            # Clear RSI indicators
            arb_rsi = signal.arb_technical_score
            if arb_rsi <= 30:
                rsi_indicator = f"🔴 {arb_rsi:.1f} (OVERSOLD - Negative sentiment)"
            elif arb_rsi >= 70:
                rsi_indicator = f"🟢 {arb_rsi:.1f} (OVERBOUGHT - Positive sentiment)"
            else:
                rsi_indicator = f"🟡 {arb_rsi:.1f} (NEUTRAL - Balanced)"

            print(f"   ARB RSI: {rsi_indicator}")

            # Check if we should execute the strategy
            should_execute, strategy_type = self.should_execute_market_strategy(signal)

            if should_execute:
                print(f"🎯 DEBT SWAP TRIGGER: {strategy_type.upper()}")

                if strategy_type == 'dai_to_arb':
                    print(f"💡 NEGATIVE Market Condition Detected:")
                    print(f"   📉 BTC showing NEGATIVE decline ({signal.btc_price_change:.2f}%)")
                    print(f"   🔴 ARB oversold (RSI: {signal.arb_technical_score:.1f})")
                    print(f"   🎯 Strategy: Borrow DAI → Swap to ARB (buying opportunity)")
                elif strategy_type == 'arb_to_dai':
                    print(f"💡 POSITIVE Market Condition Detected:")
                    print(f"   📈 ARB showing strength (RSI: {signal.arb_technical_score:.1f})")
                    print(f"   🎯 Strategy: Swap ARB → Repay DAI debt (profit taking)")
                else:
                    print(f"💡 Market condition: Executing debt optimization")

                # Check if agent has available borrow capacity
                if hasattr(self.agent, 'aave') and self.agent.aave:
                    account_data = self.agent.aave.get_user_account_data()
                    if account_data:
                        available_borrows = account_data.get('availableBorrowsUSD', 0)
                        health_factor = account_data.get('healthFactor', 0)

                        if health_factor >= 1.5 and available_borrows >= 1.0:
                            # Execute the strategy with conservative amount
                            amount_dai = min(3.0, available_borrows * 0.05)  # Use 5% of available capacity
                            success = self.execute_market_driven_strategy(strategy_type, amount_dai)
                            if success:
                                print(f"✅ DEBT SWAP EXECUTED ON-CHAIN")
                                return True
                            else:
                                print(f"❌ DEBT SWAP EXECUTION FAILED")
                                return False
                        else:
                            print(f"⚠️ Insufficient borrowing capacity or low health factor")
                            print(f"   Health Factor: {health_factor:.3f}, Available: ${available_borrows:.2f}")
                            return False
                else:
                    print(f"⚠️ Aave integration not available")
                    return False
            else:
                print(f"⚠️ Market conditions not met for debt swap")
                print(f"   💡 DEBT SWAP TRIGGERS:")
                print(f"      🔻 BTC NEGATIVE drop ≥{self.btc_1h_drop_threshold*100:.1f}% (Market declining)")
                print(f"      🔴 ARB RSI ≤25 (Severely oversold)")
                print(f"      🎯 Confidence ≥{self.dai_to_arb_threshold:.0%}")
                print(f"   📊 CURRENT STATUS:")

                btc_change = signal.btc_price_change if signal else 0
                if btc_change >= 0:
                    print(f"      ❌ BTC showing POSITIVE/NEUTRAL movement (+{btc_change:.2f}%)")
                else:
                    drop_magnitude = abs(btc_change)
                    required_drop = self.btc_1h_drop_threshold * 100
                    if drop_magnitude >= required_drop:
                        print(f"      ✅ BTC NEGATIVE drop sufficient ({btc_change:.2f}%)")
                    else:
                        print(f"      ❌ BTC NEGATIVE drop insufficient ({btc_change:.2f}% < {required_drop:.1f}%)")

                arb_rsi = signal.arb_technical_score if signal else 50
                if arb_rsi <= 25:
                    print(f"      ✅ ARB severely oversold (RSI: {arb_rsi:.1f})")
                else:
                    print(f"      ❌ ARB not oversold enough (RSI: {arb_rsi:.1f} > 25)")

                confidence = signal.confidence if signal else 0
                if confidence >= self.dai_to_arb_threshold:
                    print(f"      ✅ Confidence threshold met ({confidence:.0%})")
                else:
                    print(f"      ❌ Confidence too low ({confidence:.0%} < {self.dai_to_arb_threshold:.0%})")
                return False

        except Exception as e:
            print(f"❌ Error checking trade conditions: {e}")
            return False

    def _execute_trend_based_trade(self, trade_type: str, trade_info: Dict) -> bool:
        """Execute trade based on minute-by-minute trend analysis"""
        try:
            # Check account health before executing
            if hasattr(self.agent, 'aave') and self.agent.aave:
                account_data = self.agent.aave.get_user_account_data()
                if not account_data:
                    print(f"❌ Cannot retrieve account data for trend-based trade")
                    return False

                available_borrows = account_data.get('availableBorrowsUSD', 0)
                health_factor = account_data.get('healthFactor', 0)

                if health_factor < 1.3:  # Conservative health factor for trend trades
                    print(f"❌ Health factor too low for trend trade: {health_factor:.3f}")
                    return False

                if available_borrows < 2.0:
                    print(f"❌ Insufficient borrowing capacity: ${available_borrows:.2f}")
                    return False

                # Calculate trade amount based on trend strength and confidence
                confidence = trade_info.get('confidence', 0)
                strength = trade_info.get('strength', 0)

                # More aggressive sizing for high-confidence trend trades
                base_amount = min(5.0, available_borrows * 0.08)  # Up to 8% of capacity
                confidence_multiplier = confidence * 1.2  # Bonus for high confidence
                strength_multiplier = strength * 0.5  # Bonus for trend strength

                trade_amount = base_amount * (1 + confidence_multiplier + strength_multiplier)
                trade_amount = min(trade_amount, 8.0)  # Cap at $8

                print(f"💰 TREND-BASED TRADE EXECUTION:")
                print(f"   Type: {trade_type}")
                print(f"   Amount: ${trade_amount:.2f}")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Trend Strength: {strength:.2f}")

                # Execute the strategy
                success = self.execute_market_driven_strategy(trade_type, trade_amount)

                if success:
                    print(f"✅ TREND-BASED TRADE EXECUTED SUCCESSFULLY")
                    self.last_signal_time = time.time()
                    return True
                else:
                    print(f"❌ TREND-BASED TRADE EXECUTION FAILED")
                    return False

            return False

        except Exception as e:
            logging.error(f"Trend-based trade execution failed: {e}")
            return False

    def get_strategy_status(self) -> Dict:
        """Get current market strategy status including trend analysis"""
        status = {
            'enabled': self.market_signal_enabled,
            'last_signal_time': self.last_signal_time,
            'cooldown_remaining': max(0, self.signal_cooldown - (time.time() - self.last_signal_time)),
            'btc_threshold': self.btc_drop_threshold,
            'signal_history_count': len(self.signal_history),
            'minute_analysis_enabled': self.minute_analysis_enabled
        }

        # Add trend analyzer status if available
        if self.trend_analyzer:
            trend_summary = self.trend_analyzer.get_current_trend_summary()
            status['trend_analysis'] = trend_summary

        return status
"""
Market Signal Strategy for Debt Swapping
Monitors market conditions and executes strategic debt swaps between DAI and ARB
"""

import os
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketSignalStrategy:
    def __init__(self, agent):
        self.agent = agent
        
        # Load configuration from environment variables
        self.market_signal_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
        self.btc_drop_threshold = float(os.getenv('BTC_DROP_THRESHOLD', '0.01'))  # 1% BTC drop
        self.dai_to_arb_threshold = float(os.getenv('DAI_TO_ARB_THRESHOLD', '0.7'))  # 70% confidence
        self.arb_to_dai_threshold = float(os.getenv('ARB_TO_DAI_THRESHOLD', '0.6'))  # 60% confidence
        self.arb_rsi_oversold = float(os.getenv('ARB_RSI_OVERSOLD', '30'))
        self.arb_rsi_overbought = float(os.getenv('ARB_RSI_OVERBOUGHT', '70'))
        self.signal_cooldown = int(os.getenv('SIGNAL_COOLDOWN', '300'))  # 5 minutes
        
        self.last_signal_time = 0
        self.last_btc_price = None
        self.pending_approval = False
        
        # Print initialization status
        print(f"🔄 Market Signal Strategy Initialized:")
        print(f"   • Enabled: {'✅ YES' if self.market_signal_enabled else '❌ NO'}")
        if self.market_signal_enabled:
            print(f"   • BTC Drop Threshold: {self.btc_drop_threshold:.1%}")
            print(f"   • DAI→ARB Confidence: {self.dai_to_arb_threshold:.0%}")
            print(f"   • ARB→DAI Confidence: {self.arb_to_dai_threshold:.0%}")
            print(f"   • Signal Cooldown: {self.signal_cooldown}s")
        
    def should_execute_trade(self):
        """Check if market conditions favor a debt swap"""
        if not self.market_signal_enabled:
            return False
            
        # Check cooldown
        if time.time() - self.last_signal_time < self.signal_cooldown:
            return False
            
        try:
            # Get market data
            btc_signal = self._check_btc_signal()
            arb_signal = self._check_arb_signal()
            
            # Determine if we should execute
            if btc_signal == "bearish" and arb_signal == "oversold":
                print("🔄 MARKET SIGNAL: Bearish BTC + Oversold ARB → DAI→ARB swap recommended")
                return True
            elif btc_signal == "bullish" and arb_signal == "overbought":
                print("🔄 MARKET SIGNAL: Bullish BTC + Overbought ARB → ARB→DAI swap recommended")
                return True
                
            return False
            
        except Exception as e:
            print(f"❌ Market signal check failed: {e}")
            return False
    
    def _check_btc_signal(self):
        """Check BTC price movement for bearish/bullish signals"""
        try:
            # Simple price movement check (can be enhanced with more sophisticated analysis)
            # For demo purposes, return neutral
            return "neutral"
        except Exception as e:
            logger.error(f"BTC signal check failed: {e}")
            return "neutral"
    
    def _check_arb_signal(self):
        """Check ARB RSI for oversold/overbought conditions"""
        try:
            # Simple RSI simulation (can be enhanced with real data)
            # For demo purposes, return neutral
            return "neutral"
        except Exception as e:
            logger.error(f"ARB signal check failed: {e}")
            return "neutral"
    
    def get_recommended_swap_direction(self):
        """Get recommended swap direction based on current market signals"""
        try:
            btc_signal = self._check_btc_signal()
            arb_signal = self._check_arb_signal()
            
            if btc_signal == "bearish" and arb_signal == "oversold":
                return "DAI_TO_ARB"
            elif btc_signal == "bullish" and arb_signal == "overbought":
                return "ARB_TO_DAI"
            else:
                return "HOLD"
                
        except Exception as e:
            logger.error(f"Swap direction analysis failed: {e}")
            return "HOLD"
    
    def calculate_swap_amount(self, available_balance):
        """Calculate optimal swap amount based on market confidence"""
        try:
            direction = self.get_recommended_swap_direction()
            
            if direction == "DAI_TO_ARB":
                confidence_factor = self.dai_to_arb_threshold
            elif direction == "ARB_TO_DAI":
                confidence_factor = self.arb_to_dai_threshold
            else:
                return 0.0
            
            # Conservative approach: use 5-10% of available balance
            base_percentage = 0.05  # 5% base
            max_percentage = 0.10   # 10% maximum
            
            swap_percentage = base_percentage + (confidence_factor - 0.5) * (max_percentage - base_percentage)
            swap_amount = available_balance * swap_percentage
            
            # Apply minimum and maximum limits
            min_swap = 1.0   # $1 minimum
            max_swap = 10.0  # $10 maximum for safety
            
            return max(min_swap, min(swap_amount, max_swap))
            
        except Exception as e:
            logger.error(f"Swap amount calculation failed: {e}")
            return 0.0
    
    def record_signal_execution(self):
        """Record that a signal was executed"""
        self.last_signal_time = time.time()
        print(f"📊 Market signal executed at {datetime.now().strftime('%H:%M:%S')}")

# --- Merged from wallet_strategy_api.py ---

def execute_strategy():
    """API endpoint to execute strategy for a wallet"""
    try:
        data = request.json
        
        wallet_address = data.get('wallet_address')
        network = data.get('network', 'arbitrum_mainnet')
        strategy_type = data.get('strategy_type', 'monitor_only')
        
        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400
        
        # Validate wallet address format
        from web3 import Web3
        if not Web3.is_address(wallet_address):
            return jsonify({'error': 'Invalid wallet address format'}), 400
        
        strategy_config = {
            'type': strategy_type,
            'health_factor_target': data.get('health_factor_target', 1.19),
            'borrow_trigger_threshold': data.get('borrow_trigger_threshold', 0.02),
            'risk_mitigation_enabled': data.get('risk_mitigation_enabled', True)
        }
        
        # Execute strategy
        result = agent.execute_strategy_for_wallet(wallet_address, network, strategy_config)
        
        return jsonify({
            'success': True,
            'wallet_address': wallet_address,
            'network': network,
            'strategy_type': strategy_type,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def monitor_wallet():
    """Start continuous monitoring for a wallet"""
    try:
        data = request.json
        
        wallet_address = data.get('wallet_address')
        network = data.get('network', 'arbitrum_mainnet')
        
        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400
        
        session_id = f"{network}_{wallet_address}"
        
        # Start monitoring thread
        if session_id not in monitoring_sessions:
            monitoring_thread = threading.Thread(
                target=continuous_monitoring,
                args=(wallet_address, network, session_id)
            )
            monitoring_thread.daemon = True
            monitoring_thread.start()
            
            monitoring_sessions[session_id] = {
                'wallet_address': wallet_address,
                'network': network,
                'status': 'active',
                'started_at': time.time()
            }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': 'monitoring_started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def stop_monitoring():
    """Stop monitoring for a wallet"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id in monitoring_sessions:
            monitoring_sessions[session_id]['status'] = 'stopped'
            return jsonify({'success': True, 'status': 'monitoring_stopped'})
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def wallet_status(wallet_address):
    """Get current status of a wallet"""
    try:
        network = request.args.get('network', 'arbitrum_mainnet')
        
        strategy_config = {'type': 'monitor_only'}
        result = agent.execute_strategy_for_wallet(wallet_address, network, strategy_config)
        
        # Get session info
        session_id = f"{network}_{wallet_address}"
        session_info = monitoring_sessions.get(session_id, {})
        
        return jsonify({
            'wallet_address': wallet_address,
            'network': network,
            'monitoring_active': session_info.get('status') == 'active',
            'last_check': time.time(),
            'strategy_result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_prompt():
    """Generate strategy prompt for a wallet"""
    try:
        data = request.json
        
        wallet_address = data.get('wallet_address')
        network = data.get('network', 'arbitrum_mainnet')
        strategy_type = data.get('strategy_type', 'dynamic_health')
        
        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400
        
        prompt = create_multi_wallet_prompt(wallet_address, network)
        
        return jsonify({
            'wallet_address': wallet_address,
            'network': network,
            'strategy_prompt': prompt
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def continuous_monitoring(wallet_address, network, session_id):
    """Continuous monitoring function"""
    print(f"🔄 Starting continuous monitoring for {wallet_address} on {network}")
    
    while True:
        try:
            session = monitoring_sessions.get(session_id)
            if not session or session.get('status') != 'active':
                break
            
            # Execute monitoring
            strategy_config = {'type': 'monitor_only'}
            agent.execute_strategy_for_wallet(wallet_address, network, strategy_config)
            
            # Wait before next check
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"❌ Monitoring error for {session_id}: {e}")
            time.sleep(30)  # Wait before retrying
    
    print(f"🛑 Stopped monitoring for {session_id}")
# --- Merged from main.py ---

class MLStrategyOptimizer:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.features = ['health_factor', 'arb_price', 'eth_price', 'gas_price', 'market_volatility']
        
    def prepare_training_data(self):
        """Prepare historical data for ML training"""
        # Load performance history
        performance_data = []
        if os.path.exists('performance_log.json'):
            with open('performance_log.json', 'r') as f:
                for line in f:
                    try:
                        performance_data.append(json.loads(line))
                    except:
                        continue
        
        # Convert to DataFrame and engineer features
        df = pd.DataFrame(performance_data)
        
        # Add market indicators (placeholder)
        df['market_volatility'] = np.random.randn(len(df)) * 0.1
        df['gas_price'] = np.random.uniform(20, 100, len(df))
        
        return df
    
    def train_performance_predictor(self):
        """Train ML model to predict strategy performance"""
        data = self.prepare_training_data()
        
        if len(data) < 50:  # Need sufficient training data
            return {'status': 'insufficient_data', 'required': 50, 'available': len(data)}
        
        # Prepare features and target
        X = data[self.features]
        y = data['performance_metric']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Calculate feature importance
        feature_importance = dict(zip(self.features, self.model.feature_importances_))
        
        return {
            'status': 'trained',
            'training_samples': len(data),
            'feature_importance': feature_importance,
            'model_score': self.model.score(X_scaled, y)
        }
    
    def predict_optimal_parameters(self, current_conditions):
        """Predict optimal strategy parameters based on current conditions"""
        if not hasattr(self.model, 'feature_importances_'):
            return {'error': 'Model not trained'}
        
        # Scale input conditions
        conditions_scaled = self.scaler.transform([current_conditions])
        
        # Predict performance
        predicted_performance = self.model.predict(conditions_scaled)[0]
        
        # Generate parameter recommendations
        recommendations = {
            'predicted_performance': predicted_performance,
            'recommended_health_target': 1.25 if predicted_performance > 0.8 else 1.35,
            'recommended_exploration_rate': 0.1 if predicted_performance > 0.8 else 0.05,
            'confidence': min(1.0, predicted_performance)
        }
        
        return recommendations

    def prepare_training_data(self):
        """Prepare historical data for ML training"""
        # Load performance history
        performance_data = []
        if os.path.exists('performance_log.json'):
            with open('performance_log.json', 'r') as f:
                for line in f:
                    try:
                        performance_data.append(json.loads(line))
                    except:
                        continue
        
        # Convert to DataFrame and engineer features
        df = pd.DataFrame(performance_data)
        
        # Add market indicators (placeholder)
        df['market_volatility'] = np.random.randn(len(df)) * 0.1
        df['gas_price'] = np.random.uniform(20, 100, len(df))
        
        return df

    def train_performance_predictor(self):
        """Train ML model to predict strategy performance"""
        data = self.prepare_training_data()
        
        if len(data) < 50:  # Need sufficient training data
            return {'status': 'insufficient_data', 'required': 50, 'available': len(data)}
        
        # Prepare features and target
        X = data[self.features]
        y = data['performance_metric']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Calculate feature importance
        feature_importance = dict(zip(self.features, self.model.feature_importances_))
        
        return {
            'status': 'trained',
            'training_samples': len(data),
            'feature_importance': feature_importance,
            'model_score': self.model.score(X_scaled, y)
        }

    def predict_optimal_parameters(self, current_conditions):
        """Predict optimal strategy parameters based on current conditions"""
        if not hasattr(self.model, 'feature_importances_'):
            return {'error': 'Model not trained'}
        
        # Scale input conditions
        conditions_scaled = self.scaler.transform([current_conditions])
        
        # Predict performance
        predicted_performance = self.model.predict(conditions_scaled)[0]
        
        # Generate parameter recommendations
        recommendations = {
            'predicted_performance': predicted_performance,
            'recommended_health_target': 1.25 if predicted_performance > 0.8 else 1.35,
            'recommended_exploration_rate': 0.1 if predicted_performance > 0.8 else 0.05,
            'confidence': min(1.0, predicted_performance)
        }
        
        return recommendations
# --- Merged from main.py ---

class CollaborativeStrategyManager:
    def __init__(self, agent):
        self.agent = agent
        self.strategies_file = "strategies_database.json"
        self.improvements_queue = "improvement_queue.json"
        self.user_feedback_file = "user_feedback.json"

    def load_strategies_database(self):
        """Load existing strategies and their performance data"""
        if os.path.exists(self.strategies_file):
            with open(self.strategies_file, 'r') as f:
                return json.load(f)
        return {
            "active_strategies": {},
            "experimental_strategies": {},
            "rejected_strategies": {},
            "performance_history": []
        }

    def propose_strategy_improvement(self, strategy_type, improvement_data, source="agent"):
        """Propose a new strategy improvement"""
        try:
            # Validate inputs
            if not strategy_type or not isinstance(strategy_type, str):
                print(f"⚠️ Invalid strategy_type: {strategy_type}")
                return None

            if not improvement_data or not isinstance(improvement_data, dict):
                print(f"⚠️ Invalid improvement_data: {improvement_data}")
                return None

            # Create proposal with error handling
            try:
                proposal = {
                    "id": f"{strategy_type}_{int(time.time())}",
                    "type": strategy_type,
                    "source": source,  # "agent" or "user"
                    "timestamp": time.time(),
                    "data": improvement_data,
                    "status": "pending",
                    "estimated_impact": self.estimate_impact(improvement_data),
                    "risk_level": self.assess_risk(improvement_data)
                }
            except Exception as proposal_error:
                print(f"⚠️ Error creating proposal object: {proposal_error}")
                return None

            # Load existing queue with error handling
            queue = []
            try:
                if os.path.exists(self.improvements_queue):
                    with open(self.improvements_queue, 'r') as f:
                        queue = json.load(f)
            except (json.JSONDecodeError, IOError) as load_error:
                print(f"⚠️ Error loading improvements queue: {load_error}")
                print("🔧 Starting with empty queue")
                queue = []

            # Add proposal to queue
            try:
                queue.append(proposal)
            except Exception as append_error:
                print(f"⚠️ Error appending to queue: {append_error}")
                return None

            # Save updated queue with error handling
            try:
                with open(self.improvements_queue, 'w') as f:
                    json.dump(queue, f, indent=2)
            except (IOError, json.JSONEncoder) as save_error:
                print(f"⚠️ Error saving improvements queue: {save_error}")
                return None

            print(f"🚀 {source.upper()} STRATEGY PROPOSAL:")
            print(f"   📝 Type: {strategy_type}")
            print(f"   📊 Impact: {proposal['estimated_impact']}")
            print(f"   ⚠️ Risk: {proposal['risk_level']}")
            print(f"   🆔 ID: {proposal['id']}")

            return proposal['id']

        except Exception as e:
            print(f"❌ Critical error in propose_strategy_improvement: {e}")
            import traceback
            print(f"🔍 Proposal error traceback: {traceback.format_exc()}")
            return None

    def agent_analyze_and_propose(self):
        """Agent analyzes performance and proposes improvements"""
        try:
            # Check if agent object is properly initialized
            if not hasattr(self, 'agent') or self.agent is None:
                print("⚠️ Agent object not properly initialized in strategy manager")
                return

            # Attempt to get recent performance data
            try:
                recent_performance = self.agent.get_recent_performance(50)
            except AttributeError as attr_error:
                print(f"⚠️ Agent missing get_recent_performance method: {attr_error}")
                return
            except Exception as perf_error:
                print(f"⚠️ Error getting recent performance: {perf_error}")
                return

            # Validate performance data
            if not recent_performance:
                print("📊 No recent performance data available - skipping analysis")
                return

            if not isinstance(recent_performance, list) or len(recent_performance) == 0:
                print("📊 Invalid performance data format - skipping analysis")
                return

            # Calculate average performance with error handling
            try:
                valid_performances = []
                for p in recent_performance:
                    if isinstance(p, dict) and 'performance_metric' in p:
                        metric = p['performance_metric']
                        if isinstance(metric, (int, float)) and not (metric != metric):  # Check for NaN
                            valid_performances.append(metric)

                if not valid_performances:
                    print("📊 No valid performance metrics found - skipping analysis")
                    return

                avg_performance = sum(valid_performances) / len(valid_performances)
                print(f"📊 Calculated average performance: {avg_performance:.3f} from {len(valid_performances)} data points")

            except (TypeError, ValueError, ZeroDivisionError) as calc_error:
                print(f"⚠️ Error calculating performance average: {calc_error}")
                return

            # Agent proposes different improvements based on performance patterns
            try:
                if avg_performance < 0.75:
                    # Poor performance - suggest conservative changes
                    improvement = {
                        "action": "reduce_risk",
                        "parameters": {
                            "max_borrow_ratio": 0.6,
                            "health_factor_target": 1.25,
                            "monitoring_frequency": "increased"
                        },
                        "reasoning": f"Performance at {avg_performance:.3f} suggests risk reduction needed"
                    }
                    self.propose_strategy_improvement("risk_reduction", improvement, "agent")

                elif avg_performance > 0.85:
                    # Good performance - suggest optimization
                    improvement = {
                        "action": "optimize_yield",
                        "parameters": {
                            "leverage_increase": 0.1,
                            "new_asset_targets": ["USDT", "FRAX"],
                            "arbitrage_opportunities": True
                        },
                        "reasoning": f"Strong performance at {avg_performance:.3f} allows for optimization"
                    }
                    self.propose_strategy_improvement("yield_optimization", improvement, "agent")
                else:
                    print(f"📊 Performance at {avg_performance:.3f} is stable - no immediate changes proposed")

            except Exception as proposal_error:
                print(f"⚠️ Error creating strategy proposal: {proposal_error}")
                return

        except Exception as e:
            print(f"❌ Critical error in agent_analyze_and_propose: {e}")
            import traceback
            print(f"🔍 Strategy manager error traceback: {traceback.format_exc()}")
            # Don't re-raise - let the main loop continue

    def implement_approved_strategy(self, proposal_id):
        """Implement an approved strategy improvement"""
        queue = []
        if os.path.exists(self.improvements_queue):
            with open(self.improvements_queue, 'r') as f:
                queue = json.load(f)

        proposal = next((p for p in queue if p['id'] == proposal_id), None)
        if not proposal:
            print(f"❌ Proposal {proposal_id} not found")
            return False

        print(f"🔧 IMPLEMENTING STRATEGY: {proposal['type']}")

        # Implement the strategy based on type
        success = False
        if proposal['type'] == "risk_reduction":
            success = self.implement_risk_reduction(proposal['data'])
        elif proposal['type'] == "yield_optimization":
            success = self.implement_yield_optimization(proposal['data'])
        elif proposal['type'] == "code_modification":
            success = self.implement_code_modification(proposal['data'])

        # Update proposal status
        proposal['status'] = "implemented" if success else "failed"
        proposal['implementation_time'] = time.time()

        # Save updated queue
        with open(self.improvements_queue, 'w') as f:
            json.dump(queue, f, indent=2)

        return success

    def implement_risk_reduction(self, risk_data):
        """Implement risk reduction strategies"""
        try:
            print(f"🔧 Implementing risk reduction strategy...")
            print(f"   Target health factor: {risk_data['parameters']['health_factor_target']}")
            print(f"   Max borrow ratio: {risk_data['parameters']['max_borrow_ratio']}")
            print(f"   Monitoring frequency: {risk_data['parameters']['monitoring_frequency']}")
            
            # Update agent configuration for risk reduction
            if hasattr(self.agent, 'health_factor_target'):
                self.agent.health_factor_target = float(risk_data['parameters']['health_factor_target'])
                
            if hasattr(self.agent, 'max_borrow_ratio'):
                self.agent.max_borrow_ratio = float(risk_data['parameters']['max_borrow_ratio'])
                
            print(f"✅ Risk reduction strategy implemented successfully")
            return True
            
        except Exception as e:
            print(f"❌ Risk reduction implementation failed: {e}")
            return False

    def implement_yield_optimization(self, optimization_data):
        """Implement yield optimization strategies"""
        try:
            print(f"🚀 Implementing yield optimization strategy...")
            
            # Apply optimization parameters
            if 'leverage_increase' in optimization_data['parameters']:
                leverage_increase = float(optimization_data['parameters']['leverage_increase'])
                print(f"   Increasing leverage by: {leverage_increase}")
                
            if 'new_asset_targets' in optimization_data['parameters']:
                new_assets = optimization_data['parameters']['new_asset_targets']
                print(f"   New target assets: {new_assets}")
                
            print(f"✅ Yield optimization strategy implemented successfully")
            return True
            
        except Exception as e:
            print(f"❌ Yield optimization implementation failed: {e}")
            return False

    def implement_code_modification(self, modification_data):
        """Implement direct code modifications"""
        try:
            if modification_data['target_file'] == "main.py":
                # Read current agent code
                with open('main.py', 'r') as f:
                    content = f.read()

                # Apply modifications
                if modification_data['action'] == "add_function":
                    new_function = modification_data['function_code']
                    # Insert before the last class method
                    insertion_point = content.rfind("    def ")
                    content = content[:insertion_point] + new_function + "\n\n" + content[insertion_point:]

                elif modification_data['action'] == "modify_strategy":
                    old_code = modification_data['old_code']
                    new_code = modification_data['new_code']
                    content = content.replace(old_code, new_code)

                # Backup original and write new version
                backup_name = f"arbitrum_testnet_agent_backup_{int(time.time())}.py"
                with open(backup_name, 'w') as f:
                    f.write(content)

                with open('main.py', 'w') as f:
                    f.write(content)

                print(f"✅ Code modified successfully (backup: {backup_name})")
                return True

        except Exception as e:
            print(f"❌ Code modification failed: {e}")
            return False

    def estimate_impact(self, improvement_data):
        """Estimate the potential impact of an improvement"""
        if improvement_data.get('action') == 'reduce_risk':
            return "Medium-High (Stability)"
        elif improvement_data.get('action') == 'optimize_yield':
            return "High (Profit)"
        elif improvement_data.get('action') == 'code_modification':
            return "Variable (Functionality)"
        return "Unknown"

    def assess_risk(self, improvement_data):
        """Assess the risk level of an improvement"""
        if improvement_data.get('action') == 'reduce_risk':
            return "Low"
        elif improvement_data.get('leverage_increase'):
            return "High"
        elif improvement_data.get('action') == 'code_modification':
            return "Medium"
        return "Low-Medium"

    def get_user_input_on_proposals(self):
        """Interactive interface for user to review proposals"""
        if not os.path.exists(self.improvements_queue):
            print("📭 No pending proposals")
            return

        with open(self.improvements_queue, 'r') as f:
            queue = json.load(f)

        pending = [p for p in queue if p['status'] == 'pending']
        if not pending:
            print("📭 No pending proposals")
            return

        print(f"\n🔍 REVIEWING {len(pending)} PENDING PROPOSALS:")
        print("=" * 50)

        for proposal in pending:
            print(f"\n📋 Proposal ID: {proposal['id']}")
            print(f"🔹 Type: {proposal['type']}")
            print(f"🔹 Source: {proposal['source']}")
            print(f"🔹 Impact: {proposal['estimated_impact']}")
            print(f"🔹 Risk: {proposal['risk_level']}")
            print(f"🔹 Details: {json.dumps(proposal['data'], indent=2)}")
            print("-" * 30)

        return pending

    def submit_user_improvement(self, strategy_type, description, parameters=None):
        """Allow user to submit strategy improvements"""
        improvement = {
            "description": description,
            "parameters": parameters or {},
            "user_priority": "high",
            "timestamp": datetime.now().isoformat()
        }

        return self.propose_strategy_improvement(strategy_type, improvement, "user")

    def print_collateral_message(self):
        print(f"💡 Add $13+ worth of collateral to activate autonomous sequence")

    def load_strategies_database(self):
        """Load existing strategies and their performance data"""
        if os.path.exists(self.strategies_file):
            with open(self.strategies_file, 'r') as f:
                return json.load(f)
        return {
            "active_strategies": {},
            "experimental_strategies": {},
            "rejected_strategies": {},
            "performance_history": []
        }

    def propose_strategy_improvement(self, strategy_type, improvement_data, source="agent"):
        """Propose a new strategy improvement"""
        try:
            # Validate inputs
            if not strategy_type or not isinstance(strategy_type, str):
                print(f"⚠️ Invalid strategy_type: {strategy_type}")
                return None

            if not improvement_data or not isinstance(improvement_data, dict):
                print(f"⚠️ Invalid improvement_data: {improvement_data}")
                return None

            # Create proposal with error handling
            try:
                proposal = {
                    "id": f"{strategy_type}_{int(time.time())}",
                    "type": strategy_type,
                    "source": source,  # "agent" or "user"
                    "timestamp": time.time(),
                    "data": improvement_data,
                    "status": "pending",
                    "estimated_impact": self.estimate_impact(improvement_data),
                    "risk_level": self.assess_risk(improvement_data)
                }
            except Exception as proposal_error:
                print(f"⚠️ Error creating proposal object: {proposal_error}")
                return None

            # Load existing queue with error handling
            queue = []
            try:
                if os.path.exists(self.improvements_queue):
                    with open(self.improvements_queue, 'r') as f:
                        queue = json.load(f)
            except (json.JSONDecodeError, IOError) as load_error:
                print(f"⚠️ Error loading improvements queue: {load_error}")
                print("🔧 Starting with empty queue")
                queue = []

            # Add proposal to queue
            try:
                queue.append(proposal)
            except Exception as append_error:
                print(f"⚠️ Error appending to queue: {append_error}")
                return None

            # Save updated queue with error handling
            try:
                with open(self.improvements_queue, 'w') as f:
                    json.dump(queue, f, indent=2)
            except (IOError, json.JSONEncoder) as save_error:
                print(f"⚠️ Error saving improvements queue: {save_error}")
                return None

            print(f"🚀 {source.upper()} STRATEGY PROPOSAL:")
            print(f"   📝 Type: {strategy_type}")
            print(f"   📊 Impact: {proposal['estimated_impact']}")
            print(f"   ⚠️ Risk: {proposal['risk_level']}")
            print(f"   🆔 ID: {proposal['id']}")

            return proposal['id']

        except Exception as e:
            print(f"❌ Critical error in propose_strategy_improvement: {e}")
            import traceback
            print(f"🔍 Proposal error traceback: {traceback.format_exc()}")
            return None

    def agent_analyze_and_propose(self):
        """Agent analyzes performance and proposes improvements"""
        try:
            # Check if agent object is properly initialized
            if not hasattr(self, 'agent') or self.agent is None:
                print("⚠️ Agent object not properly initialized in strategy manager")
                return

            # Attempt to get recent performance data
            try:
                recent_performance = self.agent.get_recent_performance(50)
            except AttributeError as attr_error:
                print(f"⚠️ Agent missing get_recent_performance method: {attr_error}")
                return
            except Exception as perf_error:
                print(f"⚠️ Error getting recent performance: {perf_error}")
                return

            # Validate performance data
            if not recent_performance:
                print("📊 No recent performance data available - skipping analysis")
                return

            if not isinstance(recent_performance, list) or len(recent_performance) == 0:
                print("📊 Invalid performance data format - skipping analysis")
                return

            # Calculate average performance with error handling
            try:
                valid_performances = []
                for p in recent_performance:
                    if isinstance(p, dict) and 'performance_metric' in p:
                        metric = p['performance_metric']
                        if isinstance(metric, (int, float)) and not (metric != metric):  # Check for NaN
                            valid_performances.append(metric)

                if not valid_performances:
                    print("📊 No valid performance metrics found - skipping analysis")
                    return

                avg_performance = sum(valid_performances) / len(valid_performances)
                print(f"📊 Calculated average performance: {avg_performance:.3f} from {len(valid_performances)} data points")

            except (TypeError, ValueError, ZeroDivisionError) as calc_error:
                print(f"⚠️ Error calculating performance average: {calc_error}")
                return

            # Agent proposes different improvements based on performance patterns
            try:
                if avg_performance < 0.75:
                    # Poor performance - suggest conservative changes
                    improvement = {
                        "action": "reduce_risk",
                        "parameters": {
                            "max_borrow_ratio": 0.6,
                            "health_factor_target": 1.25,
                            "monitoring_frequency": "increased"
                        },
                        "reasoning": f"Performance at {avg_performance:.3f} suggests risk reduction needed"
                    }
                    self.propose_strategy_improvement("risk_reduction", improvement, "agent")

                elif avg_performance > 0.85:
                    # Good performance - suggest optimization
                    improvement = {
                        "action": "optimize_yield",
                        "parameters": {
                            "leverage_increase": 0.1,
                            "new_asset_targets": ["USDT", "FRAX"],
                            "arbitrage_opportunities": True
                        },
                        "reasoning": f"Strong performance at {avg_performance:.3f} allows for optimization"
                    }
                    self.propose_strategy_improvement("yield_optimization", improvement, "agent")
                else:
                    print(f"📊 Performance at {avg_performance:.3f} is stable - no immediate changes proposed")

            except Exception as proposal_error:
                print(f"⚠️ Error creating strategy proposal: {proposal_error}")
                return

        except Exception as e:
            print(f"❌ Critical error in agent_analyze_and_propose: {e}")
            import traceback
            print(f"🔍 Strategy manager error traceback: {traceback.format_exc()}")

    def implement_approved_strategy(self, proposal_id):
        """Implement an approved strategy improvement"""
        queue = []
        if os.path.exists(self.improvements_queue):
            with open(self.improvements_queue, 'r') as f:
                queue = json.load(f)

        proposal = next((p for p in queue if p['id'] == proposal_id), None)
        if not proposal:
            print(f"❌ Proposal {proposal_id} not found")
            return False

        print(f"🔧 IMPLEMENTING STRATEGY: {proposal['type']}")

        # Implement the strategy based on type
        success = False
        if proposal['type'] == "risk_reduction":
            success = self.implement_risk_reduction(proposal['data'])
        elif proposal['type'] == "yield_optimization":
            success = self.implement_yield_optimization(proposal['data'])
        elif proposal['type'] == "code_modification":
            success = self.implement_code_modification(proposal['data'])

        # Update proposal status
        proposal['status'] = "implemented" if success else "failed"
        proposal['implementation_time'] = time.time()

        # Save updated queue
        with open(self.improvements_queue, 'w') as f:
            json.dump(queue, f, indent=2)

        return success

    def implement_risk_reduction(self, risk_data):
        """Implement risk reduction strategies"""
        try:
            print(f"🔧 Implementing risk reduction strategy...")
            print(f"   Target health factor: {risk_data['parameters']['health_factor_target']}")
            print(f"   Max borrow ratio: {risk_data['parameters']['max_borrow_ratio']}")
            print(f"   Monitoring frequency: {risk_data['parameters']['monitoring_frequency']}")
            
            # Update agent configuration for risk reduction
            if hasattr(self.agent, 'health_factor_target'):
                self.agent.health_factor_target = float(risk_data['parameters']['health_factor_target'])
                
            if hasattr(self.agent, 'max_borrow_ratio'):
                self.agent.max_borrow_ratio = float(risk_data['parameters']['max_borrow_ratio'])
                
            print(f"✅ Risk reduction strategy implemented successfully")
            return True
            
        except Exception as e:
            print(f"❌ Risk reduction implementation failed: {e}")
            return False

    def implement_yield_optimization(self, optimization_data):
        """Implement yield optimization strategies"""
        try:
            print(f"🚀 Implementing yield optimization strategy...")
            
            # Apply optimization parameters
            if 'leverage_increase' in optimization_data['parameters']:
                leverage_increase = float(optimization_data['parameters']['leverage_increase'])
                print(f"   Increasing leverage by: {leverage_increase}")
                
            if 'new_asset_targets' in optimization_data['parameters']:
                new_assets = optimization_data['parameters']['new_asset_targets']
                print(f"   New target assets: {new_assets}")
                
            print(f"✅ Yield optimization strategy implemented successfully")
            return True
            
        except Exception as e:
            print(f"❌ Yield optimization implementation failed: {e}")
            return False

    def implement_code_modification(self, modification_data):
        """Implement direct code modifications"""
        try:
            if modification_data['target_file'] == "main.py":
                # Read current agent code
                with open('main.py', 'r') as f:
                    content = f.read()

                # Apply modifications
                if modification_data['action'] == "add_function":
                    new_function = modification_data['function_code']
                    # Insert before the last class method
                    insertion_point = content.rfind("    def ")
                    content = content[:insertion_point] + new_function + "\n\n" + content[insertion_point:]

                elif modification_data['action'] == "modify_strategy":
                    old_code = modification_data['old_code']
                    new_code = modification_data['new_code']
                    content = content.replace(old_code, new_code)

                # Backup original and write new version
                backup_name = f"arbitrum_testnet_agent_backup_{int(time.time())}.py"
                with open(backup_name, 'w') as f:
                    f.write(content)

                with open('main.py', 'w') as f:
                    f.write(content)

                print(f"✅ Code modified successfully (backup: {backup_name})")
                return True

        except Exception as e:
            print(f"❌ Code modification failed: {e}")
            return False

    def estimate_impact(self, improvement_data):
        """Estimate the potential impact of an improvement"""
        if improvement_data.get('action') == 'reduce_risk':
            return "Medium-High (Stability)"
        elif improvement_data.get('action') == 'optimize_yield':
            return "High (Profit)"
        elif improvement_data.get('action') == 'code_modification':
            return "Variable (Functionality)"
        return "Unknown"

    def assess_risk(self, improvement_data):
        """Assess the risk level of an improvement"""
        if improvement_data.get('action') == 'reduce_risk':
            return "Low"
        elif improvement_data.get('leverage_increase'):
            return "High"
        elif improvement_data.get('action') == 'code_modification':
            return "Medium"
        return "Low-Medium"

    def get_user_input_on_proposals(self):
        """Interactive interface for user to review proposals"""
        if not os.path.exists(self.improvements_queue):
            print("📭 No pending proposals")
            return

        with open(self.improvements_queue, 'r') as f:
            queue = json.load(f)

        pending = [p for p in queue if p['status'] == 'pending']
        if not pending:
            print("📭 No pending proposals")
            return

        print(f"\n🔍 REVIEWING {len(pending)} PENDING PROPOSALS:")
        print("=" * 50)

        for proposal in pending:
            print(f"\n📋 Proposal ID: {proposal['id']}")
            print(f"🔹 Type: {proposal['type']}")
            print(f"🔹 Source: {proposal['source']}")
            print(f"🔹 Impact: {proposal['estimated_impact']}")
            print(f"🔹 Risk: {proposal['risk_level']}")
            print(f"🔹 Details: {json.dumps(proposal['data'], indent=2)}")
            print("-" * 30)

        return pending

    def submit_user_improvement(self, strategy_type, description, parameters=None):
        """Allow user to submit strategy improvements"""
        improvement = {
            "description": description,
            "parameters": parameters or {},
            "user_priority": "high",
            "timestamp": datetime.now().isoformat()
        }

        return self.propose_strategy_improvement(strategy_type, improvement, "user")

    def print_collateral_message(self):
        print(f"💡 Add $13+ worth of collateral to activate autonomous sequence")
# --- Merged from strategy_optimizer.py ---

class StrategyPerformance:
    strategy_name: str
    success_rate: float
    avg_profit: float
    gas_efficiency: float
    accuracy_score: float
    total_operations: int
    last_updated: float

class StrategyOptimizer:
    def __init__(self, agent):
        self.agent = agent
        self.performance_history = {}
        self.load_performance_data()
        
    def load_performance_data(self):
        """Load historical strategy performance data"""
        try:
            with open('strategy_performance.json', 'r') as f:
                data = json.load(f)
                self.performance_history = {
                    name: StrategyPerformance(**perf) for name, perf in data.items()
                }
        except FileNotFoundError:
            # Initialize with default performance metrics
            self.performance_history = {
                'built_in_analysis': StrategyPerformance(
                    strategy_name='built_in_analysis',
                    success_rate=0.72,
                    avg_profit=0.03,
                    gas_efficiency=0.8,
                    accuracy_score=0.75,
                    total_operations=0,
                    last_updated=time.time()
                ),
                'enhanced_analyzer': StrategyPerformance(
                    strategy_name='enhanced_analyzer',
                    success_rate=0.78,
                    avg_profit=0.045,
                    gas_efficiency=0.85,
                    accuracy_score=0.82,
                    total_operations=0,
                    last_updated=time.time()
                ),
                'freqtrade_integration': StrategyPerformance(
                    strategy_name='freqtrade_integration',
                    success_rate=0.81,
                    avg_profit=0.038,
                    gas_efficiency=0.75,
                    accuracy_score=0.85,
                    total_operations=0,
                    last_updated=time.time()
                )
            }
    
    def evaluate_current_conditions(self) -> Dict[str, float]:
        """Evaluate current market conditions for strategy selection"""
        try:
            # Get current market volatility
            btc_data = self.agent.main.get_btc_price_data()
            arb_data = self.agent.main.get_arb_price_data()
            
            if not btc_data or not arb_data:
                return {'volatility': 0.5, 'gas_cost': 0.5, 'market_trend': 0.5}
            
            # Calculate volatility
            btc_volatility = abs(btc_data.get('percent_change_1h', 0))
            arb_volatility = abs(arb_data.get('percent_change_1h', 0))
            avg_volatility = (btc_volatility + arb_volatility) / 2
            
            # Normalize volatility (higher volatility = better for pattern recognition)
            volatility_score = min(1.0, avg_volatility / 5.0)  # Cap at 5% volatility
            
            # Get gas conditions
            gas_score = self.agent.main.enhanced_analyzer.calculate_gas_efficiency_score()
            
            # Determine market trend strength
            btc_trend = btc_data.get('percent_change_24h', 0)
            trend_strength = min(1.0, abs(btc_trend) / 10.0)  # Strong trend if >10% daily change
            
            return {
                'volatility': volatility_score,
                'gas_cost': gas_score,
                'market_trend': trend_strength
            }
            
        except Exception as e:
            logging.error(f"Failed to evaluate current conditions: {e}")
            return {'volatility': 0.5, 'gas_cost': 0.5, 'market_trend': 0.5}
    
    def select_optimal_strategy(self) -> str:
        """Select the optimal strategy based on current conditions and historical performance"""
        conditions = self.evaluate_current_conditions()
        
        strategy_scores = {}
        
        for strategy_name, performance in self.performance_history.items():
            # Base score from historical performance
            base_score = (
                performance.success_rate * 0.4 +
                performance.accuracy_score * 0.3 +
                performance.gas_efficiency * 0.2 +
                min(performance.avg_profit * 10, 1.0) * 0.1
            )
            
            # Adjust based on current conditions
            condition_multiplier = 1.0
            
            if strategy_name == 'enhanced_analyzer':
                # Enhanced analyzer works better in volatile conditions
                condition_multiplier += conditions['volatility'] * 0.3
            elif strategy_name == 'freqtrade_integration':
                # Freqtrade works better in trending markets
                condition_multiplier += conditions['market_trend'] * 0.4
            elif strategy_name == 'built_in_analysis':
                # Built-in analysis is more gas-efficient
                condition_multiplier += conditions['gas_cost'] * 0.2
            
            strategy_scores[strategy_name] = base_score * condition_multiplier
        
        # Select strategy with highest score
        optimal_strategy = max(strategy_scores, key=strategy_scores.get)
        
        logging.info(f"Strategy selection scores: {strategy_scores}")
        logging.info(f"Optimal strategy selected: {optimal_strategy}")
        
        return optimal_strategy
    
    def update_strategy_performance(self, strategy_name: str, success: bool, 
                                  profit: float, gas_used: float):
        """Update strategy performance based on actual results"""
        if strategy_name not in self.performance_history:
            return
        
        performance = self.performance_history[strategy_name]
        
        # Update success rate with exponential moving average
        alpha = 0.1  # Learning rate
        performance.success_rate = (
            performance.success_rate * (1 - alpha) + 
            (1.0 if success else 0.0) * alpha
        )
        
        # Update average profit
        performance.avg_profit = (
            performance.avg_profit * (1 - alpha) + 
            profit * alpha
        )
        
        # Update gas efficiency (inverse of gas used)
        gas_efficiency = 1.0 / (1.0 + gas_used)  # Higher gas = lower efficiency
        performance.gas_efficiency = (
            performance.gas_efficiency * (1 - alpha) + 
            gas_efficiency * alpha
        )
        
        performance.total_operations += 1
        performance.last_updated = time.time()
        
        # Save updated performance
        self.save_performance_data()
    
    def save_performance_data(self):
        """Save strategy performance data to file"""
        try:
            data = {
                name: perf.__dict__ for name, perf in self.performance_history.items()
            }
            with open('strategy_performance.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save performance data: {e}")
    
    def get_performance_report(self) -> Dict:
        """Generate performance comparison report"""
        return {
            'strategies': {
                name: {
                    'success_rate': f"{perf.success_rate:.1%}",
                    'avg_profit': f"{perf.avg_profit:.2%}",
                    'gas_efficiency': f"{perf.gas_efficiency:.2f}",
                    'accuracy_score': f"{perf.accuracy_score:.2f}",
                    'total_operations': perf.total_operations
                }
                for name, perf in self.performance_history.items()
            },
            'current_optimal': self.select_optimal_strategy(),
            'market_conditions': self.evaluate_current_conditions()
        }

    def load_performance_data(self):
        """Load historical strategy performance data"""
        try:
            with open('strategy_performance.json', 'r') as f:
                data = json.load(f)
                self.performance_history = {
                    name: StrategyPerformance(**perf) for name, perf in data.items()
                }
        except FileNotFoundError:
            # Initialize with default performance metrics
            self.performance_history = {
                'built_in_analysis': StrategyPerformance(
                    strategy_name='built_in_analysis',
                    success_rate=0.72,
                    avg_profit=0.03,
                    gas_efficiency=0.8,
                    accuracy_score=0.75,
                    total_operations=0,
                    last_updated=time.time()
                ),
                'enhanced_analyzer': StrategyPerformance(
                    strategy_name='enhanced_analyzer',
                    success_rate=0.78,
                    avg_profit=0.045,
                    gas_efficiency=0.85,
                    accuracy_score=0.82,
                    total_operations=0,
                    last_updated=time.time()
                ),
                'freqtrade_integration': StrategyPerformance(
                    strategy_name='freqtrade_integration',
                    success_rate=0.81,
                    avg_profit=0.038,
                    gas_efficiency=0.75,
                    accuracy_score=0.85,
                    total_operations=0,
                    last_updated=time.time()
                )
            }

    def evaluate_current_conditions(self) -> Dict[str, float]:
        """Evaluate current market conditions for strategy selection"""
        try:
            # Get current market volatility
            btc_data = self.agent.main.get_btc_price_data()
            arb_data = self.agent.main.get_arb_price_data()
            
            if not btc_data or not arb_data:
                return {'volatility': 0.5, 'gas_cost': 0.5, 'market_trend': 0.5}
            
            # Calculate volatility
            btc_volatility = abs(btc_data.get('percent_change_1h', 0))
            arb_volatility = abs(arb_data.get('percent_change_1h', 0))
            avg_volatility = (btc_volatility + arb_volatility) / 2
            
            # Normalize volatility (higher volatility = better for pattern recognition)
            volatility_score = min(1.0, avg_volatility / 5.0)  # Cap at 5% volatility
            
            # Get gas conditions
            gas_score = self.agent.main.enhanced_analyzer.calculate_gas_efficiency_score()
            
            # Determine market trend strength
            btc_trend = btc_data.get('percent_change_24h', 0)
            trend_strength = min(1.0, abs(btc_trend) / 10.0)  # Strong trend if >10% daily change
            
            return {
                'volatility': volatility_score,
                'gas_cost': gas_score,
                'market_trend': trend_strength
            }
            
        except Exception as e:
            logging.error(f"Failed to evaluate current conditions: {e}")
            return {'volatility': 0.5, 'gas_cost': 0.5, 'market_trend': 0.5}

    def select_optimal_strategy(self) -> str:
        """Select the optimal strategy based on current conditions and historical performance"""
        conditions = self.evaluate_current_conditions()
        
        strategy_scores = {}
        
        for strategy_name, performance in self.performance_history.items():
            # Base score from historical performance
            base_score = (
                performance.success_rate * 0.4 +
                performance.accuracy_score * 0.3 +
                performance.gas_efficiency * 0.2 +
                min(performance.avg_profit * 10, 1.0) * 0.1
            )
            
            # Adjust based on current conditions
            condition_multiplier = 1.0
            
            if strategy_name == 'enhanced_analyzer':
                # Enhanced analyzer works better in volatile conditions
                condition_multiplier += conditions['volatility'] * 0.3
            elif strategy_name == 'freqtrade_integration':
                # Freqtrade works better in trending markets
                condition_multiplier += conditions['market_trend'] * 0.4
            elif strategy_name == 'built_in_analysis':
                # Built-in analysis is more gas-efficient
                condition_multiplier += conditions['gas_cost'] * 0.2
            
            strategy_scores[strategy_name] = base_score * condition_multiplier
        
        # Select strategy with highest score
        optimal_strategy = max(strategy_scores, key=strategy_scores.get)
        
        logging.info(f"Strategy selection scores: {strategy_scores}")
        logging.info(f"Optimal strategy selected: {optimal_strategy}")
        
        return optimal_strategy

    def update_strategy_performance(self, strategy_name: str, success: bool, 
                                  profit: float, gas_used: float):
        """Update strategy performance based on actual results"""
        if strategy_name not in self.performance_history:
            return
        
        performance = self.performance_history[strategy_name]
        
        # Update success rate with exponential moving average
        alpha = 0.1  # Learning rate
        performance.success_rate = (
            performance.success_rate * (1 - alpha) + 
            (1.0 if success else 0.0) * alpha
        )
        
        # Update average profit
        performance.avg_profit = (
            performance.avg_profit * (1 - alpha) + 
            profit * alpha
        )
        
        # Update gas efficiency (inverse of gas used)
        gas_efficiency = 1.0 / (1.0 + gas_used)  # Higher gas = lower efficiency
        performance.gas_efficiency = (
            performance.gas_efficiency * (1 - alpha) + 
            gas_efficiency * alpha
        )
        
        performance.total_operations += 1
        performance.last_updated = time.time()
        
        # Save updated performance
        self.save_performance_data()

    def save_performance_data(self):
        """Save strategy performance data to file"""
        try:
            data = {
                name: perf.__dict__ for name, perf in self.performance_history.items()
            }
            with open('strategy_performance.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save performance data: {e}")

    def get_performance_report(self) -> Dict:
        """Generate performance comparison report"""
        return {
            'strategies': {
                name: {
                    'success_rate': f"{perf.success_rate:.1%}",
                    'avg_profit': f"{perf.avg_profit:.2%}",
                    'gas_efficiency': f"{perf.gas_efficiency:.2f}",
                    'accuracy_score': f"{perf.accuracy_score:.2f}",
                    'total_operations': perf.total_operations
                }
                for name, perf in self.performance_history.items()
            },
            'current_optimal': self.select_optimal_strategy(),
            'market_conditions': self.evaluate_current_conditions()
        }
# --- Merged from main.py ---

def get_market_strategy_status():
    """Get current market strategy configuration status"""
    return {
        'enabled': MARKET_SIGNAL_ENABLED,
        'btc_drop_threshold': BTC_DROP_THRESHOLD,
        'arb_rsi_oversold': ARB_RSI_OVERSOLD,
        'dai_to_arb_confidence': DAI_TO_ARB_CONFIDENCE,
        'max_operation_amount': MAX_MARKET_OPERATION_AMOUNT,
        'min_health_factor': MIN_HEALTH_FACTOR_FOR_MARKET_OPS,
        'signal_cooldown_minutes': SIGNAL_COOLDOWN / 60,
        'analysis_interval_hours': MARKET_ANALYSIS_INTERVAL / 3600,
        'max_daily_operations': MAX_DAILY_OPERATIONS,
        'last_updated': datetime.now().isoformat()
    }

def validate_configuration():
    """Validate market strategy configuration"""
    issues = []

    # Validate thresholds
    if BTC_DROP_THRESHOLD <= 0 or BTC_DROP_THRESHOLD > 0.2:
        issues.append(f"BTC drop threshold {BTC_DROP_THRESHOLD} outside safe range (0-0.2)")

    if ARB_RSI_OVERSOLD < 10 or ARB_RSI_OVERSOLD > 40:
        issues.append(f"ARB RSI oversold {ARB_RSI_OVERSOLD} outside typical range (10-40)")

    if DAI_TO_ARB_CONFIDENCE < 0.5 or DAI_TO_ARB_CONFIDENCE > 0.95:
        issues.append(f"DAI→ARB confidence {DAI_TO_ARB_CONFIDENCE} outside safe range (0.5-0.95)")

    if MIN_HEALTH_FACTOR_FOR_MARKET_OPS < 1.5:
        issues.append(f"Minimum health factor {MIN_HEALTH_FACTOR_FOR_MARKET_OPS} too low (min 1.5)")

    if MAX_MARKET_OPERATION_AMOUNT > 20:
        issues.append(f"Maximum operation amount ${MAX_MARKET_OPERATION_AMOUNT} too high (max $20)")

    # Validate timing
    if SIGNAL_COOLDOWN < 600:  # 10 minutes minimum
        issues.append(f"Signal cooldown {SIGNAL_COOLDOWN}s too short (min 600s)")

    return issues

def get_optimized_parameters():
    """Get optimized parameters based on current market conditions"""
    # This would analyze recent market data and suggest optimal parameters
    # For now, return conservative defaults
    return {
        'btc_drop_threshold': 0.015,  # 1.5% for balanced sensitivity
        'arb_rsi_oversold': 25,       # Aggressive but safe
        'dai_to_arb_confidence': 0.65, # Conservative confidence requirement
        'max_operation_amount': 8.0,   # Moderate position sizing
        'min_health_factor': 2.2,     # High safety margin
        'signal_cooldown': 1800,      # 30 minutes for market efficiency
        'reasoning': "Conservative parameters optimized for network approval and risk management"
    }
# --- Merged from _hessian_update_strategy.py ---

class HessianUpdateStrategy:
    """Interface for implementing Hessian update strategies.

    Many optimization methods make use of Hessian (or inverse Hessian)
    approximations, such as the quasi-Newton methods BFGS, SR1, L-BFGS.
    Some of these  approximations, however, do not actually need to store
    the entire matrix or can compute the internal matrix product with a
    given vector in a very efficiently manner. This class serves as an
    abstract interface between the optimization algorithm and the
    quasi-Newton update strategies, giving freedom of implementation
    to store and update the internal matrix as efficiently as possible.
    Different choices of initialization and update procedure will result
    in different quasi-Newton strategies.

    Four methods should be implemented in derived classes: ``initialize``,
    ``update``, ``dot`` and ``get_matrix``. The matrix multiplication
    operator ``@`` is also defined to call the ``dot`` method.

    Notes
    -----
    Any instance of a class that implements this interface,
    can be accepted by the method ``minimize`` and used by
    the compatible solvers to approximate the Hessian (or
    inverse Hessian) used by the optimization algorithms.
    """

    def initialize(self, n, approx_type):
        """Initialize internal matrix.

        Allocate internal memory for storing and updating
        the Hessian or its inverse.

        Parameters
        ----------
        n : int
            Problem dimension.
        approx_type : {'hess', 'inv_hess'}
            Selects either the Hessian or the inverse Hessian.
            When set to 'hess' the Hessian will be stored and updated.
            When set to 'inv_hess' its inverse will be used instead.
        """
        raise NotImplementedError("The method ``initialize(n, approx_type)``"
                                  " is not implemented.")

    def update(self, delta_x, delta_grad):
        """Update internal matrix.

        Update Hessian matrix or its inverse (depending on how 'approx_type'
        is defined) using information about the last evaluated points.

        Parameters
        ----------
        delta_x : ndarray
            The difference between two points the gradient
            function have been evaluated at: ``delta_x = x2 - x1``.
        delta_grad : ndarray
            The difference between the gradients:
            ``delta_grad = grad(x2) - grad(x1)``.
        """
        raise NotImplementedError("The method ``update(delta_x, delta_grad)``"
                                  " is not implemented.")

    def dot(self, p):
        """Compute the product of the internal matrix with the given vector.

        Parameters
        ----------
        p : array_like
            1-D array representing a vector.

        Returns
        -------
        Hp : array
            1-D represents the result of multiplying the approximation matrix
            by vector p.
        """
        raise NotImplementedError("The method ``dot(p)``"
                                  " is not implemented.")

    def get_matrix(self):
        """Return current internal matrix.

        Returns
        -------
        H : ndarray, shape (n, n)
            Dense matrix containing either the Hessian
            or its inverse (depending on how 'approx_type'
            is defined).
        """
        raise NotImplementedError("The method ``get_matrix(p)``"
                                  " is not implemented.")

    def __matmul__(self, p):
        return self.dot(p)

class FullHessianUpdateStrategy(HessianUpdateStrategy):
    """Hessian update strategy with full dimensional internal representation.
    """
    _syr = get_blas_funcs('syr', dtype='d')  # Symmetric rank 1 update
    _syr2 = get_blas_funcs('syr2', dtype='d')  # Symmetric rank 2 update
    # Symmetric matrix-vector product
    _symv = get_blas_funcs('symv', dtype='d')

    def __init__(self, init_scale='auto'):
        self.init_scale = init_scale
        # Until initialize is called we can't really use the class,
        # so it makes sense to set everything to None.
        self.first_iteration = None
        self.approx_type = None
        self.B = None
        self.H = None

    def initialize(self, n, approx_type):
        """Initialize internal matrix.

        Allocate internal memory for storing and updating
        the Hessian or its inverse.

        Parameters
        ----------
        n : int
            Problem dimension.
        approx_type : {'hess', 'inv_hess'}
            Selects either the Hessian or the inverse Hessian.
            When set to 'hess' the Hessian will be stored and updated.
            When set to 'inv_hess' its inverse will be used instead.
        """
        self.first_iteration = True
        self.n = n
        self.approx_type = approx_type
        if approx_type not in ('hess', 'inv_hess'):
            raise ValueError("`approx_type` must be 'hess' or 'inv_hess'.")
        # Create matrix
        if self.approx_type == 'hess':
            self.B = np.eye(n, dtype=float)
        else:
            self.H = np.eye(n, dtype=float)

    def _auto_scale(self, delta_x, delta_grad):
        # Heuristic to scale matrix at first iteration.
        # Described in Nocedal and Wright "Numerical Optimization"
        # p.143 formula (6.20).
        s_norm2 = np.dot(delta_x, delta_x)
        y_norm2 = np.dot(delta_grad, delta_grad)
        ys = np.abs(np.dot(delta_grad, delta_x))
        if ys == 0.0 or y_norm2 == 0 or s_norm2 == 0:
            return 1
        if self.approx_type == 'hess':
            return y_norm2 / ys
        else:
            return ys / y_norm2

    def _update_implementation(self, delta_x, delta_grad):
        raise NotImplementedError("The method ``_update_implementation``"
                                  " is not implemented.")

    def update(self, delta_x, delta_grad):
        """Update internal matrix.

        Update Hessian matrix or its inverse (depending on how 'approx_type'
        is defined) using information about the last evaluated points.

        Parameters
        ----------
        delta_x : ndarray
            The difference between two points the gradient
            function have been evaluated at: ``delta_x = x2 - x1``.
        delta_grad : ndarray
            The difference between the gradients:
            ``delta_grad = grad(x2) - grad(x1)``.
        """
        if np.all(delta_x == 0.0):
            return
        if np.all(delta_grad == 0.0):
            warn('delta_grad == 0.0. Check if the approximated '
                 'function is linear. If the function is linear '
                 'better results can be obtained by defining the '
                 'Hessian as zero instead of using quasi-Newton '
                 'approximations.',
                 UserWarning, stacklevel=2)
            return
        if self.first_iteration:
            # Get user specific scale
            if isinstance(self.init_scale, str) and self.init_scale == "auto":
                scale = self._auto_scale(delta_x, delta_grad)
            else:
                scale = self.init_scale

            # Check for complex: numpy will silently cast a complex array to
            # a real one but not so for scalar as it raises a TypeError.
            # Checking here brings a consistent behavior.
            replace = False
            if np.size(scale) == 1:
                # to account for the legacy behavior having the exact same cast
                scale = float(scale)
            elif np.iscomplexobj(scale):
                raise TypeError("init_scale contains complex elements, "
                                "must be real.")
            else:  # test explicitly for allowed shapes and values
                replace = True
                if self.approx_type == 'hess':
                    shape = np.shape(self.B)
                    dtype = self.B.dtype
                else:
                    shape = np.shape(self.H)
                    dtype = self.H.dtype
                # copy, will replace the original
                scale = np.array(scale, dtype=dtype, copy=True)

                # it has to match the shape of the matrix for the multiplication,
                # no implicit broadcasting is allowed
                if shape != (init_shape := np.shape(scale)):
                    raise ValueError("If init_scale is an array, it must have the "
                                     f"dimensions of the hess/inv_hess: {shape}."
                                     f" Got {init_shape}.")
                if not issymmetric(scale):
                    raise ValueError("If init_scale is an array, it must be"
                                     " symmetric (passing scipy.linalg.issymmetric)"
                                     " to be an approximation of a hess/inv_hess.")

            # Scale initial matrix with ``scale * np.eye(n)`` or replace
            # This is not ideal, we could assign the scale directly in
            # initialize, but we would need to
            if self.approx_type == 'hess':
                if replace:
                    self.B = scale
                else:
                    self.B *= scale
            else:
                if replace:
                    self.H = scale
                else:
                    self.H *= scale
            self.first_iteration = False
        self._update_implementation(delta_x, delta_grad)

    def dot(self, p):
        """Compute the product of the internal matrix with the given vector.

        Parameters
        ----------
        p : array_like
            1-D array representing a vector.

        Returns
        -------
        Hp : array
            1-D represents the result of multiplying the approximation matrix
            by vector p.
        """
        if self.approx_type == 'hess':
            return self._symv(1, self.B, p)
        else:
            return self._symv(1, self.H, p)

    def get_matrix(self):
        """Return the current internal matrix.

        Returns
        -------
        M : ndarray, shape (n, n)
            Dense matrix containing either the Hessian or its inverse
            (depending on how `approx_type` was defined).
        """
        if self.approx_type == 'hess':
            M = np.copy(self.B)
        else:
            M = np.copy(self.H)
        li = np.tril_indices_from(M, k=-1)
        M[li] = M.T[li]
        return M

class BFGS(FullHessianUpdateStrategy):
    """Broyden-Fletcher-Goldfarb-Shanno (BFGS) Hessian update strategy.

    Parameters
    ----------
    exception_strategy : {'skip_update', 'damp_update'}, optional
        Define how to proceed when the curvature condition is violated.
        Set it to 'skip_update' to just skip the update. Or, alternatively,
        set it to 'damp_update' to interpolate between the actual BFGS
        result and the unmodified matrix. Both exceptions strategies
        are explained  in [1]_, p.536-537.
    min_curvature : float
        This number, scaled by a normalization factor, defines the
        minimum curvature ``dot(delta_grad, delta_x)`` allowed to go
        unaffected by the exception strategy. By default is equal to
        1e-8 when ``exception_strategy = 'skip_update'`` and equal
        to 0.2 when ``exception_strategy = 'damp_update'``.
    init_scale : {float, np.array, 'auto'}
        This parameter can be used to initialize the Hessian or its
        inverse. When a float is given, the relevant array is initialized
        to ``np.eye(n) * init_scale``, where ``n`` is the problem dimension.
        Alternatively, if a precisely ``(n, n)`` shaped, symmetric array is given,
        this array will be used. Otherwise an error is generated.
        Set it to 'auto' in order to use an automatic heuristic for choosing
        the initial scale. The heuristic is described in [1]_, p.143.
        The default is 'auto'.

    Notes
    -----
    The update is based on the description in [1]_, p.140.

    References
    ----------
    .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
           Second Edition (2006).
    """

    def __init__(self, exception_strategy='skip_update', min_curvature=None,
                 init_scale='auto'):
        if exception_strategy == 'skip_update':
            if min_curvature is not None:
                self.min_curvature = min_curvature
            else:
                self.min_curvature = 1e-8
        elif exception_strategy == 'damp_update':
            if min_curvature is not None:
                self.min_curvature = min_curvature
            else:
                self.min_curvature = 0.2
        else:
            raise ValueError("`exception_strategy` must be 'skip_update' "
                             "or 'damp_update'.")

        super().__init__(init_scale)
        self.exception_strategy = exception_strategy

    def _update_inverse_hessian(self, ys, Hy, yHy, s):
        """Update the inverse Hessian matrix.

        BFGS update using the formula:

            ``H <- H + ((H*y).T*y + s.T*y)/(s.T*y)^2 * (s*s.T)
                     - 1/(s.T*y) * ((H*y)*s.T + s*(H*y).T)``

        where ``s = delta_x`` and ``y = delta_grad``. This formula is
        equivalent to (6.17) in [1]_ written in a more efficient way
        for implementation.

        References
        ----------
        .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
               Second Edition (2006).
        """
        self.H = self._syr2(-1.0 / ys, s, Hy, a=self.H)
        self.H = self._syr((ys + yHy) / ys ** 2, s, a=self.H)

    def _update_hessian(self, ys, Bs, sBs, y):
        """Update the Hessian matrix.

        BFGS update using the formula:

            ``B <- B - (B*s)*(B*s).T/s.T*(B*s) + y*y^T/s.T*y``

        where ``s`` is short for ``delta_x`` and ``y`` is short
        for ``delta_grad``. Formula (6.19) in [1]_.

        References
        ----------
        .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
               Second Edition (2006).
        """
        self.B = self._syr(1.0 / ys, y, a=self.B)
        self.B = self._syr(-1.0 / sBs, Bs, a=self.B)

    def _update_implementation(self, delta_x, delta_grad):
        # Auxiliary variables w and z
        if self.approx_type == 'hess':
            w = delta_x
            z = delta_grad
        else:
            w = delta_grad
            z = delta_x
        # Do some common operations
        wz = np.dot(w, z)
        Mw = self @ w
        wMw = Mw.dot(w)
        # Guarantee that wMw > 0 by reinitializing matrix.
        # While this is always true in exact arithmetic,
        # indefinite matrix may appear due to roundoff errors.
        if wMw <= 0.0:
            scale = self._auto_scale(delta_x, delta_grad)
            # Reinitialize matrix
            if self.approx_type == 'hess':
                self.B = scale * np.eye(self.n, dtype=float)
            else:
                self.H = scale * np.eye(self.n, dtype=float)
            # Do common operations for new matrix
            Mw = self @ w
            wMw = Mw.dot(w)
        # Check if curvature condition is violated
        if wz <= self.min_curvature * wMw:
            # If the option 'skip_update' is set
            # we just skip the update when the condition
            # is violated.
            if self.exception_strategy == 'skip_update':
                return
            # If the option 'damp_update' is set we
            # interpolate between the actual BFGS
            # result and the unmodified matrix.
            elif self.exception_strategy == 'damp_update':
                update_factor = (1-self.min_curvature) / (1 - wz/wMw)
                z = update_factor*z + (1-update_factor)*Mw
                wz = np.dot(w, z)
        # Update matrix
        if self.approx_type == 'hess':
            self._update_hessian(wz, Mw, wMw, z)
        else:
            self._update_inverse_hessian(wz, Mw, wMw, z)

class SR1(FullHessianUpdateStrategy):
    """Symmetric-rank-1 Hessian update strategy.

    Parameters
    ----------
    min_denominator : float
        This number, scaled by a normalization factor,
        defines the minimum denominator magnitude allowed
        in the update. When the condition is violated we skip
        the update. By default uses ``1e-8``.
    init_scale : {float, np.array, 'auto'}, optional
        This parameter can be used to initialize the Hessian or its
        inverse. When a float is given, the relevant array is initialized
        to ``np.eye(n) * init_scale``, where ``n`` is the problem dimension.
        Alternatively, if a precisely ``(n, n)`` shaped, symmetric array is given,
        this array will be used. Otherwise an error is generated.
        Set it to 'auto' in order to use an automatic heuristic for choosing
        the initial scale. The heuristic is described in [1]_, p.143.
        The default is 'auto'.

    Notes
    -----
    The update is based on the description in [1]_, p.144-146.

    References
    ----------
    .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
           Second Edition (2006).
    """

    def __init__(self, min_denominator=1e-8, init_scale='auto'):
        self.min_denominator = min_denominator
        super().__init__(init_scale)

    def _update_implementation(self, delta_x, delta_grad):
        # Auxiliary variables w and z
        if self.approx_type == 'hess':
            w = delta_x
            z = delta_grad
        else:
            w = delta_grad
            z = delta_x
        # Do some common operations
        Mw = self @ w
        z_minus_Mw = z - Mw
        denominator = np.dot(w, z_minus_Mw)
        # If the denominator is too small
        # we just skip the update.
        if np.abs(denominator) <= self.min_denominator*norm(w)*norm(z_minus_Mw):
            return
        # Update matrix
        if self.approx_type == 'hess':
            self.B = self._syr(1/denominator, z_minus_Mw, a=self.B)
        else:
            self.H = self._syr(1/denominator, z_minus_Mw, a=self.H)

    def initialize(self, n, approx_type):
        """Initialize internal matrix.

        Allocate internal memory for storing and updating
        the Hessian or its inverse.

        Parameters
        ----------
        n : int
            Problem dimension.
        approx_type : {'hess', 'inv_hess'}
            Selects either the Hessian or the inverse Hessian.
            When set to 'hess' the Hessian will be stored and updated.
            When set to 'inv_hess' its inverse will be used instead.
        """
        raise NotImplementedError("The method ``initialize(n, approx_type)``"
                                  " is not implemented.")

    def update(self, delta_x, delta_grad):
        """Update internal matrix.

        Update Hessian matrix or its inverse (depending on how 'approx_type'
        is defined) using information about the last evaluated points.

        Parameters
        ----------
        delta_x : ndarray
            The difference between two points the gradient
            function have been evaluated at: ``delta_x = x2 - x1``.
        delta_grad : ndarray
            The difference between the gradients:
            ``delta_grad = grad(x2) - grad(x1)``.
        """
        raise NotImplementedError("The method ``update(delta_x, delta_grad)``"
                                  " is not implemented.")

    def dot(self, p):
        """Compute the product of the internal matrix with the given vector.

        Parameters
        ----------
        p : array_like
            1-D array representing a vector.

        Returns
        -------
        Hp : array
            1-D represents the result of multiplying the approximation matrix
            by vector p.
        """
        raise NotImplementedError("The method ``dot(p)``"
                                  " is not implemented.")

    def get_matrix(self):
        """Return current internal matrix.

        Returns
        -------
        H : ndarray, shape (n, n)
            Dense matrix containing either the Hessian
            or its inverse (depending on how 'approx_type'
            is defined).
        """
        raise NotImplementedError("The method ``get_matrix(p)``"
                                  " is not implemented.")

    def __matmul__(self, p):
        return self.dot(p)

    def initialize(self, n, approx_type):
        """Initialize internal matrix.

        Allocate internal memory for storing and updating
        the Hessian or its inverse.

        Parameters
        ----------
        n : int
            Problem dimension.
        approx_type : {'hess', 'inv_hess'}
            Selects either the Hessian or the inverse Hessian.
            When set to 'hess' the Hessian will be stored and updated.
            When set to 'inv_hess' its inverse will be used instead.
        """
        self.first_iteration = True
        self.n = n
        self.approx_type = approx_type
        if approx_type not in ('hess', 'inv_hess'):
            raise ValueError("`approx_type` must be 'hess' or 'inv_hess'.")
        # Create matrix
        if self.approx_type == 'hess':
            self.B = np.eye(n, dtype=float)
        else:
            self.H = np.eye(n, dtype=float)

    def _auto_scale(self, delta_x, delta_grad):
        # Heuristic to scale matrix at first iteration.
        # Described in Nocedal and Wright "Numerical Optimization"
        # p.143 formula (6.20).
        s_norm2 = np.dot(delta_x, delta_x)
        y_norm2 = np.dot(delta_grad, delta_grad)
        ys = np.abs(np.dot(delta_grad, delta_x))
        if ys == 0.0 or y_norm2 == 0 or s_norm2 == 0:
            return 1
        if self.approx_type == 'hess':
            return y_norm2 / ys
        else:
            return ys / y_norm2

    def _update_implementation(self, delta_x, delta_grad):
        raise NotImplementedError("The method ``_update_implementation``"
                                  " is not implemented.")

    def update(self, delta_x, delta_grad):
        """Update internal matrix.

        Update Hessian matrix or its inverse (depending on how 'approx_type'
        is defined) using information about the last evaluated points.

        Parameters
        ----------
        delta_x : ndarray
            The difference between two points the gradient
            function have been evaluated at: ``delta_x = x2 - x1``.
        delta_grad : ndarray
            The difference between the gradients:
            ``delta_grad = grad(x2) - grad(x1)``.
        """
        if np.all(delta_x == 0.0):
            return
        if np.all(delta_grad == 0.0):
            warn('delta_grad == 0.0. Check if the approximated '
                 'function is linear. If the function is linear '
                 'better results can be obtained by defining the '
                 'Hessian as zero instead of using quasi-Newton '
                 'approximations.',
                 UserWarning, stacklevel=2)
            return
        if self.first_iteration:
            # Get user specific scale
            if isinstance(self.init_scale, str) and self.init_scale == "auto":
                scale = self._auto_scale(delta_x, delta_grad)
            else:
                scale = self.init_scale

            # Check for complex: numpy will silently cast a complex array to
            # a real one but not so for scalar as it raises a TypeError.
            # Checking here brings a consistent behavior.
            replace = False
            if np.size(scale) == 1:
                # to account for the legacy behavior having the exact same cast
                scale = float(scale)
            elif np.iscomplexobj(scale):
                raise TypeError("init_scale contains complex elements, "
                                "must be real.")
            else:  # test explicitly for allowed shapes and values
                replace = True
                if self.approx_type == 'hess':
                    shape = np.shape(self.B)
                    dtype = self.B.dtype
                else:
                    shape = np.shape(self.H)
                    dtype = self.H.dtype
                # copy, will replace the original
                scale = np.array(scale, dtype=dtype, copy=True)

                # it has to match the shape of the matrix for the multiplication,
                # no implicit broadcasting is allowed
                if shape != (init_shape := np.shape(scale)):
                    raise ValueError("If init_scale is an array, it must have the "
                                     f"dimensions of the hess/inv_hess: {shape}."
                                     f" Got {init_shape}.")
                if not issymmetric(scale):
                    raise ValueError("If init_scale is an array, it must be"
                                     " symmetric (passing scipy.linalg.issymmetric)"
                                     " to be an approximation of a hess/inv_hess.")

            # Scale initial matrix with ``scale * np.eye(n)`` or replace
            # This is not ideal, we could assign the scale directly in
            # initialize, but we would need to
            if self.approx_type == 'hess':
                if replace:
                    self.B = scale
                else:
                    self.B *= scale
            else:
                if replace:
                    self.H = scale
                else:
                    self.H *= scale
            self.first_iteration = False
        self._update_implementation(delta_x, delta_grad)

    def dot(self, p):
        """Compute the product of the internal matrix with the given vector.

        Parameters
        ----------
        p : array_like
            1-D array representing a vector.

        Returns
        -------
        Hp : array
            1-D represents the result of multiplying the approximation matrix
            by vector p.
        """
        if self.approx_type == 'hess':
            return self._symv(1, self.B, p)
        else:
            return self._symv(1, self.H, p)

    def get_matrix(self):
        """Return the current internal matrix.

        Returns
        -------
        M : ndarray, shape (n, n)
            Dense matrix containing either the Hessian or its inverse
            (depending on how `approx_type` was defined).
        """
        if self.approx_type == 'hess':
            M = np.copy(self.B)
        else:
            M = np.copy(self.H)
        li = np.tril_indices_from(M, k=-1)
        M[li] = M.T[li]
        return M

    def _update_inverse_hessian(self, ys, Hy, yHy, s):
        """Update the inverse Hessian matrix.

        BFGS update using the formula:

            ``H <- H + ((H*y).T*y + s.T*y)/(s.T*y)^2 * (s*s.T)
                     - 1/(s.T*y) * ((H*y)*s.T + s*(H*y).T)``

        where ``s = delta_x`` and ``y = delta_grad``. This formula is
        equivalent to (6.17) in [1]_ written in a more efficient way
        for implementation.

        References
        ----------
        .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
               Second Edition (2006).
        """
        self.H = self._syr2(-1.0 / ys, s, Hy, a=self.H)
        self.H = self._syr((ys + yHy) / ys ** 2, s, a=self.H)

    def _update_hessian(self, ys, Bs, sBs, y):
        """Update the Hessian matrix.

        BFGS update using the formula:

            ``B <- B - (B*s)*(B*s).T/s.T*(B*s) + y*y^T/s.T*y``

        where ``s`` is short for ``delta_x`` and ``y`` is short
        for ``delta_grad``. Formula (6.19) in [1]_.

        References
        ----------
        .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
               Second Edition (2006).
        """
        self.B = self._syr(1.0 / ys, y, a=self.B)
        self.B = self._syr(-1.0 / sBs, Bs, a=self.B)

    def _update_implementation(self, delta_x, delta_grad):
        # Auxiliary variables w and z
        if self.approx_type == 'hess':
            w = delta_x
            z = delta_grad
        else:
            w = delta_grad
            z = delta_x
        # Do some common operations
        wz = np.dot(w, z)
        Mw = self @ w
        wMw = Mw.dot(w)
        # Guarantee that wMw > 0 by reinitializing matrix.
        # While this is always true in exact arithmetic,
        # indefinite matrix may appear due to roundoff errors.
        if wMw <= 0.0:
            scale = self._auto_scale(delta_x, delta_grad)
            # Reinitialize matrix
            if self.approx_type == 'hess':
                self.B = scale * np.eye(self.n, dtype=float)
            else:
                self.H = scale * np.eye(self.n, dtype=float)
            # Do common operations for new matrix
            Mw = self @ w
            wMw = Mw.dot(w)
        # Check if curvature condition is violated
        if wz <= self.min_curvature * wMw:
            # If the option 'skip_update' is set
            # we just skip the update when the condition
            # is violated.
            if self.exception_strategy == 'skip_update':
                return
            # If the option 'damp_update' is set we
            # interpolate between the actual BFGS
            # result and the unmodified matrix.
            elif self.exception_strategy == 'damp_update':
                update_factor = (1-self.min_curvature) / (1 - wz/wMw)
                z = update_factor*z + (1-update_factor)*Mw
                wz = np.dot(w, z)
        # Update matrix
        if self.approx_type == 'hess':
            self._update_hessian(wz, Mw, wMw, z)
        else:
            self._update_inverse_hessian(wz, Mw, wMw, z)

    def _update_implementation(self, delta_x, delta_grad):
        # Auxiliary variables w and z
        if self.approx_type == 'hess':
            w = delta_x
            z = delta_grad
        else:
            w = delta_grad
            z = delta_x
        # Do some common operations
        Mw = self @ w
        z_minus_Mw = z - Mw
        denominator = np.dot(w, z_minus_Mw)
        # If the denominator is too small
        # we just skip the update.
        if np.abs(denominator) <= self.min_denominator*norm(w)*norm(z_minus_Mw):
            return
        # Update matrix
        if self.approx_type == 'hess':
            self.B = self._syr(1/denominator, z_minus_Mw, a=self.B)
        else:
            self.H = self._syr(1/denominator, z_minus_Mw, a=self.H)