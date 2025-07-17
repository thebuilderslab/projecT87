
#!/usr/bin/env python3
"""
ENHANCED RPC MANAGER
Multiple fallback mechanisms for reliable blockchain connectivity
"""

import os
import time
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware

class EnhancedRPCManager:
    def __init__(self):
        self.arbitrum_mainnet_rpcs = [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.publicnode.com",
            "https://arbitrum.llamarpc.com",
            "https://rpc.ankr.com/arbitrum",
            "https://arbitrum-one.public.blastapi.io",
            "https://endpoints.omniatech.io/v1/arbitrum/one/public",
            "https://arbitrum.blockpi.network/v1/rpc/public"
        ]
        
        self.working_rpc = None
        self.w3 = None
        
    def find_working_rpc(self, max_retries=3):
        """Find a working RPC endpoint with comprehensive testing and retries"""
        print("🔍 Testing RPC endpoints for reliability...")
        
        for attempt in range(max_retries):
            for rpc_url in self.arbitrum_mainnet_rpcs:
                if self.test_rpc_endpoint(rpc_url):
                    self.working_rpc = rpc_url
                    # Enhanced connection settings for reliability
                    self.w3 = Web3(Web3.HTTPProvider(
                        rpc_url, 
                        request_kwargs={
                            'timeout': 30,
                            'headers': {
                                'User-Agent': 'ArbitrumAgent/1.0',
                                'Connection': 'keep-alive'
                            }
                        }
                    ))
                    self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    print(f"✅ Using RPC: {rpc_url}")
                    return True
            
            if attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1} failed, retrying in 2 seconds...")
                time.sleep(2)
        
        print("❌ No working RPC endpoints found after all retries")
        return False
    
    def test_rpc_endpoint(self, rpc_url, timeout=15):
        """Test RPC endpoint with multiple checks and timeout handling"""
        try:
            # Enhanced connection with timeout and retry settings
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            import requests
            
            session = requests.Session()
            retry_strategy = Retry(
                total=2,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 523, 524],
                method_whitelist=["HEAD", "GET", "POST"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Test 1: Basic connectivity with session
            w3 = Web3(Web3.HTTPProvider(
                rpc_url, 
                request_kwargs={
                    'timeout': timeout,
                    'headers': {'User-Agent': 'ArbitrumAgent/1.0'}
                },
                session=session
            ))
            
            if not w3.is_connected():
                return False
            
            # Test 2: Chain ID verification with timeout
            start_time = time.time()
            chain_id = w3.eth.chain_id
            if time.time() - start_time > timeout:
                print(f"❌ RPC {rpc_url} chain_id call timeout")
                return False
                
            if chain_id != 42161:  # Arbitrum mainnet
                return False
            
            # Test 3: Latest block with timeout
            start_time = time.time()
            latest_block = w3.eth.get_block('latest')
            if time.time() - start_time > timeout:
                print(f"❌ RPC {rpc_url} get_block call timeout")
                return False
                
            if not latest_block or latest_block.number < 1000000:
                return False
            
            # Test 4: Gas price with timeout
            start_time = time.time()
            gas_price = w3.eth.gas_price
            if time.time() - start_time > timeout:
                print(f"❌ RPC {rpc_url} gas_price call timeout")
                return False
                
            if not gas_price or gas_price <= 0:
                return False
            
            response_time = time.time() - start_time
            print(f"✅ RPC {rpc_url} passed all tests ({response_time:.2f}s)")
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ RPC {rpc_url} failed: Connection timeout")
            return False
        except requests.exceptions.ConnectionError:
            print(f"❌ RPC {rpc_url} failed: Connection error")
            return False
        except Exception as e:
            print(f"❌ RPC {rpc_url} failed: {e}")
            return False
    
    def get_token_balance_with_fallbacks(self, token_address, wallet_address):
        """Get token balance with multiple fallback methods"""
        if not self.w3:
            if not self.find_working_rpc():
                return 0.0
        
        # Method 1: Standard ERC20 balanceOf call
        try:
            balance = self.get_erc20_balance(token_address, wallet_address)
            if balance is not None:
                return balance
        except Exception as e:
            print(f"⚠️ Method 1 failed: {e}")
        
        # Method 2: Low-level eth_call
        try:
            balance = self.get_balance_low_level(token_address, wallet_address)
            if balance is not None:
                return balance
        except Exception as e:
            print(f"⚠️ Method 2 failed: {e}")
        
        # Method 3: Try different RPC endpoints
        for rpc_url in self.arbitrum_mainnet_rpcs:
            if rpc_url != self.working_rpc:
                try:
                    balance = self.get_balance_different_rpc(token_address, wallet_address, rpc_url)
                    if balance is not None:
                        return balance
                except Exception as e:
                    continue
        
        return 0.0
    
    def get_erc20_balance(self, token_address, wallet_address):
        """Standard ERC20 balance check"""
        erc20_abi = [{
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
        
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=erc20_abi
        )
        
        # Get balance and decimals
        balance_wei = contract.functions.balanceOf(wallet_address).call()
        try:
            decimals = contract.functions.decimals().call()
        except:
            decimals = 6  # USDC default
        
        return balance_wei / (10 ** decimals)
    
    def get_balance_low_level(self, token_address, wallet_address):
        """Low-level eth_call for balance"""
        # ERC20 balanceOf function signature
        function_signature = "0x70a08231"  # balanceOf(address)
        
        # Pad wallet address to 32 bytes
        padded_address = wallet_address[2:].zfill(64)
        
        # Construct call data
        call_data = function_signature + padded_address
        
        # Make the call
        result = self.w3.eth.call({
            'to': Web3.to_checksum_address(token_address),
            'data': call_data
        })
        
        if result and result != b'':
            balance_wei = int.from_bytes(result, byteorder='big')
            return balance_wei / (10 ** 6)  # USDC has 6 decimals
        
        return None
    
    def get_balance_different_rpc(self, token_address, wallet_address, rpc_url):
        """Try with a different RPC endpoint"""
        w3_alt = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 15}))
        if not w3_alt.is_connected():
            return None
        
        erc20_abi = [{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]
        
        contract = w3_alt.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=erc20_abi
        )
        
        balance_wei = contract.functions.balanceOf(wallet_address).call()
        return balance_wei / (10 ** 6)  # USDC decimals

if __name__ == "__main__":
    manager = EnhancedRPCManager()
    if manager.find_working_rpc():
        print("✅ RPC manager initialized successfully")
    else:
        print("❌ Failed to initialize RPC manager")
