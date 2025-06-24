
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class StrategyBacktester:
    def __init__(self):
        self.historical_data = []
        self.simulation_results = []
        
    def load_historical_data(self, days=30):
        """Load historical price and health factor data"""
        # Simulate historical data for backtesting
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            end=datetime.now(),
            freq='H'
        )
        
        # Generate synthetic but realistic data
        eth_prices = 2000 + np.cumsum(np.random.randn(len(dates)) * 10)
        arb_prices = 0.5 + np.cumsum(np.random.randn(len(dates)) * 0.01)
        health_factors = 1.5 + np.random.randn(len(dates)) * 0.1
        
        self.historical_data = pd.DataFrame({
            'timestamp': dates,
            'eth_price': eth_prices,
            'arb_price': arb_prices,
            'health_factor': health_factors
        })
        
        return self.historical_data
    
    def simulate_strategy(self, strategy_params):
        """Simulate strategy performance on historical data"""
        if not len(self.historical_data):
            self.load_historical_data()
        
        portfolio_value = 1000  # Starting with $1000
        trades = []
        
        for i, row in self.historical_data.iterrows():
            # Simulate strategy logic
            if row['health_factor'] > strategy_params.get('borrow_threshold', 1.25):
                # Simulate borrowing action
                action = 'borrow'
                trade_value = portfolio_value * 0.1
            elif row['health_factor'] < strategy_params.get('safety_threshold', 1.1):
                # Simulate safety action
                action = 'repay'
                trade_value = portfolio_value * 0.05
            else:
                action = 'hold'
                trade_value = 0
            
            trades.append({
                'timestamp': row['timestamp'],
                'action': action,
                'value': trade_value,
                'health_factor': row['health_factor']
            })
        
        return pd.DataFrame(trades)
    
    def generate_report(self, simulation_results):
        """Generate comprehensive backtesting report"""
        total_trades = len(simulation_results[simulation_results['action'] != 'hold'])
        avg_health_factor = simulation_results['health_factor'].mean()
        min_health_factor = simulation_results['health_factor'].min()
        
        return {
            'total_trades': total_trades,
            'avg_health_factor': avg_health_factor,
            'min_health_factor': min_health_factor,
            'safety_violations': len(simulation_results[simulation_results['health_factor'] < 1.05]),
            'recommendation': 'Strategy appears safe' if min_health_factor > 1.05 else 'REVIEW REQUIRED'
        }
