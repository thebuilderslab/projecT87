# Jovan Bot - Aave V3 Autonomous Debt Management System

## Project Overview
Autonomous Aave V3 debt management system on Arbitrum Mainnet with two distinct execution paths. Monitors collateral growth from a $47 baseline and executes fixed-value borrowing operations.

## Current Status: **Phase 1 Finalized** 

## Architecture

### Dual-Path Execution System

**Growth Path ($10.20 borrow)** - PRIORITY 1 (checked first)
- Activates on: 10% relative OR $50 absolute collateral growth from baseline
- Requires: Health factor >= 1.35, Available capacity >= $12
- Distribution:
  - $3.00 DAI supply to Aave
  - $3.00 DAI -> WBTC swap + supply to Aave
  - $2.00 DAI -> WETH swap + supply to Aave
  - $1.10 DAI -> ETH (gas reserve, held in wallet)
  - $1.10 DAI transfer to WALLET_S_ADDRESS

**Capacity Path ($5.50 borrow)** - PRIORITY 2 (checked only if growth didn't fire)
- Activates when: Available capacity >= $7
- Requires: Health factor >= 1.35
- Distribution:
  - $1.10 DAI supply to Aave
  - $1.10 DAI -> WBTC swap + supply to Aave
  - $1.10 DAI -> WETH swap + supply to Aave
  - $1.10 DAI -> ETH (gas reserve, held in wallet)
  - $1.10 DAI transfer to WALLET_S_ADDRESS

### Global Execution Lock
- `is_transacting` flag prevents double-borrowing against same collateral jump
- 130s cooldown between operations (`operation_cooldown_seconds`)
- Lock set on entry to `_execute_fixed_distribution()`, cleared on exit
- Lock stays active while `execution_state.json` has incomplete steps

### Crash Recovery (execution_state.json)
- After each successful on-chain step, state is persisted to `execution_state.json`
- Steps tracked: borrowed → dai_supplied → wbtc_supplied → weth_supplied → eth_converted → wallet_s_transferred
- On startup, agent checks for interrupted sequences and resumes from next incomplete step
- State file is wiped ONLY after successful confirmation of final WALLET_S transfer
- Helper methods: `save_execution_state()`, `load_execution_state()`, `clear_execution_state()`

### Proportional Recovery (`_execute_proportional_recovery`)
- Activated when DAI in wallet is insufficient for all remaining steps after a crash
- Nonce sync: calls `eth.get_transaction_count` before first recovery tx to clear dashboard conflicts
- Scaling factor: `scaling = current_dai / original_remaining_need` (capped at 1.0)
- Dust guard: any step scaled below $1.00 is skipped, its amount rolled into WALLET_S transfer
- Steps execute individually — failed swaps don't block remaining steps
- Leftover DAI from failed swaps gets supplied as Aave collateral (safety net)
- State only cleared after WALLET_S transfer confirmed on-chain
- Max 5 recovery attempts before force-clearing stale state

### Non-Blocking Step Execution
- In `_execute_fixed_distribution`, failed swap steps (WBTC, WETH, ETH) no longer block subsequent steps
- WALLET_S transfer always attempted regardless of swap failures
- Steps that fail are tracked in `steps_failed` list and reported at completion
- If WALLET_S transfer succeeds but some swaps failed, path is marked as "partial" success

### Liability Short Strategy — PRIORITY 3 (checked after Growth/Capacity, before IDLE)
**Purpose:** Short ETH debt to hedge against market drops. Composite two-part action.

**Macro Entry ($10.90 WETH borrow + $10.80 debt swap)**
- Activates on: >5% collateral drop from baseline + HF >1.52
- Requires: Available capacity >= $13
- Part A Distribution (borrow WETH, distribute):
  - $2.10 WETH → WBTC swap + supply to Aave
  - $2.10 WETH supply to Aave
  - $5.60 WETH → DAI swap (supply $4.50 + transfer $1.10 to WALLET_S)
  - $1.10 WETH → ETH (gas reserve)
- Part B: Swap $10.80 DAI debt → WETH debt via BidirectionalDebtSwapper

**Micro Entry ($7.20 WETH borrow + $10.10 debt swap)**
- Activates on: >2% collateral drop from baseline + HF >1.47
- Requires: Available capacity >= $9
- Part A Distribution:
  - $1.10 WETH → WBTC swap + supply
  - $1.10 WETH supply
  - $3.90 WETH → DAI swap (supply $2.80 + transfer $1.10)
  - $1.10 WETH → ETH (gas reserve)
- Part B: Swap $10.10 DAI debt → WETH debt

**Exit Trigger:** ETH recovers >2% from entry price → WETH→DAI debt swap to lock gains

**Position Tracking:** `debt_swap_positions.json` tracks active/historical positions
**Cooldown:** 600s between debt swap operations

### Health Factor Thresholds
- TARGET_HEALTH_FACTOR = 1.40
- MIN_HEALTH_FACTOR = 1.35 (absolute floor, unified across all checks)
- MACRO_ENTRY = 1.52 (Liability Short macro tier)
- MICRO_ENTRY = 1.47 (Liability Short micro tier)

### Baseline Management
- Initial baseline: $38.00 (post-rebalance)
- Updates only after successful Growth Path completion
- Does NOT update on Capacity Path completion

## Key Files
- `arbitrum_testnet_agent.py` - Main agent class with tri-path execution (Growth/Capacity/Liability Short)
- `liability_short_strategy.py` - Liability Short trigger evaluation, position tracking, ETH price monitoring
- `debt_swap_bidirectional.py` - BidirectionalDebtSwapper for on-chain DAI⇄WETH debt position swaps
- `config_constants.py` - Configuration constants
- `run_autonomous_mainnet.py` - Mainnet autonomous runner (130s cycle)
- `web_dashboard.py` - Web dashboard on port 5000
- `aave_integration.py` - Aave V3 protocol integration (DAI borrow + WETH borrow)
- `uniswap_integration.py` - Uniswap V3 swap integration (DAI/WETH→WBTC/WETH/DAI)
- `aave_health_monitor.py` - Health factor monitoring
- `environmental_configuration.py` - Environment and network config

## Contracts (Arbitrum Mainnet)
- Aave Pool: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- ParaSwap Debt Swap Adapter V3: `0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4`
- DAI: `0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1`
- WETH: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`
- WBTC: `0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f`
- WETH Variable Debt Token: `0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351`

## Workflows
- **Dashboard** (`python web_dashboard.py`) - Web UI on port 5000
- **Autonomous Agent** (`python run_autonomous_mainnet.py`) - 130s monitoring cycle

## Secrets Required
- `COIN_API` - CoinAPI key for market data
- `PRIVATE_KEY` - Wallet private key for transactions
- `WALLET_S_ADDRESS` - Destination for DAI transfers
- `ARBITRUM_RPC_URL` - Arbitrum RPC endpoint

## Recent Changes (Feb 2026)
- Implemented fixed-value dual-path system (Growth: $10.20, Capacity: $5.50)
- Added Global Execution Lock with 130s cooldown
- Unified health factor thresholds (TARGET=1.40, MIN=1.35)
- Added IERC20 approval verification before transactions
- Added DAI transfer to WALLET_S_ADDRESS step
- Removed old ALLOCATION_CONFIG percentage-based system
- Removed manual override and forced execution code
- Removed duplicate method definitions
- Baseline updates only after successful Growth Path cycle
- Added crash-resistant execution_state.json persistence for multi-step transactions
- Startup recovery: agent detects interrupted sequences and resumes from last completed step
- Fixed Uniswap slippage: both swap paths now use 1% (was 5% on second path)
- Cooldown timer in finally block ensures lock releases even on failure

### Feb 8, 2026 - Stability Fixes
- Fixed nonce conflicts: Added 3-retry loop with 1s delay for `nonce too low` errors in uniswap_integration.py
- Fixed dashboard creating full ArbitrumTestnetAgent instances (caused nonce races with main agent). Dashboard now uses read-only WorkingAgent only
- Added DAI balance pre-check before recovery attempts — prevents futile retry loops when wallet has insufficient DAI for remaining steps
- Added `_save_raw_execution_state()` method for preserving recovery metadata (attempt count)
- Block monitor now checks execution_state.json before triggering new executions (prevents double-borrows)
- Recovery auto-clears stale state after 3 failed attempts
- Health factor emergency detection: agent blocks all borrows when HF < 1.35

### Feb 12, 2026 - Liability Short Strategy
- Added `liability_short_strategy.py` with position tracking, dual-tier entry (Macro/Micro), exit trigger
- Added `borrow_weth()` to `aave_integration.py` for WETH borrowing from Aave V3
- Added `swap_weth_for_wbtc()` and `swap_weth_for_dai()` to `uniswap_integration.py`
- Whitelisted WETH→WBTC and WETH→DAI swaps in Uniswap allowlist
- Built `_execute_liability_short_entry()` composite executor (Part A borrow+distribute + Part B debt swap)
- Built `_execute_liability_short_exit()` for WETH→DAI debt swap on ETH recovery
- Wired `_check_liability_short_triggers()` into autonomous monitor (Priority 3, after Growth/Capacity)
- IDLE status now shows Liability Short position state and collateral drop monitoring
- Confirmed correct adapter address: `0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4`
