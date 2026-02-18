# Jovan Bot - Aave V3 Autonomous Debt Management System

## Overview
The Jovan Bot is an autonomous debt management system for Aave V3 on the Arbitrum Mainnet. Its primary purpose is to monitor collateral growth from a baseline and execute fixed-value borrowing operations across two distinct execution paths. It also incorporates a "USDC Tax Mode" where a portion of each borrow is converted to USDC and sent to a designated wallet, effectively acting as a profit accumulation mechanism. The system is designed for robustness with features like crash recovery, global execution locks, and a proactive "Nurse Mode" for health factor management. A key feature is the "Liability Short Strategy" to hedge against market downturns. The project aims to provide a reliable and efficient decentralized finance (DeFi) automation solution.

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

## System Architecture — Canonical Spec

### Phase 1: Growth Path ($11.40 DAI Borrow)

**Debt token:** DAI (18 decimals)
**Total borrow:** $11.40
**Min capacity required:** $13.20
**HF threshold:** > 3.10

**Distribution:**
- $2.80 → Swap DAI→WBTC → Supply WBTC to Aave
- $2.45 → Swap DAI→WETH → Supply WETH to Aave
- $2.75 → Convert DAI→WETH→USDT → Supply USDT to Aave
- $1.10 → ETH gas reserve (DAI→ETH conversion)
- $1.10 → DAI transfer to Wallet S
- $1.20 → USDC Tax → Wallet B accumulator

### Phase 1: Capacity Path ($6.70 DAI Borrow)

**Debt token:** DAI (18 decimals)
**Total borrow:** $6.70
**Min capacity required:** $8.20
**HF threshold:** > 2.90

**Distribution (equal $1.10 splits):**
- $1.10 → Swap DAI→WBTC → Supply WBTC to Aave
- $1.10 → Swap DAI→WETH → Supply WETH to Aave
- $1.10 → Convert DAI→WETH→USDT → Supply USDT to Aave
- $1.10 → ETH gas reserve (DAI→ETH conversion)
- $1.10 → DAI transfer to Wallet S
- $1.20 → USDC Tax → Wallet B accumulator

### Phase 2: Macro Short Entry ($10.90 WETH Borrow)

**Debt token:** WETH (18 decimals)
**Borrow notional:** $10.90 WETH
**HF threshold:** > 3.05
**Trigger:** Collateral velocity — $50 drop in 30 minutes (12h cooldown)

**Entry allocation from borrowed WETH (40/35/25 basket):**
- 40% ($4.36) → Swap WETH→WBTC → Supply WBTC to Aave as collateral
- 35% ($3.82) → Swap WETH→USDT → Supply USDT to Aave as collateral
- 25% ($2.73) → Retain WETH → Supply WETH directly to Aave as collateral

**No USDC on entry.**

### Phase 2: Micro Short Entry ($7.20 WETH Borrow)

**Debt token:** WETH (18 decimals)
**Borrow notional:** $7.20 WETH
**HF threshold:** > 3.00
**Trigger:** Collateral velocity — $30 drop in 20 minutes (4h cooldown)

**Entry allocation from borrowed WETH (40/35/25 basket):**
- 40% ($2.88) → Swap WETH→WBTC → Supply WBTC to Aave as collateral
- 35% ($2.52) → Swap WETH→USDT → Supply USDT to Aave as collateral
- 25% ($1.80) → Retain WETH → Supply WETH directly to Aave as collateral

**No USDC on entry.**

### Collateral Velocity Monitor (Panic Detection)
Rolling 40-minute buffer of total collateral values, sampled every ~60 seconds.
- **drop_20m** = Value_20_mins_ago - Current_Value
- **drop_30m** = Value_30_mins_ago - Current_Value
- Micro Panic: drop_20m >= $30 → Micro Short ($7.20), 4h cooldown
- Macro Panic: drop_30m >= $50 → Macro Short ($10.90), 12h cooldown
- Replaces old static percentage-based collateral drop triggers.

### Short Close — 20/20/60 Profit Distribution (Mandatory)

**Close flow:**
1. Withdraw USDT from Aave
2. Swap USDT→WETH to repay the WETH debt
3. Remaining USDT after debt repayment = `remaining_usdt_balance`

**Distribution (integer math enforced):**
- **20% Wallet S (Savings):**
  - `wallet_s_amount = int(remaining_usdt_balance * 0.20 * 1e6) / 1e6`
  - Route: USDT → WETH → DAI
  - Final action: Transfer DAI to WALLET_S
- **20% Wallet B (Yield):**
  - `wallet_b_amount = int(remaining_usdt_balance * 0.20 * 1e6) / 1e6`
  - Route: USDT → USDC (direct swap preferred, USDT → WETH → USDC as fallback)
  - Final action: USDC stays in Wallet B accumulator
- **60% Collateral (Growth):**
  - `collateral_amount = int(remaining_usdt_balance * 0.60 * 1e6) / 1e6`
  - Action: Supply remaining USDT back to Aave as USDT collateral

