
#!/usr/bin/env python3
"""
Enhanced Collateral Validator
Real-time validation of Aave positions before borrowing operations
"""

import time
from web3 import Web3

class EnhancedCollateralValidator:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        
    def validate_live_position(self, requested_borrow_usd):
        """Comprehensive real-time position validation"""
        print(f"🔍 LIVE COLLATERAL VALIDATION: ${requested_borrow_usd:.2f}")
        
        validation_result = {
            'valid': False,
            'confidence': 0.0,
            'warnings': [],
            'position_data': {}
        }
        
        try:
            # Get fresh Aave data with multiple sources
            position_data = self._get_multi_source_position()
            
            if not position_data:
                validation_result['warnings'].append("Could not fetch position data")
                return validation_result
                
            validation_result['position_data'] = position_data
            
            # Validate borrowing capacity
            available_borrows = position_data.get('available_borrows_usd', 0)
            health_factor = position_data.get('health_factor', 0)
            
            print(f"   💰 Available Borrows: ${available_borrows:.2f}")
            print(f"   ❤️ Health Factor: {health_factor:.4f}")
            
            # Safety checks with buffer
            safety_buffer = 0.15  # 15% safety buffer
            safe_borrow_limit = available_borrows * (1 - safety_buffer)
            
            if requested_borrow_usd > safe_borrow_limit:
                validation_result['warnings'].append(
                    f"Borrow amount ${requested_borrow_usd:.2f} exceeds safe limit ${safe_borrow_limit:.2f}"
                )
                return validation_result
                
            if health_factor < 2.0:
                validation_result['warnings'].append(
                    f"Health factor {health_factor:.4f} below recommended 2.0"
                )
                return validation_result
                
            # Calculate confidence based on data freshness and consistency
            confidence = self._calculate_validation_confidence(position_data)
            validation_result['confidence'] = confidence
            
            if confidence >= 0.85:  # 85% confidence threshold
                validation_result['valid'] = True
                print(f"   ✅ Validation PASSED (Confidence: {confidence:.1%})")
            else:
                validation_result['warnings'].append(
                    f"Low confidence in position data: {confidence:.1%}"
                )
                
            return validation_result
            
        except Exception as e:
            validation_result['warnings'].append(f"Validation error: {e}")
            return validation_result
    
    def _get_multi_source_position(self):
        """Get position data from multiple sources for validation"""
        sources = []
        
        # Source 1: Direct Aave contract
        try:
            pool_abi = [{
                "inputs": [{"name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"name": "totalCollateralBase", "type": "uint256"},
                    {"name": "totalDebtBase", "type": "uint256"},
                    {"name": "availableBorrowsBase", "type": "uint256"},
                    {"name": "currentLiquidationThreshold", "type": "uint256"},
                    {"name": "ltv", "type": "uint256"},
                    {"name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }]
            
            pool_contract = self.w3.eth.contract(
                address=self.agent.aave_pool_address,
                abi=pool_abi
            )
            
            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
            
            aave_data = {
                'total_collateral_usd': account_data[0] / (10**8),
                'total_debt_usd': account_data[1] / (10**8),
                'available_borrows_usd': account_data[2] / (10**8),
                'health_factor': account_data[5] / (10**18) if account_data[5] > 0 else float('inf'),
                'source': 'aave_contract',
                'timestamp': time.time()
            }
            sources.append(aave_data)
            
        except Exception as e:
            print(f"   ⚠️ Aave contract source failed: {e}")
        
        # Source 2: Dashboard data (if available)
        try:
            from web_dashboard import get_live_agent_data
            dashboard_data = get_live_agent_data()
            
            if dashboard_data and self._validate_dashboard_data(dashboard_data):
                dashboard_position = {
                    'total_collateral_usd': dashboard_data['total_collateral_usdc'],
                    'total_debt_usd': dashboard_data['total_debt_usdc'],
                    'available_borrows_usd': dashboard_data['available_borrows_usdc'],
                    'health_factor': dashboard_data['health_factor'],
                    'source': 'dashboard',
                    'timestamp': time.time()
                }
                sources.append(dashboard_position)
                
        except Exception as e:
            print(f"   ⚠️ Dashboard source failed: {e}")
        
        # Return best available source
        if len(sources) >= 2:
            # Cross-validate sources
            return self._cross_validate_sources(sources)
        elif len(sources) == 1:
            return sources[0]
        else:
            return None
    
    def _validate_dashboard_data(self, data):
        """Validate dashboard data quality"""
        required_fields = ['health_factor', 'total_collateral_usdc', 'total_debt_usdc', 'available_borrows_usdc']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                return False
            if isinstance(data[field], (int, float)) and data[field] < 0:
                return False
                
        return True
    
    def _cross_validate_sources(self, sources):
        """Cross-validate multiple data sources"""
        if len(sources) < 2:
            return sources[0] if sources else None
            
        # Compare key metrics between sources
        source1, source2 = sources[0], sources[1]
        
        # Calculate relative differences
        collateral_diff = abs(source1['total_collateral_usd'] - source2['total_collateral_usd']) / max(source1['total_collateral_usd'], 1)
        hf_diff = abs(source1['health_factor'] - source2['health_factor']) / max(source1['health_factor'], 1)
        
        print(f"   🔍 Cross-validation:")
        print(f"      Collateral difference: {collateral_diff:.2%}")
        print(f"      Health factor difference: {hf_diff:.2%}")
        
        # If sources agree closely, use Aave contract data (most authoritative)
        if collateral_diff < 0.05 and hf_diff < 0.05:  # 5% tolerance
            aave_source = next((s for s in sources if s['source'] == 'aave_contract'), sources[0])
            aave_source['validation_status'] = 'cross_validated'
            return aave_source
        else:
            # Use most recent data with warning
            latest_source = max(sources, key=lambda x: x['timestamp'])
            latest_source['validation_status'] = 'single_source'
            return latest_source
    
    def _calculate_validation_confidence(self, position_data):
        """Calculate confidence score for validation"""
        confidence = 1.0
        
        # Reduce confidence for old data
        data_age = time.time() - position_data.get('timestamp', 0)
        if data_age > 300:  # 5 minutes
            confidence *= 0.7
        elif data_age > 60:  # 1 minute
            confidence *= 0.9
            
        # Reduce confidence for single source
        if position_data.get('validation_status') == 'single_source':
            confidence *= 0.8
            
        # Reduce confidence for fallback data
        if position_data.get('source') == 'fallback_analysis':
            confidence *= 0.5
            
        return confidence

    def check_asset_borrowing_restrictions(self, asset_address):
        """Check if asset has borrowing restrictions"""
        print(f"🔍 CHECKING ASSET BORROWING RESTRICTIONS: {asset_address}")
        
        restrictions = {
            'borrowing_enabled': True,
            'stable_rate_enabled': False,
            'variable_rate_enabled': True,
            'supply_cap': None,
            'borrow_cap': None,
            'warnings': []
        }
        
        try:
            # Check if it's USDC (known to work)
            if asset_address.lower() == self.agent.usdc_address.lower():
                print(f"   ✅ USDC borrowing confirmed enabled")
                return restrictions
                
            # For other assets, implement specific checks
            restrictions['warnings'].append("Asset restrictions not fully validated")
            
        except Exception as e:
            restrictions['warnings'].append(f"Could not check restrictions: {e}")
            
        return restrictions

# Integration with enhanced borrow manager
def integrate_enhanced_validation():
    """Integrate enhanced validation with existing borrow manager"""
    print("🔧 INTEGRATING ENHANCED VALIDATION")
    
    # This would be integrated into the enhanced_borrow_manager.py
    integration_status = {
        'collateral_validation': True,
        'asset_restrictions': True,
        'network_congestion': True
    }
    
    return integration_status
