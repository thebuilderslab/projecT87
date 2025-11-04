import requests
import json
from web3 import Web3

# Check multiple recent failed transactions on Arbiscan
tx_hashes = [
    '0x3a58b71c5fbebee1e13e5464279d1a24b9df36e60d9ba4be4280a8554f5888ba',  # offset=36
    '0x46d9c6a06da36fce0cdd3e57ef9ccbe1cc94d8995460ff528e11e3f4b5cb8a9f',  # offset=100
]

print("=" * 80)
print("CHECKING ARBISCAN FOR REVERT DETAILS")
print("=" * 80)
print()

for tx_hash in tx_hashes:
    print(f"Transaction: {tx_hash}")
    print(f"Explorer: https://arbiscan.io/tx/{tx_hash}")
    print()

print("=" * 80)
print("ALTERNATIVE: Use Tenderly for detailed trace")
print("=" * 80)
print()

for tx_hash in tx_hashes:
    print(f"Tenderly: https://dashboard.tenderly.co/tx/arbitrum/{tx_hash}")

print()
print("=" * 80)
print("ANALYZING TRANSACTION INPUT vs EXPECTED")
print("=" * 80)
print()

w3 = Web3(Web3.HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU'))

tx_hash = tx_hashes[0]
tx = w3.eth.get_transaction(tx_hash)
input_hex = tx['input'].hex()[2:]

# Parse debtSwitch parameters
print("debtSwitch parameters decoded:")
print()

# Assets struct (debtAsset, debtRepayAmount)
debt_asset = '0x' + input_hex[32:72]
debt_repay_amount_hex = input_hex[72:136]
debt_repay_amount = int(debt_repay_amount_hex, 16)

print(f"Assets.debtAsset: {debt_asset}")
print(f"Assets.debtRepayAmount: {debt_repay_amount} ({debt_repay_amount/1e18} DAI)")
print()

# DebtSwitchParams
# Next should be debtRateMode (uint256)
debt_rate_mode_hex = input_hex[136:200]
debt_rate_mode = int(debt_rate_mode_hex, 16)

new_debt_asset = '0x' + input_hex[200:240]
max_new_debt_hex = input_hex[240:304]
max_new_debt = int(max_new_debt_hex, 16)

print(f"DebtSwitchParams.debtRateMode: {debt_rate_mode}")
print(f"DebtSwitchParams.newDebtAsset: {new_debt_asset}")
print(f"DebtSwitchParams.maxNewDebtAmount: {max_new_debt} ({max_new_debt/1e18} ARB)")
print()

# extraCollateralAsset, extraCollateralAmount
extra_collateral_asset = '0x' + input_hex[304:344]
extra_collateral_amount_hex = input_hex[344:408]
extra_collateral_amount = int(extra_collateral_amount_hex, 16)

print(f"DebtSwitchParams.extraCollateralAsset: {extra_collateral_asset}")
print(f"DebtSwitchParams.extraCollateralAmount: {extra_collateral_amount}")
print()

# offset
offset_hex = input_hex[408:472]
offset = int(offset_hex, 16)
print(f"DebtSwitchParams.offset: {offset} (0x{offset:02x})")
print()

# paraswapData offset pointer
paraswap_data_offset_hex = input_hex[472:536]
paraswap_data_offset = int(paraswap_data_offset_hex, 16)
print(f"DebtSwitchParams.paraswapData offset pointer: {paraswap_data_offset}")
print()

# Find the actual ParaSwap data
# The offset is relative to the start of DebtSwitchParams
# Let's find where ParaSwap data starts
print("Checking ParaSwap calldata structure...")
print()

# Look for the multiSwap selector (0x0863b7ac)
multiswap_selector = '0863b7ac'
if multiswap_selector in input_hex:
    pos = input_hex.index(multiswap_selector)
    byte_pos = pos // 2
    print(f"✅ Found multiSwap selector at byte {byte_pos}")
    print(f"   Selector: 0x{input_hex[pos:pos+8]}")
    print()
    
    # Check what's at offset 36 from this position
    fromAmount_pos = pos + 8 + (36 * 2)  # selector (4 bytes = 8 hex) + offset (36 bytes = 72 hex)
    fromAmount_hex = input_hex[fromAmount_pos:fromAmount_pos+64]
    fromAmount = int(fromAmount_hex, 16)
    
    print(f"At offset 36 from multiSwap selector:")
    print(f"  Position: byte {fromAmount_pos//2}")
    print(f"  Value: {fromAmount} ({fromAmount/1e18:.6f} ARB)")
    print()
    
    if fromAmount > 0:
        print("✅ Offset 36 points to a valid non-zero value!")
    else:
        print("❌ Offset 36 points to ZERO - this would cause borrow failure!")
else:
    print("❌ multiSwap selector not found in transaction data")

