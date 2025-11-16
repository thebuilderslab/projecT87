#!/usr/bin/env python3
"""
CORRECTED Debt Swap Executor using swapDebt() function (0xb8bd1c6b)
Fixed from debtSwitch() to match successful on-chain transactions

Key Changes:
1. Function name: debtSwitch() → swapDebt()
2. Selector: 0x0c6bc33e → 0xb8bd1c6b  
3. Structure: Flat tuples instead of nested arrays
4. debtSwapParams has 9 fields (paraswapData as bytes, NO permitParams array)
"""

import os
import sys
import time
from web3 import Web3
from decimal import Decimal
from typing import Dict, Any, Optional
from corrected_swap_debt_abi import (
    DEBT_SWITCH_SWAP_DEBT_ABI, 
    DEBT_SWITCH_V3_ADDRESS, 
    ARBITRUM_ADDRESSES,
    get_empty_permit,
    get_empty_credit_delegation_permit
)
from augustus_v5_multiswap_builder import AugustusV5MultiSwapBuilder

# Configuration
ARBITRUM_RPC = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")

# ERC20 ABI (minimal)
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

# Aave Pool ABI (minimal)
AAVE_POOL_ABI = [{
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

class CorrectedDebtSwapExecutor:
    """Execute debt swaps using the CORRECT swapDebt() function"""
    
    def __init__(self, w3: Web3, private_key: str):
        self.w3 = w3
        self.private_key = private_key
        self.account = w3.eth.account.from_key(private_key)
        self.address = self.account.address
        
        # Contracts
        self.debt_switch = w3.eth.contract(
            address=Web3.to_checksum_address(DEBT_SWITCH_V3_ADDRESS),
            abi=DEBT_SWITCH_SWAP_DEBT_ABI
        )
        
        self.aave_pool = w3.eth.contract(
            address=Web3.to_checksum_address("0x794a61358D6845594F94dc1DB02A252b5b4814aD"),
            abi=AAVE_POOL_ABI
        )
        
        # ParaSwap builder
        self.paraswap_builder = AugustusV5MultiSwapBuilder(w3, "arbitrum")
        
        print(f"✅ CorrectedDebtSwapExecutor initialized")
        print(f"   Wallet: {self.address}")
        print(f"   Debt Switch V3: {DEBT_SWITCH_V3_ADDRESS}")
        print(f"   Using swapDebt() function (selector: 0xb8bd1c6b)")
    
    def get_debt_balance(self, debt_token_address: str) -> int:
        """Get current debt balance"""
        debt_token = self.w3.eth.contract(
            address=Web3.to_checksum_address(debt_token_address),
            abi=ERC20_ABI
        )
        return debt_token.functions.balanceOf(self.address).call()
    
    def get_health_factor(self) -> Decimal:
        """Get current health factor"""
        data = self.aave_pool.functions.getUserAccountData(self.address).call()
        health_factor = Decimal(data[5]) / Decimal(1e18)
        return health_factor
    
    def execute_debt_swap(
        self,
        from_debt: str,  # 'DAI' or 'WETH'
        to_debt: str,    # 'DAI' or 'WETH'
        repay_amount_usd: float,
        slippage_bps: int = 100  # 1% slippage
    ) -> Optional[str]:
        """
        Execute debt swap: repay from_debt and borrow to_debt
        
        Examples:
        - DAI→WETH: Repay DAI debt, borrow WETH
        - WETH→DAI: Repay WETH debt, borrow DAI
        """
        print("\n" + "=" * 80)
        print(f"EXECUTING CORRECTED DEBT SWAP: {from_debt} → {to_debt}")
        print("=" * 80)
        
        try:
            # Get token addresses
            from_debt_addr = ARBITRUM_ADDRESSES[from_debt]
            to_debt_addr = ARBITRUM_ADDRESSES[to_debt]
            from_debt_variable = ARBITRUM_ADDRESSES[f"variableDebtArb{from_debt}"]
            to_debt_variable = ARBITRUM_ADDRESSES[f"variableDebtArb{to_debt}"]
            
            # Check current debt
            current_debt = self.get_debt_balance(from_debt_variable)
            print(f"Current {from_debt} debt: {current_debt / 1e18:.6f} {from_debt}")
            
            # Calculate amounts
            # For debt swaps: we need exact output (repay exact amount of old debt)
            repay_amount_wei = int(repay_amount_usd * 1e18) if from_debt == 'DAI' else int(repay_amount_usd / 3000 * 1e18)  # Rough WETH conversion
            
            print(f"\n📊 Swap Parameters:")
            print(f"   Repaying: {repay_amount_wei / 1e18:.6f} {from_debt}")
            print(f"   Direction: {from_debt} debt → {to_debt} debt")
            
            # Build ParaSwap calldata for the swap
            # In debt swap: we sell to_debt to get from_debt (to repay the old debt)
            # Use BUY mode to ensure exact repayment amount
            paraswap_data = self.paraswap_builder.build_multiswap_calldata(
                from_token=to_debt,  # We're selling the newly borrowed token
                to_token=from_debt,  # To repay the old debt
                from_amount=repay_amount_wei,  # Amount we need to repay (in BUY mode, this is destAmount)
                min_to_amount=repay_amount_wei,  # Must receive exact amount
                beneficiary=DEBT_SWITCH_V3_ADDRESS,  # Debt Switch receives the tokens
                slippage_bps=slippage_bps,
                use_buy_mode=True  # CRITICAL: BUY mode for exact output
            )
            
            if not paraswap_data:
                raise Exception("Failed to build ParaSwap calldata")
            
            # Extract max new debt amount from ParaSwap response
            max_new_debt_amount = int(paraswap_data['from_amount'])  # How much to_debt we need to borrow
            
            print(f"\n💱 Swap Details:")
            print(f"   Will borrow: {max_new_debt_amount / 1e18:.6f} {to_debt}")
            print(f"   To repay: {repay_amount_wei / 1e18:.6f} {from_debt}")
            
            # Build debtSwapParams
            debt_swap_params = {
                "debtAsset": Web3.to_checksum_address(from_debt_addr),
                "debtRepayAmount": repay_amount_wei,
                "debtRateMode": 2,  # Variable rate
                "newDebtAsset": Web3.to_checksum_address(to_debt_addr),
                "maxNewDebtAmount": max_new_debt_amount,
                "extraCollateralAsset": "0x0000000000000000000000000000000000000000",
                "extraCollateralAmount": 0,
                "offset": 0,
                "paraswapData": paraswap_data['calldata']
            }
            
            # Empty credit delegation permit (we pre-approved via EIP-712)
            credit_delegation_permit = get_empty_credit_delegation_permit()
            
            # Empty collateral permit (not needed)
            collateral_permit = get_empty_permit()
            
            print(f"\n🔧 Transaction Parameters:")
            print(f"   Function: swapDebt()")
            print(f"   Selector: 0xb8bd1c6b")
            print(f"   Debt asset: {from_debt_addr}")
            print(f"   New debt asset: {to_debt_addr}")
            print(f"   Repay amount: {repay_amount_wei}")
            print(f"   Max new debt: {max_new_debt_amount}")
            
            # Build transaction
            print(f"\n📝 Building transaction...")
            
            # Get current health factor
            hf_before = self.get_health_factor()
            print(f"   Health factor before: {hf_before:.4f}")
            
            # Build the swapDebt call
            tx = self.debt_switch.functions.swapDebt(
                debt_swap_params,
                credit_delegation_permit,
                collateral_permit
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 2000000,
                'maxFeePerGas': self.w3.eth.gas_price,
                'maxPriorityFeePerGas': self.w3.to_wei('0.01', 'gwei'),
                'chainId': 42161
            })
            
            print(f"   Gas limit: {tx['gas']}")
            print(f"   Gas price: {self.w3.from_wei(tx['maxFeePerGas'], 'gwei'):.4f} Gwei")
            
            # Sign and send
            print(f"\n🔐 Signing transaction...")
            signed_tx = self.account.sign_transaction(tx)
            
            print(f"📡 Broadcasting transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"\n✅ Transaction broadcast!")
            print(f"   TX Hash: {tx_hash_hex}")
            print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
            
            # Wait for confirmation
            print(f"\n⏳ Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                print(f"\n🎉 SUCCESS! Debt swap completed")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas used: {receipt['gasUsed']:,}")
                
                # Check new debt balances
                new_from_debt = self.get_debt_balance(from_debt_variable)
                new_to_debt = self.get_debt_balance(to_debt_variable)
                hf_after = self.get_health_factor()
                
                print(f"\n📊 Results:")
                print(f"   {from_debt} debt: {current_debt / 1e18:.6f} → {new_from_debt / 1e18:.6f}")
                print(f"   {to_debt} debt: {new_to_debt / 1e18:.6f} (new)")
                print(f"   Health factor: {hf_before:.4f} → {hf_after:.4f}")
                
                return tx_hash_hex
            else:
                print(f"\n❌ Transaction FAILED")
                print(f"   Status: {receipt['status']}")
                return None
                
        except Exception as e:
            print(f"\n❌ Error executing debt swap: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Main execution"""
    if not PRIVATE_KEY:
        print("❌ PRIVATE_KEY not set")
        return
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum")
        return
    
    print("✅ Connected to Arbitrum mainnet")
    
    # Create executor
    executor = CorrectedDebtSwapExecutor(w3, PRIVATE_KEY)
    
    # Example: Swap $25 of DAI debt to WETH debt
    print("\n" + "=" * 80)
    print("EXAMPLE: DAI → WETH Debt Swap ($25)")
    print("=" * 80)
    
    tx_hash = executor.execute_debt_swap(
        from_debt="DAI",
        to_debt="WETH",
        repay_amount_usd=25.0,
        slippage_bps=100  # 1%
    )
    
    if tx_hash:
        print(f"\n✅ Debt swap successful: {tx_hash}")
    else:
        print(f"\n❌ Debt swap failed")

if __name__ == "__main__":
    main()
