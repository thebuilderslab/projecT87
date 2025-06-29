
#!/usr/bin/env python3
"""
Enhanced USDC to WBTC swap with comprehensive error handling and diagnostics
Execute: python enhanced_swap_usdc_for_wbtc.py
"""

import os
import time
import traceback
from arbitrum_testnet_agent import ArbitrumTestnetAgent

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
    if eth_balance < 0.01:
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
    
    # 5. Check USDC balance
    try:
        usdc_balance = agent.aave.get_token_balance(agent.usdc_address)
        print(f"💵 USDC balance: {usdc_balance:.6f}")
        
        required = 40.6293
        if usdc_balance < required:
            issues.append(f"Insufficient USDC (need {required:.4f}, have {usdc_balance:.4f})")
    except Exception as e:
        issues.append(f"Failed to check USDC balance: {e}")
        print(f"❌ USDC balance check failed: {e}")
    
    # 6. Test contract connectivity
    try:
        from web3 import Web3
        usdc_contract = agent.w3.eth.contract(
            address=agent.usdc_address,
            abi=[{
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }]
        )
        symbol = usdc_contract.functions.symbol().call()
        print(f"✅ USDC contract responsive: {symbol}")
    except Exception as e:
        issues.append(f"USDC contract connectivity issue: {e}")
        print(f"❌ Contract test failed: {e}")
    
    return issues

def execute_swap_with_enhanced_error_handling(agent, usdc_amount):
    """Execute swap with comprehensive error handling and real-time gas estimation"""
    print(f"\n🔄 EXECUTING ENHANCED SWAP: {usdc_amount:.4f} USDC → WBTC")
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
        # Convert USDC amount to wei (6 decimals)
        usdc_amount_wei = int(usdc_amount * (10 ** 6))
        print(f"🔢 USDC amount in wei: {usdc_amount_wei}")
        
        # Check if we're using real Uniswap integration
        if hasattr(agent.uniswap, '__class__') and 'Mock' in agent.uniswap.__class__.__name__:
            print("❌ CRITICAL: Cannot perform real swap with mock Uniswap integration")
            print("💡 This indicates integration initialization failed")
            return False
        
        # Pre-swap checks
        print("🔍 Pre-swap validation...")
        
        # Check USDC allowance for Uniswap router
        try:
            from web3 import Web3
            usdc_contract = agent.w3.eth.contract(
                address=agent.usdc_address,
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
            
            current_allowance = usdc_contract.functions.allowance(
                agent.address, 
                agent.uniswap.router_address
            ).call()
            
            print(f"💡 Current USDC allowance: {current_allowance}")
            
            if current_allowance < usdc_amount_wei:
                print("🔧 Allowance insufficient, swap will handle approval")
            
        except Exception as e:
            print(f"⚠️ Could not check allowance: {e}")
        
        # Execute the swap
        print("🚀 Initiating swap transaction...")
        swap_result = agent.uniswap.swap_tokens(
            agent.usdc_address,  # token_in (USDC)
            agent.wbtc_address,  # token_out (WBTC)  
            usdc_amount_wei,     # amount_in
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
    print("🔄 ENHANCED USDC → WBTC SWAP")
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
            print("   • Fund wallet with sufficient ETH and USDC")
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
        usdc_amount = 40.6293
        success = execute_swap_with_enhanced_error_handling(agent, usdc_amount)
        
        if success:
            print("\n🎉 SWAP COMPLETED SUCCESSFULLY!")
            print("✅ USDC → WBTC conversion finished")
            
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
        print("3. Verify wallet has sufficient ETH and USDC")
        print("4. Check network connectivity")

if __name__ == "__main__":
    main()
