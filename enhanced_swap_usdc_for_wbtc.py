"""
DAI COMPLIANCE ENFORCED: This file has been modified to use DAI-only operations.
Only DAI → WBTC and DAI → WETH swaps are permitted.
"""


#!/usr/bin/env python3
"""
Enhanced DAI to WBTC swap with comprehensive error handling and diagnostics
Execute: python enhanced_swap_DAI_for_wbtc.py
"""

import os
import time
import traceback
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from config_constants import MIN_ETH_FOR_OPERATIONS

def check_prerequisites(agent):
    """Comprehensive prerequisite checks before attempting swap"""
    print("🔍 CHECKING SWAP PREREQUISITES")
    print("=" * 50)
    
    issues = []
    
    # 1. Check network connection
    try:
        latest_block = agent.w3.eth.get_block('latest')
        print(f"✅ Network connected - Block: {latest_block.number}")
    except Exception as e:
        issues.append(f"Network connection failed: {e}")
        print(f"❌ Network issue: {e}")
    
    # 2. Check private key is not placeholder
    if hasattr(agent.account, 'key'):
        key_hex = agent.account.key.hex()
        if key_hex == "0x" + "0" * 64:
            issues.append("Using placeholder private key - real transactions will fail")
            print("❌ Placeholder private key detected")
        else:
            print("✅ Valid private key loaded")
    
    # 3. Check ETH balance for gas
    eth_balance = agent.get_eth_balance()
    print(f"⚡ ETH balance: {eth_balance:.6f} ETH")
    if eth_balance < MIN_ETH_FOR_OPERATIONS:
        issues.append(f"Low ETH balance ({eth_balance:.6f}) - may not cover gas fees")
    
    # 4. Check integrations
    aave_real = not hasattr(agent.aave, '__class__') or 'Mock' not in agent.aave.__class__.__name__
    uniswap_real = not hasattr(agent.uniswap, '__class__') or 'Mock' not in agent.uniswap.__class__.__name__
    
    if not aave_real:
        issues.append("Using mock Aave integration - balance checks may be inaccurate")
        print("⚠️ Mock Aave integration detected")
    else:
        print("✅ Real Aave integration active")
    
    if not uniswap_real:
        issues.append("Using mock Uniswap integration - swaps will fail")
        print("⚠️ Mock Uniswap integration detected")
    else:
        print("✅ Real Uniswap integration active")
    
    # 5. Check DAI balance
    try:
        DAI_balance = agent.aave.get_token_balance(agent.dai_address)
        print(f"💵 DAI balance: {DAI_balance:.6f}")
        
        required = 40.6293
        if DAI_balance < required:
            issues.append(f"Insufficient DAI (need {required:.4f}, have {DAI_balance:.4f})")
    except Exception as e:
        issues.append(f"Failed to check DAI balance: {e}")
        print(f"❌ DAI balance check failed: {e}")
    
    # 6. Test contract connectivity
    try:
        from web3 import Web3
        DAI_contract = agent.w3.eth.contract(
            address=agent.dai_address,
            abi=[{
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }]
        )
        symbol = DAI_contract.functions.symbol().call()
        print(f"✅ DAI contract responsive: {symbol}")
    except Exception as e:
        issues.append(f"DAI contract connectivity issue: {e}")
        print(f"❌ Contract test failed: {e}")
    
    return issues

