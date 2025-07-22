
import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from aave_integration import AaveArbitrumIntegration
from aave_health_monitor import AaveHealthMonitor

class MultiWalletAgent:
    def __init__(self):
        load_dotenv()
        
        # Network configurations
        self.networks = {
            'arbitrum_sepolia': {
                'rpc_url': 'https://sepolia-rollup.arbitrum.io/rpc',
                'chain_id': 421614,
                'aave_pool': '0xE7EC1C9e6D33d2897c97Fd3c9e8b842f5c6Efc57',
                'weth': '0x980B62Da83eFf3D4576C647993b0c1D7faf17c73',
                'dai': '0x5f6bB460B6d0bdA2CCaDdd7A19B5F6E7b5b8E1DB'
            },
            'arbitrum_mainnet': {
                'rpc_url': 'https://arb1.arbitrum.io/rpc',
                'chain_id': 42161,
                'aave_pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
                'weth': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                'dai': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
            },
            'ethereum_mainnet': {
                'rpc_url': 'https://eth.llamarpc.com',
                'chain_id': 1,
                'aave_pool': '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
                'weth': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'dai': '0x6B175474E89094C44Da98b954EedeAC495271d0F'
            }
        }
        
        # Active sessions per wallet
        self.active_sessions = {}
        
    def execute_strategy_for_wallet(self, target_wallet_address, network_name, strategy_config):
        """
        Execute DeFi strategy for a specific wallet address
        
        Args:
            target_wallet_address: MetaMask wallet to execute strategy for
            network_name: Network to operate on (arbitrum_sepolia, arbitrum_mainnet, etc.)
            strategy_config: Strategy parameters and settings
        """
        print(f"🎯 MULTI-WALLET STRATEGY EXECUTION")
        print(f"   Target Wallet: {target_wallet_address}")
        print(f"   Network: {network_name}")
        print(f"   Strategy: {strategy_config.get('type', 'dynamic_health')}")
        
        # Validate network
        if network_name not in self.networks:
            raise ValueError(f"Unsupported network: {network_name}")
        
        network_config = self.networks[network_name]
        
        # Connect to network
        w3 = Web3(Web3.HTTPProvider(network_config['rpc_url']))
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to {network_name}")
        
        # Validate target wallet
        target_wallet = w3.to_checksum_address(target_wallet_address)
        
        # Get our agent's account (for gas payments)
        agent_private_key = os.getenv('PRIVATE_KEY')
        if not agent_private_key:
            raise ValueError("Agent private key not configured")
        
        agent_account = Account.from_key(agent_private_key)
        
        # Create monitoring session for target wallet
        session_id = f"{network_name}_{target_wallet}"
        
        # Initialize integrations for target wallet
        aave_integration = self.create_aave_integration(w3, network_config, target_wallet)
        health_monitor = self.create_health_monitor(w3, network_config, target_wallet, aave_integration)
        
        # Store session
        self.active_sessions[session_id] = {
            'target_wallet': target_wallet,
            'network': network_name,
            'w3': w3,
            'aave': aave_integration,
            'health_monitor': health_monitor,
            'strategy_config': strategy_config,
            'agent_account': agent_account
        }
        
        # Execute strategy
        return self.run_strategy_session(session_id)
    
    def create_aave_integration(self, w3, network_config, target_wallet):
        """Create Aave integration for target wallet"""
        # Create a mock account object for the target wallet (read-only)
        class ReadOnlyAccount:
            def __init__(self, address):
                self.address = address
        
        target_account = ReadOnlyAccount(target_wallet)
        
        # Override the integration to work with read-only monitoring
        integration = AaveArbitrumIntegration(w3, target_account)
        
        # Update contract addresses for the network
        integration.pool_address = w3.to_checksum_address(network_config['aave_pool'])
        integration.weth_address = w3.to_checksum_address(network_config['weth'])
        integration.dai_address = w3.to_checksum_address(network_config['dai'])
        
        return integration
    
    def create_health_monitor(self, w3, network_config, target_wallet, aave_integration):
        """Create health monitor for target wallet"""
        class ReadOnlyAccount:
            def __init__(self, address):
                self.address = address
        
        target_account = ReadOnlyAccount(target_wallet)
        monitor = AaveHealthMonitor(w3, target_account, aave_integration)
        
        return monitor
    
    def run_strategy_session(self, session_id):
        """Run strategy for a specific session"""
        session = self.active_sessions[session_id]
        
        print(f"🔄 Running strategy for session: {session_id}")
        
        # Get current health factor
        health_data = session['health_monitor'].get_current_health_factor()
        if not health_data:
            print("❌ Unable to get health factor")
            return False
        
        print(f"📊 Target Wallet Health Factor: {health_data['health_factor']:.4f}")
        
        # Check strategy triggers
        strategy_type = session['strategy_config'].get('type', 'monitor_only')
        
        if strategy_type == 'monitor_only':
            return self.monitor_only_strategy(session)
        elif strategy_type == 'dynamic_health':
            return self.dynamic_health_strategy(session)
        elif strategy_type == 'yield_optimization':
            return self.yield_optimization_strategy(session)
        
        return False
    
    def monitor_only_strategy(self, session):
        """Monitor wallet without executing transactions"""
        health_summary = session['health_monitor'].get_monitoring_summary()
        
        print(f"📊 MONITORING SUMMARY:")
        print(f"   Health Factor: {health_summary['current_health_factor']:.4f}")
        print(f"   ARB Price: ${health_summary['arb_price']:.4f}")
        print(f"   Borrow Trigger: {health_summary['borrow_trigger_active']}")
        print(f"   Risk Trigger: {health_summary['risk_trigger_active']}")
        
        # Log recommendations
        if health_summary['borrow_trigger_active']:
            print(f"💡 RECOMMENDATION: Consider borrowing {health_summary['optimal_dai_borrow']:.2f} DAI")
        
        if health_summary['risk_trigger_active']:
            print(f"⚠️ RISK ALERT: Consider reducing ARB exposure")
        
        return True
    
    def dynamic_health_strategy(self, session):
        """Execute dynamic health management (requires transaction capabilities)"""
        print("🚨 DYNAMIC STRATEGY: Would require transaction signing by target wallet")
        print("💡 For security, this would need MetaMask approval from the target wallet")
        
        # In a real implementation, this would:
        # 1. Generate transaction data
        # 2. Send to target wallet for approval
        # 3. Execute once approved
        
        return self.monitor_only_strategy(session)
    
    def generate_strategy_prompt(self, wallet_address, network, strategy_type="dynamic_health"):
        """Generate a prompt for strategy execution"""
        prompt = f"""
🎯 **DEFI STRATEGY EXECUTION REQUEST**

**Target Details:**
- Wallet: {wallet_address}
- Network: {network}
- Strategy: {strategy_type}

**Instructions:**
Execute the following DeFi strategy on the specified wallet:

1. **Monitor Aave Health Factor** continuously
2. **Dynamic Borrowing**: When health factor increases by 0.02+, borrow DAI to maintain 1.19 health factor
3. **Risk Management**: If health factor declines AND ARB price drops, recommend swapping ARB to DAI
4. **Yield Optimization**: Automatically supply idle collateral for lending yield

**Safety Features:**
- Read-only monitoring by default
- Transaction approval required from target wallet
- Real-time risk assessment
- Automated stop-loss recommendations

Would you like to proceed with this strategy?
"""
        return prompt

