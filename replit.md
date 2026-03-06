# PROJECT 87 — v5.2

## Overview
PROJECT 87 is a multi-tenant IaaS DeFi platform built on Arbitrum Mainnet. Users connect wallets via EIP-4361, complete the 5-step Sequential Signer activation, and receive API keys for autonomous DeFi strategy execution. The platform features a 5-dome Mars Overseer UI.

**Bot wallet:** `0xbbd55BB128645c16D6DEa9f1866bd9a7e7fC9c48`
**Deployed at:** `bot-thejamalshackle.replit.app`

## Overseer UI (v5.2) — PRIMARY /app ENTRY POINT
- **Route:** `/app` (primary) and `/overseer` (secondary) — both render `templates/overseer.html`
- **UX Architecture:** Domes are always rendered but dimmed (`body.overseer--awaiting-wallet`) until wallet connects. A full-screen connection modal (`#connect-modal`) overlays the domes on load.
- **Modal flow:** Connect wallet → check activation status → Sequential Signer (5-step) if new → "LAUNCH OVERSEER" closes modal, powers on domes
- **Auth bridge:** Inline `<script>` in `overseer.html` handles `connectWallet()`, `runActivationSequence()`, `ejectWallet()`, `hardResetWallet()`, `resignDelegation()`; calls `P87.onWalletConnected()` / `P87.onWalletEjected()` / `P87.powerOn()` to drive overseer state
- **`overseer.js` public API:** `P87.init`, `P87.showModal`, `P87.powerOn`, `P87.onWalletConnected(token, wallet)`, `P87.onWalletEjected()`, `P87._getAuthToken()`
- **`/developer`** redirects to `/app`. `developer_portal.html` is preserved but no longer the primary entry point.
- **Static files:** `static/overseer.css`, `static/overseer.js`
- **API endpoints:** `/api/telemetry` (60s cache), `/api/activity` (15s cache), `/api/telemetry/history`
- **Dome 1:** Safety — HF ring, shield indicator (ACTIVE/AWARE/DOWN), strategy badge
- **Dome 2:** USDC Reactor — fuel tank, AAVE Yield Spread readout (borrow cost / engine yield / NET PROFITABILITY)
- **Dome 3:** Mission Time — T-MINUS countdown, 3 concentric APScheduler arcs, milestones
- **Dome 4:** Strategy Sentiment — likelihood bar, live activity feed with [SHIELD DEPLOYED] tag styling
- **Dome 5:** Operator Bay — ETH fuel gauge, last nurse sweep info
- **T016:** Cross-dome SVG Bezier beams fire on REPAY_EXECUTED, NURSE_SWEEP, milestone crossings, likelihood > 70%

## HF Thresholds (v5.2)
- Emergency: 3.20 | Capacity: 3.40 | Growth: 3.60 | Micro: 4.00 | Macro: 4.05
- SHIELD_WARNING_BAND: 0.30
- Shield status: ACTIVE (HF >= path_min + 0.30), AWARE (HF < path_min + 0.30), DOWN (HF < 3.20)

## APScheduler Jobs
- `core_engine_job`: every 27 min — strategy evaluation, HF logging, shield transitions
- `nurse_sweep_job`: every 70 min — operator token sweep → user Aave supply
- `repay_deleverager_job`: every 4h — USDC→DAI→Aave repay; cap $3.60/day

## Repay Constants
- MAX_REPAY_PER_DAY_USDC=3.60, REPAY_PCT=0.10, REPAY_MIN_AMOUNT=1.10, REPAY_MIN_USDC_BALANCE=12.00

## DB Schema (v5.2 additions)
New tables: `hf_ledger`, `usdc_balance_ledger`, `repay_events`, `distribution_state`,
`wallet_cooldowns`, `hf_repay_deltas`, `usdc_milestones`, `growth_likelihood`
New column: `managed_wallets.shield_status_last`

