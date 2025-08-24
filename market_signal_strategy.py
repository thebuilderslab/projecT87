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
from typing import Dict, Optional, Tuple, List, Any
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
    should_execute: bool = False
    timestamp: float = 0 # Initialize with a default value


class MarketSignalStrategy:
    def __init__(self, agent):
        self.agent = agent
        self.coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.signal_history = []
        self.last_signal_time = 0

        # Initialize enhanced market analyzer with comprehensive technical analysis
        try:
            from enhanced_market_analyzer import EnhancedMarketAnalyzer, EnhancedMarketSignalStrategy
            self.enhanced_analyzer = EnhancedMarketAnalyzer(agent)
            self.enhanced_strategy = EnhancedMarketSignalStrategy(agent)
            logging.info("✅ Enhanced Market Analyzer with CoinMarketCap integration initialized")
        except ImportError as e:
            logging.warning(f"Enhanced market analyzer not available: {e}")
            self.enhanced_analyzer = None
            self.enhanced_strategy = None
        except Exception as e:
            logging.error(f"Failed to initialize enhanced market analyzer: {e}")
            self.enhanced_analyzer = None
            self.enhanced_strategy = None


        # Initialize advanced trend analyzer for minute-by-minute analysis
        try:
            from advanced_trend_analyzer import AdvancedTrendAnalyzer
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
        self.dai_to_arb_threshold = float(os.getenv('DAI_TO_ARB_THRESHOLD', '0.9'))  # 90% confidence for DAI→ARB (1hr window)
        self.arb_to_dai_threshold = float(os.getenv('ARB_TO_DAI_THRESHOLD', '0.6'))  # 60% confidence for ARB→DAI
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
            print("   • Confidence threshold: 90% for DAI->ARB, 60% for ARB->DAI")
            print("   • BTC drop sensitivity: 0.2% (1h)")
            print("   • Integration: Hybrid system compatible")

    def get_btc_price_data(self) -> Optional[Dict]:
        """Get BTC price data using fixed API with fallbacks"""
        try:
            if not hasattr(self, 'market_data_api') or self.market_data_api is None:
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
            if not hasattr(self, 'market_data_api') or self.market_data_api is None:
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
            if self.enhanced_analyzer:
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
                            should_execute=True
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
            should_execute = False

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

            # Final check for execution based on thresholds
            if signal_type == 'bearish' and confidence >= self.dai_to_arb_threshold:
                should_execute = True
            elif signal_type == 'bullish' and confidence >= self.arb_to_dai_threshold:
                should_execute = True

            signal = MarketSignal(
                signal_type=signal_type,
                confidence=confidence,
                btc_price_change=btc_data['percent_change_1h'],
                arb_technical_score=arb_indicators['rsi'],
                should_execute=should_execute,
                timestamp=current_time
            )

            if signal.confidence > 0.3:  # Only log significant signals
                logging.info(f"Market signal generated: {signal.signal_type} (confidence: {signal.confidence:.2f}, execute: {signal.should_execute})")
                logging.info(f"BTC 1h change: {signal.btc_price_change:.2f}%, ARB RSI: {signal.arb_technical_score:.1f}")

            return signal

        except Exception as e:
            logging.error(f"Market signal analysis failed: {e}")
            return None

    def should_execute_market_strategy(self, signal: MarketSignal) -> Tuple[bool, str]:
        """Determine if market strategy should be executed based on 1-hour confidence signal"""
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
        """Check if debt swap trade should execute based on comprehensive market analysis"""
        try:
            print(f"\n🔍 COMPREHENSIVE DEBT SWAP ANALYSIS (ENHANCED WITH COINMARKETCAP):")
            print(f"=" * 70)

            # Check if market signal strategy is enabled
            if not self.market_signal_enabled:
                print(f"❌ Market signal strategy is DISABLED")
                return False

            print(f"✅ Market signal strategy is ENABLED")
            
            # Priority 1: Enhanced technical analysis with CoinMarketCap data
            if self.enhanced_strategy:
                print(f"🚀 Running enhanced CoinMarketCap technical analysis...")
                try:
                    enhanced_decision = self.enhanced_strategy.should_execute_trade()
                    if enhanced_decision:
                        print(f"✅ ENHANCED ANALYSIS RECOMMENDS TRADE EXECUTION")
                        print(f"📊 Based on comprehensive technical indicators from CoinMarketCap API")
                        return True
                    else:
                        print(f"📊 Enhanced analysis suggests holding current position")
                        # Continue with fallback analysis
                except Exception as e:
                    print(f"⚠️ Enhanced analysis failed: {e}")
                    print(f"🔄 Falling back to standard analysis...")
            
            print(f"🔄 Running standard market signal analysis...")

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
        """Get current market strategy status including enhanced technical analysis"""
        status = {
            'enabled': self.market_signal_enabled,
            'last_signal_time': self.last_signal_time,
            'cooldown_remaining': max(0, self.signal_cooldown - (time.time() - self.last_signal_time)),
            'btc_threshold': self.btc_drop_threshold,
            'signal_history_count': len(self.signal_history),
            'minute_analysis_enabled': self.minute_analysis_enabled,
            'enhanced_analysis_enabled': self.enhanced_analyzer is not None
        }

        # Add enhanced market analysis status
        if self.enhanced_strategy:
            try:
                enhanced_status = self.enhanced_strategy.get_market_status()
                status['enhanced_market_analysis'] = enhanced_status
            except Exception as e:
                status['enhanced_market_analysis'] = {'error': str(e)}

        # Add trend analyzer status if available
        if self.trend_analyzer:
            trend_summary = self.trend_analyzer.get_current_trend_summary()
            status['trend_analysis'] = trend_summary

        return status

    def _check_btc_signal(self):
        """Check BTC price movement for bearish/bullish signals"""
        try:
            btc_data = self.get_btc_price_data()
            if not btc_data:
                return "neutral"

            btc_change_1h = btc_data.get('percent_change_1h', 0)

            if btc_change_1h <= -self.btc_drop_threshold:
                return "bearish"
            elif btc_change_1h >= self.btc_drop_threshold:
                return "bullish"
            else:
                return "neutral"
        except Exception as e:
            logging.error(f"BTC signal check failed: {e}")
            return "neutral"

    def _check_arb_signal(self):
        """Check ARB RSI for oversold/overbought conditions"""
        try:
            arb_data = self.get_arb_price_data()
            if not arb_data:
                return "neutral"

            arb_rsi = self._calculate_simple_rsi(arb_data.get('percent_change_1h', 0))

            if arb_rsi <= self.arb_rsi_oversold:
                return "oversold"
            elif arb_rsi >= self.arb_rsi_overbought:
                return "overbought"
            else:
                return "neutral"
        except Exception as e:
            logging.error(f"ARB signal check failed: {e}")
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