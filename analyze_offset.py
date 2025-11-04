from augustus_v5_multiswap_builder import AugustusV5MultiSwapBuilder
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU'))

DEBT_SWITCH_ADAPTER = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"

builder = AugustusV5MultiSwapBuilder(w3, network='arbitrum')

# Build multiSwap calldata using token symbols
from_amount = int(70 * 1e18)
to_amount = int(20 * 1e18)

print(f"Building multiSwap calldata with:")
print(f"  fromAmount: {from_amount} wei ({from_amount/1e18} ARB)")
print(f"  toAmount: {to_amount} wei ({to_amount/1e18} DAI)")
print()

result = builder.build_multiswap_calldata(
    from_token='ARB',
    to_token='DAI',
    from_amount=from_amount,
    min_to_amount=to_amount,
    beneficiary=DEBT_SWITCH_ADAPTER,
    use_buy_mode=True
)

if not result:
    print("Failed to build calldata")
    exit(1)

calldata = result['calldata']
actual_from_amount = result['from_amount']

print(f"\n✅ Calldata built successfully")
print(f"   Total length: {len(calldata)} chars ({len(calldata)//2} bytes)")
print(f"   Actual fromAmount: {actual_from_amount} wei ({actual_from_amount/1e18:.6f} ARB)")
print()

# Convert to hex without 0x
hex_data = calldata[2:]

# Search for the fromAmount value
from_amount_hex = hex(actual_from_amount)[2:].zfill(64)
print(f"Searching for fromAmount: {from_amount_hex}")
print()

if from_amount_hex in hex_data:
    char_pos = hex_data.index(from_amount_hex)
    byte_pos = char_pos // 2
    print(f"✅ FOUND fromAmount at:")
    print(f"   Character position: {char_pos}")
    print(f"   Byte position: {byte_pos}")
    print(f"   Hex offset: 0x{byte_pos:02x}")
    print()
    print(f"="*70)
    print(f"🎯 CORRECT OFFSET FOR DEBT SWITCH = {byte_pos}")
    print(f"="*70)
    print()
    
    # Show first 256 bytes with marker
    print(f"Calldata structure (first 256 bytes):")
    for i in range(0, min(512, len(hex_data)), 64):
        b_pos = i // 2
        chunk = hex_data[i:i+64]
        marker = " ← fromAmount" if i <= char_pos < i+64 else ""
        print(f"  Byte {b_pos:3d}: {chunk}{marker}")
else:
    print("❌ fromAmount not found - showing first 512 bytes:")
    for i in range(0, min(1024, len(hex_data)), 64):
        byte_pos = i // 2
        print(f"  Byte {byte_pos:3d}: {hex_data[i:i+64]}")
