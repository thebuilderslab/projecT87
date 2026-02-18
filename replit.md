# Jovan Bot - Aave V3 Autonomous Debt Management System

## Overview
The Jovan Bot is an autonomous debt management system for Aave V3 on the Arbitrum Mainnet. Its primary purpose is to monitor collateral growth and execute fixed-value borrowing operations across distinct execution paths. It includes a "USDC Tax Mode" for profit accumulation and a "Liability Short Strategy" to hedge against market downturns. The system is designed for robustness with crash recovery, global execution locks, and a "Nurse Mode" for health factor management. The project also features a web-based "5-Zone Command Center" dashboard for monitoring and interaction, as well as an automated Lis Pendens scraping pipeline for real estate lead generation, integrated with Google Docs/Sheets and a Postgres database for lead management.

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
The system operates on the Arbitrum Mainnet and is designed around two primary functions: DeFi debt management and real estate lead generation.

**DeFi Debt Management:**
- **Borrowing Paths:** Two fixed-value DAI borrowing paths ("Growth" and "Capacity") distribute borrowed DAI into various collateral assets (WBTC, WETH, USDT), ETH gas reserves, and a USDC tax accumulator.
- **Liability Short Strategy:**
    - Triggers: "Macro Short" ($10.90 WETH borrow) and "Micro Short" ($7.20 WETH borrow) based on collateral velocity drops ($50 in 30 mins, $30 in 20 mins respectively).
    - Allocation: Borrowed WETH is allocated into a 40/35/25 basket of WBTC, USDT, and WETH collateral.
    - Closing: Profits from short positions (USDT) are distributed as 20% to Wallet S (Savings, converted to DAI), 20% to Wallet B (Yield, as USDC), and 60% re-supplied as USDT collateral. Integer math is enforced for all distributions.
- **Health Factor Management:** Conservative HF thresholds (e.g., Growth min: 3.10, Capacity: 2.90) are maintained. "Nurse Mode" (`_perform_safety_sweep()`) sweeps collateral (excluding USDC) to Aave to maintain HF.
- **Execution Control:** A global execution lock and state persistence (`execution_state.json`) ensure crash recovery and prevent double-spending. A "Proportional Recovery" mechanism handles insufficient funds.
- **Delegation Mode:** Supports operating on behalf of a `TARGET_WALLET_ADDRESS` by monitoring and executing Aave operations.
- **Token Handling:** Infinite approvals for critical tokens (DAI, WETH, WBTC, USDC, USDT) are set on startup. DAI to Aave supplies are always converted via DAI→WETH→USDT.
- **Price Oracles:** AaveOracle is the primary source, with CoinMarketCap as a fallback.
- **Swap Routing:** Uniswap V3 is used for swaps. DAI→USDC uses a DAI→WETH→USDC multi-hop route.
- **Profit Accumulation:** USDC from the tax accumulates in the agent's wallet and is automatically flushed to `WALLET_B` upon reaching a $22 target, tracked in `yield_history.json`.

**Real Estate Lead Generation (Secondary Module):**
- **Pipeline:** Scrapes Lis Pendens data from 5 Connecticut towns (Hartford, East Hartford, Windsor, Berlin, Rocky Hill) using SearchIQS.
- **Scheduling:** Daily pipeline execution for scraping, AI analysis (Perplexity AI), document generation, and outreach letter creation.
- **Data Management:** Leads are stored in a Postgres database (8 tables) with Google Docs/Sheets integration for lead management.
- **Consumer Dashboard:** A multi-user, wallet-connected web dashboard (`/app`) provides a "5-Zone Command Center" UI.
    - Layout: 3-column grid displaying DeFi/Aave position, an animated avatar with a safety score and health ring, and lead pipeline town cards.
    - Features: Safety score calculation, Perplexity AI-powered chat assistant with dynamic context from user's Postgres data, and various API endpoints for data retrieval and interaction.
    - Wallet Architecture: User's connected wallet is for read-only monitoring; `WALLET_S` and `WALLET_B` are internal bot wallets.

## External Dependencies

- **Aave V3 Protocol**: Core DeFi lending protocol.
    - Aave Pool: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- **Uniswap V3**: Decentralized exchange for token swaps.
- **ParaSwap Debt Swap Adapter V3**: For bidirectional DAI⇄WETH debt swaps.
    - ParaSwap Debt Swap Adapter: `0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4`
- **Arbitrum Mainnet**: Blockchain network.
    - Arbitrum RPC URL (configured via `ARBITRUM_RPC_URL` secret)
- **CoinMarketCap API**: Fallback price oracle (`COIN_API` secret).
- **AaveOracle**: Primary price oracle.
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
- **SearchIQS**: Web scraping service for real estate data.
- **Perplexity AI**: AI service for analysis and chat (model: `sonar`).
- **Google Docs/Sheets/Drive API**: For real estate lead management and data storage.
    - Service account: `lead-doc-writer@site-link-485518.iam.gserviceaccount.com`
    - Specific document IDs configured via environment variables (e.g., `HARTFORD_ANALYSIS_DOC_ID`, `RAW_DATA_SHEET_ID`).
- **PostgreSQL Database**: Primary data store for real estate leads and user data.