
#!/usr/bin/env python3
"""
Enhanced DAI → WBTC Swap System with Full Validation
DAI COMPLIANCE ENFORCED: Only DAI → WBTC swaps permitted
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def enhanced_dai_to_wbtc_swap():
    """Execute enhanced DAI → WBTC swap with comprehensive validation"""
    try:
        print("🔄 ENHANCED DAI → WBTC SWAP SYSTEM")
        print("=" * 50)
        
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Validate DAI balance
        dai_balance = agent.aave.get_token_balance(agent.dai_address)
        print(f"💰 DAI Balance: {dai_balance:.6f}")
        
        if dai_balance < 1.0:
            print("❌ Insufficient DAI balance for swap")
            return False
        
        # Calculate swap amount (conservative)
        swap_amount = min(dai_balance * 0.5, 5.0)  # 50% of balance or max $5
        print(f"🎯 Swap Amount: ${swap_amount:.2f} DAI → WBTC")
        
        # Pre-swap validation
        print("\n🔍 Pre-swap validation...")
        
        # Validate DAI contract
        dai_contract = agent.w3.eth.contract(
            address=agent.dai_address,
            abi=agent.uniswap.erc20_abi
        )
        
        try:
            dai_symbol = dai_contract.functions.symbol().call()
            dai_decimals = dai_contract.functions.decimals().call()
            print(f"   ✅ DAI contract validated: {dai_symbol} (decimals: {dai_decimals})")
        except Exception as e:
            print(f"   ❌ DAI contract validation failed: {e}")
            return False
        
        # Validate WBTC contract
        wbtc_contract = agent.w3.eth.contract(
            address=agent.wbtc_address,
            abi=agent.uniswap.erc20_abi
        )
        
        try:
            wbtc_symbol = wbtc_contract.functions.symbol().call()
            wbtc_decimals = wbtc_contract.functions.decimals().call()
            print(f"   ✅ WBTC contract validated: {wbtc_symbol} (decimals: {wbtc_decimals})")
        except Exception as e:
            print(f"   ❌ WBTC contract validation failed: {e}")
            return False
        
        # Execute swap with enhanced error handling
        print(f"\n🔄 Executing DAI → WBTC swap...")
        
        swap_result = agent.uniswap.swap_tokens(
            agent.dai_address,     # DAI in
            agent.wbtc_address,    # WBTC out
            swap_amount,           # Amount
            500                    # 0.05% fee tier
        )
        
        if swap_result:
            print("✅ DAI → WBTC swap successful!")
            print(f"   Transaction hash: {swap_result}")
            
            # Wait for confirmation
            time.sleep(10)
            
            # Check WBTC balance
            wbtc_balance = agent.aave.get_token_balance(agent.wbtc_address)
            print(f"💰 New WBTC Balance: {wbtc_balance:.8f}")
            
            # Optional: Supply WBTC to Aave
            if wbtc_balance > 0:
                print(f"\n🔄 Supplying WBTC to Aave...")
                supply_result = agent.aave.supply_to_aave(agent.wbtc_address, wbtc_balance)
                if supply_result:
                    print("✅ WBTC supplied to Aave successfully!")
                else:
                    print("❌ WBTC supply to Aave failed")
            
            return True
        else:
            print("❌ DAI → WBTC swap failed")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced swap failed: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main execution function"""
    print("🚀 Starting Enhanced DAI → WBTC Swap")
    success = enhanced_dai_to_wbtc_swap()
    
    if success:
        print("\n🎉 SWAP COMPLETED SUCCESSFULLY")
    else:
        print("\n❌ SWAP FAILED")
    
    return success

if __name__ == "__main__":
    main()
