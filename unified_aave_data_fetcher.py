
<file_content>
import time
from decimal import Decimal

class UnifiedAaveDataFetcher:
    """Single source of truth for all Aave position data"""
    
    def __init__(self, w3, address, aave_pool_address):
        self.w3 = w3
        self.address = address
        self.aave_pool_address = aave_pool_address
        self.cache = {}
        self.cache_duration = 10  # 10 seconds cache
        
        # Standard Aave Pool ABI
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
    
    def get_live_aave_data(self, force_refresh=False):
        """Get live Aave data with caching and retry logic"""
        cache_key = "aave_data"
        current_time = time.time()
        
        # Check cache first
        if not force_refresh and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_duration:
                cached_data['data_source'] = 'UNIFIED_CACHE'
                return cached_data
        
        # Fetch fresh data with retry logic
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                pool_contract = self.w3.eth.contract(
                    address=self.aave_pool_address,
                    abi=self.pool_abi
                )
                
                print(f"🔄 Fetching live Aave data (attempt {attempt + 1}/{max_attempts})")
                account_data = pool_contract.functions.getUserAccountData(self.address).call()
                
                # Parse data (Aave V3 uses 8 decimals for USD values)
                data = {
                    'total_collateral_usd': float(Decimal(account_data[0]) / Decimal(10**8)),
                    'total_debt_usd': float(Decimal(account_data[1]) / Decimal(10**8)),
                    'available_borrows_usd': float(Decimal(account_data[2]) / Decimal(10**8)),
                    'liquidation_threshold': account_data[3],
                    'ltv': account_data[4],
                    'health_factor': float(Decimal(account_data[5]) / Decimal(10**18)) if account_data[5] > 0 else float('inf'),
                    'data_source': 'LIVE_AAVE_CONTRACT',
                    'timestamp': current_time,
                    'success': True
                }
                
                # Cache the result
                self.cache[cache_key] = (data, current_time)
                
                print(f"✅ Live Aave data fetched successfully:")
                print(f"   Collateral: ${data['total_collateral_usd']:,.2f}")
                print(f"   Debt: ${data['total_debt_usd']:,.2f}")
                print(f"   Health Factor: {data['health_factor']:.4f}")
                
                return data
                
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                
                if attempt < max_attempts - 1:
                    # Try switching RPC provider if available
                    if hasattr(self.w3, 'fallback_provider'):
                        print("🔄 Switching to next RPC provider...")
                        new_provider = self.w3.fallback_provider.switch_provider()
                        self.w3.provider = new_provider
                    
                    time.sleep(2)  # Brief delay before retry
                    continue
                else:
                    print(f"❌ All attempts failed to fetch Aave data")
                    return {
                        'success': False,
                        'error': str(e),
                        'data_source': 'FAILED_LIVE_FETCH',
                        'timestamp': current_time
                    }
    
    def clear_cache(self):
        """Clear the data cache to force fresh fetch"""
        self.cache.clear()
        print("🗑️ Aave data cache cleared")
</file_content>
