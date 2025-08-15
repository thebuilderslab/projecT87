
#!/usr/bin/env python3
"""
Debug why borrowing isn't happening
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
import time

def debug_borrowing_conditions():
    print("🔍 DEBUGGING BORROWING CONDITIONS")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"✅ Agent initialized")
        print(f"📍 Wallet: {agent.address}")
        print(f"💰 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Get current account data
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot get account data")
            return
            
        health_factor = account_data.get('healthFactor', 0)
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        total_collateral = account_data.get('totalCollateralUSD', 0)
        total_debt = account_data.get('totalDebtUSD', 0)
        
        print(f"\n📊 CURRENT POSITION:")
        print(f"   Health Factor: {health_factor:.3f}")
        print(f"   Total Collateral: ${total_collateral:.2f}")
        print(f"   Total Debt: ${total_debt:.2f}")
        print(f"   Available Borrows: ${available_borrows:.2f}")
        
        # Check borrowing conditions
        print(f"\n🔍 BORROWING CONDITION CHECKS:")
        
        # Growth-triggered conditions
        print(f"📈 GROWTH-TRIGGERED CONDITIONS:")
        growth_hf_ok = health_factor >= agent.growth_health_factor_threshold
        growth_capacity_ok = available_borrows >= agent.capacity_available_threshold
        print(f"   Health Factor >= {agent.growth_health_factor_threshold}: {'✅' if growth_hf_ok else '❌'} ({health_factor:.3f})")
        print(f"   Available Borrows >= ${agent.capacity_available_threshold}: {'✅' if growth_capacity_ok else '❌'} (${available_borrows:.2f})")
        
        # Check growth since baseline
        growth_since_baseline = 0
        if hasattr(agent, 'last_collateral_value_usd') and agent.last_collateral_value_usd > 0:
            growth_since_baseline = total_collateral - agent.last_collateral_value_usd
            growth_trigger_ok = growth_since_baseline >= agent.growth_trigger_threshold
            print(f"   Growth since baseline >= ${agent.growth_trigger_threshold}: {'✅' if growth_trigger_ok else '❌'} (${growth_since_baseline:.2f})")
        else:
            print(f"   Growth since baseline: ⚠️ No baseline set (${agent.last_collateral_value_usd:.2f})")
            growth_trigger_ok = False
        
        # Capacity-based conditions
        print(f"\n⚡ CAPACITY-BASED CONDITIONS:")
        capacity_hf_ok = health_factor >= agent.capacity_health_factor_threshold
        capacity_available_ok = available_borrows >= agent.capacity_available_threshold
        capacity_large_ok = available_borrows > 50  # $50 threshold
        print(f"   Health Factor >= {agent.capacity_health_factor_threshold}: {'✅' if capacity_hf_ok else '❌'} ({health_factor:.3f})")
        print(f"   Available Borrows >= ${agent.capacity_available_threshold}: {'✅' if capacity_available_ok else '❌'} (${available_borrows:.2f})")
        print(f"   Large Available Capacity > $50: {'✅' if capacity_large_ok else '❌'} (${available_borrows:.2f})")
        
        # Cooldown check
        print(f"\n⏰ COOLDOWN STATUS:")
        current_time = time.time()
        time_since_last = current_time - agent.last_successful_operation_time
        cooldown_ok = time_since_last >= agent.operation_cooldown_seconds
        print(f"   Time since last operation: {time_since_last:.0f}s")
        print(f"   Cooldown period: {agent.operation_cooldown_seconds}s")
        print(f"   Cooldown satisfied: {'✅' if cooldown_ok else '❌'}")
        
        # Overall verdict
        print(f"\n🎯 BORROWING VERDICT:")
        growth_ready = growth_hf_ok and growth_capacity_ok and growth_trigger_ok and cooldown_ok
        capacity_ready = capacity_hf_ok and capacity_available_ok and capacity_large_ok and cooldown_ok
        
        print(f"   Growth-triggered ready: {'✅' if growth_ready else '❌'}")
        print(f"   Capacity-based ready: {'✅' if capacity_ready else '❌'}")
        
        if growth_ready or capacity_ready:
            print(f"   🚀 BORROWING SHOULD HAPPEN!")
            
            # Test actual borrowing calculation
            borrow_amount = agent._calculate_validated_borrow_amount(available_borrows, "growth" if growth_ready else "capacity")
            print(f"   💰 Calculated borrow amount: ${borrow_amount:.2f}")
            
            if borrow_amount >= 0.5:
                print(f"   ✅ Borrow amount sufficient for execution")
            else:
                print(f"   ❌ Borrow amount too small: ${borrow_amount:.2f}")
        else:
            print(f"   ⏸️ No borrowing conditions met")
            
            # Suggestions
            print(f"\n💡 SUGGESTIONS:")
            if not growth_hf_ok or not capacity_hf_ok:
                print(f"   • Health factor too low - need more collateral")
            if not growth_capacity_ok or not capacity_available_ok:
                print(f"   • Available borrows too low - need more collateral or less debt")
            if not growth_trigger_ok:
                print(f"   • No significant growth detected - system is waiting for collateral growth")
            if not cooldown_ok:
                print(f"   • Operation in cooldown - wait {agent.operation_cooldown_seconds - time_since_last:.0f}s")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_borrowing_conditions()
