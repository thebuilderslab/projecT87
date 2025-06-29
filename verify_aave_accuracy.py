
#!/usr/bin/env python3
"""
Verify Aave Data Accuracy
Compare dashboard data with external sources to ensure accuracy
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

def verify_aave_data_accuracy():
    """Verify that our Aave data matches reality"""
    load_dotenv()
    
    print("🔍 AAVE DATA ACCURACY VERIFICATION")
    print("=" * 50)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        print(f"📊 Wallet: {agent.address}")
        print(f"🌐 Network: Arbitrum Mainnet (Chain ID: {agent.w3.eth.chain_id})")
        
        # Test enhanced Aave data function
        from web_dashboard import get_enhanced_aave_data
        aave_data = get_enhanced_aave_data(agent)
        
        if aave_data:
            print(f"\n📈 DASHBOARD AAVE DATA:")
            print(f"   Health Factor: {aave_data['health_factor']:.4f}")
            print(f"   Total Collateral: ${aave_data['total_collateral_usdc']:.2f}")
            print(f"   Total Debt: ${aave_data['total_debt_usdc']:.2f}")
            print(f"   Available Borrows: ${aave_data['available_borrows_usdc']:.2f}")
            print(f"   Data Source: {aave_data['data_source']}")
            
            # Cross-reference with expected values based on external data
            print(f"\n🎯 EXPECTED VALUES (from DeBank/Zapper):")
            print(f"   Total Collateral: ~$111 (0.0008174 WBTC + 0.009618 WETH)")
            print(f"   Total Debt: ~$20 (20.0331 USDC)")
            print(f"   Expected Health Factor: ~5.5+ (very safe)")
            
            # Calculate accuracy
            collateral_accuracy = abs(aave_data['total_collateral_usdc'] - 111) / 111 * 100
            debt_accuracy = abs(aave_data['total_debt_usdc'] - 20) / 20 * 100
            
            print(f"\n📊 ACCURACY ANALYSIS:")
            print(f"   Collateral Accuracy: {100-collateral_accuracy:.1f}% (off by ${abs(aave_data['total_collateral_usdc'] - 111):.2f})")
            print(f"   Debt Accuracy: {100-debt_accuracy:.1f}% (off by ${abs(aave_data['total_debt_usdc'] - 20):.2f})")
            
            if collateral_accuracy < 10 and debt_accuracy < 10:
                print(f"✅ ACCURACY CHECK PASSED - Data is within acceptable range")
            else:
                print(f"❌ ACCURACY CHECK FAILED - Significant discrepancies detected")
                print(f"💡 This explains why your dashboard shows inaccurate Aave data")
            
        else:
            print(f"❌ No Aave data retrieved from dashboard function")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_aave_data_accuracy()
