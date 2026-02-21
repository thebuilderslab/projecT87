# REAA Platform

## Overview
The REAA (Real Estate Agent Assistant) platform offers a comprehensive solution for real estate agents by integrating autonomous DeFi debt management on Aave V3 (Arbitrum Mainnet) with a real estate lead generation system. Its core purpose is to automate DeFi borrowing strategies and facilitate lead generation. Key features include a consumer-facing Command Center dashboard, AI chat powered by Perplexity, and advanced debt management strategies like "USDC Tax Mode" and a "Liability Short Strategy." The system is designed for robustness, incorporating crash recovery, global execution locks, and a "Nurse Mode" for maintaining health factors.

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
The REAA platform operates on the Arbitrum Mainnet, comprising distinct modules for DeFi debt management and real estate lead generation, all accessed via a web-based Command Center.

**DeFi Debt Management:**
- **Borrowing Strategies:** Features "Growth" and "Capacity" paths for DAI borrowing, distributing funds across various collateral types (WBTC, WETH, USDT), ETH gas, and a USDC tax accumulator.
- **Liability Short Strategy:** Automatically hedges against market downturns by borrowing WETH based on collateral velocity drops, diversifying it, and distributing profits from closing positions.
- **Health Factor Management:** Utilizes conservative health factor thresholds and "Nurse Mode" (`_perform_safety_sweep()`) to proactively manage account health by sweeping non-USDC collateral to Aave.
- **Execution Control:** Includes a global execution lock, state persistence for crash recovery, and "Proportional Recovery" for handling insufficient funds.
- **Delegation Mode:** Supports full-automation only, granting execution permissions (supply, borrow, repay, withdraw) to wallets that connect, sign, and enable Auto-Pilot.
- **Token Operations:** Manages token approvals and employs Uniswap V3 for multi-hop swaps. AaveOracle serves as the primary price source.
- **Profit Accumulation:** USDC profits accrue in the agent's wallet and are transferred to a designated `WALLET_B`.

**Real Estate Lead Generation (Secondary Module):**
- **Data Pipeline:** Scrapes Lis Pendens data from specific Connecticut towns using SearchIQS, processes it with Perplexity AI, and generates outreach materials.
- **Data Management:** Stores leads in a PostgreSQL database and integrates with Google Docs/Sheets for management.

**REAA Command Center (UI/UX):**
- **Dashboard (`/app`):** A multi-user, wallet-connected web dashboard with a "5-Zone Command Center" layout, displaying DeFi positions, an animated avatar with a safety score, and lead pipeline information.
- **AI Assistant:** A Perplexity AI-powered chat assistant (REAA) provides dynamic context from user data and DeFi positions.
- **Authentication:** Wallet-based authentication uses `itsdangerous.TimestampSigner` for secure access, with a 7-day token expiration.
- **Safety Score:** A client-side continuous score (0-4.0) visually represents account health, complementing a server-side qualitative safety label for AI prompt context.
- **Wallet Architecture:** Differentiates between the user's connected read-only wallet and internal bot wallets (`WALLET_S`, `WALLET_B`).
- **Data Gating:** Restricts access to sensitive tabs until the user's wallet is connected.

**Delegation Architecture (WBTC Auto-Supply & Strategy Execution):**
- **Architecture:** Employs `managed_wallets` and `wallet_actions` tables for tracking delegation status and audit trails. `delegation_client.py` interacts with the `REAADelegationManager` contract.
- **Safety Rules:** Strict protocols for auto-supply, including `bot_enabled` checks, active delegation, configurable cooldowns, and on-chain balance/allowance verification.
- **API and UI:** Provides endpoints for activating/revoking delegation and a frontend to manage status.
- **Three Permission Layers for Full Automation:**
  1. **DelegationManager Contract Flags:** User sets `setPermissions` (supply, borrow, repay, withdraw).
  2. **ERC20 Token Approvals:** User approves 15 tokens (5 assets × 3 contracts: Aave Pool, DelegationManager, Uniswap Router).
  3. **Aave V3 Credit Delegation:** User approves `variableDebtToken.approveDelegation` for DAI and WETH.
