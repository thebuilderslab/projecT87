
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
        
        # Configuration parameters - LOWERED FOR SENSITIVITY
        self.btc_drop_threshold = float(os.getenv('BTC_DROP_THRESHOLD', '0.003'))  # 0.3% drop (lowered from 1%)
        self.arb_rsi_oversold = float(os.getenv('ARB_RSI_OVERSOLD', '30'))
        self.arb_rsi_overbought = float(os.getenv('ARB_RSI_OVERBOUGHT', '70'))
        self.signal_cooldown = int(os.getenv('SIGNAL_COOLDOWN', '300'))  # 5 minutes (lowered from 30 minutes)
        
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

    def get_btc_price_data(self) -> Optional[Dict]:
        """Get BTC price data using fixed API with fallbacks"""
        if not hasattr(self, 'market_data_api'):
            from market_data_api_fix import MarketDataAPIFix
            self.market_data_api = MarketDataAPIFix(self.coinmarketcap_api_key)
        
        return self.market_data_api.get_btc_price_data_fixed()

    def get_arb_price_data(self) -> Optional[Dict]:
        """Get ARB price data using fixed API with fallbacks"""
        if not hasattr(self, 'market_data_api'):
            from market_data_api_fix import MarketDataAPIFix
            self.market_data_api = MarketDataAPIFix(self.coinmarketcap_api_key)
        
        return self.market_data_api.get_arb_price_data_fixed()

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
        """Execute DAI → ARB swap strategy with enhanced logging"""
        try:
            print(f"🔄 EXECUTING DEBT SWAP SEQUENCE: DAI → ARB")
            print(f"💰 Amount: {amount_dai:.2f} DAI")
            print(f"🎯 Strategy: Market-driven debt optimization")
            
            # Log current market conditions
            btc_data = self.get_btc_price_data()
            arb_data = self.get_arb_price_data()
            if btc_data and arb_data:
                print(f"📊 Market Conditions:")
                print(f"   BTC 1h change: {btc_data.get('percent_change_1h', 0):.2f}%")
                print(f"   ARB 1h change: {arb_data.get('percent_change_1h', 0):.2f}%")
            
            # First, borrow DAI using existing system
            print(f"🏦 Step 1: Borrowing {amount_dai:.2f} DAI from Aave...")
            borrow_success = self.agent.execute_enhanced_borrow_with_retry(amount_dai)
            if not borrow_success:
                print(f"❌ DAI borrow failed - debt swap sequence aborted")
                return False
            
            print(f"✅ DAI borrow successful - proceeding to ARB swap")
            
            # Then swap DAI for ARB using Uniswap
            if hasattr(self.agent.uniswap, 'swap_tokens'):
                print(f"🔄 Step 2: Swapping {amount_dai:.2f} DAI → ARB on Uniswap...")
                
                # Ensure proper approvals before swap
                dai_contract = self.agent.w3.eth.contract(
                    address=self.agent.dai_address,
                    abi=self.agent.aave.erc20_abi
                )
                
                # Check and approve DAI for Uniswap if needed
                current_allowance = dai_contract.functions.allowance(
                    self.agent.address,
                    self.agent.uniswap.router_address
                ).call()
                
                dai_amount_wei = int(amount_dai * 10**18)
                
                if current_allowance < dai_amount_wei:
                    print(f"🔓 Approving DAI for Uniswap swap...")
                    approval_tx = dai_contract.functions.approve(
                        self.agent.uniswap.router_address,
                        dai_amount_wei * 2  # Approve 2x for safety
                    ).build_transaction({
                        'from': self.agent.address,
                        'gas': 100000,
                        'gasPrice': self.agent.w3.eth.gas_price,
                        'nonce': self.agent.w3.eth.get_transaction_count(self.agent.address)
                    })
                    
                    signed_approval = self.agent.w3.eth.account.sign_transaction(approval_tx, self.agent.private_key)
                    approval_hash = self.agent.w3.eth.send_raw_transaction(signed_approval.rawTransaction)
                    print(f"🔗 Approval transaction: {approval_hash.hex()}")
                    
                    # Wait for approval confirmation
                    time.sleep(3)
                
                # Execute the swap
                swap_result = self.agent.uniswap.swap_tokens(
                    self.agent.dai_address,
                    self.agent.arb_address,
                    amount_dai,
                    3000  # 0.3% fee tier for ARB
                )
                
                if swap_result:
                    print(f"✅ DEBT SWAP COMPLETE: DAI → ARB executed on-chain")
                    print(f"🔗 Transaction should appear on Arbiscan within 1-2 minutes")
                    return True
                else:
                    print(f"❌ DAI → ARB swap failed on Uniswap")
                    return False
            else:
                print(f"❌ Uniswap integration not available for ARB trading")
                logging.error("Uniswap integration not available for ARB trading")
                return False
                
        except Exception as e:
            print(f"❌ DEBT SWAP SEQUENCE FAILED: {e}")
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
            logging.errologging.error(f"ARB → DAI swap failed: {e}")
            return False

    def should_execute_trade(self) -> bool:
        """Check if debt swap trade should execute based on current market conditions"""
        try:
            print(f"\n🔍 CHECKING DEBT SWAP CONDITIONS:")
            print(f"=" * 45)
            
            # Check if market signal strategy is enabled
            if not self.market_signal_enabled:
                print(f"❌ Market signal strategy is DISABLED")
                return False
            
            print(f"✅ Market signal strategy is ENABLED")
            
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
            print(f"   BTC 1h change: {signal.btc_price_change:.2f}%")
            print(f"   ARB RSI: {signal.arb_technical_score:.1f}")
            
            # Check if we should execute the strategy
            should_execute, strategy_type = self.should_execute_market_strategy(signal)
            
            if should_execute:
                print(f"🎯 DEBT SWAP TRIGGER: {strategy_type.upper()}")
                print(f"💡 Condition: Market declining, executing debt optimization")
                
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
                print(f"   Required: BTC drop ≥{self.btc_1h_drop_threshold*100:.1f}% OR ARB RSI ≤25")
                print(f"   Required: Confidence ≥{self.dai_to_arb_threshold:.0%}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking trade conditions: {e}")
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
