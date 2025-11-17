#!/usr/bin/env python3
"""
Bidirectional Debt Swap Utility
Supports both DAI<>WETH debt swaps using corrected swapDebt() function

Features:
- DAI → WETH: Repay DAI debt, borrow WETH
- WETH → DAI: Repay WETH debt, borrow DAI  
- Automatic direction detection
- ParaSwap integration with BUY mode for exact outputs
- Health factor monitoring
"""

import os
from web3 import Web3
from decimal import Decimal
from typing import Literal, Optional, Dict, Any
from corrected_swap_debt_abi import (
    DEBT_SWITCH_SWAP_DEBT_ABI,
    DEBT_SWITCH_V3_ADDRESS,
    ARBITRUM_ADDRESSES,
    get_empty_permit,
    get_empty_credit_delegation_permit
)
from augustus_v5_multiswap_builder import AugustusV5MultiSwapBuilder

DebtAsset = Literal['DAI', 'WETH']

class BidirectionalDebtSwapper:
    """Execute debt swaps in both directions: DAI<>WETH"""
    
    def __init__(self, w3: Web3, private_key: str):
        self.w3 = w3
        self.private_key = private_key
        self.account = w3.eth.account.from_key(private_key)
        self.address = self.account.address
        
        # Initialize contracts
        self.debt_switch = w3.eth.contract(
            address=Web3.to_checksum_address(DEBT_SWITCH_V3_ADDRESS),
            abi=DEBT_SWITCH_SWAP_DEBT_ABI
        )
        
        self.aave_pool = w3.eth.contract(
            address=Web3.to_checksum_address("0x794a61358D6845594F94dc1DB02A252b5b4814aD"),
            abi=[{
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
            }]
        )
        
        # ERC20 ABI for balance checks
        self.erc20_abi = [
            {"constant": True, "inputs": [{"name": "owner", "type": "address"}], 
             "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
        ]
        
        # ParaSwap builder
        self.paraswap = AugustusV5MultiSwapBuilder(w3, "arbitrum")
        
        print(f"🔄 BidirectionalDebtSwapper initialized")
        print(f"   Wallet: {self.address}")
        print(f"   Supports: DAI ↔ WETH debt swaps")
    
    def get_debt_balance(self, asset: DebtAsset) -> Decimal:
        """Get current variable debt balance for asset"""
        debt_token_addr = ARBITRUM_ADDRESSES[f"variableDebtArb{asset}"]
        debt_token = self.w3.eth.contract(
            address=Web3.to_checksum_address(debt_token_addr),
            abi=self.erc20_abi
        )
        balance_wei = debt_token.functions.balanceOf(self.address).call()
        return Decimal(balance_wei) / Decimal(1e18)
    
    def get_health_factor(self) -> Decimal:
        """Get current Aave health factor"""
        data = self.aave_pool.functions.getUserAccountData(self.address).call()
        return Decimal(data[5]) / Decimal(1e18)
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get comprehensive account summary"""
        dai_debt = self.get_debt_balance('DAI')
        weth_debt = self.get_debt_balance('WETH')
        hf = self.get_health_factor()
        
        return {
            'dai_debt': dai_debt,
            'weth_debt': weth_debt,
            'health_factor': hf,
            'total_debt_usd': float(dai_debt) + float(weth_debt) * 3000  # Rough estimate
        }
    
    def swap_debt(
        self,
        from_asset: DebtAsset,
        to_asset: DebtAsset,
        amount: Decimal,
        slippage_bps: int = 100,
        dry_run: bool = False
    ) -> Optional[str]:
        """
        Swap debt from one asset to another
        
        Args:
            from_asset: Asset to repay ('DAI' or 'WETH')
            to_asset: Asset to borrow ('DAI' or 'WETH')
            amount: Amount to repay (in asset units, not wei)
            slippage_bps: Slippage tolerance (default 1%)
            dry_run: If True, simulate without sending transaction
        
        Returns:
            Transaction hash if successful, None otherwise
        
        Examples:
            # Repay 25 DAI, borrow equivalent WETH
            swap_debt('DAI', 'WETH', Decimal('25'), slippage_bps=100)
            
            # Repay 0.01 WETH, borrow equivalent DAI
            swap_debt('WETH', 'DAI', Decimal('0.01'), slippage_bps=100)
        """
        print("\n" + "=" * 80)
        print(f"DEBT SWAP: {from_asset} → {to_asset}")
        print("=" * 80)
        
        # Validate inputs
        if from_asset == to_asset:
            print(f"❌ Cannot swap {from_asset} to itself")
            return None
        
        if from_asset not in ['DAI', 'WETH'] or to_asset not in ['DAI', 'WETH']:
            print(f"❌ Only DAI and WETH are supported")
            return None
        
        try:
            # Get addresses
            from_addr = ARBITRUM_ADDRESSES[from_asset]
            to_addr = ARBITRUM_ADDRESSES[to_asset]
            from_debt_token = ARBITRUM_ADDRESSES[f"variableDebtArb{from_asset}"]
            to_debt_token = ARBITRUM_ADDRESSES[f"variableDebtArb{to_asset}"]
            
            # Check current state
            summary = self.get_account_summary()
            print(f"\n📊 Current Position:")
            print(f"   DAI debt: {summary['dai_debt']:.6f}")
            print(f"   WETH debt: {summary['weth_debt']:.6f}")
            print(f"   Health Factor: {summary['health_factor']:.4f}")
            
            # Check if we have enough debt to repay
            current_debt = self.get_debt_balance(from_asset)
            if current_debt < amount:
                print(f"\n⚠️  Warning: Requested {amount} {from_asset} but only have {current_debt} debt")
                print(f"   Adjusting to maximum available: {current_debt}")
                amount = current_debt
            
            # Convert to wei
            repay_amount_wei = int(amount * Decimal(1e18))
            
            print(f"\n💱 Swap Details:")
            print(f"   Repaying: {amount:.6f} {from_asset}")
            print(f"   Borrowing: {to_asset} (amount TBD from ParaSwap)")
            
            # Build ParaSwap calldata
            # We sell to_asset (newly borrowed) to buy from_asset (to repay)
            # Use BUY mode for exact output (exact repayment amount)
            print(f"\n🔄 Fetching swap route from ParaSwap...")
            paraswap_data = self.paraswap.build_multiswap_calldata(
                from_token=to_asset,
                to_token=from_asset,
                from_amount=repay_amount_wei,  # Exact amount we need to receive
                min_to_amount=repay_amount_wei,
                beneficiary=DEBT_SWITCH_V3_ADDRESS,
                slippage_bps=slippage_bps,
                use_buy_mode=True  # BUY mode for exact output
            )
            
            if not paraswap_data:
                raise Exception("Failed to build ParaSwap swap route")
            
            # Max new debt amount from ParaSwap
            max_new_debt_base = int(paraswap_data['from_amount'])
            # CRITICAL: Add 3% buffer for interest accrual, slippage, and health factor fluctuations
            # Aave debt swaps require this buffer to prevent transaction reverts
            max_new_debt = int(max_new_debt_base * 1.03)
            max_new_debt_decimal = Decimal(max_new_debt) / Decimal(1e18)
            
            print(f"   ✅ Route found")
            print(f"   Will borrow: {max_new_debt_decimal:.6f} {to_asset} (includes 3% safety buffer)")
            print(f"   To repay: {amount:.6f} {from_asset}")
            
            # Build swapDebt parameters
            debt_swap_params = {
                "debtAsset": Web3.to_checksum_address(from_addr),
                "debtRepayAmount": repay_amount_wei,
                "debtRateMode": 2,  # Variable rate
                "newDebtAsset": Web3.to_checksum_address(to_addr),
                "maxNewDebtAmount": max_new_debt,
                "extraCollateralAsset": "0x0000000000000000000000000000000000000000",
                "extraCollateralAmount": 0,
                "offset": 0,
                "paraswapData": paraswap_data['calldata']
            }
            
            credit_delegation_permit = get_empty_credit_delegation_permit()
            collateral_permit = get_empty_permit()
            
            if dry_run:
                print(f"\n🔍 DRY RUN - Transaction not sent")
                print(f"   Would repay: {amount:.6f} {from_asset}")
                print(f"   Would borrow: {max_new_debt_decimal:.6f} {to_asset}")
                return "DRY_RUN"
            
            # Build transaction
            print(f"\n📝 Building transaction...")
            base_fee = self.w3.eth.gas_price
            max_fee = int(base_fee * 2)  # 2x base fee to ensure it goes through
            
            tx = self.debt_switch.functions.swapDebt(
                debt_swap_params,
                credit_delegation_permit,
                collateral_permit
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 400000,  # Based on actual usage: ~200K, 2x buffer for safety
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': self.w3.to_wei('0.01', 'gwei'),
                'chainId': 42161
            })
            
            print(f"   Gas limit: {tx['gas']:,}")
            print(f"   Max fee: {self.w3.from_wei(tx['maxFeePerGas'], 'gwei'):.4f} Gwei")
            
            # Sign and send
            print(f"\n🔐 Signing transaction...")
            signed_tx = self.account.sign_transaction(tx)
            
            print(f"📡 Broadcasting...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"\n✅ Transaction sent!")
            print(f"   TX: {tx_hash_hex}")
            print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
            
            # Wait for confirmation
            print(f"\n⏳ Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                # Get new state
                new_summary = self.get_account_summary()
                
                print(f"\n🎉 SUCCESS!")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas used: {receipt['gasUsed']:,}")
                print(f"\n📊 New Position:")
                print(f"   DAI debt: {summary['dai_debt']:.6f} → {new_summary['dai_debt']:.6f}")
                print(f"   WETH debt: {summary['weth_debt']:.6f} → {new_summary['weth_debt']:.6f}")
                print(f"   Health Factor: {summary['health_factor']:.4f} → {new_summary['health_factor']:.4f}")
                
                return tx_hash_hex
            else:
                print(f"\n❌ Transaction FAILED")
                return None
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Example usage"""
    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        print("❌ PRIVATE_KEY not set")
        return
    
    # Connect to Arbitrum
    rpc = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    if not w3.is_connected():
        print("❌ Failed to connect")
        return
    
    print("✅ Connected to Arbitrum mainnet")
    
    # Initialize swapper
    swapper = BidirectionalDebtSwapper(w3, private_key)
    
    # Get current position
    summary = swapper.get_account_summary()
    print("\n" + "=" * 80)
    print("CURRENT POSITION")
    print("=" * 80)
    print(f"DAI Debt: {summary['dai_debt']:.6f}")
    print(f"WETH Debt: {summary['weth_debt']:.6f}")
    print(f"Health Factor: {summary['health_factor']:.4f}")
    print(f"Total Debt (USD): ${summary['total_debt_usd']:.2f}")
    
    # Example swaps (commented out - uncomment to execute)
    
    # Example 1: DAI → WETH (repay $25 DAI, borrow WETH)
    # swapper.swap_debt('DAI', 'WETH', Decimal('25'), slippage_bps=100)
    
    # Example 2: WETH → DAI (repay 0.01 WETH, borrow DAI)
    # swapper.swap_debt('WETH', 'DAI', Decimal('0.01'), slippage_bps=100)

if __name__ == "__main__":
    main()
