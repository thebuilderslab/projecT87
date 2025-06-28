
#!/usr/bin/env python3
"""
Test dynamic gas calculation with current wallet balance
"""

import os
from create_position import PositionCreator
from gas_fee_calculator import ArbitrumGasCalculator

def test_dynamic_gas_with_current_balance():
    print("🧪 TESTING DYNAMIC GAS CALCULATION")
    print("=" * 50)
    
    try:
        # Test gas calculator
        gas_calc = ArbitrumGasCalculator()
        
        print("⛽ CURRENT GAS PRICES:")
        gas_prices = gas_calc.get_current_gas_prices()
        if gas_prices:
            for speed, price in gas_prices.items():
                gwei = gas_calc.w3.from_wei(price, 'gwei')
                print(f"   {speed.capitalize()}: {gwei:.2f} gwei")
        
        print("\n⛽ OPERATION COSTS:")
        operations = ['aave_supply', 'aave_borrow', 'approve_token', 'erc20_transfer']
        total_cost = 0
        
        for op in operations:
            fee_data = gas_calc.calculate_transaction_fee(op, 'market')
            if fee_data:
                cost_eth = float(fee_data['fee_eth'])
                total_cost += cost_eth
                print(f"   {op}: {fee_data['fee_eth']} ETH ({fee_data['fee_usd']})")
        
        print(f"\n💰 TOTAL ESTIMATED COST: {total_cost:.8f} ETH")
        
        # Test with current wallet
        creator = PositionCreator()
        current_balance = creator.get_eth_balance()
        
        print(f"\n💳 WALLET STATUS:")
        print(f"   Current Balance: {current_balance:.8f} ETH")
        print(f"   Required for Operations: {total_cost:.8f} ETH")
        print(f"   Available for Collateral: {max(0, current_balance - total_cost):.8f} ETH")
        
        if current_balance >= total_cost:
            print("✅ Sufficient balance for transactions!")
            collateral_eth = current_balance - total_cost
            collateral_usd = collateral_eth * 2500
            max_borrow = (collateral_usd * 0.8) / 3.5  # Health factor > 3.5
            print(f"   Max safe borrow: ${max_borrow:.4f} USDC")
        else:
            shortfall = total_cost - current_balance
            print(f"❌ Insufficient balance")
            print(f"   Shortfall: {shortfall:.8f} ETH (${shortfall * 2500:.4f})")
            print(f"   Need to add: {shortfall * 1.1:.8f} ETH minimum")
        
        # Test micro-position option
        if current_balance < total_cost:
            print(f"\n🔬 MICRO-POSITION ANALYSIS:")
            print("   With current balance, consider:")
            print("   1. Add more ETH for full $20 USDC position")
            print("   2. Wait for lower gas prices")
            print("   3. Use testnet for testing")
            
        return current_balance >= total_cost
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_dynamic_gas_with_current_balance()
    
    if success:
        print("\n🎉 READY: Current balance sufficient for dynamic gas calculation")
    else:
        print("\n⚠️ MORE FUNDS NEEDED: Add ETH to wallet for full operation")
        
    print(f"\n💡 To proceed with current balance, set AUTO_PROCEED_MICRO=true in secrets")
