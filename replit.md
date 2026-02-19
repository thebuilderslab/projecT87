# REAA Platform - Compressed replit.md

## Overview
The REAA (Real Estate Agent Assistant) platform integrates autonomous DeFi debt management on Aave V3 (Arbitrum Mainnet) with a real estate lead generation system. Its primary purpose is to automate DeFi borrowing strategies and facilitate real estate lead generation, offering a comprehensive solution for agents. Key capabilities include a consumer-facing Command Center dashboard for wallet-based interaction, Perplexity-powered AI chat, and sophisticated debt management strategies such as "USDC Tax Mode" for profit accumulation and a "Liability Short Strategy" for market downturns. The system emphasizes robustness with features like crash recovery, global execution locks, and "Nurse Mode" for health factor maintenance.

## User Preferences
I prefer iterative development with clear communication on progress.
I want to be asked before any major architectural changes or external dependency introductions.
I value detailed explanations of complex technical decisions and their implications.
I prefer a coding style that prioritizes readability and maintainability.
I want the agent to use conservative health factor thresholds to minimize risk.
I prefer the system to automatically approve necessary tokens on startup to prevent transaction failures.
I want the agent to prioritize safety and include mechanisms like "Nurse Mode" to protect collateral.
I prefer a user-friendly dashboard that simplifies complex DeFi metrics.
I want the system to be resilient to failures and capable of recovering from interrupted operations.
I want the agent to protect profit tokens (USDC) from being swept by safety mechanisms.
I want the agent to always use its own private key wallet for all operations unless explicitly configured for delegation.

## System Architecture
The REAA platform is built on the Arbitrum Mainnet, featuring distinct modules for DeFi debt management and real estate lead generation, unified by a web-based Command Center.

**DeFi Debt Management:**
- **Borrowing Strategies:** Implements "Growth" and "Capacity" paths for DAI borrowing, distributing funds across various collateral types (WBTC, WETH, USDT), ETH gas, and a USDC tax accumulator.
- **Liability Short Strategy:** Automatically hedges against market downturns by borrowing WETH based on collateral velocity drops, allocating it into a diversified basket, and distributing profits from closing positions.
- **Health Factor Management:** Employs conservative health factor thresholds and a "Nurse Mode" (`_perform_safety_sweep()`) to proactively sweep non-USDC collateral to Aave, ensuring account health.
- **Execution Control:** Features a global execution lock, state persistence for crash recovery, and a "Proportional Recovery" mechanism for handling insufficient funds.
- **Delegation Mode:** Full-automation only. Any wallet that connects, signs, and enables Auto-Pilot receives all execution permissions (supply, borrow, repay, withdraw). No monitoring-only mode exists.
- **Token Operations:** Manages token approvals and uses Uniswap V3 for multi-hop swaps (e.g., DAI→WETH→USDC). AaveOracle is the primary price source.
- **Profit Accumulation:** USDC profit accumulates in the agent's wallet and is periodically transferred to a designated `WALLET_B`.

**Real Estate Lead Generation (Secondary Module):**
- **Data Pipeline:** Scrapes Lis Pendens data from specific Connecticut towns using SearchIQS, processes it with AI (Perplexity AI), and generates outreach materials.
- **Data Management:** Utilizes a PostgreSQL database for lead storage and integrates with Google Docs/Sheets for lead management.

**REAA Command Center (UI/UX):**
- **Dashboard (`/app`):** A multi-user, wallet-connected web dashboard with a "5-Zone Command Center" layout, displaying DeFi positions, an animated avatar with a safety score, and lead pipeline information.
- **AI Assistant:** Features a Perplexity AI-powered chat assistant (REAA) providing dynamic context from the user's Postgres data and DeFi position.
- **Authentication:** Wallet-based authentication using `itsdangerous.TimestampSigner` for secure access to user-specific data and API endpoints, with a 7-day token expiration.
- **Safety Score:** A client-side continuous score (0-4.0) for visual representation of account health, distinct from a server-side qualitative safety label used for AI prompt context.
- **Wallet Architecture:** Distinguishes between the user's connected read-only wallet and internal bot wallets (`WALLET_S`, `WALLET_B`).
- **Data Gating:** Restricts access to sensitive pipeline, filings, and analysis tabs until the user's wallet is connected.

