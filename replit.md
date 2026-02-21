# REAA Platform

## Overview
The REAA (Real Estate Agent Assistant) platform is a comprehensive solution designed to empower real estate agents. It integrates autonomous DeFi debt management on Aave V3 (Arbitrum Mainnet) with a real estate lead generation system. The platform aims to automate DeFi borrowing strategies and streamline lead generation processes. Key capabilities include a consumer-facing Command Center dashboard, an AI chat powered by Perplexity for dynamic context, and advanced debt management strategies such as "USDC Tax Mode" and a "Liability Short Strategy." The system emphasizes robustness with features like crash recovery, global execution locks, and a "Nurse Mode" for maintaining health factors, ensuring secure and efficient operations.

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
- **Dashboard (`/app`):** A multi-user, wallet-connected web dashboard featuring a "5-Zone Command Center" layout. It displays DeFi positions, an animated avatar with a safety score, and lead pipeline information.
- **AI Assistant:** A Perplexity AI-powered chat assistant provides dynamic context from user data and DeFi positions.
- **Authentication:** Wallet-based authentication uses `itsdangerous.TimestampSigner` for secure access with a 7-day token expiration.
- **Safety Score:** A client-side continuous score (0-4.0) visually represents account health, complemented by a server-side qualitative safety label for AI prompt context.
- **Wallet Architecture:** Differentiates between the user's connected read-only wallet and internal bot wallets (`WALLET_S`, `WALLET_B`).
- **Data Gating:** Restricts access to sensitive tabs until the user's wallet is connected.

**Technical Implementations & System Design Choices:**

**DeFi Debt Management:**
- **Borrowing Strategies:** Implements "Growth" and "Capacity" paths for DAI borrowing, distributing funds across various collateral types (WBTC, WETH, USDT), ETH gas, and a USDC tax accumulator.
- **Liability Short Strategy:** Automatically hedges against market downturns by borrowing WETH based on collateral velocity drops, diversifying it, and managing profit distribution from closing positions.
- **Health Factor Management:** Utilizes conservative health factor thresholds and "Nurse Mode" (`_perform_safety_sweep()`) to proactively manage account health by sweeping non-USDC collateral to Aave.
- **Execution Control:** Features a global execution lock, state persistence for crash recovery, and "Proportional Recovery" for handling insufficient funds.
- **Delegation Mode:** Supports full-automation, granting execution permissions (supply, borrow, repay, withdraw) to connected and approved wallets.
- **Token Operations:** Manages token approvals and utilizes Uniswap V3 for multi-hop swaps, with AaveOracle as the primary price source.
- **Profit Accumulation:** USDC profits accumulate in the agent's wallet and are transferred to a designated `WALLET_B`.

**Real Estate Lead Generation:**
- **Data Pipeline:** Scrapes Lis Pendens data from specific Connecticut towns using SearchIQS, processes it with Perplexity AI, and generates outreach materials.
- **Data Management:** Stores leads in a PostgreSQL database and integrates with Google Docs/Sheets for management.

**Delegation Architecture (WBTC Auto-Supply & Strategy Execution):**
- Employs `managed_wallets` and `wallet_actions` tables for tracking delegation status and audit trails. Interactions occur via `REAADelegationManager` contract.
- Strict safety rules for auto-supply, including `bot_enabled` checks, active delegation, configurable cooldowns, and on-chain balance/allowance verification.
- **Permission Layers:** Requires `DelegationManager` contract flags, ERC20 token approvals for 15 tokens, and Aave V3 Credit Delegation approvals.
- **Per-Wallet Autonomous Strategy Execution:** `strategy_engine.py` implements per-wallet HF-band strategies (Growth, Capacity, Macro Short, Micro Short, Nurse Mode) executed by a monitoring loop for active, delegated wallets.
- **Distribution Pipeline Safety:** Prioritizes Resume > Nurse > Strategy. Includes borrow cooldowns, post-borrow HF rechecks, and state preservation on swap failures.
- **Token Routing:** All borrow/repay/withdraw calls route through `delegation_client.py` and the `REAADelegationManager` contract.
- **Revocation Flow:** User signs `revokeDelegation()` on-chain, and the backend updates `delegation_status` to 'revoked'.

**Multi-Tenant Infrastructure:**
- **API Keys:** `api_keys` table with SHA-256 hashing, 2-key limit per user, and revocation support.
- **Notifications:** `notifications` table with `wallet_address` for multi-tenant filtering, supporting global and per-wallet notifications.
- **Strict Multi-Tenant Position Reading:** All balance/health factor functions explicitly require `user_wallet_address` to prevent data leakage.
- **Concurrent Wallet Processing:** Uses `asyncio.gather()` with `asyncio.Semaphore` for concurrent wallet processing, offloading blocking Web3 RPC calls.
- **Transaction Broadcast Lock & Local Nonce Manager:** A single `threading.Lock()` and local nonce tracking prevent nonce collisions during concurrent bot operations.
- **Dual Revenue Streams:** Nurse sweep takes 2% of swept tokens for gas reimbursement; Growth/Capacity distribution keeps 1% of WETH from DAI->WETH gas swap.
- **ETH Gas Reserve Pipeline:** Manages DAI to ETH conversion for gas, including a skim and rollback mechanism.
- **System Parameters API:** Provides structured JSON of Black Box risk parameters.
- **FastAPI + Flask Hybrid Server:** `api_server.py` runs FastAPI on port 5000, with Flask dashboard mounted at root `/`.
- **Black Box Pydantic Schemas:** `BorrowRequest` only accepts `amount` and `asset`, enforcing hardcoded risk rules.
- **Event Loop Safety:** Synchronous Web3/strategy code in FastAPI endpoints runs in a background threadpool.

