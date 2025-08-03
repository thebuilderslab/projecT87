
#!/usr/bin/env python3
"""
Enable Debt Swaps - Set environment variables to activate debt swap system
"""

import os
import time

def enable_debt_swaps():
    """Enable debt swap system by setting environment variables"""
    print("🚀 ENABLING DEBT SWAP SYSTEM")
    print("=" * 40)
    
    # Set environment variables for current session
    os.environ['MARKET_SIGNAL_ENABLED'] = 'true'
    os.environ['BTC_DROP_THRESHOLD'] = '0.01'  # 1% BTC drop triggers swap
    os.environ['DAI_TO_ARB_THRESHOLD'] = '0.7'  # 70% confidence threshold
    os.environ['ARB_RSI_OVERSOLD'] = '30'  # RSI threshold
    os.environ['ARB_RSI_OVERBOUGHT'] = '70'  # RSI threshold
    
    print("✅ Environment variables set for current session:")
    print(f"   MARKET_SIGNAL_ENABLED: {os.getenv('MARKET_SIGNAL_ENABLED')}")
    print(f"   BTC_DROP_THRESHOLD: {os.getenv('BTC_DROP_THRESHOLD')}")
    print(f"   DAI_TO_ARB_THRESHOLD: {os.getenv('DAI_TO_ARB_THRESHOLD')}")
    print(f"   ARB_RSI_OVERSOLD: {os.getenv('ARB_RSI_OVERSOLD')}")
    
    print("\n💡 To make this permanent:")
    print("   1. Go to Replit Secrets tab")
    print("   2. Add: MARKET_SIGNAL_ENABLED = true")
    print("   3. Add: BTC_DROP_THRESHOLD = 0.01")
    print("   4. Add: DAI_TO_ARB_THRESHOLD = 0.7")
    print("   5. Add: ARB_RSI_OVERSOLD = 30")
    
    print("\n🔍 Testing debt swap readiness...")
    try:
        from debt_swap_readiness_check import check_debt_swap_readiness
        ready = check_debt_swap_readiness()
        
        if ready:
            print("\n🎉 DEBT SWAP SYSTEM ENABLED AND READY!")
            print("   • System will monitor market conditions automatically")
            print("   • Debt swaps will execute when triggers are met")
            print("   • Check dashboard console for real-time monitoring")
        else:
            print("\n⚠️ Additional setup needed - check readiness report above")
            
    except Exception as e:
        print(f"\n⚠️ Readiness check failed: {e}")
        print("   Basic environment setup completed")

if __name__ == "__main__":
    enable_debt_swaps()
