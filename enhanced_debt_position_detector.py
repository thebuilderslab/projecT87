#!/usr/bin/env python3
"""
Enhanced Debt Position Detector
Fixes the debt detection to properly identify individual asset debt positions
Ensures consistent Aave protocol monitoring throughout the system
"""

import time
from typing import Dict, List, Optional
from web3 import Web3


class EnhancedDebtPositionDetector:
    """Accurately detects individual debt positions from Aave protocol"""
    
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.user_address = agent.address
        
        # Correct Aave contracts
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Correct mainnet token addresses
        self.tokens = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548",
            'USDC': "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
            'USDT': "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            'WETH': "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            'WBTC': "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
        }
        
        # Correct debt token addresses (vToken addresses)
        self.debt_tokens = {
            'DAI': "0x8619d80FB0141ba7F184CbF22fd724116D9f7ffC",   # variableDebtDAI
            'ARB': "0x44705f578135cC5d703b4c9c122528C73Eb87145",   # variableDebtARB
            'USDC': "0xF15F26710c827DDe8ACBA678682F3Ce24f2Fb56E",  # variableDebtUSDC
            'USDT': "0xfb00AC187a8Eb5AFAE4eACE434F493Eb62672df7",  # variableDebtUSDT
            'WETH': "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351",  # variableDebtWETH
            'WBTC': "0x92b42c66840C7AD907b4BF74879FF3eF7c529473"   # variableDebtWBTC
        }
        
        print(f"🔍 Enhanced Debt Position Detector initialized")
        print(f"   Pool: {self.aave_pool}")
        print(f"   Data Provider: {self.aave_data_provider}")
        print(f"   User: {self.user_address}")
        
    def get_detailed_debt_position(self) -> Dict:
        """Get comprehensive debt position breakdown by asset"""
        
        print(f"\n🔍 ANALYZING DETAILED DEBT POSITION")
        print("=" * 50)
        
        # Get overall position first
        overall_position = self.agent.aave.get_user_account_data()
        print(f"📊 OVERALL POSITION:")
        print(f"   Total Debt USD: ${overall_position.get('totalDebtUSD', 0):.2f}")
        print(f"   Health Factor: {overall_position.get('healthFactor', 0):.4f}")
        
        # Now check individual assets using correct approach
        debt_breakdown = {}
        total_found_debt = 0
        
        # Use Data Provider ABI for getUserReserveData
        data_provider_abi = [{
            'inputs': [
                {'name': 'user', 'type': 'address'}, 
                {'name': 'asset', 'type': 'address'}
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
        
        data_provider_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.aave_data_provider),
            abi=data_provider_abi
        )
        
        print(f"\n🔍 CHECKING INDIVIDUAL ASSET DEBT POSITIONS:")
        
        for asset_name, asset_address in self.tokens.items():
            try:
                # Get reserve data for this asset (CORRECT parameter order: asset, user)
                reserve_data = data_provider_contract.functions.getUserReserveData(
                    Web3.to_checksum_address(asset_address),
                    Web3.to_checksum_address(self.user_address)
                ).call()
                
                # Extract debt amounts
                stable_debt = reserve_data[1]  # currentStableDebt
                variable_debt = reserve_data[2]  # currentVariableDebt
                atoken_balance = reserve_data[0]  # currentATokenBalance (collateral)
                
                # Convert to human readable (considering decimals)
                decimals = 18 if asset_name in ['DAI', 'WETH', 'WBTC', 'ARB'] else 6
                
                stable_debt_human = stable_debt / (10 ** decimals)
                variable_debt_human = variable_debt / (10 ** decimals)
                atoken_balance_human = atoken_balance / (10 ** decimals)
                total_debt_human = stable_debt_human + variable_debt_human
                
                if total_debt_human > 0 or atoken_balance_human > 0:
                    print(f"   📊 {asset_name} POSITION:")
                    if atoken_balance_human > 0:
                        print(f"      ✅ Collateral (aToken): {atoken_balance_human:.6f} {asset_name}")
                    if variable_debt_human > 0:
                        print(f"      ❌ Variable Debt: {variable_debt_human:.6f} {asset_name}")
                    if stable_debt_human > 0:
                        print(f"      ❌ Stable Debt: {stable_debt_human:.6f} {asset_name}")
                    
                    debt_breakdown[asset_name] = {
                        'variable_debt': variable_debt_human,
                        'stable_debt': stable_debt_human,
                        'total_debt': total_debt_human,
                        'collateral': atoken_balance_human,
                        'debt_token_address': self.debt_tokens.get(asset_name, ''),
                        'asset_address': asset_address,
                        'decimals': decimals,
                        'raw_variable_debt': variable_debt,
                        'raw_stable_debt': stable_debt
                    }
                    
                    total_found_debt += total_debt_human
                    
            except Exception as e:
                print(f"   ⚠️ {asset_name} check failed: {e}")
                continue
        
        print(f"\n📋 DEBT POSITION SUMMARY:")
        print(f"   Assets with debt: {len([k for k, v in debt_breakdown.items() if v['total_debt'] > 0])}")
        print(f"   Total debt found: {total_found_debt:.6f} tokens")
        print(f"   Reported total debt: ${overall_position.get('totalDebtUSD', 0):.2f}")
        
        return {
            'overall_position': overall_position,
            'debt_breakdown': debt_breakdown,
            'total_found_debt': total_found_debt,
            'assets_with_debt': [k for k, v in debt_breakdown.items() if v['total_debt'] > 0],
            'debt_swap_ready': len([k for k, v in debt_breakdown.items() if v['variable_debt'] > 0]) > 0
        }
    
    def validate_debt_swap_readiness(self, from_asset: str, to_asset: str, swap_amount_usd: float) -> Dict:
        """Validate if a debt swap is possible with current positions"""
        
        position_data = self.get_detailed_debt_position()
        
        print(f"\n🔧 DEBT SWAP VALIDATION:")
        print(f"   Requested: {swap_amount_usd:.2f} USD {from_asset} debt → {to_asset} debt")
        
        validation_result = {
            'can_swap': False,
            'reasons': [],
            'from_asset_debt': 0,
            'to_asset_debt': 0,
            'position_data': position_data
        }
        
        # Check if from_asset has sufficient debt
        if from_asset in position_data['debt_breakdown']:
            from_debt = position_data['debt_breakdown'][from_asset]['variable_debt']
            validation_result['from_asset_debt'] = from_debt
            
            if from_debt > 0:
                # Rough USD estimate (need proper price conversion)
                estimated_debt_usd = from_debt  # Simplified - assume 1:1 for validation
                
                if estimated_debt_usd >= swap_amount_usd:
                    validation_result['can_swap'] = True
                    print(f"   ✅ {from_asset} has {from_debt:.6f} variable debt (sufficient)")
                else:
                    validation_result['reasons'].append(f"Insufficient {from_asset} debt: {from_debt:.6f} < ${swap_amount_usd}")
                    print(f"   ❌ {from_asset} has {from_debt:.6f} variable debt (insufficient)")
            else:
                validation_result['reasons'].append(f"No variable {from_asset} debt found")
                print(f"   ❌ No variable {from_asset} debt found")
        else:
            validation_result['reasons'].append(f"No {from_asset} position found")
            print(f"   ❌ No {from_asset} position found")
        
        # Check to_asset validity
        if to_asset in self.tokens:
            print(f"   ✅ {to_asset} is supported for debt swapping")
        else:
            validation_result['reasons'].append(f"{to_asset} not supported")
            validation_result['can_swap'] = False
            print(f"   ❌ {to_asset} not supported")
        
        return validation_result


def test_enhanced_debt_detection():
    """Test the enhanced debt detection system"""
    
    print("🧪 TESTING ENHANCED DEBT DETECTION")
    print("=" * 60)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        import os
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        agent = ArbitrumTestnetAgent()
        detector = EnhancedDebtPositionDetector(agent)
        
        # Get detailed position
        position_data = detector.get_detailed_debt_position()
        
        # Test DAI debt swap validation
        dai_validation = detector.validate_debt_swap_readiness('DAI', 'ARB', 5.0)
        
        print(f"\n✅ ENHANCED DEBT DETECTION TEST COMPLETED")
        print(f"   Assets with debt: {position_data['assets_with_debt']}")
        print(f"   DAI debt swap ready: {dai_validation['can_swap']}")
        
        return {
            'success': True,
            'position_data': position_data,
            'dai_validation': dai_validation
        }
        
    except Exception as e:
        print(f"❌ Enhanced debt detection test failed: {e}")
        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    test_enhanced_debt_detection()