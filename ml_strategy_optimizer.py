
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

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
