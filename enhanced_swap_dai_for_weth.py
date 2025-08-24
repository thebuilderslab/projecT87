
#!/usr/bin/env python3
"""
Enhanced DAI → WETH Swap System with Full Validation
DAI COMPLIANCE ENFORCED: Only DAI → WETH swaps permitted
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def enhanced_dai_to_weth_swap():
    """Execute enhanced DAI → WETH swap with comprehensive validation"""
    try:
        print("🔄 ENHANCED DAI → WETH SWAP SYSTEM")
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
        swap_amount = min(dai_balance * 0.3, 3.0)  # 30% of balance or max $3
        print(f"🎯 Swap Amount: ${swap_amount:.2f} DAI → WETH")
        
        # Pre-swap validation
        print("\n🔍 Pre-swap validation...")
        
        # Validate contracts
        dai_contract = agent.w3.eth.contract(
            address=agent.dai_address,
            abi=agent.uniswap.erc20_abi
        )
        
        weth_contract = agent.w3.eth.contract(
            address=agent.weth_address,
            abi=agent.uniswap.erc20_abi
        )
        
        try:
            dai_symbol = dai_contract.functions.symbol().call()
            weth_symbol = weth_contract.functions.symbol().call()
            print(f"   ✅ Contracts validated: {dai_symbol} → {weth_symbol}")
        except Exception as e:
            print(f"   ❌ Contract validation failed: {e}")
            return False
        
        # Execute swap
        print(f"\n🔄 Executing DAI → WETH swap...")
        
        swap_result = agent.uniswap.swap_tokens(
            agent.dai_address,     # DAI in
            agent.weth_address,    # WETH out
            swap_amount,           # Amount
            500                    # 0.05% fee tier
        )
        
        if swap_result:
            print("✅ DAI → WETH swap successful!")
            print(f"   Transaction hash: {swap_result}")
            
            # Wait for confirmation
            time.sleep(10)
            
            # Check WETH balance
            weth_balance = agent.aave.get_token_balance(agent.weth_address)
            print(f"💰 New WETH Balance: {weth_balance:.6f}")
            
            # Optional: Supply WETH to Aave
            if weth_balance > 0:
                print(f"\n🔄 Supplying WETH to Aave...")
                supply_result = agent.aave.supply_to_aave(agent.weth_address, weth_balance)
                if supply_result:
                    print("✅ WETH supplied to Aave successfully!")
                else:
                    print("❌ WETH supply to Aave failed")
            
            return True
        else:
            print("❌ DAI → WETH swap failed")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced swap failed: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main execution function"""
    print("🚀 Starting Enhanced DAI → WETH Swap")
    success = enhanced_dai_to_weth_swap()
    
    if success:
        print("\n🎉 SWAP COMPLETED SUCCESSFULLY")
    else:
        print("\n❌ SWAP FAILED")
    
    return success

if __name__ == "__main__":
    main()
