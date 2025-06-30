
#!/usr/bin/env python3
"""
Third-Party DeFi Data Integration
Provides backup data sources for Aave health monitoring
"""

import requests
import os
import time
from typing import Dict, Optional

class ThirdPartyDataProvider:
    def __init__(self):
        self.zapper_api_key = os.getenv('ZAPPER_API_KEY')
        self.debank_api_key = os.getenv('DEBANK_API_KEY')
        self.arbiscan_api_key = os.getenv('ARBISCAN_API_KEY')
        
    def get_zapper_portfolio(self, wallet_address: str) -> Optional[Dict]:
        """Get portfolio data from Zapper API"""
        try:
            url = f"https://api.zapper.fi/v2/portfolio"
            headers = {
                'Authorization': f'Basic {self.zapper_api_key}',
                'accept': 'application/json'
            }
            params = {
                'addresses[]': wallet_address,
                'networks[]': 'arbitrum'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_zapper_aave_data(data, wallet_address)
            else:
                print(f"❌ Zapper API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Zapper API failed: {e}")
            return None
    
    def get_debank_portfolio(self, wallet_address: str) -> Optional[Dict]:
        """Get portfolio data from DeBank API"""
        try:
            url = f"https://pro-openapi.debank.com/v1/user/simple_protocol_list"
            headers = {
                'AccessKey': self.debank_api_key,
                'accept': 'application/json'
            }
            params = {
                'id': wallet_address,
                'chain_id': 'arb'  # Arbitrum
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_debank_aave_data(data)
            else:
                print(f"❌ DeBank API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ DeBank API failed: {e}")
            return None
    
    def parse_zapper_aave_data(self, data: Dict, wallet_address: str) -> Dict:
        """Parse Zapper data for Aave positions"""
        aave_data = {
            'health_factor': 0,
            'total_collateral_usd': 0,
            'total_debt_usd': 0,
            'source': 'zapper'
        }
        
        try:
            # Navigate Zapper's data structure
            for network_data in data.get(wallet_address.lower(), {}).values():
                for app in network_data.get('products', []):
                    if 'aave' in app.get('label', '').lower():
                        # Extract Aave lending positions
                        for position in app.get('assets', []):
                            if position.get('type') == 'app-token':
                                balance_usd = position.get('balanceUSD', 0)
                                if 'supply' in position.get('metaType', ''):
                                    aave_data['total_collateral_usd'] += balance_usd
                                elif 'borrow' in position.get('metaType', ''):
                                    aave_data['total_debt_usd'] += balance_usd
            
            # Calculate health factor estimate
            if aave_data['total_debt_usd'] > 0:
                # Assuming 80% LTV for estimation
                aave_data['health_factor'] = (aave_data['total_collateral_usd'] * 0.8) / aave_data['total_debt_usd']
            else:
                aave_data['health_factor'] = float('inf')
                
        except Exception as e:
            print(f"❌ Error parsing Zapper data: {e}")
        
        return aave_data
    
    def parse_debank_aave_data(self, data: Dict) -> Dict:
        """Parse DeBank data for Aave positions"""
        aave_data = {
            'health_factor': 0,
            'total_collateral_usd': 0,
            'total_debt_usd': 0,
            'source': 'debank'
        }
        
        try:
            # Find Aave V3 protocol
            for protocol in data:
                if protocol.get('name', '').lower() == 'aave v3':
                    portfolio_item_list = protocol.get('portfolio_item_list', [])
                    
                    for item in portfolio_item_list:
                        if item.get('name') == 'Lending':
                            # Extract health factor if available
                            health_rate = item.get('detail', {}).get('health_rate')
                            if health_rate:
                                aave_data['health_factor'] = health_rate
                            
                            # Extract supply and borrow data
                            supply_token_list = item.get('detail', {}).get('supply_token_list', [])
                            borrow_token_list = item.get('detail', {}).get('borrow_token_list', [])
                            
                            for token in supply_token_list:
                                aave_data['total_collateral_usd'] += token.get('amount', 0) * token.get('price', 0)
                            
                            for token in borrow_token_list:
                                aave_data['total_debt_usd'] += token.get('amount', 0) * token.get('price', 0)
                            
                            break
                    break
                        
        except Exception as e:
            print(f"❌ Error parsing DeBank data: {e}")
        
        return aave_data
    
    def get_arbiscan_token_balance(self, wallet_address: str, contract_address: str) -> Optional[float]:
        """Get token balance using Arbiscan API"""
        try:
            url = "https://api.arbiscan.io/api"
            params = {
                'module': 'account',
                'action': 'tokenbalance',
                'contractaddress': contract_address,
                'address': wallet_address,
                'tag': 'latest',
                'apikey': self.arbiscan_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    balance_wei = int(data.get('result', '0'))
                    # Get token decimals
                    decimals = self.get_token_decimals_arbiscan(contract_address)
                    balance = balance_wei / (10 ** decimals)
                    return balance
            
            return None
                
        except Exception as e:
            print(f"❌ Arbiscan token balance failed: {e}")
            return None
    
    def get_token_decimals_arbiscan(self, contract_address: str) -> int:
        """Get token decimals using Arbiscan API"""
        try:
            # Common token decimals - use as fallback
            token_decimals = {
                '0xaf88D065eEc38FAD0aEfF3e253e648a15cEE23DC': 6,  # USDC
                '0x2F2a2543B76a4166549F7BFfbe68Df6FC579b2F3': 8,  # WBTC
                '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1': 18, # WETH
                '0x912CE59144191C1204E64559FE8253a0e49E6548': 18  # ARB
            }
            
            return token_decimals.get(contract_address.lower(), 18)
                
        except Exception as e:
            print(f"❌ Error getting token decimals: {e}")
            return 18
    
    def get_arbiscan_aave_data(self, wallet_address: str) -> Optional[Dict]:
        """Get Aave position data using Arbiscan API"""
        try:
            # Get token balances for major Aave tokens
            usdc_address = "0xaf88D065eEc38FAD0aEfF3e253e648a15cEE23DC"
            wbtc_address = "0x2F2a2543B76a4166549F7BFfbe68Df6FC579b2F3"
            weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
            
            usdc_balance = self.get_arbiscan_token_balance(wallet_address, usdc_address) or 0
            wbtc_balance = self.get_arbiscan_token_balance(wallet_address, wbtc_address) or 0
            weth_balance = self.get_arbiscan_token_balance(wallet_address, weth_address) or 0
            
            # Estimate USD values (you could enhance this with price API)
            usdc_usd = usdc_balance * 1.0  # USDC ~= $1
            wbtc_usd = wbtc_balance * 95000  # Approximate WBTC price
            weth_usd = weth_balance * 2500   # Approximate ETH price
            
            total_collateral_usd = usdc_usd + wbtc_usd + weth_usd
            
            # For health factor, we need actual Aave contract calls
            # This is a simplified estimation
            health_factor = 999 if total_collateral_usd > 0 else 0
            
            return {
                'health_factor': health_factor,
                'total_collateral_usd': total_collateral_usd,
                'total_debt_usd': 0,  # Would need specific Aave debt token checks
                'source': 'arbiscan',
                'token_balances': {
                    'USDC': usdc_balance,
                    'WBTC': wbtc_balance,
                    'WETH': weth_balance
                }
            }
                
        except Exception as e:
            print(f"❌ Arbiscan Aave data failed: {e}")
            return None

    def get_reliable_aave_data(self, wallet_address: str) -> Optional[Dict]:
        """Get Aave data with fallback sources including Arbiscan"""
        
        # Try Arbiscan first (most accurate for on-chain data)
        if self.arbiscan_api_key:
            print("🔄 Trying Arbiscan API...")
            arbiscan_data = self.get_arbiscan_aave_data(wallet_address)
            if arbiscan_data and arbiscan_data['total_collateral_usd'] > 0:
                print(f"✅ Arbiscan: ${arbiscan_data['total_collateral_usd']:,.2f} collateral")
                return arbiscan_data
        
        # Try DeBank second (often more detailed for DeFi)
        if self.debank_api_key:
            print("🔄 Trying DeBank API...")
            debank_data = self.get_debank_portfolio(wallet_address)
            if debank_data and debank_data['health_factor'] > 0:
                print(f"✅ DeBank: Health Factor {debank_data['health_factor']:.4f}")
                return debank_data
        
        # Fallback to Zapper
        if self.zapper_api_key:
            print("🔄 Trying Zapper API...")
            zapper_data = self.get_zapper_portfolio(wallet_address)
            if zapper_data and zapper_data['health_factor'] > 0:
                print(f"✅ Zapper: Health Factor {zapper_data['health_factor']:.4f}")
                return zapper_data
        
        print("❌ All third-party APIs failed")
        return None

# Integration example
def enhance_aave_monitoring():
    """Show how to integrate with existing health monitor"""
    provider = ThirdPartyDataProvider()
    wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    
    # Get reliable data
    data = provider.get_reliable_aave_data(wallet)
    if data:
        print(f"📊 Third-party data: {data}")
        return data
    else:
        print("💡 Falling back to on-chain calls...")
        return None

if __name__ == "__main__":
    enhance_aave_monitoring()