**Integer math:** Every percentage-based calculation is cast to `int()` before being used in any Web3 call. USDT uses 6 decimals, DAI uses 18 decimals.

### DAI→USDT Conversion Rule
ALL DAI supplies to Aave MUST convert through DAI→WETH→USDT route before supplying USDT to Aave. The `_resupply_dai_to_aave()` method handles this conversion automatically. No raw DAI should ever be supplied directly to Aave. This applies to:
- Nurse Mode sweeps
- Capacity Path fallbacks
- Dust guards
- Recovery paths
- Any `_resupply_dai_to_aave()` call site

### Health Factor Management
Conservative Health Factor (HF) thresholds are maintained for different operations:
- Growth min: 3.10
- Macro (Liability Short): 3.05
- Micro (Liability Short): 3.00
- Capacity/Emergency: 2.90
A "Nurse Mode" (`_perform_safety_sweep()`) sweeps collateral (DAI, WETH, WBTC, USDT) to Aave when necessary, with a $2.00 USD hard floor to prevent gas waste on dust amounts. USDC is explicitly excluded from sweeping.

### Execution Control and Recovery
A global execution lock (`is_transacting`) with a 130s cooldown prevents double-borrowing. For robustness, the system uses `execution_state.json` to persist state after each on-chain step, enabling crash recovery. Upon startup, the agent checks for interrupted sequences and resumes from the last incomplete step. A "Proportional Recovery" mechanism handles scenarios where insufficient DAI remains for all steps, scaling down operations and prioritizing critical transfers. Steps are executed non-blockingly, allowing subsequent steps to proceed even if a swap fails.

### Delegation Mode
The system supports a "Delegation Mode" where it can operate on behalf of a user's wallet (TARGET_WALLET_ADDRESS). In this mode, the bot monitors the user's HF/collateral and executes borrows/supplies using the `on_behalf_of` parameter. It includes checks for delegation allowance to prevent gas waste.

### UI/UX and Monitoring
A web-based dashboard on port 5000 provides a "5-Zone Command Center" with a psychology-first UI. It displays safety ratings, active wealth, defensive guardrails (Liability Short targets), engine room metrics (cooldowns, capacity), and an "Intelligence Feed" with jargon translation. A traffic light system visually indicates health factor status. The dashboard's API (`/api/command-center`) refreshes data every 5 seconds. Dashboard does NOT display Wallet S balances or distributions (internal only).

### Technical Implementations
- **Token Approvals**: On startup, `_force_approve_all_tokens()` checks and sets infinite approvals for DAI, WETH, WBTC, USDC, and USDT with Aave Pool and Uniswap Router to prevent transaction failures.
- **Price Oracles**: Primary price source is AaveOracle, with CoinMarketCap API as a fallback.
- **Swap Routing**: Uniswap V3 is used for swaps. Specifically, DAI→USDC swaps are forced through a DAI→WETH→USDC multi-hop route due to lack of direct liquidity. USDT→USDC uses direct swap with multi-hop fallback.
- **Profit Accumulation**: USDC collected via the tax accumulates in the agent's wallet until a $22 target is reached, then it is automatically flushed to WALLET_B. A `yield_history.json` tracks payouts.
- **Allowed Swap Pairs**: DAI→WBTC, DAI→WETH, DAI→ARB, ARB→DAI, DAI→USDC, DAI→USDT, WETH→WBTC, WETH→DAI, WETH→USDC, WETH→USDT, USDT→WETH, USDT→USDC

## External Dependencies

- **Aave V3 Protocol**: Core DeFi lending protocol for borrowing and supplying assets.
  - Aave Pool: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- **Uniswap V3**: Decentralized exchange for token swaps.
  - Uniswap Router: `0xE59242...` (original SwapRouter)
- **ParaSwap Debt Swap Adapter V3**: For bidirectional DAI⇄WETH debt position swaps.
  - ParaSwap Debt Swap Adapter: `0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4`
- **Arbitrum Mainnet**: The blockchain network where the system operates.
  - Arbitrum RPC URL (configured via `ARBITRUM_RPC_URL` secret)
- **CoinMarketCap API**: Fallback price oracle for asset valuation (requires `COIN_API` secret).
- **AaveOracle**: Primary price oracle for Aave V3.
  - AaveOracle: `0xb56c2F0B653B2e0b10C9b928C8580Ac5Df02C7C7`