**Phase 2: WBTC Auto-Supply Delegation (Deployed on Arbitrum Mainnet):**
- **Architecture:** Introduces `managed_wallets` and `wallet_actions` tables for tracking delegation status and audit trails. A dedicated `delegation_client.py` module handles interactions with the Delegation Manager contract (`0x7427370Ab4C311B090446544078c819b3946E59d`).
- **Safety Rules:** Strict safety protocols for auto-supply, including `bot_enabled` checks, active delegation status, configurable cooldown, and on-chain balance/allowance verification before execution.
- **Cooldown:** Configurable via `AUTO_SUPPLY_COOLDOWN_SECONDS` env var (default: 3600s = 1 hour for prod, 300s = 5 min for testing). `last_auto_supply_at` starts at NULL (never supplied) and is only updated after a confirmed on-chain supply tx — never on skip or error. NULL always passes the cooldown check (first-run safe).
- **API and UI:** Provides API endpoints for activating/revoking delegation and frontend UX to manage delegation status, displaying relevant information and actions.

**Data Model: State Semantics (defi_positions & supplied_wbtc_amount):**
- **`defi_positions`**: A per-user snapshot of their Aave V3 position, updated by the monitoring loop (`run_autonomous_mainnet.py`) and on-demand via `/api/defi/state`. Fields: `health_factor`, `total_collateral_usd`, `total_debt_usd`, `net_worth_usd`, `has_active_position` (boolean), `updated_at`.
  - **`has_active_position`**: Set to `true` when `total_collateral_usd >= $0.01`. Set to `false` when collateral is below $0.01 (dust threshold). When `false`, the DeFi card shows "No Active Position" instead of stale HF/collateral values.
  - **Dust threshold**: Both `fetch_aave_position_for_wallet` functions (in `web_dashboard.py` and `run_autonomous_mainnet.py`) return `None` when both collateral and debt round to < $0.01 after conversion from on-chain 8-decimal format. This prevents dust amounts (e.g., $0.0000004 from leftover aToken interest) from creating misleading position rows.
  - **Reconciliation on no-position**: When `fetch_aave_position_for_wallet` returns `None`, the monitoring loop calls `mark_position_inactive(user_id)` to zero out the row and `reset_supplied_if_withdrawn(user_id, wallet)` to zero the supply counter.
- **`managed_wallets.supplied_wbtc_amount`**: Tracks the **current** on-chain WBTC supply attributed to auto-supply actions. This is NOT a lifetime counter.
  - **Incremented** when `auto_supply.py` executes a successful supply transaction.
  - **Reset to 0** when the monitoring loop detects the on-chain position is empty (user withdrew manually) via `reset_supplied_if_withdrawn()`.
  - **UI label**: Shown as "Current Supply" in the Auto-Pilot panel. When `has_active_position=false` and `supplied_wbtc_amount > 0`, a reconciliation note is shown: "On-chain position empty — counter resets on next refresh."
- **Edge cases**:
  - User supplies via Aave UI directly (not through auto-supply): `supplied_wbtc_amount` stays 0, but `defi_positions` reflects the on-chain position correctly.
  - User withdraws all collateral: Next monitoring refresh marks position inactive, resets supply counter.
  - Delegation revoked but position exists: Position still monitored (read-only), but no auto-supply actions are taken.

**Phase 2B: Per-Wallet Autonomous Strategy Execution:**
- **Architecture:** `strategy_engine.py` implements per-wallet HF-band strategies via `run_delegated_strategy()`. The monitoring loop (`run_autonomous_mainnet.py`) calls this for each managed wallet with `has_active_position=true` and `delegation_status='active'`.
- **HF Band Priority (highest first):**
  1. **Growth** (HF ≥ 3.10): Borrow $11.40 DAI via delegation contract `executeBorrow`. Requires $13.20 collateral cap + $50 growth since baseline.
  2. **Capacity** (HF ≥ 2.90): Borrow $6.70 DAI. Requires $8.20 collateral cap.
  3. **Macro Short** (HF ≥ 3.05): Triggered by collateral velocity drop ≥ $50 in 30 min. Borrows WETH as hedge.
  4. **Micro Short** (HF ≥ 3.00): Triggered by collateral velocity drop ≥ $30 in 20 min. Borrows WETH as smaller hedge.
  5. **SKIP**: If no band matches, logs explicit reason and takes no action.
