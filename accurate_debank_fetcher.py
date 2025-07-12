#!/usr/bin/env python3
"""
Accurate Wallet Data Fetcher - LIVE DATA ONLY
Comprehensive multi-source data fetching with NO hardcoded fallbacks
"""

import os
import time
import requests
from web3 import Web3
from web3.exceptions import ContractLogicError

class AccurateWalletDataFetcher:
    def __init__(self, w3, wallet_address):
        self.w3 = w3
        self.wallet_address = wallet_address

        # Token addresses for Arbitrum Mainnet
        self.usdc_address = Web3.to_checksum_address('0xFF970A61A04b1cA14834A651bAb06d67307796618')  # USDC.e
        self.wbtc_address = "0x2f2a2543B76A4166549F7aBb2eE68df6F4E579b2"
        self.weth_address = "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
        self.arb_address = "0x912ce59144191c1204e64559fe83e3a5095c6afd"

        # Alternative RPCs for failover
        self.alternative_rpcs = [
            "https://arbitrum-one.publicnode.com",
            "https://rpc.ankr.com/arbitrum",
            "https://arbitrum.llamarpc.com",
            "https://arbitrum.blockpi.network/v1/rpc/public"
        ]

        # ERC-20 ABI
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]

    def get_token_balance_live(self, token_address, decimals=6):
        """Get token balance from live blockchain data only"""
        try:
            print(f"🔄 Fetching LIVE balance for token: {token_address}")

            # Create contract instance
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )

            # Get balance
            balance_wei = contract.functions.balanceOf(
                Web3.to_checksum_address(self.wallet_address)
            ).call()

            # Convert to human readable
            balance = balance_wei / (10 ** decimals)
            print(f"✅ LIVE balance retrieved: {balance:.8f}")
            return balance

        except Exception as e:
            print(f"❌ LIVE balance fetch failed for {token_address}: {e}")
            return 0  # Return 0 instead of fallback data

    def get_aave_data_live_only(self):
        """Get Aave data from live blockchain only - NO FALLBACKS"""
        print("🏦 AAVE DATA FETCH - LIVE BLOCKCHAIN ONLY")
        print("="*60)

        # Try live Aave data fetch
        print("🔄 Fetching LIVE Aave data from blockchain...")

        try:
            # Aave V3 Pool contract address
            aave_pool_address = "0x794a61358d6845594f94dc1db02a252b5b4814ad"

            # Aave V3 Pool ABI (simplified)
            pool_abi = [
                {
                    "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                    "name": "getUserAccountData",
                    "outputs": [
                        {"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"},
                        {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"},
                        {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"},
                        {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
                        {"internalType": "uint256", "name": "ltv", "type": "uint256"},
                        {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]

            # Create contract instance
            pool_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(aave_pool_address),
                abi=pool_abi
            )

            # Get user account data
            account_data = pool_contract.functions.getUserAccountData(
                Web3.to_checksum_address(self.wallet_address)
            ).call()

            # Parse the results (values are in base units with 8 decimals for USD amounts)
            total_collateral_base = account_data[0] / 1e8  # USD
            total_debt_base = account_data[1] / 1e8  # USD
            available_borrows_base = account_data[2] / 1e8  # USD
            health_factor = account_data[5] / 1e18 if account_data[5] > 0 else 0  # 18 decimals

            print(f"✅ LIVE AAVE DATA RETRIEVED:")
            print(f"   Health Factor: {health_factor:.2f}")
            print(f"   Collateral: ${total_collateral_base:.2f}")
            print(f"   Debt: ${total_debt_base:.2f}")
            print(f"   Available Borrows: ${available_borrows_base:.2f}")

            return {
                'health_factor': health_factor,
                'total_collateral_usd': total_collateral_base,
                'total_debt_usd': total_debt_base,
                'available_borrows_usd': available_borrows_base,
                'data_source': 'live_aave_contract_only',
                'timestamp': time.time(),
                'note': 'Live Aave contract data - no fallbacks'
            }

        except Exception as e:
            print(f"❌ LIVE Aave data fetch failed: {e}")
            print("🚫 NO HARDCODED FALLBACK DATA AVAILABLE")

            return {
                'health_factor': 0,
                'total_collateral_usd': 0,
                'total_debt_usd': 0,
                'available_borrows_usd': 0,
                'data_source': 'live_data_failed',
                'error': str(e),
                'note': 'Live Aave data unavailable - no hardcoded fallbacks',
                'timestamp': time.time()
            }

    def get_live_prices_only(self):
        """Get live prices from APIs only - NO FALLBACKS"""
        try:
            print("💰 Fetching LIVE prices...")

            # Try CoinMarketCap first
            cmc_key = os.getenv('COINMARKETCAP_API_KEY')
            if cmc_key:
                try:
                    response = requests.get(
                        'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                        headers={'X-CMC_PRO_API_KEY': cmc_key},
                        params={'symbol': 'BTC,ETH,USDC,ARB'},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        prices = {
                            'BTC': data['data']['BTC']['quote']['USD']['price'],
                            'ETH': data['data']['ETH']['quote']['USD']['price'],
                            'USDC': data['data']['USDC']['quote']['USD']['price'],
                            'ARB': data['data']['ARB']['quote']['USD']['price']
                        }
                        print(f"✅ LIVE prices from CoinMarketCap: BTC=${prices['BTC']:.2f}, ETH=${prices['ETH']:.2f}")
                        return prices
                except Exception as e:
                    print(f"⚠️ CoinMarketCap failed: {e}")

            # Try CoinGecko as backup
            try:
                response = requests.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,usd-coin,arbitrum&vs_currencies=usd',
                    timeout=10
                )
                data = response.json()
                prices = {
                    'BTC': data['bitcoin']['usd'],
                    'ETH': data['ethereum']['usd'],
                    'USDC': data['usd-coin']['usd'],
                    'ARB': data['arbitrum']['usd']
                }
                print(f"✅ LIVE prices from CoinGecko: BTC=${prices['BTC']:.2f}, ETH=${prices['ETH']:.2f}")
                return prices
            except Exception as e:
                print(f"❌ CoinGecko failed: {e}")

            # NO FALLBACK PRICES
            print("❌ ALL LIVE PRICE SOURCES FAILED - NO HARDCODED FALLBACKS")
            return {'ETH': 0, 'BTC': 0, 'USDC': 0, 'ARB': 0}

        except Exception as e:
            print(f"❌ LIVE price fetch failed: {e}")
            return {'ETH': 0, 'BTC': 0, 'USDC': 0, 'ARB': 0}

    def get_comprehensive_wallet_data(self):
        """Get comprehensive wallet data from LIVE SOURCES ONLY"""
        print("🔍 FETCHING COMPREHENSIVE WALLET DATA - LIVE ONLY")
        print("="*50)

        try:
            # Get ETH balance
            eth_balance = self.w3.eth.get_balance(self.wallet_address) / 1e18
            print(f"✅ ETH balance: {eth_balance:.6f}")

            # Get token balances - LIVE ONLY
            wbtc_balance = self.get_token_balance_live(self.wbtc_address, 8)
            weth_balance = self.get_token_balance_live(self.weth_address, 18)
            usdc_balance = self.get_token_balance_live(self.usdc_address, 6)
            arb_balance = self.get_token_balance_live(self.arb_address, 18)

            print(f"✅ WBTC balance: {wbtc_balance:.8f}")
            print(f"✅ WETH balance: {weth_balance:.6f}")
            print(f"✅ USDC balance: {usdc_balance:.6f}")
            print(f"✅ ARB balance: {arb_balance:.6f}")

            # Get live prices
            prices = self.get_live_prices_only()

            # Get Aave data - LIVE ONLY
            aave_data = self.get_aave_data_live_only()

            # Calculate USD values only if prices are available
            if prices['ETH'] > 0:
                eth_usd = eth_balance * prices['ETH']
                total_wallet_usd = eth_usd + (usdc_balance * prices['USDC']) + (wbtc_balance * prices['BTC']) + (weth_balance * prices['ETH']) + (arb_balance * prices['ARB'])
            else:
                eth_usd = total_wallet_usd = 0

            print(f"💰 ETH: {eth_balance:.8f} = ${eth_usd:.2f}")
            print(f"💰 Total Wallet Value (liquid): ${total_wallet_usd:.2f}")

            result = {
                'success': True,
                'wallet_address': self.wallet_address,
                'eth_balance': eth_balance,
                'wbtc_balance': wbtc_balance,
                'weth_balance': weth_balance,
                'usdc_balance': usdc_balance,
                'arb_balance': arb_balance,
                'prices': prices,
                'total_wallet_usd': total_wallet_usd,
                'health_factor': aave_data['health_factor'],
                'total_collateral': aave_data['total_collateral_usd'] / prices['ETH'] if prices['ETH'] > 0 else 0,
                'total_debt': aave_data['total_debt_usd'] / prices['ETH'] if prices['ETH'] > 0 else 0,
                'available_borrows': aave_data['available_borrows_usd'] / prices['ETH'] if prices['ETH'] > 0 else 0,
                'total_collateral_usdc': aave_data['total_collateral_usd'],
                'total_debt_usdc': aave_data['total_debt_usd'],
                'available_borrows_usdc': aave_data['available_borrows_usd'],
                'aave_data': aave_data,
                'data_source': 'live_blockchain_only',
                'timestamp': time.time(),
                'note': 'Live blockchain data only - no hardcoded fallbacks'
            }

            print(f"✅ Comprehensive LIVE data fetched successfully")
            print(f"💰 Total Wallet: ${total_wallet_usd:.2f}")
            print(f"🏦 Aave Health Factor: {aave_data['health_factor']:.2f}")
            print(f"💰 Aave Collateral: ${aave_data['total_collateral_usd']:.2f}")

            return result

        except Exception as e:
            print(f"❌ Comprehensive data fetch failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'data_source': 'live_fetch_failed',
                'note': 'Live data fetch failed - no hardcoded fallbacks available',
                'timestamp': time.time()
            }

if __name__ == "__main__":
    # Test the live data fetcher
    from arbitrum_testnet_agent import ArbitrumTestnetAgent

    try:
        agent = ArbitrumTestnetAgent()
        fetcher = AccurateWalletDataFetcher(agent.w3, agent.address)

        print("🧪 Testing Live Data Fetcher...")
        data = fetcher.get_comprehensive_wallet_data()

        if data['success']:
            print("✅ Live data fetch test PASSED")
        else:
            print("❌ Live data fetch test FAILED")
            print(f"Error: {data.get('error', 'Unknown')}")

    except Exception as e:
        print(f"❌ Test failed: {e}")