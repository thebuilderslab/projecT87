
#!/usr/bin/env python3
"""
Unified Aave Data Fetcher - Single Source of Truth
Eliminates all cached data issues by fetching directly from Aave contracts
"""

import os
import time
from web3 import Web3
from eth_account import Account

class UnifiedAaveDataFetcher:
    def __init__(self, w3=None, agent_address=None):
        """Initialize with Web3 instance and wallet address"""
        self.w3 = w3
        self.agent_address = agent_address
        
        # Aave V3 Pool address on Arbitrum Mainnet
        self.aave_pool_address = Web3.to_checksum_address("0x794a61358D6845594F94dc1DB02A252b5b4814aD")
        
        # Standard Aave Pool ABI for getUserAccountData
        self.pool_abi = [{
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
        
        self.pool_contract = None
        self._initialize_contract()
    
    def _initialize_contract(self):
        """Initialize Aave pool contract"""
        if self.w3:
            try:
                self.pool_contract = self.w3.eth.contract(
                    address=self.aave_pool_address,
                    abi=self.pool_abi
                )
                print(f"✅ Unified fetcher initialized for Aave Pool: {self.aave_pool_address}")
            except Exception as e:
                print(f"❌ Failed to initialize Aave pool contract: {e}")
    
    def get_live_aave_data(self, user_address=None, retry_count=3):
        """
        Get live Aave data directly from contract - NO CACHING
        Returns standardized data format for dashboard consistency
        """
        if not user_address:
            user_address = self.agent_address
        
        if not user_address:
            print("❌ No user address provided for Aave data fetch")
            return None
            
        user_address = Web3.to_checksum_address(user_address)
        
        for attempt in range(retry_count):
            try:
                print(f"🔍 LIVE AAVE FETCH Attempt {attempt + 1}: {user_address}")
                
                # Direct contract call - bypasses all caching
                account_data = self.pool_contract.functions.getUserAccountData(user_address).call()
                
                # Aave V3 uses 8 decimal places for USD values
                total_collateral_usd = account_data[0] / (10**8)
                total_debt_usd = account_data[1] / (10**8)
                available_borrows_usd = account_data[2] / (10**8)
                current_liquidation_threshold = account_data[3] / 10000  # Convert from basis points
                ltv = account_data[4] / 10000  # Convert from basis points
                health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
                
                # Create standardized response format
                live_data = {
                    'health_factor': health_factor,
                    'total_collateral_usdc': total_collateral_usd,
                    'total_debt_usdc': total_debt_usd,
                    'available_borrows_usdc': available_borrows_usd,
                    'liquidation_threshold': current_liquidation_threshold,
                    'ltv': ltv,
                    'baseline_collateral': total_collateral_usd,  # For trigger calculations
                    'next_trigger_threshold': total_collateral_usd + 12.0,  # $12 trigger
                    'operation_cooldown': False,
                    'data_source': 'LIVE_AAVE_CONTRACT',
                    'data_quality': 'VALIDATED',
                    'last_update': time.time(),
                    'timestamp': time.time(),
                    'fetch_attempt': attempt + 1,
                    'success': True
                }
                
                print(f"✅ LIVE AAVE DATA RETRIEVED:")
                print(f"   Health Factor: {health_factor:.4f}")
                print(f"   Collateral: ${total_collateral_usd:,.2f}")
                print(f"   Debt: ${total_debt_usd:,.2f}")
                print(f"   Available Borrows: ${available_borrows_usd:,.2f}")
                print(f"   Data Source: LIVE_AAVE_CONTRACT")
                print(f"   Data Quality: ✅ VALIDATED")
                
                return live_data
                
            except Exception as e:
                print(f"❌ Live Aave fetch attempt {attempt + 1} failed: {e}")
                if attempt == retry_count - 1:
                    print(f"❌ All {retry_count} attempts failed")
                    return None
                time.sleep(1)  # Brief pause between retries
        
        return None
    
    def validate_aave_data(self, data):
        """Validate Aave data quality and completeness"""
        if not data or not isinstance(data, dict):
            return False, "No data or invalid format"
        
        required_fields = ['health_factor', 'total_collateral_usdc', 'total_debt_usdc', 'available_borrows_usdc']
        
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
            
            value = data[field]
            if value is None or (isinstance(value, (int, float)) and value < 0):
                return False, f"Invalid value for {field}: {value}"
        
        # Business logic validation
        health_factor = data.get('health_factor', 0)
        collateral = data.get('total_collateral_usdc', 0)
        debt = data.get('total_debt_usdc', 0)
        
        if health_factor < 0.1 or health_factor > 100:
            return False, f"Unrealistic health factor: {health_factor}"
        
        if debt > collateral * 2:
            return False, f"Debt too high relative to collateral"
        
        return True, "Data validated successfully"

# Global instance for unified access
_unified_fetcher = None

def get_unified_aave_data(agent=None, user_address=None):
    """
    Global function to get live Aave data
    This replaces all cached data sources
    """
    global _unified_fetcher
    
    # Initialize fetcher if needed
    if not _unified_fetcher and agent:
        _unified_fetcher = UnifiedAaveDataFetcher(
            w3=agent.w3,
            agent_address=agent.address
        )
    
    if not _unified_fetcher:
        print("❌ Unified fetcher not initialized")
        return None
    
    # Get live data
    live_data = _unified_fetcher.get_live_aave_data(user_address)
    
    if live_data:
        # Validate data before returning
        is_valid, validation_msg = _unified_fetcher.validate_aave_data(live_data)
        if is_valid:
            print(f"✅ Unified data validated: {validation_msg}")
            return live_data
        else:
            print(f"❌ Data validation failed: {validation_msg}")
            return None
    
    return None

if __name__ == "__main__":
    print("🧪 Testing Unified Aave Data Fetcher...")
    
    # Test with agent
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        # Get live data
        live_data = get_unified_aave_data(agent)
        
        if live_data:
            print(f"✅ Test successful - Live data retrieved")
            print(f"   Health Factor: {live_data['health_factor']:.4f}")
            print(f"   Data Source: {live_data['data_source']}")
        else:
            print(f"❌ Test failed - No data retrieved")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
