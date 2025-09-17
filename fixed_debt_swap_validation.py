#!/usr/bin/env python3
"""
Fixed Debt Swap Validation System
Uses corrected Aave protocol monitoring with proper parameter order
"""

from web3 import Web3
from typing import Dict, Optional

class FixedDebtSwapValidator:
    """Validates debt swap readiness using corrected Aave monitoring"""
    
    def __init__(self, w3, user_address):
        self.w3 = w3
        self.user_address = user_address
        
        # Aave contracts
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548",
        }
        
    def get_asset_debt(self, asset_name: str) -> Dict:
        """Get debt position for specific asset using corrected method"""
        
        if asset_name not in self.tokens:
            return {'error': f'Unsupported asset: {asset_name}'}
        
        asset_address = self.tokens[asset_name]
        
        # Data Provider ABI (correct parameter order)
        abi = [{
            'inputs': [
                {'name': 'asset', 'type': 'address'}, 
                {'name': 'user', 'type': 'address'}
            ],
            'name': 'getUserReserveData',
            'outputs': [
                {'name': 'currentATokenBalance', 'type': 'uint256'},
                {'name': 'currentStableDebt', 'type': 'uint256'},
                {'name': 'currentVariableDebt', 'type': 'uint256'},
                {'name': 'principalStableDebt', 'type': 'uint256'},
                {'name': 'scaledVariableDebt', 'type': 'uint256'},
                {'name': 'stableBorrowRate', 'type': 'uint256'},
                {'name': 'liquidityRate', 'type': 'uint256'},
                {'name': 'stableRateLastUpdated', 'type': 'uint40'},
                {'name': 'usageAsCollateralEnabled', 'type': 'bool'}
            ],
            'stateMutability': 'view',
            'type': 'function'
        }]
        
        try:
            data_provider = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.aave_data_provider),
                abi=abi
            )
            
            # CORRECTED: Call with (asset, user) parameter order
            reserve_data = data_provider.functions.getUserReserveData(
                Web3.to_checksum_address(asset_address),
                Web3.to_checksum_address(self.user_address)
            ).call()
            
            # Extract data
            atoken_balance = reserve_data[0]  # currentATokenBalance
            stable_debt = reserve_data[1]      # currentStableDebt
            variable_debt = reserve_data[2]    # currentVariableDebt
            
            # Convert to human readable
            decimals = 18  # DAI, ARB both use 18 decimals
            
            return {
                'success': True,
                'asset': asset_name,
                'variable_debt': variable_debt / (10 ** decimals),
                'stable_debt': stable_debt / (10 ** decimals),
                'total_debt': (variable_debt + stable_debt) / (10 ** decimals),
                'collateral': atoken_balance / (10 ** decimals),
                'raw_variable_debt': variable_debt,
                'raw_stable_debt': stable_debt,
                'decimals': decimals
            }
            
        except Exception as e:
            return {'error': f'Failed to get {asset_name} debt: {e}'}
    
    def validate_debt_swap(self, from_asset: str, to_asset: str, swap_amount_usd: float) -> Dict:
        """Validate if debt swap is possible with current positions"""
        
        print(f"\n🔧 VALIDATING DEBT SWAP:")
        print(f"   Request: {swap_amount_usd:.2f} USD {from_asset} debt → {to_asset} debt")
        
        validation_result = {
            'can_swap': False,
            'reasons': [],
            'from_asset_debt': 0,
            'to_asset_supported': False
        }
        
        # Check from_asset debt
        from_debt_data = self.get_asset_debt(from_asset)
        
        if 'error' in from_debt_data:
            validation_result['reasons'].append(from_debt_data['error'])
            print(f"   ❌ {from_debt_data['error']}")
            return validation_result
        
        from_variable_debt = from_debt_data['variable_debt']
        validation_result['from_asset_debt'] = from_variable_debt
        
        print(f"   📊 {from_asset} Variable Debt: {from_variable_debt:.6f}")
        
        if from_variable_debt > 0:
            # Rough validation (assume 1:1 USD for simplicity)
            if from_variable_debt >= swap_amount_usd:
                validation_result['can_swap'] = True
                print(f"   ✅ Sufficient {from_asset} debt for ${swap_amount_usd} swap")
            else:
                validation_result['reasons'].append(
                    f"Insufficient {from_asset} debt: {from_variable_debt:.6f} < ${swap_amount_usd}"
                )
                print(f"   ❌ Insufficient {from_asset} debt: {from_variable_debt:.6f} < ${swap_amount_usd}")
        else:
            validation_result['reasons'].append(f"No variable {from_asset} debt found")
            print(f"   ❌ No variable {from_asset} debt found")
        
        # Check to_asset support
        if to_asset in self.tokens:
            validation_result['to_asset_supported'] = True
            print(f"   ✅ {to_asset} is supported for debt swapping")
        else:
            validation_result['reasons'].append(f"{to_asset} not supported")
            validation_result['can_swap'] = False
            print(f"   ❌ {to_asset} not supported")
        
        return validation_result


def test_fixed_validation():
    """Test the fixed debt swap validation"""
    
    print("🧪 TESTING FIXED DEBT SWAP VALIDATION")
    print("=" * 50)
    
    # Direct connection
    rpc = 'https://arbitrum-one.public.blastapi.io'
    w3 = Web3(Web3.HTTPProvider(rpc))
    user_address = '0x5B823270e3719CDe8669e5e5326B455EaA8a350b'
    
    if not w3.is_connected():
        print('❌ Failed to connect to RPC')
        return False
    
    print('✅ Connected to Arbitrum Mainnet')
    
    # Create validator
    validator = FixedDebtSwapValidator(w3, user_address)
    
    # Test DAI debt detection
    print("\n🔍 Testing DAI debt detection...")
    dai_debt = validator.get_asset_debt('DAI')
    
    if 'error' in dai_debt:
        print(f"❌ DAI debt detection failed: {dai_debt['error']}")
        return False
    
    print(f"✅ DAI debt detected: {dai_debt['variable_debt']:.6f} DAI")
    
    # Test debt swap validation
    print(f"\n🔧 Testing debt swap validation...")
    validation = validator.validate_debt_swap('DAI', 'ARB', 5.0)
    
    if validation['can_swap']:
        print(f"🎉 SUCCESS: 5 DAI → ARB debt swap is READY!")
        return True
    else:
        print(f"❌ Debt swap validation failed: {validation['reasons']}")
        return False


if __name__ == "__main__":
    success = test_fixed_validation()
    if success:
        print(f"\n✅ FIXED DEBT SWAP VALIDATION: READY FOR PRODUCTION")
    else:
        print(f"\n❌ DEBT SWAP VALIDATION: STILL NEEDS FIXES")