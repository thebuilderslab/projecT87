
#!/usr/bin/env python3
"""
FUNDING BYPASS HANDLER
Handles test mode and funding requirement bypasses safely
"""

import os
import json
from typing import Dict, Any, Optional

class FundingBypassHandler:
    def __init__(self):
        self.test_config_file = 'test_funding_config.json'
        self.bypass_active = False
        self.test_config = {}
        self.load_bypass_config()
    
    def load_bypass_config(self):
        """Load test configuration if it exists"""
        try:
            if os.path.exists(self.test_config_file):
                with open(self.test_config_file, 'r') as f:
                    self.test_config = json.load(f)
                    self.bypass_active = self.test_config.get('bypass_funding_checks', False)
                    
                if self.bypass_active:
                    print("🧪 TEST MODE DETECTED")
                    print("⚠️ Funding checks will be bypassed")
                    print(f"💡 Config: {self.test_config.get('warning', 'Test mode active')}")
                    
        except Exception as e:
            print(f"⚠️ Could not load bypass config: {e}")
            self.bypass_active = False
    
    def should_bypass_funding_checks(self) -> bool:
        """Check if funding checks should be bypassed"""
        return self.bypass_active
    
    def get_minimum_requirements(self) -> Dict[str, float]:
        """Get minimum requirements (real or test values)"""
        if self.bypass_active:
            return {
                'min_eth': self.test_config.get('min_eth_override', 0.001),
                'min_usdc': self.test_config.get('min_usdc_override', 0.1)
            }
        else:
            return {
                'min_eth': 0.005,
                'min_usdc': 1.0
            }
    
    def validate_with_bypass(self, eth_balance: float, usdc_balance: float) -> Dict[str, Any]:
        """Validate balances with potential bypass"""
        requirements = self.get_minimum_requirements()
        
        result = {
            'eth_sufficient': eth_balance >= requirements['min_eth'],
            'usdc_sufficient': usdc_balance >= requirements['min_usdc'],
            'bypass_active': self.bypass_active,
            'requirements_used': requirements,
            'balances': {
                'eth': eth_balance,
                'usdc': usdc_balance
            }
        }
        
        result['ready_for_operations'] = result['eth_sufficient'] and result['usdc_sufficient']
        
        if self.bypass_active:
            print(f"🧪 TEST MODE VALIDATION:")
            print(f"   ETH: {eth_balance:.6f} >= {requirements['min_eth']} = {result['eth_sufficient']}")
            print(f"   USDC: {usdc_balance:.6f} >= {requirements['min_usdc']} = {result['usdc_sufficient']}")
        
        return result
    
    def create_test_mode(self, min_eth: float = 0.001, min_usdc: float = 0.1):
        """Create test mode configuration"""
        config = {
            'test_mode': True,
            'bypass_funding_checks': True,
            'min_eth_override': min_eth,
            'min_usdc_override': min_usdc,
            'warning': 'TEST MODE ACTIVE - REDUCED FUNDING REQUIREMENTS',
            'created_at': json.dumps(time.time())
        }
        
        with open(self.test_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.load_bypass_config()
        print(f"✅ Test mode created with ETH: {min_eth}, USDC: {min_usdc}")
    
    def disable_test_mode(self):
        """Disable test mode"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
            self.bypass_active = False
            self.test_config = {}
            print("✅ Test mode disabled")
        else:
            print("💡 Test mode was not active")

def quick_test_mode_setup():
    """Quick setup for test mode"""
    handler = FundingBypassHandler()
    
    if handler.should_bypass_funding_checks():
        print("🧪 Test mode already active")
        print(f"Requirements: ETH {handler.get_minimum_requirements()['min_eth']}, USDC {handler.get_minimum_requirements()['min_usdc']}")
        
        disable = input("Disable test mode? (y/N): ").strip().lower()
        if disable == 'y':
            handler.disable_test_mode()
    else:
        print("🧪 Setting up test mode...")
        handler.create_test_mode()

if __name__ == "__main__":
    import time
    quick_test_mode_setup()
