
#!/usr/bin/env python3
"""
Transaction Revert Diagnostic Tool
Analyzes specific reasons why borrow transactions are reverting
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3
import json

def diagnose_recent_reverts():
    """Analyze recent reverted transactions"""
    print("🔍 TRANSACTION REVERT DIAGNOSTIC")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        
        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: {agent.network_mode}")
        print(f"⛓️ Chain ID: {agent.w3.eth.chain_id}")
        
        # Get recent transactions for this address
        latest_block = agent.w3.eth.block_number
        print(f"📊 Latest block: {latest_block}")
        
        # Analyze the failing transaction hashes from logs
        failing_txs = [
            "0x37e01d19ee4b41336a846dc1079bd75ea53730a1d35bb5f4f26363fb423e43f0",
            "0xb56e516ddf8160cc316d538802ef46247c4e61a5da5ff2b5d8fb5feda1597587", 
            "0x079e4c9f9f23a7b8e85a59ff258a31d855b6336e71caab81a2ff0f935205ceee"
        ]
        
        for tx_hash in failing_txs:
            try:
                print(f"\n🔍 Analyzing transaction: {tx_hash}")
                
                # Get transaction details
                tx = agent.w3.eth.get_transaction(tx_hash)
                receipt = agent.w3.eth.get_transaction_receipt(tx_hash)
                
                print(f"   Status: {'✅ Success' if receipt.status == 1 else '❌ Reverted'}")
                print(f"   Gas used: {receipt.gasUsed:,}")
                print(f"   Gas limit: {tx.gas:,}")
                print(f"   Gas price: {tx.gasPrice:,} wei ({agent.w3.from_wei(tx.gasPrice, 'gwei'):.2f} gwei)")
                
                if receipt.status == 0:
                    # Try to get revert reason
                    try:
                        # Simulate the transaction to get revert reason
                        agent.w3.eth.call({
                            'to': tx['to'],
                            'data': tx['input'], 
                            'from': tx['from'],
                            'value': tx.get('value', 0),
                            'gas': tx['gas']
                        }, receipt.blockNumber)
                        
                    except Exception as revert_error:
                        revert_reason = str(revert_error)
                        print(f"🎯 REVERT REASON: {revert_reason}")
                        
                        # Specific analysis
                        if "insufficient collateral" in revert_reason.lower():
                            print(f"💡 ISSUE: Insufficient collateral for borrow")
                            print(f"   SOLUTION: Deposit more collateral or reduce borrow amount")
                        elif "health factor" in revert_reason.lower():
                            print(f"💡 ISSUE: Health factor would be too low")
                            print(f"   SOLUTION: Reduce borrow amount to maintain safe HF")
                        elif "borrowing not enabled" in revert_reason.lower():
                            print(f"💡 ISSUE: Borrowing not enabled for this asset")
                            print(f"   SOLUTION: Check if asset supports borrowing")
                        elif "market not active" in revert_reason.lower():
                            print(f"💡 ISSUE: Market paused or inactive")
                            print(f"   SOLUTION: Wait for market to become active")
                        elif "stable borrowing not enabled" in revert_reason.lower():
                            print(f"💡 ISSUE: Stable rate borrowing disabled")
                            print(f"   SOLUTION: Use variable rate (interestRateMode=2)")
                        else:
                            print(f"💡 ISSUE: Unknown revert reason")
                            print(f"   SOLUTION: Check Aave protocol documentation")
                            
            except Exception as tx_error:
                print(f"   ❌ Could not analyze {tx_hash}: {tx_error}")
        
        # Check current Aave position
        print(f"\n📊 CURRENT AAVE POSITION:")
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
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"   Total Collateral: ${collateral_usd:.2f}")
        print(f"   Total Debt: ${debt_usd:.2f}")
        print(f"   Available Borrows: ${available_borrows_usd:.2f}")
        print(f"   Health Factor: {health_factor:.4f}")
        
        # Determine if position supports $10 borrow
        print(f"\n🧪 CAN BORROW $10 ANALYSIS:")
        if available_borrows_usd >= 10.0:
            print(f"✅ Available capacity supports $10 borrow")
        else:
            print(f"❌ Available capacity (${available_borrows_usd:.2f}) < $10")
            
        if health_factor > 2.0:
            print(f"✅ Health factor ({health_factor:.4f}) is safe for borrowing")
        else:
            print(f"⚠️ Health factor ({health_factor:.4f}) might be too low")
            
        # Test transaction simulation
        print(f"\n🧪 TRANSACTION SIMULATION TEST:")
        try:
            usdc_address = agent.usdc_address
            user_address = agent.address
            amount_wei = 10 * (10 ** 6)  # $10 in USDC wei
            
            pool_contract.functions.borrow(
                Web3.to_checksum_address(usdc_address),
                amount_wei,
                2,  # Variable rate
                0,  # Referral code
                Web3.to_checksum_address(user_address)
            ).call({'from': Web3.to_checksum_address(user_address)})
            
            print(f"✅ Simulation SUCCESS - $10 borrow should work!")
            
        except Exception as sim_error:
            print(f"❌ Simulation FAILED: {sim_error}")
            
            # Provide specific guidance
            if "insufficient collateral" in str(sim_error).lower():
                print(f"💡 SOLUTION: Need more collateral - current ${collateral_usd:.2f}")
            elif "health factor" in str(sim_error).lower():
                print(f"💡 SOLUTION: Borrow amount too large for HF {health_factor:.4f}")
            elif "borrowing not enabled" in str(sim_error).lower():
                print(f"💡 SOLUTION: Check if USDC borrowing is enabled")
                
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")

if __name__ == "__main__":
    diagnose_recent_reverts()
