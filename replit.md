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

## System Architecture

### Core Functionality
The bot operates with a dual-path execution system: a "Growth Path" for expanding positions upon significant collateral growth, and a "Capacity Path" for utilizing available borrowing capacity. Both paths include a "$1.20 USDC Tax" where DAI is borrowed, swapped to USDC, and transferred to a separate wallet (WALLET_B_ADDRESS). This USDC is whitelisted, meaning it's never swept by health-preserving functions like "Nurse Mode."

### Health Factor Management
Conservative Health Factor (HF) thresholds are maintained for different operations:
- Growth min: 3.10
- Macro (Liability Short): 3.05
- Micro (Liability Short): 3.00
- Capacity/Emergency: 2.90
A "Nurse Mode" (`_perform_safety_sweep()`) sweeps collateral (DAI, WETH, WBTC) to Aave when necessary, with a $2.00 USD hard floor to prevent gas waste on dust amounts. USDC is explicitly excluded from sweeping.

### Liability Short Strategy
This strategy aims to hedge against market downturns by shorting ETH debt. It has two entry points (Macro and Micro) based on collateral drop and health factor. It involves borrowing WETH, distributing it, and then swapping DAI debt for WETH debt using a `BidirectionalDebtSwapper`. An exit trigger is defined for when ETH recovers.

### Execution Control and Recovery
A global execution lock (`is_transacting`) with a 130s cooldown prevents double-borrowing. For robustness, the system uses `execution_state.json` to persist state after each on-chain step, enabling crash recovery. Upon startup, the agent checks for interrupted sequences and resumes from the last incomplete step. A "Proportional Recovery" mechanism handles scenarios where insufficient DAI remains for all steps, scaling down operations and prioritizing critical transfers. Steps are executed non-blockingly, allowing subsequent steps to proceed even if a swap fails.

### Delegation Mode
The system supports a "Delegation Mode" where it can operate on behalf of a user's wallet (TARGET_WALLET_ADDRESS). In this mode, the bot monitors the user's HF/collateral and executes borrows/supplies using the `on_behalf_of` parameter. It includes checks for delegation allowance to prevent gas waste.

### UI/UX and Monitoring
A web-based dashboard on port 5000 provides a "5-Zone Command Center" with a psychology-first UI. It displays safety ratings, active wealth, defensive guardrails (Liability Short targets), engine room metrics (cooldowns, capacity), and an "Intelligence Feed" with jargon translation. A traffic light system visually indicates health factor status. The dashboard's API (`/api/command-center`) refreshes data every 5 seconds.

### Technical Implementations
- **Token Approvals**: On startup, `_force_approve_all_tokens()` checks and sets infinite approvals for DAI, WETH, WBTC, and USDC with Aave Pool and Uniswap Router to prevent transaction failures.
- **Price Oracles**: Primary price source is AaveOracle, with CoinMarketCap API as a fallback.
- **Swap Routing**: Uniswap V3 is used for swaps. Specifically, DAI→USDC swaps are forced through a DAI→WETH→USDC multi-hop route due to lack of direct liquidity.
- **Profit Accumulation**: USDC collected via the tax accumulates in the agent's wallet until a $22 target is reached, then it is automatically flushed to WALLET_B. A `yield_history.json` tracks payouts.

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
  - DAI: `0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1`
  - WETH: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`
  - WBTC: `0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f`
  - WETH Variable Debt Token: `0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351`