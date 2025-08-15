#!/usr/bin/env python3
"""
RPC Circuit Breaker - Prevents cascade failures in RPC calls
"""
import time
from typing import Dict, Any

class RPCCircuitBreaker:
    """Circuit breaker for RPC calls to prevent cascading failures"""

    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                print("🔄 Circuit breaker: Attempting recovery")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                print("✅ Circuit breaker: Recovered")
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                print(f"⚠️ Circuit breaker: OPEN due to {self.failure_count} failures")

            raise e

    def reset(self):
        """Reset circuit breaker"""
        self.failure_count = 0
        self.state = "CLOSED"
        print("🔄 Circuit breaker: Reset")
"""
RPC Circuit Breaker for reliable blockchain connections
"""

import time
from typing import Dict, List, Optional

class RPCCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise Exception("Circuit breaker is OPEN")
            else:
                self.state = "HALF_OPEN"
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        return self.state == "OPEN"
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0
"""
RPC Circuit Breaker
Implements circuit breaker pattern for RPC calls to improve reliability
"""

import time
from typing import Dict, Optional, Callable, Any
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back

class RPCCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                print("🔄 Circuit breaker: Attempting reset (HALF_OPEN)")
            else:
                raise Exception("Circuit breaker is OPEN - failing fast")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        if self.state == CircuitState.HALF_OPEN:
            print("✅ Circuit breaker: Reset to CLOSED")
    
    def _on_failure(self):
        """Handle failure and update circuit state"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"🚨 Circuit breaker: OPENED after {self.failure_count} failures")

    def get_state(self) -> str:
        """Get current circuit breaker state"""
        return self.state.value
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        print("🔄 Circuit breaker: Manually reset to CLOSED")

# Global instance for RPC calls
rpc_circuit_breaker = RPCCircuitBreaker()

print("✅ RPC Circuit Breaker initialized")

# --- Merged from enhanced_rpc_manager.py ---

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
# --- Merged from working_rpc_manager.py ---

class WorkingRPCManager:
    """Manages only the working RPC endpoints for reliability"""
    
    def __init__(self, network_mode='mainnet'):
        self.network_mode = network_mode
        self.working_rpcs = self._get_working_rpcs()
        self.current_rpc_index = 0
        
    def _get_working_rpcs(self):
        """Get list of working RPC endpoints"""
        if self.network_mode == 'mainnet':
            return [
                "https://arbitrum-mainnet.infura.io/v3/5d36f0061cbc4dda980f938ff891c141",
                "https://arb1.arbitrum.io/rpc",
                "https://arbitrum-one.publicnode.com", 
                "https://arbitrum-one.public.blastapi.io",
                "https://1rpc.io/arb"
            ]
        else:
            return [
                "https://sepolia-rollup.arbitrum.io/rpc",
                "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
            ]
    
    def get_primary_rpc(self):
        """Get the primary RPC endpoint"""
        return self.working_rpcs[0] if self.working_rpcs else None
    
    def get_next_rpc(self):
        """Get next working RPC in rotation"""
        if not self.working_rpcs:
            return None
            
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.working_rpcs)
        return self.working_rpcs[self.current_rpc_index]
    
    def get_all_working_rpcs(self):
        """Get all working RPC endpoints"""
        return self.working_rpcs.copy()
    
    def test_rpc_health(self, rpc_url):
        """Test if an RPC endpoint is healthy"""
        try:
            from web3 import Web3
            import time
            
            start_time = time.time()
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
            
            if not w3.is_connected():
                return False, "Not connected"
                
            # Test chain ID
            expected_chain_id = 42161 if self.network_mode == 'mainnet' else 421614
            chain_id = w3.eth.chain_id
            if chain_id != expected_chain_id:
                return False, f"Wrong chain ID: {chain_id}"
                
            # Test block number
            block_number = w3.eth.block_number
            if block_number < 1000000:
                return False, "Invalid block number"
                
            response_time = time.time() - start_time
            return True, f"Healthy (response: {response_time:.2f}s)"
            
        except Exception as e:
            return False, str(e)

    def _get_working_rpcs(self):
        """Get list of working RPC endpoints"""
        if self.network_mode == 'mainnet':
            return [
                "https://arbitrum-mainnet.infura.io/v3/5d36f0061cbc4dda980f938ff891c141",
                "https://arb1.arbitrum.io/rpc",
                "https://arbitrum-one.publicnode.com", 
                "https://arbitrum-one.public.blastapi.io",
                "https://1rpc.io/arb"
            ]
        else:
            return [
                "https://sepolia-rollup.arbitrum.io/rpc",
                "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
            ]

    def get_primary_rpc(self):
        """Get the primary RPC endpoint"""
        return self.working_rpcs[0] if self.working_rpcs else None

    def get_next_rpc(self):
        """Get next working RPC in rotation"""
        if not self.working_rpcs:
            return None
            
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.working_rpcs)
        return self.working_rpcs[self.current_rpc_index]

    def get_all_working_rpcs(self):
        """Get all working RPC endpoints"""
        return self.working_rpcs.copy()

    def test_rpc_health(self, rpc_url):
        """Test if an RPC endpoint is healthy"""
        try:
            from web3 import Web3
            import time
            
            start_time = time.time()
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
            
            if not w3.is_connected():
                return False, "Not connected"
                
            # Test chain ID
            expected_chain_id = 42161 if self.network_mode == 'mainnet' else 421614
            chain_id = w3.eth.chain_id
            if chain_id != expected_chain_id:
                return False, f"Wrong chain ID: {chain_id}"
                
            # Test block number
            block_number = w3.eth.block_number
            if block_number < 1000000:
                return False, "Invalid block number"
                
            response_time = time.time() - start_time
            return True, f"Healthy (response: {response_time:.2f}s)"
            
        except Exception as e:
            return False, str(e)
# --- Merged from rpc_abi.py ---

class RPC:
    # admin
    admin_addPeer = RPCEndpoint("admin_addPeer")
    admin_datadir = RPCEndpoint("admin_datadir")
    admin_nodeInfo = RPCEndpoint("admin_nodeInfo")
    admin_peers = RPCEndpoint("admin_peers")
    admin_startHTTP = RPCEndpoint("admin_startHTTP")
    admin_startWS = RPCEndpoint("admin_startWS")
    admin_stopHTTP = RPCEndpoint("admin_stopHTTP")
    admin_stopWS = RPCEndpoint("admin_stopWS")
    # deprecated
    admin_startRPC = RPCEndpoint("admin_startRPC")
    admin_stopRPC = RPCEndpoint("admin_stopRPC")

    # eth
    eth_accounts = RPCEndpoint("eth_accounts")
    eth_blockNumber = RPCEndpoint("eth_blockNumber")
    eth_call = RPCEndpoint("eth_call")
    eth_createAccessList = RPCEndpoint("eth_createAccessList")
    eth_chainId = RPCEndpoint("eth_chainId")
    eth_coinbase = RPCEndpoint("eth_coinbase")
    eth_estimateGas = RPCEndpoint("eth_estimateGas")
    eth_feeHistory = RPCEndpoint("eth_feeHistory")
    eth_maxPriorityFeePerGas = RPCEndpoint("eth_maxPriorityFeePerGas")
    eth_gasPrice = RPCEndpoint("eth_gasPrice")
    eth_getBalance = RPCEndpoint("eth_getBalance")
    eth_getBlockByHash = RPCEndpoint("eth_getBlockByHash")
    eth_getBlockByNumber = RPCEndpoint("eth_getBlockByNumber")
    eth_getBlockTransactionCountByHash = RPCEndpoint(
        "eth_getBlockTransactionCountByHash"
    )
    eth_getBlockTransactionCountByNumber = RPCEndpoint(
        "eth_getBlockTransactionCountByNumber"
    )
    eth_getCode = RPCEndpoint("eth_getCode")
    eth_getFilterChanges = RPCEndpoint("eth_getFilterChanges")
    eth_getFilterLogs = RPCEndpoint("eth_getFilterLogs")
    eth_getLogs = RPCEndpoint("eth_getLogs")
    eth_getProof = RPCEndpoint("eth_getProof")
    eth_getRawTransactionByHash = RPCEndpoint("eth_getRawTransactionByHash")
    eth_getStorageAt = RPCEndpoint("eth_getStorageAt")
    eth_getTransactionByBlockHashAndIndex = RPCEndpoint(
        "eth_getTransactionByBlockHashAndIndex"
    )
    eth_getTransactionByBlockNumberAndIndex = RPCEndpoint(
        "eth_getTransactionByBlockNumberAndIndex"
    )
    eth_getRawTransactionByBlockHashAndIndex = RPCEndpoint(
        "eth_getRawTransactionByBlockHashAndIndex"
    )
    eth_getRawTransactionByBlockNumberAndIndex = RPCEndpoint(
        "eth_getRawTransactionByBlockNumberAndIndex"
    )
    eth_getTransactionByHash = RPCEndpoint("eth_getTransactionByHash")
    eth_getTransactionCount = RPCEndpoint("eth_getTransactionCount")
    eth_getTransactionReceipt = RPCEndpoint("eth_getTransactionReceipt")
    eth_getUncleByBlockHashAndIndex = RPCEndpoint("eth_getUncleByBlockHashAndIndex")
    eth_getUncleByBlockNumberAndIndex = RPCEndpoint("eth_getUncleByBlockNumberAndIndex")
    eth_getUncleCountByBlockHash = RPCEndpoint("eth_getUncleCountByBlockHash")
    eth_getUncleCountByBlockNumber = RPCEndpoint("eth_getUncleCountByBlockNumber")
    eth_getWork = RPCEndpoint("eth_getWork")
    eth_hashrate = RPCEndpoint("eth_hashrate")
    eth_mining = RPCEndpoint("eth_mining")
    eth_newBlockFilter = RPCEndpoint("eth_newBlockFilter")
    eth_newFilter = RPCEndpoint("eth_newFilter")
    eth_newPendingTransactionFilter = RPCEndpoint("eth_newPendingTransactionFilter")
    eth_protocolVersion = RPCEndpoint("eth_protocolVersion")
    eth_sendRawTransaction = RPCEndpoint("eth_sendRawTransaction")
    eth_sendTransaction = RPCEndpoint("eth_sendTransaction")
    eth_sign = RPCEndpoint("eth_sign")
    eth_signTransaction = RPCEndpoint("eth_signTransaction")
    eth_signTypedData = RPCEndpoint("eth_signTypedData")
    eth_submitHashrate = RPCEndpoint("eth_submitHashrate")
    eth_submitWork = RPCEndpoint("eth_submitWork")
    eth_syncing = RPCEndpoint("eth_syncing")
    eth_uninstallFilter = RPCEndpoint("eth_uninstallFilter")
    eth_subscribe = RPCEndpoint("eth_subscribe")
    eth_unsubscribe = RPCEndpoint("eth_unsubscribe")

    # evm
    evm_mine = RPCEndpoint("evm_mine")
    evm_reset = RPCEndpoint("evm_reset")
    evm_revert = RPCEndpoint("evm_revert")
    evm_snapshot = RPCEndpoint("evm_snapshot")

    # miner
    miner_makeDag = RPCEndpoint("miner_makeDag")
    miner_setExtra = RPCEndpoint("miner_setExtra")
    miner_setEtherbase = RPCEndpoint("miner_setEtherbase")
    miner_setGasPrice = RPCEndpoint("miner_setGasPrice")
    miner_start = RPCEndpoint("miner_start")
    miner_stop = RPCEndpoint("miner_stop")
    miner_startAutoDag = RPCEndpoint("miner_startAutoDag")
    miner_stopAutoDag = RPCEndpoint("miner_stopAutoDag")

    # net
    net_listening = RPCEndpoint("net_listening")
    net_peerCount = RPCEndpoint("net_peerCount")
    net_version = RPCEndpoint("net_version")

    # personal
    personal_ecRecover = RPCEndpoint("personal_ecRecover")
    personal_importRawKey = RPCEndpoint("personal_importRawKey")
    personal_listAccounts = RPCEndpoint("personal_listAccounts")
    personal_listWallets = RPCEndpoint("personal_listWallets")
    personal_lockAccount = RPCEndpoint("personal_lockAccount")
    personal_newAccount = RPCEndpoint("personal_newAccount")
    personal_sendTransaction = RPCEndpoint("personal_sendTransaction")
    personal_sign = RPCEndpoint("personal_sign")
    personal_signTypedData = RPCEndpoint("personal_signTypedData")
    personal_unlockAccount = RPCEndpoint("personal_unlockAccount")

    # testing
    testing_timeTravel = RPCEndpoint("testing_timeTravel")

    # trace
    trace_block = RPCEndpoint("trace_block")
    trace_call = RPCEndpoint("trace_call")
    trace_filter = RPCEndpoint("trace_filter")
    trace_rawTransaction = RPCEndpoint("trace_rawTransaction")
    trace_replayBlockTransactions = RPCEndpoint("trace_replayBlockTransactions")
    trace_replayTransaction = RPCEndpoint("trace_replayTransaction")
    trace_transaction = RPCEndpoint("trace_transaction")

    # txpool
    txpool_content = RPCEndpoint("txpool_content")
    txpool_inspect = RPCEndpoint("txpool_inspect")
    txpool_status = RPCEndpoint("txpool_status")

    # web3
    web3_clientVersion = RPCEndpoint("web3_clientVersion")

def apply_abi_formatters_to_dict(
    normalizers: Sequence[Callable[[TypeStr, Any], Tuple[TypeStr, Any]]],
    abi_dict: Dict[str, Any],
    data: Dict[Any, Any],
) -> Dict[Any, Any]:
    fields = list(abi_dict.keys() & data.keys())
    formatted_values = map_abi_data(
        normalizers,
        [abi_dict[field] for field in fields],
        [data[field] for field in fields],
    )
    formatted_dict = dict(zip(fields, formatted_values))
    return dict(data, **formatted_dict)

def abi_request_formatters(
    normalizers: Sequence[Callable[[TypeStr, Any], Tuple[TypeStr, Any]]],
    abis: Dict[RPCEndpoint, Any],
) -> Iterable[Tuple[RPCEndpoint, Callable[..., Any]]]:
    for method, abi_types in abis.items():
        if isinstance(abi_types, list):
            yield method, map_abi_data(normalizers, abi_types)
        elif isinstance(abi_types, dict):
            single_dict_formatter = apply_abi_formatters_to_dict(normalizers, abi_types)
            yield method, apply_formatter_at_index(single_dict_formatter, 0)
        else:
            raise TypeError(
                f"ABI definitions must be a list or dictionary, got {abi_types!r}"
            )
# --- Merged from rpc.py ---

def rpc_gas_price_strategy(
    w3: Web3, transaction_params: Optional[TxParams] = None
) -> Wei:
    """
    A simple gas price strategy deriving it's value from the eth_gasPrice JSON-RPC call.
    """
    return w3.eth.gas_price
# --- Merged from rpc.py ---

class HTTPProvider(JSONBaseProvider):
    logger = logging.getLogger("web3.providers.HTTPProvider")
    endpoint_uri = None
    _request_args = None
    _request_kwargs = None
    # type ignored b/c conflict with _middlewares attr on BaseProvider
    _middlewares: Tuple[Middleware, ...] = NamedElementOnion([(http_retry_request_middleware, "http_retry_request")])  # type: ignore # noqa: E501

    def __init__(
        self,
        endpoint_uri: Optional[Union[URI, str]] = None,
        request_kwargs: Optional[Any] = None,
        session: Optional[Any] = None,
    ) -> None:
        if endpoint_uri is None:
            self.endpoint_uri = get_default_http_endpoint()
        else:
            self.endpoint_uri = URI(endpoint_uri)

        self._request_kwargs = request_kwargs or {}

        if session:
            cache_and_return_session(self.endpoint_uri, session)

        super().__init__()

    def __str__(self) -> str:
        return f"RPC connection {self.endpoint_uri}"

    @to_dict
    def get_request_kwargs(self) -> Iterable[Tuple[str, Any]]:
        if "headers" not in self._request_kwargs:
            yield "headers", self.get_request_headers()
        for key, value in self._request_kwargs.items():
            yield key, value

    def get_request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": construct_user_agent(str(type(self))),
        }

    def make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        self.logger.debug(
            f"Making request HTTP. URI: {self.endpoint_uri}, Method: {method}"
        )
        request_data = self.encode_rpc_request(method, params)
        raw_response = make_post_request(
            self.endpoint_uri, request_data, **self.get_request_kwargs()
        )
        response = self.decode_rpc_response(raw_response)
        self.logger.debug(
            f"Getting response HTTP. URI: {self.endpoint_uri}, "
            f"Method: {method}, Response: {response}"
        )
        return response

    def __str__(self) -> str:
        return f"RPC connection {self.endpoint_uri}"

    def get_request_kwargs(self) -> Iterable[Tuple[str, Any]]:
        if "headers" not in self._request_kwargs:
            yield "headers", self.get_request_headers()
        for key, value in self._request_kwargs.items():
            yield key, value

    def get_request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": construct_user_agent(str(type(self))),
        }

    def make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        self.logger.debug(
            f"Making request HTTP. URI: {self.endpoint_uri}, Method: {method}"
        )
        request_data = self.encode_rpc_request(method, params)
        raw_response = make_post_request(
            self.endpoint_uri, request_data, **self.get_request_kwargs()
        )
        response = self.decode_rpc_response(raw_response)
        self.logger.debug(
            f"Getting response HTTP. URI: {self.endpoint_uri}, "
            f"Method: {method}, Response: {response}"
        )
        return response