
#!/usr/bin/env python3
"""
Wallet Validation Script - Diagnose Agent vs Dashboard Wallet Discrepancy
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def validate_agent_wallet():
    """Validate that the agent is using the correct wallet and can access Aave data"""
    print("🔍 AGENT WALLET VALIDATION & DASHBOARD COMPARISON")
    print("=" * 60)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        print(f"🔑 Agent Wallet Address: {agent.address}")
        print(f"🌐 Network: {agent.network_mode} (Chain ID: {agent.chain_id})")
        
        # Expected dashboard wallet address (from your logs)
        expected_wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        print(f"📊 Expected Dashboard Wallet: {expected_wallet}")
        
        # Check if addresses match
        if agent.address.lower() == expected_wallet.lower():
            print(f"✅ WALLET MATCH: Agent and dashboard use same address!")
        else:
            print(f"❌ WALLET MISMATCH:")
            print(f"   Agent wallet:    {agent.address}")
            print(f"   Dashboard wallet: {expected_wallet}")
            print(f"🔧 SOLUTION: Update PRIVATE_KEY to match dashboard wallet")
            return False
        
        # Test direct Aave contract call with agent wallet
        print(f"\n🔍 TESTING AAVE CONTRACT ACCESS:")
        
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralETH", "type": "uint256"},
                {"name": "totalDebtETH", "type": "uint256"},
                {"name": "availableBorrowsETH", "type": "uint256"},
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
        
        total_collateral_eth = account_data[0] / (10**18)
        total_debt_eth = account_data[1] / (10**18)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        # Convert to USD (approximate)
        eth_price = 2960  # Current approximate ETH price
        collateral_usd = total_collateral_eth * eth_price
        debt_usd = total_debt_eth * eth_price
        
        print(f"✅ Agent Aave Query Results:")
        print(f"   Total Collateral: {total_collateral_eth:.8f} ETH (${collateral_usd:,.2f})")
        print(f"   Total Debt: {total_debt_eth:.8f} ETH (${debt_usd:,.2f})")
        print(f"   Health Factor: {health_factor:.4f}")
        
        # Compare with dashboard values (from your logs)
        expected_collateral_usd = 174.0  # From dashboard
        expected_debt_usd = 20.0         # From dashboard
        
        print(f"\n📊 DASHBOARD vs AGENT COMPARISON:")
        print(f"   Dashboard Collateral: ~${expected_collateral_usd:,.2f}")
        print(f"   Agent Collateral:     ${collateral_usd:,.2f}")
        print(f"   Dashboard Debt:       ~${expected_debt_usd:,.2f}")
        print(f"   Agent Debt:           ${debt_usd:,.2f}")
        
        if abs(collateral_usd - expected_collateral_usd) < 10:
            print(f"✅ PERFECT MATCH: Agent sees same position as dashboard!")
            print(f"🚀 TRIGGER STATUS: Collateral ${collateral_usd:,.2f} - Growth needed: ${12 - collateral_usd:,.2f}")
            
            # If collateral is above $12, the trigger should activate
            if collateral_usd >= 12:
                print(f"🎯 TRIGGER READY: Add ${12:.2f} more to activate autonomous sequence!")
            
        else:
            print(f"❌ DATA MISMATCH:")
            print(f"   Difference: ${abs(collateral_usd - expected_collateral_usd):,.2f}")
            print(f"🔧 This suggests:")
            print(f"   1. Different wallet addresses")
            print(f"   2. RPC endpoint data lag")
            print(f"   3. Contract address issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        print(f"🔧 Try running with different RPC endpoint")
        return False

if __name__ == "__main__":
    validate_agent_wallet()