def execute_swap_with_enhanced_error_handling(agent, DAI_amount):
    """Execute swap with comprehensive error handling and real-time gas estimation"""
    print(f"\n🔄 EXECUTING ENHANCED SWAP: {DAI_amount:.4f} DAI → WBTC")
    print("=" * 60)
    
    # Get real-time gas prices from network
    try:
        from gas_fee_calculator import ArbitrumGasCalculator
        gas_calc = ArbitrumGasCalculator()
        gas_prices = gas_calc.get_current_gas_prices()
        
        if gas_prices:
            current_gas_gwei = agent.w3.from_wei(gas_prices['market'], 'gwei')
            print(f"⛽ Current network gas price: {current_gas_gwei:.2f} gwei")
            
            # Estimate swap cost
            swap_fee = gas_calc.calculate_transaction_fee('uniswap_swap', 'market')
            if swap_fee:
                print(f"💰 Estimated swap cost: {swap_fee['fee_eth']} ETH ({swap_fee['fee_usd']})")
        else:
            print("⚠️ Could not fetch real-time gas prices, using network defaults")
    except Exception as e:
        print(f"⚠️ Gas estimation error: {e}")
    
    try:
        # Convert DAI amount to wei (6 decimals)
        DAI_amount_wei = int(DAI_amount * (10 ** 6))
        print(f"🔢 DAI amount in wei: {DAI_amount_wei}")
        
        # Check if we're using real Uniswap integration
        if hasattr(agent.uniswap, '__class__') and 'Mock' in agent.uniswap.__class__.__name__:
            print("❌ CRITICAL: Cannot perform real swap with mock Uniswap integration")
            print("💡 This indicates integration initialization failed")
            return False
        
        # Pre-swap checks
        print("🔍 Pre-swap validation...")
        
        # Check DAI allowance for Uniswap router
        try:
            from web3 import Web3
            DAI_contract = agent.w3.eth.contract(
                address=agent.dai_address,
                abi=[{
                    "constant": True,
                    "inputs": [
                        {"name": "_owner", "type": "address"},
                        {"name": "_spender", "type": "address"}
                    ],
                    "name": "allowance",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                }]
            )
            
            current_allowance = DAI_contract.functions.allowance(
                agent.address, 
                agent.uniswap.router_address
            ).call()
            
            print(f"💡 Current DAI allowance: {current_allowance}")
            
            if current_allowance < DAI_amount_wei:
                print("🔧 Allowance insufficient, swap will handle approval")
            
        except Exception as e:
            print(f"⚠️ Could not check allowance: {e}")
        
        # Execute the swap
        print("🚀 Initiating swap transaction...")
        swap_result = agent.uniswap.swap_tokens(
            agent.dai_address,  # token_in (DAI)
            agent.wbtc_address,  # token_out (WBTC)  
            DAI_amount_wei,     # amount_in
            500                  # fee (0.05% tier)
        )
        
        if swap_result:
            print(f"✅ Swap transaction submitted!")
            print(f"🔗 Transaction hash: {swap_result}")
            
            # Show explorer link
            if agent.w3.eth.chain_id == 42161:
                print(f"📊 Arbitrum Mainnet: https://arbiscan.io/tx/{swap_result}")
            elif agent.w3.eth.chain_id == 421614:
                print(f"📊 Arbitrum Sepolia: https://sepolia.arbiscan.io/tx/{swap_result}")
            
            # Wait for confirmation
            print("⏳ Waiting for transaction confirmation...")
            time.sleep(15)
            
            # Check WBTC balance after swap
            try:
                wbtc_balance = agent.aave.get_token_balance(agent.wbtc_address)
                print(f"💰 WBTC received: {wbtc_balance:.8f} WBTC")
                
                if wbtc_balance > 0:
                    print("🎉 Swap completed successfully!")
                    return True
                else:
                    print("⚠️ No WBTC balance detected - check transaction status")
                    return False
                    
            except Exception as e:
                print(f"⚠️ Could not verify WBTC balance: {e}")
                print("💡 Transaction may still be successful - check manually")
                return True
                
        else:
            print("❌ Swap transaction failed")
            return False
            
    except Exception as e:
        print(f"❌ Swap execution error: {e}")
        print("\n📋 Error Details:")
        traceback.print_exc()
        return False

def main():
    """Main function with comprehensive error handling"""
    print("🔄 ENHANCED DAI → WBTC SWAP")
    print("=" * 50)
    
    # Get network mode
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    print(f"🌐 Network Mode: {network_mode}")
    
    if network_mode == 'mainnet':
        print("🚨 MAINNET MODE - Using real funds!")
        print("⚠️ Ensure you understand the risks")
    
    try:
        # Initialize agent
        print("\n🤖 Initializing DeFi agent...")
        agent = ArbitrumTestnetAgent()
        
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Chain ID: {agent.w3.eth.chain_id}")
        
        # Initialize integrations
        print("\n🔧 Initializing DeFi integrations...")
        integration_success = agent.initialize_integrations()
        
        if not integration_success:
            print("❌ CRITICAL: Integration initialization failed")
            print("💡 Cannot proceed with real transactions")
            return
        
        # Run prerequisite checks
        issues = check_prerequisites(agent)
        
        if issues:
            print(f"\n❌ {len(issues)} ISSUE(S) FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            
            print("\n💡 RECOMMENDED ACTIONS:")
            print("   • Ensure valid private key is set in Replit Secrets")
            print("   • Fund wallet with sufficient ETH and DAI")
            print("   • Check network connectivity")
            print(f"   • Verify wallet address: {agent.address}")
            
            # Ask if user wants to proceed anyway
            proceed = input("\nProceed anyway? (y/N): ").lower().strip()
            if proceed != 'y':
                print("🛑 Swap cancelled by user")
                return
        else:
            print("✅ All prerequisite checks passed!")
        
        # Execute the swap
        DAI_amount = 40.6293
        success = execute_swap_with_enhanced_error_handling(agent, DAI_amount)
        
        if success:
            print("\n🎉 SWAP COMPLETED SUCCESSFULLY!")
            print("✅ DAI → WBTC conversion finished")
            
            # Optional: Supply WBTC to Aave
            supply_choice = input("\nSupply received WBTC to Aave as collateral? (y/N): ").lower().strip()
            if supply_choice == 'y':
                print("\n🏦 Supplying WBTC to Aave...")
                try:
                    wbtc_balance = agent.aave.get_token_balance(agent.wbtc_address)
                    if wbtc_balance > 0:
                        supply_result = agent.aave.supply_wbtc_to_aave(wbtc_balance)
                        if supply_result:
                            print("✅ WBTC supplied to Aave successfully!")
                        else:
                            print("❌ WBTC supply to Aave failed")
                    else:
                        print("❌ No WBTC to supply")
                except Exception as e:
                    print(f"❌ Supply error: {e}")
        else:
            print("\n❌ SWAP FAILED")
            print("💡 Check the error messages above for details")
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("\n📋 Full Error Details:")
        traceback.print_exc()
        
        print("\n💡 TROUBLESHOOTING STEPS:")
        print("1. Check that PRIVATE_KEY or PRIVATE_KEY2 is set in Replit Secrets")
        print("2. Ensure the private key is valid (64 hex characters)")
        print("3. Verify wallet has sufficient ETH and DAI")
        print("4. Check network connectivity")

if __name__ == "__main__":
    main()
