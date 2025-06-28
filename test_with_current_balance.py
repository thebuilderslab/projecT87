
#!/usr/bin/env python3
"""
Test position creation with current wallet balance
"""

import os
from create_position import PositionCreator
from gas_fee_calculator import ArbitrumGasCalculator

def test_current_balance():
    print("🧪 TESTING WITH CURRENT BALANCE")
    print("=" * 50)
    
    try:
        # Test gas calculation
        gas_calc = ArbitrumGasCalculator()
        
        print("⛽ REALISTIC GAS ESTIMATES:")
        
        # Test Aave operations
        supply_fee = gas_calc.calculate_transaction_fee('aave_supply', 'market')
        borrow_fee = gas_calc.calculate_transaction_fee('aave_borrow', 'market')
        
        print(f"   Supply ETH: {supply_fee['fee_eth']} ETH ({supply_fee['fee_usd']})")
        print(f"   Borrow USDC: {borrow_fee['fee_eth']} ETH ({borrow_fee['fee_usd']})")
        
        total_gas_eth = float(supply_fee['fee_eth']) + float(borrow_fee['fee_eth'])
        print(f"   Total Gas: {total_gas_eth:.6f} ETH (${total_gas_eth * 2500:.4f})")
        
        # Test position creation
        creator = PositionCreator()
        current_balance = creator.get_eth_balance()
        
        print(f"\n💰 CURRENT WALLET:")
        print(f"   ETH Balance: {current_balance:.6f} ETH")
        print(f"   Required Gas: {total_gas_eth:.6f} ETH")
        print(f"   Available for Collateral: {current_balance - total_gas_eth:.6f} ETH")
        
        if current_balance > total_gas_eth:
            collateral_eth = current_balance - total_gas_eth
            collateral_usd = collateral_eth * 2500  # Assuming ETH = $2500
            
            # Calculate safe borrow with health factor > 3.5
            ltv = 0.8  # Aave LTV for ETH
            max_borrow = (collateral_usd * ltv) / 3.5  # Conservative health factor
            
            print(f"\n📊 POSITION ANALYSIS:")
            print(f"   Collateral: {collateral_eth:.6f} ETH (${collateral_usd:.2f})")
            print(f"   Max Safe Borrow: ${max_borrow:.2f} USDC")
            print(f"   Requested Borrow: $20.00 USDC")
            
            if max_borrow >= 20:
                print(f"   ✅ CAN CREATE POSITION with health factor > 3.5")
                return True
            else:
                print(f"   ⚠️ Can only safely borrow ${max_borrow:.2f} USDC")
                print(f"   💡 Reduce borrow amount to ${max_borrow:.2f} for safety")
                return False
        else:
            print(f"   ❌ Insufficient balance for gas fees")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_with_current_balance()
    
    if success:
        print("\n🎉 YOUR BALANCE IS SUFFICIENT!")
        print("💡 The system was being overly conservative")
        print("🚀 Try creating the position again")
    else:
        print("\n⚠️ Balance analysis complete")
        print("💡 Consider the recommendations above")
