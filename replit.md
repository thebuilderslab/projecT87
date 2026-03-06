# PROJECT 87

## Overview
PROJECT 87 is a multi-tenant IaaS DeFi platform operating on Arbitrum Mainnet. It enables users to connect their wallets, activate a Sequential Signer, and receive API keys for autonomous DeFi strategy execution. The platform is designed to automate DeFi debt management on Aave V3 and streamline real estate lead generation, featuring a "5-dome Mars Overseer UI" and advanced debt management strategies. The project aims to provide a robust, secure, and user-friendly solution for managing DeFi positions and generating real estate leads, with a focus on autonomous operations and risk minimization.

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

### UI/UX Decisions
The platform features a "5-dome Mars Overseer UI" (Overseer UI v5.2) accessible via `/app`. This dashboard provides a visual representation of DeFi positions and system status. Key UI/UX elements include:
- **Domes:** Always rendered but dimmed until wallet connection, with a full-screen connection modal for activation.
- **Authentication:** Wallet-based authentication using EIP-4361 and `itsdangerous.TimestampSigner` with a 7-day token expiration.
- **Sequential Signer:** A 5-step activation process for new users, including token approvals and credit delegation.
- **Safety Score:** A client-side continuous score (0-4.0) with a server-side qualitative label.

### Technical Implementations & System Design Choices
The system is built on Arbitrum Mainnet, integrating DeFi and real estate modules.

**Core DeFi Debt Management:**
- **Borrowing Strategies:** Implements "Growth" and "Capacity" paths for DAI borrowing across various collateral types, ETH gas management, and a USDC tax accumulator.
- **Liability Short Strategy:** Automated hedging against market downturns by borrowing WETH based on collateral velocity drops.
- **Health Factor Management:** Utilizes conservative health factor thresholds and a "Nurse Mode" (`_perform_safety_sweep()`) to manage account health by sweeping non-USDC collateral to Aave.
- **Execution Control:** Features a global execution lock, state persistence for crash recovery, and "Proportional Recovery."
- **Delegation Architecture:** Supports a direct bot-wallet delegation model where the bot wallet executes `Pool.borrow(onBehalfOf=user)` and manages tokens directly.
- **Token Operations:** Manages token approvals and uses Uniswap V3 for multi-hop swaps.
- **Multi-Tenant Infrastructure:** Designed to handle multiple users with isolated data, API keys, and notifications.
- **Concurrency:** Uses `asyncio.gather()` with `asyncio.Semaphore` for concurrent wallet processing.
- **Transaction Management:** A single `threading.Lock()` and local nonce tracking prevent nonce collisions.
- **Revenue Streams:** Nurse sweep takes 2% of swept tokens; Growth/Capacity distribution keeps 1% of WETH.
- **System Parameters API:** Provides structured JSON of Black Box risk parameters via FastAPI.
- **Content Security Policy (CSP):** Implemented using a FastAPI middleware to generate nonces for script tags, mitigating XSS.

**Macro/Micro Short System:**
- **Purpose:** Automated hedging against collateral velocity drops.
- **Velocity Tracking:** `collateral_snapshots` track collateral over time, and `_compute_velocity_drop()` calculates drops within a configurable window.
- **Triggers:** Macro short triggers on larger collateral drops ($50+ in 5 min) and higher HF; Micro short triggers on smaller drops ($30+ in 5 min) and lower HF with cooldowns.
- **Short Close Logic:** Closes when collateral recovers or hold time expires, involving USDT withdrawal, bot token pulling, WETH repayment, and profit distribution.
- **Simulation Mode:** Supports a simulation mode (`SIMULATION_MODE = True`) for testing without on-chain execution.

**Real Estate Lead Generation:**
- **Data Pipeline:** Scrapes Lis Pendens data, processes with AI, and generates outreach materials.
- **Data Management:** Stores leads in PostgreSQL and integrates with Google Docs/Sheets.

## External Dependencies
- **Aave V3 Protocol:** Core DeFi lending protocol.
- **Uniswap V3:** Decentralized exchange for token swaps.
- **ParaSwap Debt Swap Adapter V3:** Debt swap functionalities.
- **Arbitrum Mainnet:** Primary blockchain network.
- **AaveOracle:** Primary price oracle.
- **CoinMarketCap API:** Fallback price oracle.
- **Required Tokens:** DAI, WETH, WBTC, USDC, USDT.
- **SearchIQS:** Web scraping service for real estate data.
- **Perplexity AI:** AI service (`sonar` model) for analysis and chat.
- **Google Docs/Sheets/Drive API:** For real estate lead management.
- **PostgreSQL Database:** Primary data store for real estate leads and user data.