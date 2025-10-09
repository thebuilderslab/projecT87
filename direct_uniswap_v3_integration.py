#!/usr/bin/env python3
"""
Direct Uniswap V3 Integration for Debt Swaps
Bypasses ParaSwap API to build compatible swapExactAmountOutOnUniswapV3 calldata
"""

import os
from web3 import Web3
from eth_abi import encode

class DirectUniswapV3Integration:
    """Build Uniswap V3 calldata directly for Aave Debt Switch compatibility"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
        
        # Uniswap V3 SwapRouter on Arbitrum
        self.uniswap_v3_router = self.w3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
        
        # Token addresses
        self.dai = self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
        self.arb = self.w3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548")
        
        # Pool fee (0.3% = 3000)
        self.pool_fee = 3000
    
    def build_exact_output_single_calldata(
        self,
        token_in: str,
        token_out: str,
        amount_out: int,
        amount_in_maximum: int,
        recipient: str,
        deadline: int
    ) -> str:
        """
        Build exactOutputSingle calldata for Uniswap V3
        
        Function signature: exactOutputSingle((address,address,uint24,address,uint256,uint256,uint256,uint160))
        Selector: 0x5023b4df
        """
        
        print(f"\n🔧 BUILDING DIRECT UNISWAP V3 CALLDATA")
        print(f"=" * 60)
        print(f"   Token In: {token_in}")
        print(f"   Token Out: {token_out}")
        print(f"   Amount Out: {amount_out} wei")
        print(f"   Amount In Max: {amount_in_maximum} wei")
        print(f"   Recipient: {recipient}")
        print(f"   Deadline: {deadline}")
        print(f"   Pool Fee: {self.pool_fee} (0.3%)")
        
        # exactOutputSingle parameters struct
        params = (
            self.w3.to_checksum_address(token_in),      # tokenIn
            self.w3.to_checksum_address(token_out),     # tokenOut
            self.pool_fee,                               # fee
            self.w3.to_checksum_address(recipient),     # recipient
            deadline,                                    # deadline
            amount_out,                                  # amountOut
            amount_in_maximum,                           # amountInMaximum
            0                                            # sqrtPriceLimitX96 (0 = no limit)
        )
        
        # Function selector for exactOutputSingle
        selector = "0x5023b4df"
        
        # Encode parameters
        # The struct is encoded as a tuple
        encoded_params = encode(
            ['(address,address,uint24,address,uint256,uint256,uint256,uint160)'],
            [params]
        )
        
        calldata = selector + encoded_params.hex()
        
        print(f"\n✅ Uniswap V3 Calldata Built:")
        print(f"   Method: exactOutputSingle")
        print(f"   Selector: {selector}")
        print(f"   Calldata Length: {len(calldata)} chars")
        print(f"   Full Calldata: {calldata[:100]}...")
        
        return calldata
    
    def build_arb_to_dai_swap(
        self,
        dai_amount_out: int,
        recipient: str,
        slippage_bps: int = 300  # 3% slippage
    ) -> dict:
        """
        Build ARB→DAI swap calldata for debt swap
        (This is the reverse routing needed for DAI debt → ARB debt)
        """
        
        import time
        
        # Calculate maximum ARB in (with slippage)
        # Estimate: ~2.3 ARB per 1 DAI (ARB price ~$0.55, DAI ~$1.00)
        arb_per_dai = 2.3
        arb_amount_estimate = int((dai_amount_out / 1e18) * arb_per_dai * 1e18)
        arb_max_with_slippage = int(arb_amount_estimate * (1 + slippage_bps / 10000))
        
        deadline = int(time.time()) + 1800  # 30 minutes
        
        calldata = self.build_exact_output_single_calldata(
            token_in=self.arb,
            token_out=self.dai,
            amount_out=dai_amount_out,
            amount_in_maximum=arb_max_with_slippage,
            recipient=recipient,
            deadline=deadline
        )
        
        return {
            'calldata': calldata,
            'uniswap_router': self.uniswap_v3_router,
            'method_selector': '0x5023b4df',
            'method_name': 'exactOutputSingle',
            'token_in': self.arb,
            'token_out': self.dai,
            'amount_out': dai_amount_out,
            'amount_in_max': arb_max_with_slippage,
            'expected_arb_amount': arb_amount_estimate
        }


if __name__ == "__main__":
    # Test the integration
    integrator = DirectUniswapV3Integration()
    
    # Build calldata for $10 DAI out (ARB in)
    dai_amount = int(10 * 1e18)  # 10 DAI
    recipient = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"  # Aave Debt Switch V3
    
    swap_data = integrator.build_arb_to_dai_swap(
        dai_amount_out=dai_amount,
        recipient=recipient
    )
    
    print(f"\n" + "=" * 60)
    print(f"📊 SWAP DATA SUMMARY:")
    print(f"   Uniswap Router: {swap_data['uniswap_router']}")
    print(f"   Method: {swap_data['method_name']} ({swap_data['method_selector']})")
    print(f"   DAI Out: {swap_data['amount_out'] / 1e18} DAI")
    print(f"   ARB In (est): {swap_data['expected_arb_amount'] / 1e18} ARB")
    print(f"   ARB In (max): {swap_data['amount_in_max'] / 1e18} ARB")
    print(f"   Calldata: {swap_data['calldata'][:200]}...")
    print(f"=" * 60)
