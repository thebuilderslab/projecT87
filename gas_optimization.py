#!/usr/bin/env python3
"""
Gas Optimization Module - Dynamic gas cost optimization with CoinAPI integration
Handles live gas prices, buffer calculations, and budget management
"""

import os
import requests
import time
from typing import Dict, Optional
from decimal import Decimal
from web3 import Web3

COIN_API_KEY = os.environ.get("COIN_API")
assert COIN_API_KEY is not None, "CoinAPI secret missing; aborting."

class CoinAPIGasOptimizer:
    """Dynamic gas optimization using real-time ETH prices from CoinAPI"""
    
    def __init__(self, w3: Web3, max_usd_per_tx: float = 10.0):
        self.w3 = w3
        self.coin_api_key = COIN_API_KEY
        self.max_usd_per_tx = max_usd_per_tx
        self.default_buffer_percent = 2.0  # 2% default buffer
        
        print(f"⛽ Gas Optimizer initialized with ${max_usd_per_tx} USD budget cap")
    
    def get_eth_price_coinapi(self) -> Dict:
        """Get real-time ETH price using CoinAPI with comprehensive logging"""
        try:
            print(f"\n💰 FETCHING REAL-TIME ETH PRICE")
            print("=" * 40)
            
            url = "https://rest.coinapi.io/v1/exchangerate/ETH/USD"
            headers = {"X-CoinAPI-Key": self.coin_api_key}
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            api_result = {
                'success': False,
                'price': 2500.0,  # Fallback
                'source': 'fallback',
                'response_time': response_time,
                'api_status': response.status_code,
                'timestamp': time.time()
            }
            
            if response.status_code == 200:
                data = response.json()
                eth_price = float(data['rate'])
                
                api_result.update({
                    'success': True,
                    'price': eth_price,
                    'source': 'coinapi',
                    'raw_response': data
                })
                
                print(f"✅ CoinAPI Success:")
                print(f"   ETH Price: ${eth_price:.2f}")
                print(f"   Response Time: {response_time:.3f}s")
                print(f"   Status: {response.status_code}")
                
            else:
                print(f"⚠️ CoinAPI Failed:")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                print(f"   Using fallback: ${api_result['price']:.2f}")
                
        except Exception as e:
            api_result['error'] = str(e)
            print(f"❌ CoinAPI Error: {e}")
            print(f"   Using fallback: ${api_result['price']:.2f}")
        
        return api_result
    
    def calculate_optimized_gas_params(self, 
                                     operation_type: str = 'debt_swap',
                                     buffer_percent: Optional[float] = None) -> Dict:
        """
        Calculate optimized gas parameters with comprehensive logging
        """
        if buffer_percent is None:
            buffer_percent = self.default_buffer_percent
            
        print(f"\n⛽ GAS OPTIMIZATION CALCULATION")
        print("=" * 50)
        print(f"Operation: {operation_type}")
        print(f"Buffer: {buffer_percent}%")
        print(f"Budget Cap: ${self.max_usd_per_tx}")
        
        optimization_result = {
            'success': False,
            'operation_type': operation_type,
            'buffer_percent': buffer_percent,
            'calculation_logs': [],
            'final_params': {},
            'budget_analysis': {},
            'timestamp': time.time()
        }
        
        try:
            # Step 1: Get current network gas conditions
            print(f"\n📡 NETWORK GAS CONDITIONS")
            print("-" * 30)
            
            base_gas_price = self.w3.eth.gas_price
            base_gas_gwei = self.w3.from_wei(base_gas_price, 'gwei')
            
            network_conditions = {
                'base_gas_price_wei': base_gas_price,
                'base_gas_price_gwei': float(base_gas_gwei),
                'block_number': self.w3.eth.block_number,
                'timestamp': time.time()
            }
            
            print(f"   Base Gas Price: {base_gas_gwei:.2f} gwei")
            print(f"   Block Number: {network_conditions['block_number']}")
            
            optimization_result['calculation_logs'].append({
                'step': 'network_conditions',
                'data': network_conditions
            })
            
            # Step 2: Get ETH price from CoinAPI
            eth_price_result = self.get_eth_price_coinapi()
            eth_price = eth_price_result['price']
            
            optimization_result['calculation_logs'].append({
                'step': 'eth_price_fetch',
                'data': eth_price_result
            })
            
            # Step 3: Calculate gas limits by operation type
            gas_limits = {
                'debt_swap': 350000,      # Conservative for ParaSwap + Aave
                'aave_borrow': 180000,
                'aave_supply': 150000,
                'token_approval': 60000,
                'simple_transfer': 21000
            }
            
            gas_limit = gas_limits.get(operation_type, 300000)
            
            print(f"\n🎯 GAS LIMIT CALCULATION")
            print("-" * 30)
            print(f"   Operation Type: {operation_type}")
            print(f"   Base Gas Limit: {gas_limit:,}")
            
            # Step 4: Apply buffer calculations
            buffer_multiplier = 1 + (buffer_percent / 100)
            buffered_gas_price = int(base_gas_price * buffer_multiplier)
            buffered_gas_gwei = self.w3.from_wei(buffered_gas_price, 'gwei')
            
            print(f"\n📊 BUFFER CALCULATION")
            print("-" * 30)
            print(f"   Buffer Percent: {buffer_percent}%")
            print(f"   Multiplier: {buffer_multiplier}")
            print(f"   Original: {base_gas_gwei:.2f} gwei")
            print(f"   Buffered: {buffered_gas_gwei:.2f} gwei")
            
            buffer_calculation = {
                'buffer_percent': buffer_percent,
                'buffer_multiplier': buffer_multiplier,
                'original_gas_price_gwei': float(base_gas_gwei),
                'buffered_gas_price_gwei': float(buffered_gas_gwei),
                'buffered_gas_price_wei': buffered_gas_price
            }
            
            optimization_result['calculation_logs'].append({
                'step': 'buffer_calculation',
                'data': buffer_calculation
            })
            
            # Step 5: Calculate USD costs and apply budget cap
            estimated_cost_wei = gas_limit * buffered_gas_price
            estimated_cost_eth = self.w3.from_wei(estimated_cost_wei, 'ether')
            estimated_cost_usd = float(estimated_cost_eth) * eth_price
            
            print(f"\n💰 COST ANALYSIS")
            print("-" * 30)
            print(f"   Gas Limit: {gas_limit:,}")
            print(f"   Gas Price: {buffered_gas_gwei:.2f} gwei")
            print(f"   Cost (ETH): {estimated_cost_eth:.8f}")
            print(f"   Cost (USD): ${estimated_cost_usd:.4f}")
            print(f"   Budget Cap: ${self.max_usd_per_tx}")
            
            budget_analysis = {
                'estimated_cost_eth': float(estimated_cost_eth),
                'estimated_cost_usd': estimated_cost_usd,
                'budget_cap_usd': self.max_usd_per_tx,
                'within_budget': estimated_cost_usd <= self.max_usd_per_tx,
                'budget_utilization_percent': (estimated_cost_usd / self.max_usd_per_tx) * 100
            }
            
            # Step 6: Apply budget cap if necessary
            final_gas_price = buffered_gas_price
            budget_capped = False
            
            if estimated_cost_usd > self.max_usd_per_tx:
                # Calculate maximum affordable gas price
                max_affordable_eth = self.max_usd_per_tx / eth_price
                max_affordable_gas_price = (max_affordable_eth * 1e18) / gas_limit
                
                # Ensure we don't go below 90% of market rate
                min_gas_price = int(base_gas_price * 0.9)
                final_gas_price = max(int(max_affordable_gas_price), min_gas_price)
                budget_capped = True
                
                final_cost_eth = (gas_limit * final_gas_price) / 1e18
                final_cost_usd = final_cost_eth * eth_price
                
                print(f"\n🚨 BUDGET CAP APPLIED")
                print("-" * 30)
                print(f"   Original Cost: ${estimated_cost_usd:.4f}")
                print(f"   Capped Cost: ${final_cost_usd:.4f}")
                print(f"   Adjusted Gas: {self.w3.from_wei(final_gas_price, 'gwei'):.2f} gwei")
                
                budget_analysis.update({
                    'budget_capped': True,
                    'final_cost_usd': final_cost_usd,
                    'gas_price_adjustment': 'capped_to_budget'
                })
            else:
                budget_analysis.update({
                    'budget_capped': False,
                    'final_cost_usd': estimated_cost_usd,
                    'gas_price_adjustment': 'buffered_only'
                })
            
            # Step 7: Final parameters
            final_params = {
                'gas': gas_limit,
                'gasPrice': final_gas_price,
                'gas_limit_safety_factor': 1.0,  # Already included in gas_limit
                'estimated_cost_usd': budget_analysis['final_cost_usd'],
                'eth_price_used': eth_price,
                'budget_capped': budget_capped,
                'buffer_applied_percent': buffer_percent
            }
            
            print(f"\n✅ FINAL GAS PARAMETERS")
            print("-" * 30)
            print(f"   Gas Limit: {final_params['gas']:,}")
            print(f"   Gas Price: {self.w3.from_wei(final_params['gasPrice'], 'gwei'):.2f} gwei")
            print(f"   Final Cost: ${final_params['estimated_cost_usd']:.4f}")
            print(f"   Budget Capped: {final_params['budget_capped']}")
            
            optimization_result.update({
                'success': True,
                'final_params': final_params,
                'budget_analysis': budget_analysis
            })
            
            return optimization_result
            
        except Exception as e:
            error_msg = f"Gas optimization failed: {e}"
            print(f"❌ {error_msg}")
            
            optimization_result['calculation_logs'].append({
                'step': 'error',
                'error': str(e),
                'timestamp': time.time()
            })
            
            return optimization_result
    
    def generate_gas_comparison_table(self, manual_gas_params: Dict, optimized_result: Dict) -> str:
        """Generate comparison table between manual and optimized gas parameters"""
        
        table = "\n📊 GAS PARAMETER COMPARISON TABLE\n"
        table += "=" * 60 + "\n"
        table += f"{'Parameter':<20} {'Manual':<15} {'Optimized':<15} {'Difference':<10}\n"
        table += "-" * 60 + "\n"
        
        manual_gas = manual_gas_params.get('gas', 0)
        manual_price = manual_gas_params.get('gasPrice', 0)
        manual_price_gwei = self.w3.from_wei(manual_price, 'gwei') if manual_price else 0
        
        opt_params = optimized_result.get('final_params', {})
        opt_gas = opt_params.get('gas', 0)
        opt_price = opt_params.get('gasPrice', 0)
        opt_price_gwei = self.w3.from_wei(opt_price, 'gwei') if opt_price else 0
        
        table += f"{'Gas Limit':<20} {manual_gas:<15,} {opt_gas:<15,} {opt_gas-manual_gas:<10,}\n"
        table += f"{'Gas Price (gwei)':<20} {manual_price_gwei:<15.2f} {opt_price_gwei:<15.2f} {opt_price_gwei-manual_price_gwei:<10.2f}\n"
        
        manual_cost = (manual_gas * manual_price) / 1e18 * 2500  # Assume $2500 ETH for manual
        opt_cost = opt_params.get('estimated_cost_usd', 0)
        
        table += f"{'Est. Cost (USD)':<20} ${manual_cost:<14.4f} ${opt_cost:<14.4f} ${opt_cost-manual_cost:<9.4f}\n"
        table += "=" * 60 + "\n"
        
        return table