- **Wallet B Address**: External wallet for USDC tax accumulation (`WALLET_B_ADDRESS` secret).
- **Wallet S Address**: External wallet for DAI transfers (`WALLET_S_ADDRESS` secret).
- **Required Tokens**:
  - DAI: `0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1` (18 decimals)
  - WETH: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1` (18 decimals)
  - WBTC: `0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f` (8 decimals)
  - USDC: `0xaf88d065e77c8cC2239327C5EDb3A432268e5831` (6 decimals)
  - USDT: `0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9` (6 decimals)
  - WETH Variable Debt Token: `0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351`

## Real Estate Pipeline (Zone 6)

### Overview
Automated Lis Pendens scraping pipeline for 5 Connecticut towns in Hartford County, with Google Docs/Sheets integration for lead management.

### Towns Scraped
- Hartford (CTHAR) - requires DocGroup postback to "LR" before search
- East Hartford (CTEHART)
- Windsor (CTWSR)
- Berlin (CTBER)
- Rocky Hill (CTROCK)

### Pipeline Schedule (Eastern Time)
- 7:00 AM - SearchIQS scraping (all 5 towns, 30-day lookback)
- 7:30 AM - Perplexity AI analysis of filings
- 8:00 AM - Review document generation
- 8:30 AM - Outreach letter creation

### Google Integration
- Service account: `lead-doc-writer@site-link-485518.iam.gserviceaccount.com`
- Leads folder: `128JqjJpDrSkV9ZyylFIICT-MJK5tBxOg`
- Raw data sheet: `1mxQKY-AgXPXoJyFJBJHFUat-PwxYXzy4XVqqGZPPn0o` (Bailey Group Leads)
- Hartford analysis doc: `1TVvVZevNXYZv2Ziw2rxvSIWzTTzwRBQmw4VGZidRJQY`
- **Limitation**: Service account has 0 storage quota on personal Gmail - cannot create new files, only reuse existing shared ones
- Per-town analysis doc IDs can be set via env vars: `HARTFORD_ANALYSIS_DOC_ID`, `EAST_HARTFORD_ANALYSIS_DOC_ID`, `WINDSOR_ANALYSIS_DOC_ID`, `BERLIN_ANALYSIS_DOC_ID`, `ROCKY_HILL_ANALYSIS_DOC_ID`
- Raw data sheet ID: `RAW_DATA_SHEET_ID` env var
- LOGIC doc ID: `LOGIC_DOC_ID` env var

### Court Case Lookups
- Disabled by default (CT courts site has SSL issues)
- Enable via `COURT_LOOKUP_ENABLED=true` env var

### Key Files
- `searchiqs_scraper.py` - SearchIQS web scraper with multi-town support
- `google_client.py` - Google Docs/Sheets/Drive API client with JWT auth
- `real_estate_tasks.py` - Pipeline orchestration and scheduling
- `perplexity_client.py` - AI analysis via Perplexity API
- `config.py` - All configuration including town codes and thresholds
- `db.py` - Postgres database layer (8 tables, all CRUD functions)
- `templates/consumer_dashboard.html` - Consumer-facing SPA at /app

### Database (Postgres)
8 tables: users, towns, user_towns, filings, defi_positions, income_events, lead_notes, pipeline_runs. Schema uses serial PKs, FKs with cascade, unique constraints, JSONB for raw_data/details, and indexes on filings(town_id, recording_date, status). Wallet addresses normalized to lowercase. Clear-and-rewrite pattern per town to avoid duplicates.

### Consumer App (/app)
Multi-user wallet-connected dashboard at /app with:
- Wallet auth (POST /api/auth/wallet)
- Tab navigation: Overview, Filings, Analysis, DeFi
- Town cards with filing counts
- In-app filing tables with filters (town, date range, status)
- CSV/XLSX export (GET /api/export/filings?format=csv|xlsx)
- Pipeline status and lead summary cards
- Notes system for filings (POST/GET /api/leads/notes)

### API Endpoints (15 new)
- POST /api/auth/wallet - Wallet auth (upsert user)
- GET /api/towns - Towns with filing counts
- POST /api/user/towns - Save user town selections
- GET /api/filings - Paginated filings with filters
- GET /api/filings/stats - Per-town filing stats
- GET /api/export/filings - CSV/XLSX download
- GET /api/defi/state - DeFi position data
- GET /api/pipeline/status - Latest run + town stats
- GET /api/leads/summary - Lead counts
- POST /api/leads/notes - Create note on filing
- GET /api/leads/notes - Get notes for filing
- GET /api/income/summary - Income events summary

### Recent Changes (Feb 18, 2026)
- Migrated from Google Docs/Sheets storage to Postgres database
- Built 15 new API endpoints for consumer app
- Created consumer SPA at /app with wallet connect, tabs, filing tables, export
- Scraper pipeline now writes to Postgres alongside Google Docs path
- 35 filings loaded: Hartford 16, East Hartford 11, Windsor 7, Berlin 1, Rocky Hill 0
- End-to-end tests pass for all flows

### Recent Changes (Feb 17, 2026)
- Fixed Hartford scraper: 2-step DocGroup postback to "LR" before search
- Made form fields adaptive per town (cboTown vs txtExtraField1)
- Added pre-configured doc ID support in config to bypass storage quota limit
- Court lookups disabled by default due to SSL failures
- Pipeline saves state to `real_estate_state.json`
