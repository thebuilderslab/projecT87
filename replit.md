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