- **Validation:** `validate_full_automation_ready()` checks all three layers, returning `{ready, blockers}`.
- **State Semantics (`defi_positions` & `supplied_wbtc_amount`):** `defi_positions` provides a per-user Aave V3 position snapshot, updated by a monitoring loop. `supplied_wbtc_amount` tracks current on-chain WBTC supply from auto-supply actions.
- **Per-Wallet Autonomous Strategy Execution:** `strategy_engine.py` implements per-wallet HF-band strategies (Growth, Capacity, Macro Short, Micro Short, Nurse Mode) executed by the monitoring loop for active, delegated wallets. Delegated HF thresholds: Growth 2.60, Capacity 2.40, Emergency 2.20.
- **Distribution Pipeline Safety:** Execution order is Resume > Nurse > Strategy. `resume_incomplete_distribution()` detects incomplete distributions via state file OR orphaned DAI (DAI balance ≥$5 + DAI-specific debt ≥$1). Nurse Mode skips wallets with active distributions and never sweeps DAI when user has DAI debt. `auto_supply.py` also guards against active distributions. Execution state persists for 24 hours to survive restarts. **Borrow Cooldown (30 min):** Per-wallet timestamp prevents cascading borrows. **Post-Borrow HF Recheck:** After every borrow, HF is re-fetched; if below EMERGENCY threshold, distribution aborts immediately (state preserved for recovery). **State Preservation on Swap Failure:** If borrow succeeded but ≥3 swap steps failed with 0 successes, execution state is preserved (not cleared) so resume detects it next cycle instead of triggering orphaned DAI + a fresh borrow.
- **Token Routing:** All borrow/repay/withdraw calls route through `delegation_client.py` and the `REAADelegationManager` contract. Distribution token flow is user-custodial, employing `pull_token_from_user` and `_forward_tokens_to_user` for swap safety.
- **Full Automation Permission Parity:** Frontend ensures `approveDelegation` is called to set all 4 flags, and users sign 15 ERC20 approvals for full execution parity. `validate_full_automation_ready` checks all permissions.
- **Revocation Flow:** User signs `revokeDelegation()` on-chain, and backend updates `delegation_status` to 'revoked', disabling further strategy execution.

**OpenClaw Multi-Tenant Infrastructure (Feb 2026):**
- **API Keys:** `api_keys` table with SHA-256 hashing, 2-key limit per user, revocation support. Helper functions: `create_api_key()`, `verify_api_key()`, `revoke_api_key()`, `get_user_api_keys()`.
- **Notifications:** `notifications` table with per-user notification CRUD: `create_notification()`, `get_user_notifications()`, `mark_notification_read()`, `mark_all_notifications_read()`.
- **Strict Multi-Tenant Position Reading:** `get_eth_balance()`, `get_dai_balance()`, `get_usdt_balance()`, `get_health_factor()`, `_get_usdc_balance()`, `get_aave_position()` all REQUIRE `user_wallet_address` (no default). Passing None raises `ValueError("user_wallet_address explicitly required for multi-tenant execution")`. Separate `get_bot_*` methods (`get_bot_eth_balance()`, `get_bot_dai_balance()`, `get_bot_usdt_balance()`, `get_bot_health_factor()`, `get_bot_aave_position()`, `_get_bot_usdc_balance()`) are used for bot-operator-self operations.
- **Concurrent Wallet Processing:** `run_autonomous_mainnet.py` uses native `asyncio.gather()` with `asyncio.Semaphore(5)` for concurrent wallet processing (max `MAX_CONCURRENT_WALLETS=5`). Each wallet runs via `asyncio.to_thread()` to offload blocking Web3 RPC calls. `RPC_DELAY_SECONDS=0.5` between wallet starts prevents HTTP 429 bans. No threading primitives (ThreadPoolExecutor, threading.Lock, threading.Semaphore) — pure asyncio architecture.
- **Dual Revenue Streams:** (1) Nurse sweep takes 2% of each swept token (above $5 minimum) via `pull_token_from_user()` to reimburse bot operator for gas costs. (2) Growth/Capacity distribution keeps 1% of WETH from DAI->WETH gas swap in bot wallet (no extra transaction). Min $1.50 DAI to execute gas swap (below that, DAI stays in user wallet).
- **ETH Gas Reserve Pipeline:** DAI pulled from user -> swap DAI->WETH via Uniswap -> 1% WETH stays in bot wallet (skim) -> 99% WETH unwrapped to ETH -> ETH sent to user (with 0.5% send buffer for dust). Rollback: if swap fails, DAI forwarded back to user.
- **System Parameters API:** `GET /api/v1/system/parameters` returns all Black Box risk parameters as structured JSON. Source: `strategy_engine.get_system_parameters()`.

**Black Box Risk Parameters (hardcoded, not user-configurable):**
- **HF Thresholds:** Emergency < 2.20, Capacity >= 2.40, Growth >= 2.60, Micro Short >= 3.00, Macro Short >= 3.05.
- **Growth Trigger:** HF >= 2.60 AND available_borrows >= $13.20 AND (collateral_growth >= $50 OR >= 10%). Borrows $11.40 DAI. Distribution: $2.75 USDT, $2.80 WBTC, $2.45 WETH (all supplied to Aave), $1.10 ETH gas, $1.10 Wallet_S, $1.20 USDC tax.
- **Capacity Trigger:** HF >= 2.40 AND available_borrows >= $8.20. Borrows $6.70 DAI. Distribution: $1.10 each (USDT/WBTC/WETH/ETH gas/Wallet_S) + $1.20 USDC tax.
- **Macro Short:** Collateral drops >= $50 in 30 min AND HF >= 3.05. Borrows $15.00 WETH, splits 40% WBTC / 35% USDT / 25% WETH.
- **Micro Short:** Collateral drops >= $30 in 20 min AND HF >= 3.00. Borrows $8.00 WETH, same 40/35/25 split. 4-hour cooldown.
- **Nurse Mode:** $2.00 hard floor. Sweeps DAI/WETH/WBTC/USDT to Aave. USDC never swept (profit token). DAI skipped if user has >= $1 DAI debt. 2% gas reimbursement on tokens >= $5. Skipped during active distributions.
- **Execution Controls:** 30-min borrow cooldown. 24-hour execution state TTL. Post-borrow HF recheck (aborts if < 2.20). Resume priority runs before all strategies.
- **Distribution Step Order:** borrowed -> usdt_supplied -> wbtc_supplied -> weth_supplied -> eth_converted -> wallet_s_transferred -> usdc_taxed.
- **Priority Order:** Resume (any HF) > Nurse (any HF) > Emergency (< 2.20) > Growth (>= 2.60) > Capacity (>= 2.40) > Macro (>= 3.05) > Micro (>= 3.00) > Idle.

