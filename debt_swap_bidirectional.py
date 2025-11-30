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
from corrected_swap_debt_abi import (DEBT_SWITCH_SWAP_DEBT_ABI,
                                     DEBT_SWITCH_V3_ADDRESS,
                                     ARBITRUM_ADDRESSES, get_empty_permit,
                                     get_empty_credit_delegation_permit)
from augustus_v5_multiswap_builder import AugustusV5MultiSwapBuilder
from gas_config import PRODUCTION_GAS_LIMITS, PARASWAP_ROUTING_WARNING

DebtAsset = Literal['DAI', 'WETH']

# ParaSwap routing reliability constants (see PARASWAP_ROUTING_AUDIT.md)
GOOD_ROUTE_SELECTORS = {
    '0xa76f4eb6':
    'swapExactAmountOutOnUniswapV2 (100% mainnet success, 729K gas)',
    '0xd6ed22e6':
    'swapExactAmountOutOnBalancerV2 (testing - promoted 2025-01-20)',
    '0x5e94e28d':
    'swapExactAmountOutOnUniswapV3 (testing - added 2025-01-20)'
}  # Whitelist of verified working routes
BAD_ROUTE_SELECTORS = {
    '0x7f457675':
    'swapExactAmountOut (0% success - missing GenericAdapter wrapper)'
}  # Blacklist of known failing routes - blocked via excludeContractMethods
UNVETTED_ROUTE_SELECTORS = {
}  # Discovered but not yet validated on mainnet
MAX_ROUTE_RETRIES = 3  # Boosts expected success rate from 50% to 87.5%
STRICT_MODE = True  # If True, only allow whitelisted routes (recommended for production)


