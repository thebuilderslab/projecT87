#!/usr/bin/env python3
"""
Direct Augustus V6.2 Integration - Fallback when ParaSwap API returns incompatible methods
Builds swapExactAmountOutOnUniswapV3 calldata directly for Aave Debt Switch compatibility
"""

import time
from web3 import Web3
from eth_abi import encode

class AugustusV6DirectIntegration:
    """Build Augustus V6.2 swapExactAmountOutOnUniswapV3 calldata directly"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
        
        # Augustus V6.2 on Arbitrum
        self.augustus_v6_2 = self.w3.to_checksum_address("0x6a000f20005980200259b80c5102003040001068")
        
        # Token addresses
        self.dai = self.w3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
        self.arb = self.w3.to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548")
        
        # Uniswap V3 pool fee (0.3% = 3000)
        self.pool_fee = 3000
        
        # Method selector for swapExactAmountOutOnUniswapV3
        self.method_selector = "0x5e94e28d"
    
    def encode_uniswap_v3_path(
        self,
        token_in: str,
        token_out: str,
        fee: int = 3000
    ) -> bytes:
        """
        Encode Uniswap V3 path as bytes for single-hop swap
        Format: [token_in (20)] + [fee (3)] + [token_out (20)]
        Total: 43 bytes
        """
        from eth_abi import encode
        
        # Remove 0x prefix
        token_in_clean = token_in[2:] if token_in.startswith('0x') else token_in
        token_out_clean = token_out[2:] if token_out.startswith('0x') else token_out
        
        # Build path: tokenA (20 bytes) + fee (3 bytes) + tokenB (20 bytes)
        path_hex = token_in_clean.lower() + fee.to_bytes(3, 'big').hex() + token_out_clean.lower()
        path_bytes = bytes.fromhex(path_hex)
        
        return path_bytes
    
    def encode_uniswap_v3_metadata(
        self,
        token_in: str,
        token_out: str,
        fee: int = 3000
    ) -> int:
        """
        Encode Uniswap V3 pool metadata as uint256 for Augustus V6.2
        
        Format: [token_in (20)] + [fee (3)] + [token_out (20)] + [padding (9)]
        Total: 52 bytes → truncate to first 32 bytes (uint256)
        
        Note: The full path is 43 bytes, but uint256 only holds 32 bytes.
        Augustus contract knows how to decode this format.
        """
        
        # Build full path
        path_bytes = self.encode_uniswap_v3_path(token_in, token_out, fee)
        
        # For metadata uint256: Take first 32 bytes and convert to integer
        # If path is longer than 32 bytes, it gets truncated
        metadata_bytes = path_bytes[:32] if len(path_bytes) > 32 else path_bytes + b'\x00' * (32 - len(path_bytes))
        metadata_int = int.from_bytes(metadata_bytes, byteorder='big')
        
        return metadata_int
    
    def pack_beneficiary_and_approve_flag(
        self,
        beneficiary: str,
        approve_flag: bool = False
    ) -> int:
        """
        Pack beneficiary address and approve flag into uint256
        Format: [12 bytes padding][20 bytes beneficiary][1 bit approve flag]
        """
        
        # Convert beneficiary to integer (20 bytes)
        beneficiary_int = int(beneficiary, 16)
        
        # Shift left by 1 bit to make room for approve flag
        packed = beneficiary_int << 1
        
        # Add approve flag (0 or 1)
        if approve_flag:
            packed |= 1
        
        return packed
    
    def build_swap_exact_amount_out_calldata(
        self,
        token_in: str,
        token_out: str,
        amount_out: int,
        max_amount_in: int,
        beneficiary: str,
        slippage_bps: int = 300  # 3% slippage
    ) -> dict:
        """
        Build swapExactAmountOutOnUniswapV3 calldata for Augustus V6.2
        
        Args:
            token_in: Input token address (ARB)
            token_out: Output token address (DAI)
            amount_out: Exact amount of output token to receive
            max_amount_in: Maximum amount of input token to spend
            beneficiary: Recipient address (Aave Debt Switch V3)
            slippage_bps: Slippage tolerance in basis points
        """
        
        print(f"\n🏗️  BUILDING DIRECT AUGUSTUS V6.2 CALLDATA")
        print(f"=" * 70)
        print(f"   Method: swapExactAmountOutOnUniswapV3")
        print(f"   Selector: {self.method_selector}")
        print(f"   Token In: {token_in} (ARB)")
        print(f"   Token Out: {token_out} (DAI)")
        print(f"   Exact Amount Out: {amount_out} wei ({amount_out / 1e18} DAI)")
        print(f"   Max Amount In: {max_amount_in} wei ({max_amount_in / 1e18} ARB)")
        print(f"   Beneficiary: {beneficiary}")
        
        # Build UniswapV3Data struct
        deadline = int(time.time()) + 1800  # 30 minutes
        
        # FIXED: Use full Uniswap V3 path as bytes (43 bytes), not truncated uint256
        full_path_bytes = self.encode_uniswap_v3_path(token_in, token_out, self.pool_fee)
        
        # Pack beneficiary and approve flag
        # CRITICAL: approve_flag=True triggers Augustus to handle token approval automatically
        beneficiary_packed = self.pack_beneficiary_and_approve_flag(beneficiary, approve_flag=True)
        
        # UniswapV3Data struct (tuple) - FIXED with bytes path
        uni_data = (
            max_amount_in,          # fromAmount (max ARB in)
            amount_out,             # toAmount (exact DAI out)
            max_amount_in,          # quotedAmount (for validation, use max)
            full_path_bytes,        # poolData (FULL 43-byte Uniswap V3 path as bytes)
            beneficiary_packed      # beneficiaryAndApproveFlag
        )
        
        # partnerAndFee: 0 (no partner fee)
        partner_and_fee = 0
        
        # permit: empty bytes (no permit)
        permit = b''
        
        # Decode poolData (bytes path) for validation logging
        path_hex = full_path_bytes.hex()
        logged_token_in = '0x' + path_hex[:40]
        logged_fee_hex = path_hex[40:46]
        logged_fee = int(logged_fee_hex, 16) if logged_fee_hex else 0
        logged_token_out = '0x' + path_hex[46:86]
        
        print(f"\n📦 STRUCT PARAMETERS (FIXED with full bytes path):")
        print(f"   UniswapV3Data:")
        print(f"     fromAmount: {max_amount_in} ({max_amount_in / 1e18:.6f} tokens)")
        print(f"     toAmount: {amount_out} ({amount_out / 1e18:.6f} tokens)")
        print(f"     quotedAmount: {max_amount_in}")
        print(f"     poolData (FULL 43-byte Uniswap V3 path): 0x{path_hex}")
        print(f"       ├─ Token In: {logged_token_in} {'✅' if logged_token_in.lower() == token_in.lower() else '❌'}")
        print(f"       ├─ Pool Fee: {logged_fee} bps ({logged_fee / 10000}%) {'✅' if logged_fee == self.pool_fee else '❌'}")
        print(f"       └─ Token Out: {logged_token_out} {'✅' if logged_token_out.lower() == token_out.lower() else '❌'}")
        print(f"     beneficiaryAndApproveFlag: {beneficiary_packed}")
        print(f"       ├─ Beneficiary: {beneficiary}")
        print(f"       └─ Approve Flag: True (Augustus will handle token approval)")
        print(f"   partnerAndFee: {partner_and_fee}")
        print(f"   permit: 0x{permit.hex()} (empty)")
        
        # Encode function call
        # FIXED: poolData is bytes (full Uniswap V3 path), not uint256
        encoded_params = encode(
            ['(uint256,uint256,uint256,bytes,uint256)', 'uint256', 'bytes'],
            [uni_data, partner_and_fee, permit]
        )
        
        calldata = self.method_selector + encoded_params.hex()
        
        print(f"\n✅ CALLDATA BUILT:")
        print(f"   Selector: {self.method_selector}")
        print(f"   Length: {len(calldata)} chars")
        print(f"   Full Calldata: {calldata[:200]}...")
        
        return {
            'calldata': calldata,
            'augustus_router': self.augustus_v6_2,
            'method_selector': self.method_selector,
            'method_name': 'swapExactAmountOutOnUniswapV3',
            'token_in': token_in,
            'token_out': token_out,
            'amount_out': amount_out,
            'max_amount_in': max_amount_in,
            'beneficiary': beneficiary,
            'expected_amount': max_amount_in,
            'deadline': deadline
        }
    
    def build_arb_to_dai_swap(
        self,
        dai_amount_out: int,
        beneficiary: str,
        slippage_bps: int = 300  # 3% slippage
    ) -> dict:
        """
        Build ARB→DAI swap calldata (reverse routing for DAI debt → ARB debt)
        """
        
        # Estimate ARB amount needed (ARB ~$0.55, DAI ~$1.00)
        arb_per_dai = 2.3
        arb_estimate = int((dai_amount_out / 1e18) * arb_per_dai * 1e18)
        
        # Add slippage buffer
        max_arb_in = int(arb_estimate * (1 + slippage_bps / 10000))
        
        return self.build_swap_exact_amount_out_calldata(
            token_in=self.arb,
            token_out=self.dai,
            amount_out=dai_amount_out,
            max_amount_in=max_arb_in,
            beneficiary=beneficiary,
            slippage_bps=slippage_bps
        )


if __name__ == "__main__":
    # Test the integration
    integrator = AugustusV6DirectIntegration()
    
    # Build calldata for $10 DAI out (ARB in)
    dai_amount = int(10 * 1e18)  # 10 DAI
    aave_debt_switch = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
    
    swap_data = integrator.build_arb_to_dai_swap(
        dai_amount_out=dai_amount,
        beneficiary=aave_debt_switch
    )
    
    print(f"\n" + "=" * 70)
    print(f"📊 AUGUSTUS V6.2 DIRECT SWAP DATA:")
    print(f"   Router: {swap_data['augustus_router']}")
    print(f"   Method: {swap_data['method_name']}")
    print(f"   Selector: {swap_data['method_selector']}")
    print(f"   DAI Out: {swap_data['amount_out'] / 1e18}")
    print(f"   Max ARB In: {swap_data['max_amount_in'] / 1e18}")
    print(f"   Beneficiary: {swap_data['beneficiary']}")
    print(f"=" * 70)