## Key Files
- `strategy_engine.py` — core strategy logic
- `web_dashboard.py` — Flask app, all routes including /overseer + telemetry APIs
- `db.py` — PostgreSQL helpers
- `scheduler_bootstrap.py` — APScheduler setup with pg advisory locks
- `job_core_engine.py`, `job_nurse_sweep.py`, `job_repay_deleverager.py` — scheduled jobs
- `run_autonomous_mainnet.py` — main bot process (APScheduler keep-alive loop)
- `run_both.py` — production launcher (dashboard + agent)

## REAA Platform (legacy context)
The REAA (Real Estate Agent Assistant) platform is a comprehensive solution designed to empower real estate agents by integrating autonomous DeFi debt management on Aave V3 (Arbitrum Mainnet) with a real estate lead generation system. Its primary purpose is to automate DeFi borrowing strategies and streamline lead generation. Key capabilities include a consumer-facing Command Center dashboard, an AI chat, and advanced debt management strategies like "USDC Tax Mode" and a "Liability Short Strategy." The platform emphasizes robust and secure operations through features such as crash recovery, global execution locks, and a "Nurse Mode" for maintaining health factors.

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
The REAA platform operates on the Arbitrum Mainnet, integrating distinct modules for DeFi debt management and real estate lead generation, all accessible through a web-based Command Center.

**UI/UX Decisions (REAA Command Center):**
- **Dashboard (`/app`):** A multi-user, wallet-connected web dashboard with a "5-Zone Command Center" layout, displaying DeFi positions, an animated avatar with a safety score, and lead pipeline information.
- **AI Assistant:** A Perplexity AI-powered chat assistant provides dynamic context.
- **Authentication:** Wallet-based authentication using `itsdangerous.TimestampSigner` with a 7-day token expiration.
- **Safety Score:** Client-side continuous score (0-4.0) with a server-side qualitative safety label for AI prompt context.
- **Wallet Architecture:** Distinguishes between user's read-only wallet and internal bot wallets (`WALLET_S`, `WALLET_B`).

**Technical Implementations & System Design Choices:**

**DeFi Debt Management:**
- **Borrowing Strategies:** Implements "Growth" and "Capacity" paths for DAI borrowing across various collateral types (WBTC, WETH, USDT), ETH gas, and a USDC tax accumulator.
- **Liability Short Strategy:** Automatically hedges against market downturns by borrowing WETH based on collateral velocity drops.
- **Health Factor Management:** Utilizes conservative health factor thresholds and "Nurse Mode" (`_perform_safety_sweep()`) to proactively manage account health by sweeping non-USDC collateral to Aave.
- **Execution Control:** Features a global execution lock, state persistence for crash recovery, and "Proportional Recovery."
- **Delegation Mode:** Supports full-automation, granting execution permissions to approved wallets.
- **Token Operations:** Manages token approvals and uses Uniswap V3 for multi-hop swaps, with AaveOracle as the primary price source.
- **Profit Accumulation:** USDC profits accumulate in the agent's wallet and transfer to `WALLET_B`.

**Real Estate Lead Generation:**
- **Data Pipeline:** Scrapes Lis Pendens data, processes it with Perplexity AI, and generates outreach materials.
- **Data Management:** Stores leads in PostgreSQL and integrates with Google Docs/Sheets.

