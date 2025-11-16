# Aave V3 Autonomous Debt Swap System

## Project Overview
Autonomous debt swap arbitrage system on Aave V3 Arbitrum mainnet. Executes atomic DAI↔WETH debt swaps through Aave Debt Switch V3 contract using ParaSwap for routing.

## Current Status: **Implementation Complete** ✅

### ✅ Completed
- Correct `swapDebt()` function integration (selector: `0xb8bd1c6b`)
- ParaSwap BUY mode for exact output swaps
- WETH credit delegation (100 WETH approved)
- 3% slippage buffer on `maxNewDebtAmount`
- Curve router support for DAI/WETH swaps
- Comprehensive error handling and logging

### ⚠️ Blocker: Health Factor Too Low
- Current HF: 1.17 (too close to 1.0 liquidation threshold)
- **System configured for aggressive mode: HF minimum 1.05**
- **User must add small collateral** to raise HF to 1.05+ before swaps can execute
- See `HOW_TO_FIX_HEALTH_FACTOR.md` for instructions

## Project Structure

### Core Files
- `debt_swap_bidirectional.py` - Main bidirectional DAI↔WETH swapper
- `corrected_swap_debt_abi.py` - Correct Aave Debt Switch V3 ABI
- `augustus_v5_multiswap_builder.py` - ParaSwap integration with Curve support
- `delegate_weth_credit.py` - Credit delegation script
- `check_credit_delegation.py` - Verify delegation status

### Test Scripts
- `test_bidirectional_swap_live.py` - Full bidirectional test
- `test_smaller_swap.py` - Test with 5 DAI (lower HF impact)
- `test_reverse_swap.py` - Test WETH→DAI (increases HF)

### Documentation
- `FINAL_IMPLEMENTATION_SUMMARY.md` - Complete implementation overview
- `HOW_TO_FIX_HEALTH_FACTOR.md` - Guide to resolve HF blocker
- `DEBT_SWAP_STATUS_SUMMARY.md` - Detailed status report

### Workflows
- **Dashboard** (`python web_dashboard.py`) - Web UI on port 5000
- **Autonomous Agent** (`python run_autonomous_mainnet.py`) - Automated swap bot

## Key Technical Details

### Contracts
- **Aave Pool**: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- **Debt Switch V3**: `0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4`
- **Debt Switch Adapter**: `0x3a1CE362482Dc79Ce3F55C7ee2f76fd1d91e8eD8`
- **ParaSwap Augustus V5**: `0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57`
- **ArbitrumAdapter01**: `0x369A2FDb910d432f0a07381a5E3d27572c876713`

### Token Addresses
- **DAI**: `0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1`
- **WETH**: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`
- **Stable Debt DAI**: `0x307ffe186F84a3bc2613D1eA417A5737D69A7007`
- **Variable Debt WETH**: `0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351`

### Critical Fixes Applied
1. **Function Name**: Changed from `debtSwitch()` to `swapDebt()`
2. **ParaSwap Amount**: Return `actual_from_amount` instead of input parameter
3. **Credit Delegation**: 100 WETH delegated to adapter
4. **Slippage Buffer**: 3% added to `maxNewDebtAmount`
5. **Gas Pricing**: 2x base fee to ensure confirmation
6. **Curve Router**: Added support for CurveV1StableNg routes

## Usage

### Prerequisites
```bash
export PRIVATE_KEY="your_private_key"
export ARBITRUM_RPC_URL="https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY"
```

### Test Swaps (After Adding Collateral)
```bash
# Test 5 DAI → WETH swap
python3 test_smaller_swap.py

# Test WETH → DAI reverse swap  
python3 test_reverse_swap.py

# Full bidirectional test
python3 test_bidirectional_swap_live.py
```

### Check Credit Delegation
```bash
python3 check_credit_delegation.py
```

## Next Steps

1. **Add Collateral** (Required)
   - Go to https://app.aave.com/
   - Supply 0.01-0.02 ETH to raise HF to 1.2+
   - **Aggressive mode: only need HF > 1.05**
   - See `HOW_TO_FIX_HEALTH_FACTOR.md`

2. **Test Swaps**
   - Run `test_smaller_swap.py`
   - Verify successful execution
   - Check new health factor

3. **Enable Automation**
   - Restart `Autonomous Agent` workflow
   - Monitor logs for swap execution
   - Track health factor continuously

## Architecture

```
User Wallet
    │
    ├─► Aave V3 Pool
    │   └─► Supply Collateral
    │   └─► Monitor Health Factor
    │
    └─► Aave Debt Switch V3
        │
        ├─► Credit Delegation (100 WETH)
        │
        └─► swapDebt()
            │
            ├─► Flashloan (borrow new debt)
            │
            ├─► ParaSwap Augustus V5
            │   └─► ArbitrumAdapter01
            │       └─► UniswapV3 / Curve / Sushi
            │
            └─► Repay old debt
```

## Troubleshooting

### "execution reverted" (no specific error)
**Cause**: Health factor would drop below 1.0 during swap  
**Fix**: Add more collateral or reduce swap size

### "Missing router address for CurveV1StableNg"
**Cause**: Curve router not in fallback list  
**Fix**: Already fixed - added to `augustus_v5_multiswap_builder.py`

### "Credit delegation needed"
**Cause**: Adapter lacks permission to borrow WETH  
**Fix**: Already completed - 100 WETH delegated

## Important Transactions

- **Credit Delegation**: `0xc00dab6885706f18f9bc1b078fdb2f4decaffbfbd1bccd3d28b29d32ee56600b`
- **Latest Swap Attempt**: See test output for TX hash

## Links

- **Aave App**: https://app.aave.com/
- **Arbiscan**: https://arbiscan.io/
- **ParaSwap Docs**: https://developers.paraswap.network/
- **Aave Docs**: https://docs.aave.com/

## User Preferences

- **Coding Style**: Clean, well-documented Python with detailed logging
- **Safety**: Always verify health factor before swaps
- **Testing**: Comprehensive test coverage with real mainnet data
