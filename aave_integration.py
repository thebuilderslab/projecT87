` tag within the Python code. The task is to remove this tag to fix the error and generate the complete corrected code.

<replit_final_file>
import os
import json
import math
from web3 import Web3
from eth_account import Account
from config_constants import MIN_ETH_FOR_OPERATIONS
from dotenv import load_dotenv
import requests
import time

class AaveArbitrumIntegration:
    def __init__(self, w3, account):
        self.w3 = w3
        self.account = account
        self.address = account.address

        # Determine network based on chain ID
        chain_id = self.w3.eth.chain_id

        if chain_id == 42161:  # Arbitrum Mainnet
            print(f"🌐 Initializing for Arbitrum Mainnet (Chain ID: {chain_id})")
            # Aave V3 Arbitrum MAINNET Contract Addresses (verified deployed)
            self.pool_addresses_provider = self.w3.to_checksum_address("0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb")
            self.pool_address = self.w3.to_checksum_address("0x794a61358D6845594F94dc1DB02A252b5b4814aD")
            self.pool_data_provider = self.w3.to_checksum_address("0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654")
            # Token addresses for Arbitrum Mainnet (verified from CoinGecko and Aave docs)
            self.weth_address = self.w3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
            self.wbtc_address = self.w3.to_checksum_address("0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f")
            self.dai_address = self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
            # Arbitrum Mainnet token addresses - Use Native USDC for Aave V3
            self.usdc_address = self.w3.to_checksum_address("0xAF88D065e8c38FAD0AEff3E253e648A15ceE23DC")  # Native USDC (Aave V3 supported)
            self.usdc_native_address = self.w3.to_checksum_address("0xAF88D065e8c38FAD0AEff3E253e648A15ceE23DC")  # Native USDC
            self.arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        else:  # Arbitrum Sepolia Testnet (Chain ID: 421614)
            print(f"🧪 Initializing for Arbitrum Sepolia Testnet (Chain ID: {chain_id})")
            # Aave V3 Arbitrum SEPOLIA TESTNET Contract Addresses
            self.pool_addresses_provider = self.w3.to_checksum_address("0x0496275d34753A48320CA58103d5220d394FF77F")
            self.pool_address = self.w3.to_checksum_address("0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951")
            self.pool_data_provider = self.w3.to_checksum_address("0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654")
            # Token addresses on Arbitrum SEPOLIA TESTNET
            self.weth_address = self.w3.to_checksum_address("0x980B62Da83eFf3D4576C647993b0c1D7faf17c73")
            self.wbtc_address = self.w3.to_checksum_address("0x078f358208685046a11C85e8ad32895DED33A249")
            self.dai_address = self.w3.to_checksum_address("0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE")
            self.usdc_address = self.w3.to_checksum_address("0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d")
            self.arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        print(f"🪙 ARB Token Address (checksummed): {self.arb_address}")

        # Load ABIs
        self.pool_abi = self._get_pool_abi()
        self.erc20_abi = self._get_erc20_abi()

        # Initialize contracts
        self.pool_contract = self.w3.eth.contract(
            address=self.pool_address, 
            abi=self.pool_abi
        )

        # Alternative RPC endpoints for fallback (removed unauthorized endpoints)
        self.alternative_rpcs = [
            "https://arbitrum-one.publicnode.com",
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.public.blastapi.io"
        ]

        # API keys for external data sources
        self.arbiscan_api_key = os.getenv('ARBISCAN_API_KEY')

        # Verify all contract addresses are properly checksummed
        network_name = "Arbitrum Mainnet" if chain_id == 42161 else "Arbitrum Sepolia"
        print(f"🏦 Aave Integration - Contract Address Verification ({network_name}):")
        print(f"   Pool: {self.pool_address}")
        print(f"   Data Provider: {self.pool_data_provider}")
        print(f"   WETH: {self.weth_address}")
        print(f"   WBTC: {self.wbtc_address}")
        print(f"   DAI: {self.dai_address}")
        print(f"   USDC: {self.usdc_address}")
        print(f"   ARB: {self.arb_address}")

        # Validate that all addresses are properly checksummed
        addresses_to_check = [
            ("Pool", self.pool_address),
            ("WETH", self.weth_address),
            ("WBTC", self.wbtc_address),
            ("DAI", self.dai_address),
            ("USDC", self.usdc_address),
            ("ARB", self.arb_address)
        ]

        validation_passed = True
        for name, addr in addresses_to_check:
            if addr != self.w3.to_checksum_address(addr):
                print(f"❌ {name} address not properly checksummed: {addr}")
                validation_passed = False
            else:
                print(f"✅ {name} address properly checksummed")

        if validation_passed:
            print(f"✅ All contract addresses validated successfully for {network_name}")
        else:
            print(f"⚠️ Some address validation issues detected")

        print(f"🏦 Aave integration initialized for {self.address}")

    def _get_pool_abi(self):
        """Aave V3 Pool ABI (complete with getUserAccountData function)"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"},
                    {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
                ],
                "name": "supply",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                    {"internalType": "uint16", "name": "referralCode", "type": "uint16"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"}
                ],
                "name": "borrow",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "to", "type": "address"}
                ],
                "name": "withdraw",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"}
                ],
                "name": "repay",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "user", "type": "address"}
                ],
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

    def _get_erc20_abi(self):
        """Complete ERC20 ABI for token operations - Enhanced with USDC functionality"""
        return json.loads('''
            [{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"authorizer","type":"address"},{"indexed":true,"internalType":"bytes32","name":"nonce","type":"bytes32"}],"name":"AuthorizationCanceled","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"authorizer","type":"address"},{"indexed":true,"internalType":"bytes32","name":"nonce","type":"bytes32"}],"name":"AuthorizationUsed","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_account","type":"address"}],"name":"Blacklisted","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"newBlacklister","type":"address"}],"name":"BlacklisterChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"burner","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"newMasterMinter","type":"address"}],"name":"MasterMinterChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"minter","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"minter","type":"address"},{"indexed":false,"internalType":"uint256","name":"minterAllowedAmount","type":"uint256"}],"name":"MinterConfigured","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"oldMinter","type":"address"}],"name":"MinterRemoved","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":false,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[],"name":"Pause","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"newAddress","type":"address"}],"name":"PauserChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"newRescuer","type":"address"}],"name":"RescuerChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_account","type":"address"}],"name":"UnBlacklisted","type":"event"},{"anonymous":false,"inputs":[],"name":"Unpause","type":"event"},{"inputs":[],"name":"CANCEL_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"RECEIVE_WITH_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"TRANSFER_WITH_AUTHORIZATION_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"authorizer","type":"address"},{"internalType":"bytes32","name":"nonce","type":"bytes32"}],"name":"authorizationState","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_account","type":"address"}],"name":"blacklist","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"blacklister","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"authorizer","type":"address"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"cancelAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"authorizer","type":"address"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"cancelAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"minter","type":"address"},{"internalType":"uint256","name":"minterAllowedAmount","type":"uint256"}],"name":"configureMinter","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"currency","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"decrement","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"increment","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"tokenName","type":"string"},{"internalType":"string","name":"tokenSymbol","type":"string"},{"internalType":"string","name":"tokenCurrency","type":"string"},{"internalType":"uint8","name":"tokenDecimals","type":"uint8"},{"internalType":"address","name":"newMasterMinter","type":"address"},{"internalType":"address","name":"newPauser","type":"address"},{"internalType":"address","name":"newBlacklister","type":"address"},{"internalType":"address","name":"newOwner","type":"address"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"newName","type":"string"}],"name":"initializeV2","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"lostAndFound","type":"address"}],"name":"initializeV2_1","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address[]","name":"accountsToBlacklist","type":"address[]"},{"internalType":"string","name":"newSymbol","type":"string"}],"name":"initializeV2_2","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_account","type":"address"}],"name":"isBlacklisted","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"isMinter","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"masterMinter","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_to","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"mint","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"minter","type":"address"}],"name":"minterAllowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"paused","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pauser","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"receiveWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"receiveWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"minter","type":"address"}],"name":"removeMinter","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IERC20","name":"tokenContract","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"rescueERC20","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"rescuer","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"transferWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"validAfter","type":"uint256"},{"internalType":"uint256","name":"validBefore","type":"uint256"},{"internalType":"bytes32","name":"nonce","type":"bytes32"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"transferWithAuthorization","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_account","type":"address"}],"name":"unBlackList","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"unpause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_newBlacklister","type":"address"}],"name":"updateBlacklister","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_newMasterMinter","type":"address"}],"name":"updateMasterMinter","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_newPauser","type":"address"}],"name":"updatePauser","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newRescuer","type":"address"}],"name":"updateRescuer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"}]
        ''')

    def get_arbiscan_token_balance(self, token_address: str) -> float:
        """Get token balance via Arbiscan API with fallback to screenshot data"""
        try:
            print(f"🔄 Trying Arbiscan API for token {token_address}")

            url = "https://api.arbiscan.io/api"
            params = {
                'module': 'account',
                'action': 'tokenbalance',
                'contractaddress': token_address,
                'address': self.address,
                'tag': 'latest'
            }

            # Add API key if available
            if self.arbiscan_api_key:
                params['apikey'] = self.arbiscan_api_key

            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1' and data.get('result'):
                    balance_wei = int(data.get('result', '0'))

                    # Get decimals for this token
                    decimals = 18  # Default
                    if token_address.lower() == self.usdc_address.lower():
                        decimals = 6
                    elif token_address.lower() == self.wbtc_address.lower():
                        decimals = 8

                    balance = balance_wei / (10 ** decimals)
                    print(f"✅ Arbiscan balance: {balance:.6f}")
                    return balance
                else:
                    print(f"⚠️ Arbiscan API response: {data}")
            else:
                print(f"❌ Arbiscan HTTP error: {response.status_code}")

        except Exception as e:
            print(f"❌ Arbiscan balance failed: {e}")

        # Fallback to known wallet data from screenshot
        known_balances = {
            self.wbtc_address.lower(): 0.0002,
            self.weth_address.lower(): 0.00193518,
            self.usdc_address.lower(): 0.0
        }

        fallback_balance = known_balances.get(token_address.lower(), 0.0)
        if fallback_balance > 0:
            print(f"📸 Using screenshot data for {token_address}: {fallback_balance}")
            return fallback_balance

        return -1

    def get_token_balance_with_alternative_rpc(self, token_address: str) -> float:
        """Try alternative RPC endpoints for token balance"""
        for rpc_url in self.alternative_rpcs:
            try:
                print(f"🔄 Trying alternative RPC: {rpc_url}")

                temp_w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                if not temp_w3.is_connected():
                    print(f"❌ RPC not connected: {rpc_url}")
                    continue

                if temp_w3.eth.chain_id != 42161:
                    print(f"❌ Wrong chain ID for {rpc_url}")
                    continue

                # Create contract with alternative RPC
                token_contract = temp_w3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.erc20_abi
                )

                # Get balance
                balance_wei = token_contract.functions.balanceOf(self.address).call()

                # Get decimals
                try:
                    decimals = token_contract.functions.decimals().call()
                except:
                    # Use known decimals
                    if token_address.lower() == self.usdc_address.lower():
                        decimals = 6
                    elif token_address.lower() == self.wbtc_address.lower():
                        decimals = 8
                    else:
                        decimals = 18

                balance = balance_wei / (10 ** decimals)
                print(f"✅ Alternative RPC success: {balance:.6f}")
                return balance

            except Exception as e:
                print(f"❌ Alternative RPC {rpc_url} failed: {e}")
                continue

        return -1

    def get_token_balance(self, token_address):
        """Get token balance for the user's address"""
        try:
            # Use optimized balance fetcher
            from optimized_balance_fetcher import OptimizedBalanceFetcher

            fetcher = OptimizedBalanceFetcher(self.account.address)
            balance = fetcher.get_token_balance(token_address)

            return balance

        except Exception as e:
            print(f"❌ Error getting token balance for {token_address}: {e}")
            return 0.0

    def get_supplied_balance(self, token_address):
        """Get the amount of tokens supplied to Aave for this asset with enhanced error handling"""
        try:
            print(f"🔍 Getting supplied balance for token: {token_address}")

            # Comprehensive aToken mapping for Arbitrum Mainnet
            atoken_mapping = {
                self.usdc_address.lower(): "0x724dc807b04555b71ed48a6896b6F41593b8C637",  # aUSDC for Native USDC 0xAF88D065e8c38FAD0AEff3E253e648A15ceE23DC
                self.wbtc_address.lower(): "0x6533afac2E7BCCB20dca161449A13A2D2d5B739A",  # aArbWBTC  
                self.weth_address.lower(): "0xe50fA9b4c56454E2edF6BFf7c81b50c5F05aBE61",  # aArbWETH
                self.dai_address.lower(): "0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE"   # aArbDAI
            }

            atoken_address = atoken_mapping.get(token_address.lower())
            if not atoken_address:
                print(f"⚠️ No aToken mapping found for {token_address}")
                return 0.0

            print(f"📍 Using aToken address: {atoken_address}")

            # Enhanced aToken ABI with multiple function signatures
            enhanced_atoken_abi = [
                {
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf", 
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "stateMutability": "view", 
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]

            # Multiple RPC attempt strategy
            rpcs_to_try = [
                self.w3,  # Current primary
                *[Web3(Web3.HTTPProvider(rpc)) for rpc in self.alternative_rpcs[:2]]  # Top 2 fallbacks
            ]

            for attempt, w3_instance in enumerate(rpcs_to_try):
                try:
                    if not w3_instance.is_connected():
                        continue

                    print(f"🔄 Attempt {attempt + 1}: Using RPC endpoint")

                    # Create contract with enhanced error checking
                    atoken_contract = w3_instance.eth.contract(
                        address=w3_instance.to_checksum_address(atoken_address),
                        abi=enhanced_atoken_abi
                    )

                    # Verify contract exists
                    try:
                        symbol = atoken_contract.functions.symbol().call()
                        print(f"✅ Contract verified: {symbol}")
                    except:
                        print(f"⚠️ Contract verification failed, proceeding anyway")

                    # Get balance with timeout
                    user_address = w3_instance.to_checksum_address(self.address)
                    balance_wei = atoken_contract.functions.balanceOf(user_address).call()

                    # Get decimals from aToken contract directly
                    try:
                        decimals = atoken_contract.functions.decimals().call()
                    except:
                        # Fallback to underlying token decimals
                        decimals = self._get_token_decimals(token_address)

                    balance = balance_wei / (10 ** decimals)

                    print(f"✅ Successfully retrieved balance: {balance:.8f}")
                    return balance

                except Exception as rpc_error:
                    print(f"❌ RPC attempt {attempt + 1} failed: {rpc_error}")
                    continue

            # If all RPC attempts fail, return 0 but don't crash
            print(f"⚠️ All RPC attempts failed for {token_address}, returning 0")
            return 0.0

        except Exception as e:
            print(f"❌ Critical error in get_supplied_balance for {token_address}: {e}")
            return 0.0

    def get_zapper_fallback_balance(self, token_address: str) -> float:
        """Zapper API fallback using known wallet data"""
        try:
            # Known current balances from DeBank
            known_balances = {
                self.usdc_address.lower(): 0.0,
                self.wbtc_address.lower(): 0.0002,
                self.weth_address.lower(): 0.00193518
            }
            return known_balances.get(token_address.lower(), -1)

        except Exception as e:
            print(f"❌ Zapper fallback failed: {e}")
            return -1

    def _get_balance_current_rpc_enhanced(self, token_address):
        """Enhanced balance retrieval with current RPC"""
        try:
            token_address = Web3.to_checksum_address(token_address)
            user_address = Web3.to_checksum_address(self.address)

            # Multiple retry strategies
            strategies = [
                lambda: self._direct_contract_call(token_address, user_address),
                lambda: self._low_level_call(token_address, user_address),
                lambda: self._batch_call(token_address, user_address)
            ]

            for i, strategy in enumerate(strategies):
                try:
                    print(f"🔄 Strategy {i+1} for token balance...")
                    balance = strategy()
                    if balance >= 0:
                        return balance
                except Exception as e:
                    print(f"❌ Strategy {i+1} failed: {e}")
                    continue

            return -1

        except Exception as e:
            print(f"❌ Enhanced RPC balance failed: {e}")
            return -1

    def _direct_contract_call(self, token_address, user_address):
        """Direct contract call method"""
        token_contract = self.w3.eth.contract(
            address=token_address,
            abi=self.erc20_abi
        )

        # Get decimals with fallback
        try:
            decimals = token_contract.functions.decimals().call()
        except:
            decimals = self._get_known_decimals(token_address)

        # Get balance with timeout
        balance_wei = token_contract.functions.balanceOf(user_address).call()
        balance = float(balance_wei) / float(10 ** decimals)

        print(f"✅ Direct contract call successful: {balance:.6f}")
        return balance

    def _low_level_call(self, token_address, user_address):
        """Low-level call method"""
        # balanceOf function selector: 0x70a08231
        function_selector = "0x70a08231"
        padded_address = user_address[2:].zfill(64)
        data = function_selector + padded_address

        result = self.w3.eth.call({
            'to': token_address,
            'data': data
        })

        balance_wei = int(result.hex(), 16)
        decimals = self._get_known_decimals(token_address)
        balance = float(balance_wei) / float(10 ** decimals)

        print(f"✅ Low-level call successful: {balance:.6f}")
        return balance

    def _batch_call(self, token_address, user_address):
        """Batch call method (if supported)"""
        # This is a placeholder for batch call implementation
        # For now, fall back to direct call
        return self._direct_contract_call(token_address, user_address)

    def _get_known_decimals(self, token_address):
        """Get known decimals for common tokens"""
        token_decimals = {
            self.usdc_address.lower(): 6,
            self.wbtc_address.lower(): 8,
            self.weth_address.lower(): 18,
            self.dai_address.lower(): 18,
            self.arb_address.lower(): 18
        }
        return token_decimals.get(token_address.lower(), 18)

    def get_user_account_data(self):
        """Get user account data from Aave with error handling"""
        try:
            # Call getUserAccountData directly
            account_data = self.pool_contract.functions.getUserAccountData(self.address).call()

            # Parse the returned data (Aave V3 format)
            total_collateral_usd = account_data[0] / (10**8)  # Convert from 8 decimals
            total_debt_usd = account_data[1] / (10**8)
            available_borrows_usd = account_data[2] / (10**8)
            liquidation_threshold = account_data[3] / 10000  # Convert from basis points
            ltv = account_data[4] / 10000
            health_factor_raw = account_data[5]

            # Handle health factor (infinity if no debt)
            if health_factor_raw >= 2**256 - 1:
                health_factor = float('inf')
            else:
                health_factor = health_factor_raw / (10**18)

            return {
                'totalCollateralUSD': total_collateral_usd,
                'totalDebtUSD': total_debt_usd,
                'availableBorrowsUSD': available_borrows_usd,
                'currentLiquidationThreshold': liquidation_threshold,
                'ltv': ltv,
                'healthFactor': health_factor,
                'success': True
            }

        except Exception as e:
            print(f"❌ Failed to get user account data: {e}")
            return {
                'totalCollateralUSD': 0,
                'totalDebtUSD': 0,
                'availableBorrowsUSD': 0,
                'healthFactor': float('inf'),
                'success': False,
                'error': str(e)
            }

    def get_optimized_gas_params(self, operation_type='default', market_condition='normal'):
        """Get optimized gas parameters for transactions"""
        try:
            # Base gas price from network
            base_gas_price = self.w3.eth.gas_price

            # Gas limits for different operations
            gas_limits = {
                'approve_token': 60000,
                'aave_supply': 150000,
                'aave_borrow': 180000,
                'aave_repay': 160000,
                'uniswap_swap': 120000,
                'default': 200000
            }

            # Market condition multipliers
            multipliers = {
                'normal': 1.2,
                'volatile': 1.5,
                'urgent': 2.0,
                'market': 1.3
            }

            gas_limit = gas_limits.get(operation_type, gas_limits['default'])
            multiplier = multipliers.get(market_condition, 1.2)

            return {
                'gas': gas_limit,
                'gasPrice': int(base_gas_price * multiplier)
            }

        except Exception as e:
            print(f"⚠️ Gas parameter calculation failed: {e}")
            return {
                'gas': 200000,
                'gasPrice': 100000000  # 0.1 gwei fallback
            }

    def _convert_usd_to_wei(self, amount_usd, token_address):
        """Convert USD amount to wei for the specified token"""
        try:
            # Get token decimals
            decimals = self._get_known_decimals(token_address)

            # For USDC, 1 USD = 1 USDC (approximately)
            if token_address.lower() == self.usdc_address.lower():
                amount_wei = int(amount_usd * (10 ** decimals))
                print(f"✅ USDC conversion: ${amount_usd} = {amount_wei} wei")
                return amount_wei
            # For DAI, 1 USD ≈ 1 DAI (stablecoin peg)
            elif token_address.lower() == self.dai_address.lower():
                amount_wei = int(amount_usd * (10 ** decimals))
                print(f"✅ DAI borrowing enabled: ${amount_usd} = {amount_wei} DAI wei")
                return amount_wei
            else:
                # For other tokens, would need price conversion
                print(f"⚠️ USD to wei conversion not implemented for token: {token_address}")
                # Return 0 instead of raising error to allow fallback
                return 0

        except Exception as e:
            print(f"❌ USD to wei conversion failed: {e}")
            return 0

    def approve_token(self, token_address, amount):
        """Approve token spending for Aave"""
        try:
            # Ensure all addresses are properly checksummed
            token_address = self.w3.to_checksum_address(token_address)

            if hasattr(self.account, 'address'):
                user_address = self.w3.to_checksum_address(self.account.address)
            else:
                user_address = self.w3.to_checksum_address(self.address)

            token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)

            # Validate that the approve function exists in the contract
            if not hasattr(token_contract.functions, 'approve'):
                raise ValueError(f"Token contract at {token_address} does not have approve function")

            # Get the approve function to validate its signature
            approve_function = token_contract.functions.approve
            print(f"🔍 Contract function validation:")
            print(f"   Token contract: {token_address}")
            print(f"   Approve function found: ✅")
            print(f"   Function object: {approve_function}")

            # SMART approval amount based on token balance and use case
            try:
                # Get current token balance
                current_balance = token_contract.functions.balanceOf(user_address).call()
                decimals = token_contract.functions.decimals().call()
            except:
                # Fallback decimals based on known tokens
                if token_address.lower() == self.usdc_address.lower():
                    decimals = 6
                elif token_address.lower() == self.wbtc_address.lower():
                    decimals = 8
                else:
                    decimals = 18
                current_balance = 0

            if amount >= 2**255:  # Very large amount requested
        
            

            # First approve WBTC spending for Aave pool
            print(f"🔓 Approving WBTC for Aave pool...")
            approval_tx = self.approve_token(self.wbtc_address, wbtc_amount)
            if not approval_tx:
                print(f"❌ WBTC approval failed")
                return None

            print(f"✅ WBTC approved: {approval_tx}")

            # Wait for approval confirmation
            import time
            time.sleep(5)

            # Convert WBTC amount to wei (WBTC has 8 decimals)
            wbtc_amount_wei = int(wbtc_amount * (10 ** 8))
            print(f"💱 WBTC amount in wei: {wbtc_amount_wei}")

            # Supply WBTC to Aave
            supply_tx = self.supply_to_aave(self.wbtc_address, wbtc_amount)
            if supply_tx:
                print(f"✅ WBTC supplied to Aave: {supply_tx}")
                return supply_tx
            else:
                print(f"❌ WBTC supply failed")
                return None

        except Exception as e:
            print(f"❌ Supply WBTC to Aave failed: {e}")
            import traceback
            print(f"🔍 Full error trace: {traceback.format_exc()}")
            return None

    def _get_token_decimals(self, token_address):
        """Get token decimals with fallback to known values"""
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
            return token_contract.functions.decimals().call()
        except:
            # Fallback to known decimals
            known_decimals = {
                self.usdc_address.lower(): 6,
                self.wbtc_address.lower(): 8,
                self.weth_address.lower(): 18,
                self.dai_address.lower(): 18
            }
            return known_decimals.get(token_address.lower(), 18)