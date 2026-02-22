# REAA Platform

## Overview
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

**Delegation Architecture:**
- Employs `managed_wallets` and `wallet_actions` tables for tracking delegation status and audit trails via `REAADelegationManager` contract.
- Strict safety rules for auto-supply including `bot_enabled` checks, active delegation, cooldowns, and on-chain balance/allowance verification.
- **Per-Wallet Autonomous Strategy Execution:** `strategy_engine.py` implements per-wallet HF-band strategies (Growth, Capacity, Macro Short, Micro Short, Nurse Mode).
- **Distribution Pipeline Safety:** Prioritizes Resume > Nurse > Strategy with borrow cooldowns, post-borrow HF rechecks, and state preservation on swap failures.

**4-Step Sequential Signer (Wallet Activation):**
- Step 1: Unlimited WBTC approval to DelegationManager (on-chain tx)
- Step 2: DM delegation config with full permissions (on-chain tx)
- Step 3: Gasless EIP-712 credit delegation for DAI + WETH variable debt tokens to **bot wallet** (2 signatures, no gas)
- Step 4: Unlimited USDC approval to DelegationManager (on-chain tx)
- Endpoints (`/api/register-wallet`, `/api/wallet/activation-status`) manage the activation process.
- **Credit delegation targets the bot wallet directly** — bot calls Aave Pool.borrow(onBehalfOf=user) and receives tokens as msg.sender, bypassing DM for borrows and eliminating the need for pull_token_from_user.
- Supply/repay/withdraw operations still route through `delegation_client.py` and the `REAADelegationManager` contract.

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