- **One mode per wallet per cycle.** No concurrent conflicting actions. `processed_strategy_ids` set prevents double-execution.
- **DB columns on `managed_wallets`:** `last_strategy_action` (TEXT), `last_strategy_at` (TIMESTAMPTZ), `strategy_status` (VARCHAR — active/error_permissions/disabled), `delegation_mode` (VARCHAR — full_automation/NULL), `last_collateral_baseline` (NUMERIC for growth tracking).
- **Single source of truth:** `defi_positions` → `strategy_engine.py` → `delegation_client.py` → on-chain Aave Pool via REAADelegationManager.
- **API:** `/api/user/status` returns `strategyEnabled`, `strategyStatus`, `lastStrategyAction`, `lastStrategyTimestamp`.
- **UI:** Auto-Pilot panel shows Strategy Engine status line, last action text, and timestamp.
- **Delegation routing:** All borrow/repay/withdraw calls go through `delegation_client.py` which signs with bot operator key and calls REAADelegationManager contract methods.
- **Bot wallet separation:** Bot wallet strategies (`run_strategies_for_user`) run on a separate path from delegated wallet strategies.

## External Dependencies

- **Aave V3 Protocol**: Core DeFi lending protocol on Arbitrum Mainnet.
- **Uniswap V3**: Decentralized exchange for token swaps.
- **ParaSwap Debt Swap Adapter V3**: For specific debt swap functionalities.
- **Arbitrum Mainnet**: Primary blockchain network.
- **CoinMarketCap API**: Fallback price oracle.
- **AaveOracle**: Primary price oracle.
- **Required Tokens**: DAI, WETH, WBTC, USDC, USDT, WETH Variable Debt Token (specified by contract addresses).
- **SearchIQS**: Web scraping service for real estate data.
- **Perplexity AI**: AI service (`sonar` model) for analysis and chat functionalities.
- **Google Docs/Sheets/Drive API**: For real estate lead management and data storage.
- **PostgreSQL Database**: Primary data store for real estate leads and user data.

## Delegation & Permissions

### Single Mode: Full Automation
Any wallet that connects, signs, and enables Auto-Pilot is automatically placed in **full-automation mode**. There is no monitoring-only option for users. A wallet is either:
- **Fully delegated** (`isActive=true`, all permission flags ON), or
- **Disabled / Revoked / Misconfigured** (strategies do not execute).

Misconfigurations (e.g., `isActive=true` but a flag is `false`) produce explicit `error_permissions` status — never a silent downgrade.

### On-Chain Contract
- **REAADelegationManager** on Arbitrum Mainnet: `0x7427370Ab4C311B090446544078c819b3946E59d`
- Flags are **wallet-level** (single set per wallet, not per-token):
  - `isActive` — delegation is live
  - `allowSupply` — bot can supply collateral on behalf of user
  - `allowBorrow` — bot can borrow on behalf of user
  - `allowRepay` — bot can repay debt on behalf of user
  - `allowWithdraw` — bot can withdraw collateral on behalf of user

### Token Permission Matrix (Full Parity)
Defined in `permissions.py`. All tokens the system may touch:

| Token | Address (Arbitrum) | Strategies | Actions |
|-------|--------------------|------------|---------|
| WBTC | `0x2f2a...5B0f` | auto_supply, growth/capacity swap+supply, short entry, nurse | supply |
| DAI | `0xDA10...0da1` | growth, capacity, nurse, wallet_s transfer, usdc_tax swap | borrow, supply, repay |
| WETH | `0x82aF...Bab1` | macro/micro short, growth/capacity swap+supply, nurse | borrow, supply, repay |
| USDT | `0xFd08...Cbb9` | short entry swap+supply, short close withdraw, nurse | supply, withdraw |
| USDC | `0xaf88...5831` | (profit token — user claims) | read-only, NEVER swept |

