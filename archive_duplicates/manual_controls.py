
from arbitrum_testnet_agent import ArbitrumTestnetAgent

class ManualControls:
    def __init__(self):
        self.agent = ArbitrumTestnetAgent()
        
    def fund_wallet(self, dai_amount=100, eth_amount=10):
        """Instructions for funding wallet"""
        print(f"💰 **FUNDING INSTRUCTIONS**")
        print(f"Send {dai_amount} DAI and {eth_amount} ETH to:")
        print(f"📍 Wallet Address: {self.agent.address}")
        print(f"🌐 Network: Arbitrum Sepolia")
        print(f"🔗 Bridge: https://bridge.arbitrum.io/?destinationChain=arbitrum-sepolia")
        
    def execute_strategy(self, strategy_type):
        """Execute specific strategies manually"""
        strategies = {
            "health_check": "Check current health factor and trigger conditions",
            "supply_collateral": "Supply ETH/DAI as collateral to Aave",
            "borrow_usdc": "Borrow USDC when health factor > 1.21",
            "swap_to_arb": "Swap USDC to ARB tokens",
            "risk_mitigation": "Swap ARB back to USDC if declining"
        }
        
        print(f"\n🎯 Executing: {strategies.get(strategy_type, 'Unknown strategy')}")
        
        if strategy_type == "health_check":
            summary = self.agent.health_monitor.get_monitoring_summary()
            print(f"Current Health Factor: {summary['current_health_factor']:.4f}")
            return summary
            
        elif strategy_type == "supply_collateral":
            return self.agent.aave.supply_to_aave(
                self.agent.aave.weth_address, 
                0.01  # Default 0.01 ETH
            )
            
        elif strategy_type == "supply_wbtc":
            wbtc_amount = 0.0004087  # Specific amount requested
            return self.agent.aave.supply_wbtc_to_aave(wbtc_amount)
            
        # Add more manual strategies as needed
        
    def show_menu(self):
        """Show interactive menu"""
        print("\n🎛️ **MANUAL CONTROL MENU**")
        print("1. 💰 Fund Wallet Instructions")
        print("2. 🏥 Check Health Status") 
        print("3. 🏦 Supply Collateral")
        print("4. 💸 Execute Borrow Strategy")
        print("5. 🔄 Risk Mitigation")
        print("6. 📊 Show Dashboard")
        print("0. Exit")

if __name__ == "__main__":
    controls = ManualControls()
    controls.show_menu()
