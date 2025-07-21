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

            # Get current allowance
            current_allowance = token_contract.functions.allowance(user_address, self.pool_address).call()

            # If already approved for requested amount or more, skip
            if current_allowance >= amount:
                print(f"✅ Token already approved: {current_allowance} >= {amount}")
                return True

            # Build approval transaction
            approve_txn = token_contract.functions.approve(
                self.pool_address,
                amount
            ).build_transaction({
                'from': user_address,
                'gas': 60000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(user_address)
            })

            # Sign and send transaction
            signed_txn = self.account.sign_transaction(approve_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            print(f"✅ Approval transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            print(f"❌ Token approval failed: {e}")
            return None

    def supply_to_aave(self, token_address, amount):
        """Supply tokens to Aave"""
        try:
            # Approve token first
            approval_result = self.approve_token(token_address, int(amount * (10 ** self._get_token_decimals(token_address))))
            if not approval_result:
                print(f"❌ Token approval failed for supply")
                return None

            # Convert amount to wei
            decimals = self._get_token_decimals(token_address)
            amount_wei = int(amount * (10 ** decimals))

            # Build supply transaction
            supply_txn = self.pool_contract.functions.supply(
                token_address,
                amount_wei,
                self.address,
                0  # referral code
            ).build_transaction({
                'from': self.address,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address)
            })

            # Sign and send transaction
            signed_txn = self.account.sign_transaction(supply_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            print(f"✅ Supply transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            print(f"❌ Supply failed: {e}")
            return None

    def borrow(self, amount_usd, token_address):
        """Borrow tokens from Aave"""
        try:
            # Convert USD amount to token amount
            amount_wei = self._convert_usd_to_wei(amount_usd, token_address)
            if amount_wei == 0:
                print(f"❌ Invalid borrow amount: {amount_usd} USD")
                return None

            # Build borrow transaction
            borrow_txn = self.pool_contract.functions.borrow(
                token_address,
                amount_wei,
                2,  # Variable interest rate mode
                0,  # referral code
                self.address
            ).build_transaction({
                'from': self.address,
                'gas': 180000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address)
            })

            # Sign and send transaction
            signed_txn = self.account.sign_transaction(borrow_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            print(f"✅ Borrow transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            print(f"❌ Borrow failed: {e}")
            return None

    def supply_wbtc_to_aave(self, wbtc_amount):
        """Supply WBTC to Aave with enhanced validation"""
        try:
            print(f"🏦 Supplying WBTC to Aave: {wbtc_amount:.8f} WBTC")

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

    def _convert_usd_to_wei(self, amount_usd, token_address):
        """Convert USD amount to wei for the specified token"""
        try:
            # Get token decimals
            decimals = self._get_token_decimals(token_address)

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