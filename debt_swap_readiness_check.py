
#!/usr/bin/env python3
"""
Debt Swap Readiness Check - Comprehensive verification of debt swap system
"""

import os
import sys
import time
from datetime import datetime

def check_debt_swap_readiness():
    """Comprehensive check of debt swap system readiness"""
    print("🔍 DEBT SWAP SYSTEM READINESS CHECK")
    print("=" * 50)
    
    readiness_score = 0
    max_score = 10
    
    # 1. Environment Variables Check
    print("\n1️⃣ Environment Variables:")
    market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'NOT_SET')
    if market_enabled.lower() == 'true':
        print("   ✅ MARKET_SIGNAL_ENABLED: true")
        readiness_score += 2
    else:
        print(f"   ❌ MARKET_SIGNAL_ENABLED: {market_enabled}")
        print("   💡 Set MARKET_SIGNAL_ENABLED=true in Replit Secrets")
    
    btc_threshold = os.getenv('BTC_DROP_THRESHOLD', 'NOT_SET')
    if btc_threshold != 'NOT_SET':
        print(f"   ✅ BTC_DROP_THRESHOLD: {btc_threshold}")
        readiness_score += 1
    else:
        print("   ⚠️ BTC_DROP_THRESHOLD: Using default (0.01)")
        readiness_score += 0.5
    
    dai_threshold = os.getenv('DAI_TO_ARB_THRESHOLD', 'NOT_SET')
    if dai_threshold != 'NOT_SET':
        print(f"   ✅ DAI_TO_ARB_THRESHOLD: {dai_threshold}")
        readiness_score += 1
    else:
        print("   ⚠️ DAI_TO_ARB_THRESHOLD: Using default (0.7)")
        readiness_score += 0.5
    
    # 2. Agent Integration Check
    print("\n2️⃣ Agent Integration:")
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        print("   ✅ Agent initialization: SUCCESS")
        readiness_score += 2
        
        # Check if market signal strategy exists
        if hasattr(agent, 'market_signal_strategy'):
            print("   ✅ Market signal strategy: AVAILABLE")
            readiness_score += 1
        else:
            print("   ❌ Market signal strategy: NOT FOUND")
            
    except Exception as e:
        print(f"   ❌ Agent initialization: FAILED - {e}")
    
    # 3. Market Signal Strategy Check
    print("\n3️⃣ Market Signal Strategy:")
    try:
        if os.path.exists('market_signal_strategy.py'):
            print("   ✅ Strategy file exists")
            readiness_score += 1
        else:
            print("   ❌ Strategy file missing")
            
        # Try to import market signal strategy
        try:
            from market_signal_strategy import MarketSignalStrategy
            print("   ✅ Strategy imports successfully")
            readiness_score += 1
        except Exception as e:
            print(f"   ❌ Strategy import failed: {e}")
            
    except Exception as e:
        print(f"   ❌ Strategy check failed: {e}")
    
    # 4. Network and Account Status
    print("\n4️⃣ Network & Account Status:")
    try:
        if agent:
            # Check network connection
            chain_id = agent.w3.eth.chain_id
            if chain_id == 42161:
                print("   ✅ Arbitrum Mainnet connected")
                readiness_score += 1
            else:
                print(f"   ⚠️ Connected to chain {chain_id}")
                readiness_score += 0.5
                
            # Check account data
            if hasattr(agent, 'aave'):
                agent.initialize_integrations()
                account_data = agent.aave.get_user_account_data()
                if account_data:
                    hf = account_data.get('healthFactor', 0)
                    available = account_data.get('availableBorrowsUSD', 0)
                    print(f"   ✅ Account data: HF={hf:.3f}, Available=${available:.2f}")
                    if hf > 1.5 and available > 5:
                        readiness_score += 1
                    else:
                        readiness_score += 0.5
                else:
                    print("   ⚠️ Account data unavailable")
    except Exception as e:
        print(f"   ❌ Network check failed: {e}")
    
    # 5. Dashboard Integration
    print("\n5️⃣ Dashboard Integration:")
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        if 'web_dashboard.py' in result.stdout or 'start_dashboard.py' in result.stdout:
            print("   ✅ Web dashboard running")
            readiness_score += 1
        else:
            print("   ⚠️ Web dashboard not detected")
            readiness_score += 0.5
    except:
        print("   ⚠️ Dashboard check inconclusive")
        readiness_score += 0.5
    
    # Final Assessment
    print(f"\n📊 READINESS ASSESSMENT:")
    print(f"   Score: {readiness_score:.1f}/{max_score}")
    percentage = (readiness_score / max_score) * 100
    
    if percentage >= 90:
        status = "🟢 FULLY READY"
        recommendation = "Debt swap system is ready for operation!"
    elif percentage >= 70:
        status = "🟡 MOSTLY READY" 
        recommendation = "Minor configuration needed"
    elif percentage >= 50:
        status = "🟠 PARTIALLY READY"
        recommendation = "Some key components need attention"
    else:
        status = "🔴 NOT READY"
        recommendation = "Significant setup required"
    
    print(f"   Status: {status} ({percentage:.1f}%)")
    print(f"   Recommendation: {recommendation}")
    
    # Next Steps
    print(f"\n🚀 NEXT STEPS:")
    if market_enabled.lower() != 'true':
        print("   1. Set MARKET_SIGNAL_ENABLED=true in Replit Secrets")
    if not hasattr(agent, 'market_signal_strategy') if 'agent' in locals() else True:
        print("   2. Ensure market_signal_strategy.py is properly integrated")
    if percentage < 90:
        print("   3. Run this check again after making changes")
    else:
        print("   1. System ready - debt swaps will execute when market conditions are met")
        print("   2. Monitor dashboard console for real-time debt swap activity")
    
    return readiness_score >= 7  # 70% threshold for "ready"

if __name__ == "__main__":
    ready = check_debt_swap_readiness()
    sys.exit(0 if ready else 1)