## Wallet Connection & USDC Meter

**Wallet connection flow:**
- `connectWallet()` gets the wallet address from MetaMask (or manual entry fallback).
- `authenticateWallet(address)` calls `POST /api/auth/wallet`, awaits the auth response, stores `authToken`, `userId`, and `walletAddress` in both `state` and `localStorage`.
- Only after auth succeeds, all dashboard data loaders run via `await Promise.all([loadDefiPanel(), loadIncomeSummary(), loadTowns(), loadDelegationStatus(), loadUsdcBalance()])`.
- On page reload, saved credentials in `localStorage` are restored and the same loaders fire.
- On 401 from any authenticated API call, `fullDisconnect()` fires once, wiping all user-specific state (`walletAddress`, `authToken`, `userId`, `towns`, `defiPosition`, `delegationContractAddress`, etc.) and clearing `localStorage`/`sessionStorage`.

**USDC meter:**
- Endpoint: `GET /api/wallet/usdc-balance` (authenticated, returns `{balance, wallet, target}`).
- Reads on-chain USDC balance at Arbitrum address `0xaf88d065e77c8cC2239327C5EDb3A432268e5831` for the connected user's wallet.
- `target` is a configurable goal (default $5,000).
- Command Center meter displays `USDC → WALLET $X.XX / $Y.YY` with a gradient progress bar.
- Active Wealth panel displays `USDC Wallet: $X.XX` as a text row.

**WBTC delegation UI location:**
- The WBTC Auto-Supply Delegation panel lives in the DeFi tab (`#tab-defi`), inside `#defiConnectedContent`, below the HF Thresholds section.

## Data Safety Guarantees

**Filings (Lis Pendens) Data Pipeline:**
- **Flow:** SearchIQS scrape → `replace_filings_for_town()` → `filings` table → `/api/filings/recent` → "New Opportunities" panel.
- `replace_filings_for_town(town_id, filings_list)` is the primary ingest function. It wraps DELETE+INSERT in a single Postgres transaction (atomic).
- If `filings_list` is empty (scraper returns 0 results due to network error, etc.), the function **preserves existing rows** — no delete occurs.
- This prevents historical data loss from transient scraper failures.
- **Only `source='searchiqs'` rows are replaced** on scrape — manual filings (`source='manual'`) are always preserved.
- **Source tagging:** Every filing has a `source` column (`'searchiqs'` or `'manual'`). Manual inserts are clearly tagged and never overwritten by automated scrapes.
- **Scrape status tracking:** Each town in the `towns` table has `last_scrape_status` (OK | ZERO_RESULTS | HTTP_403 | ERROR) and `last_scrape_at` (timestamp). Updated after every scrape run.
- **UI freshness:** The "New Opportunities" panel shows orange warning banners for towns with error scrape statuses, so users can see when data may be stale.
- **API:** `GET /api/filings/recent?days=7&limit=20` returns filings, counts, and per-town scrape status in `towns[]` array.

**DeFi Position Integrity:**
- `upsert_defi_position()` requires a non-empty `wallet_address` parameter — calls without it are rejected with a logged error.
- All call sites (`_refresh_defi`, `get_defi_state`, `refresh_defi_for_user`) pass the wallet address explicitly.
- NULL wallet_address rows were cleaned up (Feb 2026); the guard prevents recurrence.

**Staleness Visibility:**
- Active Wealth panel shows "Last Updated: Xm ago" with color coding (grey = fresh, orange = >30 min stale).
- `defi_positions.updated_at` is returned in `/api/defi/state` response and rendered client-side.

## External Dependencies

- **Aave V3 Protocol**: Core DeFi lending protocol.
- **Uniswap V3**: Decentralized exchange for token swaps.
- **ParaSwap Debt Swap Adapter V3**: For specific debt swap functionalities.
- **Arbitrum Mainnet**: Primary blockchain network.
- **AaveOracle**: Primary price oracle.
- **CoinMarketCap API**: Fallback price oracle.
- **Required Tokens**: DAI, WETH, WBTC, USDC, USDT.
- **SearchIQS**: Web scraping service for real estate data.
- **Perplexity AI**: AI service (`sonar` model) for analysis and chat.
- **Google Docs/Sheets/Drive API**: For real estate lead management.
- **PostgreSQL Database**: Primary data store for real estate leads and user data.