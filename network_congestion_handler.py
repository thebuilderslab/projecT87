
#!/usr/bin/env python3
"""
Network Congestion Handler
Handles high network traffic and transaction rejection scenarios
"""

import time
from web3 import Web3

class NetworkCongestionHandler:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.congestion_threshold = 2.0  # 2x base fee = congested
        
    def assess_network_congestion(self):
        """Assess current network congestion level"""
        try:
            current_block = self.w3.eth.get_block('latest')
            current_gas_price = self.w3.eth.gas_price
            base_fee = current_block.get('baseFeePerGas', current_gas_price)
            
            congestion_ratio = current_gas_price / base_fee if base_fee > 0 else 1.0
            
            congestion_level = {
                'ratio': congestion_ratio,
                'current_gas_price': current_gas_price,
                'base_fee': base_fee,
                'status': self._get_congestion_status(congestion_ratio),
                'recommended_action': self._get_recommended_action(congestion_ratio)
            }
            
            print(f"🌐 Network Congestion Assessment:")
            print(f"   Congestion Ratio: {congestion_ratio:.2f}x")
            print(f"   Status: {congestion_level['status']}")
            print(f"   Recommendation: {congestion_level['recommended_action']}")
            
            return congestion_level
            
        except Exception as e:
            print(f"❌ Could not assess network congestion: {e}")
            return {
                'status': 'unknown',
                'recommended_action': 'proceed_with_caution',
                'ratio': 1.0
            }
    
    def _get_congestion_status(self, ratio):
        """Get human-readable congestion status"""
        if ratio >= 5.0:
            return "SEVERELY_CONGESTED"
        elif ratio >= 3.0:
            return "HIGHLY_CONGESTED"
        elif ratio >= 2.0:
            return "MODERATELY_CONGESTED"
        elif ratio >= 1.5:
            return "LIGHTLY_CONGESTED"
        else:
            return "NORMAL"
    
    def _get_recommended_action(self, ratio):
        """Get recommended action based on congestion"""
        if ratio >= 5.0:
            return "WAIT_FOR_LOWER_CONGESTION"
        elif ratio >= 3.0:
            return "USE_HIGHEST_GAS_PRIORITY"
        elif ratio >= 2.0:
            return "USE_HIGH_GAS_PRIORITY"
        else:
            return "PROCEED_NORMALLY"
    
    def get_congestion_adjusted_gas(self, base_gas_params, operation_priority="normal"):
        """Get gas parameters adjusted for current congestion"""
        congestion = self.assess_network_congestion()
        
        # Base multipliers for different congestion levels
        congestion_multipliers = {
            "NORMAL": 1.2,
            "LIGHTLY_CONGESTED": 1.5,
            "MODERATELY_CONGESTED": 2.0,
            "HIGHLY_CONGESTED": 3.0,
            "SEVERELY_CONGESTED": 4.0
        }
        
        # Priority multipliers
        priority_multipliers = {
            "low": 0.8,
            "normal": 1.0,
            "high": 1.3,
            "urgent": 1.6
        }
        
        congestion_multiplier = congestion_multipliers.get(congestion['status'], 1.2)
        priority_multiplier = priority_multipliers.get(operation_priority, 1.0)
        
        total_multiplier = congestion_multiplier * priority_multiplier
        
        adjusted_params = base_gas_params.copy()
        
        if 'gasPrice' in adjusted_params:
            adjusted_params['gasPrice'] = int(adjusted_params['gasPrice'] * total_multiplier)
        
        if 'maxFeePerGas' in adjusted_params:
            adjusted_params['maxFeePerGas'] = int(adjusted_params['maxFeePerGas'] * total_multiplier)
            
        # Increase gas limit during high congestion
        if congestion['status'] in ["HIGHLY_CONGESTED", "SEVERELY_CONGESTED"]:
            adjusted_params['gas'] = int(adjusted_params.get('gas', 300000) * 1.2)
        
        print(f"⛽ Congestion-Adjusted Gas:")
        print(f"   Multiplier: {total_multiplier:.2f}x")
        print(f"   Gas Limit: {adjusted_params.get('gas', 'N/A'):,}")
        if 'gasPrice' in adjusted_params:
            print(f"   Gas Price: {self.w3.from_wei(adjusted_params['gasPrice'], 'gwei'):.2f} gwei")
        
        return adjusted_params
    
    def should_delay_operation(self, congestion_threshold=3.0):
        """Determine if operation should be delayed due to congestion"""
        congestion = self.assess_network_congestion()
        
        should_delay = congestion['ratio'] >= congestion_threshold
        
        if should_delay:
            print(f"⏳ RECOMMENDING DELAY: Network congestion {congestion['ratio']:.2f}x >= {congestion_threshold}x threshold")
        
        return should_delay, congestion