### Required User Approvals
Users must grant infinite ERC20 approvals for **all 5 tokens** to exactly **3 contracts**:
1. **DelegationManager** (`0x7427...59d`) — for transferFrom pulls
2. **Aave Pool** (`0x794a...1aD`) — for supply/borrow/repay/withdraw
3. **Uniswap Router** (`0xE592...564`) — for token swaps

Missing approvals = structured error, no partial execution.

### Full Automation Profile
All flags = `true` for any delegated wallet. Defined in `permissions.FULL_AUTOMATION`:
```
isActive=true, allowSupply=true, allowBorrow=true, allowRepay=true, allowWithdraw=true
```

### Strategy Responsibilities (Full 6-Step Engine)
1. **Growth** (HF >= 3.10): Full 6-step distribution — borrow $11.40 DAI, supply DAI to Aave, swap+supply WBTC, swap+supply WETH, ETH gas reserve, Wallet_S transfer, USDC tax.
2. **Capacity** (HF >= 2.90): Same 6-step engine with $6.70 DAI borrow.
3. **Macro Short** (HF >= 3.05): Borrow WETH, split 40% WBTC / 35% USDT / 25% WETH collateral.
4. **Micro Short** (HF >= 3.00): Same as macro with smaller size, 4h cooldown.
5. **Nurse Mode**: Sweep idle DAI/WETH/WBTC/USDT to Aave. $2 floor. NEVER touches USDC.
6. **Auto Supply**: Supply WBTC to Aave on delegation activation.
7. **Emergency** (HF < 2.50): Alert only — no automated action.

Skips are based only on HF/risk rules or strategy constraints — never on missing permissions.

### Profit Flow Comparison: Personal Bot vs User Wallet

**These are the ONLY two intentional behavior differences.** All other execution logic is identical.

#### Difference 1: Profit Bucket
```
PERSONAL BOT:
  USDC accumulates in bot wallet from Growth/Capacity tax steps
  When balance >= $22 → auto-flush ALL USDC to Wallet_B
  This is the "Profit Bucket" mechanism

USER WALLET:
  USDC from Growth/Capacity tax steps stays in user wallet permanently
  NO auto-flush. NO Profit Bucket. User claims manually via Dashboard.
  Bot NEVER touches user's USDC.
```

#### Difference 2: Liability Short Close Profit Distribution
```
PERSONAL BOT (20/20/60 split):
  On profitable short close:
  ├── 20% → Wallet_S (USDT → WETH → DAI → transfer)
  ├── 20% → Wallet_B (USDT → USDC → accumulator)
  └── 60% → Aave collateral (USDT → supply)

USER WALLET (100% to user):
  On profitable short close:
  └── 100% → Remaining profit stays in user wallet
      (No split. No transfers to Wallet_S or Wallet_B.
       Any leftover WETH/USDT sent back to user wallet.)
```

#### Everything Else: IDENTICAL
- Growth 6-step distribution (same $ amounts, same step order)
- Capacity 6-step distribution (same $ amounts, same step order)
- Liability Short entry (same WETH borrow, same 40/35/25 allocation)
- Nurse Mode sweep (same $2 floor, same tokens, same USDC protection)
- HF thresholds (same 3.10/2.90/3.05/3.00/2.50 bands)
- Emergency alerts (same behavior)
- Approval requirements (same 5 tokens × 3 contracts)

### Revocation Flow
When a user revokes delegation:
- **On-chain:** User signs `revokeDelegation()` transaction via frontend, clearing `isActive` and all flags.
- **Backend:** Sets `delegation_status='revoked'`, `strategy_status='disabled'`, `delegation_mode=NULL`, `auto_supply_wbtc=false`, `bot_enabled=false`.
- **Effect:** Wallet is excluded from `get_active_managed_wallets()` query. Strategy engine will not attempt any actions.

### Security Notes
- All on-chain calls route through `delegation_client.py`, signed by bot operator key via REAADelegationManager.
- Permission validation via `permissions.validate_full_automation()` checks all 5 flags before any strategy runs.
- Structured logging captures: delegation setup per wallet, each strategy action vs SKIP with reason codes, permission errors.
- New tokens or strategies must update `permissions.py` (TOKEN_PERMISSIONS and STRATEGY_MAP).