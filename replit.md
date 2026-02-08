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

### Health Factor Thresholds
- TARGET_HEALTH_FACTOR = 1.40
- MIN_HEALTH_FACTOR = 1.35 (unified across all checks)

### Baseline Management
- Initial baseline: $47.00
- Updates only after successful Growth Path completion
- Does NOT update on Capacity Path completion

## Key Files
- `arbitrum_testnet_agent.py` - Main agent class with dual-path execution
- `config_constants.py` - Configuration constants
- `run_autonomous_mainnet.py` - Mainnet autonomous runner (130s cycle)
- `web_dashboard.py` - Web dashboard on port 5000
- `aave_integration.py` - Aave V3 protocol integration
- `uniswap_integration.py` - Uniswap V3 swap integration
- `aave_health_monitor.py` - Health factor monitoring
- `environmental_configuration.py` - Environment and network config

## Contracts (Arbitrum Mainnet)
- Aave Pool: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- DAI: `0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1`
- WETH: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`
- WBTC: `0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f`

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
