#!/usr/bin/env python3
"""
Test the corrected debt detection to verify DAI debt is found
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_debt_position_detector import EnhancedDebtPositionDetector

def quick_test():
    """Quick test of corrected debt detection"""
    
    print("🧪 TESTING CORRECTED DEBT DETECTION")
    print("=" * 50)
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        os.environ['NETWORK_MODE'] = 'mainnet'
        
        print("⏳ Initializing agent (simplified)...")
        agent = ArbitrumTestnetAgent()
        
        print("🔍 Creating enhanced debt detector...")
        detector = EnhancedDebtPositionDetector(agent)
        
        print("📊 Getting detailed debt position...")
        position_data = detector.get_detailed_debt_position()
        
        print(f"\n✅ CORRECTED DEBT DETECTION RESULTS:")
        print(f"   Assets with debt: {position_data['assets_with_debt']}")
        print(f"   Debt swap ready: {position_data['debt_swap_ready']}")
        
        # Test specific DAI debt validation
        if 'DAI' in position_data['debt_breakdown']:
            dai_debt = position_data['debt_breakdown']['DAI']
            print(f"\n🎯 DAI DEBT FOUND:")
            print(f"   Variable Debt: {dai_debt['variable_debt']:.6f} DAI")
            print(f"   USD Value: ~${dai_debt['variable_debt']:.2f}")
            
            # Test debt swap validation for 5 DAI
            print(f"\n🔧 Testing 5 DAI → ARB debt swap validation...")
            validation = detector.validate_debt_swap_readiness('DAI', 'ARB', 5.0)
            print(f"   Can swap: {validation['can_swap']}")
            if not validation['can_swap']:
                print(f"   Reasons: {validation['reasons']}")
        
        return position_data
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = quick_test()
    if result and result.get('debt_swap_ready'):
        print(f"\n🎉 SUCCESS: Debt detection working! System can now identify debt positions.")
    else:
        print(f"\n❌ FAILED: Debt detection still not working properly.")