**Data Safety Guarantees:**
- **Filings Data Pipeline:** `replace_filings_for_town()` ensures atomic DELETE+INSERT. If scrape returns zero results, existing data is preserved. Manual filings (`source='manual'`) are never overwritten. Scrape status is tracked per town.
- **DeFi Position Integrity:** `upsert_defi_position()` requires a non-empty `wallet_address` to prevent data corruption.
- **Staleness Visibility:** Dashboard indicates data freshness with color-coded "Last Updated" timestamps.

## Content Security Policy (CSP)

### Security property

On the hardened routes (`/app` and `/admin`), the intended security property is:

> No attacker-controlled inline JavaScript can execute in the browser. Only scripts that are:
> 1) delivered by our servers from trusted origins, and
> 2) explicitly tagged with the per-request CSP nonce
> are allowed to run.

CSP is used as a defense-in-depth control against XSS and other content injection attacks, complementing input validation and output encoding.

### Implementation overview

- A FastAPI middleware generates a fresh cryptographic nonce for every HTTP request, attaches it to the response CSP header, and exposes it to downstream components.
- A custom WSGI bridge injects this nonce into the Flask request environment without shared mutable state, so each request gets its own nonce.
- A Flask context processor reads the nonce from the environment and exposes it to templates as `{{ csp_nonce }}`.
- All active templates for `/app` and `/admin` use `nonce="{{ csp_nonce }}"` on their `<script>` tags, and there are no remaining inline event handlers (`onclick`, etc.) on these routes.
- All HTML responses for `/app` and `/admin` send a CSP header whose `script-src` includes the per-request nonce and only the minimum required external script/connect/style sources.

### Verification status

The CSP behavior was verified with runtime checks:

1. **Per-request nonce consistency**
   - For `/app`, `/admin`, and `/reaa`, multiple test requests were captured.
   - Within each individual response, the nonce in the CSP header matched the nonce on all `<script nonce="…">` tags, and each request used a distinct nonce value.

2. **Cross-layer propagation (FastAPI → WSGI → Flask)**
   - Logging at three points (middleware generation, WSGI environ injection, Flask context processor) confirmed the same nonce is used end-to-end for a given request, and different requests produce different nonces.

3. **Route coverage**
   - All active HTML routes (`/app`, `/admin`, `/reaa`) and the `/` redirect (which lands on `/app`) send a CSP header with a per-request nonce.
   - 404 pages also emit a CSP header.

4. **External domains allowed**
   - Network traces during normal flows show external requests to:
     - `fonts.googleapis.com` and `fonts.gstatic.com` (Google Fonts), covered by `style-src` / `font-src`.
     - `*.arbitrum.io` (Arbitrum RPC), covered by `connect-src`.
     - Links to `arbiscan.io` are plain anchors, not script or XHR endpoints, so no CSP change is required.
   - As of this writing, WalletConnect is not fully exercised in automated tests; the CSP is configured to allow the expected WalletConnect endpoints (for example `wss://relay.walletconnect.com`, `https://explorer-api.walletconnect.com`, `https://verify.walletconnect.com`), but this has not yet been validated against a full live WalletConnect flow.

### Known limitations and open items

- **Legacy `/reaa` dashboard inline handlers (open vulnerability)**
  - The legacy consumer dashboard at `/reaa` still contains ~30 inline `onclick` handlers in its template. Under a nonce-based CSP, inline event handlers are blocked unless weakened by `unsafe-inline`, which is intentionally avoided because it significantly reduces XSS protection.
  - As long as `/reaa` is reachable and these handlers remain, this route does not fully satisfy the security property above. An attacker who can introduce HTML/attribute injection on `/reaa` may be able to execute code via those handlers.
  - **Planned remediation:** refactor `/reaa` to move inline handlers into nonced scripts using `addEventListener` or similar, or decommission the route if it is no longer needed.

- **WalletConnect validation status**
  - CSP directives include allowances for expected WalletConnect domains, but there is no end-to-end automated test yet that runs a full WalletConnect connection and signing flow under CSP.
  - **Planned remediation:** add an integration test that drives a WalletConnect session in a real browser (or headless) and confirms no CSP violations occur during connect, sign, and disconnect phases.

### Summary

- `/app` and `/admin` currently meet the stated CSP security property: no inline handlers, all executing scripts are explicitly nonced, and external domains are restricted to what the app requires.
- `/reaa` is explicitly tracked as an exception with known inline handlers and is slated for refactoring or removal.
- WalletConnect is configured but not yet fully validated by automated CSP-aware tests; this is documented as an open task.

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