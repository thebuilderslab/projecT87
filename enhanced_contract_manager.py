
#!/usr/bin/env python3
"""
ENHANCED CONTRACT MANAGER
Optimized RPC endpoint selection and contract interaction reliability
"""

import os
import time
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

class EnhancedContractManager:
    def __init__(self):
        self.arbitrum_mainnet_rpcs = [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.publicnode.com", 
            "https://arbitrum.blockpi.network/v1/rpc/public",
            "https://rpc.ankr.com/arbitrum",
            "https://arbitrum-one.public.blastapi.io",
            "https://endpoints.omniatech.io/v1/arbitrum/one/public",
            "https://arbitrum.llamarpc.com"
        ]
        
        self.working_rpc = None
        self.w3 = None
        self.rpc_performance = {}
        self.last_rpc_test = 0
        self.test_interval = 300  # 5 minutes
        
        # Token addresses (Arbitrum Mainnet)
        self.usdc_address = "0xff970a61a04b1ca14834a651bab06d7307796618"  # USDC.e (most liquid)
        self.wbtc_address = "0x2f2a259a8e58ac855e77f1ca9e0b950da8e53331"  # WBTC
        self.weth_address = "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"  # WETH
        self.arb_address = "0x912ce59144191c1204e64559fe83e3a5095c6afd"  # ARB
        
    def test_rpc_performance(self, rpc_url, timeout=5):
        """Test RPC performance with multiple metrics"""
        try:
            start_time = time.time()
            
            # Create Web3 instance
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': timeout}))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            connection_time = time.time() - start_time
            
            if not w3.is_connected():
                return None
            
            # Test chain ID
            chain_start = time.time()
            chain_id = w3.eth.chain_id
            chain_time = time.time() - chain_start
            
            if chain_id != 42161:
                return None
            
            # Test latest block
            block_start = time.time()
            latest_block = w3.eth.get_block('latest')
            block_time = time.time() - block_start
            
            # Test gas price
            gas_start = time.time()
            gas_price = w3.eth.gas_price
            gas_time = time.time() - gas_start
            
            # Test token balance call (USDC)
            token_start = time.time()
            try:
                # Simple balance check
                balance_data = w3.eth.call({
                    'to': Web3.to_checksum_address(self.usdc_address),
                    'data': '0x70a08231000000000000000000000000' + '0000000000000000000000000000000000000000'[2:]
                })
                token_time = time.time() - token_start
            except Exception:
                token_time = 999  # High penalty for failed token calls
            
            total_time = time.time() - start_time
            
            score = 1000 / (total_time + token_time + block_time)  # Higher is better
            
            return {
                'url': rpc_url,
                'score': score,
                'total_time': total_time,
                'connection_time': connection_time,
                'chain_time': chain_time,
                'block_time': block_time,
                'gas_time': gas_time,
                'token_time': token_time,
                'block_number': latest_block.number,
                'gas_price': gas_price,
                'timestamp': time.time()
            }
            
        except Exception as e:
            print(f"❌ RPC {rpc_url} failed performance test: {e}")
            return None
    
    def find_optimal_rpc(self, force_retest=False):
        """Find the optimal RPC endpoint using parallel testing"""
        current_time = time.time()
        
        # Skip retesting if recently tested and have working RPC
        if (not force_retest and 
            self.working_rpc and 
            (current_time - self.last_rpc_test) < self.test_interval):
            return True
        
        print("🔍 Testing RPC endpoints for optimal performance...")
        
        # Test all RPCs in parallel
        with ThreadPoolExecutor(max_workers=len(self.arbitrum_mainnet_rpcs)) as executor:
            future_to_rpc = {
                executor.submit(self.test_rpc_performance, rpc_url): rpc_url 
                for rpc_url in self.arbitrum_mainnet_rpcs
            }
            
            results = []
            for future in as_completed(future_to_rpc, timeout=10):
                result = future.result()
                if result:
                    results.append(result)
        
        if not results:
            print("❌ No working RPC endpoints found")
            return False
        
        # Sort by performance score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Update performance tracking
        for result in results:
            self.rpc_performance[result['url']] = result
        
        # Use best performing RPC
        best_rpc = results[0]
        self.working_rpc = best_rpc['url']
        
        # Create Web3 instance
        self.w3 = Web3(Web3.HTTPProvider(self.working_rpc, request_kwargs={'timeout': 30}))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        self.last_rpc_test = current_time
        
        print(f"✅ Optimal RPC selected: {self.working_rpc}")
        print(f"   Performance score: {best_rpc['score']:.2f}")
        print(f"   Total response time: {best_rpc['total_time']:.3f}s")
        print(f"   Token call time: {best_rpc['token_time']:.3f}s")
        
        return True
    
    def get_token_balance_robust(self, token_address, wallet_address, retries=3):
        """Get token balance with robust error handling and automatic RPC switching"""
        
        for attempt in range(retries):
            try:
                if not self.w3 or not self.w3.is_connected():
                    if not self.find_optimal_rpc():
                        continue
                
                # Method 1: Standard contract call
                try:
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
                    
                    balance_wei = contract.functions.balanceOf(wallet_address).call()
                    try:
                        decimals = contract.functions.decimals().call()
                    except:
                        # Default decimals for known tokens
                        if token_address.lower() == self.usdc_address.lower():
                            decimals = 6
                        elif token_address.lower() == self.wbtc_address.lower():
                            decimals = 8
                        else:
                            decimals = 18
                    
                    balance = balance_wei / (10 ** decimals)
                    print(f"✅ Token balance retrieved: {balance:.8f}")
                    return balance
                    
                except Exception as e:
                    print(f"⚠️ Standard method failed: {e}")
                    
                    # Method 2: Raw eth_call
                    try:
                        function_signature = "0x70a08231"  # balanceOf(address)
                        padded_address = wallet_address[2:].zfill(64) if wallet_address.startswith('0x') else wallet_address.zfill(64)
                        call_data = function_signature + padded_address
                        
                        result = self.w3.eth.call({
                            'to': Web3.to_checksum_address(token_address),
                            'data': call_data
                        })
                        
                        if result and result != b'':
                            balance_wei = int.from_bytes(result, byteorder='big')
                            
                            # Use appropriate decimals
                            if token_address.lower() == self.usdc_address.lower():
                                decimals = 6
                            elif token_address.lower() == self.wbtc_address.lower():
                                decimals = 8
                            else:
                                decimals = 18
                                
                            balance = balance_wei / (10 ** decimals)
                            print(f"✅ Token balance (raw call): {balance:.8f}")
                            return balance
                            
                    except Exception as e2:
                        print(f"⚠️ Raw call method failed: {e2}")
                        
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                
                if attempt < retries - 1:
                    # Force RPC retest on failure
                    print("🔄 Switching to different RPC endpoint...")
                    self.find_optimal_rpc(force_retest=True)
                    time.sleep(1)
        
        print(f"❌ All attempts failed for token balance")
        return 0.0
    
    def get_aave_data_robust(self, wallet_address, aave_pool_address):
        """Get Aave data with robust error handling"""
        
        try:
            if not self.w3 or not self.w3.is_connected():
                if not self.find_optimal_rpc():
                    return None
            
            # Aave V3 Pool ABI (getUserAccountData function)
            pool_abi = [{
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
            }]
            
            pool_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(aave_pool_address),
                abi=pool_abi
            )
            
            # Get user account data
            account_data = pool_contract.functions.getUserAccountData(wallet_address).call()
            
            # Parse the results (Aave returns values in base units)
            total_collateral_base = account_data[0] / 1e8  # Base currency (USD)
            total_debt_base = account_data[1] / 1e8
            available_borrows_base = account_data[2] / 1e8
            health_factor = account_data[5] / 1e18 if account_data[5] > 0 else float('inf')
            
            aave_data = {
                'health_factor': health_factor,
                'total_collateral_usd': total_collateral_base,
                'total_debt_usd': total_debt_base,
                'available_borrows_usd': available_borrows_base,
                'data_source': 'direct_aave_contract',
                'timestamp': time.time()
            }
            
            print(f"✅ Aave data retrieved successfully")
            print(f"   Health Factor: {health_factor:.2f}")
            print(f"   Collateral: ${total_collateral_base:.2f}")
            print(f"   Debt: ${total_debt_base:.2f}")
            
            return aave_data
            
        except Exception as e:
            print(f"❌ Aave data fetch failed: {e}")
            return None
    
    def optimize_for_contract_calls(self):
        """Optimize RPC selection specifically for contract interactions"""
        
        print("🔧 Optimizing RPC for contract calls...")
        
        # Test each RPC specifically for contract call performance
        contract_scores = {}
        
        for rpc_url in self.arbitrum_mainnet_rpcs:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                
                if not w3.is_connected() or w3.eth.chain_id != 42161:
                    continue
                
                # Test multiple contract calls
                start_time = time.time()
                
                # Test 1: USDC balance call
                try:
                    usdc_result = w3.eth.call({
                        'to': Web3.to_checksum_address(self.usdc_address),
                        'data': '0x70a08231000000000000000000000000' + '0000000000000000000000000000000000000000'[2:]
                    })
                    usdc_success = True
                except:
                    usdc_success = False
                
                # Test 2: Aave pool call
                try:
                    aave_pool = "0x794a61358d6845594f94dc1db02a252b5b4814ad"
                    # getUserAccountData call
                    aave_data = '0xbf92857c000000000000000000000000' + '0000000000000000000000000000000000000000'[2:]
                    aave_result = w3.eth.call({
                        'to': Web3.to_checksum_address(aave_pool),
                        'data': aave_data
                    })
                    aave_success = True
                except:
                    aave_success = False
                
                call_time = time.time() - start_time
                
                # Score based on success rate and speed
                success_rate = (usdc_success + aave_success) / 2
                speed_score = 1 / (call_time + 0.1)  # Avoid division by zero
                
                contract_scores[rpc_url] = {
                    'score': success_rate * speed_score,
                    'usdc_success': usdc_success,
                    'aave_success': aave_success,
                    'call_time': call_time,
                    'success_rate': success_rate
                }
                
                print(f"📊 {rpc_url}: Success={success_rate:.1%}, Time={call_time:.3f}s")
                
            except Exception as e:
                print(f"❌ {rpc_url} failed contract optimization test: {e}")
                continue
        
        if not contract_scores:
            print("❌ No RPCs passed contract optimization tests")
            return False
        
        # Select best RPC for contract calls
        best_rpc = max(contract_scores.keys(), key=lambda x: contract_scores[x]['score'])
        
        self.working_rpc = best_rpc
        self.w3 = Web3(Web3.HTTPProvider(best_rpc, request_kwargs={'timeout': 30}))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        print(f"✅ Optimized RPC for contracts: {best_rpc}")
        print(f"   Contract success rate: {contract_scores[best_rpc]['success_rate']:.1%}")
        print(f"   Call time: {contract_scores[best_rpc]['call_time']:.3f}s")
        
        return True

if __name__ == "__main__":
    manager = EnhancedContractManager()
    
    print("🚀 Testing Enhanced Contract Manager")
    print("=" * 50)
    
    # Test optimization
    if manager.optimize_for_contract_calls():
        print("\n📋 Testing token balance retrieval...")
        
        # Test wallet (you can replace with actual address)
        test_wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        
        # Test USDC balance
        usdc_balance = manager.get_token_balance_robust(manager.usdc_address, test_wallet)
        print(f"USDC Balance: {usdc_balance}")
        
        # Test Aave data
        aave_pool = "0x794a61358d6845594f94dc1db02a252b5b4814ad"
        aave_data = manager.get_aave_data_robust(test_wallet, aave_pool)
        if aave_data:
            print(f"Aave Health Factor: {aave_data['health_factor']}")
        
    else:
        print("❌ Contract optimization failed")
