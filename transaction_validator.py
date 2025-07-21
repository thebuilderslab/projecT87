
import os
import time
from web3 import Web3

class TransactionValidator:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        
    def validate_swap_transaction(self, token_in, token_out, amount_in):
        """Validate swap transaction before execution"""
        try:
            print(f"🔍 Validating swap: {amount_in} {token_in} → {token_out}")
            
            # Check 1: Token contracts exist
            for token_addr in [token_in, token_out]:
                if token_addr != "0x0000000000000000000000000000000000000000":
                    code = self.w3.eth.get_code(Web3.to_checksum_address(token_addr))
                    if code == b'':
                        print(f"❌ No contract at {token_addr}")
                        return False
            
            # Check 2: Balance validation
            if token_in != "0x0000000000000000000000000000000000000000":
                try:
                    balance = self.agent.aave.get_token_balance(token_in)
                    if balance < amount_in:
                        print(f"❌ Insufficient balance: {balance} < {amount_in}")
                        return False
                    print(f"✅ Balance check passed: {balance} >= {amount_in}")
                except Exception as balance_error:
                    print(f"⚠️ Balance check failed: {balance_error}")
                    return False
            
            # Check 3: Gas availability
            eth_balance = self.agent.get_eth_balance()
            min_eth_needed = 0.001  # Conservative estimate
            if eth_balance < min_eth_needed:
                print(f"❌ Insufficient ETH for gas: {eth_balance} < {min_eth_needed}")
                return False
            
            print(f"✅ Swap validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Swap validation failed: {e}")
            return False
    
    def validate_borrow_transaction(self, amount_usd, token_address):
        """Validate borrow transaction before execution"""
        try:
            print(f"🔍 Validating borrow: ${amount_usd} of {token_address}")
            
            # Get account data
            account_data = self.agent.aave.get_user_account_data()
            if not account_data or not account_data.get('success', True):
                print(f"❌ Cannot get account data")
                return False
            
            # Check available borrows
            available_borrows = account_data['availableBorrowsUSD']
            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrow capacity: ${available_borrows} < ${amount_usd}")
                return False
            
            # Check health factor after borrow
            current_debt = account_data['totalDebtUSD']
            total_collateral = account_data['totalCollateralUSD']
            new_debt = current_debt + amount_usd
            
            if total_collateral > 0:
                estimated_hf = (total_collateral * 0.8) / new_debt if new_debt > 0 else float('inf')
                if estimated_hf < 1.5:
                    print(f"❌ Health factor would be too low: {estimated_hf:.4f}")
                    return False
            
            print(f"✅ Borrow validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Borrow validation failed: {e}")
            return False