**Delegation Architecture (Feb 2026 — Bot-Wallet Direct Model):**
- Credit delegation targets bot wallet directly: user signs EIP-712 delegationWithSig → bot calls Pool.borrow(onBehalfOf=user) → tokens go to bot wallet → bot executes swaps/distributions.
- `validate_full_automation_ready()` checks: DM delegation flags, credit delegation borrowAllowance(user, BOT_WALLET) for DAI/WETH, and bot wallet DEX approvals. Legacy WBTC→DM allowance check removed.
- `ensure_bot_dex_approvals_all_tokens()` bootstraps max-uint Uniswap Router approvals for all 5 tokens on bot wallet before strategy execution.
- Auto-supply runs BEFORE strategy processing in the monitoring loop to ensure collateral is supplied before borrowing decisions.
- `pull_token_from_user` paths (short-close USDT + nurse gas reimbursement) are gated with on-chain allowance checks — skipped gracefully if user hasn't approved tokens to bot.
- `hard_reset_wallet()` performs cascading deletes (wallet_actions, api_keys, notifications, defi_positions, income_events, managed_wallets). All FKs are ON DELETE CASCADE to users(id), no FK constraint issues.
- Borrow cooldown countdown exposed via `/api/wallet/borrow-cooldown` and displayed in developer portal sidebar.
- **Pre-borrow credit delegation guards** in strategy_engine.py: checks `borrowAllowance(user, bot) > 0` for DAI and WETH before borrow calls, skips cleanly with `BORROW_SKIPPED_NO_DELEGATION` or `SHORT_SKIPPED_NO_DELEGATION` if missing.
- **Dual-column delegation signature storage:** DAI sig stored in `delegation_sig`, WETH sig in `delegation_sig_weth` (separate columns prevent overwrite). Submitted flags: `delegation_sig_submitted` and `delegation_sig_weth_submitted`.
- **Immediate on-chain submission:** `/api/register-wallet` stores sigs, resets submitted flags, and calls `submit_delegation_with_sig()` for both DAI+WETH immediately. Background `delegation_sig_processor.py` retries any that fail (max 3 retries).
- **Re-sign flow:** Developer portal checks `borrowAllowance` on-chain via `/api/delegation-status`, shows RE-SIGN button if missing, user re-signs EIP-712 with 30-day deadline, backend verifies + submits + returns borrowAllowance confirmation.
- **Per-Wallet Autonomous Strategy Execution:** `strategy_engine.py` implements per-wallet HF-band strategies (Growth, Capacity, Macro Short, Micro Short, Nurse Mode).
- **Distribution Pipeline Safety:** Prioritizes Resume > Nurse > Strategy with borrow cooldowns, post-borrow HF rechecks, and state preservation on swap failures.

**Macro/Micro Short System (Feb 2026):**
- **Purpose:** Automated hedging against collateral velocity drops (market downturns or manual withdrawals).
- **Data Storage:** Two PostgreSQL tables: `collateral_snapshots` (tracks collateral over time per wallet), `short_positions` (tracks open/closed shorts with entry/close details).
- **Velocity Tracking:** `insert_collateral_snapshot()` runs every monitoring cycle in `run_autonomous_mainnet.py`. `_compute_velocity_drop()` computes max collateral drop within a configurable time window. Stale snapshots pruned hourly (>60 min).
- **Decision Tree Priority:** Resume > Short Close > Emergency > Growth > Capacity > Macro > Micro > Idle. Short close evaluates BEFORE growth/capacity to ensure open positions are managed first.
- **Macro Short Trigger:** Collateral drops >=$50 in 5-min window + HF >= 3.05 + no existing open short. Borrows $15 WETH, splits 40% WBTC / 35% USDT / 25% WETH, all supplied to user's Aave position.
- **Micro Short Trigger:** Collateral drops >=$30 in 5-min window + HF >= 3.00 + no existing open short + 3-min cooldown since last micro close.
- **Short Close Logic:** Closes when collateral recovers to entry level OR hold time exceeds 10 minutes. Flow: withdraw USDT from user's Aave → USDT goes to user wallet (via DelegationManager: Aave→DM→user) → bot pulls USDT from user wallet (requires user USDT→bot approval) → swap USDT→WETH → repay WETH debt → distribute profit 20/20/30/20/10 (Wallet_S DAI / USDC wallet / WBTC Aave / WETH Aave / USDT Aave).
- **USDT Routing Confirmed:** `executeWithdraw()` in DelegationManager does `AavePool.withdraw(asset, amount, address(this))` then `IERC20.transfer(user, amount)`. USDT lands in USER wallet, not bot. Bot must `pull_token_from_user()` to get USDT for swapping.
- **Simulation Settings:** 5-min velocity windows, 3-min micro cooldown, 10-min max short hold, $15 macro / $8 micro short sizes.
- **Simulation Logging:** `📡 [SIM STATUS]` log line shows HF, collateral, velocity drop, snapshot count, open short status, and trigger thresholds every strategy cycle.
- **Short Position State:** Persisted in PostgreSQL via `save_short_position()` / `close_short_position()` / `get_open_short()` / `get_last_closed_short()`. Survives bot restarts.
- **Pre-borrow Guards:** Checks WETH `borrowAllowance(user, bot) > 0` before short entry, skips with `SHORT_SKIPPED_NO_DELEGATION` if missing.
- Bot wallet: 0xbbd55BB128645c16D6DEa9f1866bd9a7e7fC9c48. Variable debt tokens: DAI=0x8619d80F..., WETH=0x0c84331e... on Arbitrum mainnet (chain ID 42161).

