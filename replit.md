# Overview

This is an autonomous arbitrage trading system for Aave debt position management on Arbitrum. The system implements sophisticated debt swapping strategies between DAI and ARB tokens, leveraging Aave V3's debt swap adapter for direct position management. It features real-time market analysis, health factor monitoring, emergency safeguards, and automated execution capabilities designed for mainnet production deployment.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Components

The system is built around several key architectural components:

**Agent Framework**: The `ArbitrumTestnetAgent` serves as the central coordinator, managing wallet interactions, network connections, and DeFi protocol integrations. Despite its name, it operates on both testnet and mainnet environments.

**Debt Swap Engine**: The `AaveDebtSwapAdapter` provides direct integration with Aave V3's ParaSwapDebtSwapAdapter, enabling atomic swapping of debt positions without requiring intermediate token holdings. This eliminates the need for users to hold specific tokens for debt management.

**Market Analysis**: The system includes trend analyzers and market signal processors that monitor BTC and ARB price movements to inform trading decisions. Market signals trigger automated debt position adjustments based on configurable thresholds.

**Health Monitoring**: The `AaveHealthMonitor` continuously tracks position health factors and implements liquidation protection mechanisms. It maintains historical data for trend analysis and provides alerts when positions approach risk thresholds.

**Execution Management**: The `ProductionDebtSwapExecutor` handles the complex orchestration of debt swaps, including pre-flight validation, transaction construction, gas estimation, and post-execution verification.

## Data Storage

**Configuration Management**: Agent parameters, learning rates, and optimization targets are stored in JSON configuration files that persist across sessions.

**State Persistence**: Active swap cycles are tracked in `active_swaps.json`, maintaining detailed records of ongoing arbitrage positions including entry prices, amounts, and cycle status.

**Diagnostic Logging**: Comprehensive failure analysis is captured in timestamped JSON files, providing detailed debugging information for transaction failures and system issues.

**Baseline Tracking**: The system maintains baseline collateral values in `agent_baseline.json` for performance comparison and drift detection.

## Network Architecture

**Multi-RPC Resilience**: The system implements automatic failover across multiple Arbitrum RPC endpoints, including public and premium providers, ensuring high availability even during network congestion.

**Chain Abstraction**: While focused on Arbitrum, the architecture supports multi-chain deployment through configurable network parameters and token address mappings.

## Security Architecture

**Emergency Controls**: Multiple emergency stop mechanisms are implemented, including file-based triggers and manual intervention points that can halt all trading activities immediately.

**Transaction Verification**: A comprehensive verification system validates transaction parameters, estimates gas costs, and performs pre-flight checks before execution.

**Health Factor Protection**: Automatic position monitoring prevents operations that could lead to liquidation, with configurable safety margins and alert systems.

# External Dependencies

## Blockchain Infrastructure

**Web3 Provider**: Utilizes web3.py for Ethereum/Arbitrum blockchain interactions with support for multiple RPC providers including Alchemy, BlastAPI, and public endpoints.

**Arbitrum Network**: Primary deployment target is Arbitrum mainnet (Chain ID 42161) with fallback support for Arbitrum Sepolia testnet.

## DeFi Protocol Integration

**Aave V3**: Core lending protocol integration for borrowing, lending, and health factor monitoring. Uses official Aave pool contracts and data providers.

**Aave Debt Switch**: Integration with Aave's ParaSwapDebtSwapAdapter for direct debt position swapping without intermediate token conversions.

**Uniswap V3**: Fallback DEX integration for token swapping when direct debt swapping is not available or optimal.

## Market Data Services

**CoinMarketCap API**: Primary price data provider for BTC, ARB, and other token prices. Includes rate limiting and usage tracking.

**Backup Price Sources**: Multiple fallback price providers ensure continued operation during API outages.

## External APIs

**The Graph Protocol**: Aave subgraph integration for historical lending data and position analysis.

**Arbiscan API**: Transaction verification and blockchain state queries for the Arbitrum network.

## Development Tools

**Flask Framework**: REST API server for system monitoring, diagnostics, and external integrations.

**Replit Environment**: Cloud deployment platform with integrated secrets management and environment variable handling.