
#!/usr/bin/env python3
"""
Test Dynamic Gas Calculation Accuracy
Compares system estimates with actual wallet interface
"""

from wallet_funding_validator import DynamicWalletFundingValidator
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from gas_fee_calculator import ArbitrumGasCalculator

def test_gas_accuracy():
    print("🧪 TESTING GAS CALCULATION ACCURACY")
    print("=" * 60)
    
    try:
        # Initialize components
        agent = ArbitrumTestnetAgent()
        validator = DynamicWalletFundingValidator()
        gas_calc = ArbitrumGasCalculator()
        
        print(f"📱 YOUR WALLET INTERFACE SHOWS:")
        print(f"   Network fee: 0 ETH (< $0.01)")
        print(f"   Max fee: 0 < $0.01")
        print(f"   Speed: Market ~1 sec")
        
        # Calculate our system's estimate
        approve_fee = gas_calc.calculate_transaction_fee('approve_token', 'market')
        
        print(f"\n🤖 OUR SYSTEM CALCULATES:")
        if approve_fee:
            print(f"   Network fee: {approve_fee['fee_eth']} ETH")
            print(f"   USD cost: {approve_fee['fee_usd']}")
            print(f"   Max fee: {approve_fee['max_fee_usd']}")
            print(f"   Speed: Market")
            
            # Compare accuracy
            our_fee_usd = float(approve_fee['fee_usd'].replace('$', ''))
            wallet_fee_usd = 0.01  # From your screenshot
            
            print(f"\n📊 ACCURACY COMPARISON:")
            print(f"   Wallet interface: < $0.01")
            print(f"   Our calculation: ${our_fee_usd:.4f}")
            print(f"   Difference: ${abs(our_fee_usd - wallet_fee_usd):.4f}")
            
            if our_fee_usd <= 0.01:
                print(f"   ✅ ACCURATE: Our estimate matches wallet interface")
            else:
                print(f"   ⚠️ OVERESTIMATE: Our system is conservative")
        
        # Test full funding validation
        print(f"\n💰 DYNAMIC FUNDING VALIDATION:")
        funding_status = validator.check_wallet_funding(agent)
        
        if funding_status['ready_for_operations']:
            print(f"✅ System correctly identifies wallet as ready")
        else:
            print(f"📊 System requirements:")
            print(f"   ETH needed: {funding_status['required_gas_eth']:.8f} ETH")
            print(f"   USD cost: ${funding_status['actual_gas_cost_usd']:.4f}")
            
            # Compare with old system
            old_requirement = 0.01  # Previous hardcoded minimum
            new_requirement = funding_status['required_gas_eth']
            
            print(f"\n📈 IMPROVEMENT:")
            print(f"   Old system: {old_requirement:.8f} ETH (arbitrary)")
            print(f"   New system: {new_requirement:.8f} ETH (calculated)")
            print(f"   Reduction: {old_requirement - new_requirement:.8f} ETH")
            print(f"   Savings: ${(old_requirement - new_requirement) * 2500:.4f}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_gas_accuracy()
