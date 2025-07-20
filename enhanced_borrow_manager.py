
"""
Enhanced Borrow Manager
Provides robust borrowing functionality with fallbacks and validation
"""

import time
from web3 import Web3

class EnhancedBorrowManager:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.account = agent.account
        self.aave = agent.aave
        
    def safe_borrow_with_fallbacks(self, amount_usd, token_address):
        """Execute borrow with comprehensive safety checks and fallbacks"""
        try:
            print(f"🏦 Enhanced Borrow Manager: Attempting to borrow ${amount_usd:.2f}")
            
            # Pre-validation
            if not self._validate_borrow_conditions(amount_usd):
                return False
                
            # Execute borrow with retries
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    print(f"🔄 Borrow attempt {attempt + 1}/{max_attempts}")
                    
                    # Use the agent's Aave integration
                    result = self.aave.borrow(amount_usd, token_address)
                    
                    if result:
                        print(f"✅ Borrow successful: {result}")
                        return result
                    else:
                        print(f"❌ Borrow attempt {attempt + 1} failed")
                        
                except Exception as e:
                    print(f"❌ Borrow attempt {attempt + 1} error: {e}")
                    
                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt
                        print(f"⏱️ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        
            print(f"❌ All {max_attempts} borrow attempts failed")
            return False
            
        except Exception as e:
            print(f"❌ Enhanced borrow manager failed: {e}")
            return False
            
    def _validate_borrow_conditions(self, amount_usd):
        """Validate conditions for safe borrowing"""
        try:
            # Check health factor
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
            
            pool_contract = self.w3.eth.contract(
                address=self.agent.aave_pool_address,
                abi=pool_abi
            )
            
            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
            
            health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
            available_borrows = account_data[2] / (10**8)
            
            print(f"🔍 Validation - Health Factor: {health_factor:.4f}")
            print(f"🔍 Validation - Available Borrows: ${available_borrows:.2f}")
            
            if health_factor < 1.5:
                print(f"❌ Health factor too low: {health_factor:.4f}")
                return False
                
            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrowing capacity")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
            
    def execute_enhanced_borrow_with_retry(self, amount_usd):
        """Legacy method for compatibility"""
        return self.safe_borrow_with_fallbacks(amount_usd, self.agent.usdc_address)
"""
Enhanced Borrow Manager
Provides robust borrowing functionality with fallbacks and validation
"""

import time
from web3 import Web3

class EnhancedBorrowManager:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.account = agent.account
        self.aave = agent.aave
        
    def safe_borrow_with_fallbacks(self, amount_usd, token_address):
        """Execute borrow with comprehensive safety checks and fallbacks"""
        try:
            print(f"🏦 Enhanced Borrow Manager: Attempting to borrow ${amount_usd:.2f}")
            
            # Pre-validation
            if not self._validate_borrow_conditions(amount_usd):
                return False
                
            # Execute borrow with retries
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    print(f"🔄 Borrow attempt {attempt + 1}/{max_attempts}")
                    
                    # Use the agent's Aave integration
                    result = self.aave.borrow(amount_usd, token_address)
                    
                    if result:
                        print(f"✅ Borrow successful: {result}")
                        return result
                    else:
                        print(f"❌ Borrow attempt {attempt + 1} failed")
                        
                except Exception as e:
                    print(f"❌ Borrow attempt {attempt + 1} error: {e}")
                    
                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt
                        print(f"⏱️ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        
            print(f"❌ All {max_attempts} borrow attempts failed")
            return False
            
        except Exception as e:
            print(f"❌ Enhanced borrow manager failed: {e}")
            return False
            
    def _validate_borrow_conditions(self, amount_usd):
        """Validate conditions for safe borrowing"""
        try:
            # Check health factor
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
            
            pool_contract = self.w3.eth.contract(
                address=self.agent.aave_pool_address,
                abi=pool_abi
            )
            
            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
            
            health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
            available_borrows = account_data[2] / (10**8)
            
            print(f"🔍 Validation - Health Factor: {health_factor:.4f}")
            print(f"🔍 Validation - Available Borrows: ${available_borrows:.2f}")
            
            if health_factor < 1.5:
                print(f"❌ Health factor too low: {health_factor:.4f}")
                return False
                
            if available_borrows < amount_usd:
                print(f"❌ Insufficient borrowing capacity")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
            
    def execute_enhanced_borrow_with_retry(self, amount_usd):
        """Legacy method for compatibility"""
        return self.safe_borrow_with_fallbacks(amount_usd, self.agent.usdc_address)
