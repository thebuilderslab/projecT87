# Jovan Bot - Aave V3 Autonomous Debt Management System

## Project Overview
Autonomous Aave V3 debt management system on Arbitrum Mainnet with two distinct execution paths. Monitors collateral growth from a $47 baseline and executes fixed-value borrowing operations.

## Current Status: **USDC Tax Mode — Pay Yourself First → WALLET_B** (Feb 2026)

## Architecture

### USDC Tax Mode (formerly GHO Accumulation)
Conservative HF thresholds with $1.20 USDC Tax on every borrow. Each execution path borrows an extra $1.20 DAI, swaps it to USDC via Uniswap single-hop, then sends the USDC to WALLET_B_ADDRESS (stored in Replit secrets). USDC is whitelisted — Nurse Mode and restore_health.py never sweep it.

**HF Thresholds (Conservative):**
- Growth min: 3.10
- Macro (Liability Short): 3.05
- Micro (Liability Short): 3.00
- Capacity/Emergency: 2.90
- Monitoring cycle: 45s

### Dual-Path Execution System

**Growth Path ($11.40 borrow = $10.20 + $1.20 USDC Tax)** - PRIORITY 1
- Activates on: 10% relative OR $50 absolute collateral growth from baseline
- Requires: Health factor >= 3.10, Available capacity >= $13.20
- Distribution:
  - $3.00 DAI supply to Aave
  - $3.00 DAI -> WBTC swap + supply to Aave
  - $2.00 DAI -> WETH swap + supply to Aave
  - $1.10 DAI -> ETH (gas reserve, held in wallet)
  - $1.10 DAI transfer to WALLET_S_ADDRESS
  - $1.20 DAI -> USDC swap -> sent to WALLET_B_ADDRESS

**Capacity Path ($6.70 borrow = $5.50 + $1.20 USDC Tax)** - PRIORITY 2
- Activates when: Available capacity >= $8.20
- Requires: Health factor >= 2.90
- Distribution:
  - $1.10 DAI supply to Aave
  - $1.10 DAI -> WBTC swap + supply to Aave
  - $1.10 DAI -> WETH swap + supply to Aave
  - $1.10 DAI -> ETH (gas reserve, held in wallet)
  - $1.10 DAI transfer to WALLET_S_ADDRESS
  - $1.20 DAI -> USDC swap -> sent to WALLET_B_ADDRESS

### USDC Tax & WALLET_B Transfer
- USDC_TAX_AMOUNT = $1.20 per borrow
- USDC_HARVEST_TARGET = $22.00 (dashboard tracks cumulative USDC sent)
- USDC address: 0xaf88d065e77c8cC2239327C5EDb3A432268e5831 (native USDC, 6 decimals)
- DAI→USDC swap: Uniswap V3 multi-hop (DAI→WETH→USDC, forced route — no direct DAI/USDC liquidity on Arbitrum)
- WETH→USDC swap: Uniswap V3 for Liability Short path
- After swap, USDC is immediately transferred to WALLET_B_ADDRESS
- USDC is WHITELISTED in Nurse Mode (_perform_safety_sweep) and restore_health.py
- Dashboard Zone 4 shows USDC balance + WALLET_B address + manual "SEND USDC" button
- API endpoint: POST /api/send-usdc-to-wallet-b

### Force-Approve All Tokens (Startup)
- On every agent startup, `_force_approve_all_tokens()` checks allowances for 4 tokens (DAI, WETH, WBTC, USDC) against 2 spenders (Aave Pool, Uniswap Router)
- Sets infinite approval (2^256-1) for any token below threshold
- Prevents UNPREDICTABLE_GAS_LIMIT errors during swaps/supplies
- Idempotent: 2nd boot skips all if approvals already set

### Nurse Mode Triage ($2.00 Hard Floor)
- `_perform_safety_sweep()` sweeps COLLATERAL ONLY (DAI, WETH, WBTC) to Aave
- $2.00 USD hard floor: any token with value < $2.00 is skipped (stops burning gas on dust)
- USDC is NEVER swept — profit token, user claims via Dashboard manual "SEND USDC" button
- Uses live AaveOracle prices for WETH/WBTC USD valuation (with fallbacks)
- DAI reserved for USDC tax is protected and not swept

### AaveOracle Integration
- Primary price source: AaveOracle at 0xb56c2F0B653B2e0b10C9b928C8580Ac5Df02C7C7
- getAssetPrice() returns 8-decimal USD prices
- Fallback: CoinMarketCap API

### Global Execution Lock
- `is_transacting` flag prevents double-borrowing against same collateral jump
- 130s cooldown between operations (`operation_cooldown_seconds`)
- Lock set on entry to `_execute_fixed_distribution()`, cleared on exit
- Lock stays active while `execution_state.json` has incomplete steps

### Crash Recovery (execution_state.json)
- After each successful on-chain step, state is persisted to `execution_state.json`
- Steps tracked: borrowed → dai_supplied → wbtc_supplied → weth_supplied → eth_converted → wallet_s_transferred → usdc_taxed
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

**Macro Entry ($12.10 WETH borrow = $10.90 + $1.20 USDC Tax + $10.80 debt swap)**
- Activates on: >5% collateral drop from baseline + HF >3.05
- Requires: Available capacity >= $13
- Part A Distribution (borrow WETH, distribute):
  - $2.10 WETH → WBTC swap + supply to Aave
  - $2.10 WETH supply to Aave
  - $5.60 WETH → DAI swap (supply $4.50 + transfer $1.10 to WALLET_S)
  - $1.10 WETH → ETH (gas reserve)
  - $1.20 WETH → USDC swap → sent to WALLET_B_ADDRESS
