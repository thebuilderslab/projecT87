
#!/usr/bin/env python3
"""
Borrow Failure Diagnostic Tool
Analyzes why borrow transactions are reverting
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3
import json

def diagnose_borrow_failure():
    print("🔍 BORROW FAILURE DIAGNOSTIC")
    print("=" * 40)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: {agent.network_mode}")
        print(f"⛓️ Chain ID: {agent.w3.eth.chain_id}")
        
        # Get detailed Aave account data
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(
            address=agent.aave_pool_address,
            abi=pool_abi
        )
        
        account_data = pool_contract.functions.getUserAccountData(agent.address).call()
        
        collateral_usd = account_data[0] / (10**8)
        debt_usd = account_data[1] / (10**8)
        available_borrows_usd = account_data[2] / (10**8)
        liquidation_threshold = account_data[3] / 100
        ltv = account_data[4] / 100
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"\n📊 AAVE ACCOUNT ANALYSIS:")
        print(f"   Total Collateral: ${collateral_usd:,.2f}")
        print(f"   Total Debt: ${debt_usd:,.2f}")
        print(f"   Available Borrows: ${available_borrows_usd:,.2f}")
        print(f"   Liquidation Threshold: {liquidation_threshold:.1f}%")
        print(f"   LTV: {ltv:.1f}%")
        print(f"   Health Factor: {health_factor:.4f}")
        
        # Analyze borrowing constraints
        print(f"\n🔍 BORROWING CONSTRAINT ANALYSIS:")
        
        if collateral_usd == 0:
            print(f"❌ CRITICAL: No collateral supplied")
            print(f"   Solution: Supply collateral tokens first")
            return False
        
        if health_factor < 1.1:
            print(f"❌ CRITICAL: Health factor too low ({health_factor:.4f})")
            print(f"   Solution: Add more collateral or repay debt")
            return False
        
        if available_borrows_usd < 1.0:
            print(f"❌ CRITICAL: Insufficient borrowing capacity (${available_borrows_usd:.2f})")
            print(f"   Solution: Add more collateral")
            return False
        
        # Test small borrow simulation
        test_amounts = [1.0, 5.0, 10.0]
        
        print(f"\n🧪 BORROW SIMULATION TESTS:")
        for test_amount in test_amounts:
            if test_amount > available_borrows_usd:
                continue
                
            # Calculate post-borrow health factor
            new_debt = debt_usd + test_amount
            new_hf = (collateral_usd * liquidation_threshold / 100) / new_debt if new_debt > 0 else float('inf')
            
            status = "✅ SAFE" if new_hf > 1.1 else "❌ UNSAFE"
            print(f"   ${test_amount:.1f} borrow: New HF = {new_hf:.4f} {status}")
            
            if new_hf > 1.2:
                print(f"✅ RECOMMENDATION: Try borrowing ${test_amount:.1f} USDC")
                return True
        
        print(f"\n💡 GENERAL RECOMMENDATIONS:")
        print(f"   1. Start with very small amounts (${min(available_borrows_usd * 0.1, 1.0):.1f})")
        print(f"   2. Ensure health factor stays above 1.5")
        print(f"   3. Monitor gas prices and network congestion")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return False

if __name__ == "__main__":
    diagnose_borrow_failure()
