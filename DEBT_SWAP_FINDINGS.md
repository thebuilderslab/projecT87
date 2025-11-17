# Aave Debt Swap Debugging Findings

## Executive Summary

Successfully identified the root cause of debt swap failures: **ParaSwap REST API cannot generate the GenericAdapter wrapper required for Aave Debt Switch V3 integration**.

## ✅ What Was Successfully Fixed

### 1. Augustus V6.2 Integration
- **Discovery**: ParaSwap REST API accepts `version=6.2` parameter
- **Implementation**: Added to `/prices` endpoint configuration
- **Result**: Successfully switched from Augustus V5 to V6.2 contract

### 2. Correct Method Selector
- **Target**: `swapOnUniswapV2Fork` (selector `0x7f457675`)
- **Solution**: Exclude UniswapV3 DEX with `excludeDEXS: 'UniswapV3,CurveV1,CurveV2'`
- **Result**: API now returns correct method matching working transactions

### 3. ParaSwap API Configuration
- **Parameter**: `ignoreChecks=true` + `ignoreGasEstimate=true`
- **Purpose**: Skip balance validation (Debt Switch receives funds via flash loan)
- **Status**: Correctly implemented

### 4. Receiver Configuration
- **Parameter**: `receiver=DEBT_SWITCH_V3_ADDRESS`
- **Purpose**: Direct swap proceeds to Debt Switch for debt repayment
- **Status**: Configured but insufficient (see blocker below)

## ❌ Remaining Blocker: GenericAdapter Wrapper

### The Problem

**Working Transactions:**
- Calldata size: **3,332 bytes**
- Structure: `swapOnUniswapV2Fork` + GenericAdapter wrapper
- Success rate: 100% on mainnet

**API-Generated Transactions:**
- Calldata size: **836 bytes**  
- Structure: `swapOnUniswapV2Fork` (no wrapper)
- Revert error: `0x1bbb4abe` (Augustus custom error: insufficient repay amount)

### Root Cause

The ParaSwap REST API (`https://api.paraswap.io`) does not generate the GenericAdapter wrapper segment needed for Aave Debt Switch integration, regardless of parameters used.

**Tested configurations (all returned 836 bytes):**
- `receiver` parameter
- `receiver` + `partner` + `partnerAddress`  
- `receiver` + `takeSurplus`
- Various `includeContractMethods` / `excludeContractMethods` combinations

### Why It Fails

Without the GenericAdapter wrapper:
1. Swap executes correctly (gas usage ~382K shows execution path completes)
2. But swap proceeds go to wrong destination
3. Debt Switch has zero balance for debt repayment
4. Augustus reverts with custom error `0x1bbb4abe`

## 📊 Transaction Comparison

| Attribute | Working TX (Mainnet) | Our TX (API-generated) |
|-----------|---------------------|------------------------|
| Augustus | V6.2 (`0x6a000f20...`) | V6.2 (`0x6a000f20...`) ✅ |
| Selector | `0x7f457675` | `0x7f457675` ✅ |
| Calldata Size | 3,332 bytes | 836 bytes ❌ |
| GenericAdapter | Yes | No ❌ |
| On-chain Result | Success ✅ | Revert `0x1bbb4abe` ❌ |

## 🔍 Technical Deep Dive

### Working Transaction Structure
```
swapOnUniswapV2Fork(
  ... standard swap parameters ...
  + GenericAdapter wrapper (adds ~2,496 bytes)
    ↳ Contains routing to forward proceeds to Debt Switch
    ↳ Ensures flash-loan-aware execution
)
```

### API-Generated Structure
```
swapOnUniswapV2Fork(
  ... standard swap parameters only ...
  ✗ No GenericAdapter wrapper
  ✗ Proceeds default to user EOA instead of Debt Switch
)
```

## 💡 Potential Solutions

### Option 1: ParaSwap TypeScript SDK
The TypeScript SDK (`@paraswap/sdk`) may expose additional configuration not available via REST API.

**Pros:**
- Official ParaSwap tooling
- Likely has GenericAdapter support
- Maintained and documented

**Cons:**
- Requires Node.js/TypeScript setup in Python project
- May need inter-process communication

**Feasibility:** High

### Option 2: Manual Calldata Replication
Decode working transaction's 3,332-byte calldata and reverse-engineer GenericAdapter ABI structure.

**Pros:**
- Full control over calldata
- No external dependencies once built

**Cons:**
- Complex reverse engineering (~2,496 bytes of adapter logic)
- Brittle (breaks if ParaSwap updates GenericAdapter)
- Time-intensive implementation

**Feasibility:** Medium

### Option 3: Direct DEX Integration  
Bypass ParaSwap entirely and swap directly on Uniswap V2/V3 or Curve within the debt switch transaction.

**Pros:**
- Full control
- No ParaSwap dependency
- Simpler calldata

**Cons:**
- Worse swap rates (no aggregation)
- Need to implement routing logic
- Higher slippage risk

**Feasibility:** Medium

### Option 4: Contact ParaSwap Support
Request official guidance on generating Aave Debt Switch-compatible calldata.

**Pros:**
- May reveal hidden API parameters
- Official solution if one exists

**Cons:**
- Response time unknown
- May not be supported via REST API

**Feasibility:** Unknown

## 📁 Key Files

- `debt_swap_bidirectional.py`: Main implementation with V6.2 + correct selector
- `working_calldata_full.bin`: 3,332-byte calldata from successful transaction
- `augustus_v5_multiswap_builder.py`: Custom builder (may need GenericAdapter support)
- Working TX: `0xf5a73c455f77475d7741ba2a851cdfae5c221f5fc3be188ee41bec9a4a315b65`

## 🎯 Recommendation

**Immediate:** Try Option 1 (TypeScript SDK) first
- Quick to test
- Highest probability of official support for Aave integration
- Can fall back to Option 2 if unsuccessful

**Fallback:** Option 2 (Manual replication) if SDK doesn't expose needed functionality

**Not Recommended:** Option 3 (worse UX due to poor rates)

## 📈 Progress Summary

**Completed:**
- ✅ Identified exact Augustus contract and method needed
- ✅ Configured ParaSwap API for V6.2 + swapOnUniswapV2Fork
- ✅ Isolated root cause (GenericAdapter wrapper)
- ✅ Validated all parameters are correctly formatted

**Remaining:**
- ❌ Generate or manually build 3,332-byte calldata with GenericAdapter wrapper

**Effort Estimate:**
- Option 1 (SDK): 2-4 hours
- Option 2 (Manual): 8-12 hours
