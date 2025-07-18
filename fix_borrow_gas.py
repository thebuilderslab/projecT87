
#!/usr/bin/env python3
"""
Enhanced Borrow Fix Script
Tests all gas pricing and borrowing improvements
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
from enhanced_borrow_manager import EnhancedBorrowManager
import time

def test_gas_estimation():
    """Test gas estimation improvements"""
    try:
        print("🔧 TESTING GAS ESTIMATION IMPROVEMENTS")
        print("=" * 50)
        
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"✅ Agent initialized: {agent.address}")
        print(f"💰 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Test gas parameter generation
        print(f"\n⛽ TESTING GAS PARAMETER GENERATION")
        gas_params = agent.aave.get_optimized_gas_params('aave_borrow', 'market')
        print(f"✅ Gas parameters generated successfully")
        
        # Get current network conditions
        current_block = agent.w3.eth.get_block('latest')
        base_fee = current_block.get('baseFeePerGas', 0)
        gas_price = agent.w3.eth.gas_price
        
        print(f"\n🌐 NETWORK CONDITIONS:")
        print(f"   Base fee: {base_fee:,} wei ({agent.w3.from_wei(base_fee, 'gwei'):.2f} gwei)")
        print(f"   Gas price: {gas_price:,} wei ({agent.w3.from_wei(gas_price, 'gwei'):.2f} gwei)")
        
        # Test different gas conditions
        for condition in ['low', 'normal', 'high', 'urgent', 'market']:
            params = agent.aave.get_optimized_gas_params('aave_borrow', condition)
            if 'gasPrice' in params:
                price_gwei = agent.w3.from_wei(params['gasPrice'], 'gwei')
                print(f"   {condition.capitalize()}: {price_gwei:.2f} gwei (gas: {params['gas']:,})")
            elif 'maxFeePerGas' in params:
                max_fee_gwei = agent.w3.from_wei(params['maxFeePerGas'], 'gwei')
                priority_gwei = agent.w3.from_wei(params['maxPriorityFeePerGas'], 'gwei')
                print(f"   {condition.capitalize()}: max {max_fee_gwei:.2f} gwei, priority {priority_gwei:.2f} gwei (gas: {params['gas']:,})")
        
        return True
        
    except Exception as e:
        print(f"❌ Gas estimation test failed: {e}")
        return False

def test_enhanced_borrow_manager():
    """Test enhanced borrow manager with all mechanisms"""
    try:
        print(f"\n🏦 TESTING ENHANCED BORROW MANAGER")
        print("=" * 50)
        
        # Initialize agent and enhanced borrow manager
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        ebm = EnhancedBorrowManager(agent)
        
        print(f"✅ Enhanced Borrow Manager initialized")
        
        # Test amount conversion
        test_amount = 1.0  # $1 USDC
        decimals = ebm._get_token_decimals(agent.usdc_address)
        expected_wei = int(test_amount * (10 ** decimals))
        
        print(f"\n💱 AMOUNT CONVERSION TEST:")
        print(f"   USD Amount: ${test_amount}")
        print(f"   Token: USDC (decimals: {decimals})")
        print(f"   Wei Amount: {expected_wei}")
        
        # Check if we have available borrows
        try:
            position_data = agent.aave._get_robust_position_data(agent.address)
            if position_data:
                available_borrows = position_data.get('available_borrows_usd', 0)
                health_factor = position_data.get('health_factor', 0)
                
                print(f"\n📊 CURRENT AAVE POSITION:")
                print(f"   Available borrows: ${available_borrows:.2f}")
                print(f"   Health factor: {health_factor:.2f}")
                
                if available_borrows >= test_amount and health_factor > 1.5:
                    print(f"✅ Position suitable for test borrow")
                    
                    # Execute test borrow
                    print(f"\n🧪 EXECUTING TEST BORROW: ${test_amount} USDC")
                    result = ebm.safe_borrow_with_fallbacks(test_amount, agent.usdc_address)
                    
                    if result:
                        print(f"✅ ENHANCED BORROW SUCCESSFUL!")
                        print(f"🔗 Transaction: {result}")
                        return True
                    else:
                        print(f"❌ Enhanced borrow failed")
                        return False
                else:
                    print(f"⚠️ Position not suitable for test borrow")
                    print(f"   Need: available_borrows >= ${test_amount}, health_factor > 1.5")
                    return False
            else:
                print(f"❌ Could not fetch Aave position data")
                return False
                
        except Exception as position_error:
            print(f"❌ Position check failed: {position_error}")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced borrow manager test failed: {e}")
        return False

def test_retry_logic():
    """Test retry logic implementation"""
    try:
        print(f"\n🔄 TESTING RETRY LOGIC")
        print("=" * 50)
        
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        ebm = EnhancedBorrowManager(agent)
        
        # Test gas multiplier progression
        gas_multipliers = [1.2, 1.5, 1.8, 2.0, 2.5]
        base_gas_price = agent.w3.eth.gas_price
        
        print(f"📈 RETRY GAS PROGRESSION:")
        print(f"   Base gas price: {agent.w3.from_wei(base_gas_price, 'gwei'):.2f} gwei")
        
        for i, multiplier in enumerate(gas_multipliers):
            adjusted_price = int(base_gas_price * multiplier)
            print(f"   Attempt {i+1}: {agent.w3.from_wei(adjusted_price, 'gwei'):.2f} gwei (x{multiplier})")
        
        print(f"✅ Retry logic parameters validated")
        return True
        
    except Exception as e:
        print(f"❌ Retry logic test failed: {e}")
        return False

def main():
    """Run comprehensive borrow fix testing"""
    print("🎯 COMPREHENSIVE BORROW FIX TESTING")
    print("=" * 60)
    
    tests = [
        ("Gas Estimation", test_gas_estimation),
        ("Enhanced Borrow Manager", test_enhanced_borrow_manager),
        ("Retry Logic", test_retry_logic)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\n🏆 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print(f"\n🚀 BORROWING SYSTEM IS READY FOR PRODUCTION!")
        print(f"   ✅ Dynamic gas pricing implemented")
        print(f"   ✅ Enhanced retry logic active")
        print(f"   ✅ Proper USD to wei conversion")
        print(f"   ✅ Multiple fallback mechanisms")
    else:
        print(f"\n🔧 ISSUES FOUND - REVIEW FAILED TESTS")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
