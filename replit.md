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
- **Delegation Mode:** Supports managing Aave operations on behalf of a target wallet, with an upcoming WBTC auto-supply delegation feature.
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

**Phase 2: WBTC Auto-Supply Delegation (Future/Planned):**
- **Architecture:** Introduces `managed_wallets` and `wallet_actions` tables for tracking delegation status and audit trails. A dedicated `delegation_client.py` module handles interactions with the Delegation Manager contract.
- **Safety Rules:** Strict safety protocols for auto-supply, including `bot_enabled` checks, active delegation status, daily guards, and on-chain balance/allowance verification before execution.
- **API and UI:** Provides API endpoints for activating/revoking delegation and frontend UX to manage delegation status, displaying relevant information and actions.

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