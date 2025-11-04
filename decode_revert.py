from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU'))

# Most recent failed transaction
tx_hash = '0x3a58b71c5fbebee1e13e5464279d1a24b9df36e60d9ba4be4280a8554f5888ba'

print("=" * 80)
print("DECODING REVERT REASON")
print("=" * 80)
print(f"Transaction: {tx_hash}")
print()

tx = w3.eth.get_transaction(tx_hash)
receipt = w3.eth.get_transaction_receipt(tx_hash)

print(f"Status: {receipt['status']} (failed)")
print(f"Gas Used: {receipt['gasUsed']:,}")
print(f"Block: {receipt['blockNumber']}")
print()

# Get input data as hex string
input_hex = tx['input'].hex() if isinstance(tx['input'], bytes) else tx['input']
if input_hex.startswith('0x'):
    input_hex = input_hex[2:]

print(f"Transaction to: {tx['to']}")
print(f"Function selector: 0x{input_hex[:8]}")
print()

# Try different methods to get revert reason
print("Method 1: Replay transaction with eth_call")
print("-" * 80)
try:
    result = w3.eth.call({
        'from': tx['from'],
        'to': tx['to'],
        'data': tx['input'],
        'value': tx.get('value', 0),
        'gas': tx['gas']
    }, block_identifier=receipt['blockNumber'] - 1)
    print("❌ No revert detected (transaction would succeed)")
except Exception as e:
    print("✅ REVERT DETECTED!")
    error_str = str(e)
    print(f"Error: {error_str}")
    print()
    
    # Try to extract revert data
    if 'execution reverted:' in error_str:
        reason = error_str.split('execution reverted:')[1].strip()
        print(f"🎯 REVERT REASON: {reason}")

print()
print("Method 2: Try debug_traceTransaction (if available)")
print("-" * 80)
try:
    trace = w3.provider.make_request('debug_traceTransaction', [tx_hash, {}])
    if 'error' in trace:
        print(f"Debug trace not available: {trace['error']}")
    else:
        print("Trace obtained - analyzing...")
        # This would require parsing the trace
        print(json.dumps(trace, indent=2)[:500])
except Exception as e:
    print(f"Debug trace not available: {e}")

print()
print("Method 3: Try trace_replayTransaction (if available)")
print("-" * 80)
try:
    trace = w3.provider.make_request('trace_replayTransaction', [tx_hash, ['trace', 'stateDiff']])
    if 'error' in trace:
        print(f"Trace replay not available: {trace['error']}")
    else:
        print("Trace obtained!")
        print(json.dumps(trace, indent=2)[:500])
except Exception as e:
    print(f"Trace replay not available: {e}")

print()
print("Method 4: Use Tenderly API for detailed trace")
print("-" * 80)
print(f"Manual trace URL: https://dashboard.tenderly.co/tx/arbitrum/{tx_hash}")
print()

# Analyze transaction parameters
print("=" * 80)
print("TRANSACTION PARAMETERS SENT")
print("=" * 80)

# Decode the debtSwitch function parameters
# Function signature: debtSwitch((address,uint256),(address,uint256,uint256,address,uint256,address,uint256,bytes),((address,uint256)[]),((address,uint256,uint8,bytes32,bytes32)[]))

print(f"To contract: {tx['to']}")
print(f"Selector: 0x{input_hex[:8]}")
print()

if input_hex[:8] == '7ff9fe4c':  # debtSwitch selector
    print("✅ Function: debtSwitch")
    print()
    print("Raw calldata (first 768 bytes):")
    for i in range(0, min(1536, len(input_hex)), 64):
        byte_pos = i // 2
        chunk = input_hex[i:i+64]
        print(f"  Byte {byte_pos:3d}: {chunk}")
else:
    print(f"Unknown function selector: 0x{input_hex[:8]}")

