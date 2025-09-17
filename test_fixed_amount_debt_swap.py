#!/usr/bin/env python3
"""
Fixed Amount Debt Swap Test
Tests debt swap functionality with current system limitations:
1. Swap 5 DAI → ARB debt
2. Wait 5 minutes 
3. Swap 5 ARB → DAI debt
4. Log PnL results
"""

import os
import time
import json
from datetime import datetime
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_fixed_amount_debt_swap():
    """Execute fixed amount debt swap test"""
    
    print("🧪 FIXED AMOUNT DEBT SWAP TEST")
    print("=" * 60)
    print("📝 Test Parameters:")
    print("   Step 1: 5 DAI → ARB debt")
    print("   Step 2: Wait 5 minutes")
    print("   Step 3: 5 ARB → DAI debt")
    print("   Step 4: Log PnL results")
    print("=" * 60)
    
    try:
        # Initialize agent
        print("\n🔄 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent.w3.is_connected():
            raise Exception("❌ Web3 connection failed")
        
        print(f"✅ Connected to chain ID: {agent.w3.eth.chain_id}")
        print(f"📍 Wallet: {agent.address}")
        
        # Check initial health factor using Aave integration
        print("\n📊 PRE-TEST POSITION:")
        try:
            # Use agent's aave integration to get account data
            aave_data = agent.aave.get_user_account_data()
            
            health_data = {
                'health_factor': aave_data.get('healthFactor', 0),
                'total_debt_usdc': aave_data.get('totalDebtUSD', 0),
                'total_collateral_usdc': aave_data.get('totalCollateralUSD', 0),
                'available_borrows_usdc': aave_data.get('availableBorrowsUSD', 0),
                'data_source': aave_data.get('data_source', 'aave_contract')
            }
            
            print(f"   Health Factor: {health_data['health_factor']:.4f}")
            print(f"   Total Collateral: ${health_data['total_collateral_usdc']:.2f}")
            print(f"   Total Debt: ${health_data['total_debt_usdc']:.2f}")
            print(f"   Available Borrows: ${health_data['available_borrows_usdc']:.2f}")
            print(f"   Data Source: {health_data['data_source']}")
            
        except Exception as e:
            print(f"⚠️ Could not fetch health data: {e}")
            health_data = None
        
        # Check if we have debt swap capability
        if not hasattr(agent, 'debt_swap_integration'):
            print("⚠️ Debt swap integration not found, initializing...")
            from production_debt_swap_integration import ProductionDebtSwapIntegration
            agent.debt_swap_integration = ProductionDebtSwapIntegration(agent)
        
        # Get private key for transactions
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise Exception("❌ PRIVATE_KEY environment variable not found")
        
        print("\n🎯 STEP 1: EXECUTING 5 DAI → ARB DEBT SWAP")
        print("-" * 40)
        
        # Force trigger DAI → ARB swap (bypass market conditions)
        swap_result_1 = agent.debt_swap_integration.executor.execute_real_debt_swap(
            private_key, 'DAI', 'ARB', 5.0
        )
        
        print(f"📊 Step 1 Result: {swap_result_1.get('success', False)}")
        if swap_result_1.get('transaction_hash'):
            print(f"🔗 Transaction: {swap_result_1['transaction_hash']}")
        
        # Capture position after first swap
        print("\n📸 POSITION AFTER STEP 1:")
        try:
            aave_data_step1 = agent.aave.get_user_account_data()
            health_data_step1 = {
                'health_factor': aave_data_step1.get('healthFactor', 0),
                'total_debt_usdc': aave_data_step1.get('totalDebtUSD', 0),
                'total_collateral_usdc': aave_data_step1.get('totalCollateralUSD', 0),
                'available_borrows_usdc': aave_data_step1.get('availableBorrowsUSD', 0)
            }
            
            print(f"   Health Factor: {health_data_step1['health_factor']:.4f}")
            print(f"   Total Debt: ${health_data_step1['total_debt_usdc']:.2f}")
            
        except Exception as e:
            print(f"⚠️ Could not fetch step 1 health data: {e}")
            health_data_step1 = None
        
        print("\n⏳ STEP 2: WAITING 5 MINUTES...")
        print("-" * 40)
        print("⏰ Starting 5-minute cooldown period...")
        
        # Wait 5 minutes with progress updates
        for minute in range(5):
            print(f"   ⏱️ Minute {minute + 1}/5 completed")
            time.sleep(60)  # Wait 1 minute
        
        print("✅ 5-minute wait period completed!")
        
        print("\n🎯 STEP 3: EXECUTING 5 ARB → DAI DEBT SWAP")
        print("-" * 40)
        
        # Execute return swap
        swap_result_2 = agent.debt_swap_integration.executor.execute_real_debt_swap(
            private_key, 'ARB', 'DAI', 5.0
        )
        
        print(f"📊 Step 3 Result: {swap_result_2.get('success', False)}")
        if swap_result_2.get('transaction_hash'):
            print(f"🔗 Transaction: {swap_result_2['transaction_hash']}")
        
        # Capture final position
        print("\n📸 FINAL POSITION:")
        try:
            aave_data_final = agent.aave.get_user_account_data()
            health_data_final = {
                'health_factor': aave_data_final.get('healthFactor', 0),
                'total_debt_usdc': aave_data_final.get('totalDebtUSD', 0),
                'total_collateral_usdc': aave_data_final.get('totalCollateralUSD', 0),
                'available_borrows_usdc': aave_data_final.get('availableBorrowsUSD', 0)
            }
            
            print(f"   Health Factor: {health_data_final['health_factor']:.4f}")
            print(f"   Total Debt: ${health_data_final['total_debt_usdc']:.2f}")
            
        except Exception as e:
            print(f"⚠️ Could not fetch final health data: {e}")
            health_data_final = None
        
        # Calculate and log PnL
        print("\n📊 STEP 4: PNL ANALYSIS")
        print("-" * 40)
        
        if health_data and health_data_final:
            initial_debt = health_data['total_debt_usdc']
            final_debt = health_data_final['total_debt_usdc']
            debt_change = final_debt - initial_debt
            
            initial_hf = health_data['health_factor']
            final_hf = health_data_final['health_factor']
            hf_change = final_hf - initial_hf
            
            print(f"💰 DEBT ANALYSIS:")
            print(f"   Initial Debt: ${initial_debt:.2f}")
            print(f"   Final Debt: ${final_debt:.2f}")
            print(f"   Debt Change: ${debt_change:.2f}")
            
            print(f"❤️ HEALTH FACTOR ANALYSIS:")
            print(f"   Initial HF: {initial_hf:.4f}")
            print(f"   Final HF: {final_hf:.4f}")
            print(f"   HF Change: {hf_change:.4f}")
            
            # Determine test result
            if abs(debt_change) < 1.0 and abs(hf_change) < 0.01:
                print("✅ TEST RESULT: SUCCESSFUL - Position maintained with minimal drift")
            elif debt_change < 0:
                print(f"💰 TEST RESULT: PROFITABLE - Debt reduced by ${-debt_change:.2f}")
            else:
                print(f"⚠️ TEST RESULT: COST - Debt increased by ${debt_change:.2f}")
        
        print("\n🎉 FIXED AMOUNT DEBT SWAP TEST COMPLETED!")
        print("=" * 60)
        
        return {
            'success': True,
            'swap_1': swap_result_1,
            'swap_2': swap_result_2,
            'initial_position': health_data,
            'final_position': health_data_final
        }
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_fixed_amount_debt_swap()
    print(f"\n📋 Test Result: {result}")