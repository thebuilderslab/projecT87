#!/usr/bin/env python3
"""
ENHANCED TRANSACTION FORENSICS INFRASTRUCTURE
Comprehensive Arbitrum transaction analysis with robust RPC, ABI registry, trace fetching, 
event decoding, and token metadata caching.
"""

import os
import json
import time
import hashlib
import requests
from typing import Dict, List, Optional, Any, Tuple, Union
from web3 import Web3
from web3.types import TxReceipt, TxData, FilterParams, LogReceipt
from eth_utils import to_hex, decode_hex, keccak, function_signature_to_4byte_selector
from datetime import datetime, timedelta
import struct
from dataclasses import dataclass
import traceback

@dataclass
class RPCEndpoint:
    """RPC endpoint configuration"""
    url: str
    name: str
    timeout: int = 30
    max_retries: int = 3
    
class EnhancedRPCManager:
    """Robust RPC provider manager with fallbacks and retry logic"""
    
    def __init__(self):
        """Initialize with multiple RPC endpoints and retry logic"""
        self.endpoints = [
            RPCEndpoint(
                url=os.getenv('ALCHEMY_RPC_URL', 'https://arb1.arbitrum.io/rpc'),
                name="Alchemy/Primary",
                timeout=30,
                max_retries=3
            ),
            RPCEndpoint(
                url="https://arbitrum.llamarpc.com",
                name="LlamaRPC",
                timeout=25,
                max_retries=2
            ),
            RPCEndpoint(
                url="https://rpc.ankr.com/arbitrum",
                name="Ankr",
                timeout=25,
                max_retries=2
            ),
            RPCEndpoint(
                url="https://arb1.arbitrum.io/rpc", 
                name="Official Arbitrum",
                timeout=20,
                max_retries=2
            )
        ]
        
        self.current_endpoint = 0
        self.w3 = None
        self.connection_attempts = 0
        self.max_connection_attempts = len(self.endpoints) * 2
        
        self._establish_connection()
        
    def _establish_connection(self) -> bool:
        """Establish Web3 connection with fallback logic"""
        for attempt in range(self.max_connection_attempts):
            endpoint = self.endpoints[self.current_endpoint]
            
            try:
                print(f"🔗 Attempting connection to {endpoint.name}: {endpoint.url[:50]}...")
                
                self.w3 = Web3(Web3.HTTPProvider(
                    endpoint.url,
                    request_kwargs={'timeout': endpoint.timeout}
                ))
                
                # Test connection
                block_number = self.w3.eth.block_number
                print(f"✅ Connected to {endpoint.name} - Block: {block_number}")
                return True
                
            except Exception as e:
                print(f"❌ Connection failed to {endpoint.name}: {str(e)[:100]}")
                self.current_endpoint = (self.current_endpoint + 1) % len(self.endpoints)
                time.sleep(1)
                
        raise Exception("Failed to connect to any RPC endpoint")
    
    def execute_with_retry(self, operation: str, func, *args, **kwargs) -> Any:
        """Execute Web3 operation with retry logic"""
        for endpoint_attempt in range(len(self.endpoints)):
            endpoint = self.endpoints[self.current_endpoint]
            
            for retry in range(endpoint.max_retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    print(f"⚠️ {operation} failed on {endpoint.name} (retry {retry + 1}): {str(e)[:100]}")
                    
                    if retry == endpoint.max_retries - 1:
                        # Switch to next endpoint
                        print(f"🔄 Switching from {endpoint.name} to next endpoint")
                        self.current_endpoint = (self.current_endpoint + 1) % len(self.endpoints)
                        self._establish_connection()
                        break
                    else:
                        time.sleep(2 ** retry)  # Exponential backoff
                        
        raise Exception(f"All RPC endpoints failed for operation: {operation}")

class ABIRegistry:
    """Comprehensive ABI registry with local storage, Arbiscan API, and 4byte.directory"""
    
    def __init__(self):
        """Initialize ABI registry with caching"""
        self.cache_dir = "./abi_cache"
        self.token_cache_dir = "./token_cache"
        
        # Create cache directories
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.token_cache_dir, exist_ok=True)
        
        # Arbiscan API key
        self.arbiscan_api_key = os.getenv('ARBISCAN_API_KEY')
        
        # Core protocol ABIs (embedded for reliability)
        self.core_abis = {
            'ERC20': [
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "name": "owner", "type": "address"},
                        {"indexed": True, "name": "spender", "type": "address"},
                        {"indexed": False, "name": "value", "type": "uint256"}
                    ],
                    "name": "Approval",
                    "type": "event"
                },
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "name": "from", "type": "address"},
                        {"indexed": True, "name": "to", "type": "address"},
                        {"indexed": False, "name": "value", "type": "uint256"}
                    ],
                    "name": "Transfer",
                    "type": "event"
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
            ],
            'Aave_Pool': [
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "name": "reserve", "type": "address"},
                        {"indexed": False, "name": "user", "type": "address"},
                        {"indexed": True, "name": "onBehalfOf", "type": "address"},
                        {"indexed": False, "name": "amount", "type": "uint256"},
                        {"indexed": False, "name": "interestRateMode", "type": "uint256"},
                        {"indexed": False, "name": "borrowRate", "type": "uint256"},
                        {"indexed": True, "name": "referralCode", "type": "uint16"}
                    ],
                    "name": "Borrow",
                    "type": "event"
                },
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "name": "reserve", "type": "address"},
                        {"indexed": False, "name": "user", "type": "address"},
                        {"indexed": True, "name": "repayer", "type": "address"},
                        {"indexed": False, "name": "amount", "type": "uint256"},
                        {"indexed": False, "name": "useATokens", "type": "bool"}
                    ],
                    "name": "Repay",
                    "type": "event"
                }
            ],
            'ParaSwap_Augustus': [
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "name": "initiator", "type": "address"},
                        {"indexed": True, "name": "beneficiary", "type": "address"},
                        {"indexed": True, "name": "srcToken", "type": "address"},
                        {"indexed": False, "name": "destToken", "type": "address"},
                        {"indexed": False, "name": "srcAmount", "type": "uint256"},
                        {"indexed": False, "name": "receivedAmount", "type": "uint256"},
                        {"indexed": False, "name": "expectedAmount", "type": "uint256"}
                    ],
                    "name": "Swapped",
                    "type": "event"
                }
            ]
        }
        
        # Event signature mappings
        self.event_signatures = {
            '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef': 'Transfer',
            '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925': 'Approval',
            '0xc6a898309e823ee50bac64e45ca8adba6690e99e7841c45d754e2a38e9019d9b': 'Borrow',
            '0x4cdde6e09bb755c9a5589ebaec640bbfedff1362d4b255ebf8339782b9942faa': 'Repay',
            '0xb9d4efa96044e5f187570ba289071023c5d62e08db7a47b22530d0c4620b1d8a': 'Swapped'
        }
        
        print(f"✅ ABI Registry initialized with cache at {self.cache_dir}")
        
    def get_abi(self, contract_address: str) -> Optional[List[Dict]]:
        """Get ABI with comprehensive fallback strategy"""
        try:
            # Step 1: Check local cache
            abi = self._load_from_cache(contract_address)
            if abi:
                print(f"📁 ABI loaded from cache for {contract_address[:10]}...")
                return abi
            
            # Step 2: Try Arbiscan API
            if self.arbiscan_api_key:
                abi = self._fetch_from_arbiscan(contract_address)
                if abi:
                    self._save_to_cache(contract_address, abi)
                    print(f"🔍 ABI fetched from Arbiscan for {contract_address[:10]}...")
                    return abi
            
            # Step 3: Use core protocol ABI if recognized
            for protocol, protocol_abi in self.core_abis.items():
                if self._is_protocol_contract(contract_address, protocol):
                    print(f"🏛️ Using core {protocol} ABI for {contract_address[:10]}...")
                    return protocol_abi
            
            # Step 4: Return minimal ERC20 ABI as fallback
            print(f"⚠️ Using fallback ERC20 ABI for {contract_address[:10]}...")
            return self.core_abis['ERC20']
            
        except Exception as e:
            print(f"❌ ABI fetch error for {contract_address}: {e}")
            return self.core_abis['ERC20']
    
    def _load_from_cache(self, contract_address: str) -> Optional[List[Dict]]:
        """Load ABI from local cache"""
        cache_file = os.path.join(self.cache_dir, f"{contract_address.lower()}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_to_cache(self, contract_address: str, abi: List[Dict]) -> None:
        """Save ABI to local cache"""
        cache_file = os.path.join(self.cache_dir, f"{contract_address.lower()}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(abi, f, indent=2)
        except Exception as e:
            print(f"⚠️ Cache save failed: {e}")
    
    def _fetch_from_arbiscan(self, contract_address: str) -> Optional[List[Dict]]:
        """Fetch ABI from Arbiscan API"""
        if not self.arbiscan_api_key:
            return None
            
        try:
            url = "https://api.arbiscan.io/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': contract_address,
                'apikey': self.arbiscan_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '1':
                    return json.loads(data['result'])
        except Exception as e:
            print(f"⚠️ Arbiscan API error: {e}")
        
        return None
    
    def _is_protocol_contract(self, contract_address: str, protocol: str) -> bool:
        """Check if contract is a known protocol contract"""
        known_contracts = {
            'Aave_Pool': ['0x794a61358D6845594F94dc1DB02A252b5b4814aD'],
            'ParaSwap_Augustus': ['0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57']
        }
        
        return contract_address.lower() in [addr.lower() for addr in known_contracts.get(protocol, [])]
    
    def get_function_selector_hint(self, selector: str) -> str:
        """Get function name hint from 4byte.directory"""
        try:
            url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={selector}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    return data['results'][0]['text_signature']
        except:
            pass
        
        return f"Unknown({selector})"

class TraceAndLogFetcher:
    """Advanced trace and log fetching with comprehensive capabilities"""
    
    def __init__(self, rpc_manager: EnhancedRPCManager):
        """Initialize with RPC manager"""
        self.rpc_manager = rpc_manager
        self.supports_debug_trace = None  # Will be detected
        
    def get_transaction_receipt(self, tx_hash: str) -> Optional[TxReceipt]:
        """Get transaction receipt with retry logic"""
        return self.rpc_manager.execute_with_retry(
            "get_transaction_receipt",
            self.rpc_manager.w3.eth.get_transaction_receipt,
            tx_hash
        )
    
    def get_transaction_data(self, tx_hash: str) -> Optional[TxData]:
        """Get transaction data with retry logic"""
        return self.rpc_manager.execute_with_retry(
            "get_transaction",
            self.rpc_manager.w3.eth.get_transaction,
            tx_hash
        )
    
    def get_logs_comprehensive(self, tx_hash: str, block_number: int) -> List[LogReceipt]:
        """Get comprehensive logs using multiple strategies"""
        logs = []
        
        try:
            # Strategy 1: From transaction receipt
            receipt = self.get_transaction_receipt(tx_hash)
            if receipt and receipt.logs:
                logs.extend(receipt.logs)
                print(f"📝 Found {len(receipt.logs)} logs from transaction receipt")
            
            # Strategy 2: Block-level log filtering
            try:
                block_logs = self.rpc_manager.execute_with_retry(
                    "get_logs",
                    self.rpc_manager.w3.eth.get_logs,
                    {
                        'fromBlock': block_number,
                        'toBlock': block_number
                    }
                )
                
                # Filter for our transaction
                tx_logs = [log for log in block_logs if log.transactionHash.hex() == tx_hash]
                print(f"📝 Found {len(tx_logs)} additional logs from block filtering")
                
                # Merge unique logs
                existing_log_indices = {(log.logIndex, log.transactionIndex) for log in logs}
                for log in tx_logs:
                    if (log.logIndex, log.transactionIndex) not in existing_log_indices:
                        logs.append(log)
                        
            except Exception as e:
                print(f"⚠️ Block log filtering failed: {e}")
        
        except Exception as e:
            print(f"❌ Log fetching failed: {e}")
        
        return logs
    
    def get_debug_trace(self, tx_hash: str) -> Optional[Dict]:
        """Get debug trace with graceful fallback"""
        if self.supports_debug_trace is False:
            return None
            
        try:
            # Test debug_traceTransaction support
            trace = self.rpc_manager.execute_with_retry(
                "debug_traceTransaction",
                self.rpc_manager.w3.manager.request_blocking,
                "debug_traceTransaction",
                [tx_hash, {"tracer": "callTracer"}]
            )
            
            self.supports_debug_trace = True
            print(f"🔍 Debug trace retrieved (calls: {len(trace.get('calls', []))})")
            return trace
            
        except Exception as e:
            print(f"⚠️ Debug trace not supported or failed: {str(e)[:100]}")
            self.supports_debug_trace = False
            return None
    
    def get_block_timestamp(self, block_number: int) -> datetime:
        """Get block timestamp with caching"""
        try:
            block = self.rpc_manager.execute_with_retry(
                "get_block",
                self.rpc_manager.w3.eth.get_block,
                block_number
            )
            return datetime.fromtimestamp(block['timestamp'])
        except:
            return datetime.now()

class EventDecoder:
    """Comprehensive event and call decoder"""
    
    def __init__(self, abi_registry: ABIRegistry, rpc_manager: EnhancedRPCManager):
        """Initialize with ABI registry and RPC manager"""
        self.abi_registry = abi_registry
        self.rpc_manager = rpc_manager
        self.token_cache = TokenMetadataCache(rpc_manager)
        
        # Extended event signatures for DeFi protocols
        self.event_signatures = {
            # ERC20
            '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef': {
                'name': 'Transfer',
                'inputs': [
                    {'name': 'from', 'type': 'address', 'indexed': True},
                    {'name': 'to', 'type': 'address', 'indexed': True},
                    {'name': 'value', 'type': 'uint256', 'indexed': False}
                ]
            },
            '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925': {
                'name': 'Approval',
                'inputs': [
                    {'name': 'owner', 'type': 'address', 'indexed': True},
                    {'name': 'spender', 'type': 'address', 'indexed': True},
                    {'name': 'value', 'type': 'uint256', 'indexed': False}
                ]
            },
            # Aave v3
            '0xc6a898309e823ee50bac64e45ca8adba6690e99e7841c45d754e2a38e9019d9b': {
                'name': 'Borrow',
                'inputs': [
                    {'name': 'reserve', 'type': 'address', 'indexed': True},
                    {'name': 'user', 'type': 'address', 'indexed': False},
                    {'name': 'onBehalfOf', 'type': 'address', 'indexed': True},
                    {'name': 'amount', 'type': 'uint256', 'indexed': False},
                    {'name': 'interestRateMode', 'type': 'uint256', 'indexed': False},
                    {'name': 'borrowRate', 'type': 'uint256', 'indexed': False},
                    {'name': 'referralCode', 'type': 'uint16', 'indexed': True}
                ]
            },
            # ParaSwap
            '0xb9d4efa96044e5f187570ba289071023c5d62e08db7a47b22530d0c4620b1d8a': {
                'name': 'Swapped',
                'inputs': [
                    {'name': 'initiator', 'type': 'address', 'indexed': True},
                    {'name': 'beneficiary', 'type': 'address', 'indexed': True},
                    {'name': 'srcToken', 'type': 'address', 'indexed': True},
                    {'name': 'destToken', 'type': 'address', 'indexed': False},
                    {'name': 'srcAmount', 'type': 'uint256', 'indexed': False},
                    {'name': 'receivedAmount', 'type': 'uint256', 'indexed': False},
                    {'name': 'expectedAmount', 'type': 'uint256', 'indexed': False}
                ]
            }
        }
    
    def decode_logs(self, logs: List[LogReceipt]) -> List[Dict]:
        """Decode all logs with comprehensive fallback"""
        decoded_logs = []
        
        for log in logs:
            try:
                decoded = self.decode_single_log(log)
                decoded_logs.append(decoded)
            except Exception as e:
                # Fallback for undecoded logs
                decoded_logs.append({
                    'address': log.address,
                    'topics': [topic.hex() for topic in log.topics],
                    'data': log.data.hex(),
                    'event_name': 'Could not decode',
                    'error': str(e),
                    'log_index': log.logIndex,
                    'transaction_index': log.transactionIndex
                })
        
        return decoded_logs
    
    def decode_single_log(self, log: LogReceipt) -> Dict:
        """Decode a single log entry"""
        if not log.topics:
            return {
                'address': log.address,
                'data': log.data.hex(),
                'event_name': 'No topics',
                'log_index': log.logIndex
            }
        
        topic0 = log.topics[0].hex()
        
        # Try known event signatures first
        if topic0 in self.event_signatures:
            event_def = self.event_signatures[topic0]
            try:
                decoded_data = self._decode_event_data(log, event_def)
                
                # Enhance with token metadata
                if event_def['name'] in ['Transfer', 'Approval']:
                    token_info = self.token_cache.get_token_info(log.address)
                    decoded_data['token_symbol'] = token_info['symbol']
                    decoded_data['token_decimals'] = token_info['decimals']
                    
                    # Format amounts
                    if 'value' in decoded_data:
                        decoded_data['value_formatted'] = self._format_amount(
                            decoded_data['value'], 
                            token_info['decimals']
                        )
                
                return decoded_data
                
            except Exception as e:
                print(f"⚠️ Failed to decode known event {event_def['name']}: {e}")
        
        # Try ABI-based decoding
        try:
            abi = self.abi_registry.get_abi(log.address)
            if abi:
                contract = self.rpc_manager.w3.eth.contract(
                    address=log.address, 
                    abi=abi
                )
                decoded = contract.events.get(topic0, contract.events.__dict__.values()).__call__().processLog(log)
                
                return {
                    'address': log.address,
                    'event_name': decoded.event,
                    'args': dict(decoded.args),
                    'log_index': log.logIndex,
                    'transaction_index': log.transactionIndex,
                    'decoded_via': 'ABI'
                }
        except Exception as e:
            print(f"⚠️ ABI decoding failed for {log.address}: {e}")
        
        # Fallback: Raw log data
        return {
            'address': log.address,
            'topics': [topic.hex() for topic in log.topics],
            'data': log.data.hex(),
            'event_name': 'Could not decode',
            'log_index': log.logIndex,
            'transaction_index': log.transactionIndex,
            'topic0_hint': self.abi_registry.get_function_selector_hint(topic0)
        }
    
    def _decode_event_data(self, log: LogReceipt, event_def: Dict) -> Dict:
        """Decode event data based on event definition"""
        result = {
            'address': log.address,
            'event_name': event_def['name'],
            'log_index': log.logIndex,
            'transaction_index': log.transactionIndex
        }
        
        topic_index = 1  # Skip topic0 (event signature)
        data_offset = 0
        
        for input_def in event_def['inputs']:
            if input_def['indexed']:
                if topic_index < len(log.topics):
                    topic_data = log.topics[topic_index]
                    if input_def['type'] == 'address':
                        result[input_def['name']] = '0x' + topic_data.hex()[26:]  # Remove padding
                    elif input_def['type'].startswith('uint'):
                        result[input_def['name']] = int(topic_data.hex(), 16)
                    else:
                        result[input_def['name']] = topic_data.hex()
                    topic_index += 1
            else:
                # Decode from data field
                if input_def['type'].startswith('uint'):
                    value_bytes = log.data[data_offset:data_offset + 32]
                    result[input_def['name']] = int(value_bytes.hex(), 16)
                    data_offset += 32
                elif input_def['type'] == 'address':
                    value_bytes = log.data[data_offset:data_offset + 32]
                    result[input_def['name']] = '0x' + value_bytes.hex()[24:]  # Remove padding
                    data_offset += 32
                else:
                    # Generic handling
                    value_bytes = log.data[data_offset:data_offset + 32]
                    result[input_def['name']] = value_bytes.hex()
                    data_offset += 32
        
        return result
    
    def _format_amount(self, amount: int, decimals: int) -> str:
        """Format token amount with proper decimals"""
        if amount == 0:
            return "0"
        elif amount >= 2**256 - 1000:  # Near max uint256
            return "MAX_UINT256"
        else:
            formatted = amount / (10 ** decimals)
            return f"{formatted:.6f}".rstrip('0').rstrip('.')

class TokenMetadataCache:
    """Token metadata caching system"""
    
    def __init__(self, rpc_manager: EnhancedRPCManager):
        """Initialize token metadata cache"""
        self.rpc_manager = rpc_manager
        self.cache_dir = "./token_cache"
        self.cache = {}
        
        # Well-known tokens
        self.known_tokens = {
            '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'.lower(): {
                'symbol': 'DAI',
                'decimals': 18,
                'name': 'Dai Stablecoin'
            },
            '0x912CE59144191C1204E64559FE8253a0e49E6548'.lower(): {
                'symbol': 'ARB',
                'decimals': 18,
                'name': 'Arbitrum'
            },
            '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'.lower(): {
                'symbol': 'USDC.e',
                'decimals': 6,
                'name': 'USD Coin (Arb1)'
            },
            '0xaf88d065e77c8cC2239327C5EDb3A432268e5831'.lower(): {
                'symbol': 'USDC',
                'decimals': 6,
                'name': 'USD Coin'
            }
        }
        
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"✅ Token metadata cache initialized")
    
    def get_token_info(self, token_address: str) -> Dict[str, Union[str, int]]:
        """Get comprehensive token information"""
        address_lower = token_address.lower()
        
        # Check memory cache
        if address_lower in self.cache:
            return self.cache[address_lower]
        
        # Check known tokens
        if address_lower in self.known_tokens:
            token_info = self.known_tokens[address_lower]
            self.cache[address_lower] = token_info
            return token_info
        
        # Check disk cache
        cache_file = os.path.join(self.cache_dir, f"{address_lower}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    token_info = json.load(f)
                    self.cache[address_lower] = token_info
                    return token_info
            except:
                pass
        
        # Fetch from contract
        token_info = self._fetch_token_info(token_address)
        
        # Cache the result
        self.cache[address_lower] = token_info
        self._save_to_disk(address_lower, token_info)
        
        return token_info
    
    def _fetch_token_info(self, token_address: str) -> Dict[str, Union[str, int]]:
        """Fetch token info from contract"""
        try:
            # Basic ERC20 ABI for metadata
            erc20_abi = [
                {
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
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
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            contract = self.rpc_manager.w3.eth.contract(
                address=self.rpc_manager.w3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            symbol = self.rpc_manager.execute_with_retry(
                "get_symbol",
                contract.functions.symbol().call
            )
            
            decimals = self.rpc_manager.execute_with_retry(
                "get_decimals", 
                contract.functions.decimals().call
            )
            
            try:
                name = self.rpc_manager.execute_with_retry(
                    "get_name",
                    contract.functions.name().call
                )
            except:
                name = symbol
            
            return {
                'symbol': symbol,
                'decimals': decimals,
                'name': name
            }
            
        except Exception as e:
            print(f"⚠️ Failed to fetch token info for {token_address}: {e}")
            return {
                'symbol': f'TOKEN_{token_address[-6:].upper()}',
                'decimals': 18,
                'name': 'Unknown Token'
            }
    
    def _save_to_disk(self, address_lower: str, token_info: Dict) -> None:
        """Save token info to disk cache"""
        cache_file = os.path.join(self.cache_dir, f"{address_lower}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(token_info, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to cache token info: {e}")

class EnhancedForensicAnalyzer:
    """Main enhanced forensic analyzer orchestrating all components"""
    
    def __init__(self):
        """Initialize comprehensive forensic analyzer"""
        print(f"🔍 ENHANCED TRANSACTION FORENSICS INFRASTRUCTURE")
        print(f"⏰ {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Initialize all components
        self.rpc_manager = EnhancedRPCManager()
        self.abi_registry = ABIRegistry()
        self.trace_fetcher = TraceAndLogFetcher(self.rpc_manager)
        self.event_decoder = EventDecoder(self.abi_registry, self.rpc_manager)
        
        print(f"✅ All forensic components initialized successfully")
        print(f"   Latest block: {self.rpc_manager.w3.eth.block_number}")
        
    def analyze_transaction_comprehensive(self, tx_hash: str) -> Dict:
        """Comprehensive transaction analysis"""
        print(f"\n🔍 COMPREHENSIVE FORENSIC ANALYSIS")
        print(f"   Transaction: {tx_hash}")
        print("=" * 80)
        
        analysis_start = time.time()
        
        try:
            # Step 1: Get basic transaction data
            tx_data = self.trace_fetcher.get_transaction_data(tx_hash)
            tx_receipt = self.trace_fetcher.get_transaction_receipt(tx_hash)
            
            if not tx_data or not tx_receipt:
                return {
                    'transaction_hash': tx_hash,
                    'error': 'Transaction not found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Step 2: Get comprehensive logs
            logs = self.trace_fetcher.get_logs_comprehensive(tx_hash, tx_data['blockNumber'])
            
            # Step 3: Decode all logs
            decoded_logs = self.event_decoder.decode_logs(logs)
            
            # Step 4: Get debug trace (if available)
            debug_trace = self.trace_fetcher.get_debug_trace(tx_hash)
            
            # Step 5: Enhanced analysis
            analysis = {
                'transaction_hash': tx_hash,
                'block_number': tx_data['blockNumber'],
                'timestamp': self.trace_fetcher.get_block_timestamp(tx_data['blockNumber']).isoformat(),
                'from_address': tx_data['from'],
                'to_address': tx_data['to'],
                'value_wei': int(tx_data['value']),
                'value_eth': float(tx_data['value']) / 1e18,
                'gas_used': int(tx_receipt['gasUsed']),
                'gas_price': int(tx_data['gasPrice']),
                'gas_fee_eth': (int(tx_receipt['gasUsed']) * int(tx_data['gasPrice'])) / 1e18,
                'status': 'SUCCESS' if int(tx_receipt['status']) == 1 else 'FAILED',
                'input_data': tx_data['input'].hex(),
                'input_size_bytes': len(tx_data['input']),
                
                # Enhanced components
                'logs_analysis': {
                    'total_logs': len(decoded_logs),
                    'decoded_logs': decoded_logs,
                    'event_summary': self._create_event_summary(decoded_logs),
                    'token_transfers': self._extract_token_transfers(decoded_logs),
                    'protocol_interactions': self._identify_protocol_interactions(decoded_logs)
                },
                
                'debug_trace': debug_trace,
                'calldata_analysis': self._analyze_calldata(tx_data['input'].hex(), tx_data['to']),
                'gas_analysis': self._analyze_gas_usage(tx_receipt, tx_data),
                
                # Metadata
                'analysis_metadata': {
                    'analysis_duration_seconds': time.time() - analysis_start,
                    'rpc_endpoint': self.rpc_manager.endpoints[self.rpc_manager.current_endpoint].name,
                    'analyzer_version': '3.0.0_comprehensive',
                    'components_used': [
                        'enhanced_rpc_manager',
                        'abi_registry',
                        'trace_fetcher', 
                        'event_decoder',
                        'token_metadata_cache'
                    ]
                }
            }
            
            print(f"✅ Comprehensive analysis completed in {time.time() - analysis_start:.2f}s")
            print(f"   Status: {analysis['status']}")
            print(f"   Logs decoded: {analysis['logs_analysis']['total_logs']}")
            print(f"   Gas used: {analysis['gas_used']:,}")
            print(f"   Events: {', '.join(analysis['logs_analysis']['event_summary'].keys())}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Comprehensive analysis failed: {e}")
            traceback.print_exc()
            return {
                'transaction_hash': tx_hash,
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'analysis_duration_seconds': time.time() - analysis_start
            }
    
    def _create_event_summary(self, decoded_logs: List[Dict]) -> Dict[str, int]:
        """Create summary of events by type"""
        summary = {}
        for log in decoded_logs:
            event_name = log.get('event_name', 'Unknown')
            summary[event_name] = summary.get(event_name, 0) + 1
        return summary
    
    def _extract_token_transfers(self, decoded_logs: List[Dict]) -> List[Dict]:
        """Extract and format token transfer events"""
        transfers = []
        for log in decoded_logs:
            if log.get('event_name') == 'Transfer':
                transfer = {
                    'token_address': log['address'],
                    'token_symbol': log.get('token_symbol', 'UNKNOWN'),
                    'from': log.get('from', log.get('args', {}).get('from')),
                    'to': log.get('to', log.get('args', {}).get('to')),
                    'amount_raw': log.get('value', log.get('args', {}).get('value')),
                    'amount_formatted': log.get('value_formatted', 'Unknown'),
                    'log_index': log.get('log_index')
                }
                transfers.append(transfer)
        return transfers
    
    def _identify_protocol_interactions(self, decoded_logs: List[Dict]) -> Dict[str, List[str]]:
        """Identify DeFi protocol interactions"""
        protocols = {}
        
        for log in decoded_logs:
            event_name = log.get('event_name', '')
            address = log.get('address', '').lower()
            
            # Aave
            if event_name in ['Borrow', 'Repay', 'Supply', 'Withdraw'] or \
               address == '0x794a61358d6845594f94dc1db02a252b5b4814ad':
                if 'Aave' not in protocols:
                    protocols['Aave'] = []
                protocols['Aave'].append(event_name)
            
            # ParaSwap
            if event_name in ['Swapped', 'BoughtV3'] or \
               address == '0xdef171fe48cf0115b1d80b88dc8eab59176fee57':
                if 'ParaSwap' not in protocols:
                    protocols['ParaSwap'] = []
                protocols['ParaSwap'].append(event_name)
            
            # Uniswap
            if event_name in ['Swap', 'Mint', 'Burn']:
                if 'Uniswap' not in protocols:
                    protocols['Uniswap'] = []
                protocols['Uniswap'].append(event_name)
        
        return protocols
    
    def _analyze_calldata(self, input_hex: str, to_address: str) -> Dict:
        """Analyze transaction calldata"""
        if not input_hex or input_hex == '0x':
            return {'type': 'No calldata'}
        
        if len(input_hex) < 10:
            return {'type': 'Invalid calldata', 'raw': input_hex}
        
        function_selector = input_hex[:10]
        
        analysis = {
            'function_selector': function_selector,
            'function_hint': self.abi_registry.get_function_selector_hint(function_selector),
            'data_length_bytes': (len(input_hex) - 2) // 2,
            'to_contract': to_address,
            'raw_calldata': input_hex
        }
        
        # Try to get more detailed analysis based on known contracts
        try:
            abi = self.abi_registry.get_abi(to_address)
            if abi:
                contract = self.rpc_manager.w3.eth.contract(
                    address=to_address,
                    abi=abi
                )
                # Additional calldata analysis could be added here
                analysis['abi_available'] = True
        except:
            analysis['abi_available'] = False
        
        return analysis
    
    def _analyze_gas_usage(self, receipt: TxReceipt, tx_data: TxData) -> Dict:
        """Analyze gas usage patterns"""
        gas_used = int(receipt['gasUsed'])
        gas_limit = int(tx_data['gas'])
        gas_price = int(tx_data['gasPrice'])
        
        return {
            'gas_used': gas_used,
            'gas_limit': gas_limit,
            'gas_efficiency': (gas_used / gas_limit) * 100,
            'gas_price_gwei': gas_price / 1e9,
            'total_fee_eth': (gas_used * gas_price) / 1e18,
            'gas_analysis': 'efficient' if gas_used / gas_limit < 0.8 else 'high_usage'
        }

def main():
    """Test the enhanced forensic analyzer with provided transaction hashes"""
    target_transactions = [
        '0x5f5d8e9b2ddd18cb3ee46a1e1f27d84d10725d61fa965ab272786ceac47f8996',
        '0x3ab14c6aeeae1da04c1b7530067d4980a46d9f6ec807592e020218371fffd33c'
    ]
    
    try:
        print(f"🚀 TESTING ENHANCED FORENSIC INFRASTRUCTURE")
        print(f"   Target transactions: {len(target_transactions)}")
        print("=" * 80)
        
        analyzer = EnhancedForensicAnalyzer()
        
        results = []
        for i, tx_hash in enumerate(target_transactions, 1):
            print(f"\n🎯 ANALYZING TRANSACTION {i}/{len(target_transactions)}")
            
            analysis = analyzer.analyze_transaction_comprehensive(tx_hash)
            results.append(analysis)
            
            # Brief summary
            if 'error' not in analysis:
                print(f"   ✅ Success - {analysis['logs_analysis']['total_logs']} events decoded")
            else:
                print(f"   ❌ Failed - {analysis['error']}")
            
            if i < len(target_transactions):
                time.sleep(2)  # Rate limiting
        
        # Save comprehensive report
        report = {
            'forensic_report_metadata': {
                'created_at': datetime.now().isoformat(),
                'analyzer_version': '3.0.0_comprehensive',
                'target_transactions': target_transactions,
                'infrastructure_components': [
                    'enhanced_rpc_manager',
                    'abi_registry_system', 
                    'trace_log_fetcher',
                    'event_call_decoders',
                    'token_metadata_cache'
                ]
            },
            'transaction_analyses': results,
            'summary': {
                'total_transactions': len(target_transactions),
                'successful_analyses': len([r for r in results if 'error' not in r]),
                'total_events_decoded': sum(r.get('logs_analysis', {}).get('total_logs', 0) for r in results if 'error' not in r)
            }
        }
        
        with open('forensic_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n✅ FORENSIC ANALYSIS COMPLETE")
        print(f"   Report saved: forensic_analysis_report.json")
        print(f"   Successful analyses: {report['summary']['successful_analyses']}/{report['summary']['total_transactions']}")
        print(f"   Total events decoded: {report['summary']['total_events_decoded']}")
        
        return report
        
    except Exception as e:
        print(f"❌ Forensic analysis failed: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()