# Usage examples and API
def create_multi_wallet_prompt(target_wallet, network="arbitrum_mainnet"):
    """Create a prompt for multi-wallet strategy execution"""
    agent = MultiWalletAgent()
    return agent.generate_strategy_prompt(target_wallet, network)

def execute_for_wallet(target_wallet, network="arbitrum_mainnet", strategy="monitor_only"):
    """Execute strategy for a specific wallet"""
    agent = MultiWalletAgent()
    
    strategy_config = {
        'type': strategy,
        'health_factor_target': 1.19,
        'borrow_trigger_threshold': 0.02,
        'risk_mitigation_enabled': True
    }
    
    return agent.execute_strategy_for_wallet(target_wallet, network, strategy_config)

if __name__ == "__main__":
    # Example usage
    example_wallet = "0x742d35Cc6676C4C8da4fDc4d0D60a6f3F8E2d6d1"  # Example MetaMask address
    
    print("🚀 Multi-Wallet DeFi Agent")
    print("=" * 50)
    
    # Generate prompt for user
    prompt = create_multi_wallet_prompt(example_wallet, "arbitrum_mainnet")
    print(prompt)
    
    # Execute monitoring
    try:
        result = execute_for_wallet(example_wallet, "arbitrum_mainnet", "monitor_only")
        print(f"✅ Strategy execution result: {result}")
    except Exception as e:
        print(f"❌ Strategy execution failed: {e}")
