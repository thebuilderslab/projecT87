#!/usr/bin/env python3
"""
Decode successful swap transactions to extract exact parameter structure
Analyzing: 0x131d57b4543338e4ed728a75e0a5571f3c1c21a5c6cad45c969dbd42a3571980 (DAI→WETH)
"""

from web3 import Web3

# Successful transaction input data from Arbiscan
# Transaction: 0x1654d629a2db455e6eb9509465d233b5d1e8050333ea030c5580d6c6ae4f1bae (WETH→DAI)
input_data_weth_to_dai = """
0xb8bd1c6b
00000000000000000000000000000000000000000000000000000000000001a0
0000000000000000000000000c84331e39d6658cd6e6b9ba04736cc4c4734351
0000000000000000000000000000000000000000000000000090d6c11b46db8d
00000000000000000000000000000000000000000000000000000000691a5683
000000000000000000000000000000000000000000000000000000000000001b
3b015bb29a832cb9b87efc81441921db2aac4d01b4b8d158d729c89fc1593e85
0deb201b13e153fe5359ab11126e28252a54f1ef9de83a0b63e1511f65404423
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000da10009cbd5d07dd0cecc66161fc93d7c9000da1
0000000000000000000000000000000000000000000000056bc75e2d63100000
0000000000000000000000000000000000000000000000000000000000000002
00000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab1
0000000000000000000000000000000000000000000000000073df00e29f160a
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000120
00000000000000000000000000000000000000000000000000000000000002e0
"""

# Clean and parse
input_hex = '0x' + ''.join(input_data_weth_to_dai.split())
print("=" * 80)
print("DECODING SUCCESSFUL WETH→DAI SWAP TRANSACTION")
print("=" * 80)
print(f"Input data length: {len(input_hex)} characters")
print(f"Method ID: {input_hex[:10]}")
print()

# Parse parameters (skip method ID)
data = input_hex[10:]
params = []
for i in range(0, len(data), 64):
    if i + 64 <= len(data):
        params.append(data[i:i+64])

print("PARAMETER STRUCTURE:")
print("-" * 80)
for idx, param in enumerate(params):
    value_int = int(param, 16)
    print(f"[{idx:2d}]: 0x{param}")
    if idx == 0:
        print(f"      → Offset to debtSwapParams struct: {value_int}")
    elif idx == 1:
        addr = '0x' + param[24:]
        print(f"      → Credit delegation debt token: {addr}")
    elif idx == 2:
        print(f"      → Credit delegation value: {value_int}")
    elif idx == 3:
        print(f"      → Credit delegation deadline: {value_int}")
    elif idx == 4:
        print(f"      → Credit delegation v: {value_int}")
    elif idx == 5:
        print(f"      → Credit delegation r: 0x{param}")
    elif idx == 6:
        print(f"      → Credit delegation s: 0x{param}")
    elif idx >= 7 and idx <= 12:
        print(f"      → Collateral permit param [{idx-7}]: {value_int if value_int > 0 else 'empty'}")
    elif idx == 13:
        addr = '0x' + param[24:]
        print(f"      → debtAsset (DAI): {addr}")
    elif idx == 14:
        print(f"      → debtRepayAmount: {value_int / 1e18:.6f} DAI")
    elif idx == 15:
        print(f"      → debtRateMode: {value_int} (2 = variable)")
    elif idx == 16:
        addr = '0x' + param[24:]
        print(f"      → newDebtAsset (WETH): {addr}")
    elif idx == 17:
        print(f"      → maxNewDebtAmount: {value_int / 1e18:.6f} WETH")
    elif idx == 18:
        addr = '0x' + param[24:]
        print(f"      → extraCollateralAsset: {addr if value_int > 0 else 'none'}")
    elif idx == 19:
        print(f"      → extraCollateralAmount: {value_int}")
    elif idx == 20:
        print(f"      → offset: {value_int}")
    elif idx == 21:
        print(f"      → Offset to paraswapData: {value_int}")
    elif idx == 22:
        print(f"      → Offset to permitParams: {value_int}")

print()
print("=" * 80)
print("CRITICAL FINDINGS:")
print("=" * 80)
print("✅ Function: swapDebt(tuple,tuple,tuple) - NOT debtSwitch()")
print("✅ Selector: 0xb8bd1c6b")
print("✅ Structure: THREE flat tuples as top-level parameters")
print("   1. debtSwapParams tuple (offset at [0])")
print("   2. creditDelegationPermit tuple (values at [1-6])")
print("   3. collateralATokenPermit tuple (values at [7-12])")
print()
print("🔍 debtSwapParams contains:")
print("   - debtAsset: DAI address")
print("   - debtRepayAmount: 100 DAI")
print("   - debtRateMode: 2 (variable)")
print("   - newDebtAsset: WETH address")
print("   - maxNewDebtAmount: ~0.0327 WETH")
print("   - extraCollateralAsset: 0x0 (none)")
print("   - extraCollateralAmount: 0")
print("   - offset: 0")
print("   - paraswapData: bytes (offset pointer)")
print("   - permitParams: array (offset pointer)")
print()
