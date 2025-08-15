#!/usr/bin/env python3
"""
Fixed OptimizedBalanceFetcher - Corrected method signatures
"""

import os
import requests
import time
from web3 import Web3

class OptimizedBalanceFetcher:
    def __init__(self, wallet_address):
        self.wallet_address = wallet_address
        self.arbiscan_api_key = os.getenv('ARBISCAN_API_KEY')
        self.zapper_api_key = os.getenv('ZAPPER_API_KEY')
        self.arbitrum_rpc = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')

        print(f"🔄 OptimizedBalanceFetcher initialized for {wallet_address}")
        print(f"   ARBISCAN_API_KEY: {'✅ Available' if self.arbiscan_api_key else '❌ Missing'}")
        print(f"   ARBITRUM_RPC_URL: {self.arbitrum_rpc}")
        print(f"   ZAPPER_API_KEY: {'✅ Available' if self.zapper_api_key else '❌ Missing'}")

    def get_token_balance(self, token_address):
        """Get token balance - fixed method signature"""
        try:
            # Method 1: Direct RPC call
            w3 = Web3(Web3.HTTPProvider(self.arbitrum_rpc))
            if w3.is_connected():
                balance = self._get_balance_via_rpc(w3, token_address)
                if balance is not None:
                    return balance

            # Method 2: Arbiscan API
            if self.arbiscan_api_key:
                balance = self._get_balance_via_arbiscan(token_address)
                if balance is not None:
                    return balance

            # Method 3: Return 0 as fallback
            print(f"⚠️ Could not fetch balance for {token_address}, returning 0")
            return 0.0

        except Exception as e:
            print(f"❌ Error getting token balance for {token_address}: {e}")
            return 0.0

    def _get_balance_via_rpc(self, w3, token_address):
        """Get balance via RPC call"""
        try:
            # ERC20 balanceOf ABI
            abi = [{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }, {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }]

            contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=abi
            )

            balance_wei = contract.functions.balanceOf(self.wallet_address).call()

            try:
                decimals = contract.functions.decimals().call()
            except:
                # Default decimals for common tokens
                if 'usdc' in token_address.lower():
                    decimals = 6
                elif 'wbtc' in token_address.lower():
                    decimals = 8
                else:
                    decimals = 18

            balance = balance_wei / (10 ** decimals)
            print(f"✅ RPC balance for {token_address}: {balance}")
            return balance

        except Exception as e:
            print(f"⚠️ RPC balance fetch failed for {token_address}: {e}")
            return None

    def _get_balance_via_arbiscan(self, token_address):
        """Get balance via Arbiscan API"""
        try:
            url = "https://api.arbiscan.io/api"
            params = {
                'module': 'account',
                'action': 'tokenbalance',
                'contractaddress': token_address,
                'address': self.wallet_address,
                'tag': 'latest',
                'apikey': self.arbiscan_api_key
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    balance_wei = int(data['result'])

                    # Determine decimals based on token
                    if 'usdc' in token_address.lower():
                        decimals = 6
                    elif 'wbtc' in token_address.lower():
                        decimals = 8
                    else:
                        decimals = 18

                    balance = balance_wei / (10 ** decimals)
                    print(f"✅ Arbiscan balance for {token_address}: {balance}")
                    return balance

            return None

        except Exception as e:
            print(f"⚠️ Arbiscan balance fetch failed for {token_address}: {e}")
            return None

    def get_comprehensive_wallet_data(self):
        """Get comprehensive wallet data"""
        try:
            # Token addresses for Arbitrum Mainnet
            tokens = {
                'WBTC': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',
                'USDC': '0xaf88d065e77c8cF0eAEFf3e253e648a15cEe23dC',
                'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
            }

            balances = {}
            for name, address in tokens.items():
                balances[name.lower() + '_balance'] = self.get_token_balance(address)

            # Get ETH balance
            try:
                w3 = Web3(Web3.HTTPProvider(self.arbitrum_rpc))
                eth_balance_wei = w3.eth.get_balance(self.wallet_address)
                balances['eth_balance'] = w3.from_wei(eth_balance_wei, 'ether')
            except:
                balances['eth_balance'] = 0.0

            return {
                'wallet_address': self.wallet_address,
                'success': True,
                'timestamp': time.time(),
                **balances
            }

        except Exception as e:
            print(f"❌ Comprehensive wallet data error: {e}")
            return {
                'wallet_address': self.wallet_address,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }

if __name__ == "__main__":
    # Test the fetcher
    wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    fetcher = OptimizedBalanceFetcher(wallet)

    # Test USDC balance
    usdc_address = "0xaf88d065e77c8cF0eAEFf3e253e648a15cEe23dC"
    balance = fetcher.get_token_balance(usdc_address)
    print(f"USDC Balance: {balance}")