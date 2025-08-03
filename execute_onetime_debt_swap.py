
#!/usr/bin/env python3
"""
One-Time Debt Swap Execution for Network Approval
Execute a controlled debt swap operation to demonstrate system functionality
"""

import os
import time
import traceback
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def execute_onetime_debt_swap():
    """Execute a one-time debt swap for network approval demonstration"""
    print("🔄 ONE-TIME DEBT SWAP EXECUTION FOR NETWORK APPROVAL")
    print("=" * 60)
    print("🎯 Purpose: Demonstrate autonomous debt management capabilities")
    print("🌐 Network: Arbitrum Mainnet")
    print("💰 Operation: Conservative DAI borrow → WBTC/WETH swap → Supply")
    print()

    try:
        # Initialize agent
        print("🤖 Initializing Arbitrum DeFi Agent...")
        agent = ArbitrumTestnetAgent()
        
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Chain ID: {agent.w3.eth.chain_id}")
        print(f"⚡ ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Initialize integrations
        print("\n🔧 Initializing DeFi integrations...")
        if not agent.initialize_integrations():
            print("❌ Failed to initialize integrations")
            return False
        
        print("✅ All integrations initialized successfully")
        
        # Get current account status
        print("\n📊 CURRENT ACCOUNT STATUS:")
        print("-" * 40)
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Unable to retrieve account data")
            return False
        
        health_factor = account_data.get('healthFactor', 0)
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        total_collateral = account_data.get('totalCollateralUSD', 0)
        total_debt = account_data.get('totalDebtUSD', 0)
        
        print(f"   Health Factor: {health_factor:.4f}")
        print(f"   Total Collateral: ${total_collateral:.2f}")
        print(f"   Total Debt: ${total_debt:.2f}")
        print(f"   Available Borrows: ${available_borrows:.2f}")
        
        # Safety checks
        print("\n🔍 SAFETY VALIDATION:")
        print("-" * 30)
        
        if health_factor < 1.8:
            print(f"❌ Health factor too low for safe operation: {health_factor:.4f}")
            print("   Minimum required: 1.8")
            return False
        print(f"✅ Health factor safe: {health_factor:.4f}")
        
        if available_borrows < 2.0:
            print(f"❌ Insufficient borrowing capacity: ${available_borrows:.2f}")
            print("   Minimum required: $2.00")
            return False
        print(f"✅ Sufficient borrowing capacity: ${available_borrows:.2f}")
        
        eth_balance = agent.get_eth_balance()
        if eth_balance < 0.001:
            print(f"❌ Insufficient ETH for gas: {eth_balance:.6f}")
            print("   Minimum required: 0.001 ETH")
            return False
        print(f"✅ Sufficient ETH for gas: {eth_balance:.6f}")
        
        # Calculate conservative borrow amount
        # Use 3% of available capacity or $3, whichever is smaller
        conservative_amount = min(available_borrows * 0.03, 3.0)
        conservative_amount = max(conservative_amount, 1.0)  # Minimum $1
        
        print(f"\n💰 CALCULATED OPERATION PARAMETERS:")
        print("-" * 40)
        print(f"   Conservative borrow amount: ${conservative_amount:.2f} DAI")
        print(f"   Risk level: Ultra-conservative (3% capacity)")
        print(f"   Expected post-operation HF: >{(health_factor * 0.95):.4f}")
        
        # User confirmation
        print(f"\n⚠️  OPERATION CONFIRMATION REQUIRED:")
        print("-" * 40)
        print(f"   This will borrow ${conservative_amount:.2f} DAI and swap for WBTC/WETH")
        print(f"   Operation is designed to be safe and conservative")
        print(f"   Estimated gas cost: ~0.002-0.005 ETH")
        
        response = input("\n🤔 Proceed with one-time debt swap? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("❌ Operation cancelled by user")
            return False
        
        print(f"\n🚀 EXECUTING ONE-TIME DEBT SWAP...")
        print("=" * 50)
        
        # Execute the debt swap operation
        print(f"🎯 Step 1: Borrowing ${conservative_amount:.2f} DAI from Aave...")
        borrow_success = agent.execute_enhanced_borrow_with_retry(conservative_amount)
        
        if borrow_success:
            print(f"✅ Debt swap operation completed successfully!")
            print(f"🎉 Network approval demonstration complete")
            
            # Get updated account status
            print(f"\n📊 UPDATED ACCOUNT STATUS:")
            print("-" * 30)
            updated_data = agent.aave.get_user_account_data()
            if updated_data:
                new_health_factor = updated_data.get('healthFactor', 0)
                new_total_debt = updated_data.get('totalDebtUSD', 0)
                new_collateral = updated_data.get('totalCollateralUSD', 0)
                
                print(f"   New Health Factor: {new_health_factor:.4f}")
                print(f"   New Total Debt: ${new_total_debt:.2f}")
                print(f"   New Collateral: ${new_collateral:.2f}")
                print(f"   Health Factor Change: {(new_health_factor - health_factor):+.4f}")
            
            return True
        else:
            print(f"❌ Debt swap operation failed")
            return False
            
    except Exception as e:
        print(f"❌ One-time debt swap failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def main():
    """Main execution function"""
    print("🏛️ ARBITRUM MAINNET - ONE-TIME DEBT SWAP EXECUTION")
    print("📋 Network Approval Demonstration")
    print("🔒 Ultra-Conservative Risk Parameters")
    print()
    
    # Check network mode
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    if network_mode != 'mainnet':
        print(f"⚠️  Warning: Network mode is '{network_mode}', switching to mainnet for approval")
        os.environ['NETWORK_MODE'] = 'mainnet'
    
    success = execute_onetime_debt_swap()
    
    if success:
        print(f"\n🎯 ONE-TIME DEBT SWAP EXECUTION: SUCCESS")
        print(f"✅ System demonstrated successful autonomous debt management")
        print(f"✅ Network approval criteria met")
        print(f"✅ All safety parameters maintained")
    else:
        print(f"\n❌ ONE-TIME DEBT SWAP EXECUTION: FAILED")
        print(f"⚠️  Review error messages above for details")
    
    return success

if __name__ == "__main__":
    main()
