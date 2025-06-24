
import os
import json
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import requests
from collections import deque

class AaveHealthMonitor:
    def __init__(self, w3, account, aave_integration):
        self.w3 = w3
        self.account = account
        self.aave = aave_integration
        
        # Health factor history (stores last 100 readings)
        self.health_history = deque(maxlen=100)
        self.arb_price_history = deque(maxlen=50)
        
        # Aave V3 Data Provider for health factor - working Arbitrum Sepolia address
        self.data_provider_address = self.w3.to_checksum_address("0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654")
        self.data_provider_abi = self._get_data_provider_abi()
        
        # ARB token address on Arbitrum Sepolia (working deployed contract)
        self.arb_address = self.w3.to_checksum_address("0x6FE14d3CC2f7bDdffBa5CdB3d8B725077dbbf5d5")
        
        # Ensure account address is properly formatted and checksummed
        if hasattr(self.account, 'address'):
            self.user_address = self.w3.to_checksum_address(self.account.address)
        else:
            # Handle case where account might be a string or other format
            account_str = str(self.account)
            if account_str.startswith('0x'):
                self.user_address = self.w3.to_checksum_address(account_str)
            else:
                raise ValueError(f"Invalid account format: {account_str}")
        
        print(f"📊 Health Monitor Addresses:")
        print(f"   User: {self.user_address}")
        print(f"   Data Provider: {self.data_provider_address}")
        print(f"   ARB Token: {self.arb_address}")
        
        print(f"📊 Enhanced Aave Health Monitor initialized for {self.user_address}")
    
    def _get_data_provider_abi(self):
        """Aave V3 Pool Data Provider ABI for user account data"""
        return [
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"internalType": "uint256", "name": "totalCollateralETH", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalDebtETH", "type": "uint256"},
                    {"internalType": "uint256", "name": "availableBorrowsETH", "type": "uint256"},
                    {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
                    {"internalType": "uint256", "name": "ltv", "type": "uint256"},
                    {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def get_current_health_factor(self):
        """Get current health factor from Aave"""
        try:
            # Use pre-checksummed addresses
            user_address = self.user_address
            data_provider_address = self.data_provider_address
            
            print(f"🔍 Calling getUserAccountData with:")
            print(f"   Contract: {data_provider_address}")
            print(f"   User: {user_address}")
            
            # Create contract instance
            data_provider_contract = self.w3.eth.contract(
                address=data_provider_address,
                abi=self.data_provider_abi
            )
            
            # Test if contract exists
            try:
                code = self.w3.eth.get_code(data_provider_address)
                if code == b'':
                    print(f"❌ No contract deployed at {data_provider_address}")
                    return None
            except Exception as code_err:
                print(f"❌ Error checking contract code: {code_err}")
                return None
            
            # Call the function
            user_data = data_provider_contract.functions.getUserAccountData(user_address).call()
            
            # Extract data
            total_collateral_eth = user_data[0] / 1e18
            total_debt_eth = user_data[1] / 1e18
            available_borrows_eth = user_data[2] / 1e18
            health_factor_raw = user_data[5]
            
            # Health factor is returned in 1e18 format, convert to decimal
            health_factor = health_factor_raw / 1e18 if health_factor_raw < 2**256 - 1 else float('inf')
            
            account_data = {
                'total_collateral_eth': total_collateral_eth,
                'total_debt_eth': total_debt_eth,
                'available_borrows_eth': available_borrows_eth,
                'health_factor': health_factor,
                'timestamp': time.time()
            }
            
            # Store in history
            self.health_history.append(account_data)
            
            print(f"✅ Health factor retrieved: {health_factor:.4f}")
            return account_data
            
        except Exception as e:
            print(f"❌ Failed to get health factor: {e}")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   User address: {self.user_address}")
            print(f"   Contract address: {self.data_provider_address}")
            return None
    
    def get_arb_price(self):
        """Get ARB price from CoinMarketCap API"""
        try:
            # Check for API key
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            print(f"🔍 CoinMarketCap API Key status: {'Found' if api_key else 'NOT FOUND'}")
            
            if not api_key:
                print("❌ CoinMarketCap API key not found in environment")
                print("   Please add COINMARKETCAP_API_KEY to your Replit secrets")
                return None
                
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': api_key,
            }
            
            params = {
                'symbol': 'ARB',
                'convert': 'USD'
            }
            
            print(f"🌐 Making CoinMarketCap API request:")
            print(f"   URL: {url}")
            print(f"   Params: {params}")
            print(f"   API Key (first 8 chars): {api_key[:8]}...")
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Response received successfully")
                
                if 'data' in data and 'ARB' in data['data']:
                    arb_price = data['data']['ARB']['quote']['USD']['price']
                    
                    price_data = {
                        'price': arb_price,
                        'timestamp': time.time()
                    }
                    
                    print(f"💰 ARB Price: ${arb_price:.4f}")
                    self.arb_price_history.append(price_data)
                    return price_data
                else:
                    print(f"❌ Invalid CoinMarketCap response format:")
                    print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    if 'data' in data:
                        print(f"   Data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'Data not a dict'}")
                    return None
            elif response.status_code == 429:
                print(f"❌ CoinMarketCap rate limit exceeded - waiting...")
                return None
            else:
                print(f"❌ CoinMarketCap API error: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Raw response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ ARB price fetch error: {e}")
            print(f"   Exception type: {type(e).__name__}")
            return None
    
    def check_health_factor_increase_trigger(self, threshold=0.02):
        """Check if health factor has increased by threshold amount"""
        if len(self.health_history) < 2:
            return False, 0
        
        current_hf = self.health_history[-1]['health_factor']
        previous_hf = self.health_history[-2]['health_factor']
        
        increase = current_hf - previous_hf
        
        triggered = increase >= threshold
        
        if triggered:
            print(f"🚨 BORROW TRIGGER: Health factor increased by {increase:.4f} (from {previous_hf:.4f} to {current_hf:.4f})")
        
        return triggered, increase
    
    def check_risk_mitigation_trigger(self, arb_decline_threshold=0.05):
        """Check if both health factor is declining AND ARB price is declining"""
        if len(self.health_history) < 2 or len(self.arb_price_history) < 5:
            return False, {}
        
        # Check health factor decline
        current_hf = self.health_history[-1]['health_factor']
        previous_hf = self.health_history[-2]['health_factor']
        hf_declining = current_hf < previous_hf
        
        # Check ARB price decline (compare with 5-period moving average)
        recent_arb_prices = [p['price'] for p in list(self.arb_price_history)[-5:]]
        current_arb_price = recent_arb_prices[-1]
        avg_recent_price = sum(recent_arb_prices[:-1]) / len(recent_arb_prices[:-1])
        
        arb_decline_pct = (avg_recent_price - current_arb_price) / avg_recent_price
        arb_declining = arb_decline_pct >= arb_decline_threshold
        
        risk_triggered = hf_declining and arb_declining
        
        risk_data = {
            'health_factor_declining': hf_declining,
            'hf_change': current_hf - previous_hf,
            'arb_declining': arb_declining,
            'arb_decline_pct': arb_decline_pct,
            'current_arb_price': current_arb_price,
            'avg_recent_arb': avg_recent_price
        }
        
        if risk_triggered:
            print(f"🚨 RISK MITIGATION TRIGGER:")
            print(f"   Health Factor: {previous_hf:.4f} → {current_hf:.4f} (declining)")
            print(f"   ARB Price: ${avg_recent_price:.4f} → ${current_arb_price:.4f} (-{arb_decline_pct*100:.2f}%)")
        
        return risk_triggered, risk_data
    
    def get_arb_balance(self):
        """Get current ARB token balance"""
        try:
            # Use pre-checksummed addresses
            arb_address = self.arb_address
            user_address = self.user_address
            
            print(f"🔍 Getting ARB balance for {user_address} from {arb_address}")
            
            # Test if ARB contract exists
            try:
                code = self.w3.eth.get_code(arb_address)
                if code == b'':
                    print(f"❌ No ARB contract deployed at {arb_address}")
                    return 0.0
            except Exception as code_err:
                print(f"❌ Error checking ARB contract code: {code_err}")
                return 0.0
            
            arb_contract = self.w3.eth.contract(
                address=arb_address, 
                abi=self.aave.erc20_abi
            )
                
            balance = arb_contract.functions.balanceOf(user_address).call()
            decimals = arb_contract.functions.decimals().call()
            
            formatted_balance = float(balance) / float(10 ** decimals)
            print(f"✅ ARB balance: {formatted_balance:.4f}")
            
            return formatted_balance
            
        except Exception as e:
            print(f"❌ Failed to get ARB balance: {e}")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   User address: {user_address}")
            print(f"   ARB address: {arb_address}")
            return 0.0
    
    def calculate_optimal_usdc_borrow(self, target_health_factor=1.19):
        """Calculate optimal USDC borrow amount to reach target health factor"""
        try:
            current_data = self.get_current_health_factor()
            if not current_data:
                return 0.0
            
            current_hf = current_data['health_factor']
            total_collateral_eth = current_data['total_collateral_eth']
            total_debt_eth = current_data['total_debt_eth']
            
            # Convert all values to float to avoid Decimal/float mixing
            # Handle Decimal, int, float, and string types safely
            try:
                current_hf = float(current_hf) if current_hf is not None else 0.0
            except (TypeError, ValueError):
                current_hf = 0.0
                
            try:
                total_collateral_eth = float(total_collateral_eth) if total_collateral_eth is not None else 0.0
            except (TypeError, ValueError):
                total_collateral_eth = 0.0
                
            try:
                total_debt_eth = float(total_debt_eth) if total_debt_eth is not None else 0.0
            except (TypeError, ValueError):
                total_debt_eth = 0.0
                
            target_health_factor = float(target_health_factor)
            
            # Simplified calculation: assuming 1 ETH = $2000, 1 USDC = $1
            # Target: (collateral * liquidation_threshold) / (total_debt + new_usdc_debt) = target_hf
            
            # Assume average liquidation threshold of 82.5% for WBTC/WETH/DAI mix
            liquidation_threshold = float(0.825)
            eth_price_usd = float(2000.0)  # Simplified assumption
            
            # Calculate how much USDC we can borrow to reach target health factor
            collateral_value_usd = total_collateral_eth * eth_price_usd
            current_debt_usd = total_debt_eth * eth_price_usd
            
            # (collateral_value * liq_threshold) / (current_debt + new_usdc_debt) = target_hf
            # new_usdc_debt = (collateral_value * liq_threshold) / target_hf - current_debt
            
            max_debt_for_target = (collateral_value_usd * liquidation_threshold) / target_health_factor
            optimal_usdc_borrow = max_debt_for_target - current_debt_usd
            
            return max(0.0, optimal_usdc_borrow)
            
        except Exception as e:
            print(f"❌ Failed to calculate optimal borrow: {e}")
            return 0.0
    
    def get_monitoring_summary(self):
        """Get comprehensive monitoring summary"""
        current_health = self.get_current_health_factor()
        current_arb_price = self.get_arb_price()
        arb_balance = self.get_arb_balance()
        
        borrow_trigger, hf_increase = self.check_health_factor_increase_trigger()
        risk_trigger, risk_data = self.check_risk_mitigation_trigger()
        
        optimal_borrow = self.calculate_optimal_usdc_borrow() if borrow_trigger else 0
        
        summary = {
            'current_health_factor': current_health['health_factor'] if current_health else 0,
            'arb_price': current_arb_price['price'] if current_arb_price else 0,
            'arb_balance': arb_balance,
            'borrow_trigger_active': borrow_trigger,
            'health_factor_increase': hf_increase,
            'risk_trigger_active': risk_trigger,
            'risk_data': risk_data,
            'optimal_usdc_borrow': optimal_borrow,
            'timestamp': time.time()
        }
        
        return summary
