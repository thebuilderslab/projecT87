
import os
import time
from web3 import Web3

class TransactionValidator:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        
    def validate_swap_transaction(self, token_in, token_out, amount_in):
        """Validate swap transaction before execution with comprehensive checks"""
        try:
            print(f"🔍 Validating swap: {amount_in} {token_in} → {token_out}")
            
            # Check 1: Token contracts exist and are valid
            for token_addr in [token_in, token_out]:
                if token_addr != "0x0000000000000000000000000000000000000000":
                    try:
                        checksummed_addr = Web3.to_checksum_address(token_addr)
                        code = self.w3.eth.get_code(checksummed_addr)
                        if code == b'':
                            print(f"❌ No contract at {token_addr}")
                            return False
                        
                        # Verify it's an ERC20 token
                        token_contract = self.w3.eth.contract(
                            address=checksummed_addr,
                            abi=self.agent.uniswap.erc20_abi
                        )
                        symbol = token_contract.functions.symbol().call()
                        print(f"✅ Token {symbol} contract verified at {checksummed_addr}")
                        
                    except Exception as contract_error:
                        print(f"❌ Token contract validation failed for {token_addr}: {contract_error}")
                        return False
            
            # Check 2: Enhanced balance validation
            if token_in != "0x0000000000000000000000000000000000000000":
                try:
                    balance = self.agent.aave.get_token_balance(token_in)
                    if balance < amount_in:
                        print(f"❌ Insufficient balance: {balance:.6f} < {amount_in:.6f}")
                        return False
                    
                    # Check for reasonable buffer (5% extra)
                    buffer_amount = amount_in * 1.05
                    if balance < buffer_amount:
                        print(f"⚠️ Tight balance margin: {balance:.6f} vs needed {buffer_amount:.6f}")
                    
                    print(f"✅ Balance check passed: {balance:.6f} >= {amount_in:.6f}")
                except Exception as balance_error:
                    print(f"⚠️ Balance check failed: {balance_error}")
                    return False
            
            # Check 3: Enhanced gas availability
            eth_balance = self.agent.get_eth_balance()
            
            # Dynamic gas requirement based on network
            chain_id = self.w3.eth.chain_id
            if chain_id == 42161:  # Arbitrum Mainnet
                min_eth_needed = 0.0005  # 0.0005 ETH for Arbitrum
            else:
                min_eth_needed = 0.001   # 0.001 ETH for other networks
                
            if eth_balance < min_eth_needed:
                print(f"❌ Insufficient ETH for gas: {eth_balance:.6f} < {min_eth_needed}")
                return False
            
            # Check 4: Network congestion
            try:
                gas_price = self.w3.eth.gas_price
                base_fee = self.w3.eth.get_block('latest').get('baseFeePerGas', gas_price)
                congestion_ratio = gas_price / base_fee if base_fee > 0 else 1.0
                
                if congestion_ratio > 5.0:
                    print(f"⚠️ High network congestion detected: {congestion_ratio:.2f}x base fee")
                    print("💡 Consider waiting for lower gas prices")
                
            except Exception as gas_error:
                print(f"⚠️ Could not check network congestion: {gas_error}")
            
            # Check 5: Validate swap route exists (basic check)
            if token_in.lower() == token_out.lower():
                print("❌ Cannot swap token to itself")
                return False
            
            # Check 6: Amount sanity check
            if amount_in <= 0:
                print(f"❌ Invalid swap amount: {amount_in}")
                return False
            
            if amount_in > 1000:  # Sanity check for very large amounts
                print(f"⚠️ Large swap amount detected: ${amount_in:.2f}")
                user_confirm = input("Continue with large swap? (y/N): ").lower().strip()
                if user_confirm != 'y':
                    print("❌ Large swap cancelled by validation")
                    return False
            
            print(f"✅ Comprehensive swap validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Swap validation failed: {e}")
            import traceback
            print(f"🔍 Validation error details: {traceback.format_exc()}")
            return False
    
    def validate_borrow_transaction(self, amount_usd, token_address):
        """Validate borrow transaction before execution with enhanced checks"""
        try:
            print(f"🔍 Validating borrow: ${amount_usd:.2f} of {token_address}")
            
            # Check 1: Token address validation
            try:
                checksummed_token = Web3.to_checksum_address(token_address)
                token_contract = self.w3.eth.contract(
                    address=checksummed_token,
                    abi=self.agent.aave.erc20_abi
                )
                token_symbol = token_contract.functions.symbol().call()
                print(f"✅ Borrow token validated: {token_symbol}")
                
                # Ensure we're borrowing DAI (part of system validation)
                if token_symbol.upper() != 'DAI':
                    print(f"⚠️ Warning: Borrowing {token_symbol} instead of DAI")
                    
            except Exception as token_error:
                print(f"❌ Invalid borrow token address: {token_error}")
                return False
            
            # Check 2: Get account data
            account_data = self.agent.aave.get_user_account_data()
            if not account_data or not account_data.get('success', True):
                print(f"❌ Cannot get account data")
                return False
            
            # Check 3: Available borrow capacity
            available_borrows = account_data['availableBorrowsUSD']
            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrow capacity: ${available_borrows:.2f} < ${amount_usd:.2f}")
                return False
            
            # Check 4: Ensure sufficient buffer in borrow capacity
            safe_borrow_amount = available_borrows * 0.8  # Use only 80% of available
            if amount_usd > safe_borrow_amount:
                print(f"⚠️ Borrow amount exceeds safe threshold: ${amount_usd:.2f} > ${safe_borrow_amount:.2f}")
                # Allow but warn
            
            # Check 5: Health factor validation
            current_debt = account_data['totalDebtUSD']
            total_collateral = account_data['totalCollateralUSD']
            new_debt = current_debt + amount_usd
            
            if total_collateral > 0:
                # Conservative health factor calculation
                estimated_hf = (total_collateral * 0.75) / new_debt if new_debt > 0 else float('inf')
                
                print(f"📊 Health factor analysis:")
                print(f"   Current debt: ${current_debt:.2f}")
                print(f"   New debt: ${new_debt:.2f}")
                print(f"   Collateral: ${total_collateral:.2f}")
                print(f"   Estimated HF after borrow: {estimated_hf:.4f}")
                
                if estimated_hf < 1.8:  # Conservative threshold
                    print(f"❌ Health factor would be too low: {estimated_hf:.4f} < 1.8")
                    return False
                elif estimated_hf < 2.0:
                    print(f"⚠️ Health factor approaching minimum: {estimated_hf:.4f}")
            
            # Check 6: ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            min_eth_needed = 0.0005  # Minimum ETH for borrow transaction
            if eth_balance < min_eth_needed:
                print(f"❌ Insufficient ETH for borrow gas: {eth_balance:.6f} < {min_eth_needed}")
                return False
            
            # Check 7: Validate borrow amount is reasonable
            if amount_usd < 0.5:
                print(f"❌ Borrow amount too small: ${amount_usd:.2f} < $0.5")
                return False
            
            if amount_usd > 500:  # Large borrow safety check
                print(f"⚠️ Large borrow amount: ${amount_usd:.2f}")
                print("💡 Consider breaking into smaller borrows")
            
            # Check 8: Network conditions
            try:
                gas_price = self.w3.eth.gas_price
                current_block = self.w3.eth.block_number
                print(f"🌐 Network status: Block {current_block}, Gas {self.w3.from_wei(gas_price, 'gwei'):.2f} gwei")
            except Exception as network_error:
                print(f"⚠️ Could not check network conditions: {network_error}")
            
            print(f"✅ Comprehensive borrow validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Borrow validation failed: {e}")
            import traceback
            print(f"🔍 Validation error details: {traceback.format_exc()}")
            return False
    
    def validate_supply_transaction(self, token_address, amount):
        """Validate supply transaction before execution"""
        try:
            print(f"🔍 Validating supply: {amount:.6f} tokens to {token_address}")
            
            # Check token balance
            balance = self.agent.aave.get_token_balance(token_address)
            if balance < amount:
                print(f"❌ Insufficient token balance: {balance:.6f} < {amount:.6f}")
                return False
            
            # Check ETH for gas
            eth_balance = self.agent.get_eth_balance()
            if eth_balance < 0.0005:
                print(f"❌ Insufficient ETH for supply gas: {eth_balance:.6f}")
                return False
            
            print(f"✅ Supply validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Supply validation failed: {e}")
            return False
