#!/usr/bin/env python3
"""
Aave Debt Swap Adapter - Direct debt position swapping
Implements Aave V3 ParaSwapDebtSwapAdapter integration for DAI ↔ ARB debt swaps
Similar to GHO→ARB debt swaps shown in Aave interface
"""

import os
import time
import json
import traceback
from datetime import datetime
from typing import Dict, Optional, Tuple
from web3 import Web3

class AaveDebtSwapAdapter:
    """
    Aave V3 Debt Swap Adapter for Arbitrum Mainnet
    Enables direct swapping of debt positions (DAI debt ↔ ARB debt)
    """
    
    def __init__(self, agent):
        """Initialize debt swap adapter with agent and contract configurations"""
        self.agent = agent
        self.w3 = agent.w3
        self.address = agent.address
        self.private_key = agent.private_key
        
        # Aave V3 Contract Addresses (Arbitrum Mainnet) - Using canonical addresses
        self.aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.paraswap_debt_swap_adapter = "0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9"
        
        # Token Addresses (Arbitrum Mainnet)
        self.dai_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
        self.arb_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
        
        # Initialize contracts
        self._initialize_contracts()
        
        print(f"✅ Aave Debt Swap Adapter initialized")
        print(f"   Pool: {self.aave_pool_address}")
        print(f"   Debt Swap Adapter: {self.paraswap_debt_swap_adapter}")
        
    def _initialize_contracts(self):
        """Initialize Aave contracts with required ABIs"""
        
        # ParaSwap Debt Swap Adapter ABI (key functions)
        self.debt_swap_abi = [
            {
                "inputs": [
                    {
                        "components": [
                            {"name": "debtAsset", "type": "address"},
                            {"name": "newDebtAsset", "type": "address"},
                            {"name": "debtRepayAmount", "type": "uint256"},
                            {"name": "maxNewDebtAmount", "type": "uint256"},
                            {"name": "extraCollateralAmount", "type": "uint256"},
                            {"name": "extraCollateralAsset", "type": "address"},
                            {"name": "offset", "type": "uint256"},
                            {"name": "paraswapData", "type": "bytes"}
                        ],
                        "name": "debtSwapParams",
                        "type": "tuple"
                    },
                    {
                        "components": [
                            {"name": "debtToken", "type": "address"},
                            {"name": "value", "type": "uint256"},
                            {"name": "deadline", "type": "uint256"},
                            {"name": "v", "type": "uint8"},
                            {"name": "r", "type": "bytes32"},
                            {"name": "s", "type": "bytes32"}
                        ],
                        "name": "creditDelegationPermit",
                        "type": "tuple"
                    }
                ],
                "name": "swapDebt",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        # Standard Aave Pool ABI for debt operations
        self.pool_abi = [
            {
                "inputs": [{"name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"name": "totalCollateralBase", "type": "uint256"},
                    {"name": "totalDebtBase", "type": "uint256"},
                    {"name": "availableBorrowsBase", "type": "uint256"},
                    {"name": "currentLiquidationThreshold", "type": "uint256"},
                    {"name": "ltv", "type": "uint256"},
                    {"name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "asset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "interestRateMode", "type": "uint256"},
                    {"name": "referralCode", "type": "uint16"},
                    {"name": "onBehalfOf", "type": "address"}
                ],
                "name": "borrow",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        # Initialize contract instances
        self.debt_swap_contract = self.w3.eth.contract(
            address=self.paraswap_debt_swap_adapter,
            abi=self.debt_swap_abi
        )
        
        self.pool_contract = self.w3.eth.contract(
            address=self.aave_pool_address,
            abi=self.pool_abi
        )
        
    def get_current_debt_positions(self) -> Dict:
        """Get current debt positions from Aave"""
        try:
            print("🔍 CHECKING CURRENT DEBT POSITIONS...")
            
            # Get account data from Aave
            account_data = self.pool_contract.functions.getUserAccountData(self.address).call()
            
            # Parse basic position data
            total_collateral_usd = account_data[0] / (10**8)
            total_debt_usd = account_data[1] / (10**8)
            available_borrows_usd = account_data[2] / (10**8)
            health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
            
            # Get specific debt token balances
            dai_debt = self._get_debt_balance(self.dai_address)
            arb_debt = self._get_debt_balance(self.arb_address)
            
            position_data = {
                'total_collateral_usd': total_collateral_usd,
                'total_debt_usd': total_debt_usd,
                'available_borrows_usd': available_borrows_usd,
                'health_factor': health_factor,
                'dai_debt': dai_debt,
                'arb_debt': arb_debt,
                'timestamp': time.time()
            }
            
            print(f"📊 CURRENT DEBT POSITION:")
            print(f"   Total Collateral: ${total_collateral_usd:.2f}")
            print(f"   Total Debt: ${total_debt_usd:.2f}")
            print(f"   Health Factor: {health_factor:.6f}")
            print(f"   DAI Debt: {dai_debt:.6f}")
            print(f"   ARB Debt: {arb_debt:.6f}")
            
            return position_data
            
        except Exception as e:
            print(f"❌ Error getting debt positions: {e}")
            return {}
    
    def _get_debt_balance(self, token_address: str) -> float:
        """Get debt balance for specific token"""
        try:
            # Standard debt token ABI for balance check
            debt_token_abi = [
                {
                    "inputs": [{"name": "user", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Get variable debt token address (implementation specific)
            # For now, return 0 - this would need to be implemented with proper debt token addresses
            return 0.0
            
        except Exception as e:
            print(f"⚠️ Error getting debt balance for {token_address}: {e}")
            return 0.0
    
    def prepare_debt_swap_params(self, from_debt_asset: str, to_debt_asset: str, 
                                swap_amount_usd: float, max_slippage: float = 0.01) -> Dict:
        """Prepare parameters for debt swap operation"""
        try:
            print(f"🔧 PREPARING DEBT SWAP PARAMETERS...")
            print(f"   From: {from_debt_asset}")
            print(f"   To: {to_debt_asset}")
            print(f"   Amount: ${swap_amount_usd:.2f}")
            print(f"   Max Slippage: {max_slippage*100:.1f}%")
            
            # Convert USD amount to token amounts
            if from_debt_asset == self.dai_address:
                debt_repay_amount = int(swap_amount_usd * 1e18)  # DAI has 18 decimals
                from_symbol = "DAI"
            elif from_debt_asset == self.arb_address:
                # Get ARB price to calculate amount
                arb_price = self._get_arb_price_usd()
                debt_repay_amount = int((swap_amount_usd / arb_price) * 1e18)
                from_symbol = "ARB"
            else:
                raise ValueError(f"Unsupported debt asset: {from_debt_asset}")
            
            # Calculate maximum new debt amount with slippage protection
            if to_debt_asset == self.dai_address:
                max_new_debt_amount = int(swap_amount_usd * (1 + max_slippage) * 1e18)
                to_symbol = "DAI"
            elif to_debt_asset == self.arb_address:
                arb_price = self._get_arb_price_usd()
                max_new_debt_amount = int((swap_amount_usd * (1 + max_slippage) / arb_price) * 1e18)
                to_symbol = "ARB"
            else:
                raise ValueError(f"Unsupported target debt asset: {to_debt_asset}")
            
            # Prepare debt swap parameters structure
            debt_swap_params = {
                'debtAsset': from_debt_asset,
                'newDebtAsset': to_debt_asset,
                'debtRepayAmount': debt_repay_amount,
                'maxNewDebtAmount': max_new_debt_amount,
                'extraCollateralAmount': 0,  # No additional collateral needed
                'extraCollateralAsset': "0x0000000000000000000000000000000000000000",
                'offset': 0,  # ParaSwap data offset
                'paraswapData': b''  # Will be populated with actual swap data
            }
            
            print(f"✅ Debt swap parameters prepared:")
            print(f"   Repay Amount: {debt_repay_amount / 1e18:.6f} {from_symbol}")
            print(f"   Max New Debt: {max_new_debt_amount / 1e18:.6f} {to_symbol}")
            
            return debt_swap_params
            
        except Exception as e:
            print(f"❌ Error preparing debt swap parameters: {e}")
            return {}
    
    def _get_arb_price_usd(self) -> float:
        """Get current ARB price in USD"""
        try:
            # For demo purposes, using approximate price
            # In production, this should fetch from price oracle or API
            return 0.55  # Approximate ARB price in USD
            
        except Exception as e:
            print(f"⚠️ Error getting ARB price: {e}")
            return 0.55  # Fallback price
    
    def execute_dai_debt_to_arb_debt_swap(self, swap_amount_usd: float) -> Dict:
        """Execute DAI debt → ARB debt swap"""
        print(f"\n🔄 EXECUTING DAI DEBT → ARB DEBT SWAP: ${swap_amount_usd:.2f}")
        print("=" * 70)
        
        swap_result = {
            'operation': 'DAI_DEBT_TO_ARB_DEBT_SWAP',
            'start_time': datetime.now().isoformat(),
            'input_amount_usd': swap_amount_usd,
            'success': False
        }
        
        try:
            # Get initial debt positions
            initial_position = self.get_current_debt_positions()
            swap_result['initial_position'] = initial_position
            
            # Safety checks
            if initial_position.get('health_factor', 0) < 1.5:
                raise Exception(f"Health factor too low: {initial_position.get('health_factor', 0):.6f}")
            
            if initial_position.get('dai_debt', 0) < swap_amount_usd:
                raise Exception(f"Insufficient DAI debt: ${initial_position.get('dai_debt', 0):.2f} < ${swap_amount_usd:.2f}")
            
            # Prepare debt swap parameters
            debt_swap_params = self.prepare_debt_swap_params(
                from_debt_asset=self.dai_address,
                to_debt_asset=self.arb_address,
                swap_amount_usd=swap_amount_usd,
                max_slippage=0.01  # 1% slippage tolerance
            )
            
            if not debt_swap_params:
                raise Exception("Failed to prepare debt swap parameters")
            
            # NOTE: This is a simplified implementation
            # In production, this would need:
            # 1. ParaSwap API integration to get swap data
            # 2. Credit delegation setup
            # 3. Proper gas estimation and transaction building
            # 4. Flash loan coordination
            
            print(f"⚠️ DEBT SWAP SIMULATION MODE")
            print(f"📋 Would execute debt swap with parameters:")
            print(f"   From Debt Asset: {debt_swap_params['debtAsset']}")
            print(f"   To Debt Asset: {debt_swap_params['newDebtAsset']}")
            print(f"   Repay Amount: {debt_swap_params['debtRepayAmount']}")
            print(f"   Max New Debt: {debt_swap_params['maxNewDebtAmount']}")
            
            # For now, simulate successful completion
            swap_result['success'] = True
            swap_result['simulated'] = True
            swap_result['debt_swap_params'] = debt_swap_params
            
            print(f"✅ DAI DEBT → ARB DEBT SWAP SIMULATION COMPLETED")
            
            return swap_result
            
        except Exception as e:
            print(f"❌ DAI debt → ARB debt swap failed: {e}")
            swap_result['error'] = str(e)
            swap_result['error_details'] = traceback.format_exc()
            return swap_result
        
        finally:
            swap_result['end_time'] = datetime.now().isoformat()
    
    def execute_arb_debt_to_dai_debt_swap(self, swap_amount_usd: float) -> Dict:
        """Execute ARB debt → DAI debt swap"""
        print(f"\n🔄 EXECUTING ARB DEBT → DAI DEBT SWAP: ${swap_amount_usd:.2f}")
        print("=" * 70)
        
        swap_result = {
            'operation': 'ARB_DEBT_TO_DAI_DEBT_SWAP',
            'start_time': datetime.now().isoformat(),
            'input_amount_usd': swap_amount_usd,
            'success': False
        }
        
        try:
            # Get initial debt positions
            initial_position = self.get_current_debt_positions()
            swap_result['initial_position'] = initial_position
            
            # Safety checks
            if initial_position.get('health_factor', 0) < 1.5:
                raise Exception(f"Health factor too low: {initial_position.get('health_factor', 0):.6f}")
            
            if initial_position.get('arb_debt', 0) < swap_amount_usd:
                raise Exception(f"Insufficient ARB debt: ${initial_position.get('arb_debt', 0):.2f} < ${swap_amount_usd:.2f}")
            
            # Prepare debt swap parameters
            debt_swap_params = self.prepare_debt_swap_params(
                from_debt_asset=self.arb_address,
                to_debt_asset=self.dai_address,
                swap_amount_usd=swap_amount_usd,
                max_slippage=0.01  # 1% slippage tolerance
            )
            
            if not debt_swap_params:
                raise Exception("Failed to prepare debt swap parameters")
            
            print(f"⚠️ DEBT SWAP SIMULATION MODE")
            print(f"📋 Would execute debt swap with parameters:")
            print(f"   From Debt Asset: {debt_swap_params['debtAsset']}")
            print(f"   To Debt Asset: {debt_swap_params['newDebtAsset']}")
            print(f"   Repay Amount: {debt_swap_params['debtRepayAmount']}")
            print(f"   Max New Debt: {debt_swap_params['maxNewDebtAmount']}")
            
            # For now, simulate successful completion
            swap_result['success'] = True
            swap_result['simulated'] = True
            swap_result['debt_swap_params'] = debt_swap_params
            
            print(f"✅ ARB DEBT → DAI DEBT SWAP SIMULATION COMPLETED")
            
            return swap_result
            
        except Exception as e:
            print(f"❌ ARB debt → DAI debt swap failed: {e}")
            swap_result['error'] = str(e)
            swap_result['error_details'] = traceback.format_exc()
            return swap_result
        
        finally:
            swap_result['end_time'] = datetime.now().isoformat()
    
    def execute_contrarian_debt_swap_cycle(self, swap_amount_usd: float = 5.0) -> Dict:
        """Execute complete contrarian debt swap cycle: DAI debt → ARB debt → DAI debt"""
        print(f"\n🎯 EXECUTING CONTRARIAN DEBT SWAP CYCLE: ${swap_amount_usd:.2f}")
        print("=" * 80)
        
        cycle_result = {
            'operation': 'CONTRARIAN_DEBT_SWAP_CYCLE',
            'start_time': datetime.now().isoformat(),
            'cycle_amount_usd': swap_amount_usd,
            'operations': {},
            'overall_success': False
        }
        
        try:
            # Get initial position
            initial_position = self.get_current_debt_positions()
            cycle_result['initial_position'] = initial_position
            
            print(f"📊 INITIAL DEBT POSITION:")
            print(f"   Health Factor: {initial_position.get('health_factor', 0):.6f}")
            print(f"   Total Debt: ${initial_position.get('total_debt_usd', 0):.2f}")
            
            # Phase 1: DAI debt → ARB debt (Contrarian entry)
            print(f"\n🚀 PHASE 1: DAI DEBT → ARB DEBT (CONTRARIAN ENTRY)")
            dai_to_arb_result = self.execute_dai_debt_to_arb_debt_swap(swap_amount_usd)
            cycle_result['operations']['dai_to_arb_debt_swap'] = dai_to_arb_result
            
            if not dai_to_arb_result.get('success'):
                raise Exception("Phase 1 (DAI → ARB debt swap) failed")
            
            # Wait between operations
            print(f"\n⏳ Waiting 10 seconds between operations...")
            time.sleep(10)
            
            # Phase 2: ARB debt → DAI debt (Contrarian exit)
            print(f"\n🚀 PHASE 2: ARB DEBT → DAI DEBT (CONTRARIAN EXIT)")
            arb_to_dai_result = self.execute_arb_debt_to_dai_debt_swap(swap_amount_usd)
            cycle_result['operations']['arb_to_dai_debt_swap'] = arb_to_dai_result
            
            if not arb_to_dai_result.get('success'):
                raise Exception("Phase 2 (ARB → DAI debt swap) failed")
            
            # Get final position
            final_position = self.get_current_debt_positions()
            cycle_result['final_position'] = final_position
            
            # Calculate results
            successful_operations = sum(1 for op in cycle_result['operations'].values() if op.get('success', False))
            total_operations = len(cycle_result['operations'])
            
            cycle_result['successful_operations'] = successful_operations
            cycle_result['total_operations'] = total_operations
            cycle_result['overall_success'] = successful_operations == total_operations
            
            print(f"\n🏆 CONTRARIAN DEBT SWAP CYCLE COMPLETED")
            print("=" * 80)
            print(f"✅ Overall Success: {'YES' if cycle_result['overall_success'] else 'NO'}")
            print(f"✅ Successful Operations: {successful_operations}/{total_operations}")
            print(f"📊 Health Factor: {initial_position.get('health_factor', 0):.6f} → {final_position.get('health_factor', 0):.6f}")
            
            return cycle_result
            
        except Exception as e:
            print(f"❌ Contrarian debt swap cycle failed: {e}")
            cycle_result['error'] = str(e)
            cycle_result['error_details'] = traceback.format_exc()
            return cycle_result
        
        finally:
            cycle_result['end_time'] = datetime.now().isoformat()

def main():
    """Test debt swap adapter functionality"""
    print("🚀 AAVE DEBT SWAP ADAPTER - TESTING")
    print("=" * 60)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        
        # Initialize debt swap adapter
        debt_swap_adapter = AaveDebtSwapAdapter(agent)
        
        # Test debt position checking
        current_position = debt_swap_adapter.get_current_debt_positions()
        
        if current_position.get('health_factor', 0) < 1.5:
            print(f"⚠️ Health factor too low for debt swaps: {current_position.get('health_factor', 0):.6f}")
            return
        
        # Test contrarian debt swap cycle
        cycle_result = debt_swap_adapter.execute_contrarian_debt_swap_cycle(swap_amount_usd=5.0)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debt_swap_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(cycle_result, f, indent=2, default=str)
        
        print(f"\n📁 Debt swap test results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Debt swap adapter test failed: {e}")
        print(f"   Error details: {traceback.format_exc()}")

if __name__ == "__main__":
    main()