
#!/usr/bin/env python3
"""
Withdraw WETH from Aave V3 Script
Execute: python withdraw_weth.py
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Withdraw 0.005981 WETH from Aave V3"""
    print("💰 WETH Withdrawal from Aave V3")
    print("=" * 50)

    # Get network mode from environment
    network_mode = os.getenv('NETWORK_MODE', 'mainnet')
    print(f"🌐 Network Mode: {network_mode}")

    if network_mode == 'mainnet':
        print("🚨 MAINNET MODE - Using real funds!")

    try:
        print("🤖 Initializing DeFi agent...")
        agent = ArbitrumTestnetAgent(network_mode)

        print("📍 Wallet:", agent.address)
        print("🌐 Chain ID:", agent.w3.eth.chain_id)

        # Initialize Aave integration if not already done
        if not hasattr(agent, 'aave'):
            from aave_integration import AaveArbitrumIntegration
            agent.aave = AaveArbitrumIntegration(agent.w3, agent.account)

        # Check current Aave position first
        print("\n📊 Checking current Aave position...")
        
        # Get current health factor and position data
        if hasattr(agent, 'health_monitor'):
            health_data = agent.health_monitor.get_current_health_factor()
            if health_data:
                print(f"🏥 Current Health Factor: {health_data['health_factor']:.4f}")
                print(f"💰 Total Collateral: {health_data['total_collateral_eth']:.6f} ETH")
                print(f"💸 Total Debt: {health_data['total_debt_eth']:.6f} ETH")
        
        # Withdraw amount
        withdraw_amount = 0.005981
        print(f"\n🏦 Withdrawing {withdraw_amount} WETH from Aave V3...")

        # Check if we have sufficient collateral to withdraw
        current_collateral = health_data['total_collateral_eth'] if health_data else 0
        if current_collateral < withdraw_amount:
            print(f"❌ Insufficient collateral. Available: {current_collateral:.6f} ETH, Requested: {withdraw_amount} ETH")
            return

        # Safety check: ensure withdrawal won't put health factor below 1.5
        if health_data and health_data['total_debt_eth'] > 0:
            # Estimate health factor after withdrawal
            remaining_collateral = current_collateral - withdraw_amount
            estimated_hf = (remaining_collateral * 2500 * 0.8) / (health_data['total_debt_eth'] * 2500)  # Rough estimation
            
            if estimated_hf < 1.5:
                print(f"⚠️ WARNING: Withdrawal may reduce health factor to {estimated_hf:.2f}")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Withdrawal cancelled for safety")
                    return

        # Execute withdrawal using Aave integration
        try:
            # Build withdrawal transaction
            user_address = agent.w3.to_checksum_address(agent.address)
            
            # Aave withdraw ABI
            withdraw_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "asset", "type": "address"},
                        {"internalType": "uint256", "name": "amount", "type": "uint256"},
                        {"internalType": "address", "name": "to", "type": "address"}
                    ],
                    "name": "withdraw",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]
            
            # Create pool contract
            pool_contract = agent.w3.eth.contract(
                address=agent.aave.pool_address,
                abi=withdraw_abi
            )
            
            # Convert amount to wei
            amount_wei = agent.w3.to_wei(withdraw_amount, 'ether')
            
            # Get current nonce
            nonce = agent.w3.eth.get_transaction_count(user_address, 'pending')
            print(f"🔢 Using nonce: {nonce}")
            
            # Build transaction
            transaction = pool_contract.functions.withdraw(
                agent.aave.weth_address,  # WETH asset address
                amount_wei,               # Amount in wei
                user_address              # Recipient address
            ).build_transaction({
                'chainId': agent.w3.eth.chain_id,
                'gas': 300000,
                'gasPrice': int(agent.w3.eth.gas_price * 1.1),  # 10% higher gas price
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_txn = agent.w3.eth.account.sign_transaction(transaction, agent.account.key)
            tx_hash = agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            tx_hash_hex = tx_hash.hex()
            print(f"✅ Withdrawal transaction sent: {tx_hash_hex}")
            
            # Show explorer link
            if agent.w3.eth.chain_id == 42161:
                explorer_url = f"https://arbiscan.io/tx/{tx_hash_hex}"
            else:
                explorer_url = f"https://sepolia.arbiscan.io/tx/{tx_hash_hex}"
            
            print(f"📊 View on explorer: {explorer_url}")
            
            # Wait for confirmation
            print("⏳ Waiting for transaction confirmation...")
            receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print("✅ WETH withdrawal completed successfully!")
                print(f"🎉 Withdrawn {withdraw_amount} WETH from Aave V3")
                
                # Check updated position
                time.sleep(5)  # Wait for state to update
                if hasattr(agent, 'health_monitor'):
                    updated_health = agent.health_monitor.get_current_health_factor()
                    if updated_health:
                        print(f"🏥 Updated Health Factor: {updated_health['health_factor']:.4f}")
                        print(f"💰 Remaining Collateral: {updated_health['total_collateral_eth']:.6f} ETH")
            else:
                print("❌ Withdrawal transaction failed")
                
        except Exception as e:
            print(f"❌ Withdrawal failed: {e}")
            print("💡 Check your collateral balance and ensure sufficient gas")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Ensure your wallet is properly configured")

if __name__ == "__main__":
    main()
