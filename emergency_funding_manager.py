
#!/usr/bin/env python3
"""
EMERGENCY FUNDING MANAGER
Handles low ETH balance and gas fee optimization
"""

import os
from web3 import Web3
from enhanced_rpc_manager import EnhancedRPCManager

class EmergencyFundingManager:
    def __init__(self):
        self.rpc_manager = EnhancedRPCManager()
        self.min_eth_required = 0.005  # Minimum ETH for operations
        
    def check_and_optimize_gas(self, wallet_address):
        """Check ETH balance and optimize gas usage"""
        if not self.rpc_manager.find_working_rpc():
            return False
        
        w3 = self.rpc_manager.w3
        eth_balance = w3.eth.get_balance(wallet_address) / 10**18
        
        print(f"⚡ Current ETH Balance: {eth_balance:.6f} ETH")
        print(f"💡 Minimum Required: {self.min_eth_required:.6f} ETH")
        
        if eth_balance < self.min_eth_required:
            print("❌ Insufficient ETH for gas fees")
            self.provide_funding_guidance(wallet_address, eth_balance)
            return False
        else:
            print("✅ Sufficient ETH for gas fees")
            return True
    
    def provide_funding_guidance(self, wallet_address, current_balance):
        """Provide specific funding guidance"""
        needed_eth = self.min_eth_required - current_balance
        
        print(f"\n💰 FUNDING GUIDANCE")
        print(f"=" * 40)
        print(f"📍 Wallet: {wallet_address}")
        print(f"🏦 Current: {current_balance:.6f} ETH")
        print(f"💎 Needed: {needed_eth:.6f} ETH")
        print(f"💵 USD Cost: ~${needed_eth * 2500:.2f}")
        
        print(f"\n🚀 FUNDING OPTIONS:")
        print(f"1. 🏦 CEX Transfer: Send from Coinbase/Binance")
        print(f"2. 🌉 Bridge: Use Arbitrum bridge from mainnet")
        print(f"3. 💳 Buy directly: Use on-ramp services")
        
        print(f"\n⚡ OPTIMIZED GAS SETTINGS:")
        print(f"• Use 0.01 Gwei gas price (Arbitrum is cheap)")
        print(f"• Batch transactions when possible")
        print(f"• Monitor gas prices before executing")
    
    def calculate_optimized_gas(self, operation_type="swap"):
        """Calculate optimized gas settings"""
        if not self.rpc_manager.w3:
            return None
        
        try:
            # Get current gas price
            current_gas_price = self.rpc_manager.w3.eth.gas_price
            
            # Arbitrum typically has very low gas prices
            optimized_gas_price = min(current_gas_price, self.rpc_manager.w3.to_wei(0.1, 'gwei'))
            
            # Gas limits for different operations
            gas_limits = {
                'approve': 60000,
                'swap': 300000,
                'supply': 200000,
                'borrow': 250000
            }
            
            gas_limit = gas_limits.get(operation_type, 200000)
            
            estimated_cost_eth = (optimized_gas_price * gas_limit) / 10**18
            estimated_cost_usd = estimated_cost_eth * 2500
            
            return {
                'gas_price': optimized_gas_price,
                'gas_limit': gas_limit,
                'estimated_cost_eth': estimated_cost_eth,
                'estimated_cost_usd': estimated_cost_usd
            }
            
        except Exception as e:
            print(f"❌ Gas calculation error: {e}")
            return None

if __name__ == "__main__":
    # Test the funding manager
    manager = EmergencyFundingManager()
    
    # Example wallet address (replace with actual)
    test_wallet = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
    
    result = manager.check_and_optimize_gas(test_wallet)
    print(f"\nFunding check result: {'✅ READY' if result else '❌ NEEDS FUNDING'}")
