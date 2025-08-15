
#!/usr/bin/env python3
"""
1-Hour Confidence Validator for DAI → ARB Swap Decisions
Specialized system for validating price decline predictions within 1-hour windows
"""

import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class OneHourSignal:
    confidence_score: float
    btc_1h_decline: float
    arb_1h_momentum: float
    market_conditions: Dict
    execution_recommended: bool
    timestamp: float

class OneHourConfidenceValidator:
    def __init__(self, market_analyzer, market_strategy):
        self.market_analyzer = market_analyzer
        self.market_strategy = market_strategy
        
        # 1-hour specific thresholds
        self.min_confidence_1h = 0.92  # 92% confidence for 1-hour decisions
        self.btc_decline_threshold_1h = 0.003  # 0.3% decline
        self.arb_momentum_threshold_1h = 0.005  # 0.5% momentum
        
        # Track recent predictions for accuracy
        self.recent_predictions = []
        self.prediction_accuracy = 0.85  # Track actual accuracy
        
    def validate_1h_dai_to_arb_decision(self) -> Optional[OneHourSignal]:
        """Validate whether to execute DAI→ARB swap based on 1-hour prediction"""
        try:
            # Get current market signal
            enhanced_signal = self.market_analyzer.generate_enhanced_signal()
            if not enhanced_signal:
                return None
            
            # Get 1-hour BTC and ARB data
            btc_1h_data = self.market_analyzer.get_historical_price_data('BTC', 1)
            arb_1h_data = self.market_analyzer.get_historical_price_data('ARB', 1)
            
            if not btc_1h_data or not arb_1h_data:
                logging.warning("Insufficient 1-hour data for validation")
                return None
            
            # Calculate 1-hour trends
            btc_1h_trend = self._calculate_1h_trend(btc_1h_data)
            arb_1h_trend = self._calculate_1h_trend(arb_1h_data)
            
            # Validate market conditions for 1-hour prediction
            market_conditions = self._assess_1h_market_conditions(enhanced_signal)
            
            # Calculate confidence score for 1-hour decision
            confidence_score = self._calculate_1h_confidence(
                enhanced_signal, btc_1h_trend, arb_1h_trend, market_conditions
            )
            
            # Determine execution recommendation
            execution_recommended = (
                confidence_score >= self.min_confidence_1h and
                btc_1h_trend <= -self.btc_decline_threshold_1h and
                abs(arb_1h_trend) >= self.arb_momentum_threshold_1h * 0.5  # Reduced threshold for ARB
            )
            
            signal = OneHourSignal(
                confidence_score=confidence_score,
                btc_1h_decline=btc_1h_trend,
                arb_1h_momentum=arb_1h_trend,
                market_conditions=market_conditions,
                execution_recommended=execution_recommended,
                timestamp=time.time()
            )
            
            if execution_recommended:
                logging.info(f"🎯 1-HOUR EXECUTION SIGNAL: Confidence {confidence_score:.1%}")
                logging.info(f"   BTC 1h decline: {btc_1h_trend:.1%}, ARB momentum: {arb_1h_trend:.1%}")
            
            return signal
            
        except Exception as e:
            logging.error(f"1-hour validation failed: {e}")
            return None
    
    def _calculate_1h_trend(self, price_data) -> float:
        """Calculate 1-hour price trend"""
        if len(price_data) < 2:
            return 0.0
        
        try:
            latest = float(price_data[-1]['quote']['USD']['close'])
            previous = float(price_data[0]['quote']['USD']['close'])
            return (latest - previous) / previous
        except:
            return 0.0
    
    def _assess_1h_market_conditions(self, enhanced_signal) -> Dict:
        """Assess market conditions specifically for 1-hour predictions"""
        return {
            'volatility': enhanced_signal.btc_analysis.get('volatility', 0),
            'volume_strength': enhanced_signal.arb_analysis.get('volume_trend', {}).get('strength', 0),
            'gas_efficiency': enhanced_signal.gas_efficiency_score,
            'pattern_count': enhanced_signal.pattern_analysis.get('count', 0),
            'overall_confidence': enhanced_signal.confidence
        }
    
    def _calculate_1h_confidence(self, enhanced_signal, btc_trend, arb_trend, conditions) -> float:
        """Calculate specialized confidence score for 1-hour decisions"""
        try:
            # Base confidence from enhanced signal
            base_confidence = enhanced_signal.confidence
            
            # 1-hour trend bonuses/penalties
            btc_trend_bonus = min(0.10, abs(btc_trend) * 20) if btc_trend < 0 else -0.05
            arb_momentum_bonus = min(0.05, abs(arb_trend) * 10)
            
            # Market condition adjustments
            volatility_adjustment = conditions['volatility'] * 0.05
            volume_adjustment = conditions['volume_strength'] * 0.03
            gas_adjustment = conditions['gas_efficiency'] * 0.02
            pattern_adjustment = min(0.05, conditions['pattern_count'] * 0.02)
            
            # Calculate final confidence
            final_confidence = (
                base_confidence +
                btc_trend_bonus +
                arb_momentum_bonus +
                volatility_adjustment +
                volume_adjustment +
                gas_adjustment +
                pattern_adjustment
            )
            
            # Apply historical accuracy factor
            final_confidence *= self.prediction_accuracy
            
            return min(0.98, max(0.0, final_confidence))
            
        except Exception as e:
            logging.error(f"Confidence calculation failed: {e}")
            return 0.0
    
    def update_prediction_accuracy(self, prediction_success: bool):
        """Update prediction accuracy based on actual results"""
        # Simple exponential moving average
        learning_rate = 0.1
        if prediction_success:
            self.prediction_accuracy = self.prediction_accuracy + (learning_rate * (1.0 - self.prediction_accuracy))
        else:
            self.prediction_accuracy = self.prediction_accuracy - (learning_rate * self.prediction_accuracy)
        
        # Keep accuracy within reasonable bounds
        self.prediction_accuracy = max(0.3, min(0.95, self.prediction_accuracy))
        
        logging.info(f"Updated 1-hour prediction accuracy: {self.prediction_accuracy:.1%}")

