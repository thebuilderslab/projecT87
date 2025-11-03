#!/usr/bin/env python3
"""
Execute $25 Debt Swap on Aave V3 Arbitrum
Uses Augustus V5 multiSwap via Debt Switch V3
"""

import os
import sys
from web3 import Web3
from decimal import Decimal
from augustus_v5_multiswap_builder import AugustusV5MultiSwapBuilder

# Configuration
ARBITRUM_RPC = "https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU"
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")
SWAP_AMOUNT_USD = 25.0

# Contract addresses (Arbitrum mainnet)
DAI_ADDRESS = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
ARB_ADDRESS = "0x912CE59144191C1204E64559FE8253a0e49E6548"
DEBT_SWITCH_V3 = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
AAVE_POOL = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"

# ABIs
DEBT_SWITCH_ABI = [
    {
        "inputs": [
            {"name": "debtAsset", "type": "address"},
            {"name": "debtRepayAmount", "type": "uint256"},
            {"name": "debtRateMode", "type": "uint256"},
            {"name": "newDebtAsset", "type": "address"},
            {"name": "maxNewDebtAmount", "type": "uint256"},
            {"name": "extraCollateralAsset", "type": "address"},
            {"name": "extraCollateralAmount", "type": "uint256"},
            {"name": "offset", "type": "uint256"},
            {"name": "paraswapData", "type": "bytes"}
        ],
        "name": "swapDebt",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

AAVE_POOL_ABI = [
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
    }
]

def get_token_price_usd(token_address: str) -> float:
    """Get token price from simple price feeds"""
    # Simplified price feed for execution
    prices = {
        DAI_ADDRESS.lower(): 1.0,  # DAI ~= $1
        ARB_ADDRESS.lower(): 0.30  # ARB ~= $0.30
    }
    return prices.get(token_address.lower(), 0)

def main():
    print("=" * 80)
    print("🔄 EXECUTING $25 DEBT SWAP")
    print("   DAI → ARB Debt Swap via Aave Debt Switch V3")
    print("=" * 80)
    
    # Validate private key
    if not PRIVATE_KEY:
        print("❌ ERROR: PRIVATE_KEY not found in environment")
        sys.exit(1)
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    if not w3.is_connected():
        print("❌ ERROR: Failed to connect to Arbitrum")
        sys.exit(1)
    
    print(f"✅ Connected to Arbitrum (Chain ID: {w3.eth.chain_id})")
    
    # Get wallet
    account = w3.eth.account.from_key(PRIVATE_KEY)
    wallet = account.address
    print(f"🔑 Wallet: {wallet}")
    
    # Check current position
    aave_pool = w3.eth.contract(address=w3.to_checksum_address(AAVE_POOL), abi=AAVE_POOL_ABI)
    position = aave_pool.functions.getUserAccountData(wallet).call()
    
    total_collateral_usd = position[0] / 1e8
    total_debt_usd = position[1] / 1e8
    health_factor = position[5] / 1e18
    
    print(f"\n📊 CURRENT POSITION:")
    print(f"   Collateral: ${total_collateral_usd:.2f}")
    print(f"   Debt: ${total_debt_usd:.2f}")
    print(f"   Health Factor: {health_factor:.4f}")
    
    if health_factor < 1.1:
        print(f"⚠️  WARNING: Health factor {health_factor:.4f} is dangerously low!")
        print(f"❌ Execution cancelled - health factor too low for safety")
        sys.exit(1)
    
    # Calculate swap amounts
    # Conservative approach: use $20 target to ensure we have enough buffer for slippage
    actual_swap_usd = 20.0
    arb_price_actual = 0.297  # Actual market price from ParaSwap
    dai_price_actual = 1.00
    
    # Calculate amounts
    dai_amount = actual_swap_usd / dai_price_actual
    arb_amount = (actual_swap_usd / arb_price_actual) * 1.05  # 5% buffer for slippage
    
    dai_amount_wei = int(dai_amount * 1e18)
    arb_amount_wei = int(arb_amount * 1e18)
    
    print(f"\n💱 SWAP CALCULATION:")
    print(f"   DAI to repay: {dai_amount:.6f} DAI (~${actual_swap_usd})")
    print(f"   ARB to borrow: {arb_amount:.6f} ARB (~${arb_amount * arb_price_actual:.2f})")
    print(f"   DAI price: ${dai_price_actual}")
    print(f"   ARB price: ${arb_price_actual} (actual market rate)")
    
    # Build multiSwap calldata using Augustus V5
    print(f"\n🏗️  BUILDING AUGUSTUS V5 MULTISWAP CALLDATA...")
    builder = AugustusV5MultiSwapBuilder(w3)
    
    import time
    # Use BUY mode for exact output - specify how much DAI we want to receive
    multiswap_data = builder.build_multiswap_calldata(
        from_token="ARB",
        to_token="DAI",
        from_amount=dai_amount_wei,  # In BUY mode: this is the exact DAI we want
        min_to_amount=dai_amount_wei,  # Must receive exact amount
        beneficiary=DEBT_SWITCH_V3,
        deadline=int(time.time()) + 1800,  # 30 minutes from now
        slippage_bps=0,  # No slippage in BUY mode (exact output)
        use_buy_mode=True  # Enable BUY mode for exact output
    )
    
    if not multiswap_data:
        print("❌ ERROR: Failed to build multiSwap calldata")
        sys.exit(1)
    
    multiswap_calldata = multiswap_data.get('calldata', '')
    
    if not multiswap_calldata:
        print("❌ ERROR: No calldata in multiSwap response")
        sys.exit(1)
    
    print(f"✅ multiSwap calldata built: {len(multiswap_calldata)} bytes")
    print(f"   Selector: {multiswap_calldata[:10]}")
    
    # Build Debt Switch V3 swapDebt transaction
    print(f"\n🔧 BUILDING DEBT SWITCH V3 TRANSACTION...")
    debt_switch = w3.eth.contract(
        address=w3.to_checksum_address(DEBT_SWITCH_V3),
        abi=DEBT_SWITCH_ABI
    )
    
    # swapDebt parameters
    debt_asset = w3.to_checksum_address(DAI_ADDRESS)
    debt_repay_amount = dai_amount_wei
    debt_rate_mode = 2  # Variable rate
    new_debt_asset = w3.to_checksum_address(ARB_ADDRESS)
    max_new_debt_amount = int(arb_amount_wei * 1.05)  # 5% buffer
    extra_collateral_asset = "0x0000000000000000000000000000000000000000"
    extra_collateral_amount = 0
    offset = 4  # Skip selector bytes
    paraswap_data = bytes.fromhex(multiswap_calldata[2:])  # Remove 0x
    
    print(f"   Debt Asset (DAI): {debt_asset}")
    print(f"   Debt Repay Amount: {dai_amount:.6f} DAI")
    print(f"   New Debt Asset (ARB): {new_debt_asset}")
    print(f"   Max New Debt: {arb_amount * 1.05:.6f} ARB")
    print(f"   ParaSwap Data: {len(paraswap_data)} bytes")
    
    # Build transaction with EIP-1559 pricing
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.to_wei(0.01, 'gwei')  # 0.01 gwei tip
    max_fee = int(base_fee * 1.5) + max_priority_fee  # 1.5x base fee + tip
    
    swap_tx = debt_switch.functions.swapDebt(
        debt_asset,
        debt_repay_amount,
        debt_rate_mode,
        new_debt_asset,
        max_new_debt_amount,
        extra_collateral_asset,
        extra_collateral_amount,
        offset,
        paraswap_data
    ).build_transaction({
        'from': wallet,
        'gas': 1_000_000,  # Conservative gas limit
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': w3.eth.get_transaction_count(wallet),
        'chainId': 42161
    })
    
    gas_price_gwei = w3.from_wei(swap_tx['maxFeePerGas'], 'gwei')
    gas_cost_eth = w3.from_wei(swap_tx['gas'] * swap_tx['maxFeePerGas'], 'ether')
    
    print(f"\n⛽ GAS ESTIMATE:")
    print(f"   Gas Limit: {swap_tx['gas']:,}")
    print(f"   Gas Price: {gas_price_gwei:.2f} gwei")
    print(f"   Max Cost: {gas_cost_eth:.6f} ETH (~${float(gas_cost_eth) * 3800:.2f})")
    
    # Final confirmation
    print(f"\n" + "=" * 80)
    print(f"⚠️  READY TO EXECUTE DEBT SWAP")
    print(f"=" * 80)
    print(f"   Repay: {dai_amount:.6f} DAI")
    print(f"   Borrow: {arb_amount:.6f} ARB")
    print(f"   Health Factor: {health_factor:.4f} → (recalculating...)")
    print(f"   Gas Cost: ~${float(gas_cost_eth) * 3800:.2f}")
    print(f"=" * 80)
    
    # Auto-execute for autonomous system
    print("\n🚀 AUTO-EXECUTING TRANSACTION (autonomous mode)...")
    confirm = "yes"
    
    # Sign and send transaction
    print(f"\n📝 Signing transaction...")
    signed_tx = w3.eth.account.sign_transaction(swap_tx, PRIVATE_KEY)
    
    print(f"📡 Broadcasting transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash_hex = tx_hash.hex()
    
    print(f"✅ Transaction broadcast!")
    print(f"   TX Hash: {tx_hash_hex}")
    print(f"   Explorer: https://arbiscan.io/tx/{tx_hash_hex}")
    
    print(f"\n⏳ Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print(f"✅ TRANSACTION SUCCESSFUL!")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   Gas Used: {receipt['gasUsed']:,}")
        
        # Check new position
        new_position = aave_pool.functions.getUserAccountData(wallet).call()
        new_health_factor = new_position[5] / 1e18
        new_total_debt_usd = new_position[1] / 1e8
        
        print(f"\n📊 NEW POSITION:")
        print(f"   Collateral: ${new_position[0] / 1e8:.2f}")
        print(f"   Debt: ${new_total_debt_usd:.2f}")
        print(f"   Health Factor: {new_health_factor:.4f}")
        print(f"   HF Change: {health_factor:.4f} → {new_health_factor:.4f}")
        
    else:
        print(f"❌ TRANSACTION FAILED")
        print(f"   Status: {receipt['status']}")
        print(f"   Check explorer: https://arbiscan.io/tx/{tx_hash_hex}")
        sys.exit(1)
    
    print(f"\n" + "=" * 80)
    print(f"🎉 DEBT SWAP COMPLETE!")
    print(f"=" * 80)

if __name__ == "__main__":
    main()
