
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
    
    def get_reliable_aave_data(self, wallet_address: str) -> Optional[Dict]:
        """Get Aave data with fallback sources"""
        
        # Try DeBank first (often more detailed for DeFi)
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
