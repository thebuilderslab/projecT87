#!/usr/bin/env python3
"""
Augustus V5 multiSwap Calldata Builder
Builds compliant multiSwap calldata for Aave Debt Switch integration
"""

import json
import time
import requests
from typing import Any, Dict, List, Optional
from eth_abi.abi import encode
from web3 import Web3

class AugustusV5MultiSwapBuilder:
    """
    Builds Augustus V5 multiSwap calldata for Aave Debt Switch V3
    
    multiSwap ABI Structure (Utils.SellData):
    - fromToken: address
    - fromAmount: uint256
    - toAmount: uint256 (min amount out - slippage protection)
    - expectedAmount: uint256
    - beneficiary: address (who receives tokens)
    - path: Utils.Path[] (swap routes)
      - to: address (destination token for this path)
      - totalNetworkFee: uint256
      - routes: Utils.Route[]
        - exchange: address (DEX adapter)
        - targetExchange: address (actual DEX)
        - percent: uint256 (percentage to route)
        - payload: bytes (DEX-specific data)
        - networkFee: uint256
    - partner: address (referral/partner address)
    - feePercent: uint256 (fee in basis points)
    - permit: bytes (EIP-2612 permit, empty if not used)
    - deadline: uint256 (Unix timestamp)
    - uuid: bytes16 (unique identifier)
    """
    
    def __init__(self, w3: Web3, network: str = "arbitrum"):
        self.w3 = w3
        self.network = network
        self.chain_id = 42161 if network == "arbitrum" else 1
        
        # Augustus V5 on Arbitrum
        self.augustus_v5 = self.w3.to_checksum_address("0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57")
        
        # ArbitrumAdapter01 - Generic adapter for ALL DEXs on Arbitrum
        # This single adapter handles UniswapV3, Sushi, Camelot, etc. internally
        self.arbitrum_adapter = self.w3.to_checksum_address("0x369A2FDb910d432f0a07381a5E3d27572c876713")
        
        # ParaSwap API
        self.paraswap_api_base = "https://apiv5.paraswap.io"
        
        # multiSwap selector
        self.multiswap_selector = "0x0863b7ac"
        
        # Token addresses (Arbitrum)
        self.tokens = {
            'DAI': self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"),
            'ARB': self.w3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548"),
            'WETH': self.w3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
        }
        
        print(f"🔧 Augustus V5 multiSwap Builder initialized")
        print(f"   Augustus V5: {self.augustus_v5}")
        print(f"   ArbitrumAdapter01: {self.arbitrum_adapter} (generic adapter for ALL DEXs)")
        print(f"   Chain: {self.network} (ID: {self.chain_id})")
    
    def get_paraswap_price_route(self, from_token: str, to_token: str, amount: int) -> Optional[Dict[str, Any]]:
        """Get price and route data from ParaSwap API"""
        try:
            from_token_addr = self.tokens.get(from_token.upper())
            to_token_addr = self.tokens.get(to_token.upper())
            
            if not from_token_addr or not to_token_addr:
                raise ValueError(f"Unknown tokens: {from_token} or {to_token}")
            
            # ParaSwap prices endpoint
            url = f"{self.paraswap_api_base}/prices"
            params = {
                'srcToken': from_token_addr,
                'destToken': to_token_addr,
                'amount': str(amount),
                'srcDecimals': '18',
                'destDecimals': '18',
                'side': 'SELL',
                'network': str(self.chain_id),
                'excludeDirectContractMethods': 'true'  # Force multi-hop routing
            }
            
            print(f"\n🌐 Fetching ParaSwap price route for {from_token} → {to_token}...")
            print(f"   Amount: {amount / 1e18:.6f} {from_token}")
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                price_data = response.json()
                
                print(f"   ✅ Price route obtained:")
                print(f"      Expected output: {int(price_data['priceRoute']['destAmount']) / 1e18:.6f} {to_token}")
                print(f"      Gas estimate: {price_data['priceRoute'].get('gasCost', 'N/A')}")
                
                return price_data['priceRoute']
            else:
                print(f"   ❌ ParaSwap API error: {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting ParaSwap price: {e}")
            return None
    
    def build_multiswap_calldata(
        self,
        from_token: str,
        to_token: str,
        from_amount: int,
        min_to_amount: int,
        beneficiary: str,
        deadline: Optional[int] = None,
        slippage_bps: int = 400  # 4% slippage
    ) -> Optional[Dict[str, Any]]:
        """
        Build multiSwap calldata for Augustus V5
        
        Args:
            from_token: Source token symbol (e.g., 'ARB')
            to_token: Destination token symbol (e.g., 'DAI')
            from_amount: Exact amount to swap (in wei)
            min_to_amount: Minimum amount to receive (in wei)
            beneficiary: Address to receive swapped tokens
            deadline: Unix timestamp deadline (default: 30 mins from now)
            slippage_bps: Slippage tolerance in basis points (default: 400 = 4%)
        
        Returns:
            Dict with calldata, method info, and parameters
        """
        try:
            print(f"\n🏗️  BUILDING AUGUSTUS V5 multiSwap CALLDATA")
            print("=" * 80)
            
            # Get token addresses
            from_token_addr = self.tokens.get(from_token.upper())
            to_token_addr = self.tokens.get(to_token.upper())
            
            if not from_token_addr or not to_token_addr:
                raise ValueError(f"Unknown tokens: {from_token} or {to_token}")
            
            # Get ParaSwap price route for routing data
            price_route = self.get_paraswap_price_route(from_token, to_token, from_amount)
            
            if not price_route:
                raise Exception("Failed to get ParaSwap price route")
            
            # Calculate expected amount with slippage
            expected_amount = int(price_route['destAmount'])
            min_amount = min_to_amount if min_to_amount > 0 else int(expected_amount * (10000 - slippage_bps) / 10000)
            
            # Set deadline (30 minutes from now if not provided)
            if deadline is None:
                deadline = int(time.time()) + 1800
            
            # Build paths from ParaSwap bestRoute
            paths = self._build_paths_from_paraswap(price_route, to_token_addr)
            
            if not paths:
                raise Exception("Failed to build swap paths from ParaSwap route")
            
            # Build SellData struct
            sell_data = {
                'fromToken': from_token_addr,
                'fromAmount': from_amount,
                'toAmount': min_amount,  # Min amount out (slippage protection)
                'expectedAmount': expected_amount,
                'beneficiary': self.w3.to_checksum_address(beneficiary),
                'path': paths,
                'partner': '0x0000000000000000000000000000000000000000',  # No partner
                'feePercent': 0,  # No fee
                'permit': b'',  # No permit
                'deadline': deadline,
                'uuid': b'\x00' * 16  # Empty UUID
            }
            
            print(f"\n📋 MULTISWA STRUCT PARAMETERS:")
            print(f"   fromToken: {sell_data['fromToken']} ({from_token})")
            print(f"   fromAmount: {sell_data['fromAmount']} ({sell_data['fromAmount'] / 1e18:.6f} {from_token})")
            print(f"   toAmount (min): {sell_data['toAmount']} ({sell_data['toAmount'] / 1e18:.6f} {to_token})")
            print(f"   expectedAmount: {sell_data['expectedAmount']} ({sell_data['expectedAmount'] / 1e18:.6f} {to_token})")
            print(f"   beneficiary: {sell_data['beneficiary']}")
            print(f"   paths: {len(sell_data['path'])} route(s)")
            print(f"   deadline: {sell_data['deadline']} (Unix timestamp)")
            
            # Encode the struct
            calldata = self._encode_multiswap_struct(sell_data)
            
            if not calldata:
                raise Exception("Failed to encode multiSwap struct")
            
            full_calldata = self.multiswap_selector + calldata[2:]  # Add selector
            
            print(f"\n✅ MULTISWAP CALLDATA BUILT:")
            print(f"   Method: multiSwap")
            print(f"   Selector: {self.multiswap_selector}")
            print(f"   Calldata length: {len(full_calldata)} chars ({len(full_calldata)//2} bytes)")
            print(f"   Augustus V5 Router: {self.augustus_v5}")
            print("=" * 80)
            
            return {
                'calldata': full_calldata,
                'method_selector': self.multiswap_selector,
                'method_name': 'multiSwap',
                'augustus_router': self.augustus_v5,
                'from_token': from_token_addr,
                'to_token': to_token_addr,
                'from_amount': from_amount,
                'min_to_amount': min_amount,
                'expected_amount': expected_amount,
                'beneficiary': beneficiary,
                'deadline': deadline,
                'struct_params': sell_data
            }
            
        except Exception as e:
            print(f"❌ Error building multiSwap calldata: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _build_paths_from_paraswap(self, price_route: Dict[str, Any], to_token: str) -> List[Dict[str, Any]]:
        """
        Build path array from ParaSwap price route
        
        CRITICAL: Uses ArbitrumAdapter01 (0x369A2FDb910d432f0a07381a5E3d27572c876713) 
        as the adapter for ALL routes. This single generic adapter handles all DEX 
        swaps on Arbitrum (UniswapV3, Sushi, Camelot, etc.) internally via payload routing.
        """
        try:
            paths = []
            best_route = price_route.get('bestRoute', [])
            
            if not best_route:
                raise ValueError("No bestRoute in ParaSwap response - cannot build paths without routing data")
            
            # Build paths from ParaSwap bestRoute
            for i, route_segment in enumerate(best_route):
                swaps = route_segment.get('swaps', [])
                
                routes = []
                for swap in swaps:
                    swap_exchanges = swap.get('swapExchanges', [])
                    
                    for exchange_data in swap_exchanges:
                        # CRITICAL: Extract router and payload from ParaSwap data
                        # exchange_data['exchange'] is symbolic name ("UniswapV2") NOT an address
                        # Real router address is in exchange_data['data']['router']
                        # Payload for DEX swap is in exchange_data['data'].get('payload')
                        
                        exchange_name = exchange_data.get('exchange', 'Unknown')
                        data_field = exchange_data.get('data', {})
                        
                        # Safely extract and validate router address
                        router_address = data_field.get('router')
                        if not router_address or not isinstance(router_address, str):
                            raise ValueError(f"Missing or invalid router address in ParaSwap data for {exchange_name}")
                        
                        # Validate router is a hex address
                        if not router_address.startswith('0x') or len(router_address) != 42:
                            raise ValueError(f"Invalid router address format: {router_address}")
                        
                        # Extract payload (may be empty string or missing)
                        payload_hex = data_field.get('payload', '')
                        if payload_hex and isinstance(payload_hex, str) and payload_hex.startswith('0x'):
                            payload_bytes = bytes.fromhex(payload_hex[2:])
                        else:
                            payload_bytes = b''
                        
                        routes.append({
                            'exchange': self.arbitrum_adapter,  # Always use ArbitrumAdapter01
                            'targetExchange': self.w3.to_checksum_address(router_address),
                            'percent': int(exchange_data.get('percent', 10000)),
                            'payload': payload_bytes,  # Forward ParaSwap payload
                            'networkFee': int(exchange_data.get('networkFee', 0))
                        })
                        
                        payload_info = f"{len(payload_bytes)} bytes" if payload_bytes else "empty"
                        print(f"      Route: {exchange_name} → ArbitrumAdapter01 → {router_address[:10]}... (payload: {payload_info}, {exchange_data.get('percent', 100)}%)")
                
                if routes:
                    dest_token = route_segment.get('destToken', to_token)
                    paths.append({
                        'to': self.w3.to_checksum_address(dest_token),
                        'totalNetworkFee': int(route_segment.get('networkFee', 0)),
                        'routes': routes
                    })
            
            if not paths:
                raise ValueError("Failed to build any valid paths from ParaSwap route data")
            
            print(f"   ✅ Built {len(paths)} path(s) with {sum(len(p['routes']) for p in paths)} route(s)")
            print(f"      All routes use ArbitrumAdapter01: {self.arbitrum_adapter}")
            
            return paths
            
        except Exception as e:
            print(f"   ❌ Error building paths: {e}")
            raise  # Re-raise instead of returning invalid fallback
    
    def _encode_multiswap_struct(self, sell_data: Dict[str, Any]) -> Optional[str]:
        """Encode SellData struct using eth_abi"""
        try:
            # Define the SellData tuple structure for encoding
            # (address,uint256,uint256,uint256,address,(address,uint256,(address,address,uint256,bytes,uint256)[])[],address,uint256,bytes,uint256,bytes16)
            
            # Encode paths
            encoded_paths = []
            for path in sell_data['path']:
                encoded_routes = []
                for route in path['routes']:
                    encoded_routes.append((
                        route['exchange'],
                        route['targetExchange'],
                        route['percent'],
                        route['payload'],
                        route['networkFee']
                    ))
                
                encoded_paths.append((
                    path['to'],
                    path['totalNetworkFee'],
                    encoded_routes
                ))
            
            # Encode the complete SellData struct
            encoded = encode(
                ['(address,uint256,uint256,uint256,address,(address,uint256,(address,address,uint256,bytes,uint256)[])[],address,uint256,bytes,uint256,bytes16)'],
                [(
                    sell_data['fromToken'],
                    sell_data['fromAmount'],
                    sell_data['toAmount'],
                    sell_data['expectedAmount'],
                    sell_data['beneficiary'],
                    encoded_paths,
                    sell_data['partner'],
                    sell_data['feePercent'],
                    sell_data['permit'],
                    sell_data['deadline'],
                    sell_data['uuid']
                )]
            )
            
            return '0x' + encoded.hex()
            
        except Exception as e:
            print(f"❌ Encoding error: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    # Test the builder
    from web3 import Web3
    
    w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
    
    builder = AugustusV5MultiSwapBuilder(w3, network="arbitrum")
    
    # Test: Build multiSwap for ARB → DAI swap (reverse of our debt swap)
    # We need to swap ARB to get DAI to repay debt
    test_debt_switch = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
    
    result = builder.build_multiswap_calldata(
        from_token='ARB',
        to_token='DAI',
        from_amount=int(60 * 1e18),  # 60 ARB
        min_to_amount=int(24 * 1e18),  # Min 24 DAI out
        beneficiary=test_debt_switch,
        slippage_bps=400  # 4% slippage
    )
    
    if result:
        print(f"\n✅ TEST SUCCESSFUL!")
        print(f"   Calldata: {result['calldata'][:100]}...")
        print(f"   Method: {result['method_name']}")
        print(f"   Selector: {result['method_selector']}")
    else:
        print(f"\n❌ TEST FAILED!")