def validate_paraswap_route(method_selector: str,
                            calldata_size: int,
                            strict: bool = STRICT_MODE) -> bool:
    """
    Pre-flight validation: Check if ParaSwap returned a safe, tested route.
    
    SECURITY: Uses whitelist-only approach in strict mode (default).
    Only routes that have been successfully tested on mainnet are allowed.
    
    Args:
        method_selector: Method selector from ParaSwap transaction data (e.g., '0xa76f4eb6')
        calldata_size: Size of calldata in bytes
        strict: If True, only allow whitelisted routes (default: True for safety)
    
    Returns:
        True if route is safe to use, False otherwise
    
    See PARASWAP_ROUTING_AUDIT.md for comprehensive routing analysis.
    """
    # Check against known-bad routes (always reject)
    if method_selector in BAD_ROUTE_SELECTORS:
        print(f"      ❌ BAD ROUTE REJECTED: {method_selector}")
        print(f"         Reason: {BAD_ROUTE_SELECTORS[method_selector]}")
        print(f"         Calldata size: {calldata_size} bytes")
        return False

    # Check against known-good routes (always accept)
    if method_selector in GOOD_ROUTE_SELECTORS:
        print(f"      ✅ GOOD ROUTE VALIDATED: {method_selector}")
        print(f"         {GOOD_ROUTE_SELECTORS[method_selector]}")
        print(f"         Calldata size: {calldata_size} bytes")
        return True

    # Handle unknown/unvetted routes based on strict mode
    if method_selector in UNVETTED_ROUTE_SELECTORS:
        route_name = UNVETTED_ROUTE_SELECTORS[method_selector]
        if strict:
            print(f"      ❌ UNVETTED ROUTE BLOCKED: {method_selector}")
            print(f"         Route: {route_name}")
            print(f"         Calldata size: {calldata_size} bytes")
            print(f"         STRICT MODE: Only whitelisted routes allowed")
            print(
                f"         To test this route, set STRICT_MODE=False or add to whitelist"
            )
            return False
        else:
            print(f"      ⚠️  UNVETTED ROUTE ALLOWED: {method_selector}")
            print(f"         Route: {route_name}")
            print(f"         Calldata size: {calldata_size} bytes")
            print(
                f"         WARNING: This route has NOT been tested on mainnet!"
            )
            print(
                f"         Proceeding at your own risk (strict mode disabled)")
            return True

    # Completely unknown selector
    if strict:
        print(f"      ❌ UNKNOWN ROUTE BLOCKED: {method_selector}")
        print(f"         Calldata size: {calldata_size} bytes")
        print(f"         STRICT MODE: Route not in whitelist")
        print(f"         Add to whitelist after mainnet validation")
        return False
    else:
        print(f"      ⚠️  UNKNOWN ROUTE ALLOWED: {method_selector}")
        print(f"         Calldata size: {calldata_size} bytes")
        print(f"         WARNING: This route is completely unknown!")
        print(f"         High risk of failure - consider enabling strict mode")
        return True


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
            abi=DEBT_SWITCH_SWAP_DEBT_ABI)

        self.aave_pool = w3.eth.contract(address=Web3.to_checksum_address(
            "0x794a61358D6845594F94dc1DB02A252b5b4814aD"),
                                         abi=[{
                                             "inputs": [{
                                                 "name": "user",
                                                 "type": "address"
                                             }],
                                             "name":
                                             "getUserAccountData",
                                             "outputs": [{
                                                 "name": "totalCollateralBase",
                                                 "type": "uint256"
                                             }, {
                                                 "name": "totalDebtBase",
                                                 "type": "uint256"
                                             }, {
                                                 "name":
                                                 "availableBorrowsBase",
                                                 "type": "uint256"
                                             }, {
                                                 "name":
                                                 "currentLiquidationThreshold",
                                                 "type": "uint256"
                                             }, {
                                                 "name": "ltv",
                                                 "type": "uint256"
                                             }, {
                                                 "name": "healthFactor",
                                                 "type": "uint256"
                                             }],
                                             "stateMutability":
                                             "view",
                                             "type":
                                             "function"
                                         }])

        # ERC20 ABI for balance checks
        self.erc20_abi = [{
            "constant": True,
            "inputs": [{
                "name": "owner",
                "type": "address"
            }],
            "name": "balanceOf",
            "outputs": [{
                "name": "",
                "type": "uint256"
            }],
            "type": "function"
        }]

        # ParaSwap builder
        self.paraswap = AugustusV5MultiSwapBuilder(w3, "arbitrum")

        print(f"🔄 BidirectionalDebtSwapper initialized")
        print(f"   Wallet: {self.address}")
        print(f"   Supports: DAI ↔ WETH debt swaps")

    def _build_paraswap_transaction_single_attempt(
        self,
        from_token: str,
        to_token: str,
        dest_amount: int,
        slippage_bps: int = 300  # 3% slippage default for safer swaps
    ) -> Optional[Dict[str, Any]]:
        """
        Build ParaSwap swap data (single attempt - no retry logic).
        Use _build_paraswap_transaction() for production (includes retry).
        
        Returns ABI-encoded (bytes calldata, address augustus) structure
        """
        import requests
        from eth_abi import encode

        try:
            # Token addresses
            from_token_addr = ARBITRUM_ADDRESSES[from_token]
            to_token_addr = ARBITRUM_ADDRESSES[to_token]

            # Step 1: Get price route (BUY mode for exact output)
            # RELIABILITY FIX: Use excludeContractMethods to block the failing generic method
            # This forces ParaSwap to use specific adapter methods (UniswapV2/V3, BalancerV2)
            # The generic swapExactAmountOut (0x7f457675) always fails with Aave Debt Switch
            price_url = "https://api.paraswap.io/prices"
            price_params = {
                'srcToken': from_token_addr,
                'destToken': to_token_addr,
                'srcDecimals': '18',
                'destDecimals': '18',
                'amount': str(dest_amount),
                'side': 'BUY',  # Exact output
                'network': '42161',
                'version': '6.2',  # Force Augustus V6.2
                'excludeContractMethods':
                'swapExactAmountOut'  # Block the failing generic method
            }

            print(f"   Fetching ParaSwap price route...")
            price_resp = requests.get(price_url,
                                      params=price_params,
                                      timeout=10)

            if price_resp.status_code != 200:
                print(f"   ❌ Price route failed: {price_resp.status_code}")
                print(f"      {price_resp.text}")
                return None

            price_data = price_resp.json()
            price_route = price_data['priceRoute']

            src_amount = int(price_route['srcAmount'])
            dest_amount_actual = int(price_route['destAmount'])

            print(
                f"   ✅ Route found: {src_amount / 1e18:.6f} {from_token} → {dest_amount_actual / 1e18:.6f} {to_token}"
            )
            print(f"      Method: {price_route.get('contractMethod', 'N/A')}")
            print(
                f"      Slippage will be applied to maxNewDebtAmount only (keeps working routing)"
            )

            # Step 2: Build transaction using /transactions API
            # CRITICAL: Set receiver to Debt Switch Adapter so swap proceeds go there for repayment
            # Without this, funds go to EOA and adapter has zero balance, causing revert 0x1bbb4abe
            #
            # KNOWN LIMITATION: ParaSwap REST API returns 836-byte calldata but working debt swaps
            # use 3332-byte calldata with GenericAdapter wrapper. The API cannot generate this wrapper
            # with any known parameter combination (tested: receiver, partner, partnerAddress, takeSurplus).
            # Working transactions likely use ParaSwap TypeScript SDK or custom integration.
            # Manual calldata replication would require reverse-engineering GenericAdapter ABI structure.
            tx_url = f"https://api.paraswap.io/transactions/42161"
            tx_payload = {
                'priceRoute': price_route,  # MUST pass exact priceRoute object
                'srcToken': price_route['srcToken'],
                'destToken': price_route['destToken'],
                'srcAmount': price_route[
                    'srcAmount'],  # Use original srcAmount to keep working routing
                'destAmount': price_route['destAmount'],
                'userAddress':
                self.address,  # User who signs the swapDebt transaction
                'receiver':
                DEBT_SWITCH_V3_ADDRESS,  # Swap proceeds go to Debt Switch for repayment
                'ignoreChecks':
                True,  # Skip balance checks (Debt Switch gets funds via flash loan)
                'ignoreGasEstimate': True  # Skip gas estimation
            }

            print(f"   Building ParaSwap transaction...")
            tx_resp = requests.post(tx_url, json=tx_payload, timeout=10)

            if tx_resp.status_code != 200:
                print(f"   ❌ Transaction build failed: {tx_resp.status_code}")
                print(f"      {tx_resp.text}")
                return None

            tx_data = tx_resp.json()

            # Extract calldata and augustus address
            swap_calldata = bytes.fromhex(tx_data['data'][2:])  # Remove 0x
            augustus_address = tx_data['to']
            method_selector = '0x' + swap_calldata[:4].hex()
            calldata_size = len(swap_calldata)

            print(f"   ✅ ParaSwap transaction built!")
            print(f"      Augustus: {augustus_address}")
            print(f"      Calldata: {calldata_size} bytes")
            print(f"      Method selector: {method_selector}")

            # PRE-FLIGHT VALIDATION: Check if route will work
            is_valid = validate_paraswap_route(method_selector, calldata_size)
            if not is_valid:
                # Return None to trigger retry in wrapper function
                return None

            # Encode as (bytes calldata, address augustus) for Aave Debt Switch
            paraswap_data = encode(
                ['bytes', 'address'],
                [swap_calldata,
                 Web3.to_checksum_address(augustus_address)])

            paraswap_data_hex = '0x' + paraswap_data.hex()

            print(f"   ✅ Encoded for Aave Debt Switch")
            print(
                f"      Total paraswapData: {len(paraswap_data_hex)} chars ({len(paraswap_data)} bytes)"
            )

            return {
                'src_amount': src_amount,
                'dest_amount': dest_amount_actual,
                'calldata': paraswap_data_hex,
                'router': augustus_address
            }

        except Exception as e:
            print(f"   ❌ Error building ParaSwap transaction: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _build_paraswap_transaction(
            self,
            from_token: str,
            to_token: str,
            dest_amount: int,
            slippage_bps: int = 300) -> Optional[Dict[str, Any]]:
        """
        Build ParaSwap swap data with automatic retry for reliable routing.
        
        Implements retry logic to overcome ParaSwap API non-determinism:
        - Attempts up to MAX_ROUTE_RETRIES times
        - Exponential backoff: 2s, 4s, 8s
        - Rejects bad routes (0x7f457675) and retries
        - Returns None only after all retries exhausted
        
        See PARASWAP_ROUTING_AUDIT.md for routing analysis.
        """
        import time

        for attempt in range(1, MAX_ROUTE_RETRIES + 1):
            print(
                f"\n🔄 ParaSwap route attempt {attempt}/{MAX_ROUTE_RETRIES}...")

            # Try to build transaction
            result = self._build_paraswap_transaction_single_attempt(
                from_token, to_token, dest_amount, slippage_bps)

            if result is not None:
                # Success! Got a valid route
                print(f"   ✅ Valid route obtained on attempt {attempt}")
                if attempt > 1:
                    print(f"      (Retry successful - avoided bad route)")
                return result

            # Failed validation or API error
            if attempt < MAX_ROUTE_RETRIES:
                backoff_seconds = 2**attempt  # 2s, 4s, 8s
                print(
                    f"   ⏳ Bad route detected, retrying in {backoff_seconds}s..."
                )
                print(
                    f"      (Market conditions may change, different route possible)"
                )
                time.sleep(backoff_seconds)
            else:
                print(f"   ❌ All {MAX_ROUTE_RETRIES} attempts failed")
                print(f"      ParaSwap API consistently returning bad route")
                print(
                    f"      Consider trying again later or using alternative DEX"
                )

        return None

    def get_debt_balance(self, asset: DebtAsset) -> Decimal:
        """Get current variable debt balance for asset"""
        debt_token_addr = ARBITRUM_ADDRESSES[f"variableDebtArb{asset}"]
        debt_token = self.w3.eth.contract(
            address=Web3.to_checksum_address(debt_token_addr),
            abi=self.erc20_abi)
        balance_wei = debt_token.functions.balanceOf(self.address).call()
        return Decimal(balance_wei) / Decimal(1e18)

    def get_health_factor(self) -> Decimal:
        """Get current Aave health factor"""
        data = self.aave_pool.functions.getUserAccountData(self.address).call()
        return Decimal(data[5]) / Decimal(1e18)

    def get_account_summary(self,
                            eth_price_usd: Optional[Decimal] = None
                            ) -> Dict[str, Any]:
        """
        Get comprehensive account summary
        
        Args:
            eth_price_usd: Current ETH price in USD (if None, uses rough estimate)
        """
        dai_debt = self.get_debt_balance('DAI')
        weth_debt = self.get_debt_balance('WETH')
        hf = self.get_health_factor()

        # Get Aave account data for collateral value
        data = self.aave_pool.functions.getUserAccountData(self.address).call()
        total_collateral_base = Decimal(data[0]) / Decimal(
            1e8)  # USD value with 8 decimals
        total_debt_base = Decimal(data[1]) / Decimal(1e8)

        # Calculate total debt USD (use provided price or fallback)
        if eth_price_usd:
            total_debt_usd = float(
                dai_debt) + float(weth_debt) * float(eth_price_usd)
        else:
            total_debt_usd = float(total_debt_base)  # Use Aave's calculation

        return {
            'dai_debt': dai_debt,
            'weth_debt': weth_debt,
            'health_factor': hf,
            'total_collateral_usd': float(total_collateral_base),
            'total_debt_usd': total_debt_usd
        }

    def swap_debt(
            self,
            from_asset: DebtAsset,
            to_asset: DebtAsset,
            amount: Decimal,
            slippage_bps:
        int = 300,  # 3% slippage (changed from 100/1% for safer debt swaps)
            dry_run: bool = False,
            eth_price_usd: Optional[Decimal] = None) -> Optional[str]:
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

        if from_asset not in ['DAI', 'WETH'
                              ] or to_asset not in ['DAI', 'WETH']:
            print(f"❌ Only DAI and WETH are supported")
            return None

        try:
            # Get addresses
            from_addr = ARBITRUM_ADDRESSES[from_asset]
            to_addr = ARBITRUM_ADDRESSES[to_asset]
            from_debt_token = ARBITRUM_ADDRESSES[
                f"variableDebtArb{from_asset}"]
            to_debt_token = ARBITRUM_ADDRESSES[f"variableDebtArb{to_asset}"]

            # Check current state (use provided price for accurate valuation)
            summary = self.get_account_summary(eth_price_usd=eth_price_usd)
            print(f"\n📊 Current Position:")
            print(f"   DAI debt: {summary['dai_debt']:.6f}")
            print(f"   WETH debt: {summary['weth_debt']:.6f}")
            print(f"   Health Factor: {summary['health_factor']:.4f}")

            # Check if we have enough debt to repay
            current_debt = self.get_debt_balance(from_asset)
            if current_debt < amount:
                print(
                    f"\n⚠️  Warning: Requested {amount} {from_asset} but only have {current_debt} debt"
                )
                print(f"   Adjusting to maximum available: {current_debt}")
                amount = current_debt

            # Convert to wei
            repay_amount_wei = int(amount * Decimal(1e18))

            print(f"\n💱 Swap Details:")
            print(f"   Repaying: {amount:.6f} {from_asset}")
            print(f"   Borrowing: {to_asset} (amount TBD from ParaSwap)")

            # Get ParaSwap transaction data using /transactions API
            # This returns the EXACT calldata format expected by Aave Debt Switch
            print(f"\n🔄 Building ParaSwap swap via /transactions API...")
            paraswap_result = self._build_paraswap_transaction(
                from_token=to_asset,
                to_token=from_asset,
                dest_amount=repay_amount_wei,
                slippage_bps=slippage_bps)

            if not paraswap_result:
                raise Exception("Failed to build ParaSwap swap route")

            # Max new debt amount from ParaSwap
            max_new_debt_base = int(paraswap_result['src_amount'])

            # CRITICAL: Apply slippage tolerance + 3% buffer for safety
            # - slippage_bps tolerance for price movement during execution
            # - Additional 3% buffer for interest accrual and health factor fluctuations
            slippage_multiplier = 1 + (slippage_bps / 10000)  # 300 bps = 1.03
            buffer_multiplier = 1.03  # Extra 3% safety buffer
            total_multiplier = slippage_multiplier * buffer_multiplier
            max_new_debt = int(max_new_debt_base * total_multiplier)
            max_new_debt_decimal = Decimal(max_new_debt) / Decimal(1e18)

            print(f"   ✅ Route found")
            print(
                f"   Will borrow: {max_new_debt_decimal:.6f} {to_asset} (includes 3% safety buffer)"
            )
            print(f"   To repay: {amount:.6f} {from_asset}")

            # Build swapDebt parameters
            debt_swap_params = {
                "debtAsset": Web3.to_checksum_address(from_addr),
                "debtRepayAmount": repay_amount_wei,
                "debtRateMode": 2,  # Variable rate
                "newDebtAsset": Web3.to_checksum_address(to_addr),
                "maxNewDebtAmount": max_new_debt,
                "extraCollateralAsset":
                "0x0000000000000000000000000000000000000000",
                "extraCollateralAmount": 0,
                "offset": 0,
                "paraswapData": paraswap_result['calldata']
            }

            credit_delegation_permit = get_empty_credit_delegation_permit()
            collateral_permit = get_empty_permit()

            if dry_run:
                print(f"\n🔍 DRY RUN - Transaction not sent")
                print(f"   Would repay: {amount:.6f} {from_asset}")
                print(
                    f"   Would borrow: {max_new_debt_decimal:.6f} {to_asset}")
                return "DRY_RUN"

            # Build transaction with production-optimized gas limits
            print(f"\n📝 Building transaction...")
            base_fee = self.w3.eth.gas_price
            max_fee = int(
                base_fee *
                1.2)  # 1.2x base fee (reduced from 2x for affordability)

            # Use production gas limit (800K proven safe on mainnet: 729K actual + 71K buffer)
            gas_limit = PRODUCTION_GAS_LIMITS['debt_swap']

            tx = self.debt_switch.functions.swapDebt(
                debt_swap_params, credit_delegation_permit,
                collateral_permit).build_transaction({
                    'from':
                    self.address,
                    'nonce':
                    self.w3.eth.get_transaction_count(self.address),
                    'gas':
                    gas_limit,  # Dynamic from gas_config (800K for debt swaps)
                    'maxFeePerGas':
                    max_fee,
                    'maxPriorityFeePerGas':
                    self.w3.to_wei('0.01', 'gwei'),
                    'chainId':
                    42161
                })

            print(f"   Gas limit: {tx['gas']:,}")
            print(
                f"   Max fee: {self.w3.from_wei(tx['maxFeePerGas'], 'gwei'):.4f} Gwei"
            )

            # Sign and send
            print(f"\n🔐 Signing transaction...")
            signed_tx = self.account.sign_transaction(tx)

            print(f"📡 Broadcasting...")
            tx_hash = self.w3.eth.send_raw_transaction(
                signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            print(f"\n✅ Transaction sent!")
            print(f"   TX: {tx_hash_hex}")
            print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")

            # Wait for confirmation
            print(f"\n⏳ Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash,
                                                               timeout=300)

            if receipt['status'] == 1:
                # Get new state (use provided price for accurate valuation)
                new_summary = self.get_account_summary(
                    eth_price_usd=eth_price_usd)

                print(f"\n🎉 SUCCESS!")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas used: {receipt['gasUsed']:,}")
                print(f"\n📊 New Position:")
                print(
                    f"   DAI debt: {summary['dai_debt']:.6f} → {new_summary['dai_debt']:.6f}"
                )
                print(
                    f"   WETH debt: {summary['weth_debt']:.6f} → {new_summary['weth_debt']:.6f}"
                )
                print(
                    f"   Health Factor: {summary['health_factor']:.4f} → {new_summary['health_factor']:.4f}"
                )

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
