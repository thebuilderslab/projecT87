
#!/usr/bin/env python3
"""
Test Enhanced RPC Manager
Verify that contract interactions work reliably
"""

import os
from enhanced_contract_manager import EnhancedContractManager
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_enhanced_rpc():
    print("🧪 TESTING ENHANCED RPC MANAGER")
    print("=" * 50)
    
    try:
        # Initialize enhanced contract manager
        manager = EnhancedContractManager()
        
        # Test RPC optimization
        print("\n🔧 Testing RPC optimization...")
        if manager.optimize_for_contract_calls():
            print("✅ RPC optimization successful")
        else:
            print("❌ RPC optimization failed")
            return False
        
        # Get test wallet address
        try:
            agent = ArbitrumTestnetAgent()
            test_wallet = agent.address
            print(f"📝 Testing with wallet: {test_wallet}")
        except Exception as e:
            print(f"⚠️ Could not get agent wallet, using default: {e}")
            test_wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        
        # Test token balance retrieval
        print("\n💰 Testing token balance retrieval...")
        
        tokens_to_test = [
            ("USDC", manager.usdc_address),
            ("WBTC", manager.wbtc_address), 
            ("WETH", manager.weth_address),
            ("ARB", manager.arb_address)
        ]
        
        success_count = 0
        for name, address in tokens_to_test:
            print(f"\n🔄 Testing {name} balance...")
            try:
                balance = manager.get_token_balance_robust(address, test_wallet)
                print(f"✅ {name} balance: {balance:.8f}")
                success_count += 1
            except Exception as e:
                print(f"❌ {name} balance failed: {e}")
        
        print(f"\n📊 Token balance success rate: {success_count}/{len(tokens_to_test)} ({success_count/len(tokens_to_test)*100:.1f}%)")
        
        # Test Aave data retrieval
        print("\n🏦 Testing Aave data retrieval...")
        try:
            aave_pool = "0x794a61358d6845594f94dc1db02a252b5b4814ad"
            aave_data = manager.get_aave_data_robust(test_wallet, aave_pool)
            
            if aave_data:
                print("✅ Aave data retrieved successfully")
                print(f"   Health Factor: {aave_data['health_factor']:.2f}")
                print(f"   Collateral: ${aave_data['total_collateral_usd']:.2f}")
                print(f"   Debt: ${aave_data['total_debt_usd']:.2f}")
            else:
                print("❌ Aave data retrieval failed")
        except Exception as e:
            print(f"❌ Aave data test failed: {e}")
        
        # Test RPC performance tracking
        print("\n📈 RPC Performance Summary:")
        if manager.rpc_performance:
            for rpc_url, perf_data in manager.rpc_performance.items():
                print(f"   {rpc_url}:")
                print(f"     Score: {perf_data['score']:.2f}")
                print(f"     Total time: {perf_data['total_time']:.3f}s")
                print(f"     Token call time: {perf_data['token_time']:.3f}s")
        
        print("\n✅ Enhanced RPC testing completed")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced RPC test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_rpc()
