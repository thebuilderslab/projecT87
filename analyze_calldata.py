from web3 import Web3
import json

# Read the last execution's calldata from logs
with open('/tmp/debt_swap_corrected.log', 'r') as f:
    log_content = f.read()

# Extract the calldata from execute_debt_swap_25.py output
# The script stores it in memory, so let me rebuild it instead

from augustus_v5_multiswap_builder import AugustusV5MultiSwapBuilder
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU'))

ARB_ADDRESS = "0x912CE59144191C1204E64559FE8253a0e49E6548"
DAI_ADDRESS = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
DEBT_SWITCH_ADAPTER = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"

builder = AugustusV5MultiSwapBuilder(w3, chain='arbitrum')

# Build a sample multiswap calldata
result = builder.build_multiswap_calldata(
    from_token=ARB_ADDRESS,
    to_token=DAI_ADDRESS,
    from_amount=int(70.7 * 1e18),  # Approximate ARB amount
    min_amount=int(20 * 1e18),      # 20 DAI minimum
    beneficiary=DEBT_SWITCH_ADAPTER,
    mode='BUY',
    exact_output_amount=int(20 * 1e18)
)

if result:
    calldata = result['calldata']
    print(f"Calldata: {calldata[:200]}...")
    print(f"\nCalldata length: {len(calldata)} chars ({len(calldata)//2} bytes)")
    print(f"\nAnalyzing byte positions:")
    print(f"=" * 80)
    
    # Remove 0x prefix
    hex_data = calldata[2:]
    
    # Decode byte by byte
    print(f"Bytes 0-3 (selector): {hex_data[0:8]}")
    print(f"Bytes 4-35 (param 1): {hex_data[8:72]}")
    
    # Try to find fromAmount value
    from_amount_hex = hex(int(70.7 * 1e18))[2:].zfill(64)
    print(f"\nSearching for fromAmount: {from_amount_hex}")
    
    # Find its position
    if from_amount_hex in hex_data:
        pos = hex_data.index(from_amount_hex)
        byte_pos = pos // 2
        print(f"✅ Found at character position {pos} = byte position {byte_pos}")
    else:
        # Try searching for a close value (ParaSwap might adjust it)
        print("❌ Exact value not found - ParaSwap may have adjusted the amount")
        print(f"\nFirst 200 bytes of calldata:")
        for i in range(0, min(400, len(hex_data)), 64):
            byte_pos = i // 2
            print(f"  Byte {byte_pos:3d}: {hex_data[i:i+64]}")

else:
    print("Failed to build calldata")
