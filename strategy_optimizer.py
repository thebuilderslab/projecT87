
"""
Strategy Optimizer - Compares different market analysis approaches
Determines the most effective strategy based on success rates, gas costs, and accuracy
"""

import json
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
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
            btc_data = self.agent.market_signal_strategy.get_btc_price_data()
            arb_data = self.agent.market_signal_strategy.get_arb_price_data()
            
            if not btc_data or not arb_data:
                return {'volatility': 0.5, 'gas_cost': 0.5, 'market_trend': 0.5}
            
            # Calculate volatility
            btc_volatility = abs(btc_data.get('percent_change_1h', 0))
            arb_volatility = abs(arb_data.get('percent_change_1h', 0))
            avg_volatility = (btc_volatility + arb_volatility) / 2
            
            # Normalize volatility (higher volatility = better for pattern recognition)
            volatility_score = min(1.0, avg_volatility / 5.0)  # Cap at 5% volatility
            
            # Get gas conditions
            gas_score = self.agent.market_signal_strategy.enhanced_analyzer.calculate_gas_efficiency_score()
            
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