**5-Step Sequential Signer (Wallet Activation):**
- Step 1: Unlimited WBTC approval to DelegationManager (on-chain tx)
- Step 2: DM delegation config with full permissions (on-chain tx)
- Step 3: Gasless EIP-712 credit delegation for DAI + WETH variable debt tokens to **bot wallet** (2 signatures, no gas)
- Step 4: Unlimited USDC approval to DelegationManager (on-chain tx)
- Step 5: Unlimited USDT approval to **bot wallet** (on-chain tx) — Required for short close routing where bot pulls USDT from user wallet after Aave withdrawal
- Endpoints (`/api/register-wallet`, `/api/wallet/activation-status`) manage the activation process.
- **Credit delegation targets the bot wallet directly** — bot calls Aave Pool.borrow(onBehalfOf=user) and receives tokens as msg.sender, bypassing DM for borrows and eliminating the need for pull_token_from_user.
- Supply/repay/withdraw operations still route through `delegation_client.py` and the `REAADelegationManager` contract.
- **Existing wallet USDT prompt:** For wallets activated before Step 5, `/api/delegation-status` returns `usdt_allowance_to_bot`, and the portal shows an `[ APPROVE USDT FOR SHORT CLOSE ]` button if missing.
- **SIMULATION_MODE:** `SIMULATION_MODE = True` in `strategy_engine.py` routes short entry/close through mock functions (`_execute_mock_short_entry` / `_execute_mock_short_close`) that log what would happen without executing on-chain transactions. Mock close also checks USDT allowance and reports approval status. Short positions are still persisted in DB for state tracking. Set `SIMULATION_MODE = False` for live trading.

**Multi-Tenant Infrastructure:**
- **API Keys:** `api_keys` table with SHA-256 hashing, 2-key limit, and revocation support.
- **Notifications:** `notifications` table with `wallet_address` for multi-tenant filtering.
- **Strict Multi-Tenant Position Reading:** All balance/health factor functions explicitly require `user_wallet_address`.
- **Concurrent Wallet Processing:** Uses `asyncio.gather()` with `asyncio.Semaphore` for concurrent wallet processing.
- **Transaction Broadcast Lock & Local Nonce Manager:** A single `threading.Lock()` and local nonce tracking prevent nonce collisions.
- **Dual Revenue Streams:** Nurse sweep takes 2% of swept tokens; Growth/Capacity distribution keeps 1% of WETH.
- **ETH Gas Reserve Pipeline:** Manages DAI to ETH conversion for gas.
- **System Parameters API:** Provides structured JSON of Black Box risk parameters.
- **FastAPI + Flask Hybrid Server:** `api_server.py` runs FastAPI on port 5000 with Flask dashboard mounted at root `/`.
- **Black Box Pydantic Schemas:** `BorrowRequest` enforces hardcoded risk rules.

**Data Safety Guarantees:**
- **Filings Data Pipeline:** `replace_filings_for_town()` ensures atomic DELETE+INSERT, preserves existing data on zero results, and manual filings are never overwritten.
- **DeFi Position Integrity:** `upsert_defi_position()` requires a non-empty `wallet_address`.
- **Staleness Visibility:** Dashboard indicates data freshness with color-coded "Last Updated" timestamps.

**Content Security Policy (CSP):**
- Implemented as a defense-in-depth control against XSS, ensuring no attacker-controlled inline JavaScript can execute.
- A FastAPI middleware generates a fresh cryptographic nonce for each request, which is propagated to Flask templates.
- All active templates for `/app` and `/admin` use `nonce="{{ csp_nonce }}"` on their `<script>` tags, and external domains are whitelisted.

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