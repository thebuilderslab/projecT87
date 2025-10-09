"""
Augustus V6.2 swapExactAmountIn Integration
Uses the proven, heavily-used method on Arbitrum mainnet
"""

from web3 import Web3
from eth_abi import encode
import time

class AugustusV6SwapExactIn:
    """Direct Augustus V6.2 swapExactAmountIn integration (proven method)"""
    
    def __init__(self):
        self.augustus_v6_router = '0x6A000F20005980200259B80c5102003040001068'
        self.method_selector = '0xe3ead59e'  # swapExactAmountIn
        
        # Arbitrum token addresses
        self.tokens = {
            'ARB': '0x912CE59144191C1204E64559FE8253a0e49E6548',
            'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
            'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
        }
        
        # Uniswap V3 pool fee (3000 = 0.3%)
        self.pool_fee = 3000
        
    def encode_uniswap_v3_path(self, token_in: str, token_out: str, fee: int) -> bytes:
        """Encode Uniswap V3 path: token_in(20 bytes) + fee(3 bytes) + token_out(20 bytes)"""
        token_in_bytes = bytes.fromhex(token_in[2:].lower())
        token_out_bytes = bytes.fromhex(token_out[2:].lower())
        fee_bytes = fee.to_bytes(3, byteorder='big')
        
        path = token_in_bytes + fee_bytes + token_out_bytes
        return path
        
    def pack_beneficiary_and_approve_flag(self, beneficiary: str, approve_flag: bool = True) -> int:
        """Pack beneficiary address and approve flag into uint256"""
        beneficiary_int = int(beneficiary, 16)
        beneficiary_shifted = beneficiary_int << 1
        
        if approve_flag:
            packed = beneficiary_shifted | 1
        else:
            packed = beneficiary_shifted
            
        return packed
        
    def build_swap_exact_amount_in_calldata(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        beneficiary: str
    ) -> dict:
        """
        Build swapExactAmountIn calldata for Augustus V6.2
        
        This is the PROVEN method used on Arbitrum mainnet (vs swapExactAmountOut which isn't used)
        
        Args:
            token_in: Input token address (ARB)
            token_out: Output token address (DAI)
            amount_in: Exact amount of input token (ARB amount in wei)
            min_amount_out: Minimum output amount (DAI amount in wei, with slippage)
            beneficiary: Beneficiary address (Debt Switch contract)
        """
        
        print(f"\n🏗️  BUILDING SWAP EXACT AMOUNT IN CALLDATA (PROVEN METHOD)")
        print("=" * 70)
        print(f"   Method: swapExactAmountIn")
        print(f"   Selector: {self.method_selector}")
        print(f"   Token In: {token_in} (ARB)")
        print(f"   Token Out: {token_out} (DAI)")
        print(f"   Exact Amount In: {amount_in} wei ({amount_in / 1e18} ARB)")
        print(f"   Min Amount Out: {min_amount_out} wei ({min_amount_out / 1e18} DAI)")
        print(f"   Beneficiary: {beneficiary}")
        
        # Build UniswapV3Data struct
        full_path_bytes = self.encode_uniswap_v3_path(token_in, token_out, self.pool_fee)
        
        # Pack beneficiary and approve flag
        beneficiary_packed = self.pack_beneficiary_and_approve_flag(beneficiary, approve_flag=True)
        
        # UniswapV3Data struct for swapExactAmountIn:
        # (uint256 fromAmount, uint256 toAmount, uint256 quotedAmount, bytes poolData, uint256 beneficiaryAndApproveFlag)
        uni_data = (
            amount_in,              # fromAmount (exact ARB in)
            min_amount_out,         # toAmount (min DAI out with slippage)
            min_amount_out,         # quotedAmount (for validation)
            full_path_bytes,        # poolData (full 43-byte Uniswap V3 path)
            beneficiary_packed      # beneficiaryAndApproveFlag
        )
        
        # partnerAndFee: 0 (no partner fee)
        partner_and_fee = 0
        
        # permit: empty bytes (no permit)
        permit = b''
        
        # Log struct details
        path_hex = full_path_bytes.hex()
        logged_token_in = '0x' + path_hex[:40]
        logged_fee = int(path_hex[40:46], 16)
        logged_token_out = '0x' + path_hex[46:86]
        
        print(f"\n📦 STRUCT PARAMETERS (swapExactAmountIn):")
        print(f"   UniswapV3Data:")
        print(f"     fromAmount (exact in): {amount_in} ({amount_in / 1e18:.6f} ARB)")
        print(f"     toAmount (min out): {min_amount_out} ({min_amount_out / 1e18:.6f} DAI)")
        print(f"     quotedAmount: {min_amount_out}")
        print(f"     poolData (43-byte path): 0x{path_hex}")
        print(f"       ├─ Token In: {logged_token_in} {'✅' if logged_token_in.lower() == token_in.lower() else '❌'}")
        print(f"       ├─ Pool Fee: {logged_fee} bps ({logged_fee / 10000}%) {'✅' if logged_fee == self.pool_fee else '❌'}")
        print(f"       └─ Token Out: {logged_token_out} {'✅' if logged_token_out.lower() == token_out.lower() else '❌'}")
        print(f"     beneficiaryAndApproveFlag: {beneficiary_packed}")
        print(f"       ├─ Beneficiary: {beneficiary}")
        print(f"       └─ Approve Flag: True")
        print(f"   partnerAndFee: {partner_and_fee}")
        print(f"   permit: 0x{permit.hex()} (empty)")
        
        # Encode function call with correct ABI
        encoded_params = encode(
            ['(uint256,uint256,uint256,bytes,uint256)', 'uint256', 'bytes'],
            [uni_data, partner_and_fee, permit]
        )
        
        calldata = self.method_selector + encoded_params.hex()
        
        print(f"\n✅ CALLDATA BUILT:")
        print(f"   Selector: {self.method_selector}")
        print(f"   Length: {len(calldata)} chars")
        print(f"   Full Calldata: {calldata[:150]}...")
        
        print(f"\n✅ AUGUSTUS V6.2 swapExactAmountIn CALLDATA SUCCESSFUL!")
        print(f"   Router: {self.augustus_v6_router}")
        print(f"   Method: swapExactAmountIn (PROVEN on Arbitrum)")
        print(f"   ARB In: {amount_in / 1e18}")
        print(f"   Min DAI Out: {min_amount_out / 1e18}")
        
        return {
            'augustus_router': self.augustus_v6_router,
            'calldata': calldata,
            'method_name': 'swapExactAmountIn',
            'method_selector': self.method_selector,
            'amount_in': amount_in,
            'min_amount_out': min_amount_out
        }


if __name__ == '__main__':
    # Test the integration
    swapper = AugustusV6SwapExactIn()
    
    # Example: Swap 60 ARB for minimum 24 DAI (4% slippage on $25)
    result = swapper.build_swap_exact_amount_in_calldata(
        token_in=swapper.tokens['ARB'],
        token_out=swapper.tokens['DAI'],
        amount_in=int(60 * 1e18),  # 60 ARB
        min_amount_out=int(24 * 1e18),  # Min 24 DAI (4% slippage)
        beneficiary='0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4'  # Debt Switch
    )
    
    print(f"\n✅ Test Complete!")
    print(f"   Calldata: {result['calldata'][:100]}...")
