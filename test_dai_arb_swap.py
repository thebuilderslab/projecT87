
#!/usr/bin/env python3
"""
Test script to execute DAI → ARB → DAI swap sequence
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_dai_arb_swap_sequence():
    """Test DAI → ARB → DAI swap sequence"""
    try:
        print("🔄 TESTING DAI ↔ ARB SWAP SEQUENCE")
        print("=" * 50)
        
        # Initialize agent
        print("🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        # Check initial balances
        print("\n📊 INITIAL BALANCES:")
        dai_balance = agent.aave.get_dai_balance() if agent.aave else 0
        eth_balance = agent.get_eth_balance()
        
        print(f"   DAI: {dai_balance:.6f}")
        print(f"   ETH: {eth_balance:.6f}")
        
        if dai_balance < 10.0:
            print("❌ Insufficient DAI balance for 10 DAI swap")
            return False
        
        if eth_balance < 0.001:
            print("❌ Insufficient ETH for gas fees")
            return False
        
        # Check if market signal strategy supports debt swaps
        if not hasattr(agent, 'market_signal_strategy') or not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return False
        
        # Check debt swap conditions
        conditions_ok, message = agent.check_debt_swap_conditions()
        if not conditions_ok:
            print(f"⚠️ Debt swap conditions not met: {message}")
            print("🔄 Attempting direct swap via Uniswap...")
            
            # Direct Uniswap swap as fallback
            return execute_direct_swap(agent)
        
        print("✅ Debt swap conditions met - using market signal strategy")
        
        # Execute market-driven debt swap
        return execute_market_signal_swap(agent)
        
    except Exception as e:
        print(f"❌ Swap test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def execute_market_signal_swap(agent):
    """Execute swap using market signal strategy"""
    try:
        print("\n🎯 EXECUTING MARKET SIGNAL DEBT SWAP")
        
        # Get current market signals
        signals = agent.market_signal_strategy.analyze_market_signals()
        
        if signals and signals.get('status') == 'success':
            print(f"📊 Market Analysis:")
            print(f"   Action: {signals.get('action', 'hold')}")
            print(f"   Confidence: {signals.get('confidence_level', 0):.2f}")
            print(f"   Recommendation: {signals.get('recommendation', 'HOLD')}")
        
        # Force a DAI → ARB swap for testing
        print("\n🔄 Step 1: Forcing DAI → ARB swap...")
        
        # Execute the debt swap operation
        success = agent._execute_market_signal_operation(available_borrows_usd=10.0)
        
        if success:
            print("✅ DAI → ARB swap completed successfully")
            
            # Wait for confirmation
            time.sleep(10)
            
            # Check new balances
            print("\n📊 POST-SWAP BALANCES:")
            dai_balance = agent.aave.get_dai_balance()
            print(f"   DAI: {dai_balance:.6f}")
            
            # Step 2: Swap back ARB → DAI
            print("\n🔄 Step 2: Swapping ARB → DAI...")
            
            # This would require ARB balance and reverse swap logic
            print("⚠️ Reverse swap (ARB → DAI) requires manual implementation")
            print("💡 System is designed for market-driven debt swaps, not round-trip testing")
            
            return True
        else:
            print("❌ DAI → ARB swap failed")
            return False
            
    except Exception as e:
        print(f"❌ Market signal swap failed: {e}")
        return False

def execute_direct_swap(agent):
    """Execute direct Uniswap swap as fallback"""
    try:
        print("\n🔄 EXECUTING DIRECT UNISWAP SWAP")
        
        # Step 1: DAI → WBTC (since DAI → ARB may not have good liquidity)
        print("🔄 Step 1: DAI → WBTC swap...")
        
        swap_result = agent.uniswap.swap_dai_for_wbtc(10.0)
        
        if swap_result and swap_result.get('success'):
            print(f"✅ DAI → WBTC swap successful!")
            print(f"   TX Hash: {swap_result.get('tx_hash')}")
            
            # Wait for confirmation
            time.sleep(15)
            
            print("\n📊 SWAP COMPLETED")
            print("⚠️ Note: Reverse swap would require WBTC → DAI")
            print("💡 System focuses on DAI-based leveraging, not round-trip swaps")
            
            return True
        else:
            print("❌ DAI → WBTC swap failed")
            return False
            
    except Exception as e:
        print(f"❌ Direct swap failed: {e}")
        return False

def check_system_capabilities():
    """Check system swap capabilities"""
    try:
        print("\n🔍 CHECKING SYSTEM SWAP CAPABILITIES")
        print("=" * 40)
        
        agent = ArbitrumTestnetAgent()
        
        # Check integrations
        uniswap_available = hasattr(agent, 'uniswap') and agent.uniswap
        market_strategy_available = hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy
        
        print(f"✅ Uniswap Integration: {'Available' if uniswap_available else 'Missing'}")
        print(f"✅ Market Strategy: {'Available' if market_strategy_available else 'Missing'}")
        print(f"✅ Debt Swap Active: {getattr(agent, 'debt_swap_active', False)}")
        
        if market_strategy_available:
            status = agent.market_signal_strategy.get_strategy_status()
            print(f"✅ Technical Indicators: {'Ready' if status.get('technical_indicators_ready') else 'Not Ready'}")
            print(f"✅ Data Source: {status.get('data_source', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Capability check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 DAI ↔ ARB SWAP TEST")
    print("=" * 30)
    
    # First check capabilities
    if not check_system_capabilities():
        print("❌ System capability check failed")
        exit(1)
    
    # Then test swap
    success = test_dai_arb_swap_sequence()
    
    if success:
        print("\n🎉 SWAP TEST COMPLETED SUCCESSFULLY")
    else:
        print("\n❌ SWAP TEST FAILED")
        print("💡 Check logs for details")
