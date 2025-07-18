
#!/usr/bin/env python3
"""
Safe Borrow Test
Conservative borrowing with enhanced validation
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3
import time

def safe_borrow_test():
    print("🧪 SAFE BORROW TEST")
    print("=" * 30)
    
    try:
        # Initialize agent and integrations
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Get current position
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
        available_borrows_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"💰 Available Borrows: ${available_borrows_usd:.2f}")
        print(f"❤️ Health Factor: {health_factor:.4f}")
        
        if health_factor < 2.0:
            print(f"⚠️ Health factor too low for safe borrowing")
            return False
        
        if available_borrows_usd < 1.0:
            print(f"⚠️ Insufficient borrowing capacity")
            return False
        
        # Use very conservative amount (5% of available)
        safe_amount = min(available_borrows_usd * 0.05, 2.0)
        print(f"\n🏦 Testing ultra-safe borrow: ${safe_amount:.2f}")
        
        # Manual borrow transaction with enhanced gas
        user_address = Web3.to_checksum_address(agent.address)
        amount_wei = int(safe_amount * (10 ** 6))  # USDC has 6 decimals
        
        print(f"💱 Amount: ${safe_amount:.2f} = {amount_wei} wei")
        
        # Get fresh gas price with higher premium
        base_gas_price = agent.w3.eth.gas_price
        gas_price = int(base_gas_price * 3.0)  # 3x premium for reliability
        gas_limit = 500000  # Higher gas limit
        
        print(f"⛽ Gas: {gas_limit:,} limit, {gas_price:,} price ({gas_price/1e9:.2f} gwei)")
        
        # Build transaction with maximum safety parameters
        nonce = agent.w3.eth.get_transaction_count(user_address, 'pending')
        
        transaction = agent.aave.pool_contract.functions.borrow(
            Web3.to_checksum_address(agent.usdc_address),
            amount_wei,
            2,  # Variable rate
            0,  # No referral
            user_address
        ).build_transaction({
            'chainId': agent.w3.eth.chain_id,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': nonce,
            'from': user_address
        })
        
        # Sign and send
        signed_txn = agent.w3.eth.account.sign_transaction(transaction, agent.account.key)
        tx_hash = agent.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        tx_hash_hex = tx_hash.hex()
        print(f"✅ Transaction sent: {tx_hash_hex}")
        
        # Wait for confirmation
        print(f"⏳ Waiting for confirmation...")
        receipt = agent.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print(f"🎉 BORROW SUCCESS!")
            print(f"📊 Transaction: https://arbiscan.io/tx/{tx_hash_hex}")
            return True
        else:
            print(f"❌ Transaction reverted")
            
            # Try to get revert reason
            try:
                agent.w3.eth.call(transaction, receipt.blockNumber)
            except Exception as revert_error:
                print(f"🔍 Revert reason: {revert_error}")
            
            return False
            
    except Exception as e:
        print(f"❌ Safe borrow test failed: {e}")
        return False

if __name__ == "__main__":
    safe_borrow_test()
