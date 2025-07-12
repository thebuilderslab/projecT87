
#!/usr/bin/env python3
"""
Wallet Validation Script - Diagnose Agent vs Dashboard Wallet Discrepancy
"""

import os
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def validate_agent_wallet():
    """Validate that the agent is using the correct wallet and can access Aave data"""
    print("🔍 AGENT WALLET VALIDATION")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        print(f"🔑 Agent Wallet Address: {agent.address}")
        print(f"🌐 Network: {agent.network_mode} (Chain ID: {agent.chain_id})")
        print(f"🔗 RPC URL: {agent.rpc_url}")
        print(f"🏦 Aave Pool: {agent.aave_pool_address}")
        
        # Check wallet balance
        eth_balance = agent.get_eth_balance()
        print(f"💰 ETH Balance: {eth_balance:.6f} ETH")
        
        # Test direct Aave contract call
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
        
        print(f"✅ Aave Query Success:")
        print(f"   Total Collateral: {total_collateral_eth:.8f} ETH")
        print(f"   Total Debt: {total_debt_eth:.8f} ETH")
        print(f"   Health Factor: {health_factor:.4f}")
        
        # Convert to USD
        eth_price = 3000  # Approximate
        collateral_usd = total_collateral_eth * eth_price
        debt_usd = total_debt_eth * eth_price
        
        print(f"   Collateral USD: ${collateral_usd:,.2f}")
        print(f"   Debt USD: ${debt_usd:,.2f}")
        
        # Compare with expected dashboard values
        print(f"\n📊 COMPARISON:")
        expected_collateral = 174.0  # From dashboard logs
        if abs(collateral_usd - expected_collateral) < 10:
            print(f"✅ MATCH: Agent sees ~${collateral_usd:,.2f}, dashboard shows ~${expected_collateral:,.2f}")
        else:
            print(f"❌ MISMATCH: Agent sees ${collateral_usd:,.2f}, but dashboard shows ~${expected_collateral:,.2f}")
            print(f"🔧 This suggests either:")
            print(f"   1. Wallet address mismatch between agent and dashboard")
            print(f"   2. RPC endpoint returning stale/incorrect data")
            print(f"   3. Contract address or ABI issue")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    validate_agent_wallet()
