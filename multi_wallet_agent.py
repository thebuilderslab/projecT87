
import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from aave_integration import AaveArbitrumIntegration
from aave_integration import AaveHealthMonitor

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

# --- Merged from main.py ---

def check_agent_status():
    """Check if agent is ready and functional"""
    url = "http://localhost:5000/api/wallet_status"
    
    try:
        print("🔍 Checking agent status...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'error' not in data:
                print("✅ AGENT STATUS: READY")
                print(f"   Wallet: {data.get('wallet_address', 'Unknown')}")
                print(f"   Network: {data.get('network_name', 'Unknown')}")
                print(f"   ETH Balance: {data.get('eth_balance', 0):.6f}")
                print(f"   Health Factor: {data.get('health_factor', 0):.4f}")
                
                if data.get('health_factor', 0) > 0:
                    print("✅ AAVE INTEGRATION: ACTIVE")
                else:
                    print("⚠️ AAVE INTEGRATION: CHECKING...")
                
                return True
            else:
                print(f"❌ AGENT ERROR: {data['error']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard not running - start with 'python web_dashboard.py'")
        return False
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

def monitor_agent_status(check_interval=5):
    """Monitor agent status until ready"""
    print("🤖 DeFi Agent Status Monitor")
    print("=" * 40)
    
    attempts = 0
    max_attempts = 20  # 100 seconds total
    
    while attempts < max_attempts:
        attempts += 1
        print(f"\n📊 Status Check #{attempts}")
        
        if check_agent_status():
            print("\n🎉 AGENT IS READY FOR OPERATION!")
            print("🌐 Access dashboard at your Replit webview URL")
            return True
        
        if attempts < max_attempts:
            print(f"⏳ Waiting {check_interval} seconds before next check...")
            time.sleep(check_interval)
    
    print(f"\n⚠️ Agent not ready after {max_attempts} attempts")
    print("💡 Check the dashboard console for initialization errors")
    return False
# --- Merged from validate_agent_wallet.py ---

def validate_agent_wallet():
    """Validate that the agent is using the correct wallet and can access Aave data"""
    print("🔍 AGENT WALLET VALIDATION & DASHBOARD COMPARISON")
    print("=" * 60)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized successfully")
        print(f"🔑 Agent Wallet Address: {agent.address}")
        print(f"🌐 Network: {agent.network_mode} (Chain ID: {agent.chain_id})")
        
        # Expected dashboard wallet address (from your logs)
        expected_wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
        print(f"📊 Expected Dashboard Wallet: {expected_wallet}")
        
        # Check if addresses match
        if agent.address.lower() == expected_wallet.lower():
            print(f"✅ WALLET MATCH: Agent and dashboard use same address!")
        else:
            print(f"❌ WALLET MISMATCH:")
            print(f"   Agent wallet:    {agent.address}")
            print(f"   Dashboard wallet: {expected_wallet}")
            print(f"🔧 SOLUTION: Update PRIVATE_KEY to match dashboard wallet")
            return False
        
        # Test direct Aave contract call with agent wallet
        print(f"\n🔍 TESTING AAVE CONTRACT ACCESS:")
        
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralETH", "type": "uint256"},
                {"name": "totalDebtETH", "type": "uint256"},
                {"name": "availableBorrowsETH", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(
            address=agent.aave_pool_address,
            abi=pool_abi
        )
        
        account_data = pool_contract.functions.getUserAccountData(agent.address).call()
        
        total_collateral_eth = account_data[0] / (10**18)
        total_debt_eth = account_data[1] / (10**18)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        # Convert to USD (approximate)
        eth_price = 2960  # Current approximate ETH price
        collateral_usd = total_collateral_eth * eth_price
        debt_usd = total_debt_eth * eth_price
        
        print(f"✅ Agent Aave Query Results:")
        print(f"   Total Collateral: {total_collateral_eth:.8f} ETH (${collateral_usd:,.2f})")
        print(f"   Total Debt: {total_debt_eth:.8f} ETH (${debt_usd:,.2f})")
        print(f"   Health Factor: {health_factor:.4f}")
        
        # Compare with dashboard values (from your logs)
        expected_collateral_usd = 174.0  # From dashboard
        expected_debt_usd = 20.0         # From dashboard
        
        print(f"\n📊 DASHBOARD vs AGENT COMPARISON:")
        print(f"   Dashboard Collateral: ~${expected_collateral_usd:,.2f}")
        print(f"   Agent Collateral:     ${collateral_usd:,.2f}")
        print(f"   Dashboard Debt:       ~${expected_debt_usd:,.2f}")
        print(f"   Agent Debt:           ${debt_usd:,.2f}")
        
        if abs(collateral_usd - expected_collateral_usd) < 10:
            print(f"✅ PERFECT MATCH: Agent sees same position as dashboard!")
            print(f"🚀 TRIGGER STATUS: Collateral ${collateral_usd:,.2f} - Growth needed: ${12 - collateral_usd:,.2f}")
            
            # If collateral is above $12, the trigger should activate
            if collateral_usd >= 12:
                print(f"🎯 TRIGGER READY: Add ${12:.2f} more to activate autonomous sequence!")
            
        else:
            print(f"❌ DATA MISMATCH:")
            print(f"   Difference: ${abs(collateral_usd - expected_collateral_usd):,.2f}")
            print(f"🔧 This suggests:")
            print(f"   1. Different wallet addresses")
            print(f"   2. RPC endpoint data lag")
            print(f"   3. Contract address issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        print(f"🔧 Try running with different RPC endpoint")
        return False
# --- Merged from main.py ---

def debug_agent_position():
    """Debug why agent isn't detecting position properly"""
    print("🔍 DEBUGGING AGENT POSITION DETECTION")
    print("=" * 60)
    
    # Initialize connection
    private_key = os.getenv('PRIVATE_KEY')
    rpc_url = "https://arbitrum-mainnet.infura.io/v3/5d36f0061cbc4dda980f938ff891c141"
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = Account.from_key(private_key)
    address = account.address
    
    print(f"📍 Wallet: {address}")
    print(f"🌐 Chain ID: {w3.eth.chain_id}")
    print(f"💰 ETH Balance: {w3.from_wei(w3.eth.get_balance(address), 'ether'):.6f} ETH")
    
    # Aave V3 Pool on Arbitrum
    aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    
    # Standard Aave Pool ABI for getUserAccountData
    pool_abi = [{
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {"name": "totalCollateralBase", "type": "uint256"},
            {"name": "totalDebtBase", "type": "uint256"},
            {"name": "availableBorrowsBase", "type": "uint256"},
            {"name": "currentLiquidationThreshold", "type": "uint256"},
            {"name": "ltv", "type": "uint256"},
            {"name": "healthFactor", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }]
    
    try:
        print(f"\n🏦 TESTING AAVE POSITION DETECTION:")
        
        # Method 1: Direct Aave Pool Query
        pool_contract = w3.eth.contract(address=aave_pool, abi=pool_abi)
        account_data = pool_contract.functions.getUserAccountData(address).call()
        
        total_collateral_usd = account_data[0] / (10**8)  # Aave uses 8 decimals for USD
        total_debt_usd = account_data[1] / (10**8)
        available_borrows_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"   ✅ Direct Aave Query Results:")
        print(f"      Total Collateral: ${total_collateral_usd:,.2f}")
        print(f"      Total Debt: ${total_debt_usd:,.2f}")
        print(f"      Available Borrows: ${available_borrows_usd:,.2f}")
        print(f"      Health Factor: {health_factor:.4f}")
        
        # Method 2: Check Individual aToken Balances
        print(f"\n🔍 TESTING INDIVIDUAL ATOKEN BALANCES:")
        
        # aToken addresses on Arbitrum Mainnet
        atoken_addresses = {
            "aWBTC": "0x6533afac2E7BCCB20dca161449A13A2D2d5B739A",
            "aWETH": "0xe50fA9b4c56454E2edF6BFf7c81b50c5F05aBE61", 
            "aUSDC": "0x724dc807b04555b71ed48a6896b6F41593b8C637"
        }
        
        atoken_abi = [{
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        total_detected = 0
        for token_name, token_address in atoken_addresses.items():
            try:
                token_contract = w3.eth.contract(address=token_address, abi=atoken_abi)
                balance = token_contract.functions.balanceOf(address).call()
                
                # Convert to readable format
                if token_name == "aUSDC":
                    decimals = 6
                elif token_name == "aWBTC":
                    decimals = 8
                else:
                    decimals = 18
                    
                readable_balance = balance / (10**decimals)
                print(f"      {token_name}: {readable_balance:.8f}")
                
                if readable_balance > 0:
                    total_detected += 1
                    
            except Exception as e:
                print(f"      {token_name}: ❌ Error - {e}")
        
        print(f"\n📊 POSITION ANALYSIS:")
        print(f"   Aave shows collateral: ${total_collateral_usd:,.2f}")
        print(f"   Individual aTokens detected: {total_detected}")
        print(f"   Agent baseline: $175.17")
        print(f"   Growth needed for trigger: $12.00")
        print(f"   Current growth: ${total_collateral_usd - 175.17:,.2f}")
        
        if total_collateral_usd >= (175.17 + 12):
            print(f"   🚀 TRIGGER SHOULD ACTIVATE!")
        else:
            print(f"   ⏸️ Trigger threshold not met")
            
        # Method 3: Test Dashboard Data Function
        print(f"\n🔍 TESTING DASHBOARD DATA FUNCTION:")
        try:
            from web_dashboard import get_live_agent_data
            dashboard_data = get_live_agent_data()
            
            if dashboard_data:
                print(f"   ✅ Dashboard data retrieved:")
                print(f"      Source: {dashboard_data.get('data_source', 'unknown')}")
                print(f"      Health Factor: {dashboard_data.get('health_factor', 0):.4f}")
                print(f"      Collateral: ${dashboard_data.get('total_collateral_usdc', 0):,.2f}")
                print(f"      Debt: ${dashboard_data.get('total_debt_usdc', 0):,.2f}")
            else:
                print(f"   ❌ No dashboard data retrieved")
                
        except Exception as e:
            print(f"   ❌ Dashboard data error: {e}")
            
        # Method 4: Compare with Baseline File
        print(f"\n📋 CHECKING BASELINE STORAGE:")
        baseline_file = "agent_baseline.json"
        if os.path.exists(baseline_file):
            import json
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
                print(f"   Stored baseline: ${baseline_data.get('last_collateral_value_usd', 0):,.2f}")
        else:
            print(f"   No baseline file found")
            
        # Recommendations
        print(f"\n💡 DEBUGGING RECOMMENDATIONS:")
        
        if total_collateral_usd > 180:
            print(f"   1. ✅ Position detected correctly: ${total_collateral_usd:,.2f}")
            print(f"   2. 🔧 Agent trigger logic needs adjustment")
            print(f"   3. 🎯 Current position should trigger autonomous sequence")
        elif total_detected == 0:
            print(f"   1. ❌ aToken balance detection failing")
            print(f"   2. 🔧 RPC endpoint may have limitations")
            print(f"   3. 🎯 Try alternative data source")
        else:
            print(f"   1. ⚠️ Partial detection - some tokens visible")
            print(f"   2. 🔧 Mixed data source reliability")
            print(f"   3. 🎯 Use direct Aave pool data as primary source")
            
        return {
            'aave_collateral': total_collateral_usd,
            'aave_debt': total_debt_usd,
            'health_factor': health_factor,
            'atoken_detected': total_detected,
            'trigger_ready': total_collateral_usd >= (175.17 + 12)
        }
        
    except Exception as e:
        print(f"❌ Critical error in debugging: {e}")
        import traceback
        traceback.print_exc()
        return None
# --- Merged from user_agent.py ---

class UserAgent:
    """Represents a parsed user agent header value.

    The default implementation does no parsing, only the :attr:`string`
    attribute is set. A subclass may parse the string to set the
    common attributes or expose other information. Set
    :attr:`werkzeug.wrappers.Request.user_agent_class` to use a
    subclass.

    :param string: The header value to parse.

    .. versionadded:: 2.0
        This replaces the previous ``useragents`` module, but does not
        provide a built-in parser.
    """

    platform: str | None = None
    """The OS name, if it could be parsed from the string."""

    browser: str | None = None
    """The browser name, if it could be parsed from the string."""

    version: str | None = None
    """The browser version, if it could be parsed from the string."""

    language: str | None = None
    """The browser language, if it could be parsed from the string."""

    def __init__(self, string: str) -> None:
        self.string: str = string
        """The original header value."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.browser}/{self.version}>"

    def __str__(self) -> str:
        return self.string

    def __bool__(self) -> bool:
        return bool(self.browser)

    def to_header(self) -> str:
        """Convert to a header value."""
        return self.string

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.browser}/{self.version}>"

    def __str__(self) -> str:
        return self.string

    def __bool__(self) -> bool:
        return bool(self.browser)

    def to_header(self) -> str:
        """Convert to a header value."""
        return self.string