- Part B: Swap $10.80 DAI debt → WETH debt via BidirectionalDebtSwapper

**Micro Entry ($8.40 WETH borrow = $7.20 + $1.20 USDC Tax + $10.10 debt swap)**
- Activates on: >2% collateral drop from baseline + HF >3.00
- Requires: Available capacity >= $9
- Part A Distribution:
  - $1.10 WETH → WBTC swap + supply
  - $1.10 WETH supply
  - $3.90 WETH → DAI swap (supply $2.80 + transfer $1.10)
  - $1.10 WETH → ETH (gas reserve)
  - $1.20 WETH → USDC swap → sent to WALLET_B_ADDRESS
- Part B: Swap $10.10 DAI debt → WETH debt

**Exit Trigger:** ETH recovers >2% from entry price → WETH→DAI debt swap to lock gains

**Position Tracking:** `debt_swap_positions.json` tracks active/historical positions
**Cooldown:** 600s between debt swap operations

### Health Factor Thresholds (Conservative USDC Mode)
- MIN_HEALTH_FACTOR_GROWTH = 3.10
- MIN_HEALTH_FACTOR_MACRO = 3.05
- MIN_HEALTH_FACTOR_MICRO = 3.00
- MIN_HEALTH_FACTOR_CAPACITY = 2.90 (absolute floor)
- All borrow methods enforce floor 2.90

### Delegation Mode (Operate on Behalf of User Wallet)
- **Self-Trade Mode** (default): Bot uses its own private key wallet for all operations
- **Delegation Mode**: Set `TARGET_WALLET_ADDRESS` env var to a user's wallet address
  - Bot monitors that wallet's HF/collateral instead of its own
  - Borrows use `on_behalf_of` parameter against user's collateral
  - Supplies go into user's Aave position
  - User must call `approveBorrowAllowance(bot_address, amount)` on Aave V3 variable debt tokens for DAI and WETH
  - `check_delegation_allowance()` verifies allowance before every delegated borrow — prevents gas waste
  - `get_user_account_data(target=wallet)` reads any wallet's HF/collateral
  - Startup banner shows operation mode and target wallet

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

## Web Dashboard — 5-Zone Command Center
- Psychology-first UI with anxiety-reducing terminology
- Zone 1: Safety Rating (circular SVG gauge with traffic light glow)
- Zone 2: Active Wealth (net value, collateral, debt breakdown)
- Zone 3: Defensive Guardrails (Micro/Macro trigger targets from Liability Short)
- Zone 4: Engine Room (cooldown timers, capacity meter)
- Zone 5: Intelligence Feed (color-coded log with jargon translation)
- Traffic light system: green (HF>3.10), amber (2.90-3.10), pulsing red (<2.90)
- API: `/api/command-center` consolidates all zone data, refreshes every 5s
- Agent writes `system_status.json` each cycle with HF, triggers, cooldowns
- Jargon translation: swap→Rebalancing Assets, borrow→Expanding Position, repay→Reducing Risk

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

### Feb 14, 2026 - Phase 3: Universal USDC Tax + Delegation Mode
- **Universal USDC Tax**: All 4 strategies now collect USDC. Macro borrows $12.10 ($10.90+$1.20), Micro $8.40 ($7.20+$1.20)
- DAI→USDC swap via Uniswap V3 single-hop (fee tiers: 100bp, 500bp, 3000bp)
- WETH→USDC swap for Liability Short paths
- USDC automatically sent to WALLET_B_ADDRESS after every tax swap
- **Delegation Mode**: `get_target_wallet()` and `get_delegation_mode()` in config_constants.py
- `check_delegation_allowance()` reads Aave V3 variable debt token borrowAllowance before delegated borrows
- `borrow_dai()`, `borrow_weth()`, `supply_to_aave()` all accept `on_behalf_of` parameter
- `get_user_account_data(target=wallet)` queries any wallet's Aave position
- Allowance guard prevents gas waste: delegated borrows abort if allowance insufficient
- Pre-flight audit in run_autonomous_mainnet.py shows operation mode and all 4 strategy borrow amounts
- Fixed stale HF floor (1.35 → 2.90) in all borrow methods

### Feb 16, 2026 - Router Fix + HF Threshold Update
- **Uniswap Router**: Switched from SwapRouter02 (0x68b346...) to original SwapRouter (0xE59242...) — STF errors on all swaps
- **ABI Update**: Added `deadline` field to exactInputSingle and exactInput structs (required by original SwapRouter)
- **DAI→USDC**: Forced multi-hop route DAI→WETH→USDC via exactInput (no direct DAI/USDC liquidity on Arbitrum)
- **HF Threshold**: capacity_health_factor_threshold restored to 2.90 (self.capacity_health_factor_threshold at line 610)
- **Balance Check**: Fixed stale balance comparison after Nurse Mode sweep — now rechecks if delta looks low
- **STF Root Cause**: Missing `'from': self.address` in all Uniswap `build_transaction()` calls — estimate_gas simulated from null address, failing transferFrom
- **STF Fix**: Added `'from': self.address` to all 4 build_transaction calls in uniswap_integration.py (exactInputSingle, 2x exactInput, approve)
- **Result**: All swaps now working — DAI→USDC, DAI→WBTC, DAI→WETH confirmed on-chain. Full capacity path completed successfully.
