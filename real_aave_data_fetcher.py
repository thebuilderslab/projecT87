
#!/usr/bin/env python3
"""
Real Aave Data Fetcher
Fetches accurate, real-time data directly from Aave contracts
"""

import os
from web3 import Web3
import requests

class RealAaveDataFetcher:
    def __init__(self, w3, wallet_address):
        self.w3 = w3
        self.wallet_address = Web3.to_checksum_address(wallet_address)
        
        # Aave V3 Arbitrum addresses
        self.pool_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        self.price_oracle = "0xb56c2F0B653B2e0b10C9b928C8580Ac5Df02C7C7"
        
        # Token addresses
        self.usdc_address = "0xaf88d065eec38faD0AEFf3e253e648a15cEe23dC"
        self.wbtc_address = "0x2f2a2543B76A4166549F7bffBE68df6Fc579b2F3"
        self.weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
        
        # ABI for data provider
        self.data_provider_abi = [
            {
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
            }
        ]
    
    def get_accurate_aave_data(self):
        """Get accurate Aave data directly from contracts"""
        try:
            print(f"🔍 Fetching real Aave data for {self.wallet_address}")
            
            # Create contract instance
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.pool_data_provider),
                abi=self.data_provider_abi
            )
            
            # Call getUserAccountData
            result = contract.functions.getUserAccountData(self.wallet_address).call()
            
            # Parse results (values are in 8 decimals for USD amounts)
            total_collateral_base = result[0] / 1e8  # USD
            total_debt_base = result[1] / 1e8  # USD
            available_borrows_base = result[2] / 1e8  # USD
            health_factor_raw = result[5]
            
            # Health factor is in 18 decimals, or max uint256 if no debt
            if health_factor_raw == 2**256 - 1:
                health_factor = float('inf')
            else:
                health_factor = health_factor_raw / 1e18
            
            accurate_data = {
                'health_factor': min(health_factor, 999.9) if health_factor != float('inf') else 999.9,
                'total_collateral_usdc': total_collateral_base,
                'total_debt_usdc': total_debt_base,
                'available_borrows_usdc': available_borrows_base,
                'data_source': 'aave_contract_direct',
                'timestamp': __import__('time').time()
            }
            
            print(f"✅ Real Aave data retrieved:")
            print(f"   Health Factor: {accurate_data['health_factor']:.4f}")
            print(f"   Collateral: ${accurate_data['total_collateral_usdc']:.2f}")
            print(f"   Debt: ${accurate_data['total_debt_usdc']:.2f}")
            print(f"   Available Borrows: ${accurate_data['available_borrows_usdc']:.2f}")
            
            return accurate_data
            
        except Exception as e:
            print(f"❌ Real Aave data fetch failed: {e}")
            return None
    
    def get_token_balance_direct(self, token_address):
        """Get token balance directly via contract call"""
        try:
            token_abi = [
                {
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]
            
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=token_abi
            )
            
            balance_wei = contract.functions.balanceOf(self.wallet_address).call()
            decimals = contract.functions.decimals().call()
            balance = balance_wei / (10 ** decimals)
            
            return balance
            
        except Exception as e:
            print(f"❌ Direct token balance failed for {token_address}: {e}")
            return 0.0

def test_real_data_fetcher():
    """Test the real data fetcher"""
    from arbitrum_testnet_agent import ArbitrumTestnetAgent
    
    try:
        agent = ArbitrumTestnetAgent()
        fetcher = RealAaveDataFetcher(agent.w3, agent.address)
        
        print("🧪 Testing Real Aave Data Fetcher")
        print("=" * 50)
        
        # Test Aave data
        aave_data = fetcher.get_accurate_aave_data()
        if aave_data:
            print("✅ Real Aave data fetch successful")
        else:
            print("❌ Real Aave data fetch failed")
        
        # Test token balances
        usdc_balance = fetcher.get_token_balance_direct(fetcher.usdc_address)
        print(f"💰 USDC Balance: {usdc_balance:.6f}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_real_data_fetcher()
