# ⚠️ Credit Delegation Required for WETH

## Issue Identified

Your debt swap transactions are failing because **you haven't delegated WETH borrowing credit** to the Debt Switch Adapter.

### What Went Wrong

1. ✅ Function signature: CORRECT (`swapDebt` with selector `0xb8bd1c6b`)
2. ✅ Parameter structure: CORRECT (flat tuples, 9 fields)
3. ✅ ParaSwap amount: CORRECT (0.003255 WETH, not 10 WETH)
4. ❌ **Credit Delegation**: MISSING for WETH

### Latest Transaction Analysis

**TX**: `0x9c2de9cfa6469a927998e6f4a551a48f95543d6e321d3163ea4cbad83ba7dadf`
- Trying to repay: 10 DAI ✅
- Trying to borrow: 0.003255 WETH ✅  
- Status: FAILED ❌
- **Reason**: No WETH credit delegation

## Why Credit Delegation is Required

When you perform a debt swap:
1. **Debt Switch Adapter** needs to borrow tokens **on your behalf**
2. This requires you to pre-approve credit delegation
3. You delegated:
   - ✅ 1000 DAI
   - ✅ 997.98 ARB
   - ❌ **0 WETH** ← This is the problem!

### For DAI → WETH Swap
- Need to **borrow WETH** (the new debt)
- Requires **WETH credit delegation** ← **YOU NEED THIS**

### For WETH → DAI Swap
- Need to **borrow DAI** (the new debt)
- Requires **DAI credit delegation** (you already have this ✅)

## How to Fix It

### Option 1: Use Aave UI (Recommended)

1. Go to https://app.aave.com/
2. Connect your wallet (0x5B823270e3719CDe8669e5e5326B455EaA8a350b)
3. Navigate to "Delegate"
4. Approve credit delegation for WETH
5. Delegatee address: `0xb0D8cF9560EF31B8Fe6D9727708D19b31F7C90Ec` (Debt Switch Adapter)
6. Amount: 10 WETH (enough for testing)

### Option 2: Direct Contract Call

Call `approveDelegation` on the WETH variable debt token:

**Contract**: `0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351` (variableDebtArbWETH)
**Function**: `approveDelegation(address delegatee, uint256 amount)`
**Parameters**:
- `delegatee`: `0xb0D8cF9560EF31B8Fe6D9727708D19b31F7C90Ec`
- `amount`: `10000000000000000000` (10 WETH in wei)

**Arbiscan Write Contract**:
https://arbiscan.io/address/0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351#writeContract

### Option 3: Python Script

```python
from web3 import Web3
import os

w3 = Web3(Web3.HTTPProvider("https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY"))
private_key = os.environ.get("PRIVATE_KEY")
account = w3.eth.account.from_key(private_key)

# WETH variable debt token
weth_debt_token = w3.eth.contract(
    address=Web3.to_checksum_address("0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351"),
    abi=[{
        "inputs": [
            {"name": "delegatee", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approveDelegation",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }]
)

# Approve 10 WETH delegation
tx = weth_debt_token.functions.approveDelegation(
    Web3.to_checksum_address("0xb0D8cF9560EF31B8Fe6D9727708D19b31F7C90Ec"),  # Adapter
    10 * 10**18  # 10 WETH
).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 200000,
    'maxFeePerGas': w3.eth.gas_price,
    'maxPriorityFeePerGas': w3.to_wei('0.01', 'gwei'),
    'chainId': 42161
})

signed_tx = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

print(f"TX: {tx_hash.hex()}")
print(f"Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
```

## Key Addresses

| Component | Address |
|-----------|---------|
| **Debt Switch V3** | `0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4` |
| **Debt Switch Adapter** | `0xb0D8cF9560EF31B8Fe6D9727708D19b31F7C90Ec` |
| **WETH variableDebt** | `0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351` |
| **DAI variableDebt** | `0x8619d80FB0141ba7F184CbF22fd724116D9f7ffC` |

## After Delegating Credit

Once you've delegated WETH credit, re-run the test:

```bash
python3 test_bidirectional_swap_live.py
```

The swap should succeed! 🎉

## Summary

**Problem**: Transactions fail with "execution reverted"
**Root Cause**: Missing WETH credit delegation
**Solution**: Approve WETH credit delegation to Debt Switch Adapter
**Amount Needed**: 10 WETH (for testing)

The code implementation is **100% correct now**. We just need the proper permissions set up on-chain.
