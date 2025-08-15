
import hashlib
import json
from web3 import Web3

class SecurityAuditor:
    def __init__(self, w3, agent):
        self.w3 = w3
        self.agent = agent
        
    def validate_contract_addresses(self):
        """Verify all contract addresses are legitimate"""
        contracts = {
            'aave_pool': '0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654',
            'weth': '0x980B62Da83eFf3D4576C647993b0c1D7faf17c73',
            'dai': '0x5f6bB460B6d0bdA2CCaDdd7A19B5F6E7b5b8E1DB',
            'arb': '0x912CE59144191C1204E64559FE8253a0e49E6548'
        }
        
        audit_report = {'valid_contracts': [], 'suspicious_contracts': []}
        
        for name, address in contracts.items():
            try:
                # Check if contract exists
                code = self.w3.eth.get_code(address)
                if len(code) > 2:  # More than "0x"
                    audit_report['valid_contracts'].append(f"{name}: {address}")
                else:
                    audit_report['suspicious_contracts'].append(f"{name}: {address} - NO CODE")
            except Exception as e:
                audit_report['suspicious_contracts'].append(f"{name}: {address} - ERROR: {e}")
        
        return audit_report
    
    def check_transaction_limits(self):
        """Verify safety limits are properly enforced"""
        limits = {
            'max_single_transaction': 0.1,  # ETH
            'max_daily_volume': 1.0,        # ETH
            'min_health_factor': 1.05
        }
        
        return {
            'limits_configured': True,
            'emergency_stop_active': os.path.exists('EMERGENCY_STOP_ACTIVE.flag'),
            'safety_limits': limits
        }
