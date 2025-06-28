
#!/usr/bin/env python3
"""
Withdraw 0.006537 WETH from Aave and then use it to borrow 20 USDC
"""

import os
import time
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def main():
    """Withdraw WETH from Aave and then borrow 20 USDC"""
    print("💰 WITHDRAW WETH & BORROW 20 USDC")
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

        # Step 1: Withdraw 0.006537 WETH from Aave
        withdraw_amount = 0.006537
        print(f"\n🏦 Step 1: Withdrawing {withdraw_amount} WETH from Aave...")

        # Check if we have sufficient collateral to withdraw
        current_collateral = health_data['total_collateral_eth'] if health_data else 0
        if current_collateral < withdraw_amount:
            print(f"❌ Insufficient collateral. Available: {current_collateral:.6f} ETH, Requested: {withdraw_amount} ETH")
            return

        # Execute withdrawal using Aave integration
        try:
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
            user_address = agent.w3.to_checksum_address(agent.address)
            nonce = agent.w3.eth.get_transaction_count(user_address, 'pending')
            print(f"🔢 Using nonce: {nonce}")
            
            # Build withdrawal transaction
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
            print("⏳ Waiting for withdrawal confirmation...")
            receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print("✅ WETH withdrawal completed successfully!")
                print(f"🎉 Withdrawn {withdraw_amount} WETH from Aave")
                
                # Wait for state to update
                time.sleep(10)
                
                # Step 2: Check new ETH balance and create 20 USDC borrow position
                print(f"\n💰 Step 2: Creating 20 USDC borrow position...")
                
                # Get current ETH balance
                eth_balance = agent.w3.from_wei(agent.w3.eth.get_balance(user_address), 'ether')
                print(f"💰 Current ETH Balance: {eth_balance:.6f} ETH")
                
                # Calculate safe amount for collateral (keep some for gas)
                gas_reserve = 0.001  # 0.001 ETH for gas
                collateral_amount = eth_balance - gas_reserve
                
                if collateral_amount > 0.005:  # Minimum viable collateral
                    print(f"🏦 Using {collateral_amount:.6f} ETH as collateral for 20 USDC borrow...")
                    
                    # Estimate health factor
                    eth_price = 2500  # Approximate ETH price
                    collateral_value = collateral_amount * eth_price
                    borrow_amount = 20.0  # $20 USDC
                    ltv = 0.8  # 80% LTV for ETH
                    estimated_hf = (collateral_value * ltv) / borrow_amount
                    
                    print(f"📊 Estimated Position:")
                    print(f"   Collateral: {collateral_amount:.6f} ETH (${collateral_value:.2f})")
                    print(f"   Borrow: ${borrow_amount:.2f} USDC")
                    print(f"   Estimated Health Factor: {estimated_hf:.2f}")
                    
                    if estimated_hf > 3.0:  # Safe health factor
                        # Import position creator
                        from create_position import PositionCreator
                        
                        # Create position with the withdrawn ETH
                        creator = PositionCreator()
                        
                        # Supply ETH as collateral
                        print("🔄 Supplying ETH as collateral...")
                        supply_success = creator.supply_eth_collateral(collateral_amount)
                        
                        if supply_success:
                            time.sleep(10)  # Wait for confirmation
                            
                            # Borrow 20 USDC
                            print("🔄 Borrowing 20 USDC...")
                            borrow_success = creator.borrow_usdc(20.0)
                            
                            if borrow_success:
                                print("🎉 SUCCESS: 20 USDC borrowed successfully!")
                                print("🏥 Checking final health factor...")
                                
                                # Check final position
                                final_position = creator.get_aave_position()
                                if final_position:
                                    print(f"📊 Final Position:")
                                    print(f"   Collateral: ${final_position['collateral']:.2f}")
                                    print(f"   Debt: ${final_position['debt']:.2f}")
                                    print(f"   Health Factor: {final_position['health_factor']:.2f}")
                                    
                                    if final_position['health_factor'] > 3.0:
                                        print("✅ Health factor is safe!")
                                    else:
                                        print("⚠️ Health factor is low")
                            else:
                                print("❌ USDC borrow failed")
                        else:
                            print("❌ ETH supply failed")
                    else:
                        print("❌ Estimated health factor too low for safe borrowing")
                        print(f"💡 Need more ETH for safe 20 USDC borrow")
                else:
                    print("❌ Insufficient ETH balance after withdrawal")
                    
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
